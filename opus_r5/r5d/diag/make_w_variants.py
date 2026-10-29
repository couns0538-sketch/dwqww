"""R5D candidate fixes (scratch only). W2: helpers do not store TT entries at plies 1-2 (root children and
grandchildren); W3: helpers do not store at ply 1. Every store call in the main search, qsearch and ProbCut."""
import subprocess
from pathlib import Path

WT = "D:/grok-pc-data/dwqww/.claude/worktrees/opus-r5d-matefix"
for name, max_ply in (("exp_w2", 2), ("exp_w3", 1)):
    root = Path("F:/opus_scratch/r5/r5d") / name
    root.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(["git", "-C", WT, "-c", "core.autocrlf=false", "archive", "HEAD", "src", "include"],
                             check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
    n = 0
    for rel in ("src/search/alphabeta.inc", "src/search/qsearch.inc"):
        p = root / rel
        s = p.read_bytes().decode()
        n += s.count("shared_.tt.store(")
        s = s.replace("shared_.tt.store(", f"if (is_main() || ply > {max_ply}) shared_.tt.store(")
        p.write_bytes(s.encode())
    print("prepared", name, "sites", n)
