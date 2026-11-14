#include "forge/board.hpp"
#include "forge/search.hpp"
#include "forge/uci.hpp"

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

namespace {

constexpr std::uint64_t kBench11 = 312866;
constexpr std::uint64_t kBench13 = 862329;
constexpr std::uint64_t kPerft5 = 4865609;
constexpr int kSearchCount = 200;
constexpr int kSearchDepth = 10;

class CoutCapture {
public:
    CoutCapture() : previous_(std::cout.rdbuf(buffer_.rdbuf())) {}
    CoutCapture(const CoutCapture&) = delete;
    CoutCapture& operator=(const CoutCapture&) = delete;
    ~CoutCapture() { std::cout.rdbuf(previous_); }
    [[nodiscard]] std::string text() const { return buffer_.str(); }

private:
    std::ostringstream buffer_;
    std::streambuf* previous_;
};

std::string run_uci(std::string_view commands) {
    CoutCapture capture;
    std::istringstream input{std::string(commands)};
    const int code = forge::uci_loop(input);
    const std::string text = capture.text();
    if (code != 0) {
        std::cerr << "uci_loop returned " << code << '\n' << text << '\n';
    }
    return text;
}

[[nodiscard]] bool parse_u64_after(std::string_view text, std::string_view key, std::uint64_t& out) {
    const std::size_t at = text.find(key);
    if (at == std::string_view::npos) return false;
    const char* begin = text.data() + at + key.size();
    char* end = nullptr;
    const unsigned long long value = std::strtoull(begin, &end, 10);
    if (end == begin) return false;
    out = static_cast<std::uint64_t>(value);
    return true;
}

[[nodiscard]] std::uint64_t mix(std::uint64_t x) {
    x ^= x >> 30U;
    x *= 0xBF58476D1CE4E5B9ULL;
    x ^= x >> 27U;
    x *= 0x94D049BB133111EBULL;
    x ^= x >> 31U;
    return x;
}

std::vector<forge::Board> make_positions(int count) {
    constexpr std::string_view seeds[] = {
        forge::Board::StandardStartFen,
        "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 3 8",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "2r3k1/pp3ppp/4p3/3n4/3P2b1/2N1PN2/PP3PPP/R3K2R w KQ - 1 16",
        "4k3/8/4K3/8/8/8/4P3/8 w - - 0 1",
        "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    };

    std::vector<forge::Board> positions;
    positions.reserve(static_cast<std::size_t>(count));
    std::uint64_t state = 0xC0FFEE1234ABCDULL;
    for (std::size_t seed_index = 0; positions.size() < static_cast<std::size_t>(count); ++seed_index) {
        forge::Board board;
        const std::string_view fen = seeds[seed_index % (sizeof(seeds) / sizeof(seeds[0]))];
        if (!board.set_fen(fen)) continue;
        for (int ply = 0; ply < 24 && positions.size() < static_cast<std::size_t>(count); ++ply) {
            const forge::MoveList legal = board.legal_moves();
            if (legal.empty()) break;
            positions.push_back(board);
            state = mix(state + static_cast<std::uint64_t>(legal.size()) + seed_index);
            const forge::Move chosen = legal[static_cast<std::size_t>(state % legal.size())];
            forge::Undo undo;
            if (!board.make_move(chosen, undo)) break;
        }
    }
    return positions;
}

[[nodiscard]] bool move_is_legal(const forge::Board& board, forge::Move move) {
    if (move.is_none() || !board.is_legal(move)) return false;
    const forge::MoveList legal = board.legal_moves();
    for (const forge::Move candidate : legal) {
        if (candidate == move) return true;
    }
    return false;
}

int search_many(const std::vector<forge::Board>& positions) {
    forge::Searcher searcher(16, 1);
    int failures = 0;
    std::uint64_t nodes = 0;
    for (std::size_t i = 0; i < positions.size(); ++i) {
        if (i % 25 == 0) searcher.clear();
        forge::SearchLimits limits;
        limits.depth = kSearchDepth;
        const forge::SearchInfo info =
            searcher.search(positions[i], limits, false, forge::Searcher::TTAccess::Exclusive);
        nodes += info.nodes;
        if (!move_is_legal(positions[i], info.best_move)) {
            std::cerr << "illegal move at search " << i << ": " << forge::Board::move_to_uci(info.best_move) << '\n';
            ++failures;
        }
    }
    std::cout << "sanitizer_searches " << positions.size() << " depth " << kSearchDepth
              << " failures " << failures << " nodes " << nodes << '\n';
    return failures;
}

}  // namespace

int main() {
    int failures = 0;
    if (forge::tune::LmrLateParentRelief) {
        std::cerr << "option did not start off\n";
        ++failures;
    }

    const std::string identity = run_uci(
        "uci\n"
        "setoption name Threads value 1\n"
        "setoption name Hash value 16\n"
        "setoption name OwnBook value false\n"
        "isready\n"
        "bench 11\n"
        "bench 13\n"
        "position startpos\n"
        "go perft 5\n"
        "quit\n");

    const std::string option_line = "option name LmrLateParentRelief type check default false";
    if (identity.find(option_line) == std::string::npos) {
        std::cerr << "uci answer is missing the default-off option line\n";
        ++failures;
    }
    if (forge::tune::LmrLateParentRelief) {
        std::cerr << "advertising the option turned it on\n";
        ++failures;
    }

    std::uint64_t bench11 = 0;
    std::uint64_t bench13 = 0;
    std::uint64_t perft5 = 0;
    const bool parsed11 = parse_u64_after(identity, "info string bench depth 11 nodes ", bench11);
    const bool parsed13 = parse_u64_after(identity, "info string bench depth 13 nodes ", bench13);
    const bool parsed_perft = parse_u64_after(identity, "\nnodes ", perft5);
    std::cout << "defaults bench11 " << bench11 << " bench13 " << bench13 << " perft5 " << perft5 << '\n';
    if (!parsed11 || !parsed13 || !parsed_perft || bench11 != kBench11 || bench13 != kBench13 || perft5 != kPerft5) {
        std::cerr << "default bench or perft mismatch\n";
        ++failures;
    }

    const std::string enabled = run_uci(
        "setoption name LmrLateParentRelief value true\n"
        "isready\n"
        "bench 13\n"
        "quit\n");
    std::uint64_t bench13_on = 0;
    const bool parsed_on = parse_u64_after(enabled, "info string bench depth 13 nodes ", bench13_on);
    std::cout << "option_on bench13 " << bench13_on << '\n';
    if (!forge::tune::LmrLateParentRelief || !parsed_on || bench13_on == 0 || bench13_on == kBench13) {
        std::cerr << "bench 13 did not change with LmrLateParentRelief on\n";
        ++failures;
    }

    const std::string rejected = run_uci("setoption name LmrLateParentRelief value maybe\nquit\n");
    if (!forge::tune::LmrLateParentRelief || rejected.find("invalid value for option LmrLateParentRelief") == std::string::npos) {
        std::cerr << "invalid option value was accepted\n";
        ++failures;
    }

    const std::vector<forge::Board> positions = make_positions(kSearchCount);
    if (static_cast<int>(positions.size()) != kSearchCount) {
        std::cerr << "built " << positions.size() << " positions\n";
        return 1;
    }
    failures += search_many(positions);

    const std::string disabled = run_uci(
        "setoption name LmrLateParentRelief value false\n"
        "isready\n"
        "bench 11\n"
        "bench 13\n"
        "position startpos\n"
        "go perft 5\n"
        "quit\n");
    std::uint64_t bench11_after = 0;
    std::uint64_t bench13_after = 0;
    std::uint64_t perft_after = 0;
    const bool parsed_after =
        parse_u64_after(disabled, "info string bench depth 11 nodes ", bench11_after) &&
        parse_u64_after(disabled, "info string bench depth 13 nodes ", bench13_after) &&
        parse_u64_after(disabled, "\nnodes ", perft_after);
    std::cout << "defaults_after bench11 " << bench11_after << " bench13 " << bench13_after
              << " perft5 " << perft_after << '\n';
    if (forge::tune::LmrLateParentRelief || !parsed_after || bench11_after != kBench11 ||
        bench13_after != kBench13 || perft_after != kPerft5) {
        std::cerr << "defaults changed after turning the option off\n";
        ++failures;
    }

    if (failures != 0) {
        std::cerr << "FAIL late_parent_relief failures " << failures << '\n';
        return 1;
    }
    std::cout << "PASS late_parent_relief\n";
    return 0;
}
