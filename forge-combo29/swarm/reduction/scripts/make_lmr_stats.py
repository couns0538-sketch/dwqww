#!/usr/bin/env python3
"""make_lmr_stats.py SRC_DIR [cap|nocap]

Write the LMR-stats instrumentation into a COPY of a forge-combo29 tree. Nothing
in the repository is touched: the caller passes a scratch tree.

Modes:
  nocap  the base tree (6b98f217). It has no bare_king_lmr_cap, so the cap part of
         the report is compiled in but reports cap_switch absent.
  cap    the base tree with seat 03's ported r15 bare-king patch applied
         (swarm/03/job6/base_bare_king_on.patch.txt), whose gate is
         FORGE_FIX_BARE_KING_LMR_CAP.

The instrumentation is behind FORGE_LMR_STATS (default 0). With it off the
preprocessor reproduces the original statements verbatim, which is what makes the
flag-off pin gate meaningful.

Counted per root move and per completed depth iteration:
  applied    reduced searches actually entered
  rN         histogram of the FINAL reduction r, signed (r-2, r-1, r0, r1 ...)
  rsum       sum of r, so a mean can be computed without the histogram
  research   full-depth re-searches after a reduced search failed high
  rej        nodes where LMR was skipped although depth/movecount allowed it,
             with a per-guard count of EVERY failing guard (the counts overlap and
             rej is not their sum)
  cap_gate   nodes where the BARE_KING_LMR_CAP gate was true
  cap_clamp  nodes where it actually lowered r
  cap_r*     the r statistics at those nodes (same signed bins)
"""

import os
import sys

CPP = "src/search.cpp"
HPP = "include/forge/search.hpp"

# ---------------------------------------------------------------- search.hpp
HPP_SWITCH_OLD = "#pragma once\n"
HPP_SWITCH_NEW = """#pragma once

// FORGE_LMR_STATS (diagnostic build switch, default 0 = off): count every late-move
// reduction the search applies, by magnitude, by guard that rejected it, by root
// move and by depth, and the same for the BARE_KING_LMR_CAP gate where the tree
// has one. Off by default; with it off the preprocessed code is unchanged.
#ifndef FORGE_LMR_STATS
#define FORGE_LMR_STATS 0
#endif

// FORGE_LMR_KEYS (diagnostic, default 0): per-ply fingerprints of the positions the
// search visits -- count, XOR of keys, and sum of keys. XOR is order-independent and
// cancels multiplicity, so two builds agreeing on count+XOR+sum visited the same
// multiset of positions at that ply; agreeing on XOR but not on count means the same
// SET with a different number of visits. That distinction is the prior question behind
// a reduction-count comparison and it needs no storage, only three integers per ply.
#ifndef FORGE_LMR_KEYS
#define FORGE_LMR_KEYS 0
#endif

// FORGE_LMR_STATS_PRINT (default 1, meaningful only when FORGE_LMR_STATS is on):
// whether the counters are also PRINTED. Building counters-on/print-off isolates
// "the counters do not perturb the tree" from "the print path does not perturb it",
// which are two different claims and only the second one involves I/O.
#ifndef FORGE_LMR_STATS_PRINT
#define FORGE_LMR_STATS_PRINT 1
#endif
"""

