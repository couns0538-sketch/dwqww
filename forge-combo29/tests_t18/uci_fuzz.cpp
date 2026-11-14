// UCI input fuzzer for Forge.
// Part A: hand-written commands. Part B: fixed-seed lines (default 200000).
// Generated "go" searches are capped at 200 nodes. Generated "go perft" depths
// above 2 are rewritten to 1, and generated "bench" depths that would run
// deeper than 2 are rewritten to "bench 1", so the suite cannot start a
// multi-minute tree walk. The engine binary is unchanged by that rewrite;
// only the text this driver feeds it is limited.

#include "forge/board.hpp"
#include "forge/uci.hpp"

#include <algorithm>
#include <charconv>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <mutex>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <utility>
#include <vector>

namespace {

constexpr std::uint64_t kSeed = 0x5418C0FFEEULL;
constexpr int kDefaultLines = 200000;
constexpr std::chrono::milliseconds kHang{5000};

class SplitMix {
public:
    explicit SplitMix(std::uint64_t seed) : state_(seed) {}

    std::uint64_t next() {
        std::uint64_t z = (state_ += 0x9E3779B97F4A7C15ULL);
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31);
    }

    std::uint64_t below(std::uint64_t n) { return next() % n; }

private:
    std::uint64_t state_;
};

std::string preview(std::string_view text) {
    constexpr std::size_t kMax = 160;
    std::string out;
    const std::size_t n = std::min(text.size(), kMax);
    out.reserve(n * 2);
    constexpr char hex[] = "0123456789abcdef";
    for (std::size_t i = 0; i < n; ++i) {
        const unsigned char c = static_cast<unsigned char>(text[i]);
        if (c >= 32 && c < 127) {
            out.push_back(static_cast<char>(c));
        } else {
            out += "\\x";
            out.push_back(hex[c >> 4]);
            out.push_back(hex[c & 15]);
        }
    }
    if (text.size() > kMax) out += "...";
    out += " (len=";
    out += std::to_string(text.size());
    out += ")";
    return out;
}

bool takes_number(std::string_view token) {
    return token == "depth" || token == "nodes" || token == "movetime" || token == "wtime" ||
           token == "btime" || token == "winc" || token == "binc" || token == "movestogo" || token == "mate";
}

std::vector<std::string> tokens_of(const std::string& line) {
    std::istringstream in(line);
    std::vector<std::string> tokens;
    std::string token;
    while (in >> token) tokens.push_back(std::move(token));
    return tokens;
}

bool parsed_int(std::string_view text, int& value) {
    const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
    return result.ec == std::errc{} && result.ptr == text.data() + text.size();
}

// Driver limit for generated lines only. Hand-written cases are fed unchanged.
std::string limit_generated(const std::string& line) {
    const std::vector<std::string> tokens = tokens_of(line);
    if (tokens.empty()) return line;
    if (tokens[0] == "bench") {
        int depth = 0;
        if (tokens.size() >= 2 && parsed_int(tokens[1], depth) && std::clamp(depth, 1, 64) <= 2) return line;
        return "bench 1";
    }
    if (tokens[0] != "go") return line;
    if (tokens.size() >= 2 && tokens[1] == "perft") {
        int depth = 0;
        if (tokens.size() >= 3 && parsed_int(tokens[2], depth) && depth >= 0 && depth <= 2) return line;
        return "go perft 1";
    }
    if (takes_number(tokens.back())) return line + " 0 nodes 200";
    return line + " nodes 200";
}

void expect_eq(const char* input, const std::string& got, const char* want) {
    if (got != want) {
        std::cerr << "driver self-check failed\ninput: " << input << "\ngot:   " << got << "\nwant:  " << want
                  << "\n";
        std::_Exit(1);
    }
}

