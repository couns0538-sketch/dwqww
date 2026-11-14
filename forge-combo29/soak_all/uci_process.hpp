#pragma once
// POSIX transport for the soak driver only. Engine source is not modified.
// Transcript prefixes distinguish submitted commands, stdout, and stderr;
// received line payloads (including CR, if present) are preserved verbatim.
#include <algorithm>
#include <cerrno>
#include <chrono>
#include <csignal>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <poll.h>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <utility>
#include <vector>

struct UciResult {
    std::string move, score_kind, score_bound, transcript, stderr_output;
    int score = 0, depth = 0;
    unsigned long long nodes = 0, reported_ms = 0;
    double wall_ms = 0.0;
    std::vector<std::string> pv;
    bool positive_mate() const { return score_kind == "mate" && score > 0; }
    bool same(const UciResult& other) const {
        return move == other.move && score_kind == other.score_kind &&
               score == other.score && score_bound == other.score_bound && nodes == other.nodes;
    }
};

class UciProcess {
    using Clock = std::chrono::steady_clock;
    using Deadline = Clock::time_point;
    pid_t child_ = -1;
    int input_ = -1, output_ = -1, error_ = -1;
    bool output_eof_ = false, error_eof_ = false;
    std::string pending_, pending_error_, trace_, stderr_;

