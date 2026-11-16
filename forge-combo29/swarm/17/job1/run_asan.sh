#!/usr/bin/env bash
# seat 17 area 7 job 1: run N searches under the ASan+UBSan build and report every sanitizer line.
# usage: run_asan.sh <exe> <epdfile> <first> <count> <depth> <outdir>
set -u
EXE="$1"; EPD="$2"; FIRST="$3"; COUNT="$4"; DEPTH="$5"; OUT="$6"
mkdir -p "$OUT"
: > "$OUT/sanitizer_lines.txt"
: > "$OUT/search_log.txt"
: > "$OUT/bestmoves.txt"
{
  echo "exe: $EXE"
  echo "sha256: $(sha256sum "$EXE" | cut -d' ' -f1)"
  echo "sanitizer symbols: $(nm -C "$EXE" | grep -cE '__asan_|__ubsan_')"
  echo "options sent: none"
  echo "position epd: $EPD first $FIRST count $COUNT depth $DEPTH"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/run.meta"
end=$((FIRST + COUNT - 1))
n=0
for i in $(seq "$FIRST" "$end"); do
  fen=$(sed -n "${i}p" "$EPD" | sed 's/ *;.*$//')
  [ -z "$fen" ] && continue
  n=$((n+1))
  printf 'uci\nisready\nposition fen %s\ngo depth %s\nquit\n' "$fen" "$DEPTH" \
    | ASAN_OPTIONS=detect_leaks=0:abort_on_error=0 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=0 \
      timeout 120 "$EXE" > "$OUT/one_$i.log" 2>&1
  rc=$?
  bm=$(grep -m1 '^bestmove' "$OUT/one_$i.log" | awk '{print $2}')
  echo "$i|$rc|$fen|$bm" >> "$OUT/bestmoves.txt"
  if [ "$rc" -ne 0 ]; then echo "EXIT $rc on line $i: $fen" >> "$OUT/sanitizer_lines.txt"; fi
  grep -E "ERROR: AddressSanitizer|runtime error:|SUMMARY: |AddressSanitizer:|UndefinedBehaviorSanitizer" "$OUT/one_$i.log" >> "$OUT/sanitizer_lines.txt"
  cat "$OUT/one_$i.log" >> "$OUT/search_log.txt"
done
echo "searches: $n" >> "$OUT/run.meta"
echo "sanitizer_lines: $(wc -l < "$OUT/sanitizer_lines.txt")" >> "$OUT/run.meta"
date -u >> "$OUT/run.meta"
cat "$OUT/run.meta"
