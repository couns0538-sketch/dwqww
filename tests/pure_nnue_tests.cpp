// Tests for UCI PureNnue (O4; rule in forge/search_options.hpp): the evaluation is a stand-alone v2 net alone,
// without the hand-crafted evaluation (HCE).
//   1. selection and the fail-loud request rule (options::apply_nnue_v2 / nnue_v2_problem): PureNnue needs a
//      stand-alone net; a residual net with PureNnue and a stand-alone net without PureNnue are errors; with
//      NNUEKingBuckets 0 PureNnue selects a one-bucket net, with NNUEKingBuckets N a net of N buckets; UseNNUE
//      false wins; the C4 rules for residual nets are unchanged;
//   2. the evaluation path: over random make/unmake walks driven through the real Worker::static_evaluate,
//      PureNnue gives exactly the network's evaluation (and never builds the HCE's PSQT accumulator), while the
//      same weights flagged residual give clamp(HCE + network); every accumulator the engine computed equals a
//      from-scratch refresh;
//   3. search: a PureNnue search is deterministic and searches another tree than the residual-flagged twin;
//   4. UCI (when the engine executable is given as argv[1]): the option is advertised, errors exit with status 2,
//      a stand-alone net becomes active and searches.
// usage: forge_pure_nnue_tests [<forge executable>] [plies per walk net (default 12000)]
// Writes temporary files into the working directory (removed at the end).
#include "forge/nnue_v2.hpp"
#include "forge/search.hpp"
#include "forge/search_options.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#if !defined(_WIN32)
#include <sys/wait.h>
#endif

namespace forge {
struct SearcherTestProbe {
    static SearchStack* root(Worker& w) { return &w.stack_[4]; }
    static int eval(Worker& w, const Board& b, SearchStack* ss) { return w.static_evaluate(b, ss); }
    static void move(Worker& w, SearchStack* ss, const Board& b, Move m) { w.record_move(ss, b, m); (ss + 1)->ply = ss->ply + 1; }
    static void null(Worker& w, SearchStack* ss) { w.record_null_move(ss); (ss + 1)->ply = ss->ply + 1; }
};
} // namespace forge

using namespace forge;
using Probe = SearcherTestProbe;
namespace v2 = forge::nnue::v2;

