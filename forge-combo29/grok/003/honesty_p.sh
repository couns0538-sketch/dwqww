#!/usr/bin/env bash
# Fresh process per line on exe P. No setoption.
set -u
EXE=/agent/repos/work/forge-combo29/build/forge
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

run_one p_bench11 "bench 11"
run_one p_bench13 "bench 13"
run_one p_bench16 "bench 16"
run_one p_perft5 "go perft 5"
printf 'uci\nquit\n' | "$EXE" > "$OUT/uci_p.txt"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$ID"
  echo "command=uci"
  echo "options=none"
} > "$OUT/uci_p.meta"

{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$ID"
  echo "bench11=$(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$OUT/p_bench11.txt" | head -1)"
  echo "bench13=$(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$OUT/p_bench13.txt" | head -1)"
  echo "bench16=$(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$OUT/p_bench16.txt" | head -1)"
  echo "perft5=$(grep -E '^nodes [0-9]+$' "$OUT/p_perft5.txt" | awk '{print $2}' | tail -1)"
  echo "expect_bench11=312866"
  echo "expect_bench13=862329"
  echo "expect_bench16=3024920"
  echo "expect_perft5=4865609"
} > "$OUT/HONESTY_P.txt"

python3 - "$OUT/HONESTY_P.txt" "$OUT/uci_p.txt" <<'PY'
import sys
got = {}
for line in open(sys.argv[1], encoding="utf-8"):
    if "=" in line:
        key, value = line.strip().split("=", 1)
        got[key] = value
pairs = [
    ("bench11", "expect_bench11"),
    ("bench13", "expect_bench13"),
    ("bench16", "expect_bench16"),
    ("perft5", "expect_perft5"),
]
ok = all(got.get(a) == got.get(b) and got.get(a) for a, b in pairs)
print("HONESTY_P", "PASS" if ok else "FAIL")
for a, b in pairs:
    print(f"{a} {got.get(a)} expect {got.get(b)}")
text = open(sys.argv[2], encoding="utf-8").read().splitlines()
want = [
    "option name IdeaS38 type check default false",
    "option name IdeaS38_Divisor type spin default 64 min 1 max 4096",
    "option name IdeaS38_Clamp type spin default 1 min 0 max 8",
]
uci_ok = True
for line in want:
    found = line in text
    uci_ok = uci_ok and found
    print(("PASS" if found else "FAIL"), line)
sys.exit(0 if ok and uci_ok else 1)
PY
