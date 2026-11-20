#!/usr/bin/env bash
# Honesty check. One fresh process per line. No setoption.
# usage: honesty_exe.sh EXE TAG OUTDIR
set -u
EXE=$1
TAG=$2
OUT=$3
mkdir -p "$OUT"
sha=$(sha256sum "$EXE" | awk '{print $1}')
idname=$(printf 'uci\nquit\n' | "$EXE" | awk -F'id name ' '/^id name /{print $2; exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  local raw="$OUT/honesty_${TAG}_${name}.txt"
  local meta="$OUT/honesty_${TAG}_${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe=$EXE"
    echo "sha256=$sha"
    echo "id_name=$idname"
    echo "options_sent=none"
    echo "command=$cmd"
  } > "$meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
python3 - "$OUT" "$TAG" << 'PY'
import sys
from pathlib import Path
out = Path(sys.argv[1])
tag = sys.argv[2]
expect = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
lines = []
ok = True
for name, want in expect.items():
    text = (out / f"honesty_{tag}_{name}.txt").read_text()
    got = None
    for line in text.splitlines():
        if "nodes" in line.split():
            parts = line.replace(":", " ").split()
            got = int(parts[parts.index("nodes") + 1])
    match = got == want
    ok = ok and match
    lines.append(f"{name} nodes {got} expect {want} {'OK' if match else 'MISMATCH'}")
text = "\n".join(lines) + ("\nHONESTY PASS\n" if ok else "\nHONESTY FAIL\n")
(out / f"HONESTY_{tag}.txt").write_text(text)
print(text, end="")
PY
