#!/usr/bin/env bash
# Honesty check. One fresh process per line. No setoption.
# usage: honesty_run.sh TAG EXE
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
TAG="${1:?tag}"
EXE="${2:?exe}"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk -F'id name ' '/^id name /{print substr($0,9); exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  local raw="$DIR/${TAG}_${name}.txt"
  local meta="$DIR/${TAG}_${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDNAME"
    echo "options_sent=none"
    echo "command=$cmd"
    echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
python3 - "$DIR" "$TAG" << 'PY'
import sys
d, tag = sys.argv[1], sys.argv[2]
def nodes_bench(path):
    line = open(path).read().strip().splitlines()[-1]
    parts = line.split()
    i = parts.index("nodes")
    return int(parts[i + 1])
def nodes_perft(path):
    for line in open(path):
        if line.startswith("nodes "):
            return int(line.split()[1])
    return -1
expect = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
ok = True
lines = []
for name, exp in expect.items():
    path = f"{d}/{tag}_{name}.txt"
    got = nodes_perft(path) if name == "perft5" else nodes_bench(path)
    flag = "OK" if got == exp else "MISS"
    if flag != "OK":
        ok = False
    lines.append(f"{name} got={got} expect={exp} {flag}")
lines.append(f"HONESTY_{tag} {'PASS' if ok else 'FAIL'}")
text = "\n".join(lines) + "\n"
open(f"{d}/HONESTY_{tag}.txt", "w").write(text)
print(text, end="")
sys.exit(0 if ok else 1)
PY
