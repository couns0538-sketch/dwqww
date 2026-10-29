"""R5D suspect-order experiments 4 and 6 (scratch only): exports of the base tree 5eabdb7 with
   NOASP: no aspiration window (every iteration searches the full window);
   NOMDP: no mate-distance pruning in the main search.
usage: make_asp_mdp.py <worktree> <scratch root>   (writes <scratch>/exp_noasp and <scratch>/exp_nomdp)"""
import subprocess
import sys
from pathlib import Path

wt, scratch = sys.argv[1], Path(sys.argv[2])
archive = subprocess.run(["git", "-C", wt, "-c", "core.autocrlf=false", "archive", "5eabdb7", "src", "include"],
                         check=True, capture_output=True).stdout


def variant(name, path, old, new):
    root = scratch / name
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
    p = root / path
    s = p.read_bytes().decode()
    assert s.count(old) == 1, (name, old[:60])
    p.write_bytes(s.replace(old, new).encode())
    print("prepared", root)


variant("exp_noasp", "src/search/iterative.inc", "        if (depth >= 4) {\n            alpha = std::max(score - delta, -Infinite);",
        "        if (false && depth >= 4) {  // R5D NOASP\n            alpha = std::max(score - delta, -Infinite);")
variant("exp_nomdp", "src/search/alphabeta.inc",
        "        alpha = std::max(alpha, mated_in(ply));\n        beta = std::min(beta, mate_in(ply + 1));\n        if (alpha >= beta) return alpha;\n",
        "        // R5D NOMDP: mate distance pruning removed\n")
