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

struct UciShutdownResult {
    bool reaped = false, timed_out = false, driver_sigterm = false, driver_sigkill = false;
    int exit_code = -1, signal = 0;
    bool quit_attempted = false, quit_sent = false;
    int shutdown_budget_ms = 0;
    double quit_to_exit_ms = -1.0, shutdown_total_ms = 0.0;
    std::string transcript, stderr_output, error;
    // Added only for the separately authorized 0020 diagnostic path below.
    bool diagnostic_window = false, natural_exit_observed_within_5s = false;
    bool diagnostic_fallback_used = false;
    bool stdout_eof_before_shutdown = false, stderr_eof_before_shutdown = false;
    int quit_write_budget_ms = 0, natural_grace_ms = 0;
    int term_observation_ms = 0, kill_observation_ms = 0;
    double quit_write_begin_ms = -1.0, quit_write_end_ms = -1.0;
    double stdin_close_ms = -1.0, reap_observed_ms = -1.0;
    double stdout_eof_observed_ms = -1.0, stderr_eof_observed_ms = -1.0;
    double natural_deadline_ms = -1.0;
    double sigterm_attempt_ms = -1.0, sigkill_attempt_ms = -1.0;
    int sigterm_errno = 0, sigkill_errno = 0;
    int unreaped_child_pid = -1;
};

struct UciDiagnosticShutdownDeadlines {
    std::int64_t natural_ns, terminate_ns, kill_ns;
};
inline constexpr UciDiagnosticShutdownDeadlines uci_diagnostic_shutdown_deadlines(std::int64_t delivered_ns) {
    const auto natural = delivered_ns + 5000000000LL;
    const auto terminate = std::max(natural, std::min(natural + 250000000LL, 5600000000LL));
    const auto kill = std::max(terminate, std::min(terminate + 250000000LL, 5600000000LL));
    return {natural, terminate, kill};
}
inline constexpr bool uci_diagnostic_natural_exit(const UciShutdownResult& r) {
    return r.quit_sent && r.reaped && r.exit_code == 0 && r.signal == 0 &&
        !r.driver_sigterm && !r.driver_sigkill &&
        r.quit_write_end_ms >= 0.0 && r.reap_observed_ms >= r.quit_write_end_ms &&
        r.reap_observed_ms <= r.quit_write_end_ms + 5000.0;
}

class UciStartupError : public std::runtime_error {
public:
    UciShutdownResult shutdown;
    UciStartupError(const std::string& message, UciShutdownResult status)
        : std::runtime_error(message), shutdown(std::move(status)) {}
};

