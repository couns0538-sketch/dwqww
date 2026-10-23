// SPDX-License-Identifier: MIT
// Original synchronous data-generation adapter. Links an unchanged, frozen
// Forge core; contains no search, evaluation, move-generation or NNUE code.
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#ifndef FORGE_DRIVER_SOURCE_ID
#define FORGE_DRIVER_SOURCE_ID "unidentified"
#endif

namespace {
struct DiagnosticScore {
    std::optional<int> cp;
    bool missing = true;
};

class OpponentProcess {
public:
    explicit OpponentProcess(const char* path) {
        int input[2], output[2];
        if (pipe(input) || pipe(output)) throw std::runtime_error("opponent pipe failed");
        pid_ = fork();
        if (pid_ == 0) {
            if (dup2(input[0], STDIN_FILENO) < 0 || dup2(output[1], STDOUT_FILENO) < 0) _exit(126);
            ::close(input[0]); ::close(input[1]); ::close(output[0]); ::close(output[1]);
            execl(path, path, static_cast<char*>(nullptr));
            _exit(127);
        }
        ::close(input[0]); ::close(output[1]);
        if (pid_ < 0) throw std::runtime_error("opponent fork failed");
        input_ = fdopen(input[1], "w"); output_ = fdopen(output[0], "r");
        if (!input_ || !output_) throw std::runtime_error("opponent stream failed");
        send("uci"); until("uciok");
        send("setoption name Threads value 1");
        send("setoption name Hash value 16");
        send("setoption name OwnBook value false");
        send("isready"); until("readyok");
    }
    ~OpponentProcess() { if (!closed_) { try { close(); } catch (...) {} } }
    int pid() const { return static_cast<int>(pid_); }
    void send(const std::string& command) {
        if (std::fprintf(input_, "%s\n", command.c_str()) < 0 || std::fflush(input_))
            throw std::runtime_error("opponent write failed");
    }
    std::vector<std::string> until(const std::string& terminal) {
        std::vector<std::string> lines;
        char* text = nullptr;
        std::size_t capacity = 0;
        while (true) {
            const auto length = getline(&text, &capacity, output_);
            if (length < 0) { std::free(text); throw std::runtime_error("opponent EOF waiting for " + terminal); }
            std::string line(text, static_cast<std::size_t>(length));
            while (!line.empty() && (line.back() == '\r' || line.back() == '\n')) line.pop_back();
            lines.push_back(line);
            if (line == terminal || line.starts_with(terminal + " ")) break;
        }
        std::free(text);
        return lines;
    }
    void new_game() { send("ucinewgame"); send("isready"); until("readyok"); }
    std::pair<std::string, DiagnosticScore> search(const std::vector<std::string>& moves, std::uint64_t nodes) {
        std::string position = "position startpos moves";
        for (const auto& move : moves) position += " " + move;
        send(position); send("go nodes " + std::to_string(nodes));
        DiagnosticScore score;
        std::string bestmove;
        for (const auto& line : until("bestmove")) {
            std::istringstream fields(line);
            std::string token;
            fields >> token;
            if (token == "bestmove") fields >> bestmove;
            else if (token == "info" && !line.starts_with("info string ")) {
                while (fields >> token) if (token == "score") {
                    std::string kind; int value;
                    if (!(fields >> kind >> value)) throw std::runtime_error("malformed opponent score");
                    score.missing = false;
                    score.cp = kind == "cp" ? std::optional<int>(value) : std::nullopt;
                    break;
                }
            }
        }
        return {bestmove, score};
    }
    int close() {
        if (closed_) return code_;
        send("quit"); std::fclose(input_); input_ = nullptr;
        int status = 0;
        if (waitpid(pid_, &status, 0) != pid_) throw std::runtime_error("opponent waitpid failed");
        std::fclose(output_); output_ = nullptr;
        code_ = WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status);
        closed_ = true;
        std::cout << "info string opponent_closed " << pid_ << " exit " << code_ << '\n';
        return code_;
    }
private:
    pid_t pid_ = -1;
    FILE* input_ = nullptr;
    FILE* output_ = nullptr;
    int code_ = 1;
    bool closed_ = false;
};

