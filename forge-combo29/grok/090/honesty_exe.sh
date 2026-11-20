#!/usr/bin/env bash
# Honesty check. Fresh process per line. No setoption.
# usage: honesty_exe.sh EXE PREFIX
set -u
EXE=$1
PREFIX=$2
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
OUT="$REPO/forge-combo29/grok/$S"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/${PREFIX}_${name}.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDNAME"
    echo "id_name_source=separate uci/quit of the same exe path, not this process"
    echo "options_sent=none"
    echo "command=$cmd"
  } > "$OUT/${PREFIX}_${name}.meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
python3 - "$OUT" "$PREFIX" << 'PY'
import pathlib, sys
out = pathlib.Path(sys.argv[1])
prefix = sys.argv[2]
expect = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
ok = True
for name, want in expect.items():
    text = (out / f"{prefix}_{name}.txt").read_text()
    found = None
    for line in text.splitlines():
        parts = line.split()
        if "nodes" in parts:
            i = parts.index("nodes")
            if i + 1 < len(parts) and parts[i + 1].isdigit():
                found = int(parts[i + 1])
    flag = "ok" if found == want else "MISMATCH"
    if found != want:
        ok = False
    print(f"{prefix}_{name} nodes {found} expected {want} {flag}")
print("all_match", "yes" if ok else "no")
sys.exit(0 if ok else 1)
PY