class UciProcess {
    using Clock = std::chrono::steady_clock;
    using Deadline = Clock::time_point;
    pid_t child_ = -1;
    int input_ = -1, output_ = -1, error_ = -1;
    bool output_eof_ = false, error_eof_ = false;
    std::string pending_, pending_error_, trace_, stderr_;
    bool have_child_status_ = false, finished_ = false;
    int child_status_ = 0;
    UciShutdownResult final_status_;

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
    void emit_output_lines(bool flush_tail = false) {
        std::size_t end = 0;
        while ((end = pending_.find('\n')) != std::string::npos) {
            trace_ += "< stdout " + pending_.substr(0, end + 1);
            pending_.erase(0, end + 1);
        }
        if (flush_tail && !pending_.empty()) {
            trace_ += "< stdout " + pending_;
            trace_ += "\n! transport stdout ended without newline\n";
            pending_.clear();
        }
    }
    void read_available(int fd, bool is_error) {
        char buffer[8192];
        std::size_t received = 0;
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
                // Return to the deadline-aware caller even if a runaway child
                // writes continuously; one readable pipe cannot monopolize it.
                received += static_cast<std::size_t>(size);
                if (received >= 65536) return;
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
            if (remaining(end) == 0) fail("engine response timeout");
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
                    child_status_ = status;
                    have_child_status_ = true;
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
        try { (void)finish_diagnostic(); }
        catch (...) {
            // Last-resort helper-exception path. No allocations and no early
            // signal: allow an additional full5s after closing stdin. This is
            // explicitly an exceptional fallback, not the normal5600ms budget.
            final_status_.diagnostic_window = true;
            final_status_.diagnostic_fallback_used = true;
            final_status_.timed_out = true;
            final_status_.natural_exit_observed_within_5s = false;
            close_fd(input_);
            const auto fallback_start = Clock::now();
            const auto natural_end = fallback_start + std::chrono::milliseconds(5000);
            const auto cleanup_end = natural_end + std::chrono::milliseconds(250);
            auto reap_noalloc = [&]() noexcept {
                if (child_ <= 0) return;
                int status = 0;
                const pid_t got = waitpid(child_, &status, WNOHANG);
                if (got == child_) {
                    child_status_ = status; have_child_status_ = true; child_ = -1;
                } else if (got < 0 && errno == ECHILD) child_ = -1;
            };
            while (child_ > 0 && Clock::now() < natural_end) {
                reap_noalloc();
                if (child_ > 0) (void)poll(nullptr, 0, std::min(10, remaining(natural_end)));
            }
            reap_noalloc();
            if (child_ > 0) final_status_.driver_sigkill = kill(child_, SIGKILL) == 0;
            while (child_ > 0 && Clock::now() < cleanup_end) {
                reap_noalloc();
                if (child_ > 0) (void)poll(nullptr, 0, std::min(10, remaining(cleanup_end)));
            }
            reap_noalloc();
            if (child_ > 0) final_status_.unreaped_child_pid = static_cast<int>(child_);
            child_ = -1;
            close_fd(output_); close_fd(error_);
            final_status_.reaped = have_child_status_;
            if (have_child_status_) {
                if (WIFEXITED(child_status_)) final_status_.exit_code = WEXITSTATUS(child_status_);
                if (WIFSIGNALED(child_status_)) final_status_.signal = WTERMSIG(child_status_);
            }
            finished_ = true;
        }
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
        } catch (const std::exception& caught) {
            const std::string original = caught.what();
            shutdown();
            auto startup_status = final_status_;
            startup_status.transcript = trace_;
            startup_status.stderr_output = stderr_;
            throw UciStartupError(original + "\n! observed startup shutdown\n" + trace_, std::move(startup_status));
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
    // Explicitly observe quit, pipe EOF, and process status. The entire method
    // is bounded by timeout_ms; its final 40% is reserved for SIGTERM/SIGKILL
    // escalation. Driver-initiated signals are reported separately from an
    // unsolicited engine crash. Calling it again returns the recorded result.
    UciShutdownResult finish(int timeout_ms = 250) {
        if (finished_) return final_status_;
        const std::size_t begin_trace = trace_.size(), begin_error = stderr_.size();
        const auto started = Clock::now();
        const int budget = std::max(1, timeout_ms);
        const auto end = started + std::chrono::milliseconds(budget);
        const auto graceful_end = started + std::chrono::milliseconds(budget * 3 / 5);
        const auto terminate_end = started + std::chrono::milliseconds(budget * 4 / 5);
        UciShutdownResult result;
        result.shutdown_budget_ms = budget;
        Clock::time_point quit_started{};
        auto error = [&](const std::string& message) {
            if (!result.error.empty()) result.error += "; ";
            result.error += message.substr(0, message.find('\n'));
        };
        auto reap = [&] {
            if (child_ <= 0) return;
            int status = 0;
            const pid_t got = waitpid(child_, &status, WNOHANG);
            if (got == child_) {
                if (result.quit_sent) result.quit_to_exit_ms = std::chrono::duration<double, std::milli>(Clock::now() - quit_started).count();
                child_status_ = status; have_child_status_ = true; child_ = -1;
            } else if (got < 0 && errno != EINTR) {
                error(std::string("shutdown waitpid failed: ") + std::strerror(errno));
                if (errno == ECHILD) child_ = -1;
            }
        };
        auto drain = [&] {
            try {
                if (error_ >= 0 && !error_eof_) read_available(error_, true);
                if (output_ >= 0 && !output_eof_) read_available(output_, false);
                emit_output_lines(output_eof_);
                emit_error_lines(error_eof_);
            } catch (const std::exception& caught) { error(caught.what()); }
            reap();
        };
        auto observe_until = [&](Deadline until) {
            for (;;) {
                drain();
                if (child_ <= 0 && output_eof_ && error_eof_) return;
                const int left = remaining(until);
                if (!left) return;
                pollfd descriptors[2] = {
                    {output_eof_ ? -1 : output_, POLLIN, 0},
                    {error_eof_ ? -1 : error_, POLLIN, 0},
                };
                const int polled = poll(descriptors, 2, std::min(10, left));
                if (polled < 0 && errno != EINTR) {
                    error(std::string("shutdown poll failed: ") + std::strerror(errno)); return;
                }
            }
        };
        if (child_ > 0 && input_ >= 0) {
            result.quit_attempted = true; quit_started = Clock::now();
            try { send_until("quit", graceful_end); result.quit_sent = true; }
            catch (const std::exception& caught) { error(caught.what()); }
        }
        close_fd(input_);
        observe_until(graceful_end);
        if (child_ > 0 || !output_eof_ || !error_eof_) {
            result.timed_out = true;
            if (child_ > 0) result.driver_sigterm = kill(child_, SIGTERM) == 0;
            observe_until(terminate_end);
        }
        if (child_ > 0 || !output_eof_ || !error_eof_) {
            if (child_ > 0) result.driver_sigkill = kill(child_, SIGKILL) == 0;
            observe_until(end);
        }
        drain();
        emit_output_lines(true); emit_error_lines(true);
        if (child_ > 0) {
            result.timed_out = true;
            if (!result.driver_sigkill) result.driver_sigkill = kill(child_, SIGKILL) == 0;
            reap();
            if (child_ > 0) {
                error("child exit status unavailable at shutdown deadline");
                child_ = -1;
            }
        }
        close_fd(output_); close_fd(error_);
        result.reaped = have_child_status_;
        if (have_child_status_) {
            if (WIFEXITED(child_status_)) result.exit_code = WEXITSTATUS(child_status_);
            if (WIFSIGNALED(child_status_)) result.signal = WTERMSIG(child_status_);
        }
        result.shutdown_total_ms = std::chrono::duration<double, std::milli>(Clock::now() - started).count();
        trace_ += "! shutdown timing_schema=1 budget_ms=" + std::to_string(result.shutdown_budget_ms) +
            " quit_attempted=" + std::to_string(result.quit_attempted) + " quit_sent=" + std::to_string(result.quit_sent) +
            " quit_to_exit_ms=" + std::to_string(result.quit_to_exit_ms) + " total_ms=" + std::to_string(result.shutdown_total_ms) + "\n";
        trace_ += "! shutdown reaped=" + std::to_string(result.reaped) +
            " exit=" + std::to_string(result.exit_code) + " signal=" + std::to_string(result.signal) +
            " timed_out=" + std::to_string(result.timed_out) +
            " driver_sigterm=" + std::to_string(result.driver_sigterm) +
            " driver_sigkill=" + std::to_string(result.driver_sigkill) + "\n";
        result.transcript = trace_.substr(begin_trace);
        result.stderr_output = stderr_.substr(begin_error);
        final_status_ = result; finished_ = true;
        return final_status_;
    }
    // Diagnostic only: preserve a full 5000ms no-signal window after the quit
    // write completes. The frozen finish() above remains unchanged; this private
    // copy also routes constructor/destructor cleanup through this diagnostic path.
    UciShutdownResult finish_diagnostic() {
        if (finished_) return final_status_;
        const std::size_t begin_trace = trace_.size(), begin_error = stderr_.size();
        const auto started = Clock::now();
        UciShutdownResult result;
        result.diagnostic_window = true;
        result.shutdown_budget_ms = 5600;
        result.quit_write_budget_ms = 100;
        result.natural_grace_ms = 5000;
        result.term_observation_ms = 250;
        result.kill_observation_ms = 250;
        result.stdout_eof_before_shutdown = output_eof_;
        result.stderr_eof_before_shutdown = error_eof_;
        auto elapsed = [&] { return std::chrono::duration<double, std::milli>(Clock::now() - started).count(); };
        auto event = [&](const std::string& name, double at) {
            trace_ += "! diagnostic_shutdown event=" + name + " elapsed_ms=" + std::to_string(at) + "\n";
        };
        std::vector<std::string> errors_seen;
        auto error = [&](const std::string& message) {
            const auto first = message.substr(0, message.find('\n'));
            if (std::find(errors_seen.begin(), errors_seen.end(), first) != errors_seen.end()) return;
            errors_seen.push_back(first);
            if (!result.error.empty()) result.error += "; ";
            result.error += first;
        };
        auto record_eof = [&] {
            if (output_eof_ && result.stdout_eof_observed_ms < 0) {
                result.stdout_eof_observed_ms = elapsed();
                event(result.stdout_eof_before_shutdown ? "stdout_eof_preexisting" : "stdout_eof_observed", result.stdout_eof_observed_ms);
            }
            if (error_eof_ && result.stderr_eof_observed_ms < 0) {
                result.stderr_eof_observed_ms = elapsed();
                event(result.stderr_eof_before_shutdown ? "stderr_eof_preexisting" : "stderr_eof_observed", result.stderr_eof_observed_ms);
            }
        };
        auto reap = [&] {
            if (child_ <= 0) return;
            int status = 0;
            const pid_t got = waitpid(child_, &status, WNOHANG);
            if (got == child_) {
                result.reap_observed_ms = elapsed();
                event("reap_observed", result.reap_observed_ms);
                if (result.quit_attempted) result.quit_to_exit_ms = result.reap_observed_ms - result.quit_write_begin_ms;
                child_status_ = status; have_child_status_ = true; child_ = -1;
            } else if (got < 0 && errno != EINTR) {
                error(std::string("diagnostic shutdown waitpid failed: ") + std::strerror(errno));
                if (errno == ECHILD) child_ = -1;
            }
        };
        auto drain = [&] {
            try {
                if (error_ >= 0 && !error_eof_) read_available(error_, true);
                if (output_ >= 0 && !output_eof_) read_available(output_, false);
                emit_output_lines(output_eof_); emit_error_lines(error_eof_);
            } catch (const std::exception& caught) { error(caught.what()); }
            record_eof(); reap();
        };
        auto observe_until = [&](Deadline until) {
            for (;;) {
                drain();
                if (child_ <= 0 && output_eof_ && error_eof_) return;
                const int left = remaining(until);
                if (!left) return;
                pollfd descriptors[2] = {
                    {output_eof_ ? -1 : output_, POLLIN, 0},
                    {error_eof_ ? -1 : error_, POLLIN, 0},
                };
                const int polled = poll(descriptors, 2, std::min(10, left));
                if ((polled < 0 && errno != EINTR) || ((descriptors[0].revents | descriptors[1].revents) & POLLNVAL)) {
                    error(polled < 0 ? std::string("diagnostic shutdown poll failed: ") + std::strerror(errno) : "diagnostic shutdown invalid pipe descriptor");
                    // A polling error does not authorize early cleanup signals.
                    // Avoid a busy loop if a pipe remains invalid until grace ends.
                    (void)poll(nullptr, 0, std::min(10, remaining(until)));
                }
            }
        };
        auto deliver_signal = [&](int signal, double& at, bool& succeeded, int& signal_errno, const char* name) {
            if (child_ <= 0) return;
            at = elapsed(); event(std::string(name) + "_attempt", at);
            const int status = kill(child_, signal);
            signal_errno = status == 0 ? 0 : errno;
            succeeded = status == 0;
            trace_ += "! diagnostic_shutdown signal=" + std::string(name) + " succeeded=" + std::to_string(succeeded) +
                " errno=" + std::to_string(signal_errno) + "\n";
            if (!succeeded) error(std::string("diagnostic shutdown ") + name + " failed: " + std::strerror(signal_errno));
        };
        record_eof();
        auto delivery_end = Clock::now();
        if (child_ > 0 && input_ >= 0) {
            result.quit_attempted = true;
            result.quit_write_begin_ms = elapsed(); event("quit_write_begin", result.quit_write_begin_ms);
            try {
                // This shutdown-only send checks the deadline before every
                // nonblocking write, including after EINTR. Existing ordinary
                // send/read/constructor behavior is deliberately unchanged.
                const auto write_end = started + std::chrono::milliseconds(100);
                const std::string data = "quit\n";
                trace_ += "> stdin quit\n";
                std::size_t written = 0;
                while (written < data.size()) {
                    if (!remaining(write_end)) throw std::runtime_error("diagnostic quit write timeout");
                    const ssize_t n = write(input_, data.data() + written, data.size() - written);
                    if (n > 0) { written += static_cast<std::size_t>(n); continue; }
                    if (n < 0 && errno == EINTR) continue;
                    if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
                        pollfd descriptor{input_, POLLOUT, 0};
                        const int status = poll(&descriptor, 1, remaining(write_end));
                        if (status >= 0 || errno == EINTR) continue;
                        throw std::runtime_error(std::string("diagnostic quit poll failed: ") + std::strerror(errno));
                    }
                    throw std::runtime_error("diagnostic quit write failed after " + std::to_string(written) + " bytes");
                }
                result.quit_sent = true;
                delivery_end = Clock::now();
                result.quit_write_end_ms = std::chrono::duration<double, std::milli>(delivery_end - started).count();
                if (result.quit_write_end_ms > 100.0) error("diagnostic quit delivery observed after write budget");
                event("quit_write_complete", result.quit_write_end_ms);
            } catch (const std::exception& caught) {
                error(caught.what()); delivery_end = Clock::now();
                event("quit_write_failed", elapsed());
            }
        } else {
            error("quit unavailable: process or stdin already absent");
        }
        close_fd(input_);
        result.stdin_close_ms = elapsed(); event("stdin_closed", result.stdin_close_ms);
        // The successful path is bounded by100ms write+5000ms grace+250+250ms.
        // Failed writes retain a diagnostic observation window where possible;
        // quit_sent remains false, so they cannot count as natural quit exits.
        const auto schedule = uci_diagnostic_shutdown_deadlines(std::chrono::duration_cast<std::chrono::nanoseconds>(delivery_end - started).count());
        const auto natural_end = started + std::chrono::nanoseconds(schedule.natural_ns);
        // Never shorten natural grace, even if an observed scheduling delay
        // exceeded the write budget. In that abnormal case shorten cleanup
        // observation instead and report the write-budget error above.
        const auto terminate_end = started + std::chrono::nanoseconds(schedule.terminate_ns);
        const auto kill_end = started + std::chrono::nanoseconds(schedule.kill_ns);
        result.natural_deadline_ms = std::chrono::duration<double, std::milli>(natural_end - started).count();
        event("natural_deadline_declared", result.natural_deadline_ms);
        observe_until(natural_end);
        if (child_ > 0 || !output_eof_ || !error_eof_) {
            result.timed_out = true;
            deliver_signal(SIGTERM, result.sigterm_attempt_ms, result.driver_sigterm, result.sigterm_errno, "sigterm");
            observe_until(terminate_end);
        }
        if (child_ > 0 || !output_eof_ || !error_eof_) {
            deliver_signal(SIGKILL, result.sigkill_attempt_ms, result.driver_sigkill, result.sigkill_errno, "sigkill");
            observe_until(kill_end);
        }
        drain(); emit_output_lines(true); emit_error_lines(true);
        if (child_ > 0) {
            result.timed_out = true;
            error("child exit status unavailable at diagnostic shutdown deadline");
            // No unbounded wait or hidden additional signal after the deadline.
            result.unreaped_child_pid = static_cast<int>(child_);
            child_ = -1;
        }
        close_fd(output_); close_fd(error_);
        result.reaped = have_child_status_;
        if (have_child_status_) {
            if (WIFEXITED(child_status_)) result.exit_code = WEXITSTATUS(child_status_);
            if (WIFSIGNALED(child_status_)) result.signal = WTERMSIG(child_status_);
        }
        result.natural_exit_observed_within_5s = uci_diagnostic_natural_exit(result);
        result.shutdown_total_ms = elapsed();
        trace_ += "! diagnostic_shutdown complete natural_exit_within_5s=" + std::to_string(result.natural_exit_observed_within_5s) +
            " reaped=" + std::to_string(result.reaped) + " exit=" + std::to_string(result.exit_code) +
            " signal=" + std::to_string(result.signal) + " timed_out=" + std::to_string(result.timed_out) +
            " total_ms=" + std::to_string(result.shutdown_total_ms) + "\n";
        result.transcript = trace_.substr(begin_trace); result.stderr_output = stderr_.substr(begin_error);
        final_status_ = result; finished_ = true;
        return final_status_;
    }
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
            // Cold-state protocol: reset histories as well as the hash. The
            // separate clear_hash() method intentionally preserves histories.
            send_until("ucinewgame", end);
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
