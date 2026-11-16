#!/usr/bin/env bash
# honesty.sh EXE OUTDIR : the honesty check of the brief. One fresh process per line, raw output kept.
set -u
EXE="${1:?exe}"
OUT="${2:?outdir}"
mkdir -p "$OUT"
EXE_ABS="$(readlink -f "$EXE")"
{
  echo "exe $EXE_ABS"
  sha256sum "$EXE_ABS"
  printf 'uci\nquit\n' | "$EXE_ABS" 2>&1 | tr -d '\r' > "$OUT/uci_answer.txt"
  grep -c . "$OUT/uci_answer.txt"
  grep -E '^id name' "$OUT/uci_answer.txt"
} > "$OUT/honesty.meta" 2>&1
for d in 11 13 16; do
  printf 'bench %s\nquit\n' "$d" | "$EXE_ABS" 2>&1 | tr -d '\r' > "$OUT/bench_$d.raw.txt"
done
printf 'go perft 5\nquit\n' | "$EXE_ABS" 2>&1 | tr -d '\r' > "$OUT/perft5.raw.txt"

# parse: exact numbers out of the raw files
{
  echo "# parsed from the raw files above"
  for d in 11 13 16; do
    n=$(grep -o 'bench depth [0-9]* nodes [0-9]*' "$OUT/bench_$d.raw.txt" | sed 's/.*nodes //')
    echo "bench $d nodes ${n:-MISSING}"
  done
  n=$(grep -E '^nodes [0-9]+$' "$OUT/perft5.raw.txt" | sed 's/nodes //')
  echo "perft 5 nodes ${n:-MISSING}"
} > "$OUT/honesty_numbers.txt"
date -u
cat "$OUT/honesty_numbers.txt"
