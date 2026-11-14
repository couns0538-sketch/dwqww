// Short-clock match of two UCI engines. Reports time losses, illegal moves,
// and crashes for each side. Concurrency is the number of games in flight.

#include "forge/board.hpp"

#include <atomic>
#include <chrono>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <poll.h>
#include <signal.h>
#include <string>
#include <sys/wait.h>
#include <thread>
#include <unistd.h>
#include <vector>

namespace {

struct Tally {
    int time_losses = 0;
    int illegal = 0;
    int crashes = 0;
};

struct Engine {
    std::string path;
    pid_t pid = -1;
    int in_fd = -1;
    int out_fd = -1;
    std::string pending;
    bool alive = false;
};

[[nodiscard]] bool write_all(int fd, const std::string& text) {
    const char* data = text.data();
    std::size_t left = text.size();
    while (left > 0) {
        const ssize_t wrote = ::write(fd, data, left);
        if (wrote < 0) {
            if (errno == EINTR) continue;
            return false;
        }
        data += wrote;
        left -= static_cast<std::size_t>(wrote);
    }
    return true;
}

void stop_engine(Engine& engine) {
    if (engine.pid > 0) {
        kill(engine.pid, SIGKILL);
        int status = 0;
        waitpid(engine.pid, &status, 0);
        engine.pid = -1;
    }
    if (engine.in_fd >= 0) {
        close(engine.in_fd);
        engine.in_fd = -1;
    }
    if (engine.out_fd >= 0) {
        close(engine.out_fd);
        engine.out_fd = -1;
    }
    engine.pending.clear();
    engine.alive = false;
}

[[nodiscard]] bool read_line(Engine& engine, std::string& line, int timeout_ms) {
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
    while (true) {
        const auto split = engine.pending.find('\n');
        if (split != std::string::npos) {
            line = engine.pending.substr(0, split);
            if (!line.empty() && line.back() == '\r') line.pop_back();
            engine.pending.erase(0, split + 1);
            return true;
        }
        const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
                              deadline - std::chrono::steady_clock::now())
                              .count();
        if (left <= 0) return false;
        pollfd pfd{};
        pfd.fd = engine.out_fd;
        pfd.events = POLLIN;
        const int ready = poll(&pfd, 1, static_cast<int>(left));
        if (ready < 0) {
            if (errno == EINTR) continue;
            return false;
        }
        if (ready == 0) return false;
        char buffer[4096];
        const ssize_t got = ::read(engine.out_fd, buffer, sizeof buffer);
        if (got <= 0) return false;
        engine.pending.append(buffer, buffer + got);
    }
}

[[nodiscard]] bool wait_for(Engine& engine, const std::string& prefix, int timeout_ms) {
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
    std::string line;
    while (true) {
        const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
                              deadline - std::chrono::steady_clock::now())
                              .count();
        if (left <= 0) return false;
        if (!read_line(engine, line, static_cast<int>(left))) return false;
        if (line.rfind(prefix, 0) == 0) return true;
    }
}

[[nodiscard]] bool start_engine(Engine& engine) {
    stop_engine(engine);
    int to_child[2] = {-1, -1};
    int from_child[2] = {-1, -1};
    if (pipe(to_child) != 0 || pipe(from_child) != 0) {
        if (to_child[0] >= 0) {
            close(to_child[0]);
            close(to_child[1]);
        }
        return false;
    }
    const pid_t pid = fork();
    if (pid < 0) {
        close(to_child[0]);
        close(to_child[1]);
        close(from_child[0]);
        close(from_child[1]);
        return false;
    }
    if (pid == 0) {
        dup2(to_child[0], STDIN_FILENO);
        dup2(from_child[1], STDOUT_FILENO);
        int devnull = open("/dev/null", O_WRONLY);
        if (devnull >= 0) dup2(devnull, STDERR_FILENO);
        close(to_child[0]);
        close(to_child[1]);
        close(from_child[0]);
        close(from_child[1]);
        if (devnull >= 0) close(devnull);
        execl(engine.path.c_str(), engine.path.c_str(), static_cast<char*>(nullptr));
        _exit(127);
    }
    close(to_child[0]);
    close(from_child[1]);
    engine.pid = pid;
    engine.in_fd = to_child[1];
    engine.out_fd = from_child[0];
    engine.pending.clear();
    engine.alive = true;
    if (!write_all(engine.in_fd, "uci\n") || !wait_for(engine, "uciok", 10000)) {
        stop_engine(engine);
        return false;
    }
    const char* setup =
        "setoption name OwnBook value false\n"
        "setoption name Threads value 1\n"
        "setoption name Hash value 16\n"
        "setoption name Move Overhead value 10\n"
        "isready\n";
    if (!write_all(engine.in_fd, setup) || !wait_for(engine, "readyok", 10000)) {
        stop_engine(engine);
        return false;
    }
    return true;
}