void self_check_driver() {
    expect_eq("go", limit_generated("go"), "go nodes 200");
    expect_eq("go nodes", limit_generated("go nodes"), "go nodes 0 nodes 200");
    expect_eq("go depth 9", limit_generated("go depth 9"), "go depth 9 nodes 200");
    expect_eq("go mate", limit_generated("go mate"), "go mate 0 nodes 200");
    expect_eq("go searchmoves", limit_generated("go searchmoves"), "go searchmoves nodes 200");
    expect_eq("go perft 10", limit_generated("go perft 10"), "go perft 1");
    expect_eq("go perft", limit_generated("go perft"), "go perft 1");
    expect_eq("go perft 2", limit_generated("go perft 2"), "go perft 2");
    expect_eq("bench 9", limit_generated("bench 9"), "bench 1");
    expect_eq("bench", limit_generated("bench"), "bench 1");
    expect_eq("bench foo", limit_generated("bench foo"), "bench 1");
    expect_eq("bench 2", limit_generated("bench 2"), "bench 2");
    expect_eq("bench -3", limit_generated("bench -3"), "bench -3");
    expect_eq("position", limit_generated("position"), "position");
}

class DiscardBuf : public std::streambuf {
public:
    int_type overflow(int_type c) override { return c; }
    std::streamsize xsputn(const char*, std::streamsize n) override { return n; }
};

class FeedBuf;

class LineQueue {
public:
    struct Taken {
        bool eof = false;
        std::string line;
    };

    Taken take() {
        std::unique_lock lock(mu_);
        waiting_ = true;
        cv_.notify_all();
        cv_.wait(lock, [&] { return has_ || eof_; });
        waiting_ = false;
        if (!has_) return Taken{true, {}};
        has_ = false;
        Taken taken;
        taken.line = std::move(line_);
        line_.clear();
        return taken;
    }

    bool send(std::string line, std::chrono::milliseconds budget, std::string& hang) {
        line.erase(std::remove(line.begin(), line.end(), '\n'), line.end());
        std::unique_lock lock(mu_);
        if (!cv_.wait_for(lock, budget, [&] { return (waiting_ && !has_) || done_; })) {
            hang = "previous command exceeded 5s: " + preview(last_);
            return false;
        }
        if (done_) {
            hang = error_.empty() ? "session ended before the line was read" : error_;
            return false;
        }
        line_ = std::move(line);
        last_ = line_;
        has_ = true;
        cv_.notify_all();
        if (!cv_.wait_for(lock, budget, [&] { return (waiting_ && !has_) || done_; })) {
            hang = "command exceeded 5s: " + preview(last_);
            return false;
        }
        if (done_ && !error_.empty()) {
            hang = error_;
            return false;
        }
        return true;
    }

    bool finish(std::chrono::milliseconds budget, std::string& hang) {
        std::unique_lock lock(mu_);
        if (!cv_.wait_for(lock, budget, [&] { return (waiting_ && !has_) || done_; })) {
            hang = "previous command exceeded 5s before shutdown: " + preview(last_);
            return false;
        }
        if (!done_) {
            eof_ = true;
            cv_.notify_all();
            if (!cv_.wait_for(lock, budget, [&] { return done_; })) {
                hang = "shutdown exceeded 5s after: " + preview(last_);
                return false;
            }
        }
        if (!error_.empty()) {
            hang = error_;
            return false;
        }
        return true;
    }

    void set_done(std::string error) {
        {
            const std::lock_guard<std::mutex> lock(mu_);
            if (!error.empty()) error_ = std::move(error);
            done_ = true;
        }
        cv_.notify_all();
    }

private:
    std::mutex mu_;
    std::condition_variable cv_;
    std::string line_;
    std::string last_;
    std::string error_;
    bool has_ = false;
    bool waiting_ = false;
    bool eof_ = false;
    bool done_ = false;
};

class FeedBuf : public std::streambuf {
public:
    explicit FeedBuf(LineQueue& queue) : queue_(queue) {}

protected:
    int_type underflow() override {
        if (gptr() < egptr()) return traits_type::to_int_type(*gptr());
        const LineQueue::Taken taken = queue_.take();
        if (taken.eof) return traits_type::eof();
        buf_ = std::move(taken.line);
        buf_.push_back('\n');
        setg(buf_.data(), buf_.data(), buf_.data() + buf_.size());
        return traits_type::to_int_type(*gptr());
    }

private:
    LineQueue& queue_;
    std::string buf_;
};

class Session {
public:
    void start() {
        thread_ = std::thread([this] {
            std::string error;
            try {
                FeedBuf buf(queue_);
                std::istream in(&buf);
                in.tie(&std::cout);
                const int code = forge::uci_loop(in);
                if (code != 0) error = "uci_loop returned " + std::to_string(code);
            } catch (const std::exception& ex) {
                error = std::string("exception: ") + ex.what();
            } catch (...) {
                error = "unknown exception";
            }
            queue_.set_done(std::move(error));
        });
    }

