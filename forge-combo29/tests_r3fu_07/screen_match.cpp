#include "forge/board.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <mutex>
#include <poll.h>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>
#include <vector>
#include <array>
#include <chrono>
#include <cerrno>

namespace {

constexpr int kNodes = 50000;
constexpr double kNormal95 = 1.959963984540054;

struct Engine {
    pid_t pid = -1;
    int to_child = -1;
    int from_child = -1;
    std::string pending;

    Engine() = default;
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;

    ~Engine() { stop(); }

    void stop() {
        if (to_child >= 0) {
            close(to_child);
            to_child = -1;
        }
        if (from_child >= 0) {
            close(from_child);
            from_child = -1;
        }
        if (pid > 0) {
            kill(pid, SIGTERM);
            int status = 0;
            waitpid(pid, &status, 0);
            pid = -1;
        }
    }

    void start(const std::string& path) {
        int in_pipe[2];
        int out_pipe[2];
        if (pipe(in_pipe) != 0 || pipe(out_pipe) != 0) throw std::runtime_error("pipe");
        const pid_t child = fork();
        if (child < 0) throw std::runtime_error("fork");
        if (child == 0) {
            dup2(in_pipe[0], STDIN_FILENO);
            dup2(out_pipe[1], STDOUT_FILENO);
            close(in_pipe[0]);
            close(in_pipe[1]);
            close(out_pipe[0]);
            close(out_pipe[1]);
            execl(path.c_str(), path.c_str(), static_cast<char*>(nullptr));
            _exit(127);
        }
        close(in_pipe[0]);
        close(out_pipe[1]);
        pid = child;
        to_child = in_pipe[1];
        from_child = out_pipe[0];
    }

    void send(const std::string& line) {
        std::string text = line;
        text.push_back('\n');
        const char* data = text.data();
        std::size_t left = text.size();
        while (left > 0) {
            const ssize_t wrote = write(to_child, data, left);
            if (wrote < 0 && errno == EINTR) continue;
            if (wrote <= 0) throw std::runtime_error("engine write failed");
            data += wrote;
            left -= static_cast<std::size_t>(wrote);
        }
    }

    // Empty string means the wait timed out or the process closed the pipe.
    std::string read_line(int timeout_ms) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
        while (true) {
            const auto split = pending.find('\n');
            if (split != std::string::npos) {
                std::string line = pending.substr(0, split);
                pending.erase(0, split + 1);
                if (!line.empty() && line.back() == '\r') line.pop_back();
                return line;
            }
            const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
                deadline - std::chrono::steady_clock::now()).count();
            if (left <= 0) return {};
            pollfd watch{};
            watch.fd = from_child;
            watch.events = POLLIN;
            const int ready = poll(&watch, 1, static_cast<int>(left));
            if (ready <= 0) return {};
            char buffer[4096];
            const ssize_t got = read(from_child, buffer, sizeof buffer);
            if (got <= 0) return {};
            pending.append(buffer, static_cast<std::size_t>(got));
        }
    }

    bool wait_token(const std::string& token, int timeout_ms) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
        while (std::chrono::steady_clock::now() < deadline) {
            const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
                deadline - std::chrono::steady_clock::now()).count();
            const std::string line = read_line(static_cast<int>(std::max<std::int64_t>(left, 1)));
            if (line.empty()) return false;
            if (line.rfind(token, 0) == 0) return true;
        }
        return false;
    }

    std::string best_move(int timeout_ms) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
        while (std::chrono::steady_clock::now() < deadline) {
            const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
                deadline - std::chrono::steady_clock::now()).count();
            const std::string line = read_line(static_cast<int>(std::max<std::int64_t>(left, 1)));
            if (line.empty()) return {};
            if (line.rfind("bestmove ", 0) == 0) {
                std::istringstream input(line.substr(9));
                std::string move;
                input >> move;
                return move;
            }
        }
        return {};
    }
};

struct Slot {
    Engine on;
    Engine off;
};

std::string capture_command(const std::string& command) {
    FILE* pipe = popen(command.c_str(), "r");
    if (pipe == nullptr) return {};
    std::string output;
    char buffer[512];
    while (fgets(buffer, sizeof buffer, pipe) != nullptr) output += buffer;
    pclose(pipe);
    while (!output.empty() && (output.back() == '\n' || output.back() == '\r')) output.pop_back();
    return output;
}

