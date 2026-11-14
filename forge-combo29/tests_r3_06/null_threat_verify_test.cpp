#include "forge/board.hpp"
#include "forge/search.hpp"
#include "forge/uci.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

constexpr std::uint64_t ExpectedBench11 = 312866;
constexpr std::uint64_t ExpectedBench13 = 862329;
constexpr std::uint64_t ExpectedPerft5 = 4865609;
constexpr std::string_view OptionLine = "option name NullThreatVerify type check default false";

class CoutCapture {
public:
    explicit CoutCapture(std::string& sink) : sink_(sink), old_(std::cout.rdbuf(buffer_.rdbuf())) {}
    ~CoutCapture() {
        std::cout.rdbuf(old_);
        sink_ = buffer_.str();
    }
    CoutCapture(const CoutCapture&) = delete;
    CoutCapture& operator=(const CoutCapture&) = delete;

private:
    std::string& sink_;
    std::ostringstream buffer_;
    std::streambuf* old_;
};

std::string run_uci(std::string_view script) {
    std::string output;
    {
        std::istringstream input{std::string(script)};
        CoutCapture capture(output);
        const int code = forge::uci_loop(input);
        if (code != 0) std::cerr << "uci_loop returned " << code << '\n';
    }
    return output;
}

int count_option(const std::string& text) {
    int count = 0;
    std::istringstream lines(text);
    std::string line;
    while (std::getline(lines, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line == OptionLine) ++count;
    }
    return count;
}

std::vector<std::uint64_t> bench_nodes(const std::string& text, int depth) {
    std::vector<std::uint64_t> found;
    const std::string prefix = "info string bench depth " + std::to_string(depth) + " nodes ";
    std::istringstream lines(text);
    std::string line;
    while (std::getline(lines, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.compare(0, prefix.size(), prefix) != 0) continue;
        std::uint64_t nodes = 0;
        std::istringstream rest(line.substr(prefix.size()));
        if (rest >> nodes) found.push_back(nodes);
    }
    return found;
}

std::uint64_t perft_total(const std::string& text) {
    std::uint64_t last = 0;
    std::istringstream lines(text);
    std::string line;
    while (std::getline(lines, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.rfind("nodes ", 0) != 0) continue;
        std::uint64_t nodes = 0;
        std::istringstream rest(line.substr(6));
        if (rest >> nodes) last = nodes;
    }
    return last;
}

bool move_is_legal(const forge::Board& board, forge::Move move) {
    if (move.is_none() || !board.is_legal(move)) return false;
    const forge::MoveList legal = board.legal_moves();
    for (const forge::Move candidate : legal) {
        if (candidate == move) return true;
    }
    return false;
}

std::vector<forge::Board> two_hundred_positions() {
    std::vector<forge::Board> positions;
    positions.reserve(200);
    std::uint64_t rng = 0x6A09E667F3BCC909ULL;
    auto next_word = [&rng]() {
        rng = rng * 6364136223846793005ULL + 1442695040888963407ULL;
        return rng;
    };
    forge::Board board;
    (void)board.set_fen(forge::Board::StandardStartFen);
    int steps_since_reset = 0;
    while (positions.size() < 200) {
        forge::MoveList legal = board.legal_moves();
        const bool reset = legal.empty() || board.halfmove_clock() >= 80 || steps_since_reset >= 24;
        if (reset) {
            (void)board.set_fen(forge::Board::StandardStartFen);
            legal = board.legal_moves();
            steps_since_reset = 0;
        }
        positions.push_back(board);
        const forge::Move chosen = legal[static_cast<std::size_t>(next_word() % legal.size())];
        forge::Undo undo;
        (void)board.make_move(chosen, undo);
        ++steps_since_reset;
    }
    return positions;
}

int check_threat_predicate() {
    const std::array<std::pair<std::string_view, bool>, 11> cases{{
        {forge::Board::StandardStartFen, false},
        {"8/8/8/4p3/3N4/8/8/4K2k w - - 0 1", true},
        {"8/8/4n3/8/3B4/8/8/4K2k w - - 0 1", false},
        {"3r4/8/8/8/3Q4/8/8/4K2k w - - 0 1", true},
        {"3q4/8/8/8/3R4/8/8/4K2k w - - 0 1", false},
        {"8/8/8/8/8/8/1k6/R6K w - - 0 1", false},
        {"8/8/8/4p3/3Q4/8/8/4K2k w - - 0 1", true},
        {"4k3/8/8/3n4/2P5/8/8/4K3 b - - 0 1", true},
        {"3r4/8/3p4/8/3Q4/8/8/4K2k w - - 0 1", false},
        {"8/8/1n6/8/R7/8/8/4K2k w - - 0 1", true},
        {"8/8/8/8/8/2N5/8/b3K2k w - - 0 1", false},
    }};
    int failures = 0;
    for (const auto& item : cases) {
        forge::Board board;
        if (!board.set_fen(item.first)) {
            std::cerr << "FAIL predicate fen rejected " << item.first << '\n';
            ++failures;
            continue;
        }
        const bool got = forge::cheaper_enemy_attacks_dearer(board);
        if (got != item.second) {
            std::cerr << "FAIL predicate " << item.first << " expected " << item.second << " got " << got << '\n';
            ++failures;
        }
    }
    std::cout << "predicate cases " << cases.size() << " failures " << failures << '\n';
    return failures;
}