    bool send(const std::string& line, std::string& hang) { return queue_.send(line, kHang, hang); }

    bool finish(std::string& hang) {
        const bool ok = queue_.finish(kHang, hang);
        if (thread_.joinable()) thread_.join();
        return ok;
    }

    ~Session() {
        if (thread_.joinable()) thread_.join();
    }

    Session(const Session&) = delete;
    Session& operator=(const Session&) = delete;
    Session() = default;

private:
    LineQueue queue_;
    std::thread thread_;
};

bool send_setup(Session& session, std::string& hang) {
    const char* setup[] = {
        "uci",
        "isready",
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        "setoption name OwnBook value false",
        "setoption name UseNNUE value true",
        "setoption name Ponder value false",
        "isready",
    };
    for (const char* line : setup) {
        if (!session.send(line, hang)) return false;
    }
    return true;
}

std::string two_thousand_moves() {
    forge::Board board;
    const char* cycle[] = {"g1f3", "g8f6", "f3g1", "f6g8"};
    constexpr int cycle_len = 4;
    std::string line = "position startpos moves";
    for (int i = 0; i < 2000; ++i) {
        const std::string move = cycle[i % cycle_len];
        const std::optional<forge::Move> parsed = board.parse_uci(move);
        if (!parsed.has_value()) {
            std::cerr << "legal-move cycle broke at ply " << i << " move " << move << " fen " << board.fen() << "\n";
            std::_Exit(1);
        }
        forge::Undo undo;
        (void)board.make_move(*parsed, undo);
        line += ' ';
        line += move;
    }
    line += " not-a-move";
    return line;
}

std::string two_thousand_bad_moves() {
    std::string line = "position startpos moves";
    for (int i = 0; i < 2000; ++i) line += " e2e5";
    return line;
}

std::string hundred_k_value() {
    std::string line = "setoption name Hash value ";
    line.append(100000, '9');
    return line;
}

std::string hundred_k_name() {
    std::string line = "setoption name ";
    line.append(100000, 'Z');
    line += " value 1";
    return line;
}

std::string one_mb_line() {
    std::string line(1024U * 1024U, 'x');
    line[0] = static_cast<char>(0xFF);
    line[1] = static_cast<char>(0x80);
    line[2] = '\t';
    line[100] = static_cast<char>(0xFE);
    line[1000] = static_cast<char>(0xC0);
    return line;
}

std::string high_bytes() {
    std::string line;
    for (int b = 128; b <= 255; ++b) line.push_back(static_cast<char>(b));
    return line;
}

std::string bytes_except_newline() {
    std::string line;
    for (int b = 1; b <= 255; ++b) {
        if (b != '\n') line.push_back(static_cast<char>(b));
    }
    return line;
}

std::string nul_in_command() {
    std::string line = "position";
    line.push_back('\0');
    line += "startpos";
    return line;
}

void add(std::vector<std::string>& lines, std::string line) { lines.push_back(std::move(line)); }

void add_go(std::vector<std::string>& lines, const char* go) {
    add(lines, go);
    add(lines, "stop");
}