HPP_MEMBERS_OLD = "    std::size_t root_effort_count_ = 0;\n"
HPP_MEMBERS_NEW = """    std::size_t root_effort_count_ = 0;
#if FORGE_LMR_STATS
public:
    // One block of reduction counters. Used per depth iteration and per root move.
    struct LmrStatBlock {
        // r is signed: the LMR terms subtract for tt_pv, check and history, so r can be
        // negative (a reduction that becomes an extension). 24 bins, index = r + 8.
        static constexpr int kBinOffset = 8;
        static constexpr int kBins = 24;
        std::uint64_t applied = 0;
        std::uint64_t research = 0;
        std::uint64_t r_sum = 0;
        std::uint64_t r_hist[kBins] = {};
        std::uint64_t rej = 0;
        std::uint64_t rej_mate = 0;
        std::uint64_t rej_fifty = 0;
        std::uint64_t rej_depth = 0;
        std::uint64_t rej_movecount = 0;
        std::uint64_t rej_bare = 0;
        std::uint64_t rej_pvcap = 0;
        std::uint64_t cap_gate = 0;
        std::uint64_t cap_clamped = 0;
        std::uint64_t cap_r_sum = 0;
        std::uint64_t cap_r_hist[kBins] = {};
        void clear() { *this = LmrStatBlock{}; }
        void add(const LmrStatBlock& o) {
            applied += o.applied;
            research += o.research;
            r_sum += o.r_sum;
            rej += o.rej;
            rej_mate += o.rej_mate;
            rej_fifty += o.rej_fifty;
            rej_depth += o.rej_depth;
            rej_movecount += o.rej_movecount;
            rej_bare += o.rej_bare;
            rej_pvcap += o.rej_pvcap;
            cap_gate += o.cap_gate;
            cap_clamped += o.cap_clamped;
            cap_r_sum += o.cap_r_sum;
            for (int i = 0; i < kBins; ++i) {
                r_hist[i] += o.r_hist[i];
                cap_r_hist[i] += o.cap_r_hist[i];
            }
        }
        void take(const LmrStatBlock& o) {
            applied -= o.applied;
            research -= o.research;
            r_sum -= o.r_sum;
            rej -= o.rej;
            rej_mate -= o.rej_mate;
            rej_fifty -= o.rej_fifty;
            rej_depth -= o.rej_depth;
            rej_movecount -= o.rej_movecount;
            rej_bare -= o.rej_bare;
            rej_pvcap -= o.rej_pvcap;
            cap_gate -= o.cap_gate;
            cap_clamped -= o.cap_clamped;
            cap_r_sum -= o.cap_r_sum;
            for (int i = 0; i < kBins; ++i) {
                r_hist[i] -= o.r_hist[i];
                cap_r_hist[i] -= o.cap_r_hist[i];
            }
        }
    };
private:
#if FORGE_LMR_KEYS
    std::uint64_t key_count_[MaxPly + 8] = {};
    std::uint64_t key_xor_[MaxPly + 8] = {};
    std::uint64_t key_sum_[MaxPly + 8] = {};
#endif
    LmrStatBlock lmr_iter_;
    std::array<LmrStatBlock, 256> lmr_root_;
    LmrStatBlock lmr_total_;
    std::size_t lmr_root_current_ = 0;
    bool lmr_cap_present_ = false;
    [[nodiscard]] LmrStatBlock& lmr_here() { return lmr_root_[lmr_root_current_]; }
#endif
"""

# ---------------------------------------------------------------- search.cpp
CPP_INCLUDE_OLD = "#include <cstring>\n"
CPP_INCLUDE_NEW = """#include <cstring>
#if FORGE_LMR_STATS
#include <cstdio>
#endif
"""