std::string fen_of_epd(const std::string& line) {
    std::istringstream input(line);
    std::string fields[6];
    for (int i = 0; i < 6; ++i) input >> fields[i];
    if (fields[0].empty() || fields[1].empty() || fields[2].empty() || fields[3].empty()) return {};
    const auto digits = [](const std::string& text) {
        return !text.empty() && std::all_of(text.begin(), text.end(), [](unsigned char ch) { return std::isdigit(ch) != 0; });
    };
    if (digits(fields[4]) && digits(fields[5])) {
        return fields[0] + " " + fields[1] + " " + fields[2] + " " + fields[3] + " " + fields[4] + " " + fields[5];
    }
    return fields[0] + " " + fields[1] + " " + fields[2] + " " + fields[3] + " 0 1";
}

std::vector<std::string> load_fens(const std::string& path, int start_pair, int pair_count) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open book");
    std::vector<std::string> fens;
    fens.reserve(static_cast<std::size_t>(pair_count));
    std::string line;
    int index = 0;
    const int begin = start_pair;
    const int end = start_pair + pair_count;
    while (std::getline(input, line)) {
        if (line.empty() || line[0] == '#') continue;
        if (index >= begin && index < end) {
            const std::string fen = fen_of_epd(line);
            if (fen.empty()) throw std::runtime_error("bad epd");
            fens.push_back(fen);
        }
        ++index;
        if (index >= end) break;
    }
    if (static_cast<int>(fens.size()) != pair_count) throw std::runtime_error("book ended before the chunk");
    return fens;
}

std::string square_name(int square) {
    std::string text;
    text += static_cast<char>('a' + forge::file_of(square));
    text += static_cast<char>('1' + forge::rank_of(square));
    return text;
}

std::string san(const forge::Board& board, const forge::Move& move) {
    if (move.is_castle()) return (move.flags & forge::KingCastle) != 0 ? "O-O" : "O-O-O";
    const int type = forge::piece_type(board.moved_piece(move));
    const forge::MoveList legal = board.legal_moves();
    std::string text;
    if (type != forge::Pawn) {
        text += " PNBRQK"[type];
        bool other = false;
        bool same_file = false;
        bool same_rank = false;
        for (const forge::Move& candidate : legal) {
            if (candidate.to != move.to || candidate.from == move.from) continue;
            if (forge::piece_type(board.moved_piece(candidate)) != type) continue;
            other = true;
            if (forge::file_of(candidate.from) == forge::file_of(move.from)) same_file = true;
            if (forge::rank_of(candidate.from) == forge::rank_of(move.from)) same_rank = true;
        }
        if (other) {
            if (!same_file) text += static_cast<char>('a' + forge::file_of(move.from));
            else if (!same_rank) text += static_cast<char>('1' + forge::rank_of(move.from));
            else {
                text += static_cast<char>('a' + forge::file_of(move.from));
                text += static_cast<char>('1' + forge::rank_of(move.from));
            }
        }
    } else if (move.is_capture()) {
        text += static_cast<char>('a' + forge::file_of(move.from));
    }
    if (move.is_capture()) text += 'x';
    text += square_name(move.to);
    if (move.is_promotion()) text += std::string("=") + " PNBRQK"[move.promotion];
    forge::Board next = board;
    forge::Undo undo;
    if (!next.make_move(move, undo)) return text;
    if (next.in_check()) text += next.legal_moves().empty() ? '#' : '+';
    return text;
}

enum class Ending { Ongoing, WhiteWin, BlackWin, Draw };

struct GameResult {
    std::string pgn;
    int on_points_twice = 0; // 0, 1, or 2 (draw is 1) so a pair can sum without floats
    bool on_white = false;
    std::string termination;
};

Ending finished(const forge::Board& board) {
    if (board.legal_moves().empty()) return board.in_check() ? (board.side_to_move() == forge::White ? Ending::BlackWin : Ending::WhiteWin) : Ending::Draw;
    if (board.is_repetition() || board.halfmove_clock() >= 100 || board.is_insufficient_material()) return Ending::Draw;
    return Ending::Ongoing;
}

