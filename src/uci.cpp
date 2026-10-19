#include "forge/board.hpp"
#include "forge/book.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"
#include "forge/uci_output.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>
#include <string_view>
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

namespace {

// Ply number implied by the position's move counters (0 at the start position).
int game_ply(const forge::Board& board) {
    return 2 * (board.fullmove_number() - 1) + (board.side_to_move() == forge::Black ? 1 : 0);
}

} // namespace

int main() {
    forge::Board board;
    forge::Searcher searcher;
    int move_overhead_ms = 10;
    bool ponder_enabled = false;
    forge::book::Book book;
    book.load_embedded();
    bool own_book = forge::book::embedded_available();
    std::string book_file;
    int book_depth = 30;
    int book_variety = 30;
    std::uint64_t book_rng = static_cast<std::uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count()) | 1ULL;
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
        const auto command_start = std::chrono::steady_clock::now();
        std::istringstream input(line);
        std::string command;
        input >> command;
        if (command == "uci") {
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            std::cout << "id name Chess Engine Forge 6.4.5 candidate\n"
                         "id author OpenAI\n"
                         "option name Hash type spin default 32 min 1 max 2048\n"
                         "option name Threads type spin default 1 min 1 max 256\n"
                         "option name Move Overhead type spin default 10 min 0 max 1000\n"
                         "option name Ponder type check default false\n"
                         "option name OwnBook type check default " << (forge::book::embedded_available() ? "true" : "false") << "\n"
                         "option name Book File type string default <empty>\n"
                         "option name Book Depth type spin default 30 min 0 max 100\n"
                         "option name Book Variety type spin default 30 min 0 max 100\n";
            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\n";
#ifdef FORGE_EXPOSE_TUNABLES
            // Development builds advertise the search constants so match
            // runners can set them; release builds accept them silently.
            for (const forge::tune::Parameter& parameter : forge::tune::parameters()) {
                std::cout << "option name " << parameter.name << " type spin default " << *parameter.value
                          << " min " << parameter.minimum << " max " << parameter.maximum << "\n";
            }
#endif
            std::cout << "option name Clear Hash type button\n"
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
            bool handled_tunable = false;
            for (const forge::tune::Parameter& parameter : forge::tune::parameters()) {
                if (name != parameter.name) continue;
                handled_tunable = true;
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                } else {
                    *parameter.value = std::clamp(value, parameter.minimum, parameter.maximum);
                    forge::tune::refresh();
                }
            }
            if (handled_tunable) {
                // Unlisted development options; nothing else to do.
            } else if (name == "Clear Hash") {
                searcher.clear_hash();
            } else if (name == "Ponder") {
                if (value_text == "true") ponder_enabled = true;
                else if (value_text == "false") ponder_enabled = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option Ponder" << std::endl;
                }
            } else if (name == "OwnBook") {
                if (value_text == "true") own_book = true;
                else if (value_text == "false") own_book = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option OwnBook" << std::endl;
                }
            } else if (name == "Book File") {
                std::string rest;
                std::getline(input, rest);
                std::string path = value_text + rest;
                while (!path.empty() && (path.back() == ' ' || path.back() == '\r')) path.pop_back();
                if (path.empty() || path == "<empty>") {
                    book_file.clear();
                    book.load_embedded();
                } else if (book.load_file(path)) {
                    book_file = path;
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string loaded book " << path << " with " << book.size() << " entries" << std::endl;
                } else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string cannot load book " << path << std::endl;
                }
            } else if (name == "Book Depth" || name == "Book Variety") {
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                } else if (name == "Book Depth") {
                    book_depth = std::clamp(value, 0, 100);
                } else {
                    book_variety = std::clamp(value, 0, 100);
                }
            } else if (name == "UseNNUE") {
                if (value_text == "true") forge::nnue::enabled = true;
                else if (value_text == "false") forge::nnue::enabled = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option UseNNUE" << std::endl;
                }
                searcher.clear_hash();
            } else if (name == "Hash" || name == "Move Overhead" || name == "Threads") {
                int value = 0;
                const auto parsed = std::from_chars(
                    value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid value for option " << name << std::endl; }
                } else if (name == "Hash") {
                    searcher.resize_hash(static_cast<std::size_t>(std::clamp(value, 1, 2048)));
                } else if (name == "Threads") {
                    searcher.set_threads(std::clamp(value, 1, 256));
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
                limits.request_start = command_start;
                limits.move_overhead_ms = move_overhead_ms;
                // Book moves apply to game play (clock or movetime searches), not
                // to analysis, pondering or restricted searches.
                const bool game_search = (limits.time_ms >= 0 || limits.movetime_ms >= 0) && !limits.infinite &&
                                         !limits.ponder && !limits.search_moves_specified && limits.mate_moves == 0;
                if (game_search && (own_book || !book_file.empty()) && !book.empty() && game_ply(board) < book_depth) {
                    const forge::Move book_move = book.probe(board, book_variety, book_rng);
                    if (!book_move.is_none()) {
                        std::string prediction;
                        if (ponder_enabled) {
                            forge::Board reply_board = board;
                            forge::Undo undo;
                            (void)reply_board.make_move(book_move, undo);
                            const forge::Move reply = book.probe(reply_board, 0, book_rng);
                            if (!reply.is_none()) prediction = " ponder " + forge::Board::move_to_uci(reply);
                        }
                        const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                        std::cout << "info string book move " << forge::Board::move_to_uci(book_move) << std::endl;
                        std::cout << "bestmove " << forge::Board::move_to_uci(book_move) << prediction << std::endl;
                        continue;
                    }
                }
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
        } else if (command == "bench") {
            // Fixed-depth search over a small position set; prints a node
            // signature and speed for quick regression and performance checks.
            stop_search();
            int depth = 13;
            if (int parsed = 0; input >> parsed) depth = std::clamp(parsed, 1, 64);
            constexpr std::array<std::string_view, 8> fens{
                forge::Board::StandardStartFen,
                "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
                "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
                "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
                "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
                "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
                "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
                "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
            };
            std::uint64_t total_nodes = 0;
            const auto start = std::chrono::steady_clock::now();
            forge::Searcher bench_searcher(16);
            for (const std::string_view fen : fens) {
                forge::Board bench_board;
                if (!bench_board.set_fen(fen)) continue;
                forge::SearchLimits limits;
                limits.depth = depth;
                bench_searcher.clear();
                total_nodes += bench_searcher.search(bench_board, limits).nodes;
            }
            const auto elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::steady_clock::now() - start).count();
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            std::cout << "info string bench depth " << depth << " nodes " << total_nodes << " time " << elapsed_ms
                      << " nps " << (elapsed_ms > 0 ? total_nodes * 1000U / static_cast<std::uint64_t>(elapsed_ms) : 0)
                      << std::endl;
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
