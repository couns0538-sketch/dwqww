#include "forge/board.hpp"
#include "forge/search.hpp"
#include "forge/tm_finish.hpp"

#include <cstdint>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

int g_failures = 0;

void expect(bool ok, const std::string& name) {
    if (ok) {
        std::cout << "PASS " << name << '\n';
        return;
    }
    std::cerr << "FAIL " << name << '\n';
    ++g_failures;
}

void test_made_up_timings() {
    struct Case {
        std::int64_t prev;
        std::int64_t last;
        std::int64_t remaining;
        bool skip;
        const char* name;
    };
    // Invented millisecond triples. A step with last <= 2*prev extends as
    // last*last/prev. A larger step uses sqrt(last*prev) and skips when
    // last*prev > remaining*remaining. Non-positive samples stay; a spent
    // budget skips.
    const Case cases[] = {
        {100, 400, 1600, false, "spike mean 200 inside 1600 stays"},
        {100, 400, 1599, false, "spike mean 200 inside 1599 stays"},
        {100, 400, 199, true, "spike mean 200 over 199 skips"},
        {100, 400, 200, false, "spike mean 200 equal 200 stays"},
        {0, 500, 1, false, "missing previous sample stays"},
        {10, 0, 1, false, "missing last sample stays"},
        {-3, 40, 5, false, "negative previous stays"},
        {8, -1, 5, false, "negative last stays"},
        {10, 10, 0, true, "budget already spent skips"},
        {10, 10, -4, true, "negative budget skips"},
        {5, 20, 79, false, "spike mean 10 inside 79 stays"},
        {5, 20, 9, true, "spike mean 10 over 9 skips"},
        {5, 20, 10, false, "spike mean 10 equal 10 stays"},
        {1, 1, 1, false, "flat one millisecond stays"},
        {1, 2, 3, true, "double growth 4 against 3 skips"},
        {1, 2, 4, false, "double growth 4 equal 4 stays"},
        {100, 10, 5, false, "shrinking iteration stays"},
        {3, 3, 100, false, "slow growth stays"},
        {1, 100000, 50, true, "steep spike still skips a 50 ms budget"},
        {16, 86, 34, true, "measured spike shape 16 then 86 skips a 34 ms budget"},
        {16, 86, 38, false, "measured spike shape fits a 38 ms budget"},
        {16, 32, 50, true, "exact double still compounds 64 against 50"},
        {16, 33, 40, false, "just past double uses the mean 23 inside 40"},
        {10, 20, 30, true, "exact double 40 against 30 skips"},
        {20, 30, 50, false, "ratio 1.5 predicts 45 inside 50"},
        {1000000000LL, 2000000000LL, 3000000000LL, true, "wide double compounds"},
        {2000000000LL, 2000000000LL, 2000000000LL, false, "wide equal product stays"},
        {2000000000LL, 5000000000LL, 6000000000LL, false, "wide spike mean stays under the budget"},
        {4000000000LL, 5000000000LL, 7000000000LL, false, "wide modest ratio stays"},
    };
    for (const Case& item : cases) {
        const bool got = forge::iteration_will_not_finish(item.prev, item.last, item.remaining);
        expect(got == item.skip, std::string("timing ") + item.name + " prev " + std::to_string(item.prev) +
                                      " last " + std::to_string(item.last) + " remaining " +
                                      std::to_string(item.remaining));
    }
}

struct ClockRun {
    int depth = 0;
    std::uint64_t elapsed_ms = 0;
    std::string move;
    std::string log;
    bool held = false;
    int hold_depth = 0;
    std::int64_t prev = 0;
    std::int64_t last = 0;
    std::int64_t remaining = 0;
    int max_info_depth = 0;
    bool move_legal = false;
};

bool parse_hold(const std::string& log, int& depth, std::int64_t& prev, std::int64_t& last,
                std::int64_t& remaining) {
    const std::string key = "TmFinishIteration hold depth ";
    const auto pos = log.find(key);
    if (pos == std::string::npos) return false;
    std::istringstream in(log.substr(pos + key.size()));
    std::string word;
    in >> depth >> word >> prev >> word >> last >> word >> remaining;
    return static_cast<bool>(in) && word == "remaining";
}

int max_info_depth(const std::string& log) {
    int deepest = 0;
    std::istringstream lines(log);
    std::string line;
    while (std::getline(lines, line)) {
        constexpr const char* prefix = "info depth ";
        if (line.compare(0, 11, prefix) != 0) continue;
        int depth = 0;
        std::istringstream in(line.substr(11));
        in >> depth;
        if (depth > deepest) deepest = depth;
    }
    return deepest;
}

bool returned_move_legal(const forge::Board& board, const forge::Move& move) {
    const forge::MoveList legal = board.legal_moves();
    if (legal.empty()) return move.is_none();
    for (const forge::Move candidate : legal) {
        if (candidate == move) return true;
    }
    return false;
}

ClockRun play_clock(std::string_view fen, std::int64_t wtime_ms, bool option) {
    forge::tune::TmFinishIteration = option;
    forge::Board board;
    ClockRun run;
    if (!board.set_fen(fen)) {
        run.log = "bad fen";
        return run;
    }
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.time_ms = wtime_ms;
    limits.move_overhead_ms = 10;
    std::ostringstream captured;
    std::streambuf* previous = std::cout.rdbuf(captured.rdbuf());
    const forge::SearchInfo info = searcher.search(board, limits, true);
    std::cout.rdbuf(previous);
    run.depth = info.depth;
    run.elapsed_ms = info.elapsed_ms;
    run.move = forge::Board::move_to_uci(info.best_move);
    run.log = captured.str();
    run.move_legal = returned_move_legal(board, info.best_move);
    run.max_info_depth = max_info_depth(run.log);
    run.held = parse_hold(run.log, run.hold_depth, run.prev, run.last, run.remaining);
    return run;
}