    static Deadline deadline(int timeout_ms) {
        return Clock::now() + std::chrono::milliseconds(std::max(1, timeout_ms));
    }
    static int remaining(Deadline end) {
        const auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - Clock::now()).count();
        if (ns <= 0) return 0;
        return static_cast<int>(std::min<std::int64_t>((ns + 999999) / 1000000, 2147483647));
    }
    static void close_fd(int& fd) noexcept {
        if (fd >= 0) close(fd);
        fd = -1;
    }
    [[noreturn]] void fail(const std::string& reason) {
        // Timeouts and disconnects must retain even an unterminated final line.
        while (!pending_.empty()) {
            const auto end = pending_.find('\n');
            if (end == std::string::npos) {
                trace_ += "< stdout " + pending_;
                trace_ += "\n! transport unparsed stdout ended without newline\n";
                pending_.clear();
            } else {
                trace_ += "< stdout " + pending_.substr(0, end + 1);
                pending_.erase(0, end + 1);
            }
        }
        emit_error_lines(true);
        throw std::runtime_error(reason + "\n" + trace_);
    }
    void emit_error_lines(bool flush_tail = false) {
        std::size_t end = 0;
        while ((end = pending_error_.find('\n')) != std::string::npos) {
            trace_ += "! stderr " + pending_error_.substr(0, end + 1);
            pending_error_.erase(0, end + 1);
        }
        if (flush_tail && !pending_error_.empty()) {
            trace_ += "! stderr " + pending_error_;
            trace_ += "\n! transport stderr ended without newline\n";
            pending_error_.clear();
        }
    }
    void read_available(int fd, bool is_error) {
        char buffer[8192];
        for (;;) {
            const ssize_t size = read(fd, buffer, sizeof(buffer));
            if (size > 0) {
                if (is_error) {
                    stderr_.append(buffer, static_cast<std::size_t>(size));
                    pending_error_.append(buffer, static_cast<std::size_t>(size));
                    emit_error_lines();
                } else {
                    pending_.append(buffer, static_cast<std::size_t>(size));
                }
                continue;
            }
            if (size == 0) {
                if (is_error) {
                    error_eof_ = true;
                    emit_error_lines(true);
                } else {
                    output_eof_ = true;
                }
                return;
            }
            if (errno == EINTR) continue;
            if (errno == EAGAIN || errno == EWOULDBLOCK) return;
            fail(std::string("engine pipe read failed: ") + std::strerror(errno));
        }
    }
    void pump(Deadline end) {
        const int left = remaining(end);
        if (left == 0) fail("engine response timeout");
        pollfd descriptors[2] = {
            {output_eof_ ? -1 : output_, POLLIN, 0},
            {error_eof_ ? -1 : error_, POLLIN, 0},
        };
        int status;
        do { status = poll(descriptors, 2, remaining(end)); } while (status < 0 && errno == EINTR && remaining(end) > 0);
        if (status == 0) fail("engine response timeout");
        if (status < 0) fail(std::string("engine poll failed: ") + std::strerror(errno));
        // Drain diagnostics before parsing stdout from the same poll wakeup.
        if (descriptors[1].revents & (POLLIN | POLLHUP | POLLERR)) read_available(error_, true);
        if (descriptors[0].revents & (POLLIN | POLLHUP | POLLERR)) read_available(output_, false);
        if ((descriptors[0].revents | descriptors[1].revents) & POLLNVAL) fail("engine pipe became invalid");
    }
    std::string line_until(Deadline end) {
        for (;;) {
            const auto split = pending_.find('\n');
            if (split != std::string::npos) {
                const std::string raw = pending_.substr(0, split + 1);
                pending_.erase(0, split + 1);
                trace_ += "< stdout " + raw;
                std::string parsed = raw.substr(0, raw.size() - 1);
                if (!parsed.empty() && parsed.back() == '\r') parsed.pop_back();
                return parsed;
            }
            if (output_eof_) {
                if (!pending_.empty()) {
                    trace_ += "< stdout " + pending_;
                    trace_ += "\n! transport stdout ended without newline\n";
                    pending_.clear();
                }
                if (!error_eof_) read_available(error_, true);
                int status = 0;
                const pid_t reaped = waitpid(child_, &status, WNOHANG);
                std::string detail = "engine disconnected";
                if (reaped == child_) {
                    child_ = -1;
                    if (WIFSIGNALED(status)) detail += " signal=" + std::to_string(WTERMSIG(status));
                    else if (WIFEXITED(status)) detail += " exit=" + std::to_string(WEXITSTATUS(status));
                }
                fail(detail);
            }
            pump(end);
        }
    }
    void send_until(const std::string& command, Deadline end) {
        if (command.find('\n') != std::string::npos || command.find('\r') != std::string::npos)
            fail("embedded newline in UCI command");
        trace_ += "> stdin " + command + "\n";
        const std::string data = command + "\n";
        std::size_t written = 0;
        while (written < data.size()) {
            const ssize_t size = write(input_, data.data() + written, data.size() - written);
            if (size > 0) {
                written += static_cast<std::size_t>(size);
                continue;
            }
            if (size < 0 && errno == EINTR) continue;
            if (size < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
                pollfd descriptor{input_, POLLOUT, 0};
                const int left = remaining(end);
                if (left == 0) fail("engine stdin timeout");
                const int result = poll(&descriptor, 1, left);
                if (result < 0 && errno == EINTR) continue;
                if (result == 0) fail("engine stdin timeout");
                if (result < 0) fail(std::string("engine stdin poll failed: ") + std::strerror(errno));
                continue;
            }
            if (error_ >= 0 && !error_eof_) read_available(error_, true);
            fail("engine stdin closed after " + std::to_string(written) + " bytes of command");
        }
    }
    void until_deadline(const std::string& expected, Deadline end) {
        while (line_until(end) != expected) {}
    }
    void ready_until(Deadline end) {
        send_until("isready", end);
        until_deadline("readyok", end);
    }
    void shutdown() noexcept {
        if (child_ > 0) {
            try { send_until("quit", deadline(100)); } catch (...) {}
        }
        close_fd(input_);
        if (child_ > 0) {
            int status = 0;
            const auto end = deadline(250);
            while (remaining(end) > 0) {
                const pid_t got = waitpid(child_, &status, WNOHANG);
                if (got == child_ || (got < 0 && errno == ECHILD)) {
                    child_ = -1;
                    break;
                }
                if (got < 0 && errno != EINTR) break;
                poll(nullptr, 0, std::min(10, remaining(end)));
            }
            if (child_ > 0) {
                kill(child_, SIGKILL);
                while (waitpid(child_, &status, 0) < 0 && errno == EINTR) {}
                child_ = -1;
            }
        }
        close_fd(output_);
        close_fd(error_);
    }
    static bool move_text(const std::string& move) {
        return (move.size() == 4 || move.size() == 5) &&
            move[0] >= 'a' && move[0] <= 'h' && move[1] >= '1' && move[1] <= '8' &&
            move[2] >= 'a' && move[2] <= 'h' && move[3] >= '1' && move[3] <= '8' &&
            (move.size() == 4 || std::string("qrbn").find(move[4]) != std::string::npos);
    }

