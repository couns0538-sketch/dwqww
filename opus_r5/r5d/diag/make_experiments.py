"""R5D fix experiments (scratch only): F3 = helpers never store in the main search; F2 = helpers skip only fail-low
upper bounds without a best move and without a mate score. Each variant is a fresh export of the branch."""
import subprocess
import sys
from pathlib import Path

WT = "D:/grok-pc-data/dwqww/.claude/worktrees/opus-r5d-matefix"
STORE = "    if (excluded.is_none() && !(root_node && root_restricted_) && !claim) {\n"
VARIANTS = {
    "exp_f3": "    if (excluded.is_none() && !(root_node && root_restricted_) && !claim && is_main()) {\n",
    "exp_f2": ("    if (excluded.is_none() && !(root_node && root_restricted_) && !claim &&\n"
               "        (is_main() || bound != BoundUpper || !best_move.is_none() || is_mate_score(best_score))) {\n"),
}
for name, new in VARIANTS.items():
    root = Path("F:/opus_scratch/r5/r5d") / name
    root.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(["git", "-C", WT, "-c", "core.autocrlf=false", "archive", "HEAD", "src", "include"],
                             check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
    p = root / "src/search/alphabeta.inc"
    s = p.read_bytes().decode()
    assert s.count(STORE) == 1, name
    p.write_bytes(s.replace(STORE, new).encode())
    print("prepared", name)
sys.exit(0)
