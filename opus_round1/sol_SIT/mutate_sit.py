"""Planted-bug mutants for S-IT (copies src/include/tests into a NEW folder and patches one spot)."""
import os
import shutil
import sys

src, dst, which = sys.argv[1], sys.argv[2], sys.argv[3]
if os.path.exists(dst):
    raise SystemExit("mutant dir exists: " + dst)
for d in ("src", "include", "tests"):
    shutil.copytree(os.path.join(src, d), os.path.join(dst, d))

TT_Q_OLD = ("    const int tt_score = !claim && tt_hit && tte.score_usable(board.halfmove_clock())\n"
            "                             ? score_from_tt(tte.score, ply) : ValueNone;\n"
            "    const Bound tt_bound = tt_hit ? tte.bound() : BoundNone;\n"
            "    const bool tt_pv")
TT_S_OLD = ("    const int tt_score = !claim && tt_hit && tte.score_usable(board.halfmove_clock())\n"
            "                             ? score_from_tt(tte.score, ply) : ValueNone;\n"
            "    const int tt_depth")
M = {
    # qsearch uses cached TT scores at claim nodes
    "tt_cut": ("src/search.cpp", TT_Q_OLD, TT_Q_OLD.replace("!claim && ", "")),
    # search uses cached TT scores at claim nodes
    "tt_cut_search": ("src/search.cpp", TT_S_OLD, TT_S_OLD.replace("!claim && ", "")),
    # the claim forces a draw instead of acting as a floor (loses mate precedence)
    "forced_draw": ("src/search.cpp",
                    "        if (claim) {\n            if (beta <= 0) return 0;\n            alpha = std::max(alpha, 0);\n        }\n    }",
                    "        if (claim) return 0;\n    }"),
    # history before the most recent null move is scanned
    "null_window": ("src/board.cpp",
                    "                                                         static_cast<std::ptrdiff_t>(plies_from_null_));",
                    "                                                         static_cast<std::ptrdiff_t>(1024));"),
    # qsearch stores the history-dependent claim value in the TT
    "store": ("src/search.cpp",
              "    if (!claim) {\n        shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), in_check",
              "    if (true) {\n        shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), in_check"),
    # one earlier occurrence is enough (twofold instead of threefold)
    "twofold": ("src/board.cpp", "        if (count >= 2 && is_legal(move)) return true;",
                "        if (count >= 1 && is_legal(move)) return true;"),
}
f, old, new = M[which]
p = os.path.join(dst, f)
s = open(p, encoding="utf-8").read()
if s.count(old) != 1:
    raise SystemExit("pattern for %s occurs %d times" % (which, s.count(old)))
open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))
print("mutant", which, "written to", dst)
