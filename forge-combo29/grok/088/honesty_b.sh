#!/usr/bin/env bash
# Honesty check for exe B. One fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="${1:-/tmp/forge-b/forge}"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk -F'id name ' '/^id name /{print substr($0,9); exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  local raw="$DIR/${name}.txt"
  local meta="$DIR/${name}.meta"
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
run_one honesty_b_bench11 "bench 11"
run_one honesty_b_bench13 "bench 13"
run_one honesty_b_bench16 "bench 16"
run_one honesty_b_perft5 "go perft 5"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$IDNAME"
  echo "bench11=$(grep -E 'nodes ' "$DIR/honesty_b_bench11.txt" | tail -n 1)"
  echo "bench13=$(grep -E 'nodes ' "$DIR/honesty_b_bench13.txt" | tail -n 1)"
  echo "bench16=$(grep -E 'nodes ' "$DIR/honesty_b_bench16.txt" | tail -n 1)"
  echo "perft5=$(grep -E '^nodes ' "$DIR/honesty_b_perft5.txt" | tail -n 1)"
  python3 - "$DIR" << 'PY'
import sys
d = sys.argv[1]
def nodes_bench(path):
    line = open(path).read().strip().splitlines()[-1]
    parts = line.split()
    i = parts.index("nodes")
    return int(parts[i+1]), line
def nodes_perft(path):
    for line in open(path):
        if line.startswith("nodes "):
            return int(line.split()[1]), line.strip()
    return -1, ""
expect = {
    "honesty_b_bench11.txt": 312866,
    "honesty_b_bench13.txt": 862329,
    "honesty_b_bench16.txt": 3024920,
}
ok = True
for name, exp in expect.items():
    got, line = nodes_bench(f"{d}/{name}")
    flag = "OK" if got == exp else "MISS"
    if flag != "OK":
        ok = False
    print(f"{name} got={got} expect={exp} {flag}")
got, line = nodes_perft(f"{d}/honesty_b_perft5.txt")
flag = "OK" if got == 4865609 else "MISS"
if flag != "OK":
    ok = False
print(f"honesty_b_perft5.txt got={got} expect=4865609 {flag}")
print("HONESTY_B", "PASS" if ok else "FAIL")
PY
} > "$DIR/HONESTY_B.txt"
cat "$DIR/HONESTY_B.txt"