namespace {

int checks = 0;
int failures = 0;
void report(bool okay, const std::string& label) {
    ++checks;
    if (!okay) ++failures;
    std::cout << (okay ? "PASS " : "FAIL ") << label << '\n';
}

struct Rng {
    std::uint64_t s;
    std::uint64_t next() {
        s ^= s >> 12U; s ^= s << 25U; s ^= s >> 27U;
        return s * 2685821657736338717ULL;
    }
    int below(int n) { return static_cast<int>(next() % static_cast<std::uint64_t>(n)); }
    bool chance(int percent) { return below(100) < percent; }
};

std::vector<std::string> temporary_files;

// ---------------------------------------------------------------- v2 files (independent writer, format in nnue_v2.hpp)
struct Spec {
    int king_buckets = 1;
    bool mirror = false;
    bool residual = false;
    std::array<std::uint8_t, 64> king_map{};
    std::vector<std::int16_t> w1, b1, w2, b2;
};

std::uint64_t fnv(const std::string& data) {
    std::uint64_t h = 0xcbf29ce484222325ULL;
    for (const unsigned char c : data) { h ^= c; h *= 0x100000001b3ULL; }
    return h;
}
void put32(std::string& s, std::uint32_t v) { for (int i = 0; i < 4; ++i) s.push_back(static_cast<char>((v >> (8 * i)) & 0xFFU)); }
void putf(std::string& s, float f) { std::uint32_t v = 0; std::memcpy(&v, &f, 4); put32(s, v); }

std::string serialise(const Spec& n) {
    std::string s = "FORGENN2";
    put32(s, 2); put32(s, 160); put32(s, 0); put32(s, 768); put32(s, nnue::HiddenSize);
    put32(s, static_cast<std::uint32_t>(n.king_buckets)); put32(s, 1); put32(s, (n.residual ? 1U : 0U) | (n.mirror ? 2U : 0U));
    putf(s, 4096.0F); putf(s, 4096.0F); putf(s, 2.25F);
    for (const std::uint8_t b : n.king_map) s.push_back(static_cast<char>(b));
    s.append(33, '\0');
    s.append(160 - s.size(), '\0');
    for (const auto* a : {&n.w1, &n.b1, &n.w2, &n.b2}) {
        for (const std::int16_t v : *a) {
            const auto u = static_cast<std::uint16_t>(v);
            s.push_back(static_cast<char>(u & 0xFFU));
            s.push_back(static_cast<char>(u >> 8U));
        }
    }
    const std::uint64_t h = fnv(s);
    for (int i = 0; i < 8; ++i) s.push_back(static_cast<char>((h >> (8 * i)) & 0xFFU));
    return s;
}

void write_file(const std::string& path, const std::string& bytes) {
    std::ofstream out(path, std::ios::binary);
    out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
    if (std::find(temporary_files.begin(), temporary_files.end(), path) == temporary_files.end()) temporary_files.push_back(path);
}

std::string read_file(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    std::ostringstream text;
    text << in.rdbuf();
    return text.str();
}

int half_index(int square) { const int f = square & 7; return (square >> 3) * 4 + (f < 4 ? f : 7 - f); }
std::array<std::uint8_t, 64> map4() {   // the standard mirrored 4-bucket layout of tools/nnue/forge_nnue_v2.py
    const char* rows[8] = {"0011", "0011", "2222", "2222", "3333", "3333", "3333", "3333"};
    std::array<std::uint8_t, 64> m{};
    for (int s = 0; s < 64; ++s) {
        const int h = half_index(s);
        m[static_cast<std::size_t>(s)] = static_cast<std::uint8_t>(rows[h / 4][h % 4] - '0');
    }
    return m;
}

// Random weights with an evaluation scale like a real net's (most evaluations within a few hundred cp).
Spec random_net(int buckets, bool mirror, bool residual, std::uint64_t seed) {
    Spec n;
    Rng rng{seed};
    n.king_buckets = buckets;
    n.mirror = mirror;
    n.residual = residual;
    if (buckets == 4) n.king_map = map4();
    const std::size_t hidden = nnue::HiddenSize;
    auto value = [&rng](int range) { return static_cast<std::int16_t>(rng.below(2 * range + 1) - range); };
    n.w1.resize(static_cast<std::size_t>(buckets) * 768 * hidden);
    for (auto& v : n.w1) v = value(220);
    n.b1.resize(hidden);
    for (auto& v : n.b1) v = value(1200);
    n.w2.resize(2 * hidden);
    for (auto& v : n.w2) v = value(900);
    n.b2 = {value(500)};
    return n;
}

bool load_spec(const std::string& path, const Spec& n) {
    write_file(path, serialise(n));
    std::string error;
    const bool ok = v2::load(path, &error);
    if (!ok) std::cout << "load error: " << error << '\n';
    return ok;
}

// The UCI layer's sequence after an option change, then the request rule.
std::string problem_after(int king_buckets, bool pure, const std::string& file, const std::string& load_error = "") {
    options::nnue_king_buckets = king_buckets;
    options::pure_nnue = pure;
    (void)options::apply_nnue_v2(nullptr);
    return options::nnue_v2_problem(file, load_error);
}
bool contains(const std::string& text, const std::string& what) { return text.find(what) != std::string::npos; }

// ---------------------------------------------------------------- 1. selection and request rule
void test_rules(const std::string& dir) {
    const std::string pure1 = dir + "pure1.fnn2";
    const std::string resid1 = dir + "resid1.fnn2";
    const std::string pure4 = dir + "pure4.fnn2";
    const std::string resid4 = dir + "resid4.fnn2";
    v2::unload();
    std::string p = problem_after(0, false, "");
    report(p.empty() && !options::nnue_v2, "defaults: no request, no problem, compiled-in net");
    p = problem_after(0, true, "");
    report(contains(p, "PureNnue is 1 but no v2 net is loaded") && !options::nnue_v2, "PureNnue without NNUEFile: " + p);
    p = problem_after(0, true, dir + "missing.fnn2", "cannot open " + dir + "missing.fnn2");
    report(contains(p, "cannot open") && !options::nnue_v2, "PureNnue with a file that did not load: " + p);

    report(load_spec(resid1, random_net(1, false, true, 81)), "load a residual one-bucket net");
    p = problem_after(0, true, resid1);
    report(contains(p, "is a residual net") && !options::nnue_v2 && v2::active() == nullptr, "PureNnue with a residual net: " + p);
    p = problem_after(1, false, resid1);
    report(p.empty() && options::nnue_v2 && v2::active() == v2::loaded() && v2::active()->residual,
           "C4 rule unchanged: residual one-bucket net with NNUEKingBuckets 1 and PureNnue 0 is active");
    p = problem_after(0, false, resid1);
    report(contains(p, "NNUEKingBuckets is 0") && !options::nnue_v2, "C4 rule unchanged: residual net, NNUEKingBuckets 0: " + p);

    report(load_spec(pure1, random_net(1, false, false, 82)), "load a stand-alone one-bucket net");
    p = problem_after(0, true, pure1);
    report(p.empty() && options::nnue_v2 && v2::active() == v2::loaded() && !v2::active()->residual,
           "PureNnue with a stand-alone one-bucket net and NNUEKingBuckets 0: active, no problem");
    p = problem_after(1, true, pure1);
    report(p.empty() && options::nnue_v2, "PureNnue with the stand-alone net and NNUEKingBuckets 1: active");
    p = problem_after(0, false, pure1);
    report(contains(p, "is a stand-alone net") && contains(p, "set PureNnue 1") && !options::nnue_v2 && v2::active() == nullptr,
           "stand-alone net without PureNnue (NNUEKingBuckets 0): " + p);
    p = problem_after(1, false, pure1);
    report(contains(p, "is a stand-alone net") && !options::nnue_v2, "stand-alone net without PureNnue (NNUEKingBuckets 1): " + p);
    p = problem_after(2, true, pure1);
    report(contains(p, "does not match") && !options::nnue_v2, "PureNnue, NNUEKingBuckets 2 vs a one-bucket net: " + p);
    nnue::enabled = false;
    p = problem_after(0, true, pure1);
    const bool off_ok = p.empty() && !options::nnue_v2;
    v2::unload();
    p = problem_after(0, true, "");
    report(off_ok && p.empty() && !options::nnue_v2, "UseNNUE false wins over PureNnue (not an error, HCE only)");
    nnue::enabled = true;
    p = problem_after(0, true, "");
    report(!p.empty(), "UseNNUE true again: PureNnue without a net is a problem again");

    report(load_spec(pure4, random_net(4, true, false, 83)), "load a stand-alone mirrored 4-bucket net");
    p = problem_after(0, true, pure4);
    report(contains(p, "set NNUEKingBuckets 4 as well") && !options::nnue_v2, "PureNnue alone with a 4-bucket net: " + p);
    p = problem_after(4, true, pure4);
    report(p.empty() && options::nnue_v2 && v2::active()->king_buckets == 4, "PureNnue + NNUEKingBuckets 4 with the stand-alone 4-bucket net: active");
    p = problem_after(4, false, pure4);
    report(contains(p, "is a stand-alone net") && !options::nnue_v2, "stand-alone 4-bucket net, NNUEKingBuckets 4, PureNnue 0: " + p);
    report(load_spec(resid4, random_net(4, true, true, 84)), "load a residual mirrored 4-bucket net");
    p = problem_after(4, true, resid4);
    report(contains(p, "is a residual net") && !options::nnue_v2, "PureNnue + NNUEKingBuckets 4 with a residual 4-bucket net: " + p);
    p = problem_after(4, false, resid4);
    report(p.empty() && options::nnue_v2 && v2::active()->residual, "C4 rule unchanged: residual 4-bucket net with NNUEKingBuckets 4 is active");
    v2::unload();
    p = problem_after(0, false, "");
    report(p.empty() && !options::nnue_v2, "PureNnue 0, NNUEFile <empty>, NNUEKingBuckets 0: request cleared");
}

// ---------------------------------------------------------------- 2. evaluation path
const std::vector<std::string> start_fens = {
    std::string(Board::StandardStartFen),
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "8/8/4k3/8/2K5/8/3P4/8 w - - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "8/P7/8/8/8/8/p7/K6k w - - 0 1",
    "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
};

Board position(const std::string& fen) {
    Board b;
    std::string error;
    if (!b.set_fen(fen, &error)) throw std::runtime_error(fen + ": " + error);
    return b;
}

nnue::Accumulator reference(const v2::Net& net, const Board& b) {
    nnue::Accumulator acc;
    v2::refresh(net, b, White, acc.values[White].data());
    v2::refresh(net, b, Black, acc.values[Black].data());
    acc.valid = true;
    return acc;
}
bool same_values(const nnue::Accumulator& a, const nnue::Accumulator& b) {
    return std::memcmp(a.values.data(), b.values.data(), sizeof(a.values)) == 0;
}
int expected_eval(const v2::Net& net, const Board& b, bool pure) {
    const int network = v2::evaluate(net, b, reference(net, b));
    return pure ? network : std::clamp(Evaluator::evaluate_uncached(b) + network, -MateInMaxPly + 1, MateInMaxPly - 1);
}

struct WalkStats {
    long plies = 0, evals = 0, verified = 0, eval_mismatch = 0, acc_mismatch = 0, psqt_built = 0, differs_from_other = 0,
         hce_nonzero = 0, differs_where_hce_zero = 0;
};

// Random make/unmake walk (as tests/nnue_v2_tests.cpp): evaluations at random plies through the real
// Worker::static_evaluate; checks the value against the rule for `pure` and every accumulator computed.
void walk(Worker& w, const v2::Net& net, bool pure, std::uint64_t seed, long target_plies, WalkStats& st) {
    Rng rng{seed};
    constexpr int MaxDepth = 24;
    while (st.plies < target_plies) {
        Board board = position(start_fens[static_cast<std::size_t>(rng.below(static_cast<int>(start_fens.size())))]);
        w.clear();
        SearchLimits limits;
        limits.depth = 1;
        const std::vector<Worker*> all{&w};
        (void)w.search(board, limits, false, all);
        SearchStack* root = Probe::root(w);
        std::vector<Board> path{board};
        struct Step { bool null; Move move; Undo undo; NullUndo null_undo; };
        std::vector<Step> steps;
        int depth = 0;
        const int length = 200 + rng.below(400);
        for (int t = 0; t < length && st.plies < target_plies; ++t) {
            SearchStack* ss = root + depth;
            if (depth < MaxDepth && (depth == 0 || rng.chance(58))) {
                const MoveList moves = board.legal_moves();
                if (moves.empty()) continue;
                Step step{};
                if (!board.in_check() && rng.chance(4)) {
                    step.null = true;
                    Probe::null(w, ss);
                    board.make_null_move(step.null_undo);
                } else {
                    step.move = moves[static_cast<std::size_t>(rng.below(static_cast<int>(moves.size())))];
                    Probe::move(w, ss, board, step.move);
                    (void)board.make_move(step.move, step.undo);
                }
                steps.push_back(step);
                path.push_back(board);
                ++depth;
                ++st.plies;
                if (rng.chance(45)) {
                    std::vector<bool> was_valid(static_cast<std::size_t>(depth + 1));
                    for (int j = 0; j <= depth; ++j) was_valid[static_cast<std::size_t>(j)] = (root + j)->accumulator.valid;
                    const int actual = Probe::eval(w, board, root + depth);
                    ++st.evals;
                    for (int j = 0; j <= depth; ++j) {
                        SearchStack* e = root + j;
                        if (j > 0 && e->runtime_psqt.valid) ++st.psqt_built;
                        if (!e->accumulator.valid || was_valid[static_cast<std::size_t>(j)]) continue;
                        ++st.verified;
                        if (!same_values(e->accumulator, reference(net, path[static_cast<std::size_t>(j)]))) ++st.acc_mismatch;
                    }
                    if (actual != expected_eval(net, board, pure)) ++st.eval_mismatch;
                    // Control: the two rules differ exactly where the HCE is non-zero (no clamping at these values).
                    const bool hce_nonzero = Evaluator::evaluate_uncached(board) != 0;
                    const bool differs = actual != expected_eval(net, board, !pure);
                    st.hce_nonzero += hce_nonzero ? 1 : 0;
                    st.differs_from_other += differs ? 1 : 0;
                    st.differs_where_hce_zero += differs && !hce_nonzero ? 1 : 0;
                }
            } else if (depth > 0) {
                const Step& step = steps.back();
                if (step.null) board.unmake_null_move(step.null_undo);
                else board.unmake_move(step.move, step.undo);
                steps.pop_back();
                path.pop_back();
                --depth;
                if (rng.chance(30)) {
                    const int actual = Probe::eval(w, board, root + depth);
                    ++st.evals;
                    if (actual != expected_eval(net, board, pure)) ++st.eval_mismatch;
                    if (!same_values((root + depth)->accumulator, reference(net, board))) ++st.acc_mismatch;
                }
            }
        }
    }
}

void test_eval_path(const std::string& dir, long plies) {
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    struct Case { const char* name; int buckets; bool mirror; int option_buckets; };
    const std::vector<Case> cases = {{"one-bucket net (NNUEKingBuckets 0)", 1, false, 0}, {"mirrored 4-bucket net (NNUEKingBuckets 4)", 4, true, 4}};
    std::uint64_t seed = 91;
    for (const Case& c : cases) {
        for (const bool pure : {true, false}) {
            // The same weights; only the header flag differs (stand-alone for PureNnue, residual otherwise).
            Spec n = random_net(c.buckets, c.mirror, !pure, seed);
            report(load_spec(dir + "walk.fnn2", n), std::string("load ") + c.name + (pure ? " (stand-alone)" : " (residual twin)"));
            options::nnue_king_buckets = pure ? c.option_buckets : c.buckets;
            options::pure_nnue = pure;
            const bool active = options::apply_nnue_v2(nullptr);
            report(active && options::nnue_v2 && v2::active()->residual == !pure, std::string("select ") + c.name + (pure ? " with PureNnue" : " residual"));
            if (!active) continue;
            WalkStats st;
            walk(*worker, *v2::active(), pure, seed * 7919U, plies, st);
            std::cout << "WALK " << c.name << (pure ? " PureNnue" : " residual") << ": plies " << st.plies << " evaluations " << st.evals
                      << " accumulators verified " << st.verified << " eval mismatches " << st.eval_mismatch << " accumulator mismatches "
                      << st.acc_mismatch << " HCE PSQT accumulators built " << st.psqt_built << " evaluations unequal to the other rule "
                      << st.differs_from_other << '\n';
            if (pure) {
                report(st.eval_mismatch == 0 && st.acc_mismatch == 0 && st.verified > st.plies / 4,
                       std::string(c.name) + ", PureNnue: static_evaluate == network alone and every accumulator == refresh (" +
                           std::to_string(st.evals) + " evaluations, " + std::to_string(st.plies) + " plies)");
                report(st.psqt_built == 0, std::string(c.name) + ", PureNnue: the HCE's PSQT accumulator is never built");
            } else {
                report(st.eval_mismatch == 0 && st.acc_mismatch == 0,
                       std::string(c.name) + ", residual twin: static_evaluate == clamp(HCE + network) (" + std::to_string(st.evals) + " evaluations)");
                report(st.psqt_built > 0, std::string(c.name) + ", residual twin: the HCE's PSQT accumulator is built (control)");
            }
            report(st.differs_from_other == st.hce_nonzero && st.differs_where_hce_zero == 0 && st.hce_nonzero * 2 > st.evals,
                   std::string(c.name) + (pure ? ", PureNnue" : ", residual") + ": the other rule's value differs exactly where the HCE is "
                       "non-zero (" + std::to_string(st.differs_from_other) + " of " + std::to_string(st.hce_nonzero) + " such evaluations, " +
                       std::to_string(st.evals) + " in all; control)");
        }
        ++seed;
    }
    options::nnue_king_buckets = 0;
    options::pure_nnue = false;
    v2::unload();
    (void)options::apply_nnue_v2(nullptr);
}

// ---------------------------------------------------------------- 3. search
std::uint64_t search_nodes(const Board& b, int depth) {
    Searcher searcher(16, 1);
    SearchLimits limits;
    limits.depth = depth;
    return searcher.search(b, limits, false, Searcher::TTAccess::Exclusive).nodes;
}

void test_search(const std::string& dir) {
    const Board b = position(start_fens[1]);
    std::array<std::uint64_t, 3> nodes{};
    for (int i = 0; i < 3; ++i) {
        const bool pure = i < 2;
        report(load_spec(dir + "search.fnn2", random_net(1, false, !pure, 95)), "load search net");
        options::nnue_king_buckets = pure ? 0 : 1;
        options::pure_nnue = pure;
        report(options::apply_nnue_v2(nullptr), pure ? "select with PureNnue" : "select the residual twin");
        nodes[static_cast<std::size_t>(i)] = search_nodes(b, 6);
    }
    report(nodes[0] == nodes[1] && nodes[0] > 0, "PureNnue depth-6 search is deterministic (" + std::to_string(nodes[0]) + " nodes twice)");
    report(nodes[0] != nodes[2], "PureNnue searches another tree than the residual twin (" + std::to_string(nodes[0]) + " vs " +
                                     std::to_string(nodes[2]) + " nodes)");
    options::nnue_king_buckets = 0;
    options::pure_nnue = false;
    v2::unload();
    (void)options::apply_nnue_v2(nullptr);
}

// ---------------------------------------------------------------- 4. UCI
struct Run {
    std::string out;
    int status = -1;
};
std::string quote(const std::string& text) { return "\"" + text + "\""; }
Run run_engine(const std::string& engine, const std::string& name, const std::string& script) {
    const std::string in = "pure_nnue_uci_" + name + ".in";
    const std::string out = "pure_nnue_uci_" + name + ".out";
    write_file(in, script);
    temporary_files.push_back(out);
    std::string command = quote(engine) + " < " + quote(in) + " > " + quote(out);
#if defined(_WIN32)
    command = "\"" + command + "\"";   // cmd.exe /c strips one pair of outer quotes
#endif
    std::fflush(nullptr);
    const int raw = std::system(command.c_str());
    Run run;
#if defined(_WIN32)
    run.status = raw;
#else
    run.status = WIFEXITED(raw) ? WEXITSTATUS(raw) : 128 + (WIFSIGNALED(raw) ? WTERMSIG(raw) : 0);
#endif
    run.out = read_file(out);
    return run;
}
int count(const std::string& text, const std::string& what) {
    int n = 0;
    for (std::size_t at = text.find(what); at != std::string::npos; at = text.find(what, at + what.size())) ++n;
    return n;
}
bool has_line(const std::string& text, const std::string& prefix) {
    std::istringstream lines(text);
    for (std::string line; std::getline(lines, line);) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.rfind(prefix, 0) == 0) return true;
    }
    return false;
}
std::string last_error(const std::string& text) {
    std::istringstream lines(text);
    std::string last = "(no ERROR line)";
    for (std::string line; std::getline(lines, line);) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.rfind("info string ERROR NNUE v2:", 0) == 0) last = line;
    }
    return last;
}
const std::string Head = "uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n";
std::string set(const std::string& name, const std::string& value) { return "setoption name " + name + " value " + value + "\n"; }

