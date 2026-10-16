#include "forge/board.hpp"
#include "forge/search.hpp"
#include "forge/uci_output.hpp"

#include <algorithm>
#include <charconv>
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

namespace {

void apply_position(forge::Board& board, std::istringstream& input) {
    forge::Board candidate = board;
    std::string token;
    if (!(input >> token)) return;
    if (token == "startpos") {
        (void)candidate.set_fen(forge::Board::StandardStartFen);
    } else if (token == "fen") {
        std::string fen;
        for (int i = 0; i < 6 && input >> token; ++i) {
            if (!fen.empty()) fen += ' ';
            fen += token;
        }
        std::string error;
        if (!candidate.set_fen(fen, &error)) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid FEN: " << error << std::endl; }
            return;
        }
    } else {
        return;
    }
    if (!(input >> token)) {
        board = candidate;
        return;
    }
    if (token != "moves") return;
    while (input >> token) {
        const auto move = candidate.parse_uci(token);
        if (!move.has_value()) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string illegal move " << token << std::endl; }
            return;
        }
        forge::Undo undo;
        (void)candidate.make_move(*move, undo);
    }
    board = candidate;
}

bool is_go_keyword(const std::string& token) {
    return token == "depth" || token == "nodes" || token == "movetime" || token == "movestogo" ||
           token == "infinite" || token == "wtime" || token == "btime" || token == "winc" ||
           token == "binc" || token == "mate" || token == "searchmoves" || token == "ponder";
}

forge::SearchLimits parse_limits(std::istringstream& input, forge::Board& board) {
    forge::SearchLimits limits;
    std::string token;
    std::vector<std::string> tokens;
    while (input >> token) tokens.push_back(token);
    const forge::Color side = board.side_to_move();
    for (std::size_t i = 0; i < tokens.size();) {
        token = tokens[i++];
        auto read_int = [&]() {
            int value = 0;
            if (i < tokens.size()) {
                const std::string& text = tokens[i++];
                const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
                if (result.ec != std::errc{} || result.ptr != text.data() + text.size()) return 0;
            }
            return value;
        };
        if (token == "depth") limits.depth = std::clamp(read_int(), 1, 64);
        else if (token == "nodes") {
            if (i < tokens.size()) {
                const std::string& text = tokens[i++];
                std::uint64_t value = 0;
                const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
                if (result.ec == std::errc{} && result.ptr == text.data() + text.size()) {
                    limits.nodes = value;
                    limits.nodes_specified = true;
                }
            }
        }
        else if (token == "movetime") limits.movetime_ms = std::max(0, read_int());
        else if (token == "movestogo") limits.moves_to_go = std::max(1, read_int());
        else if (token == "mate") limits.mate_moves = std::clamp(read_int(), 0, 32);
        else if (token == "infinite") limits.infinite = true;
        else if (token == "ponder") limits.ponder = true;
        else if (token == "wtime") { const int value = std::max(0, read_int()); if (side == forge::White) limits.time_ms = value; }
        else if (token == "btime") { const int value = std::max(0, read_int()); if (side == forge::Black) limits.time_ms = value; }
        else if (token == "winc") { const int value = std::max(0, read_int()); if (side == forge::White) limits.increment_ms = value; }
        else if (token == "binc") { const int value = std::max(0, read_int()); if (side == forge::Black) limits.increment_ms = value; }
        else if (token == "searchmoves") {
            limits.search_moves_specified = true;
            while (i < tokens.size() && !is_go_keyword(tokens[i])) {
                const auto move = board.parse_uci(tokens[i++]);
                if (move.has_value()) limits.search_moves.push_back(*move);
            }
        }
    }
    return limits;
}

} // namespace

