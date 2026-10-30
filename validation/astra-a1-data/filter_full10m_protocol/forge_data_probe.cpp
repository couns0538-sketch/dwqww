// Offline, single-worker Forge position analysis. No engine/search policy changes.
// IDEA_SOURCE: user Astra A1 data contract and Forge public Board/Searcher/Evaluator APIs.
#include "forge/search.hpp"
#include "forge/eval.hpp"

#include <algorithm>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#if defined(_WIN32)
#define NOMINMAX
#include <windows.h>
#else
#include <sys/resource.h>
#endif

namespace {
using namespace forge;
constexpr std::size_t MaxLine = 4096;
struct Config { std::uint64_t nodes = 1024; std::size_t hash_mb = 1; int depth = 64; };
std::uint64_t integer(std::string_view s, std::uint64_t low, std::uint64_t high) {
    std::uint64_t n = 0;
    const auto parsed = std::from_chars(s.data(), s.data() + s.size(), n);
    if (s.empty() || parsed.ec != std::errc{} || parsed.ptr != s.data() + s.size() || n < low || n > high)
        throw std::runtime_error("integer outside supported range");
    return n;
}
std::string quote(std::string_view value) {
    static constexpr char hex[] = "0123456789abcdef";
    std::string out = "\"";
    for (const unsigned char c : value) {
        if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
        else if (c < 32 || c >= 127) {
            out += "\\u00"; out += hex[c >> 4U]; out += hex[c & 15U];
        } else out += static_cast<char>(c);
    }
    out += '"'; return out;
}
std::uint64_t cpu_ns() {
#if defined(_WIN32)
    FILETIME created{}, exited{}, kernel{}, user{};
    if (!GetProcessTimes(GetCurrentProcess(), &created, &exited, &kernel, &user))
        throw std::runtime_error("GetProcessTimes failed");
    const auto ticks = [](const FILETIME& time) {
        return (static_cast<std::uint64_t>(time.dwHighDateTime) << 32U) | time.dwLowDateTime;
    };
    return (ticks(kernel) + ticks(user)) * 100U;
#else
    rusage usage{};
    if (getrusage(RUSAGE_SELF, &usage) != 0) throw std::runtime_error("getrusage failed");
    return (static_cast<std::uint64_t>(usage.ru_utime.tv_sec) + static_cast<std::uint64_t>(usage.ru_stime.tv_sec)) * 1000000000ULL
         + (static_cast<std::uint64_t>(usage.ru_utime.tv_usec) + static_cast<std::uint64_t>(usage.ru_stime.tv_usec)) * 1000ULL;
#endif
}
// Bounded input allocation; drain an overlong record so the following row remains parseable.
bool line(std::string& out, bool& too_long) {
    out.clear(); too_long = false; bool read = false;
    for (int c; (c = std::cin.get()) != EOF;) {
        read = true; if (c == '\n') break;
        if (out.size() < MaxLine) out += static_cast<char>(c); else too_long = true;
    }
    if (!out.empty() && out.back() == '\r') out.pop_back();
    return read;
}
void validate_clocks(std::string_view fen) {
    std::istringstream in{std::string(fen)}; std::string fields[6], extra;
    for (auto& f : fields) if (!(in >> f)) throw std::runtime_error("FEN must contain six fields");
    if (in >> extra) throw std::runtime_error("FEN must contain exactly six fields");
    (void)integer(fields[4], 0, 65535); (void)integer(fields[5], 1, 65535);
}
std::string terminal_reason(const Board& board, const MoveList& moves) {
    if (moves.empty()) return board.in_check() ? "checkmate" : "stalemate";
    if (board.halfmove_clock() >= 100) return "fifty_move";
    if (board.is_insufficient_material()) return "insufficient_material";
    return {};
}
void timing(std::ostringstream& out, std::chrono::steady_clock::time_point start, std::uint64_t cpu_start) {
    const auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now() - start).count();
    const auto cpu = cpu_ns();
    out << ",\"elapsed_ns\":" << elapsed << ",\"cpu_ns\":" << (cpu - cpu_start)
        << ",\"process_cpu_ns\":" << cpu;
}
std::string request(std::string_view id, std::string_view op, std::string_view fen,
                    const Config& cfg, Searcher& searcher) {
    const auto started = std::chrono::steady_clock::now(); const auto cpu_start = cpu_ns();
    validate_clocks(fen);
    Board board; std::string error;
    if (!board.set_fen(fen, &error)) throw std::runtime_error("invalid FEN: " + error);
    const auto moves = board.legal_moves();
    const auto terminal = terminal_reason(board, moves);
    const int hce = Evaluator::evaluate_uncached(board);
    if (hce < -32767 || hce > 32767) throw std::runtime_error("HCE cannot fit FHCE int16 safely");
    std::ostringstream out; out << std::boolalpha;
    out << "{\"id\":" << quote(id) << ",\"operation\":" << quote(op) << ",\"ok\":true,\"fen\":" << quote(board.fen())
        << ",\"in_check\":" << board.in_check() << ",\"terminal\":" << !terminal.empty()
        << ",\"terminal_reason\":" << quote(terminal) << ",\"hce\":" << hce
        << ",\"nodes_limit\":" << cfg.nodes << ",\"hash_mb\":" << cfg.hash_mb << ",\"threads\":1";
    if (op == "inspect") {
        out << ",\"analyzed\":false,\"moves\":[";
        bool first = true;
        for (const auto move : moves) {
            Board child = board; Undo undo;
            if (!child.make_move(move, undo)) throw std::runtime_error("legal move rejected by make_move");
            if (!first) out << ',';
            first = false;
            out << "{\"uci\":" << quote(Board::move_to_uci(move)) << ",\"capture\":" << move.is_capture()
                << ",\"promotion\":" << move.is_promotion() << ",\"fen\":" << quote(child.fen()) << '}';
        }
        out << ']';
    } else if (!terminal.empty() || (op == "filter" && board.in_check())) {
        // No fabricated search label: these roots are removed before the quiet-position rule.
        out << ",\"analyzed\":false,\"bestmove\":null,\"capture\":false,\"promotion\":false,\"score\":null,\"nodes\":0,\"depth\":0";
    } else {
        // Clear TT, all histories and evaluation caches, so labels do not depend on row order.
        searcher.clear(); searcher.reset_stop();
        SearchLimits limits; limits.depth = cfg.depth; limits.nodes = cfg.nodes; limits.nodes_specified = true;
        const auto result = searcher.search(board, limits, false, Searcher::TTAccess::Exclusive);
        if (result.depth <= 0) throw std::runtime_error("node budget completed no iterative-deepening iteration");
        if (result.score < -MateValue || result.score > MateValue) throw std::runtime_error("invalid search score sentinel");
        if (result.best_move.is_none() || std::find(moves.begin(), moves.end(), result.best_move) == moves.end())
            throw std::runtime_error("search returned no legal best move");
        out << ",\"analyzed\":true,\"bestmove\":" << quote(Board::move_to_uci(result.best_move))
            << ",\"capture\":" << result.best_move.is_capture() << ",\"promotion\":" << result.best_move.is_promotion()
            << ",\"score\":" << result.score << ",\"nodes\":" << result.nodes << ",\"depth\":" << result.depth;
    }
    timing(out, started, cpu_start); out << '}'; return out.str();
}
} // namespace
int main(int argc, char** argv) {
    try {
        Config cfg;
        for (int i = 1; i < argc; ++i) {
            const std::string arg = argv[i];
            if (arg == "--version") {
                std::cout << "{\"protocol\":\"forge-data-probe-v1\",\"threads\":1,\"search_options\":\"default_OFF\",\"max_line_bytes\":4096,\"fen_history\":\"single_position_no_prior_repetition_history\"}\n";
                return 0;
            }
            if (i + 1 == argc) throw std::runtime_error("missing value for " + arg);
            const std::string value = argv[++i];
            if (arg == "--nodes") cfg.nodes = integer(value, 1, 1000000000ULL);
            else if (arg == "--hash-mb") cfg.hash_mb = static_cast<std::size_t>(integer(value, 1, 256));
            else if (arg == "--max-depth") cfg.depth = static_cast<int>(integer(value, 1, 64));
            else throw std::runtime_error("unknown argument " + arg);
        }
        // Initializes attack tables before the single worker is created. No worker thread is launched.
        Board initialized;
        auto searcher = std::make_unique<Searcher>(cfg.hash_mb, 1);
        std::string input; bool too_long = false;
        while (line(input, too_long)) {
            std::string id, operation;
            try {
                const auto a = input.find('\t');
                if (a != std::string::npos) id = input.substr(0, a);
                if (too_long) throw std::runtime_error("request exceeds 4096 bytes");
                if (a == std::string::npos || a == 0 || a > 128) throw std::runtime_error("request needs bounded nonempty id and tab separators");
                const auto b = input.find('\t', a + 1);
                if (b == std::string::npos || input.find('\t', b + 1) != std::string::npos)
                    throw std::runtime_error("request must have exactly three tab-separated fields");
                operation = input.substr(a + 1, b - a - 1);
                if (operation != "inspect" && operation != "analyze" && operation != "filter")
                    throw std::runtime_error("unknown operation");
                std::cout << request(id, operation, std::string_view(input).substr(b + 1), cfg, *searcher) << '\n';
            } catch (const std::exception& e) {
                std::cout << "{\"id\":" << quote(id.substr(0, 128)) << ",\"operation\":" << quote(operation)
                          << ",\"ok\":false,\"error\":" << quote(e.what()) << "}\n";
            }
            std::cout.flush(); if (!std::cout) return 3;
        }
        if (std::cin.bad()) throw std::runtime_error("input read failure");
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "forge_data_probe: " << e.what() << '\n'; return 2;
    }
}
