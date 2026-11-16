#!/usr/bin/env bash
# check_19f5.sh -- seat 10's OWN harness (not a copy of seat 19's) for finding 19-F5:
#   "bench is a UCI command on stdin; main ignores argv; `forge bench 13` gives nothing useful".
# Every command below is run from THIS file; raw output goes beside it.
set -u
EXE="$1"
OUT="${2:-.}"
mkdir -p "$OUT"
: > "$OUT/raw_all.txt"
stamp() { date -u; }

# P1 + P3: bench as an ARGV (main ignores argv) -- must print no bench line
A1="$OUT/raw_a1.txt"; : > "$A1"
A2="$OUT/raw_a2.txt"; : > "$A2"
B1="$OUT/raw_b1.txt"; : > "$B1"
B2="$OUT/raw_b2.txt"; : > "$B2"
{
  echo "===== A1: bench 13 as ARGUMENT (no stdin)"
  echo "\$ $EXE bench 13 </dev/null"
  stamp
} >> "$OUT/raw_all.txt"
t0=$(date +%s.%N)
timeout 20 "$EXE" bench 13 < /dev/null > "$A1" 2>&1; cat "$A1" >> "$OUT/raw_all.txt"
rc=$?
t1=$(date +%s.%N)
{ echo "rc=$rc elapsed=$(python3 -c "print(round($t1-$t0,3))")"; stamp; echo; } >> "$OUT/raw_all.txt"

{
  echo "===== A2: quit on stdin, bench 13 as ARGUMENT"
  echo "\$ printf 'quit\\n' | $EXE bench 13"
  stamp
} >> "$OUT/raw_all.txt"
t0=$(date +%s.%N)
printf 'quit\n' | timeout 20 "$EXE" bench 13 > "$A2" 2>&1; cat "$A2" >> "$OUT/raw_all.txt"
rc=$?
t1=$(date +%s.%N)
{ echo "rc=$rc elapsed=$(python3 -c "print(round($t1-$t0,3))")"; stamp; echo; } >> "$OUT/raw_all.txt"

# P2: bench on stdin
{
  echo "===== B1: bench 13 on STDIN"
  echo "\$ printf 'bench 13\\nquit\\n' | $EXE"
  stamp
} >> "$OUT/raw_all.txt"
t0=$(date +%s.%N)
printf 'bench 13\nquit\n' | timeout 600 "$EXE" > "$B1" 2>&1; cat "$B1" >> "$OUT/raw_all.txt"
rc=$?
t1=$(date +%s.%N)
{ echo "rc=$rc elapsed=$(python3 -c "print(round($t1-$t0,3))")"; stamp; echo; } >> "$OUT/raw_all.txt"

# the same for bench 11 and 16 (the finding is about the mechanism, so check it is not depth-specific)
{
  echo "===== B2: bench 11 and 16 on STDIN"
  echo "\$ printf 'bench 11\\nbench 16\\nquit\\n' | $EXE"
  stamp
} >> "$OUT/raw_all.txt"
printf 'bench 11\nbench 16\nquit\n' | timeout 600 "$EXE" > "$B2" 2>&1; cat "$B2" >> "$OUT/raw_all.txt"
{ echo "rc=$?"; stamp; echo; } >> "$OUT/raw_all.txt"

# P4: source line numbers
{
  echo "===== C1: the source lines seat 19 cites"
  echo "\$ grep -n 'bench' src/uci.cpp"
  stamp
} >> "$OUT/raw_all.txt"
grep -n 'bench' /agent/repos/base/forge-combo29/src/uci.cpp >> "$OUT/raw_all.txt" 2>&1
{
  echo
  echo "===== C2: main() in uci.cpp"
  echo "\$ grep -n 'int main' src/uci.cpp"
  stamp
} >> "$OUT/raw_all.txt"
grep -n 'int main' /agent/repos/base/forge-combo29/src/uci.cpp >> "$OUT/raw_all.txt" 2>&1
{
  echo
  echo "===== C3: main's body (does it touch argv at all?)"
  echo "\$ sed -n '/int main/,\$p' /agent/repos/base/forge-combo29/src/uci.cpp"
  stamp
} >> "$OUT/raw_all.txt"
sed -n '/int main/,$p' /agent/repos/base/forge-combo29/src/uci.cpp >> "$OUT/raw_all.txt" 2>&1

{
  echo "===== VERDICT (computed from raw_all.txt only, written to verdict.txt)"
  echo "P1: bench lines in the ARGV-mode part (A1+A2) of raw_all.txt, want 0:"
  awk '/===== B1:/{exit} {print}' "$OUT/raw_all.txt" | grep -c 'bench depth' || true
  echo "P1b: bench lines printed by A1 alone (raw_a1.txt), want 0:"
  grep -c 'bench depth' "$OUT/raw_a1.txt" || true
  echo "P2: the stdin-mode bench 13 line, want: info string bench depth 13 nodes 862329"
  grep 'bench depth 13' "$OUT/raw_b1.txt" || echo "  (none)"
  echo "P2b: stdin-mode bench 11 / 16 lines:"
  grep -E 'bench depth (11|16)' "$OUT/raw_b2.txt" || echo "  (none)"
  echo "P3: A2 (quit on stdin, bench as ARGV) printed nodes, want 0:"
  grep -c 'bench depth' "$OUT/raw_a2.txt" || true
  echo "P4: the cited source lines:"
  grep -n 'command == "bench"' /agent/repos/base/forge-combo29/src/uci.cpp
  grep -n 'int main' /agent/repos/base/forge-combo29/src/uci.cpp
} > "$OUT/verdict.txt"
cat "$OUT/verdict.txt"

echo "--- raw_all.txt written to $OUT"
