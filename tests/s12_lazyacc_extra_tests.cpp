// S12 follow-up: two checks on the null-edge accumulator alias (FORGE_NNUE_LAZY_ACC) that Sol's regression test
// (forge_sol_S12_lazyacc_native_regression_v2_20261027.cpp) does not make, because every case there starts from
// Worker::clear(). Both guard invariants the search keeps today (it never makes two null moves in a row), so in the
// engine they are defense in depth: a null child must not keep an alias from an earlier use of its stack entry, and
// computed_owner must not trust an owner pointer that is not a lower, valid, physical frame.
#include "forge/search.hpp"
#include "forge/eval_params.hpp"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

namespace forge {
struct SearcherTestProbe {
    static SearchStack* root(Worker& w) { return &w.stack_[4]; }
    static void plies(Worker& w) {
        for (int i = 0; i < MaxPly + 4; ++i) w.stack_[static_cast<std::size_t>(i)].ply = i - 4;
    }
    static int eval(Worker& w, const Board& b, SearchStack* ss) { return w.static_evaluate(b, ss); }
    static void move(Worker& w, SearchStack* ss, const Board& b, Move m) { w.record_move(ss, b, m); }
    static void null(Worker& w, SearchStack* ss) { w.record_null_move(ss); }
};
}

using namespace forge;
using Probe = SearcherTestProbe;
namespace {
int checks = 0, failures = 0;
void check(bool okay, const std::string& label) {
    ++checks;
    if (!okay) ++failures;
    std::cout << (okay ? "PASS " : "FAIL ") << label << '\n';
}
// Fresh runtime PSQT, computed like the oracle in tests/runtime_psqt_tests.cpp.
Evaluator::RuntimePsqt psqt_oracle(const Board& b) {
    Score score = 0; int phase = 0;
    for (int square = 0; square < 64; ++square) {
        const Piece p = b.piece_at(square); if (p == Empty) continue;
        const int type = piece_type(p); phase += PhaseValue[static_cast<std::size_t>(type)];
        const Score term = params::table[static_cast<std::size_t>(params::Psqt + (type - 1) * 64
            + (color_of(p) == White ? square : flip_square(square)))];
        score += color_of(p) == White ? term : -term;
    }
    return {score, phase, true};
}
// The evaluation a fresh accumulator gives for this board (the parity target of Sol's test).
int expected_eval(const Board& b) {
    nnue::Accumulator fresh;
    nnue::refresh(b, fresh);
    return nnue::residual()
        ? std::clamp(Evaluator::evaluate_uncached(b) + nnue::evaluate(b, fresh), -MateInMaxPly + 1, MateInMaxPly - 1)
        : nnue::evaluate(b, fresh);
}
SearchStack* begin(Worker& w, const Board& b) {
    w.clear();
    Probe::plies(w);
    SearchStack* ss = Probe::root(w);
    nnue::refresh(b, ss->accumulator);
    ss->runtime_psqt = psqt_oracle(b);
    return ss;
}
Move move(Board& b, const std::string& text) {
    const auto m = b.parse_uci(text);
    if (!m) throw std::runtime_error("illegal fixture move: " + text);
    return *m;
}
}

int main() {
    try {
        check(nnue::available(), "compiled network available");
        if (!nnue::available()) return 1;
        nnue::enabled = true;
        SharedSearchState shared(1);
        shared.lazy_acc_enabled = true;
        auto owned = std::make_unique<Worker>(shared, 0);
        Worker& w = *owned;
        Board b;
        if (!b.set_fen(std::string(Board::StandardStartFen))) throw std::runtime_error("start FEN");

        // 1. Reuse after a null-null chain: the chain leaves (ss + 2) aliased to the root. The same entry then
        //    becomes a null child of a real move; it must borrow that real frame, not the stale root.
        SearchStack* ss = begin(w, b);
        Probe::null(w, ss);
        NullUndo n1;
        b.make_null_move(n1);
        Probe::null(w, ss + 1);
        NullUndo n2;
        b.make_null_move(n2);
        check(Probe::eval(w, b, ss + 2) == expected_eval(b), "null-null chain evaluates like a fresh accumulator");
        check((ss + 2)->accumulator_owner == ss, "null-null chain aliases the root");
        b.unmake_null_move(n2);
        b.unmake_null_move(n1);
        const Move knight = move(b, "g1f3");
        Probe::move(w, ss, b, knight);
        Undo undo;
        if (!b.make_move(knight, undo)) throw std::runtime_error("fixture make failed");
        Probe::null(w, ss + 1);
        check((ss + 2)->accumulator_owner == nullptr, "record_null_move clears the entry's old alias");
        NullUndo n3;
        b.make_null_move(n3);
        check(Probe::eval(w, b, ss + 2) == expected_eval(b), "null child of a real move after a reused chain: parity");
        check((ss + 2)->accumulator_owner == ss + 1, "null child borrows the new real parent, not the stale root");
        b.unmake_null_move(n3);
        b.unmake_move(knight, undo);

        // 2. An owner pointer that is not a lower, valid, physical frame is ignored (the walk materializes instead).
        ss = begin(w, b);
        Probe::move(w, ss, b, knight);
        (void)b.make_move(knight, undo);
        Probe::null(w, ss + 1);
        NullUndo n4;
        b.make_null_move(n4);
        (ss + 2)->accumulator_owner = ss + 1;  // lower but not valid: the real parent is not evaluated yet
        check(!(ss + 1)->accumulator.valid, "fixture: the real parent is not materialized");
        check(Probe::eval(w, b, ss + 2) == expected_eval(b), "owner pointing at an unmaterialized frame is ignored");
        b.unmake_null_move(n4);
        Probe::null(w, ss + 1);
        b.make_null_move(n4);
        (ss + 2)->accumulator_owner = ss + 3;  // not an ancestor
        (ss + 3)->accumulator.valid = false;
        check(Probe::eval(w, b, ss + 2) == expected_eval(b), "owner pointing above the frame is ignored");
        b.unmake_null_move(n4);
        b.unmake_move(knight, undo);

        std::cout << "CHECKS " << checks << " FAILURES " << failures << '\n';
        return failures == 0 ? 0 : 1;
    } catch (const std::exception& e) {
        std::cerr << "FAIL exception " << e.what() << '\n';
        return 1;
    }
}
