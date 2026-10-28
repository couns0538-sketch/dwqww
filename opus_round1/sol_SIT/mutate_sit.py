"""Planted-bug mutants for S-IT (copies src/include/tests into a NEW folder and patches one spot).

usage: python -I -B mutate_sit.py <worktree> <new dir> <mutant>      (python -I -B mutate_sit.py --list)
Every mutant must make tests/intended_threefold_tests.cpp fail. Each edit's pattern must occur exactly once.
Not mutated on purpose (equivalent mutants, no value can show them): the legality test on a claim hit (a
position reached by an illegal move, with the mover's king attacked, never occurred in a legal history); the
castling rights dropped by the claiming move (the resulting position has fewer rights than every window
position, and the same position with the old rights, king or rook off its home square, never occurs either; a
mutant that kept the old rights survived, see logs); the pv_node recompute at claim nodes (search efficiency
only, values unchanged by design).
"""
import os
import shutil
import sys

TT_Q_OLD = ("    const int tt_score = !claim && tt_hit && tte.score_usable(board.halfmove_clock())\n"
            "                             ? score_from_tt(tte.score, ply) : ValueNone;\n"
            "    const Bound tt_bound = tt_hit ? tte.bound() : BoundNone;\n"
            "    const bool tt_pv")
TT_S_OLD = ("    const int tt_score = !claim && tt_hit && tte.score_usable(board.halfmove_clock())\n"
            "                             ? score_from_tt(tte.score, ply) : ValueNone;\n"
            "    const int tt_depth")
SEARCH_CLAIM = ("        if (claim) {\n            if (beta <= 0) return 0;\n            claim_raised_alpha = alpha < 0;\n"
                "            alpha = std::max(alpha, 0);\n            pv_node = beta - alpha > 1;\n        }\n    }")
QSEARCH_CLAIM = ("    const bool claim = options::intended_threefold && board.can_claim_threefold_by_next_move();\n"
                 "    if (claim) {\n        if (beta <= 0) return 0;\n        alpha = std::max(alpha, 0);\n    }\n")
