#include "forge/board.hpp"

#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cerrno>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

#include <poll.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

// Drives the engine over UCI. `softnodes` checks 200 positions:
// searched nodes lie in [N, 4N], and the move matches `go depth D`
// for the depth of the last finished iteration. `depth10` checks that
// 200 searches to depth 10 each return a legal move.

namespace {

constexpr int kPositions = 200;
constexpr std::uint64_t kSoft = 1000;

class Engine {
public:
    explicit Engine(const std::string& path) {
        int to_child[2];
        int from_child[2];
        if (pipe(to_child) != 0 || pipe(from_child) != 0) fail("pipe");
        pid_ = fork();
        if (pid_ < 0) fail("fork");
        if (pid_ == 0) {
            dup2(to_child[0], STDIN_FILENO);
            dup2(from_child[1], STDOUT_FILENO);
            close(to_child[0]);
            close(to_child[1]);
            close(from_child[0]);
            close(from_child[1]);
            execl(path.c_str(), path.c_str(), static_cast<char*>(nullptr));
            _exit(127);
        }
        close(to_child[0]);
        close(from_child[1]);
        write_fd_ = to_child[1];
        read_fd_ = from_child[0];
    }

    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;

    ~Engine() {
        if (pid_ > 0) (void)finish();
    }

    int finish() {
        if (pid_ <= 0) return 0;
        send("quit\n");
        close(write_fd_);
        close(read_fd_);
        write_fd_ = -1;
        read_fd_ = -1;
        int status = 0;
        waitpid(pid_, &status, 0);
        pid_ = -1;
        return status;
    }

    void send(const std::string& text) {
        const char* data = text.data();
        std::size_t left = text.size();
        while (left > 0) {
            const ssize_t wrote = ::write(write_fd_, data, left);
            if (wrote < 0) {
                if (errno == EINTR) continue;
                fail("write");
            }
            data += wrote;
            left -= static_cast<std::size_t>(wrote);
        }
    }

    bool read_line(std::string& line, std::chrono::steady_clock::time_point deadline) {
        for (;;) {
            const auto split = pending_.find('\n');
            if (split != std::string::npos) {
                line = pending_.substr(0, split);
                if (!line.empty() && line.back() == '\r') line.pop_back();
                pending_.erase(0, split + 1);
                return true;
            }
            const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
                deadline - std::chrono::steady_clock::now());
            if (left.count() <= 0) return false;
            pollfd pfd{};
            pfd.fd = read_fd_;
            pfd.events = POLLIN;
            const int polled = ::poll(&pfd, 1, static_cast<int>(left.count()));
            if (polled < 0) {
                if (errno == EINTR) continue;
                return false;
            }
            if (polled == 0) return false;
            char buffer[4096];
            const ssize_t got = ::read(read_fd_, buffer, sizeof buffer);
            if (got < 0) {
                if (errno == EINTR) continue;
                return false;
            }
            if (got == 0) return false;
            pending_.append(buffer, buffer + got);
        }
    }

    bool wait_ready(int timeout_ms) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
        std::string line;
        while (read_line(line, deadline)) {
            if (line == "readyok") return true;
        }
        return false;
    }

private:
    [[noreturn]] void fail(const char* what) {
        std::cerr << "engine io " << what << std::endl;
        std::exit(2);
    }

    pid_t pid_ = -1;
    int write_fd_ = -1;
    int read_fd_ = -1;
    std::string pending_;
};

struct GoResult {
    bool ok = false;
    std::string best;
    int depth = -1;
    std::string score;
    std::uint64_t info_nodes = 0;
    std::uint64_t soft_nodes = 0;
    bool saw_soft = false;
};

void note_info(const std::string& line, GoResult& result) {
    constexpr std::string_view kSoft = "info string softnodes nodes ";
    if (line.compare(0, kSoft.size(), kSoft) == 0) {
        result.soft_nodes = std::strtoull(line.c_str() + kSoft.size(), nullptr, 10);
        result.saw_soft = true;
        return;
    }
    if (line.compare(0, 5, "info ") != 0 || line.compare(0, 11, "info string") == 0) return;
    std::istringstream input(line);
    std::string token;
    input >> token;
    while (input >> token) {
        if (token == "depth") {
            input >> result.depth;
        } else if (token == "score") {
            std::string kind;
            std::string value;
            input >> kind >> value;
            result.score = kind + " " + value;
        } else if (token == "nodes") {
            input >> result.info_nodes;
        } else if (token == "pv") {
            break;
        }
    }
}