void expect_failure(const std::string& engine, const std::string& name, const std::string& options, const std::string& trigger,
                    const std::string& phrase) {
    const Run r = run_engine(engine, name, Head + options + trigger + "\nquit\n");
    const bool no_answer = !has_line(r.out, "readyok") && !has_line(r.out, "bestmove") && !contains(r.out, "bench depth");
    report(r.status == 2 && count(r.out, "info string ERROR NNUE v2: ") >= 2 && no_answer && contains(last_error(r.out), phrase),
           "UCI " + name + ": exit status " + std::to_string(r.status) + " at " + trigger + (no_answer ? ", no answer: " : ", ANSWERED: ") +
               last_error(r.out));
}

void test_uci(const std::string& engine, const std::string& dir) {
    const std::string pure = dir + "uci_pure.fnn2";
    const std::string resid = dir + "uci_resid.fnn2";
    write_file(pure, serialise(random_net(1, false, false, 97)));
    write_file(resid, serialise(random_net(1, false, true, 97)));
    {
        const Run r = run_engine(engine, "defaults", Head + "isready\ngo depth 1\nquit\n");
        report(r.status == 0 && contains(r.out, "option name PureNnue type spin default 0 min 0 max 1") && has_line(r.out, "readyok") &&
                   has_line(r.out, "bestmove") && !contains(r.out, "NNUE v2"),
               "UCI defaults: PureNnue advertised (spin 0-1, default 0), nothing NNUE v2 printed, exit 0");
    }
    expect_failure(engine, "pure_without_file", set("PureNnue", "1"), "isready", "no v2 net is loaded");
    expect_failure(engine, "pure_with_residual_net", set("NNUEFile", resid) + set("PureNnue", "1"), "go depth 1", "is a residual net");
    expect_failure(engine, "standalone_without_pure", set("NNUEFile", pure) + set("NNUEKingBuckets", "1"), "bench 2", "set PureNnue 1");
    expect_failure(engine, "pure_switched_off_again", set("NNUEFile", pure) + set("PureNnue", "1") + set("PureNnue", "0"), "isready",
                   "set PureNnue 1");
    {
        const std::string active = "info string NNUE v2: active: " + pure + " king buckets 1 output buckets 1 hidden " +
                                   std::to_string(nnue::HiddenSize) + " unmirrored stand-alone";
        // As for C4's options, the half-set request (PureNnue before NNUEFile) is reported once at once and
        // resolved by NNUEFile; nothing is reported after that.
        const Run r = run_engine(engine, "pure_active", Head + set("PureNnue", "1") + set("NNUEFile", pure) +
                                                            "isready\ngo depth 4\nbench 2\nquit\n");
        report(r.status == 0 && count(r.out, active) == 2 && has_line(r.out, "readyok") && has_line(r.out, "bestmove") &&
                   contains(r.out, "bench depth 2 nodes") && count(r.out, "ERROR") == 1 &&
                   r.out.find("ERROR") < r.out.find("info string NNUE v2: loaded"),
               "UCI PureNnue + stand-alone net: \"" + active + " ...\" (activation + isready), readyok, bestmove, bench, exit 0; "
               "only the half-set request before NNUEFile was reported (" + last_error(r.out) + ")");
        const Run s = run_engine(engine, "pure_active_file_first", Head + set("NNUEFile", pure) + set("PureNnue", "1") + "isready\nquit\n");
        report(s.status == 0 && count(s.out, active) == 2 && has_line(s.out, "readyok") && count(s.out, "ERROR") == 1 &&
                   contains(s.out, "set PureNnue 1"),
               "UCI NNUEFile before PureNnue: active, readyok, exit 0 (the half-set request named once: " + last_error(s.out) + ")");
    }
    {
        const Run r = run_engine(engine, "pure_cleared", Head + set("PureNnue", "1") + set("NNUEFile", pure) + set("PureNnue", "0") +
                                                             set("NNUEFile", "<empty>") + "isready\ngo depth 1\nquit\n");
        report(r.status == 0 && has_line(r.out, "readyok") && has_line(r.out, "bestmove") && contains(r.out, "info string NNUE v2: off"),
               "UCI PureNnue 0 + NNUEFile <empty>: request cleared, compiled-in net, exit 0");
    }
    {
        const Run r = run_engine(engine, "pure_invalid_value", Head + set("PureNnue", "maybe") + set("PureNnue", "2") + "isready\nquit\n");
        report(r.status == 0 && count(r.out, "info string invalid value for option PureNnue") == 2 && has_line(r.out, "readyok") &&
                   !contains(r.out, "ERROR"),
               "UCI PureNnue maybe / 2: invalid values reported, the option stays 0 (no request)");
    }
    {
        const std::string active = "info string NNUE v2: active: " + pure + " king buckets 1";
        const Run r = run_engine(engine, "pure_alias_true", Head + set("NNUEFile", pure) + set("PureNnue", "true") + "isready\n" +
                                                                set("PureNnue", "false") + "isready\nquit\n");
        report(r.status == 2 && count(r.out, active) == 2 && count(r.out, "readyok") == 1 && contains(last_error(r.out), "set PureNnue 1"),
               "UCI PureNnue true / false are accepted as 1 / 0 (true: active, readyok; false: the stand-alone net is an error again)");
    }
    {
        const Run r = run_engine(engine, "pure_usennue_false", Head + set("UseNNUE", "false") + set("PureNnue", "1") + "isready\ngo depth 1\nquit\n");
        report(r.status == 0 && has_line(r.out, "readyok") && has_line(r.out, "bestmove") && !contains(r.out, "ERROR"),
               "UCI UseNNUE false + PureNnue 1: not an error (hand-crafted evaluation only)");
    }
}

} // namespace

int main(int argc, char** argv) {
    const std::string engine = argc > 1 ? argv[1] : "";
    const long plies = argc > 2 ? std::stol(argv[2]) : 12000;
    const std::string dir = "pure_nnue_test_";
    test_rules(dir);
    test_eval_path(dir, plies);
    test_search(dir);
    if (!engine.empty()) {
        std::string path = engine;
#if defined(_WIN32)
        for (char& c : path) if (c == '/') c = '\\';
#endif
        test_uci(path, dir);
    } else {
        std::cout << "(no engine executable given: UCI tests skipped)\n";
    }
    v2::unload();
    for (const std::string& file : temporary_files) std::remove(file.c_str());
    std::cout << checks - failures << "/" << checks << " checks passed\n";
    return failures == 0 ? 0 : 1;
}
