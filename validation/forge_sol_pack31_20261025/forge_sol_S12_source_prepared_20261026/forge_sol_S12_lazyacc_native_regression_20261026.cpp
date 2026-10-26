// ORIGINAL Forge-only test. Prepared source: NOT COMPILED OR EXECUTED yet.
// This also compiles against the supplied baseline: parity can pass there, but
// the actual zero-copy assertions must fail. No baseline behavior is mocked.
#include "forge/search.hpp"
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
    template<class State> static bool mode(State& s, bool enabled) {
        if constexpr (requires { s.lazy_acc_enabled; }) { s.lazy_acc_enabled = enabled; return true; }
        else return false;
    }
    template<class Frame> static Frame* owner(Frame* ss) {
        if (ss->accumulator.valid) return ss;
        if constexpr (requires { ss->accumulator_owner; }) return ss->accumulator_owner;
        else return nullptr;
    }
    template<class W> static std::uint64_t avoided(const W& w) {
        if constexpr (requires { w.lazy_acc_stats_.copies_avoided; }) return w.lazy_acc_stats_.copies_avoided;
        else return 0;
    }
};
}

using namespace forge;
namespace {
int checks = 0, failures = 0;
void check(bool okay, const std::string& label) {
    ++checks;
    if (!okay) ++failures;
    std::cout << (okay ? "PASS " : "FAIL ") << label << '\n';
}
Board board(const std::string& fen) {
    Board b;
    if (!b.set_fen(fen)) throw std::runtime_error("invalid FEN: " + fen);
    return b;
}
Move move(Board& b, const std::string& text) {
    const auto m = b.parse_uci(text);
    if (!m) throw std::runtime_error("illegal fixture move: " + text + " in " + b.fen());
    return *m;
}
SearchStack* begin(Worker& w, const Board& b) {
    w.clear();
    SearcherTestProbe::plies(w);
    SearchStack* ss = SearcherTestProbe::root(w);
    nnue::refresh(b, ss->accumulator);
    ss->runtime_psqt = Evaluator::refresh_runtime_psqt(b);
    return ss;
}
void verify(Worker& w, const Board& b, SearchStack* ss, const std::string& label) {
    const int actual = SearcherTestProbe::eval(w, b, ss);
    SearchStack* owner = SearcherTestProbe::owner(ss);
    check(owner != nullptr && owner->accumulator.valid && owner <= ss, label + " physical owner exists within ancestor chain");
    if (!owner) return;
    nnue::Accumulator fresh;
    nnue::refresh(b, fresh);
    check(std::memcmp(fresh.values.data(), owner->accumulator.values.data(), sizeof(fresh.values)) == 0,
          label + " all actual float words equal fresh refresh");
    check(nnue::evaluate(b, fresh) == nnue::evaluate(b, owner->accumulator), label + " actual NNUE integer API parity");
    const int expected = nnue::residual()
        ? std::clamp(Evaluator::evaluate_uncached(b) + nnue::evaluate(b, fresh), -MateInMaxPly + 1, MateInMaxPly - 1)
        : nnue::evaluate(b, fresh);
    check(actual == expected, label + " complete actual Worker evaluation parity");
    if (nnue::residual()) {
        const auto psqt = Evaluator::refresh_runtime_psqt(b);
        check(owner->runtime_psqt.valid == psqt.valid && owner->runtime_psqt.score == psqt.score
              && owner->runtime_psqt.phase == psqt.phase, label + " PSQT score phase and validity parity");
    }
}
void special(Worker& w, Board b, const std::string& uci, const std::string& label) {
    auto* ss = begin(w, b);
    Move m = move(b, uci);
    SearcherTestProbe::move(w, ss, b, m);
    Undo undo;
    if (!b.make_move(m, undo)) throw std::runtime_error("fixture make failed");
    verify(w, b, ss + 1, label + " real");
    SearcherTestProbe::null(w, ss + 1);
    NullUndo null;
    b.make_null_move(null);
    verify(w, b, ss + 2, label + " real then null");
    check(!((ss + 2)->accumulator.valid), label + " null cache remains unmaterialized");
    check(SearcherTestProbe::owner(ss + 2) == ss + 1, label + " null borrows physical real predecessor");
    b.unmake_null_move(null);
    b.unmake_move(m, undo);
    verify(w, b, ss, label + " restored root");
}
}