const char* result_tag(Ending ending) {
    if (ending == Ending::WhiteWin) return "1-0";
    if (ending == Ending::BlackWin) return "0-1";
    return "1/2-1/2";
}

int on_points(Ending ending, bool on_white) {
    if (ending == Ending::Draw) return 1;
    const bool white_won = ending == Ending::WhiteWin;
    return white_won == on_white ? 2 : 0;
}

GameResult play_game(Engine& on, Engine& off, const std::string& fen, bool on_white, int round_number) {
    GameResult result;
    result.on_white = on_white;
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        result.termination = "illegal fen";
        result.on_points_twice = 0;
        result.pgn = "[Result \"*\"]\n\n*\n";
        return result;
    }
    on.send("ucinewgame");
    off.send("ucinewgame");
    on.send("isready");
    off.send("isready");
    if (!on.wait_token("readyok", 20000) || !off.wait_token("readyok", 20000)) {
        result.termination = "engine not ready";
        result.on_points_twice = 0;
        result.pgn = "[Result \"*\"]\n\n*\n";
        return result;
    }
    std::vector<std::string> moves;
    Ending ending = Ending::Ongoing;
    std::string termination = "normal";
    for (int ply = 0; ply < 1000 && ending == Ending::Ongoing; ++ply) {
        ending = finished(board);
        if (ending != Ending::Ongoing) break;
        const bool white = board.side_to_move() == forge::White;
        Engine& mover = (white == on_white) ? on : off;
        mover.send("position fen " + board.fen());
        mover.send("go nodes " + std::to_string(kNodes));
        const std::string uci = mover.best_move(120000);
        const auto parsed = board.parse_uci(uci);
        if (!parsed.has_value()) {
            ending = white ? Ending::BlackWin : Ending::WhiteWin;
            termination = "illegal move " + uci;
            break;
        }
        moves.push_back(san(board, *parsed));
        forge::Undo undo;
        if (!board.make_move(*parsed, undo)) {
            ending = white ? Ending::BlackWin : Ending::WhiteWin;
            termination = "rejected move " + uci;
            break;
        }
    }
    if (ending == Ending::Ongoing) {
        ending = Ending::Draw;
        termination = "ply cap";
    }
    result.termination = termination;
    result.on_points_twice = on_points(ending, on_white);
    std::ostringstream pgn;
    pgn << "[Event \"NullSeeVeto equal-node screen\"]\n";
    pgn << "[Site \"local\"]\n";
    pgn << "[Date \"2026.11.14\"]\n";
    pgn << "[Round \"" << round_number << "\"]\n";
    pgn << "[White \"" << (on_white ? "NullSeeVeto on" : "NullSeeVeto off") << "\"]\n";
    pgn << "[Black \"" << (on_white ? "NullSeeVeto off" : "NullSeeVeto on") << "\"]\n";
    pgn << "[Result \"" << result_tag(ending) << "\"]\n";
    pgn << "[FEN \"" << fen << "\"]\n";
    pgn << "[SetUp \"1\"]\n";
    pgn << "[Termination \"" << termination << "\"]\n";
    pgn << "[Nodes \"" << kNodes << "\"]\n\n";
    for (std::size_t i = 0; i < moves.size(); ++i) {
        if (i % 2 == 0) pgn << (i / 2 + 1) << ". ";
        pgn << moves[i];
        if (i + 1 == moves.size() || i % 2 == 1) pgn << ' ';
        else pgn << ' ';
    }
    pgn << result_tag(ending) << "\n\n";
    result.pgn = pgn.str();
    return result;
}

void boot(Engine& engine, const std::string& path, bool veto) {
    engine.start(path);
    engine.send("uci");
    if (!engine.wait_token("uciok", 10000)) throw std::runtime_error("uciok missing");
    engine.send("setoption name Threads value 1");
    engine.send("setoption name Hash value 16");
    engine.send("setoption name OwnBook value false");
    engine.send(std::string("setoption name NullSeeVeto value ") + (veto ? "true" : "false"));
    engine.send("isready");
    if (!engine.wait_token("readyok", 20000)) throw std::runtime_error("readyok missing");
}

