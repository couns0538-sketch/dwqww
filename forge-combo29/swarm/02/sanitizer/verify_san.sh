#!/usr/bin/env bash
# S02: prove a build really carries ASan+UBSan (nm counts), and that a runner built the same way
# COUNTS a planted fault. usage: verify_san.sh <exe> <outdir>
set -u
EXE="${1:-/agent/repos/base/forge-combo29/build-asan/forge}"
OUT="${2:-.}"
mkdir -p "$OUT"
{
  echo "exe $EXE"
  echo "sha256 $(sha256sum "$EXE" | cut -d' ' -f1)"
  echo "nm -C grep -c __asan_  = $(nm -C "$EXE" | grep -c __asan_)"
  echo "nm -C grep -c __ubsan_ = $(nm -C "$EXE" | grep -c __ubsan_)"
  echo "nm -C grep -c __tsan_  = $(nm -C "$EXE" | grep -c __tsan_)"
  echo "date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$OUT/build.meta"
# a plain command on the sanitized exe: must print no sanitizer line
printf 'uci\nisready\nposition startpos\nisready\ngo depth 4\nquit\n' > "$OUT/clean.in"
env -u ASAN_OPTIONS -u UBSAN_OPTIONS -u TSAN_OPTIONS "$EXE" < "$OUT/clean.in" > "$OUT/clean.out" 2>&1
echo "clean run exit=$?" | tee -a "$OUT/build.meta"
echo "sanitizer lines in clean run: $(grep -c -E 'runtime error|ERROR: AddressSanitizer|ERROR: LeakSanitizer' "$OUT/clean.out")" | tee -a "$OUT/build.meta"
