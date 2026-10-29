"""R5D experiment F6 (scratch only): helpers write nothing to the TT (main search, qsearch, ProbCut, claim stores)."""
import subprocess
from pathlib import Path

WT = "D:/grok-pc-data/dwqww/.claude/worktrees/opus-r5d-matefix"
root = Path("F:/opus_scratch/r5/r5d/exp_f6")
root.mkdir(parents=True, exist_ok=True)
archive = subprocess.run(["git", "-C", WT, "-c", "core.autocrlf=false", "archive", "HEAD", "src", "include"],
                         check=True, capture_output=True).stdout
subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
count = 0
for rel in ("src/search/alphabeta.inc", "src/search/qsearch.inc"):
    p = root / rel
    s = p.read_bytes().decode()
    n = s.count("shared_.tt.store(")
    s = s.replace("shared_.tt.store(", "if (is_main()) shared_.tt.store(")
    count += n
    p.write_bytes(s.encode())
print("helper stores disabled at", count, "call sites")