std::vector<std::string> part_a_lines() {
    std::vector<std::string> lines;
    add(lines, "");
    add(lines, " ");
    add(lines, "\t");
    add(lines, "\t\t");
    add(lines, " \t ");
    add(lines, "\r");
    add(lines, "\r\t");
    add(lines, "stop");
    add(lines, "ponderhit");
    add(lines, "stop");
    add(lines, "ponderhit extra junk");
    add(lines, "ucinewgame");
    add(lines, "position");
    add(lines, "position\t");
    add(lines, "position fen");
    add(lines, "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR");
    add(lines, "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w");
    add(lines, "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq");
    add(lines, "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -");
    add(lines, "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0");
    add(lines, "position fen 4k3/8/8/8/8/8/8/4K3 w - -");
    add(lines, "position fen 8/8/8/8/8/8/8/8 w - - 0 1");
    add(lines, "position fen 4k3/8/8/8/8/8/8/4K3 w - - 0 1 extra");
    add(lines, std::string("position fen ") + std::string(1, static_cast<char>(0xFF)) + " w - - 0 1");
    add(lines, "position startpos");
    add(lines, "position startpos moves e2e5");
    add(lines, "position startpos moves e2e4 e2e4");
    add(lines, "position startpos moves a1a8");
    add(lines, "position startpos moves e2");
    add(lines, "position startpos moves e2e4e5");
    add(lines, "position startpos moves e2-e4");
    add(lines, "position startpos moves O-O");
    add(lines, "position startpos moves e4");
    add(lines, "position startpos moves e2e4n");
    add(lines, "position startpos moves 0000");
    add(lines, "position startpos moves e2e4\te7e5");
    add(lines, "position moves e2e4");
    add(lines, "position foo");
    add(lines, "position startpos moves");
    add(lines, two_thousand_moves());
    add(lines, two_thousand_bad_moves());
    add(lines, nul_in_command());
    add_go(lines, "go");
    add_go(lines, "go depth 0");
    add_go(lines, "go depth -5");
    add_go(lines, "go depth 999999");
    add_go(lines, "go nodes 0");
    add_go(lines, "go movetime 0");
    add_go(lines, "go movetime -1");
    add_go(lines, "go wtime 1 btime 1");
    add_go(lines, "go wtime 0");
    add_go(lines, "go movestogo 0");
    add_go(lines, "go mate 0");
    add_go(lines, "go depth");
    add_go(lines, "go nodes");
    add_go(lines, "go movetime");
    add_go(lines, "go wtime");
    add_go(lines, "go btime");
    add_go(lines, "go winc");
    add_go(lines, "go binc");
    add_go(lines, "go mate");
    add_go(lines, "go movestogo");
    add_go(lines, "go searchmoves");
    add_go(lines, "go searchmoves zzzz");
    add_go(lines, "go searchmoves e2e4");
    add_go(lines, "go searchmoves e2e4 e7e5");
    add_go(lines, "go foobar");
    add_go(lines, "go depth abc");
    add_go(lines, "go nodes -1");
    add_go(lines, "go depth --5");
    add_go(lines, "go movetime 999999999999999999999");
    add_go(lines, "go wtime 3000000000");
    add_go(lines, "go wtime 2147483647");
    add_go(lines, "go wtime -1");
    add_go(lines, "go btime 0");
    add_go(lines, "go winc -5");
    add_go(lines, "go binc -1");
    add_go(lines, "go mate -1");
    add_go(lines, "go mate 999999");
    add_go(lines, "go movestogo -3");
    add_go(lines, "go movestogo 999999");
    add_go(lines, "go infinite");
    add_go(lines, "go ponder");
    add(lines, "go ponder wtime 20 btime 20");
    add(lines, "ponderhit");
    add(lines, "stop");
    add(lines, "go depth 999999");
    add(lines, "ucinewgame");
    add(lines, "\tgo\tdepth\t1\t");
    add(lines, "stop");
    add(lines, "go perft");
    add(lines, "go perft -1");
    add(lines, "go perft 99");
    add(lines, "go perft abc");
    add(lines, "go perft 0");
    add(lines, "go perft 1");
    add(lines, "go perft 2");
    add(lines, "go nodes 1");
    add(lines, "stop");
    add(lines, "setoption");
    add(lines, "setoption name");
    add(lines, "setoption value 1");
    add(lines, "setoption name Hash");
    add(lines, "setoption name Hash value");
    add(lines, "setoption name Hash value abc");
    add(lines, "setoption name Hash value -1");
    add(lines, "setoption name Hash value 0");
    add(lines, "setoption name Threads value -5");
    add(lines, "setoption name Threads value foo");
    add(lines, "setoption name Threads value 2");
    add(lines, "go nodes 30");
    add(lines, "stop");
    add(lines, "setoption name Threads value 1");
    add(lines, "setoption name OwnBook value true");
    add(lines, "setoption name OwnBook value maybe");
    add(lines, "setoption name OwnBook value false");
    add(lines, "setoption name Ponder value true");
    add(lines, "setoption name Ponder value false");
    add(lines, "setoption name Move Overhead value -1");
    add(lines, "setoption name Move Overhead value 99999");
    add(lines, "setoption name Move Overhead value 10");
    add(lines, "setoption name Clear Hash");
    add(lines, "setoption name Clear Hash value");
    add(lines, "setoption name Book File value nosuch-book.bin");
    add(lines, "setoption name Book File value <empty>");
    add(lines, "setoption name Book Depth value -1");
    add(lines, "setoption name Book Variety value 1000");
    add(lines, "setoption name Book Variety value -4");
    add(lines, "setoption name UseNNUE value maybe");
    add(lines, "setoption name UseNNUE value false");
    add(lines, "go depth 1");
    add(lines, "stop");
    add(lines, "setoption name UseNNUE value true");
    add(lines, "setoption name NotAnOption value 1");
    add(lines, "setoption name NotAnOption");
    add(lines, hundred_k_value());
    add(lines, hundred_k_name());
    add(lines, "setoption name Hash value 16");
    add(lines, high_bytes());
    add(lines, bytes_except_newline());
    add(lines, one_mb_line());
    add(lines, "zzzz");
    add(lines, "uciok");
    add(lines, "bestmove e2e4");
    add(lines, "uci");
    add(lines, "isready");
    add(lines, "uci isready");
    add(lines, "bench 1");
    add(lines, "bench 0");
    add(lines, "bench -5");
    add(lines, "position startpos moves " + std::string(1, static_cast<char>(0x80)) +
                   std::string(1, static_cast<char>(0x81)) + std::string(1, static_cast<char>(0x82)) +
                   std::string(1, static_cast<char>(0x83)));
    add(lines, "quit");
    return lines;
}

