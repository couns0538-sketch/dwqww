// S41 NetScale tests: the forge::net_scale::apply arithmetic, the actual private Worker::static_evaluate path at
// every scale (independent oracle built from the public evaluator and nnue::evaluate on the same accumulator), the
// hand-crafted-only path (never scaled), and a search whose node count changes with the option and repeats at 100.
#include "forge/net_scale.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static SearchStack* root(Worker& w) { return &w.stack_[4]; }
    static int eval(Worker& w, const Board& b, SearchStack* ss) { return w.static_evaluate(b, ss); }
};
} // namespace forge

using namespace forge;
using Probe = SearcherTestProbe;

namespace {
int checks = 0;
int failures = 0;

void check(bool okay, const std::string& label) {
    ++checks;
    if (!okay) {
        ++failures;
        std::cout << "FAIL " << label << '\n';
    }
}

// Independent statement of the documented arithmetic: |v| * pct / 100 rounded down, sign restored.
int oracle_scale(int value, int pct) {
    const std::int64_t magnitude = value < 0 ? -static_cast<std::int64_t>(value) : static_cast<std::int64_t>(value);
    const std::int64_t scaled = magnitude * pct / 100;
    return static_cast<int>(value < 0 ? -scaled : scaled);
}

Board position(const std::string& fen) {
    Board b;
    std::string error;
    if (!b.set_fen(fen, &error)) throw std::runtime_error(fen + ": " + error);
    return b;
}

struct RestoreGlobals {
    ~RestoreGlobals() {
        net_scale::percent = net_scale::Default;
        nnue::enabled = true;
    }
};

const std::vector<std::string> fixtures{
    std::string(Board::StandardStartFen),
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "4k3/8/8/8/8/8/8/QQQQK3 w - - 0 1",          // huge material edge: large positive evaluation
    "qqqqk3/8/8/8/8/8/8/4K3 w - - 0 1",          // and its negative mirror for the side to move
    "8/8/8/4k3/8/8/4P3/4K3 b - - 0 1",
};
const std::vector<int> scales{100, 50, 51, 77, 90, 95, 98, 99, 101, 110, 133, 150};
} // namespace

int main() {
    RestoreGlobals restore;

    // 1. Constants and the default.
    check(net_scale::Default == 100, "Default is 100 (OFF)");
    check(net_scale::Minimum <= net_scale::Default && net_scale::Default <= net_scale::Maximum, "Default inside [Minimum, Maximum]");
    check(net_scale::percent == net_scale::Default, "process starts with NetScale OFF");

    // 2. apply(): identity at 100 for every value in range; documented arithmetic and odd symmetry elsewhere.
    int identity_bad = 0;
    for (int v = -40000; v <= 40000; ++v) identity_bad += net_scale::apply(v, 100) != v ? 1 : 0;
    check(identity_bad == 0, "apply(v, 100) == v for all v in [-40000, 40000]");
    int arithmetic_bad = 0;
    int symmetry_bad = 0;
    for (int pct = net_scale::Minimum; pct <= net_scale::Maximum; ++pct) {
        for (int v = -40000; v <= 40000; v += 7) {
            arithmetic_bad += net_scale::apply(v, pct) != oracle_scale(v, pct) ? 1 : 0;
            symmetry_bad += net_scale::apply(-v, pct) != -net_scale::apply(v, pct) ? 1 : 0;
        }
        for (const int v : {-1, 0, 1, 99, 100, 101, -99, -100, -101, 31871, -31871}) {
            arithmetic_bad += net_scale::apply(v, pct) != oracle_scale(v, pct) ? 1 : 0;
        }
    }
    check(arithmetic_bad == 0, "apply(v, pct) == trunc(v * pct / 100) for pct 50..150");
    check(symmetry_bad == 0, "apply(-v, pct) == -apply(v, pct)");
    check(net_scale::apply(-150, 99) == -148 && net_scale::apply(150, 99) == 148, "truncation toward zero (150 * 0.99)");

    // 3. The actual Worker::static_evaluate at every scale, against the independent oracle on the same accumulator.
    check(nnue::available() && nnue::residual(), "fixture uses the compiled residual network");
    SharedSearchState shared(1);
    auto owned = std::make_unique<Worker>(shared, 0);
    Worker& w = *owned;
    int worker_checks = 0;
    for (const std::string& fen : fixtures) {
        const Board b = position(fen);
        w.clear();
        SearchLimits limits;
        limits.depth = 1;
        const std::vector<Worker*> all{&w};
        net_scale::percent = net_scale::Default;
        (void)w.search(b, limits, false, all);
        SearchStack* ss = Probe::root(w);
        const int hce = Evaluator::evaluate_uncached(b);
        for (const int pct : scales) {
            net_scale::percent = pct;
            const int actual = Probe::eval(w, b, ss);
            const int network = nnue::evaluate(b, ss->accumulator);
            const int expected = std::clamp(oracle_scale(hce + network, pct), -MateInMaxPly + 1, MateInMaxPly - 1);
            check(actual == expected, fen + " NetScale " + std::to_string(pct) + ": Worker eval " + std::to_string(actual) +
                                          " == oracle " + std::to_string(expected));
            if (pct == net_scale::Default) {
                check(actual == std::clamp(hce + network, -MateInMaxPly + 1, MateInMaxPly - 1),
                      fen + " NetScale 100 equals the AL1 residual evaluation");
            }
            ++worker_checks;
        }
        // Hand-crafted-only path: never scaled.
        nnue::enabled = false;
        for (const int pct : {50, 100, 150}) {
            net_scale::percent = pct;
            check(Probe::eval(w, b, ss) == hce, fen + " UseNNUE off: NetScale " + std::to_string(pct) + " leaves the HCE unchanged");
        }
        nnue::enabled = true;
    }
    net_scale::percent = net_scale::Default;

    // 4. Search level: NetScale changes the search (ON != OFF) and 100 repeats exactly.
    auto nodes = [](int pct) {
        net_scale::percent = pct;
        Searcher searcher(16);
        searcher.clear();
        Board b = position("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
        SearchLimits limits;
        limits.depth = 7;
        const std::uint64_t n = searcher.search(b, limits, false, Searcher::TTAccess::Exclusive).nodes;
        net_scale::percent = net_scale::Default;
        return n;
    };
    const std::uint64_t off_a = nodes(100);
    const std::uint64_t off_b = nodes(100);
    const std::uint64_t on_90 = nodes(90);
    const std::uint64_t on_110 = nodes(110);
    check(off_a == off_b, "NetScale 100 search repeats exactly (" + std::to_string(off_a) + ")");
    check(on_90 != off_a, "NetScale 90 changes the search (" + std::to_string(on_90) + " vs " + std::to_string(off_a) + ")");
    check(on_110 != off_a, "NetScale 110 changes the search (" + std::to_string(on_110) + " vs " + std::to_string(off_a) + ")");

    std::cout << "worker scale checks " << worker_checks << ", search nodes off " << off_a << " / 90 " << on_90
              << " / 110 " << on_110 << '\n';
    std::cout << "SUMMARY checks=" << checks << " failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