int main() {
    forge::Board board;
    forge::Searcher searcher;
    int move_overhead_ms = 10;
    bool ponder_enabled = false;
    bool ponder_search_active = false;
    std::thread worker;
    std::mutex stop_mutex;
    std::condition_variable stop_cv;
    bool stop_requested = false;
    bool ponder_hit_received = false;
    auto stop_search = [&]() {
        {
            const std::lock_guard<std::mutex> lock(stop_mutex);
            stop_requested = true;
        }
        searcher.stop();
        stop_cv.notify_all();
        if (worker.joinable()) worker.join();
        ponder_search_active = false;
    };

    std::string line;
    while (std::getline(std::cin, line)) {
        std::istringstream input(line);
        std::string command;
        input >> command;
        if (command == "uci") {
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            std::cout << "id name Chess Engine Forge 6.0.0\n"
                         "id author OpenAI\n"
                         "option name Hash type spin default 32 min 1 max 2048\n"
                         "option name Move Overhead type spin default 10 min 0 max 1000\n"
                         "option name Ponder type check default false\n"
                         "option name Clear Hash type button\n"
                         "uciok" << std::endl;
        } else if (command == "isready") {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "readyok" << std::endl; }
        } else if (command == "ucinewgame") {
            stop_search();
            searcher.clear();
            (void)board.set_fen(forge::Board::StandardStartFen);
        } else if (command == "setoption") {
            stop_search();
            std::string token;
            std::string name;
            std::string value_text;
            input >> token;
            if (token == "name") {
                while (input >> token && token != "value") {
                    if (!name.empty()) name += ' ';
                    name += token;
                }
                if (token == "value") input >> value_text;
            }
            if (name == "Clear Hash") {
                searcher.clear_hash();
            } else if (name == "Ponder") {
                if (value_text == "true") ponder_enabled = true;
                else if (value_text == "false") ponder_enabled = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option Ponder" << std::endl;
                }
            } else if (name == "Hash" || name == "Move Overhead") {
                int value = 0;
                const auto parsed = std::from_chars(
                    value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid value for option " << name << std::endl; }
                } else if (name == "Hash") {
                    searcher.resize_hash(static_cast<std::size_t>(std::clamp(value, 1, 2048)));
                } else {
                    move_overhead_ms = std::clamp(value, 0, 1000);
                }
            }
        } else if (command == "position") {
            stop_search();
            apply_position(board, input);
        } else if (command == "go") {
            stop_search();
            std::string first;
            const auto position = input.tellg();
            input >> first;
            if (first == "perft") {
                std::string depth_text;
                int depth = -1;
                if (!(input >> depth_text)) depth_text.clear();
                const auto parsed = std::from_chars(
                    depth_text.data(), depth_text.data() + depth_text.size(), depth);
                if (parsed.ec != std::errc{} || parsed.ptr != depth_text.data() + depth_text.size() ||
                    depth < 0 || depth > 10) {
                    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string perft depth must be an integer from 0 to 10" << std::endl; }
                    continue;
                }
                if (depth == 0) {
                    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "nodes 1" << std::endl; }
                    continue;
                }
                std::uint64_t total = 0;
                for (const forge::Move move : board.legal_moves()) {
                    forge::Undo undo;
                    (void)board.make_move(move, undo);
                    const std::uint64_t nodes = board.perft(depth - 1);
                    board.unmake_move(move, undo);
                    total += nodes;
                    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << forge::Board::move_to_uci(move) << ": " << nodes << std::endl; }
                }
                { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "nodes " << total << std::endl; }
            } else {
                input.clear();
                input.seekg(position);
                forge::SearchLimits limits = parse_limits(input, board);
                limits.move_overhead_ms = move_overhead_ms;
                const forge::Board search_board = board;
                {
                    const std::lock_guard<std::mutex> lock(stop_mutex);
                    stop_requested = false;
                    ponder_hit_received = false;
                }
                ponder_search_active = limits.ponder;
                searcher.reset_stop();
                worker = std::thread([&searcher, &stop_mutex, &stop_cv, &stop_requested,
                                      &ponder_hit_received, search_board, limits, ponder_enabled]() mutable {
                    const forge::SearchInfo result = searcher.search(search_board, limits, true);
                    if (limits.infinite || limits.ponder) {
                        std::unique_lock<std::mutex> lock(stop_mutex);
                        stop_cv.wait(lock, [&stop_requested, &ponder_hit_received, &limits] {
                            return stop_requested || (limits.ponder && ponder_hit_received);
                        });
                    }
                    const std::string best = result.best_move.from == result.best_move.to
                        ? "0000" : forge::Board::move_to_uci(result.best_move);
                    std::string prediction;
                    if (ponder_enabled && result.pv.size() > 1 &&
                        result.pv.front().from == result.best_move.from &&
                        result.pv.front().to == result.best_move.to &&
                        result.pv.front().promotion == result.best_move.promotion) {
                        prediction = " ponder " + forge::Board::move_to_uci(result.pv[1]);
                    }
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "bestmove " << best << prediction << std::endl;
                });
            }
        } else if (command == "ponderhit") {
            if (ponder_search_active) {
                searcher.ponderhit();
                {
                    const std::lock_guard<std::mutex> lock(stop_mutex);
                    ponder_hit_received = true;
                }
                stop_cv.notify_all();
                ponder_search_active = false;
            }
        } else if (command == "stop") {
            stop_search();
        } else if (command == "quit") {
            stop_search();
            break;
        }
    }
    stop_search();
    return 0;
}