GoResult wait_bestmove(Engine& engine, int timeout_ms) {
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
    GoResult result;
    std::string line;
    while (engine.read_line(line, deadline)) {
        if (line.compare(0, 9, "bestmove ") == 0) {
            std::istringstream input(line);
            std::string tag;
            input >> tag >> result.best;
            result.ok = !result.best.empty();
            return result;
        }
        note_info(line, result);
    }
    return result;
}

std::uint64_t mix(std::uint64_t& state) {
    state = state * 6364136223846793005ULL + 1ULL;
    return state;
}

std::vector<std::string> make_positions(int count) {
    std::vector<std::string> positions;
    positions.reserve(static_cast<std::size_t>(count));
    std::uint64_t state = 0x51f15e5d9aULL;
    int spins = 0;
    while (static_cast<int>(positions.size()) < count) {
        if (++spins > 200000) break;
        forge::Board board;
        if (!board.set_fen(forge::Board::StandardStartFen)) {
            std::cerr << "start fen rejected" << std::endl;
            std::exit(2);
        }
        const int plies = 6 + static_cast<int>(mix(state) % 18ULL);
        bool played = true;
        for (int ply = 0; ply < plies; ++ply) {
            const forge::MoveList moves = board.legal_moves();
            if (moves.empty()) {
                played = false;
                break;
            }
            const forge::Move chosen = moves[static_cast<std::size_t>(mix(state) % moves.size())];
            forge::Undo undo;
            if (!board.make_move(chosen, undo)) {
                played = false;
                break;
            }
        }
        if (!played) continue;
        if (board.legal_moves().empty()) continue;
        if (board.is_repetition() || board.halfmove_clock() >= 100 || board.is_insufficient_material()) continue;
        const std::string fen = board.fen();
        bool duplicate = false;
        for (const std::string& have : positions) {
            if (have == fen) duplicate = true;
        }
        if (duplicate) continue;
        positions.push_back(fen);
    }
    return positions;
}

bool move_is_legal(const std::string& fen, const std::string& uci) {
    forge::Board board;
    if (!board.set_fen(fen)) return false;
    const std::optional<forge::Move> parsed = board.parse_uci(uci);
    if (!parsed.has_value() || parsed->is_none()) return false;
    const forge::MoveList moves = board.legal_moves();
    for (std::size_t i = 0; i < moves.size(); ++i) {
        if (moves[i] == *parsed) return true;
    }
    return false;
}

void prepare(Engine& engine) {
    engine.send("uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
                "setoption name OwnBook value false\nisready\n");
    if (!engine.wait_ready(10000)) {
        std::cerr << "FAIL engine did not answer readyok" << std::endl;
        std::exit(1);
    }
}

bool fresh_position(Engine& engine, const std::string& fen) {
    engine.send("ucinewgame\nposition fen " + fen + "\nisready\n");
    return engine.wait_ready(10000);
}

