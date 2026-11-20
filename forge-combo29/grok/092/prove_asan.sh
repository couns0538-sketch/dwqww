#!/usr/bin/env bash
# Sanitizer proofs for seat 092. The real exe and the scratch exe are built the same way.
set -u
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
REAL=/tmp/forge-asan/forge
BUG=/tmp/forge-asan-bug/forge
cd "$DIR"
echo "real_asan_symbols $(nm -C "$REAL" | grep -c __asan_)" | tee asan_nm.txt
echo "bug_asan_symbols $(nm -C "$BUG" | grep -c __asan_)" | tee -a asan_nm.txt
python3 "$DIR/harness.py" search "$REAL" "$DIR/asan_G_d10.txt" /tmp/pos/set_G.epd 10 100 true
python3 "$DIR/harness.py" search "$BUG" "$DIR/asan_bug.txt" "$DIR/asan_bug.fen" 1 - true || true
echo "real_sanitizer_lines $(grep -c -E 'AddressSanitizer|runtime error:' asan_G_d10.txt.raw || true)"
echo "bug_sanitizer_lines $(grep -c -E 'AddressSanitizer|runtime error:' asan_bug.txt.raw || true)"
grep -n -E 'AddressSanitizer|runtime error:' asan_bug.txt.raw | head -n 5