forge::SearchInfo search_core(forge::Searcher& searcher, const forge::Board& board, std::uint64_t nodes) {
    forge::SearchLimits limits;
    limits.nodes = nodes;
    limits.nodes_specified = true;
    searcher.reset_stop();
#ifdef FORGE_DRIVER_EXCLUSIVE_TT
    return searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
#else
    return searcher.search(board, limits, false);
#endif
}

void native_game(std::istringstream& command, forge::Searcher& searcher, OpponentProcess& opponent) {
    std::uint64_t nodes;
    int max_ply, score_cap, white, black, opening_count;
    if (!(command >> nodes >> max_ply >> score_cap >> white >> black >> opening_count)
        || nodes == 0 || max_ply < 1 || score_cap < 1 || opening_count < 0
        || white < 0 || white > 1 || black < 0 || black > 1)
        throw std::runtime_error("invalid native game settings");
    forge::Board board;
    std::vector<std::string> moves;
    std::ostringstream samples;
    bool first_sample = true;
    int missing_scores = 0;
    for (int index = 0; index < opening_count; ++index) {
        std::string text;
        if (!(command >> text)) throw std::runtime_error("incomplete native opening");
        const auto move = board.parse_uci(text);
        if (!move) throw std::runtime_error("illegal native opening");
        forge::Undo undo;
        if (!board.make_move(*move, undo)) throw std::runtime_error("opening make failed");
        moves.push_back(text);
    }
    searcher.clear();
    if (white || black) opponent.new_game();
    double result = .5;
    std::string termination;
    while (true) {
        // Mate precedes every draw rule, including the explicit ply limit.
        if (!board.has_legal_move()) {
            if (board.in_check()) {
                result = board.side_to_move() == forge::White ? 0.0 : 1.0;
                termination = "checkmate";
            } else termination = "stalemate";
        } else if (board.is_insufficient_material()) termination = "insufficient_material";
        else if (board.is_repetition()) termination = "threefold_repetition";
        else if (board.halfmove_clock() >= 100) termination = "fifty_move_rule";
        else if (static_cast<int>(moves.size()) >= max_ply) termination = "adjudicated_max_ply_draw";
        if (!termination.empty()) break;
        const int engine = board.side_to_move() == forge::White ? white : black;
        DiagnosticScore score;
        std::string text;
        if (engine) {
            auto reply = opponent.search(moves, nodes);
            text = std::move(reply.first);
            score = reply.second;
        } else {
            const auto reply = search_core(searcher, board, nodes);
            text = forge::Board::move_to_uci(reply.best_move);
            if (reply.depth > 0) {
                score.missing = false;
                if (!forge::is_mate_score(reply.score)) score.cp = reply.score;
            }
        }
        const auto move = board.parse_uci(text);
        if (!move) throw std::runtime_error("native game received illegal bestmove: " + text);
        if (score.missing) ++missing_scores;
        if ((score.missing || (score.cp && std::abs(*score.cp) <= score_cap)) && !board.in_check()
            && !move->is_capture() && !move->is_promotion() && !board.gives_check(*move)) {
            if (!first_sample) samples << ',';
            first_sample = false;
            samples << "{\"fen\":\"" << board.fen() << "\",\"ply\":" << moves.size()
                    << ",\"bestmove\":\"" << text << "\",\"score_cp_stm\":";
            if (score.cp) samples << *score.cp; else samples << "null";
            samples << ",\"forge_score_missing\":" << (score.missing ? "true" : "false")
                    << ",\"engine_index\":" << engine << '}';
        }
        forge::Undo undo;
        if (!board.make_move(*move, undo)) throw std::runtime_error("native game make failed");
        moves.push_back(text);
    }
    std::cout << "gamejson {\"moves\":[";
    for (std::size_t index = 0; index < moves.size(); ++index) {
        if (index) std::cout << ',';
        std::cout << '"' << moves[index] << '"';
    }
    std::cout << "],\"samples\":[" << samples.str() << "],\"result_white\":" << result
              << ",\"termination\":\"" << termination << "\",\"final_fen\":\"" << board.fen()
              << "\",\"missing_score_positions\":" << missing_scores << "}\n";
}
} // namespace

