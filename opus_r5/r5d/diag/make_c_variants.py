"""R5D candidate fixes (scratch only). C6: in a multi-worker search a same-position TT entry is overwritten only by an
equal-or-deeper result, an exact bound or a newer generation (store rule). C2: helpers store no upper bounds."""
import subprocess
from pathlib import Path

WT = "D:/grok-pc-data/dwqww/.claude/worktrees/opus-r5d-matefix"


def export(name):
    root = Path("F:/opus_scratch/r5/r5d") / name
    root.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(["git", "-C", WT, "-c", "core.autocrlf=false", "archive", "HEAD", "src", "include"],
                             check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
    return root


def patch(path, old, new):
    s = path.read_bytes().decode()
    assert s.count(old) == 1, (path, old[:60])
    path.write_bytes(s.replace(old, new).encode())


# C6
root = export("exp_c6")
patch(root / "include/forge/tt.hpp", "    bool lockless_ = false;\n",
      "    bool lockless_ = false;\npublic:\n    bool shared_writers_ = false;  // R5D experiment: more than one worker\nprivate:\n")
patch(root / "src/search/tt.inc",
      "    if (bound == BoundExact || !same_position || depth + 4 > entry->depth || entry->generation() != generation_) {\n",
      "    const bool deep_enough = shared_writers_ ? depth >= entry->depth : depth + 4 > entry->depth;\n"
      "    if (bound == BoundExact || !same_position || deep_enough || entry->generation() != generation_) {\n")
patch(root / "src/search/searcher.inc", "    shared_.tt.new_search();\n",
      "    shared_.tt.new_search();\n    shared_.tt.shared_writers_ = workers_.size() > 1;\n")
print("prepared exp_c6")

# C2
root = export("exp_c2")
patch(root / "src/search/alphabeta.inc",
      "    if (excluded.is_none() && !(root_node && root_restricted_) && !claim) {\n",
      "    if (excluded.is_none() && !(root_node && root_restricted_) && !claim && (is_main() || bound != BoundUpper)) {\n")
q = root / "src/search/qsearch.inc"
s = q.read_bytes().decode()
old = "        shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), in_check ? ValueNone : ss->raw_eval, best_move, 0, bound, tt_pv, board.halfmove_clock());\n"
assert s.count(old) == 1
s = s.replace(old, "        if (is_main() || bound != BoundUpper) " + old.lstrip())
q.write_bytes(s.encode())
print("prepared exp_c2")
