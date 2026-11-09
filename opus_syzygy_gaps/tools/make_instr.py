#!/usr/bin/env python3
"""make_instr.py - test-only instrumented copy of a Forge tree (never built into an engine that is handed on).

usage: python -I -B make_instr.py <src tree> <new dst tree>
Every TB-band score that a search node returns or uses as a claim is checked against the loaded tables at that node, per
site. Interior probing is limited by the test global syzygy::test_card (the root filter is skipped when it is set), so that
5-piece nodes are searched while the 5-piece tables stay loaded as truth. Each anchor must match exactly once.
"""
import os
import shutil
import sys

HOOK_HEADER = r'''
// ---- test instrumentation (make_instr.py) ----
namespace forge::syzygy {
struct ClaimSite { std::uint64_t events = 0, wrong = 0, unknown = 0; };
inline constexpr int ClaimSites = 16;
extern ClaimSite claim_sites[ClaimSites];
extern int test_card;
extern std::uint64_t corr_updates_tb, corr_updates_all, pv_bound_returns;
inline const char* claim_site_name(int i) {
    static const char* n[ClaimSites] = {"-", "null_move", "end_pruned_loss", "end_other_win", "end_other_loss", "rfp_return",
        "razor_return", "probcut_return", "singular_multicut", "tt_cut_main", "tt_cut_qs", "qs_standpat", "qs_end", "pv_tb_bound",
        "tb_probe_nonpv", "-"};
    return n[i];
}
void claim_check(Board& board, int site, int score);
}
'''

HOOK_BODY = r'''
// ---- test instrumentation (make_instr.py) ----
namespace forge::syzygy {
ClaimSite claim_sites[ClaimSites];
int test_card = 0;
std::uint64_t corr_updates_tb = 0, corr_updates_all = 0, pv_bound_returns = 0;
[[gnu::cold]] void claim_check(Board& board, int site, int score) {
    if (std::abs(score) < TbWinInMaxPly || std::abs(score) >= MateInMaxPly) return;
    ClaimSite& s = claim_sites[site];
    ++s.events;
    int dtz = 0;
    bool rounded = false;
    if (!probe_dtz(board, dtz, rounded)) { ++s.unknown; return; }
    const int clock = board.halfmove_clock();
    const int d = dtz < 0 ? -dtz : dtz;
    const bool sign_ok = score > 0 ? dtz > 0 : dtz < 0;
    if (!sign_ok || d + clock > 100) {
        if (s.wrong < 8) {
            std::cerr << "WRONG site " << claim_site_name(site) << " score " << score << " dtz " << dtz << " clock " << clock
                      << " fen " << board.fen() << "\n";
        }
        ++s.wrong;
    } else if (d + clock == 100 && rounded) {
        ++s.unknown;
    }
}
} // namespace forge::syzygy
'''