CPP_HELPERS_OLD = "int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {\n"
CPP_HELPERS_NEW = r'''#if FORGE_LMR_STATS
#if FORGE_LMR_STATS_PRINT
namespace {
void lmr_print_block(const char* tag, int depth, const char* root, const Worker::LmrStatBlock& b) {
    std::printf("info string %s depth %d root %s applied %llu rmean ", tag, depth, root,
                static_cast<unsigned long long>(b.applied));
    if (b.applied) std::printf("%.2f", static_cast<double>(b.r_sum) / static_cast<double>(b.applied));
    else std::printf("-");
    std::printf(" mag");
    for (int i = 0; i < Worker::LmrStatBlock::kBins; ++i)
        if (b.r_hist[i])
            std::printf(" r%d=%llu", i - Worker::LmrStatBlock::kBinOffset,
                        static_cast<unsigned long long>(b.r_hist[i]));
    std::printf(" research %llu", static_cast<unsigned long long>(b.research));
    std::printf(" rej %llu", static_cast<unsigned long long>(b.rej));
    std::printf(" [mate %llu fifty %llu depth %llu movecount %llu baremode %llu pvcap %llu]",
                static_cast<unsigned long long>(b.rej_mate), static_cast<unsigned long long>(b.rej_fifty),
                static_cast<unsigned long long>(b.rej_depth), static_cast<unsigned long long>(b.rej_movecount),
                static_cast<unsigned long long>(b.rej_bare), static_cast<unsigned long long>(b.rej_pvcap));
    std::printf(" cap_gate %llu cap_clamp %llu", static_cast<unsigned long long>(b.cap_gate),
                static_cast<unsigned long long>(b.cap_clamped));
    if (b.cap_gate) {
        std::printf(" cap_rmean %.2f cap_mag", static_cast<double>(b.cap_r_sum) / static_cast<double>(b.cap_gate));
        for (int i = 0; i < Worker::LmrStatBlock::kBins; ++i)
            if (b.cap_r_hist[i])
                std::printf(" r%d=%llu", i - Worker::LmrStatBlock::kBinOffset,
                            static_cast<unsigned long long>(b.cap_r_hist[i]));
    }
    std::printf("\n");
}
} // namespace
#endif // FORGE_LMR_STATS_PRINT

void Worker::lmr_note_reject(bool mate, bool fifty, bool dep, bool mcnt, bool bare, bool pvcap) {
    for (LmrStatBlock* b : {&lmr_iter_, &lmr_here()}) {
        ++b->rej;
        if (!mate) ++b->rej_mate;
        if (!fifty) ++b->rej_fifty;
        if (!dep) ++b->rej_depth;
        if (!mcnt) ++b->rej_movecount;
        if (!bare) ++b->rej_bare;
        if (!pvcap) ++b->rej_pvcap;
    }
}

void Worker::lmr_note_apply(int r_final, int r_before_cap, bool cap_gate, bool cap_clamped) {
    const int slot = std::clamp(r_final + LmrStatBlock::kBinOffset, 0, LmrStatBlock::kBins - 1);
    const int cap_slot = std::clamp(r_before_cap + LmrStatBlock::kBinOffset, 0, LmrStatBlock::kBins - 1);
    for (LmrStatBlock* b : {&lmr_iter_, &lmr_here()}) {
        ++b->applied;
        ++b->r_hist[slot];
        b->r_sum += static_cast<std::uint64_t>(r_final);
        if (cap_gate) {
            ++b->cap_gate;
            ++b->cap_r_hist[cap_slot];
            b->cap_r_sum += static_cast<std::uint64_t>(r_before_cap);
            if (cap_clamped) ++b->cap_clamped;
        }
    }
}

void Worker::lmr_note_research() {
    for (LmrStatBlock* b : {&lmr_iter_, &lmr_here()}) ++b->research;
}

void Worker::lmr_begin_iteration() {
#if FORGE_LMR_KEYS
    for (int i = 0; i < MaxPly + 8; ++i) { key_count_[i] = 0; key_xor_[i] = 0; key_sum_[i] = 0; }
#endif
    lmr_iter_.clear();
    for (auto& block : lmr_root_) block.clear();
}

void Worker::lmr_flush_iteration(int depth, bool emit) {
    lmr_total_.add(lmr_iter_);
#if FORGE_LMR_STATS_PRINT
    if (!emit) return;
    const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
#if FORGE_LMR_KEYS
    for (int p = 0; p < MaxPly + 8; ++p) {
        if (!key_count_[p]) continue;
        std::printf("info string keys depth %d ply %d count %llu xor %016llx sum %016llx\n",
                    depth, p, static_cast<unsigned long long>(key_count_[p]),
                    static_cast<unsigned long long>(key_xor_[p]),
                    static_cast<unsigned long long>(key_sum_[p]));
    }
    std::fflush(stdout);
#endif
    lmr_print_block("lmr", depth, "all", lmr_iter_);
    for (std::size_t i = 0; i < root_effort_count_ && i < lmr_root_.size(); ++i) {
        const LmrStatBlock& b = lmr_root_[i];
        if (b.applied == 0 && b.rej == 0 && b.cap_gate == 0) continue;
        const std::string root = Board::move_to_uci(root_effort_moves_[i]);
        lmr_print_block("lmr", depth, root.c_str(), b);
    }
    std::fflush(stdout);
#else
    (void)depth;
    (void)emit;
#endif
}

void Worker::lmr_flush_total(bool emit) {
#if FORGE_LMR_STATS_PRINT
    if (!emit) return;
    const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
    lmr_print_block("lmrsum", 0, "all", lmr_total_);
    std::printf("info string lmrsum cap_switch %s\n", lmr_cap_present_ ? "present" : "absent");
    std::fflush(stdout);
#else
    (void)emit;
#endif
}
#endif

int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {
'''

CPP_ROOTINIT_OLD = "    root_effort_count_ = root_candidates.size();\n"
CPP_ROOTINIT_NEW = """    root_effort_count_ = root_candidates.size();
#if FORGE_LMR_STATS
    lmr_total_.clear();
    lmr_iter_.clear();
    for (auto& block : lmr_root_) block.clear();
    lmr_root_current_ = 0;
    lmr_cap_present_ = FORGE_LMR_STATS_CAP_PRESENT;
#endif
"""


def patch_text(text, old, new, what, count=1):
    n = text.count(old)
    if n != count:
        sys.exit(f"ANCHOR FAIL: {what}: found {n} occurrences, expected {count}")
    return text.replace(old, new, count)