struct Tally {
    int wins = 0;
    int losses = 0;
    int draws = 0;
    std::array<int, 5> pairs{};
    std::mutex mutex;
};

void add_pair(Tally& tally, int first, int second) {
    const int sum = first + second;
    const int bin = sum / 1; // 0,1,2,3,4 because each game stores 0, 1, or 2
    if (bin < 0 || bin > 4) return;
    if (sum == 4) ++tally.wins, ++tally.wins;
    else if (sum == 0) ++tally.losses, ++tally.losses;
    else {
        // Decode the two game points back into W/L/D.
        for (const int points : {first, second}) {
            if (points == 2) ++tally.wins;
            else if (points == 0) ++tally.losses;
            else ++tally.draws;
        }
    }
    ++tally.pairs[static_cast<std::size_t>(sum)];
}

std::string statistics_text(const Tally& tally, const std::string& command, const std::string& versions) {
    const int games = tally.wins + tally.losses + tally.draws;
    const int pair_count = tally.pairs[0] + tally.pairs[1] + tally.pairs[2] + tally.pairs[3] + tally.pairs[4];
    double pair_sum = 0;
    std::vector<double> scores;
    scores.reserve(static_cast<std::size_t>(pair_count));
    for (int bin = 0; bin < 5; ++bin) {
        const double per_game = bin / 4.0; // pair points 0..4 map to a per-game score 0..1
        for (int n = 0; n < tally.pairs[static_cast<std::size_t>(bin)]; ++n) {
            scores.push_back(per_game);
            pair_sum += per_game;
        }
    }
    double elo = 0;
    double low = 0;
    double high = 0;
    double los = 0.5;
    bool elo_known = false;
    if (pair_count >= 2 && !scores.empty()) {
        elo_known = true;
        const double mean = pair_sum / static_cast<double>(pair_count);
        double square = 0;
        for (const double score : scores) {
            const double delta = score - mean;
            square += delta * delta;
        }
        const double variance = square / static_cast<double>(pair_count - 1);
        const double error = std::sqrt(variance / static_cast<double>(pair_count));
        if (mean <= 0.0) {
            elo = -10000;
            low = -10000;
            high = -10000;
            los = 0;
        } else if (mean >= 1.0) {
            elo = 10000;
            low = 10000;
            high = 10000;
            los = 1;
        } else if (error == 0.0) {
            elo = -400.0 * std::log10(1.0 / mean - 1.0);
            low = elo;
            high = elo;
            los = mean > 0.5 ? 1.0 : (mean < 0.5 ? 0.0 : 0.5);
        } else {
            elo = -400.0 * std::log10(1.0 / mean - 1.0);
            const double slope = (400.0 / std::log(10.0)) / (mean * (1.0 - mean));
            const double margin = kNormal95 * slope * error;
            low = elo - margin;
            high = elo + margin;
            const double z = (mean - 0.5) / error;
            los = 0.5 * (1.0 + std::erf(z / std::sqrt(2.0)));
        }
    }
    std::ostringstream out;
    out.setf(std::ios::fixed);
    out.precision(2);
    out << "screen: equal nodes, same binary, NullSeeVeto on versus off\n";
    out << "not a strength claim\n";
    out << "W-L-D option on first: " << tally.wins << "-" << tally.losses << "-" << tally.draws << "\n";
    out << "games: " << games << "\n";
    out << "pairs: " << pair_count << "\n";
    if (elo_known) out << "Elo 95%: " << elo << " [" << low << ", " << high << "]\n";
    else out << "Elo 95%: n/a (need at least 2 pairs)\n";
    out.precision(4);
    out << "LOS: " << los << "\n";
    out << "pentanomial (on-engine pair points 0, 0.5, 1, 1.5, 2): "
        << tally.pairs[0] << ", " << tally.pairs[1] << ", " << tally.pairs[2] << ", "
        << tally.pairs[3] << ", " << tally.pairs[4] << "\n";
    out << "The middle bin is a pair score of 1, which is two draws or a win and a loss.\n";
    out << "command: " << command << "\n";
    out << versions << "\n";
    return out.str();
}