S = "src/search.cpp"
B = "src/board.cpp"
M = {
    # --- the original six (code of edc2519, patterns updated for the follow-up) ---
    # qsearch uses cached TT scores at claim nodes
    "tt_cut": [(S, TT_Q_OLD, TT_Q_OLD.replace("!claim && ", ""))],
    # search uses cached TT scores at claim nodes
    "tt_cut_search": [(S, TT_S_OLD, TT_S_OLD.replace("!claim && ", ""))],
    # the claim forces a draw in search() instead of acting as a floor (loses mate precedence and captures)
    "forced_draw": [(S, SEARCH_CLAIM, "        if (claim) return 0;\n    }")],
    # history before the most recent null move is scanned
    "null_window": [(B, "                                                         static_cast<std::ptrdiff_t>(plies_from_null_));",
                     "                                                         static_cast<std::ptrdiff_t>(1024));")],
    # qsearch stores the history-dependent claim value in the TT (final store)
    "store": [(S, "    if (!claim) {\n        shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), in_check",
               "    if (true) {\n        shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), in_check")],
    # one earlier occurrence is enough (twofold instead of threefold): every window key joins the set
    "twofold": [(B, "        if ((buckets & bucket) != 0U) {", "        if (true) {"),
                (B, "            for (std::ptrdiff_t j = i + 2; j <= size - 2; j += 2) {",
                 "            for (std::ptrdiff_t j = i; j <= size - 2; j += 2) {")],
    # --- code review (reviewer's single-guard mutants, same edits as review_sit/mut/make_single.py) ---
    # search() post-loop floor removed
    "search_floor": [(S, "    if (claim && best_score < 0) best_score = 0;\n\n    if (best_score >= beta) {",
                      "\n\n    if (best_score >= beta) {")],
    # search() final TT store guard removed (the real score is stored at claim nodes)
    "search_store": [(S, "if (excluded.is_none() && !(root_node && root_restricted_) && !claim) {",
                      "if (excluded.is_none() && !(root_node && root_restricted_)) {")],
    # ProbCut TT store guard removed
    "probcut_store": [(S, "                    if (!claim) {\n                        shared_.tt.store(tt_probe, board.key(), score_to_tt(value, ply)",
                       "                    if (true) {\n                        shared_.tt.store(tt_probe, board.key(), score_to_tt(value, ply)")],
    # correction-history guard removed
    "correction": [(S, "if (!in_check && excluded.is_none() && !claim && !is_mate_score(best_score) &&",
                    "if (!in_check && excluded.is_none() && !is_mate_score(best_score) &&")],
    # qsearch stand-pat TT store guard removed
    "standpat_store": [(S, "if (!tt_hit && !claim) shared_.tt.store(", "if (!tt_hit) shared_.tt.store(")],
    # qsearch claim as a forced draw (same edit as review_sit/mut/make_qforced.py)
    "qsearch_forced_draw": [(S, QSEARCH_CLAIM,
                             "    const bool claim = options::intended_threefold && board.can_claim_threefold_by_next_move();\n"
                             "    if (claim) return 0;\n")],
    # --- code-review follow-up fixes ---
    # placeholder entries carry the real (history-dependent) score instead of the raw ValueNone
    "placeholder_score_qsearch": [(S, "shared_.tt.store(tt_probe, board.key(), ValueNone, in_check ? ValueNone : ss->raw_eval",
                                   "shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), in_check ? ValueNone : ss->raw_eval")],
    "placeholder_score_search": [(S, "shared_.tt.store(tt_probe, board.key(), ValueNone, ss->raw_eval, best_move, 0, BoundUpper",
                                  "shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, 0, BoundUpper")],
    # the trap: ValueNone passed through score_to_tt (stored as 32002 + ply, a mate-like score at other plies)
    "placeholder_via_score_to_tt": [(S, "shared_.tt.store(tt_probe, board.key(), ValueNone, ss->raw_eval, best_move, 0, BoundUpper",
                                     "shared_.tt.store(tt_probe, board.key(), score_to_tt(ValueNone, ply), ss->raw_eval, best_move, 0, BoundUpper")],
    # fail-low continuation bonus although the claim floor raised alpha
    "fail_low_bonus": [(S, "best_move.is_none() && !claim_raised_alpha &&", "best_move.is_none() &&")],
    # perf fix: only the first duplicated key joins the set (an early exit as in the old pre-check)
    "dup_first_only": [(B, "    for (std::ptrdiff_t i = size - 2; i >= lo; i -= 2) {\n        const std::uint64_t key = key_at(i);",
                        "    for (std::ptrdiff_t i = size - 2; i >= lo && twice_count == 0; i -= 2) {\n        const std::uint64_t key = key_at(i);")],
    # perf fix: the current castling-rights term is not removed from the resulting key
    "castling_base": [(B, "const std::uint64_t base = key_ ^ ep_key ^ Z.side ^ Z.castling[castling_];",
                       "const std::uint64_t base = key_ ^ ep_key ^ Z.side;")],
    # perf fix: the bucket mask of the set is never filled (the mask then rejects every resulting key)
    "mask_unset": [(B, "                    twice_buckets |= bucket;\n", "")],
    # perf fix: king moves are not generated
    "king_skipped": [(B, "           reaches_twice(Queen, [occ](int square) { return attacks::queen(square, occ); }) ||\n"
                         "           reaches_twice(King, [](int square) { return attacks::king(square); });",
                      "           reaches_twice(Queen, [occ](int square) { return attacks::queen(square, occ); });")],
}

if len(sys.argv) == 2 and sys.argv[1] == "--list":
    print(" ".join(M))
    raise SystemExit(0)
src, dst, which = sys.argv[1], sys.argv[2], sys.argv[3]
if which not in M:
    raise SystemExit("unknown mutant %s; known: %s" % (which, " ".join(M)))
if os.path.exists(dst):
    raise SystemExit("mutant dir exists: " + dst)
for d in ("src", "include", "tests"):
    shutil.copytree(os.path.join(src, d), os.path.join(dst, d))
for f, old, new in M[which]:
    p = os.path.join(dst, f)
    s = open(p, encoding="utf-8").read()
    if s.count(old) != 1:
        raise SystemExit("pattern for %s occurs %d times in %s" % (which, s.count(old), f))
    open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))
print("mutant", which, "written to", dst)