def do_hpp(root):
    p = os.path.join(root, HPP)
    s = open(p).read()
    s = patch_text(s, HPP_SWITCH_OLD, HPP_SWITCH_NEW, "hpp switch")
    s = patch_text(s, HPP_MEMBERS_OLD, HPP_MEMBERS_NEW, "hpp members")
    old = "    int qsearch(Board& board, SearchStack* ss, int alpha, int beta);\n"
    new = old + """#if FORGE_LMR_STATS
    void lmr_note_reject(bool mate, bool fifty, bool dep, bool mcnt, bool bare, bool pvcap);
    void lmr_note_apply(int r_final, int r_before_cap, bool cap_gate, bool cap_clamped);
    void lmr_note_research();
    void lmr_begin_iteration();
    void lmr_flush_iteration(int depth, bool emit);
    void lmr_flush_total(bool emit);
#endif
"""
    s = patch_text(s, old, new, "hpp method decls")
    open(p, "w").write(s)


KEY_ANCHOR = """    ++local_nodes_;
    seldepth_ = std::max(seldepth_, ply);
"""
KEY_NEW = """    ++local_nodes_;
#if FORGE_LMR_KEYS
    if (ply >= 0 && ply < MaxPly + 8) {
        const std::uint64_t visited_key = board.key();
        ++key_count_[ply];
        key_xor_[ply] ^= visited_key;
        key_sum_[ply] += visited_key;
    }
#endif
    seldepth_ = std::max(seldepth_, ply);
"""


def do_cpp(root, cap, cap_macro):
    p = os.path.join(root, CPP)
    s = open(p).read()
    s = patch_text(s, CPP_INCLUDE_OLD, CPP_INCLUDE_NEW, "cpp include")
    s = patch_text(s, CPP_HELPERS_OLD, CPP_HELPERS_NEW, "cpp helpers")
    s = patch_text(s, CPP_ROOTINIT_OLD, CPP_ROOTINIT_NEW, "cpp root init")

    # define the cap-present constant from the tree's own switch
    old = "#if FORGE_LMR_STATS\n#include <cstdio>\n#endif\n"
    new = ("#if FORGE_LMR_STATS\n#include <cstdio>\n" + cap_macro + "#endif\n")
    s = patch_text(s, old, new, "cpp cap present macro")

    # 1. the LMR guard, with its five conditions named once so the rejection
    #    counters cannot describe a different condition than the one gating LMR.
    guard_old = """        if (mate_moves_ == 0 && board.halfmove_clock() + new_depth < 100 && depth >= 2 &&
            move_count > 1 + (root_node ? 1 : 0) && !bare_king_mode &&
            (quiet || !ss->tt_pv || move_count > 4)) {
"""
    guard_new = """#if FORGE_LMR_STATS
        // The guard's conditions, named once: the rejection counters below read the
        // same flags that gate LMR, so they cannot drift from the condition.
        const bool lg_mate = mate_moves_ == 0;
        const bool lg_fifty = board.halfmove_clock() + new_depth < 100;
        const bool lg_depth = depth >= 2;
        const bool lg_mcount = move_count > 1 + (root_node ? 1 : 0);
        const bool lg_bare = !bare_king_mode;
        const bool lg_pvcap = (quiet || !ss->tt_pv || move_count > 4);
        const bool lmr_guard = lg_mate && lg_fifty && lg_depth && lg_mcount && lg_bare && lg_pvcap;
        if (!root_node && !lmr_guard) lmr_note_reject(lg_mate, lg_fifty, lg_depth, lg_mcount, lg_bare, lg_pvcap);
        if (lmr_guard) {
#else
        if (mate_moves_ == 0 && board.halfmove_clock() + new_depth < 100 && depth >= 2 &&
            move_count > 1 + (root_node ? 1 : 0) && !bare_king_mode &&
            (quiet || !ss->tt_pv || move_count > 4)) {
#endif
"""
    s = patch_text(s, guard_old, guard_new, "cpp lmr guard")

    # 2. the cap site (cap trees only) captures r before the clamp
    if cap:
        cap_old = "            if (bare_king_lmr_cap) r = std::min(r, 1);\n"
        cap_new = """#if FORGE_LMR_STATS
            const int lmr_r_before_cap = r;
            const bool lmr_cap_gate = bare_king_lmr_cap;
            if (bare_king_lmr_cap) r = std::min(r, 1);
            const bool lmr_cap_clamped = lmr_cap_gate && (r < lmr_r_before_cap);
#else
            if (bare_king_lmr_cap) r = std::min(r, 1);
#endif
"""
        s = patch_text(s, cap_old, cap_new, "cpp cap site")
        note = """#if FORGE_LMR_STATS
            lmr_note_apply(r, lmr_r_before_cap, lmr_cap_gate, lmr_cap_clamped);
#endif
"""
    else:
        note = """#if FORGE_LMR_STATS
            lmr_note_apply(r, r, false, false);
#endif
"""

    # 3. count the applied reduction once the final r is known
    apply_old = "            const int reduced_depth = std::clamp(new_depth - r, 1, new_depth);\n"
    s = patch_text(s, apply_old, apply_old + note, "cpp note apply")

    # 4. count the re-search
    research_old = """            if (full_depth_needed) {
                if (tune::LmrDeeperShallower) {
"""
    research_new = """            if (full_depth_needed) {
#if FORGE_LMR_STATS
                lmr_note_research();
#endif
                if (tune::LmrDeeperShallower) {
"""
    s = patch_text(s, research_old, research_new, "cpp note research")

    # 5. attribute the subtree below a root move to that root move. The index is
    #    already computed inside the root-only block, so both hooks sit in code
    #    that runs at ply 0 only: no save/restore is needed and no other move
    #    loop (qsearch, singular verification) is touched.
    mark_old = """        if (root_node) {
            const auto root_effort_end = root_effort_moves_.begin() + static_cast<std::ptrdiff_t>(root_effort_count_);
            root_effort_index = static_cast<std::size_t>(std::find(root_effort_moves_.begin(), root_effort_end, move) - root_effort_moves_.begin());
            assert(root_effort_index < root_effort_count_);
        }
"""
    mark_new = """        if (root_node) {
            const auto root_effort_end = root_effort_moves_.begin() + static_cast<std::ptrdiff_t>(root_effort_count_);
            root_effort_index = static_cast<std::size_t>(std::find(root_effort_moves_.begin(), root_effort_end, move) - root_effort_moves_.begin());
            assert(root_effort_index < root_effort_count_);
#if FORGE_LMR_STATS
            lmr_root_current_ = root_effort_index;
#endif
        }
"""
    s = patch_text(s, mark_old, mark_new, "cpp root current set")

    restore_old = """        if (root_node && root_effort_index < root_effort_count_)
            root_move_nodes_[root_effort_index] += local_nodes_ - nodes_before;
"""
    restore_new = """        if (root_node && root_effort_index < root_effort_count_) {
            root_move_nodes_[root_effort_index] += local_nodes_ - nodes_before;
#if FORGE_LMR_STATS
            lmr_root_current_ = 0;
#endif
        }
"""
    s = patch_text(s, restore_old, restore_new, "cpp root current restore")

    # per-ply visited-key fingerprint (FORGE_LMR_KEYS). There are TWO
    # `++local_nodes_; seldepth_ = ...` sites in this tree (search and
    # search_cuckoo); both are real node visits, so both are counted, and the
    # expected count is asserted rather than assumed -- an earlier version of this
    # generator used a bare str.replace on an anchor that did not match, silently
    # inserted nothing, and the resulting build printed no key lines at all.
    s = patch_text(s, KEY_ANCHOR, KEY_NEW, "cpp key fingerprint", count=2)

    open(p, "w").write(s)