int main() {
    try {
        check(nnue::available(), "actual compiled network available");
        if (!nnue::available()) return 1;
        nnue::enabled = true;
        SharedSearchState shared(1);
        check(SearcherTestProbe::mode(shared, true), "actual opt-in implementation present (must fail on base)");
        auto owned = std::make_unique<Worker>(shared, 0);
        Worker& w = *owned;
        Board b = board(std::string(Board::StandardStartFen));
        SearchStack* ss = begin(w, b);
        nnue::Accumulator root_before = ss->accumulator;
        SearcherTestProbe::null(w, ss);
        NullUndo first;
        b.make_null_move(first);
        // Poison the local cache: an alias must use its physical owner's cache.
        (ss + 1)->runtime_psqt = {123, -7, true};
        ss->runtime_psqt.valid = false;
        verify(w, b, ss + 1, "null with invalid owner PSQT and poisoned local PSQT");
        check(!(ss + 1)->accumulator.valid, "actual null accumulator copy avoided (must fail on base)");
        check(SearcherTestProbe::owner(ss + 1) == ss, "null uses root physical owner");
        SearcherTestProbe::null(w, ss + 1);
        NullUndo second;
        b.make_null_move(second);
        verify(w, b, ss + 2, "null-null chain");
        check(SearcherTestProbe::owner(ss + 2) == ss, "alias chain is flattened to physical root");
        check(SearcherTestProbe::avoided(w) >= 2, "real skip counter changed (must fail on base)");
        check(std::memcmp(root_before.values.data(), ss->accumulator.values.data(), sizeof(root_before.values)) == 0,
              "null chain leaves physical root float words unchanged");
        // A nonempty edge after aliased frames must use the same exact input.
        const Move knight = move(b, "g1f3");
        SearcherTestProbe::move(w, ss + 2, b, knight);
        Undo knight_undo;
        (void)b.make_move(knight, knight_undo);
        verify(w, b, ss + 3, "null-null-real");
        b.unmake_move(knight, knight_undo);
        b.unmake_null_move(second);
        b.unmake_null_move(first);
        // Reuse the old aliased child as a real sibling. A retained alias would
        // give the root features and fail both float words and integer parity.
        SearcherTestProbe::move(w, ss, b, knight);
        check(SearcherTestProbe::owner(ss + 1) == nullptr, "sibling invalidation clears stale alias");
        (void)b.make_move(knight, knight_undo);
        verify(w, b, ss + 1, "overwritten alias sibling");
        verify(w, b, ss + 1, "same-ply repeated evaluation");
        b.unmake_move(knight, knight_undo);
        ss = begin(w, b);
        check(SearcherTestProbe::owner(ss + 1) == nullptr, "Worker clear/root restart removes stale aliases");
        // Lazy replay over a real edge and a null edge, neither yet evaluated.
        SearcherTestProbe::move(w, ss, b, knight);
        (void)b.make_move(knight, knight_undo);
        SearcherTestProbe::null(w, ss + 1);
        b.make_null_move(first);
        verify(w, b, ss + 2, "unevaluated real-null ancestor replay");
        b.unmake_null_move(first);
        b.unmake_move(knight, knight_undo);
        special(w, board("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"), "e5d6", "en passant");
        special(w, board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"), "e1g1", "white castle");
        special(w, board("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1"), "e8c8", "black castle");
        special(w, board("4k3/P7/8/8/8/8/8/4K3 w - - 0 1"), "a7a8n", "white underpromotion");
        special(w, board("4k3/8/8/8/8/8/p7/4K3 b - - 0 1"), "a2a1n", "black underpromotion");
        special(w, board("1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1"), "a7b8n", "capture underpromotion");
        // With NNUE disabled, the alias option must not be entered at all.
        nnue::enabled = false;
        ss = begin(w, b);
        const auto before = SearcherTestProbe::avoided(w);
        check(SearcherTestProbe::eval(w, b, ss) == Evaluator::evaluate_uncached(b), "UseNNUE false retains HCE behavior");
        check(SearcherTestProbe::avoided(w) == before, "UseNNUE false adds no skipped-copy claims");
        nnue::enabled = true;
        std::cout << "CHECKS " << checks << " FAILURES " << failures << '\n';
        return failures == 0 ? 0 : 1;
    } catch (const std::exception& e) {
        std::cerr << "FAIL exception " << e.what() << '\n';
        return 1;
    }
}