std::string noise(SplitMix& rng, int n) {
    static constexpr char alphabet[] =
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-.@#$%^&*()[]{}<>?!'`~|";
    std::string text;
    text.resize(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) {
        const std::uint64_t roll = rng.below(24);
        if (roll == 0) {
            text[static_cast<std::size_t>(i)] = static_cast<char>(128 + rng.below(128));
        } else if (roll == 1) {
            text[static_cast<std::size_t>(i)] = static_cast<char>(1 + rng.below(8));
        } else if (roll == 2) {
            text[static_cast<std::size_t>(i)] = '\0';
        } else {
            text[static_cast<std::size_t>(i)] = alphabet[rng.below(sizeof(alphabet) - 1)];
        }
    }
    return text;
}

std::string number_token(SplitMix& rng) {
    static constexpr std::string_view values[] = {
        "0",     "-1",     "-5",      "1",        "2",
        "3",     "7",      "16",      "32",       "64",
        "100",   "999999", "-999999", "2147483647", "2147483648",
        "4294967295", "999999999999999999999", "+5", "00", "--1",
        "1e9",   "0x10",   "-0",      "000",      "-",
    };
    if (rng.below(8) == 0) {
        const int digits = 1 + static_cast<int>(rng.below(48));
        std::string text = rng.below(2) == 0 ? "-" : "";
        for (int i = 0; i < digits; ++i) text.push_back(static_cast<char>('0' + rng.below(10)));
        return text;
    }
    return std::string(values[rng.below(sizeof(values) / sizeof(values[0]))]);
}

std::string fen_soup(SplitMix& rng) {
    static constexpr char pieces[] = "pnbrqkPNBRQK12345678/";
    const int n = 1 + static_cast<int>(rng.below(24));
    std::string text;
    text.resize(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) text[static_cast<std::size_t>(i)] = pieces[rng.below(sizeof(pieces) - 1)];
    return text;
}

std::string option_value(std::string_view name, SplitMix& rng) {
    if (name == "Hash") {
        static constexpr std::string_view values[] = {"1", "16", "0", "-1", "x", "99999999999999999999"};
        return std::string(values[rng.below(6)]);
    }
    if (name == "Threads") {
        static constexpr std::string_view values[] = {"1", "2", "0", "-5", "no", "99999999999999999999"};
        return std::string(values[rng.below(6)]);
    }
    if (name == "Book File") return "nosuch-" + noise(rng, 1 + static_cast<int>(rng.below(16)));
    if (name == "Ponder" || name == "OwnBook" || name == "UseNNUE") {
        static constexpr std::string_view values[] = {"true", "false", "TRUE", "yes", "0", "1", "maybe"};
        return std::string(values[rng.below(7)]);
    }
    return number_token(rng);
}