int main(int argc, char** argv) {
    std::ios::sync_with_stdio(false);
    forge::Board board;
    forge::Searcher searcher(16, 1);
    std::string cached_base;
    std::vector<std::string> cached_moves;
    std::unique_ptr<OpponentProcess> opponent;
    try {
        if (argc == 3 && std::string(argv[1]) == "--coordinator") opponent = std::make_unique<OpponentProcess>(argv[2]);
        else if (argc != 1) throw std::runtime_error("expected --coordinator <5101-helper>");
        for (std::string line; std::getline(std::cin, line);) {
            std::istringstream command(line);
            std::string verb;
            command >> verb;
            if (verb == "uci") {
                std::cout << "id name Forge frozen-core synchronous generator " FORGE_DRIVER_SOURCE_ID "\n"
                          << "id author OpenAI\n"
                          << "option name Hash type spin default 16 min 1 max 2048\n"
                          << "option name Threads type spin default 1 min 1 max 1\n"
                          << "option name OwnBook type check default false\n";
                if (opponent) std::cout << "info string opponent_pid " << opponent->pid() << '\n';
                std::cout << "uciok\n";
            } else if (verb == "isready") {
                std::cout << "readyok\n";
            } else if (verb == "ucinewgame") {
                searcher.clear();
                cached_base.clear();
                cached_moves.clear();
            } else if (verb == "setoption") {
                std::string name_token, name, value_token, value;
                command >> name_token >> name >> value_token >> value;
                if (name_token != "name" || value_token != "value")
                    throw std::runtime_error("unsupported option syntax");
                if (name == "Hash") searcher.resize_hash(std::stoul(value));
                else if (!((name == "Threads" && value == "1") || (name == "OwnBook" && value == "false")))
                    throw std::runtime_error("unsupported generation option");
            } else if (verb == "position") {
                std::string kind, base, token;
                command >> kind;
                if (kind == "startpos") {
                    base = forge::Board::StandardStartFen;
                } else if (kind == "fen") {
                    for (int field = 0; field < 6; ++field) {
                        if (!(command >> token)) throw std::runtime_error("incomplete FEN");
                        if (field) base += ' ';
                        base += token;
                    }
                } else throw std::runtime_error("unsupported position syntax");
                std::vector<std::string> requested;
                if (command >> token) {
                    if (token != "moves") throw std::runtime_error("expected moves");
                    while (command >> token) requested.push_back(token);
                }
                std::size_t offset = 0;
                if (base == cached_base && requested.size() >= cached_moves.size()
                    && std::equal(cached_moves.begin(), cached_moves.end(), requested.begin())) {
                    offset = cached_moves.size();
                } else {
                    std::string error;
                    if (!board.set_fen(base, &error)) throw std::runtime_error("invalid FEN: " + error);
                }
                for (; offset < requested.size(); ++offset) {
                    const auto move = board.parse_uci(requested[offset]);
                    if (!move) throw std::runtime_error("illegal move: " + requested[offset]);
                    forge::Undo undo;
                    if (!board.make_move(*move, undo)) throw std::runtime_error("make_move rejected legal move");
                }
                cached_base = base;
                cached_moves = std::move(requested);
            } else if (verb == "go") {
                std::string budget;
                std::uint64_t nodes = 0;
                if (!(command >> budget >> nodes) || budget != "nodes" || nodes == 0)
                    throw std::runtime_error("only a positive go nodes budget is supported");
                const auto result = search_core(searcher, board, nodes);
                if (result.depth > 0) {
                    std::cout << "info depth " << result.depth << " score ";
                    if (forge::is_mate_score(result.score)) {
                        const int distance = forge::MateValue - std::abs(result.score);
                        const int mate = (distance + 1) / 2;
                        std::cout << "mate " << (result.score < 0 ? -mate : mate);
                    } else std::cout << "cp " << result.score;
                    std::cout << " nodes " << result.nodes << '\n';
                }
                std::cout << "bestmove " << (result.best_move.from == result.best_move.to
                    ? "0000" : forge::Board::move_to_uci(result.best_move)) << '\n';
            } else if (verb == "game") {
                if (!opponent) throw std::runtime_error("game requires coordinator mode");
                native_game(command, searcher, *opponent);
            } else if (verb == "quit") {
                return opponent ? opponent->close() : 0;
            } else if (!verb.empty()) {
                throw std::runtime_error("unsupported command: " + verb);
            }
            std::cout.flush();
        }
    } catch (const std::exception& error) {
        std::cerr << "native generator adapter failed: " << error.what() << '\n';
        return 1;
    }
    return opponent ? opponent->close() : 0;
}
