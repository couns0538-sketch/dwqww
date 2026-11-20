#!/usr/bin/env bash
# AddressSanitizer + UndefinedBehaviorSanitizer proof on exe P, switch true.
set -euo pipefail
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build-asan/forge
SHA=$(sha256sum "$EXE" | awk '{print $1}')
nm -C "$EXE" | grep -c __asan_ > "$DIR/asan_nm_count.txt"
echo "sha256=$SHA" >> "$DIR/asan_nm_count.txt"
echo "exe=$EXE" >> "$DIR/asan_nm_count.txt"
cat "$DIR/asan_nm_count.txt"
head -n 100 /tmp/kimi5/set_G.epd > "$DIR/g100.epd"
python3 "$DIR/harness_depth.py" "$EXE" "$DIR/g100.epd" 10 asan_g100 "$DIR" IdeaK9 true IdeaK9_Cap 3
grep -c -E 'AddressSanitizer|UndefinedBehaviorSanitizer|runtime error:' "$DIR/asan_g100.raw.txt" > "$DIR/asan_g100_sanitizer_lines.txt" || true
echo "sanitizer_lines=$(cat "$DIR/asan_g100_sanitizer_lines.txt")"
