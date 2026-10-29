"""R5D diagnosis 5 (scratch only, on a fresh export): at the node "1.Kc5 Ka6" (White to move, mate in 2 with Re7) log,
per search, what happens to Re7: pruned by LMP skip / futility / history / SEE, or searched (depth, value)."""
import subprocess
from pathlib import Path

WT = "D:/grok-pc-data/dwqww/.claude/worktrees/opus-r5d-matefix"
root = Path("F:/opus_scratch/r5/r5d/diag5")
root.mkdir(parents=True, exist_ok=True)
archive = subprocess.run(["git", "-C", WT, "-c", "core.autocrlf=false", "archive", "HEAD", "src", "include"],
                         check=True, capture_output=True).stdout
subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)

sc = root / "src/search.cpp"
s = sc.read_bytes().decode()
anchor = '#include "forge/uci_output.hpp"\n'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '#include <cstdio>\n#include <mutex>\n#include <string>\n'
              'namespace r5d_diag { std::uint64_t key = 0; std::string log; bool on = false; std::mutex mutex; }\n')
sc.write_bytes(s.encode())

ab = root / "src/search/alphabeta.inc"
a = ab.read_bytes().decode()


def rep(old, new):
    global a
    assert a.count(old) == 1, old[:60]
    a = a.replace(old, new)


# A per-node note list for the watched node.
rep("    int move_count = 0;\n    bool skip_quiets = false;\n",
    "    int move_count = 0;\n    bool skip_quiets = false;\n"
    "    const bool r5d_watch = r5d_diag::on && board.key() == r5d_diag::key;\n    std::string r5d_note;\n")
# Moves the picker no longer yields after skip_quiets are invisible; record the LMP trigger and pruning decisions.
rep("            if (quiet && !skip_quiets && move_count >= FORGE_LMP_THRESHOLD(depth, improving)) skip_quiets = true;\n#endif\n",
    "            if (quiet && !skip_quiets && move_count >= FORGE_LMP_THRESHOLD(depth, improving)) {\n"
    "                skip_quiets = true;\n"
    "                if (r5d_watch) r5d_note += \" LMP-skip@\" + std::to_string(move_count) + \"(\" + Board::move_to_uci(move) + \")\";\n"
    "            }\n#endif\n")
rep("""                    skip_quiets = true;
                    continue;
                }
#ifdef FORGE_PROF
                prof::count(prof::Counter::HistoryChecks);""", """                    skip_quiets = true;
                    if (r5d_watch) r5d_note += " futility-skip@" + std::to_string(move_count) + "(" + Board::move_to_uci(move) + ")";
                    continue;
                }
#ifdef FORGE_PROF
                prof::count(prof::Counter::HistoryChecks);""")
rep("""                if (lmr_depth <= tune::HistoryPruneDepth && history < history_prune_threshold) continue;
                if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) continue;
#endif""", """                if (lmr_depth <= tune::HistoryPruneDepth && history < history_prune_threshold) {
                    if (r5d_watch) r5d_note += " hist-prune(" + Board::move_to_uci(move) + " h" + std::to_string(history) + ")";
                    continue;
                }
                if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) {
                    if (r5d_watch) r5d_note += " see-prune(" + Board::move_to_uci(move) + ")";
                    continue;
                }
#endif""")
rep("""        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (root_node && root_effort_index < root_effort_count_)""", """        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (r5d_watch && Board::move_to_uci(move) == "e8e7")
            r5d_note += " Re7#" + std::to_string(move_count) + "=" + std::to_string(score);
        if (root_node && root_effort_index < root_effort_count_)""")
rep("""    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
""", """    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
    if (r5d_watch) {
        char r5d_buf[200];
        std::snprintf(r5d_buf, sizeof r5d_buf, "  w%d it%d d%d [%d,%d] moves %d best %d %s bound %d:", id_, root_depth_, depth,
                      alpha, beta, move_count, best_score, Board::move_to_uci(best_move).c_str(), static_cast<int>(bound));
        const std::lock_guard<std::mutex> lock(r5d_diag::mutex);
        r5d_diag::log += r5d_buf + r5d_note + "\\n";
    }
""")
ab.write_bytes(a.encode())
print("diag5 ready")