void run_chunk(const std::string& engine, const std::string& book, int start_pair, int pair_count,
               int concurrency, const std::string& pgn_path, const std::string& summary_path,
               const std::string& command) {
    const std::vector<std::string> fens = load_fens(book, start_pair, pair_count);
    std::vector<Slot> slots(static_cast<std::size_t>(concurrency));
    for (Slot& slot : slots) {
        boot(slot.on, engine, true);
        boot(slot.off, engine, false);
    }
    Tally tally;
    std::ofstream pgn(pgn_path);
    if (!pgn) throw std::runtime_error("cannot write pgn");
    std::mutex pgn_mutex;
    std::vector<std::thread> threads;
    for (int slot_index = 0; slot_index < concurrency; ++slot_index) {
        threads.emplace_back([&, slot_index]() {
            for (int pair = slot_index; pair < pair_count; pair += concurrency) {
                const GameResult white = play_game(slots[static_cast<std::size_t>(slot_index)].on,
                                                    slots[static_cast<std::size_t>(slot_index)].off,
                                                    fens[static_cast<std::size_t>(pair)], true, start_pair + pair);
                const GameResult black = play_game(slots[static_cast<std::size_t>(slot_index)].on,
                                                    slots[static_cast<std::size_t>(slot_index)].off,
                                                    fens[static_cast<std::size_t>(pair)], false, start_pair + pair);
                const std::lock_guard<std::mutex> lock(pgn_mutex);
                pgn << white.pgn << black.pgn;
                add_pair(tally, white.on_points_twice, black.on_points_twice);
            }
        });
    }
    for (std::thread& thread : threads) thread.join();
    pgn.close();
    const std::string versions =
        "engine sha256: " + capture_command("sha256sum " + engine + " | cut -d' ' -f1") + "\n" +
        "book sha256: " + capture_command("sha256sum " + book + " | cut -d' ' -f1") + "\n" +
        "compiler: " + capture_command("c++ --version | head -n 1") + "\n" +
        "id: " + capture_command("printf 'uci\\nquit\\n' | " + engine + " | head -n 1");
    std::ofstream summary(summary_path);
    summary << statistics_text(tally, command, versions);
}

std::string bench_once(const std::string& engine, bool veto) {
    Engine child;
    boot(child, engine, veto);
    child.send("bench 13");
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(120);
    while (std::chrono::steady_clock::now() < deadline) {
        const std::string line = child.read_line(120000);
        if (line.rfind("info string bench depth 13 ", 0) == 0) return line;
        if (line.empty()) break;
    }
    return "bench failed";
}

void run_bench(const std::string& engine, const std::string& path) {
    std::ofstream out(path);
    out << "bench 13 nodes per second, five alternating runs, same binary\n";
    out << "order: off on off on off on off on off on\n";
    out << "not a strength claim\n";
    for (int run = 0; run < 5; ++run) {
        out << "off " << (run + 1) << ": " << bench_once(engine, false) << "\n";
        out << "on " << (run + 1) << ": " << bench_once(engine, true) << "\n";
    }
}

}  // namespace

int main(int argc, char** argv) {
    signal(SIGPIPE, SIG_IGN);
    try {
        if (argc >= 2 && std::string(argv[1]) == "bench") {
            if (argc != 4) {
                std::cerr << "usage: screen_match bench <engine> <out.txt>\n";
                return 2;
            }
            run_bench(argv[2], argv[3]);
            return 0;
        }
        if (argc != 8) {
            std::cerr << "usage: screen_match <engine> <epd> <start_pair> <pair_count> <concurrency> <pgn> <summary>\n";
            return 2;
        }
        const std::string engine = argv[1];
        const std::string book = argv[2];
        const int start_pair = std::stoi(argv[3]);
        const int pair_count = std::stoi(argv[4]);
        const int concurrency = std::stoi(argv[5]);
        std::ostringstream command;
        for (int i = 0; i < argc; ++i) {
            if (i != 0) command << ' ';
            command << argv[i];
        }
        run_chunk(engine, book, start_pair, pair_count, concurrency, argv[6], argv[7], command.str());
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "screen_match: " << error.what() << "\n";
        return 1;
    }
}