int search_two_hundred() {
    if (!forge::tune::NullThreatVerify) {
        std::cerr << "FAIL NullThreatVerify was not left on before the depth-10 searches\n";
        return 1;
    }
    const std::vector<forge::Board> positions = two_hundred_positions();
    if (positions.size() != 200) {
        std::cerr << "FAIL built " << positions.size() << " positions\n";
        return 1;
    }
    forge::Searcher searcher(16, 1);
    int failures = 0;
    for (std::size_t i = 0; i < positions.size(); ++i) {
        if (i % 25 == 0) searcher.clear();
        forge::SearchLimits limits;
        limits.depth = 10;
        const forge::SearchInfo info =
            searcher.search(positions[i], limits, false, forge::Searcher::TTAccess::Exclusive);
        if (!move_is_legal(positions[i], info.best_move)) {
            std::cerr << "FAIL illegal move at " << i << " " << positions[i].fen() << " move "
                      << forge::Board::move_to_uci(info.best_move) << '\n';
            ++failures;
            break;
        }
    }
    std::cout << "depth10 searches " << positions.size() << " illegal " << failures << '\n';
    return failures;
}

}  // namespace

int main() {
    int failures = 0;
    if (forge::tune::NullThreatVerify) {
        std::cerr << "FAIL NullThreatVerify default is not false\n";
        ++failures;
    }

    const std::string defaults = run_uci(
        "uci\n"
        "setoption name Threads value 1\n"
        "setoption name Hash value 16\n"
        "setoption name OwnBook value false\n"
        "isready\n"
        "bench 11\n"
        "bench 13\n"
        "position startpos\n"
        "go perft 5\n"
        "setoption name NullThreatVerify value true\n"
        "bench 13\n"
        "quit\n");

    if (count_option(defaults) != 1) {
        std::cerr << "FAIL uci option line count " << count_option(defaults) << '\n';
        ++failures;
    }
    if (defaults.find("unknown option") != std::string::npos ||
        defaults.find("invalid value") != std::string::npos) {
        std::cerr << "FAIL uci reported an option error\n";
        ++failures;
    }
    const std::vector<std::uint64_t> bench11 = bench_nodes(defaults, 11);
    const std::vector<std::uint64_t> bench13 = bench_nodes(defaults, 13);
    const std::uint64_t perft5 = perft_total(defaults);
    if (bench11.size() != 1 || bench11[0] != ExpectedBench11) {
        std::cerr << "FAIL default bench 11\n";
        ++failures;
    }
    if (bench13.size() != 2 || bench13[0] != ExpectedBench13) {
        std::cerr << "FAIL default bench 13\n";
        ++failures;
    }
    if (perft5 != ExpectedPerft5) {
        std::cerr << "FAIL default perft 5 " << perft5 << '\n';
        ++failures;
    }
    if (!forge::tune::NullThreatVerify) {
        std::cerr << "FAIL setoption did not enable NullThreatVerify\n";
        ++failures;
    }
    const std::uint64_t bench13_on = bench13.size() == 2 ? bench13[1] : 0;
    std::cout << "defaults bench11 " << (bench11.empty() ? 0 : bench11[0]) << " bench13 "
              << (bench13.empty() ? 0 : bench13[0]) << " perft5 " << perft5 << '\n';
    std::cout << "NullThreatVerify bench13 " << bench13_on << '\n';
    if (bench13_on == 0 || bench13_on == ExpectedBench13) {
        std::cerr << "FAIL bench 13 did not change with NullThreatVerify on\n";
        ++failures;
    }

    failures += check_threat_predicate();
    failures += search_two_hundred();

    forge::tune::NullThreatVerify = false;
    const std::string restored = run_uci(
        "setoption name Threads value 1\n"
        "setoption name Hash value 16\n"
        "setoption name OwnBook value false\n"
        "setoption name NullThreatVerify value false\n"
        "bench 11\n"
        "bench 13\n"
        "position startpos\n"
        "go perft 5\n"
        "quit\n");
    const std::vector<std::uint64_t> bench11_back = bench_nodes(restored, 11);
    const std::vector<std::uint64_t> bench13_back = bench_nodes(restored, 13);
    const std::uint64_t perft_back = perft_total(restored);
    std::cout << "restored bench11 " << (bench11_back.empty() ? 0 : bench11_back[0]) << " bench13 "
              << (bench13_back.empty() ? 0 : bench13_back[0]) << " perft5 " << perft_back << '\n';
    if (bench11_back.size() != 1 || bench11_back[0] != ExpectedBench11 || bench13_back.size() != 1 ||
        bench13_back[0] != ExpectedBench13 || perft_back != ExpectedPerft5 || forge::tune::NullThreatVerify) {
        std::cerr << "FAIL defaults changed after turning NullThreatVerify off\n";
        ++failures;
    }

    if (failures != 0) {
        std::cerr << "FAIL null_threat_verify_test failures " << failures << '\n';
        return 1;
    }
    std::cout << "PASS null_threat_verify_test\n";
    return 0;
}