[[nodiscard]] std::string best_move_token(const std::string& line) {
    std::size_t start = std::string("bestmove").size();
    while (start < line.size() && line[start] == ' ') ++start;
    std::size_t end = start;
    while (end < line.size() && line[end] != ' ') ++end;
    return line.substr(start, end - start);
}

enum class EndKind { Playing, Time, Illegal, Crash, Done };

struct Side {
    Engine* engine = nullptr;
    Tally* tally = nullptr;
    int clock_ms = 0;
};

void finish_game(Side& failed, EndKind kind) {
    if (kind == EndKind::Time) ++failed.tally->time_losses;
    else if (kind == EndKind::Illegal) ++failed.tally->illegal;
    else if (kind == EndKind::Crash) ++failed.tally->crashes;
}

[[nodiscard]] EndKind play_one(Side white, Side black, int base_ms, int inc_ms, const std::vector<std::string>& opening,
                                 int& plies_played) {
    plies_played = 0;
    white.clock_ms = base_ms;
    black.clock_ms = base_ms;
    for (Side* side : {&white, &black}) {
        if (!side->engine->alive && !start_engine(*side->engine)) {
            finish_game(*side, EndKind::Crash);
            return EndKind::Crash;
        }
        if (!write_all(side->engine->in_fd, "ucinewgame\nisready\n") || !wait_for(*side->engine, "readyok", 10000)) {
            finish_game(*side, EndKind::Crash);
            stop_engine(*side->engine);
            return EndKind::Crash;
        }
    }
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) return EndKind::Done;
    std::string moves;
    for (const std::string& uci : opening) {
        const auto parsed = board.parse_uci(uci);
        if (!parsed || !board.is_legal(*parsed)) return EndKind::Done;
        forge::Undo undo;
        if (!board.make_move(*parsed, undo)) return EndKind::Done;
        if (!moves.empty()) moves += ' ';
        moves += uci;
    }
    plies_played = static_cast<int>(opening.size());
    for (int ply = 0; ply < 240; ++ply) {
        if (!board.has_legal_move()) return EndKind::Done;
        if (board.halfmove_clock() >= 100 || board.is_insufficient_material() || board.is_repetition()) return EndKind::Done;
        Side& side = board.side_to_move() == forge::White ? white : black;
        std::string command = "position startpos";
        if (!moves.empty()) command += " moves " + moves;
        command += "\ngo wtime " + std::to_string(white.clock_ms) + " btime " + std::to_string(black.clock_ms) +
                   " winc " + std::to_string(inc_ms) + " binc " + std::to_string(inc_ms) + "\n";
        const auto started = std::chrono::steady_clock::now();
        if (!write_all(side.engine->in_fd, command)) {
            finish_game(side, EndKind::Crash);
            stop_engine(*side.engine);
            return EndKind::Crash;
        }
        const int budget = side.clock_ms + 3000;
        std::string line;
        bool got = false;
        const auto deadline = started + std::chrono::milliseconds(budget);
        while (std::chrono::steady_clock::now() < deadline) {
            const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
                                  deadline - std::chrono::steady_clock::now())
                                  .count();
            if (left <= 0) break;
            if (!read_line(*side.engine, line, static_cast<int>(left))) break;
            if (line.rfind("bestmove", 0) == 0) {
                got = true;
                break;
            }
        }
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
                                 std::chrono::steady_clock::now() - started)
                                 .count();
        if (!got) {
            finish_game(side, EndKind::Time);
            stop_engine(*side.engine);
            return EndKind::Time;
        }
        if (elapsed > side.clock_ms) {
            finish_game(side, EndKind::Time);
            return EndKind::Time;
        }
        side.clock_ms = static_cast<int>(side.clock_ms - elapsed + inc_ms);
        const std::string token = best_move_token(line);
        const auto parsed = board.parse_uci(token);
        if (!parsed || !board.is_legal(*parsed)) {
            finish_game(side, EndKind::Illegal);
            return EndKind::Illegal;
        }
        forge::Undo undo;
        if (!board.make_move(*parsed, undo)) {
            finish_game(side, EndKind::Illegal);
            return EndKind::Illegal;
        }
        if (!moves.empty()) moves += ' ';
        moves += token;
        ++plies_played;
    }
    return EndKind::Done;
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 7) {
        std::cerr << "usage: short_clock_match <new> <base> <base_ms> <inc_ms> <games> <concurrency>\n";
        return 2;
    }
    signal(SIGPIPE, SIG_IGN);
    const std::string new_path = argv[1];
    const std::string base_path = argv[2];
    const int base_ms = std::stoi(argv[3]);
    const int inc_ms = std::stoi(argv[4]);
    const int games = std::stoi(argv[5]);
    const int concurrency = std::stoi(argv[6]);
    const std::vector<std::vector<std::string>> openings = {
        {},
        {"e2e4", "e7e5"},
        {"d2d4", "d7d5"},
        {"c2c4", "e7e5"},
        {"g1f3", "g8f6"},
        {"e2e4", "c7c5"},
        {"d2d4", "g8f6"},
        {"c2c4", "c7c5"},
    };
    std::atomic<int> next{0};
    std::atomic<long long> ply_sum{0};
    std::vector<Tally> fresh(static_cast<std::size_t>(concurrency));
    std::vector<Tally> base(static_cast<std::size_t>(concurrency));
    std::vector<std::thread> workers;
    workers.reserve(static_cast<std::size_t>(concurrency));
    for (int worker = 0; worker < concurrency; ++worker) {
        workers.emplace_back([&, worker]() {
            Engine neu;
            Engine old;
            neu.path = new_path;
            old.path = base_path;
            if (!start_engine(neu) || !start_engine(old)) {
                fresh[static_cast<std::size_t>(worker)].crashes += 1;
                stop_engine(neu);
                stop_engine(old);
                return;
            }
            while (true) {
                const int id = next.fetch_add(1);
                if (id >= games) break;
                const bool new_is_white = (id % 2) == 0;
                Side white;
                Side black;
                white.engine = new_is_white ? &neu : &old;
                black.engine = new_is_white ? &old : &neu;
                white.tally = new_is_white ? &fresh[static_cast<std::size_t>(worker)] : &base[static_cast<std::size_t>(worker)];
                black.tally = new_is_white ? &base[static_cast<std::size_t>(worker)] : &fresh[static_cast<std::size_t>(worker)];
                int plies = 0;
                (void)play_one(white, black, base_ms, inc_ms, openings[static_cast<std::size_t>(id) % openings.size()],
                               plies);
                ply_sum.fetch_add(plies);
                if ((id + 1) % 50 == 0) {
                    std::cerr << "played " << (id + 1) << "\n";
                }
            }
            const bool quit_new = !neu.alive || write_all(neu.in_fd, "quit\n");
            const bool quit_old = !old.alive || write_all(old.in_fd, "quit\n");
            (void)quit_new;
            (void)quit_old;
            stop_engine(neu);
            stop_engine(old);
        });
    }
    for (auto& worker : workers) worker.join();
    Tally neu;
    Tally old;
    for (int worker = 0; worker < concurrency; ++worker) {
        neu.time_losses += fresh[static_cast<std::size_t>(worker)].time_losses;
        neu.illegal += fresh[static_cast<std::size_t>(worker)].illegal;
        neu.crashes += fresh[static_cast<std::size_t>(worker)].crashes;
        old.time_losses += base[static_cast<std::size_t>(worker)].time_losses;
        old.illegal += base[static_cast<std::size_t>(worker)].illegal;
        old.crashes += base[static_cast<std::size_t>(worker)].crashes;
    }
    std::cout << "games " << games << " base_ms " << base_ms << " inc_ms " << inc_ms << " mean_plies "
              << (games > 0 ? static_cast<double>(ply_sum.load()) / games : 0) << "\n";
    std::cout << "new time_losses " << neu.time_losses << " illegal " << neu.illegal << " crashes " << neu.crashes
              << "\n";
    std::cout << "base time_losses " << old.time_losses << " illegal " << old.illegal << " crashes " << old.crashes
              << "\n";
    return 0;
}
