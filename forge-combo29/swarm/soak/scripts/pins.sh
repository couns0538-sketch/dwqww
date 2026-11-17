#!/usr/bin/env bash
# Four honesty pins. A fresh engine process per line, raw output saved.
set -u
EXE="${1:?exe}"
OUT="${2:?outdir}"
mkdir -p "$OUT"
for d in 11 13 16; do
  printf 'uci\nsetoption name OwnBook value false\nposition startpos\nisready\nbench %s\nquit\n' "$d" \
    | "$EXE" > "$OUT/bench_$d.txt" 2>&1
  grep -E '^info string bench depth|^nodes ' "$OUT/bench_$d.txt" | tail -1
done
printf 'uci\nisready\ngo perft 5\nquit\n' | "$EXE" > "$OUT/perft5.txt" 2>&1
grep -E '^nodes ' "$OUT/perft5.txt"
sha256sum "$EXE"
"$EXE" <<< $'uci\nquit' | grep 'id name'