std::string generate_once(SplitMix& rng) {
    const std::uint64_t roll = rng.below(100);
    if (roll < 6) {
        static constexpr std::string_view blanks[] = {"", " ", "\t", "\t\t", " \t ", "\r", "\r "};
        return std::string(blanks[rng.below(7)]);
    }
    if (roll < 14) {
        if (rng.below(2) == 0) return noise(rng, 1 + static_cast<int>(rng.below(32)));
        std::string line;
        const int n = 1 + static_cast<int>(rng.below(24));
        for (int i = 0; i < n; ++i) line.push_back(static_cast<char>(128 + rng.below(128)));
        return line;
    }
    if (roll < 40) {
        const int kind = static_cast<int>(rng.below(6));
        if (kind == 0) return "position";
        if (kind == 1) return "position startpos";
        if (kind == 2) {
            std::string line = "position startpos moves";
            const int n = 1 + static_cast<int>(rng.below(10));
            for (int i = 0; i < n; ++i) {
                line.push_back(' ');
                const int pick = static_cast<int>(rng.below(6));
                if (pick == 0) line += "e2e4";
                else if (pick == 1) line += "e7e5";
                else if (pick == 2) line += "e2e5";
                else if (pick == 3) line += "e2";
                else if (pick == 4) line += noise(rng, 2 + static_cast<int>(rng.below(5)));
                else line += fen_soup(rng);
            }
            return line;
        }
        if (kind == 3) {
            static constexpr std::string_view fens[] = {
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "8/8/8/4k3/8/4K3/8/8 w - - 0 1",
                "8/8/8/8/8/4k3/4P3/4K3 w - - 0 1",
                "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1",
                "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
            };
            return std::string("position fen ") + std::string(fens[rng.below(5)]);
        }
        std::string line = "position fen";
        const int fields = static_cast<int>(rng.below(8));
        for (int i = 0; i < fields; ++i) {
            line.push_back(' ');
            if (rng.below(2) == 0) line += fen_soup(rng);
            else if (rng.below(2) == 0) line += number_token(rng);
            else line += noise(rng, 1 + static_cast<int>(rng.below(8)));
        }
        return line;
    }
    if (roll < 56) {
        if (rng.below(25) == 0) {
            return "go perft " + std::to_string(static_cast<int>(rng.below(3)));
        }
        std::string line = "go";
        static constexpr std::string_view keys[] = {
            "depth", "nodes", "movetime", "wtime", "btime", "winc", "binc", "movestogo",
            "mate",  "infinite", "ponder", "searchmoves", "blarg", "fen", "perft",
        };
        const int n = static_cast<int>(rng.below(6));
        for (int i = 0; i < n; ++i) {
            line.push_back(' ');
            const std::string_view key = keys[rng.below(sizeof(keys) / sizeof(keys[0]))];
            line += key;
            if (key == "infinite" || key == "ponder") continue;
            if (rng.below(4) == 0) continue;
            line.push_back(' ');
            if (key == "searchmoves") {
                line += rng.below(2) == 0 ? "e2e4" : noise(rng, 4);
            } else if (key == "perft") {
                line += std::to_string(static_cast<int>(rng.below(3)));
            } else {
                line += number_token(rng);
            }
        }
        if (rng.below(5) == 0) {
            line.push_back(' ');
            line += noise(rng, 1 + static_cast<int>(rng.below(8)));
        }
        return line;
    }
    if (roll < 80) {
        static constexpr std::string_view names[] = {
            "Hash", "Threads", "Move Overhead", "Ponder", "OwnBook", "Book File", "Book Depth", "Book Variety",
            "UseNNUE", "Clear Hash", "LmrQuietBase", "LmrQuietDivisor", "LmrNoisyBase", "NullMoveBase",
            "NullMoveDepthDivisor", "TmSoftDivisor", "TmHardPercent", "HistoryBonusQuadratic", "HistoryBonusLinear",
            "HistoryBonusMax", "FutilityBase", "SeeQuietMultiplier", "NotAnOption",
        };
        const int kind = static_cast<int>(rng.below(5));
        if (kind == 0) return "setoption";
        if (kind == 1) return "setoption name";
        if (kind == 2) return "setoption value " + number_token(rng);
        const std::string_view name = names[rng.below(sizeof(names) / sizeof(names[0]))];
        if (kind == 3) return std::string("setoption name ") + std::string(name);
        std::string line = std::string("setoption name ") + std::string(name) + " value ";
        if (rng.below(40) == 0) line.append(64 + static_cast<std::size_t>(rng.below(200)), 'Q');
        else line += option_value(name, rng);
        return line;
    }
    if (roll < 94) {
        static constexpr std::string_view commands[] = {"uci", "isready", "ucinewgame", "stop", "ponderhit", "foo",
                                                         "uciok", "zzzz"};
        return std::string(commands[rng.below(8)]);
    }
    if (rng.below(2) == 0) return "bench " + number_token(rng);
    return noise(rng, 1 + static_cast<int>(rng.below(12))) + " " + number_token(rng);
}