public:
    explicit UciProcess(const std::string& path, int thread_count = 1, int timeout_ms = 30000) {
        std::signal(SIGPIPE, SIG_IGN);
        int to_child[2] = {-1, -1}, from_child[2] = {-1, -1}, errors[2] = {-1, -1};
        if (pipe(to_child) != 0 || pipe(from_child) != 0 || pipe(errors) != 0) {
            for (int* pair : {to_child, from_child, errors}) { close_fd(pair[0]); close_fd(pair[1]); }
            throw std::runtime_error("cannot create engine pipes");
        }
        child_ = fork();
        if (child_ < 0) {
            for (int* pair : {to_child, from_child, errors}) { close_fd(pair[0]); close_fd(pair[1]); }
            throw std::runtime_error("cannot fork engine");
        }
        if (child_ == 0) {
            if (dup2(to_child[0], STDIN_FILENO) < 0 || dup2(from_child[1], STDOUT_FILENO) < 0 ||
                dup2(errors[1], STDERR_FILENO) < 0) _exit(126);
            for (int* pair : {to_child, from_child, errors}) { close(pair[0]); close(pair[1]); }
            execl(path.c_str(), path.c_str(), static_cast<char*>(nullptr));
            const char message[] = "engine exec failed\n";
            (void)write(STDERR_FILENO, message, sizeof(message) - 1);
            _exit(127);
        }
        close_fd(to_child[0]); close_fd(from_child[1]); close_fd(errors[1]);
        input_ = to_child[1]; output_ = from_child[0]; error_ = errors[0];
        try {
            for (const int fd : {input_, output_, error_}) {
                const int flags = fcntl(fd, F_GETFL, 0);
                if (flags < 0 || fcntl(fd, F_SETFL, flags | O_NONBLOCK) < 0)
                    fail("cannot make engine pipe nonblocking");
                const int fd_flags = fcntl(fd, F_GETFD, 0);
                if (fd_flags < 0 || fcntl(fd, F_SETFD, fd_flags | FD_CLOEXEC) < 0)
                    fail("cannot mark engine pipe close-on-exec");
            }
            const auto end = deadline(timeout_ms);
            send_until("uci", end);
            until_deadline("uciok", end);
            send_until("setoption name Threads value " + std::to_string(thread_count), end);
            send_until("setoption name Hash value 16", end);
            send_until("setoption name OwnBook value false", end);
            ready_until(end);
        } catch (...) {
            shutdown();
            throw;
        }
    }
    ~UciProcess() { shutdown(); }
    UciProcess(const UciProcess&) = delete;
    UciProcess& operator=(const UciProcess&) = delete;

    const std::string& transcript() const { return trace_; }
    const std::string& stderr_output() const { return stderr_; }
    void send(const std::string& command, int timeout_ms = 30000) { send_until(command, deadline(timeout_ms)); }
    std::string line(int timeout_ms = 30000) { return line_until(deadline(timeout_ms)); }
    void until(const std::string& expected, int timeout_ms = 30000) { until_deadline(expected, deadline(timeout_ms)); }
    void ready(int timeout_ms = 30000) { ready_until(deadline(timeout_ms)); }
    void threads(int count, int timeout_ms = 30000) {
        const auto end = deadline(timeout_ms);
        send_until("setoption name Threads value " + std::to_string(count), end);
        ready_until(end);
    }
    void clear_hash(int timeout_ms = 30000) {
        const auto end = deadline(timeout_ms);
        send_until("setoption name Clear Hash", end);
        ready_until(end);
    }

    UciResult search(const std::string& fen, int depth, int timeout_ms = 30000, bool fresh_hash = true) {
        const auto end = deadline(timeout_ms);
        const std::size_t begin_trace = trace_.size(), begin_error = stderr_.size();
        if (fresh_hash) {
            send_until("setoption name Clear Hash", end);
            ready_until(end);
        }
        send_until("position fen " + fen, end);
        const auto started = Clock::now();
        send_until("go depth " + std::to_string(depth), end);
        UciResult result;
        for (;;) {
            const auto text = line_until(end);
            std::istringstream input(text);
            std::string token;
            input >> token;
            if (token == "bestmove") {
                if (!(input >> result.move)) fail("engine bestmove has no move");
                result.wall_ms = std::chrono::duration<double, std::milli>(Clock::now() - started).count();
                if (!error_eof_) read_available(error_, true);
                result.transcript = trace_.substr(begin_trace);
                result.stderr_output = stderr_.substr(begin_error);
                if (result.score_kind.empty()) fail("engine bestmove has no completed score info");
                return result;
            }
            if (token != "info") continue;
            UciResult info;
            int multipv = 1;
            bool has_depth = false, has_score = false, has_nodes = false, has_time = false;
            while (input >> token) {
                if (token == "string") break;
                if (token == "depth") { has_depth = static_cast<bool>(input >> info.depth); }
                else if (token == "multipv") input >> multipv;
                else if (token == "score") {
                    has_score = static_cast<bool>(input >> info.score_kind >> info.score);
                    has_score = has_score && (info.score_kind == "cp" || info.score_kind == "mate");
                } else if (token == "lowerbound" || token == "upperbound") info.score_bound = token;
                else if (token == "nodes") has_nodes = static_cast<bool>(input >> info.nodes);
                else if (token == "time") has_time = static_cast<bool>(input >> info.reported_ms);
                else if (token == "pv") {
                    while (input >> token) info.pv.push_back(token);
                    break;
                }
            }
            // Do not splice values from distinct info lines (e.g. current-move
            // diagnostics) into an apparently completed depth result.
            if (multipv == 1 && has_depth && has_score && has_nodes && has_time) {
                result.depth = info.depth;
                result.score_kind = info.score_kind;
                result.score = info.score;
                result.score_bound = info.score_bound;
                result.nodes = info.nodes;
                result.reported_ms = info.reported_ms;
                result.pv = std::move(info.pv);
            }
        }
    }

    std::vector<std::string> legal_moves(const std::string& fen, int timeout_ms = 30000) {
        const auto end = deadline(timeout_ms);
        send_until("position fen " + fen, end);
        send_until("go perft 1", end);
        std::vector<std::string> moves;
        for (;;) {
            const auto text = line_until(end);
            std::istringstream input(text);
            std::string token;
            input >> token;
            if (token == "nodes") {
                unsigned long long total = 0;
                if (!(input >> total) || total != moves.size()) fail("engine perft-1 move count mismatch");
                std::sort(moves.begin(), moves.end());
                if (std::adjacent_find(moves.begin(), moves.end()) != moves.end()) fail("duplicate engine legal move");
                if (!error_eof_) read_available(error_, true);
                return moves;
            }
            if (!token.empty() && token.back() == ':') {
                token.pop_back();
                unsigned long long leaves = 0;
                if (!move_text(token) || !(input >> leaves) || leaves != 1) fail("malformed engine perft-1 move");
                moves.push_back(token);
            }
        }
    }
};