EDITS = [
    # root: limit interior probes, skip the root filter
    ('src/tablebase.inc',
     "    const int largest = max_pieces();\n    search_cardinality.store(largest, std::memory_order_relaxed);\n    root_display.store(0, std::memory_order_relaxed);\n",
     "    const int largest = max_pieces();\n    search_cardinality.store(test_card != 0 ? test_card : largest, std::memory_order_relaxed);\n    root_display.store(0, std::memory_order_relaxed);\n    if (test_card != 0) return;\n"),
    ('src/tablebase.inc',
     "    const bool pv_node = beta - alpha > 1;\n    if (bound != BoundExact && !pv_node",
     "    const bool pv_node = beta - alpha > 1;\n    if (bound != BoundExact && pv_node && !(bound == BoundLower ? value >= beta : value <= alpha)) { ++syzygy::pv_bound_returns; syzygy::claim_check(board, 13, value); }\n    if (bound != BoundExact && !pv_node"),
    # null move
    ('src/search.cpp',
     "            if (null_score >= beta) {\n                if (is_mate_score(null_score)) null_score = beta;\n",
     "            if (null_score >= beta) {\n                syzygy::claim_check(board, 1, null_score);\n                if (is_mate_score(null_score)) null_score = beta;\n"),
    # RFP
    ('src/search.cpp',
     "            eval < MateInMaxPly) {\n            return eval;\n",
     "            eval < MateInMaxPly) {\n            syzygy::claim_check(board, 5, eval);\n            return eval;\n"),
    # razor
    ('src/search.cpp',
     "            if (razor < alpha) return razor;\n",
     "            if (razor < alpha) { if (razor < 0) syzygy::claim_check(board, 6, razor); return razor; }\n"),
    # probcut
    ('src/search.cpp',
     "                if (value >= probcut_beta) {\n                    shared_.tt.store(tt_probe, board.key(), score_to_tt(value, ply), ss->raw_eval, move, depth - 3, BoundLower, ss->tt_pv, board.halfmove_clock());\n",
     "                if (value >= probcut_beta) {\n                    syzygy::claim_check(board, 7, value);\n                    shared_.tt.store(tt_probe, board.key(), score_to_tt(value, ply), ss->raw_eval, move, depth - 3, BoundLower, ss->tt_pv, board.halfmove_clock());\n"),
    # singular multicut
    ('src/search.cpp',
     "            } else if (singular_beta >= beta) {\n                return singular_beta;\n",
     "            } else if (singular_beta >= beta) {\n                syzygy::claim_check(board, 8, singular_beta);\n                return singular_beta;\n"),
    # TT cut main
    ('src/search.cpp',
     "        board.halfmove_clock() < 90 &&\n        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||\n         (tt_bound == BoundUpper && tt_score <= alpha))) {\n        return tt_score;\n",
     "        board.halfmove_clock() < 90 &&\n        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||\n         (tt_bound == BoundUpper && tt_score <= alpha))) {\n        if (tt_bound == BoundExact || (tt_bound == BoundLower) == (tt_score > 0)) syzygy::claim_check(board, 9, tt_score);\n        return tt_score;\n"),
    # TT cut qsearch
    ('src/search.cpp',
     "        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||\n         (tt_bound == BoundUpper && tt_score <= alpha))) {\n        return tt_score;\n    }\n\n    int best_score;\n",
     "        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||\n         (tt_bound == BoundUpper && tt_score <= alpha))) {\n        if (tt_bound == BoundExact || (tt_bound == BoundLower) == (tt_score > 0)) syzygy::claim_check(board, 10, tt_score);\n        return tt_score;\n    }\n\n    int best_score;\n"),
    # pruning flags
    ('src/search.cpp',
     "    bool skip_quiets = false;\n    const bool has_material = board.has_non_pawn_material(board.side_to_move());\n",
     "    bool skip_quiets = false;\n    bool test_pruned = false;\n    const bool has_material = board.has_non_pawn_material(board.side_to_move());\n"),
    ('src/search.cpp',
     "            if (quiet && !skip_quiets && move_count >= lmp_threshold(depth, improving)) skip_quiets = true;\n",
     "            if (quiet && !skip_quiets && move_count >= lmp_threshold(depth, improving)) { skip_quiets = true; test_pruned = true; }\n"),
    ('src/search.cpp',
     "                    ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth <= alpha) {\n                    skip_quiets = true;\n                    continue;\n",
     "                    ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth <= alpha) {\n                    skip_quiets = true;\n                    test_pruned = true;\n                    continue;\n"),
    ('src/search.cpp',
     "                if (lmr_depth <= tune::HistoryPruneDepth && history < -tune::HistoryPruneMultiplier * depth) continue;\n                if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) continue;\n",
     "                if (lmr_depth <= tune::HistoryPruneDepth && history < -tune::HistoryPruneMultiplier * depth) { test_pruned = true; continue; }\n                if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) { test_pruned = true; continue; }\n"),
    ('src/search.cpp',
     "                if (!(picker.last_move_see_nonnegative() && see_threshold <= 0) &&\n                    !board.see_ge(move, see_threshold)) continue;\n",
     "                if (!(picker.last_move_see_nonnegative() && see_threshold <= 0) &&\n                    !board.see_ge(move, see_threshold)) { test_pruned = true; continue; }\n"),
    # node end
    ('src/search.cpp',
     "    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);\n    if (excluded.is_none() && !(root_node && root_restricted_)) {\n",
     "    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);\n    if (excluded.is_none()) {\n        if (best_score <= -syzygy::TbWinInMaxPly && bound != BoundLower) syzygy::claim_check(board, test_pruned ? 2 : 4, best_score);\n        else if (best_score >= syzygy::TbWinInMaxPly && bound != BoundUpper) syzygy::claim_check(board, 3, best_score);\n    }\n    if (excluded.is_none() && !(root_node && root_restricted_)) {\n"),
    # correction history
    ('src/search.cpp',
     "        !(bound == BoundUpper && best_score >= ss->static_eval)) {\n        update_correction(board, depth, best_score, ss->static_eval);\n",
     "        !(bound == BoundUpper && best_score >= ss->static_eval)) {\n        ++syzygy::corr_updates_all;\n        if (std::abs(best_score) >= syzygy::TbWinInMaxPly) ++syzygy::corr_updates_tb;\n        update_correction(board, depth, best_score, ss->static_eval);\n"),
    # qsearch stand pat from a TT bound and end
    ('src/search.cpp',
     "        if (best_score >= beta) {\n            if (!tt_hit) shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());\n",
     "        if (best_score >= beta) {\n            syzygy::claim_check(board, 11, best_score);\n            if (!tt_hit) shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());\n"),
]


def main():
    src, dst = sys.argv[1:3]
    if os.path.exists(dst):
        sys.exit(f'refusing: {dst} exists')
    shutil.copytree(src, dst)
    for rel, old, new in EDITS:
        p = os.path.join(dst, rel)
        s = open(p, encoding='utf-8', newline='').read()
        n = s.count(old)
        if n != 1:
            sys.exit(f'anchor count {n} in {rel}: {old[:80]!r}')
        open(p, 'w', encoding='utf-8', newline='').write(s.replace(old, new))
    p = os.path.join(dst, 'include/forge/syzygy.hpp')
    s = open(p, encoding='utf-8', newline='').read()
    open(p, 'w', encoding='utf-8', newline='').write(s + HOOK_HEADER)
    p = os.path.join(dst, 'src/search.cpp')
    s = open(p, encoding='utf-8', newline='').read()
    open(p, 'w', encoding='utf-8', newline='').write(s + HOOK_BODY)
    print('instrumented', dst)


if __name__ == '__main__':
    main()