std::string generate_line(SplitMix& rng) {
    for (;;) {
        std::string line = generate_once(rng);
        const std::vector<std::string> tokens = tokens_of(line);
        if (tokens.empty() || tokens[0] != "quit") return line;
    }
}

bool run_session(const char* name, const std::vector<std::string>& lines, bool limit) {
    const auto started = std::chrono::steady_clock::now();
    DiscardBuf discard;
    std::streambuf* const previous = std::cout.rdbuf(&discard);
    Session session;
    session.start();
    std::string hang;
    bool ok = send_setup(session, hang);
    std::size_t index = 0;
    for (; ok && index < lines.size(); ++index) {
        const std::string& raw = lines[index];
        const std::string fed = limit ? limit_generated(raw) : raw;
        if (!session.send(fed, hang)) {
            std::cerr << name << " failed at index " << index << "\nraw: " << preview(raw) << "\nfed: " << preview(fed)
                      << "\n" << hang << "\n";
            ok = false;
            break;
        }
        if (index > 0 && index % 10000 == 0) {
            std::cerr << name << " " << index << "\n";
        }
    }
    if (ok && !session.finish(hang)) {
        std::cerr << name << " failed during shutdown\n" << hang << "\n";
        ok = false;
    }
    if (!ok) {
        std::cerr << name << " FAILED\n";
        std::_Exit(1);
    }
    std::cout.rdbuf(previous);
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - started);
    std::cerr << name << " cases=" << lines.size() << " ok time_ms=" << elapsed.count() << "\n";
    return true;
}

bool run_generated(int line_count) {
    const auto started = std::chrono::steady_clock::now();
    DiscardBuf discard;
    std::streambuf* const previous = std::cout.rdbuf(&discard);
    Session session;
    session.start();
    std::string hang;
    bool ok = send_setup(session, hang);
    SplitMix rng(kSeed);
    int index = 0;
    for (; ok && index < line_count; ++index) {
        const std::string raw = generate_line(rng);
        const std::string fed = limit_generated(raw);
        if (!session.send(fed, hang)) {
            std::cerr << "part_b failed at index " << index << "\nraw: " << preview(raw) << "\nfed: " << preview(fed)
                      << "\n" << hang << "\n";
            ok = false;
            break;
        }
        if (index > 0 && index % 10000 == 0) std::cerr << "part_b " << index << "\n";
    }
    if (ok) {
        if (!session.send("quit", hang)) {
            std::cerr << "part_b quit failed\n" << hang << "\n";
            ok = false;
        }
    }
    if (ok && !session.finish(hang)) {
        std::cerr << "part_b failed during shutdown\n" << hang << "\n";
        ok = false;
    }
    if (!ok) {
        std::cerr << "part_b FAILED\n";
        std::_Exit(1);
    }
    std::cout.rdbuf(previous);
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - started);
    std::cerr << "part_b seed=" << kSeed << " lines=" << line_count << " ok time_ms=" << elapsed.count() << "\n";
    return true;
}

}  // namespace

int main(int argc, char** argv) {
    self_check_driver();
    int line_count = kDefaultLines;
    if (argc >= 2) {
        int parsed = 0;
        const std::string text = argv[1];
        if (!parsed_int(text, parsed) || parsed < 0) {
            std::cerr << "usage: uci_fuzz [generated-line-count]\n";
            return 2;
        }
        line_count = parsed;
    }
    std::cerr << "seed=" << kSeed << " generated_lines=" << line_count << "\n";
    const std::vector<std::string> hand = part_a_lines();
    if (hand.size() < 80) {
        std::cerr << "part A has " << hand.size() << " cases, need at least 80\n";
        return 1;
    }
    std::cerr << "part_a hand_written=" << hand.size() << "\n";
    run_session("part_a", hand, false);
    run_generated(line_count);
    std::cerr << "SANITIZERS clean\n";
    return 0;
}
