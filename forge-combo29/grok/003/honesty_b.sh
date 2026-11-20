#!/usr/bin/env bash
# Fresh process per line. No setoption. Raw output stays beside this script.
set -u
EXE=/agent/repos/base/forge-combo29/build/forge
OUT="$(cd "$(dirname "$0")" && pwd)"
cd "$OUT"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | sed -n 's/^id name //p' | head -1)

run_one() {
  local name="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/${name}.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$ID"
    echo "command=$cmd"
    echo "options=none"
  } > "$OUT/${name}.meta"
}

run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"

{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$ID"
  echo "bench11=$(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$OUT/bench11.txt" | head -1)"
  echo "bench13=$(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$OUT/bench13.txt" | head -1)"
  echo "bench16=$(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$OUT/bench16.txt" | head -1)"
  echo "perft5=$(grep -E '^nodes [0-9]+$' "$OUT/perft5.txt" | awk '{print $2}' | tail -1)"
  echo "expect_bench11=312866"
  echo "expect_bench13=862329"
  echo "expect_bench16=3024920"
  echo "expect_perft5=4865609"
} > "$OUT/HONESTY_B.txt"

python3 - "$OUT/HONESTY_B.txt" <<'PY'
import sys
text = open(sys.argv[1], encoding="utf-8").read().splitlines()
got = {}
for line in text:
    if "=" in line:
        k, v = line.split("=", 1)
        got[k] = v
pairs = [
    ("bench11", "expect_bench11"),
    ("bench13", "expect_bench13"),
    ("bench16", "expect_bench16"),
    ("perft5", "expect_perft5"),
]
ok = all(got.get(a) == got.get(b) and got.get(a) not in (None, "") for a, b in pairs)
print("HONESTY_B", "PASS" if ok else "FAIL")
for a, b in pairs:
    print(f"{a} {got.get(a)} expect {got.get(b)}")
sys.exit(0 if ok else 1)
PY
