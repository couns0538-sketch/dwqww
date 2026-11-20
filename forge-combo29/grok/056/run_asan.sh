#!/usr/bin/env bash
# Sanitizer proof. Same depth_sum.py runner for the clean search and the
# scratch engine that reads one past a heap array on one FEN.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT=forge-combo29/grok/$S
export ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=0:symbolize=1
export UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1:print_stacktrace=1
head -n 100 /tmp/G.epd > "$OUT/G100.epd"
nm -C /tmp/forge-asan/forge | grep -c __asan_ > "$OUT/asan_nm_count.txt"
python3 "$OUT/depth_sum.py" --exe /tmp/forge-asan/forge --fens "$OUT/G100.epd" --depth 10 \
  --prefix "$OUT/asan_G100_d10" \
  --setoption IdeaS34=true \
  --setoption IdeaS34_EaseZero=2 \
  --setoption IdeaS34_EaseMid=1 \
  --setoption IdeaS34_Couple=2 \
  --setoption IdeaS34_Full=4 \
  --setoption IdeaS34_NoTt=2
{
  echo "asan_symbol_count=$(cat "$OUT/asan_nm_count.txt")"
  echo "sanitizer_lines=$(grep -c -E 'AddressSanitizer|UndefinedBehaviorSanitizer|runtime error:' "$OUT/asan_G100_d10.log" || true)"
} >> "$OUT/asan_G100_d10.meta"
echo '8/8/8/8/8/8/8/K6k w - - 0 1' > "$OUT/asan_probe.fen"
set +e
python3 "$OUT/depth_sum.py" --exe /tmp/forge-asan-bad/forge --fens "$OUT/asan_probe.fen" --depth 10 \
  --prefix "$OUT/asan_probe" \
  --setoption IdeaS34=true \
  --setoption IdeaS34_EaseZero=2 \
  --setoption IdeaS34_EaseMid=1 \
  --setoption IdeaS34_Couple=2 \
  --setoption IdeaS34_Full=4 \
  --setoption IdeaS34_NoTt=2
echo "probe_exit=$?"
set -e
{
  echo "asan_symbol_count=$(nm -C /tmp/forge-asan-bad/forge | grep -c __asan_)"
  echo "sanitizer_lines=$(grep -c -E 'AddressSanitizer|UndefinedBehaviorSanitizer|runtime error:' "$OUT/asan_probe.log" || true)"
} >> "$OUT/asan_probe.meta"
echo "---- probe sanitizer lines ----"
grep -n -E 'AddressSanitizer|UndefinedBehaviorSanitizer|runtime error:' "$OUT/asan_probe.log" | head -20
echo "---- clean sanitizer lines ----"
grep -c -E 'AddressSanitizer|UndefinedBehaviorSanitizer|runtime error:' "$OUT/asan_G100_d10.log" || true