int run_softnodes(const std::string& engine_path) {
    const std::vector<std::string> positions = make_positions(kPositions);
    if (static_cast<int>(positions.size()) != kPositions) {
        std::cerr << "FAIL only built " << positions.size() << " positions" << std::endl;
        return 1;
    }
    Engine engine(engine_path);
    prepare(engine);

    engine.send("ucinewgame\nposition startpos\nisready\n");
    if (!engine.wait_ready(10000)) {
        std::cerr << "FAIL startpos ready" << std::endl;
        return 1;
    }
    engine.send("go nodes 400\n");
    const GoResult hard = wait_bestmove(engine, 20000);
    if (!hard.ok || hard.saw_soft || hard.info_nodes > 400) {
        std::cerr << "FAIL go nodes changed: ok " << hard.ok << " soft " << hard.saw_soft
                  << " nodes " << hard.info_nodes << " move " << hard.best << std::endl;
        return 1;
    }
    std::cout << "go_nodes_unchanged info_nodes " << hard.info_nodes << " move " << hard.best << std::endl;

    int failures = 0;
    bool printed_sample = false;
    for (int index = 0; index < kPositions; ++index) {
        const std::string& fen = positions[static_cast<std::size_t>(index)];
        if (!fresh_position(engine, fen)) {
            std::cerr << "FAIL ready before soft " << index << std::endl;
            return 1;
        }
        engine.send("go softnodes " + std::to_string(kSoft) + "\n");
        const GoResult soft = wait_bestmove(engine, 30000);
        const std::uint64_t nodes = soft.soft_nodes;
        if (!soft.ok || !soft.saw_soft || soft.depth < 1 || nodes < kSoft || nodes > kSoft * 4 ||
            !move_is_legal(fen, soft.best)) {
            std::cerr << "FAIL soft " << index << " fen " << fen << " ok " << soft.ok
                      << " depth " << soft.depth << " nodes " << nodes << " move " << soft.best
                      << " saw " << soft.saw_soft << std::endl;
            ++failures;
            if (failures > 8) return 1;
            continue;
        }
        if (!fresh_position(engine, fen)) {
            std::cerr << "FAIL ready before depth " << index << std::endl;
            return 1;
        }
        engine.send("go depth " + std::to_string(soft.depth) + "\n");
        const GoResult fixed = wait_bestmove(engine, 30000);
        if (!fixed.ok || fixed.best != soft.best || fixed.score != soft.score || fixed.saw_soft) {
            std::cerr << "FAIL match " << index << " fen " << fen << " depth " << soft.depth
                      << " soft " << soft.best << " " << soft.score << " depthmove " << fixed.best
                      << " " << fixed.score << std::endl;
            ++failures;
            if (failures > 8) return 1;
            continue;
        }
        if (!printed_sample) {
            std::cout << "sample fen " << fen << " depth " << soft.depth << " nodes " << nodes
                      << " move " << soft.best << " score " << soft.score << std::endl;
            printed_sample = true;
        }
        if (index % 25 == 24) {
            std::cout << "progress " << (index + 1) << " last_nodes " << nodes << std::endl;
        }
    }
    const int status = engine.finish();
    if (failures != 0) {
        std::cerr << "FAIL softnodes failures " << failures << std::endl;
        return 1;
    }
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        std::cerr << "FAIL engine exit status " << status << std::endl;
        return 1;
    }
    std::cout << "SOFTNODES_PASS " << kPositions << " budget " << kSoft << std::endl;
    return 0;
}

int run_depth10(const std::string& engine_path) {
    const std::vector<std::string> positions = make_positions(kPositions);
    if (static_cast<int>(positions.size()) != kPositions) {
        std::cerr << "FAIL only built " << positions.size() << " positions" << std::endl;
        return 1;
    }
    Engine engine(engine_path);
    prepare(engine);
    int failures = 0;
    for (int index = 0; index < kPositions; ++index) {
        const std::string& fen = positions[static_cast<std::size_t>(index)];
        if (!fresh_position(engine, fen)) {
            std::cerr << "FAIL ready " << index << std::endl;
            return 1;
        }
        engine.send("go depth 10\n");
        const GoResult result = wait_bestmove(engine, 120000);
        if (!result.ok || result.depth < 10 || !move_is_legal(fen, result.best)) {
            std::cerr << "FAIL depth10 " << index << " fen " << fen << " depth " << result.depth
                      << " move " << result.best << std::endl;
            ++failures;
            if (failures > 8) return 1;
        } else if (index % 25 == 24) {
            std::cout << "legal_progress " << (index + 1) << " move " << result.best << std::endl;
        }
    }
    const int status = engine.finish();
    if (failures != 0) {
        std::cerr << "FAIL depth10 failures " << failures << std::endl;
        return 1;
    }
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        std::cerr << "FAIL engine exit status " << status << std::endl;
        return 1;
    }
    std::cout << "DEPTH10_LEGAL_PASS " << kPositions << std::endl;
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: softnodes_test <engine> <softnodes|depth10>" << std::endl;
        return 2;
    }
    const std::string path = argv[1];
    const std::string mode = argv[2];
    if (mode == "softnodes") return run_softnodes(path);
    if (mode == "depth10") return run_depth10(path);
    std::cerr << "unknown mode " << mode << std::endl;
    return 2;
}
