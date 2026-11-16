#!/usr/bin/env bash
# sanrun.sh — THE RUNNER used for every sanitizer claim of seat 20. One function, used both on the real
# engine and on the planted-fault copy, so a "0 sanitizer lines" means something.
#
# usage: sanrun.sh <exe> <stdin-file> <label> <outdir>
# prints: label, exit code, sanitizer line count, and the first few sanitizer lines.
set -u
EXE="${1:?exe}"; IN="${2:?stdin}"; LABEL="${3:?label}"; OUT="${4:?outdir}"
mkdir -p "$OUT"
unset ASAN_OPTIONS UBSAN_OPTIONS TSAN_OPTIONS
export ASAN_OPTIONS="detect_leaks=1:abort_on_error=0"
export UBSAN_OPTIONS="print_stacktrace=1:halt_on_error=0"
f="$OUT/${LABEL}.out.txt"
timeout 900 "$EXE" < "$IN" > "$f" 2>&1
rc=$?
n=$(grep -c -E 'AddressSanitizer|runtime error:|LeakSanitizer|UndefinedBehaviorSanitizer|SUMMARY: ' "$f")
{
  echo "label=$LABEL"
  echo "exe=$EXE"
  echo "sha256=$(sha256sum "$EXE" | cut -d' ' -f1)"
  echo "nm___asan_=$(nm -C "$EXE" 2>/dev/null | grep -c __asan_)"
  echo "nm___ubsan_=$(nm -C "$EXE" 2>/dev/null | grep -c __ubsan_)"
  echo "nm___tsan_=$(nm -C "$EXE" 2>/dev/null | grep -c __tsan_)"
  echo "asan_options=$ASAN_OPTIONS"
  echo "ubsan_options=$UBSAN_OPTIONS"
  echo "tsan_options=${TSAN_OPTIONS:-<unset>}"
  echo "stdin=$(cat "$IN" | tr '\n' '|')"
  echo "exit=$rc"
  echo "sanitizer_lines=$n"
} > "$OUT/${LABEL}.meta"
echo "--- $LABEL  exit=$rc  sanitizer_lines=$n"
[ "$n" -gt 0 ] && grep -n -E 'AddressSanitizer|runtime error:|LeakSanitizer|SUMMARY: ' "$f" | head -6
exit 0