void test_clock_search() {
    const std::string_view fens[] = {
        forge::Board::StandardStartFen,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    };
    const std::int64_t budgets[] = {200, 400, 800, 1500, 3000, 6000};
    ClockRun held;
    std::string fen_used;
    std::int64_t budget_used = 0;
    bool found = false;
    for (const std::string_view fen : fens) {
        for (const std::int64_t budget : budgets) {
            ClockRun run = play_clock(fen, budget, true);
            std::cout << "clock try budget " << budget << " depth " << run.depth << " elapsed " << run.elapsed_ms
                      << " move " << run.move << " held " << (run.held ? "yes" : "no") << '\n';
            if (!run.move_legal) {
                expect(false, "clock move legal during search");
                std::cerr << run.log;
                return;
            }
            if (!run.held) continue;
            held = std::move(run);
            fen_used = std::string(fen);
            budget_used = budget;
            found = true;
            break;
        }
        if (found) break;
    }
    expect(found, "clock search printed a hold");
    if (!found) return;
    const bool agrees =
        forge::iteration_will_not_finish(held.prev, held.last, held.remaining);
    expect(agrees, "hold numbers match iteration_will_not_finish");
    expect(held.hold_depth == held.depth, "played depth is the held finished depth");
    expect(held.max_info_depth == held.hold_depth, "no deeper finished info line");
    expect(held.move_legal, "held best move is legal");
    std::cout << "HOLD fen " << fen_used << '\n';
    std::cout << "HOLD wtime " << budget_used << " depth " << held.depth << " move " << held.move << " prev "
              << held.prev << " last " << held.last << " remaining " << held.remaining << " elapsed "
              << held.elapsed_ms << '\n';
    std::cout << held.log;

    forge::tune::TmFinishIteration = false;
    const ClockRun off = play_clock(fen_used, budget_used, false);
    expect(off.log.find("TmFinishIteration hold") == std::string::npos, "option off prints no hold");
    expect(off.move_legal, "option off clock move is legal");
    std::cout << "OFF depth " << off.depth << " elapsed " << off.elapsed_ms << " move " << off.move << '\n';
    forge::tune::TmFinishIteration = false;
}

std::vector<std::string> sample_positions(int count) {
    std::vector<std::string> fens;
    fens.reserve(static_cast<std::size_t>(count));
    forge::Board board;
    (void)board.set_fen(forge::Board::StandardStartFen);
    std::mt19937 rng(15);
    while (static_cast<int>(fens.size()) < count) {
        const forge::MoveList legal = board.legal_moves();
        const bool stop = legal.empty() || board.halfmove_clock() >= 80 || board.is_insufficient_material() ||
                          board.fullmove_number() > 36;
        if (stop) {
            (void)board.set_fen(forge::Board::StandardStartFen);
            continue;
        }
        std::uniform_int_distribution<int> pick(0, static_cast<int>(legal.size()) - 1);
        forge::Undo undo;
        if (!board.make_move(legal[static_cast<std::size_t>(pick(rng))], undo)) {
            (void)board.set_fen(forge::Board::StandardStartFen);
            continue;
        }
        fens.push_back(board.fen());
    }
    return fens;
}

void test_two_hundred_depth10() {
    forge::tune::TmFinishIteration = true;
    const std::vector<std::string> fens = sample_positions(200);
    expect(static_cast<int>(fens.size()) == 200, "sampled 200 positions");
    forge::Searcher searcher(16, 1);
    int illegal = 0;
    for (int index = 0; index < static_cast<int>(fens.size()); ++index) {
        forge::Board board;
        if (!board.set_fen(fens[static_cast<std::size_t>(index)])) {
            ++illegal;
            std::cerr << "FAIL bad fen " << index << '\n';
            continue;
        }
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = 10;
        const forge::SearchInfo info = searcher.search(board, limits, false);
        if (!returned_move_legal(board, info.best_move)) {
            ++illegal;
            std::cerr << "FAIL illegal move " << forge::Board::move_to_uci(info.best_move) << " fen "
                      << fens[static_cast<std::size_t>(index)] << '\n';
        }
        if ((index + 1) % 25 == 0) {
            std::cout << "depth10 " << (index + 1) << "/200 move " << forge::Board::move_to_uci(info.best_move)
                      << '\n';
        }
    }
    expect(illegal == 0, "200 depth-10 searches returned legal moves");
    forge::tune::TmFinishIteration = false;
}

void test_fixed_depth_ignores_option() {
    auto nodes = [](bool option) {
        forge::tune::TmFinishIteration = option;
        forge::Board board;
        (void)board.set_fen(forge::Board::StandardStartFen);
        forge::Searcher searcher(16, 1);
        forge::SearchLimits limits;
        limits.depth = 6;
        return searcher.search(board, limits, false).nodes;
    };
    const std::uint64_t off = nodes(false);
    const std::uint64_t on = nodes(true);
    expect(off == on && off > 0, "depth 6 startpos nodes match with option on and off (" + std::to_string(off) + ")");
    forge::tune::TmFinishIteration = false;
    expect(forge::tune::TmFinishIteration == false, "option defaults to off");
}

}  // namespace

int main(int argc, char** argv) {
    bool deep = true;
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--no-deep") deep = false;
    }
    expect(forge::tune::TmFinishIteration == false, "TmFinishIteration starts false");
    test_made_up_timings();
    test_fixed_depth_ignores_option();
    test_clock_search();
    if (deep) test_two_hundred_depth10();
    if (g_failures != 0) {
        std::cerr << g_failures << " failure(s)\n";
        return 1;
    }
    std::cout << "all passed\n";
    return 0;
}
