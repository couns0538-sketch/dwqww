// Own-project diagnostic only; no engine source changes. SOURCE ONLY, not run.
// One actual Worker construction; histories are not cleared per corpus row.
#include "forge/search.hpp"
#include <algorithm>
#include <bit>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <immintrin.h>

#ifndef FORGE_SOL_S12_ALIAS_MODE
#error "Diagnostic mode must be explicitly bound by the helper recipe"
#endif
static_assert(FORGE_SOL_S12_ALIAS_MODE >= 0 && FORGE_SOL_S12_ALIAS_MODE <= 2);
static_assert(forge::nnue::HiddenSize == 256);
static_assert(sizeof(float) == 4 && sizeof(std::uint32_t) == 4);

namespace forge {
struct SearcherTestProbe {
    static SearchStack* root(Worker& w) { return &w.stack_[4]; }
    static void plies(Worker& w) {
        for (int i = 0; i < MaxPly + 4; ++i) w.stack_[static_cast<std::size_t>(i)].ply = i - 4;
    }
    static int eval(Worker& w, const Board& b, SearchStack* s) { return w.static_evaluate(b, s); }
    static void move(Worker& w, SearchStack* s, const Board& b, Move m) { w.record_move(s, b, m); }
    static void null(Worker& w, SearchStack* s) { w.record_null_move(s); }
    template<class S> static bool mode(S& s) {
        if constexpr (requires { s.lazy_acc_enabled; }) {
            s.lazy_acc_enabled = FORGE_SOL_S12_ALIAS_MODE == 2;
            return true;
        } else return false;
    }
    template<class S> static S* owner(S* s) {
        if (s->accumulator.valid) return s;
        if constexpr (requires { s->accumulator_owner; }) return s->accumulator_owner;
        else return nullptr;
    }
    template<class W> static void stats(const W& w) {
        if constexpr (requires { w.lazy_acc_stats_; }) {
            const auto a = w.lazy_acc_stats_;
            std::cerr << ",\"refreshes\":" << a.refreshes << ",\"updates\":" << a.updates
                << ",\"zero_dirty_edges\":" << a.zero_dirty_edges << ",\"copies_avoided\":" << a.copies_avoided
                << ",\"alias_hits\":" << a.alias_hits << ",\"evaluations\":" << a.evaluations;
        } else std::cerr << ",\"refreshes\":0,\"updates\":0,\"zero_dirty_edges\":0,\"copies_avoided\":0,\"alias_hits\":0,\"evaluations\":0";
    }
};
}
using namespace forge;
namespace {
std::uint64_t evaluations = 0, nulls = 0, legal_children = 0, selected_nulls = 0;
void require(bool condition, const char* text) { if (!condition) throw std::runtime_error(text); }
void u32(std::uint32_t x) {
    for (int i = 0; i < 4; ++i) std::cout.put(static_cast<char>((x >> (8 * i)) & 255U));
}
void u64(std::uint64_t x) { u32(static_cast<std::uint32_t>(x)); u32(static_cast<std::uint32_t>(x >> 32)); }
int verify(Worker& w, const Board& b, SearchStack* s) {
    const int score = SearcherTestProbe::eval(w, b, s); ++evaluations;
    auto* owner = SearcherTestProbe::owner(s);
    require(owner && owner >= SearcherTestProbe::root(w) && owner <= s && owner->accumulator.valid,
            "resolved owner is not a valid initialized ancestor");
    nnue::Accumulator fresh;
    nnue::refresh(b, fresh);
    require(std::memcmp(fresh.values.data(), owner->accumulator.values.data(), sizeof(fresh.values)) == 0,
            "fresh/incremental float words differ");
    const int network = nnue::evaluate(b, fresh);
    require(network == nnue::evaluate(b, owner->accumulator), "NNUE integer output differs");
    const int expected = nnue::residual()
        ? std::clamp(Evaluator::evaluate_uncached(b) + network, -MateInMaxPly + 1, MateInMaxPly - 1) : network;
    require(score == expected, "actual Worker/full fresh evaluation differs");
    if (nnue::residual()) {
        const auto p = Evaluator::refresh_runtime_psqt(b);
        require(owner->runtime_psqt.valid == p.valid && owner->runtime_psqt.score == p.score
                && owner->runtime_psqt.phase == p.phase, "resolved owner PSQT differs");
    }
    return score;
}
void transitions(Worker& w, Board& b, SearchStack* r) {
    const auto key = b.key();
    if (!b.in_check()) {
        SearcherTestProbe::null(w, r); NullUndo a; b.make_null_move(a); ++nulls;
        SearcherTestProbe::null(w, r + 1); NullUndo c; b.make_null_move(c); ++nulls;
        verify(w, b, r + 2); // Neither intermediate frame was evaluated.
        b.unmake_null_move(c); b.unmake_null_move(a);
    }
    const auto moves = b.legal_moves();
    if (!moves.empty()) {
        const Move m = moves.front();
        SearcherTestProbe::move(w, r, b, m); Undo a;
        require(b.make_move(m, a), "legal move failed"); ++legal_children;
        if (!b.in_check()) {
            SearcherTestProbe::null(w, r + 1); NullUndo c; b.make_null_move(c); ++nulls;
            verify(w, b, r + 2); // Unevaluated real-null replay.
            b.unmake_null_move(c);
        }
        verify(w, b, r + 1); b.unmake_move(m, a);
        // The selected null below aliases this child in ON. Then overwrite it
        // through the real record_move path, not diagnostic alias assignment.
        if (!b.in_check()) {
            SearcherTestProbe::null(w, r); NullUndo c; b.make_null_move(c); ++nulls;
            verify(w, b, r + 1); b.unmake_null_move(c);
        }
        SearcherTestProbe::move(w, r, b, m);
        require(b.make_move(m, a), "sibling move failed"); ++legal_children;
        verify(w, b, r + 1); b.unmake_move(m, a);
    }
    require(b.key() == key, "make/unmake key restoration differs");
    verify(w, b, r);
}
}
int main(int argc, char** argv) {
    try {
        require(argc == 5 && std::string(argv[1]) == "--positions" && std::string(argv[3]) == "--child-limit",
                "fixed argument schema required");
        const std::uint64_t count = std::stoull(argv[2]), limit = std::stoull(argv[4]);
        require(count == 8192 && limit == 1024, "preregistered bounded corpus prefix required");
        require(nnue::available(), "actual network unavailable"); nnue::enabled = true;
        SharedSearchState shared(1);
        const bool implementation = SearcherTestProbe::mode(shared);
        require(implementation == (FORGE_SOL_S12_ALIAS_MODE != 0), "mode/header/core source identity differs");
        auto owned = std::make_unique<Worker>(shared, 0); // Exactly one constructor/history initialization.
        Worker& w = *owned; SearcherTestProbe::plies(w);
        u32(0x4b323146); u32(1); u32(256); u32(2068); u64(count); u64(limit); u32(_mm_getcsr() & 0x0000ffc0U);
        std::string fen;
        for (std::uint64_t index = 0; index < count; ++index) {
            require(static_cast<bool>(std::getline(std::cin, fen)), "truncated original corpus prefix");
            Board b; require(b.set_fen(fen), "invalid original corpus FEN");
            auto* r = SearcherTestProbe::root(w);
            // Initialize only this root. Child invalidation is exclusively the
            // actual record_move/record_null implementation; never Worker.clear.
            *r = SearchStack{}; r->ply = 0;
            nnue::refresh(b, r->accumulator);
            r->runtime_psqt = Evaluator::refresh_runtime_psqt(b);
            if (index < limit) transitions(w, b, r);
            SearchStack* selected = r;
            NullUndo undo;
            const bool take_null = !b.in_check();
            if (take_null) {
                SearcherTestProbe::null(w, r); b.make_null_move(undo); ++nulls; ++selected_nulls;
                selected = r + 1;
            }
            const int score = verify(w, b, selected);
            require(verify(w, b, selected) == score, "same-ply repeated evaluation differs");
            const auto* owner = SearcherTestProbe::owner(selected);
            u64(index); u64(b.key()); u32(std::bit_cast<std::uint32_t>(static_cast<std::int32_t>(score)));
            for (const auto& perspective : owner->accumulator.values)
                for (float lane : perspective) u32(std::bit_cast<std::uint32_t>(lane));
            if (take_null) b.unmake_null_move(undo);
        }
        std::cout.flush(); require(static_cast<bool>(std::cout), "binary stdout write failed");
        std::cerr << "{\"positions\":" << count << ",\"record_bytes\":2068,\"header_bytes\":36"
            << ",\"mode\":" << FORGE_SOL_S12_ALIAS_MODE << ",\"implementation_present\":" << implementation
            << ",\"worker_constructions\":1,\"history_clears_after_construction\":0"
            << ",\"transition_roots\":" << limit << ",\"oracle_root_refreshes\":" << count
            << ",\"selected_nulls\":" << selected_nulls << ",\"legal_children\":" << legal_children
            << ",\"nulls\":" << nulls << ",\"verified_evaluations\":" << evaluations
            << ",\"fresh_mismatches\":0,\"state_mismatches\":0";
        SearcherTestProbe::stats(w); std::cerr << "}\n";
        return 0;
    } catch (const std::exception& error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