def do_loop_hooks(root):
    p = os.path.join(root, CPP)
    s = open(p).read()

    old = """    for (int depth = 1; depth <= max_depth; ++depth) {
        root_depth_ = depth;
"""
    new = """    for (int depth = 1; depth <= max_depth; ++depth) {
        root_depth_ = depth;
#if FORGE_LMR_STATS
        lmr_begin_iteration();
#endif
"""
    s = patch_text(s, old, new, "cpp iteration begin")

    old = """        } else {
            emit(depth, score, result.pv);
        }
"""
    new = """        } else {
            emit(depth, score, result.pv);
        }
#if FORGE_LMR_STATS
        lmr_flush_iteration(depth, emit_info);
#endif
"""
    s = patch_text(s, old, new, "cpp iteration flush")

    old = "    if (result.best_move.is_none()) result.best_move = root_candidates.front();\n"
    new = """    if (result.best_move.is_none()) result.best_move = root_candidates.front();
#if FORGE_LMR_STATS
    lmr_flush_total(emit_info);
#endif
"""
    s = patch_text(s, old, new, "cpp total flush")

    open(p, "w").write(s)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: make_lmr_stats.py SRC_DIR [cap|nocap]")
    root = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "nocap"
    cap = mode == "cap"
    cap_macro = ("#define FORGE_LMR_STATS_CAP_PRESENT 1\n" if cap
                 else "#define FORGE_LMR_STATS_CAP_PRESENT 0\n")
    do_hpp(root)
    do_cpp(root, cap, cap_macro)
    do_loop_hooks(root)
    print(f"instrumented {root} (mode={mode})")


if __name__ == "__main__":
    main()
