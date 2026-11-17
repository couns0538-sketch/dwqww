#include "forge/board.hpp"
#include "forge/uci.hpp"

#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <sstream>
#include <streambuf>
#include <string>
#include <string_view>
#include <thread>

namespace {

class PipeBuf : public std::streambuf {
public:
    void push(std::string_view text) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            queue_.append(text);
        }
        cv_.notify_all();
    }

    void close() {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            closed_ = true;
        }
        cv_.notify_all();
    }

protected:
    int_type underflow() override {
        if (gptr() < egptr()) return traits_type::to_int_type(*gptr());
        std::unique_lock<std::mutex> lock(mutex_);
        cv_.wait(lock, [this] { return pos_ < queue_.size() || closed_; });
        if (pos_ >= queue_.size()) return traits_type::eof();
        const std::size_t n = std::min(queue_.size() - pos_, sizeof(buf_));
        std::char_traits<char>::copy(buf_, queue_.data() + pos_, n);
        pos_ += n;
        setg(buf_, buf_, buf_ + n);
        return traits_type::to_int_type(*gptr());
    }

private:
    std::mutex mutex_;
    std::condition_variable cv_;
    std::string queue_;
    std::size_t pos_ = 0;
    bool closed_ = false;
    char buf_[4096]{};
};

class CaptureBuf : public std::streambuf {
public:
    bool wait_line_prefix(std::size_t& cursor, std::string_view prefix, int timeout_ms, std::string& matched) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
        std::unique_lock<std::mutex> lock(mutex_);
        while (true) {
            while (true) {
                const std::size_t nl = text_.find('\n', cursor);
                if (nl == std::string::npos) break;
                std::string line = text_.substr(cursor, nl - cursor);
                if (!line.empty() && line.back() == '\r') line.pop_back();
                cursor = nl + 1;
                if (line.rfind(prefix, 0) == 0) {
                    matched = std::move(line);
                    return true;
                }
            }
            if (cv_.wait_until(lock, deadline) == std::cv_status::timeout) return false;
        }
    }

protected:
    int_type overflow(int_type ch) override {
        if (ch != traits_type::eof()) {
            {
                std::lock_guard<std::mutex> lock(mutex_);
                text_.push_back(traits_type::to_char_type(ch));
            }
            cv_.notify_all();
        }
        return ch;
    }

private:
    std::mutex mutex_;
    std::condition_variable cv_;
    std::string text_;
};

bool legal_bestmove(std::string_view fen, const std::string& line, std::string& move_out) {
    std::istringstream in(line);
    std::string tag;
    if (!(in >> tag >> move_out) || tag != "bestmove") return false;
    forge::Board board;
    if (!board.set_fen(fen)) return false;
    const auto parsed = board.parse_uci(move_out);
    return parsed.has_value() && board.is_legal(*parsed);
}

} // namespace

int main() {
    PipeBuf pipe;
    CaptureBuf capture;
    std::istream uci_in(&pipe);
    std::streambuf* saved_cout = std::cout.rdbuf(&capture);
    std::thread engine([&uci_in] { (void)forge::uci_loop(uci_in); });

    int failures = 0;
    std::size_t cursor = 0;
    std::string line;
    std::string move;

    pipe.push("setoption name Threads value 1\nsetoption name Hash value 16\n"
              "setoption name OwnBook value false\nsetoption name MultiPV value 4\nisready\n");
    if (!capture.wait_line_prefix(cursor, "readyok", 5000, line)) ++failures;

    pipe.push("position startpos\ngo infinite\n");
    std::this_thread::sleep_for(std::chrono::milliseconds(300));
    const auto t_stop = std::chrono::steady_clock::now();
    pipe.push("stop\n");
    const bool got_inf = capture.wait_line_prefix(cursor, "bestmove ", 2000, line);
    const auto stop_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - t_stop).count();
    const bool ok_inf = got_inf && stop_ms <= 300 && legal_bestmove(forge::Board::StandardStartFen, line, move);
    if (!ok_inf) ++failures;

    const auto t_mt = std::chrono::steady_clock::now();
    pipe.push("position startpos\ngo movetime 200\n");
    const bool got_mt = capture.wait_line_prefix(cursor, "bestmove ", 2000, line);
    const auto mt_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - t_mt).count();
    std::string mt_move;
    const bool ok_mt = got_mt && mt_ms <= 400 && legal_bestmove(forge::Board::StandardStartFen, line, mt_move);
    if (!ok_mt) ++failures;

    constexpr std::string_view kMateFen = "6k1/5ppp/8/8/8/8/8/R6K w - - 0 1";
    const auto t_nodes = std::chrono::steady_clock::now();
    pipe.push("position fen 6k1/5ppp/8/8/8/8/8/R6K w - - 0 1\ngo nodes 2500\n");
    const bool got_nodes = capture.wait_line_prefix(cursor, "bestmove ", 2000, line);
    const auto nodes_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - t_nodes).count();
    std::string nodes_move;
    const bool ok_nodes = got_nodes && nodes_ms <= 400 && legal_bestmove(kMateFen, line, nodes_move) && nodes_move == "a1a8";
    if (!ok_nodes) ++failures;

    pipe.push("ucinewgame\nsetoption name MultiPV value 1\nisready\n");
    if (!capture.wait_line_prefix(cursor, "readyok", 5000, line)) ++failures;
    pipe.push("bench 11\nbench 13\n");
    std::string bench11;
    std::string bench13;
    const bool ok_b11 = capture.wait_line_prefix(cursor, "info string bench depth 11 nodes 312866 ", 60000, bench11);
    const bool ok_b13 = capture.wait_line_prefix(cursor, "info string bench depth 13 nodes 862329 ", 60000, bench13);
    if (!ok_b11 || !ok_b13) ++failures;

    pipe.push("quit\n");
    pipe.close();
    engine.join();
    std::cout.rdbuf(saved_cout);

    std::cout << "infinite_stop_ms " << stop_ms << " move " << move << (ok_inf ? " PASS\n" : " FAIL\n")
              << "movetime_200_ms " << mt_ms << " move " << mt_move << (ok_mt ? " PASS\n" : " FAIL\n")
              << "nodes_2500_ms " << nodes_ms << " move " << nodes_move << (ok_nodes ? " PASS\n" : " FAIL\n")
              << "multipv1_bench " << (ok_b11 && ok_b13 ? "PASS\n" : "FAIL\n");
    return failures == 0 ? 0 : 1;
}
