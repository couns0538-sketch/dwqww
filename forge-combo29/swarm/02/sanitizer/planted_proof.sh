#!/usr/bin/env bash
# S02: the runner that must COUNT a planted fault. Two builds, built the same way
# (-fsanitize=address,undefined), run through this same function:
#   clean   = the real engine at 6b98f217, given the same input lines
#   fault   = a scratch copy with a heap over-read (command "sanprobe") and a signed overflow ("ubprobe")
# usage: planted_proof.sh <clean_exe> <fault_exe> <outdir>
set -u
CLEAN="${1:?clean exe}"
FAULT="${2:?fault exe}"
OUT="${3:-.}"
mkdir -p "$OUT"

count_lines() { # file -> number of sanitizer report lines
  grep -c -E 'ERROR: AddressSanitizer|runtime error:|ERROR: LeakSanitizer|SUMMARY: (AddressSanitizer|UndefinedBehaviorSanitizer)' "$1"
}

run_case() { # tag, exe, inputfile
  local tag="$1" exe="$2" in="$3"
  local out="$OUT/$tag.out"
  env -u ASAN_OPTIONS -u UBSAN_OPTIONS -u TSAN_OPTIONS \
      "$exe" < "$in" > "$out" 2>&1
  local rc=$?
  {
    echo "case $tag"
    echo "exe $exe"
    echo "sha256 $(sha256sum "$exe" | cut -d' ' -f1)"
    echo "nm __asan_ $(nm -C "$exe" | grep -c __asan_)  __ubsan_ $(nm -C "$exe" | grep -c __ubsan_)"
    echo "exit $rc"
    echo "sanitizer_lines $(count_lines "$out")"
    echo "date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } >> "$OUT/meta.txt"
  echo "[$tag] exit=$rc sanitizer_lines=$(count_lines "$out")"
}

: > "$OUT/meta.txt"
# the input: a normal session, then the two planted-fault triggers (the clean build just ignores them
# as unknown commands — that is the point: same input, same runner, only the fault build must be caught)
cat > "$OUT/probe.in" <<'IN'
uci
isready
position startpos
isready
go depth 2
sanprobe
ubprobe
isready
quit
IN

run_case clean "$CLEAN" "$OUT/probe.in"
run_case fault "$FAULT" "$OUT/probe.in"

# a control: the fault build on the SAME input with the probes removed must report nothing
grep -v -E '^(sanprobe|ubprobe)$' "$OUT/probe.in" > "$OUT/probe_control.in"
run_case fault_control "$FAULT" "$OUT/probe_control.in"
grep -E 'ERROR: AddressSanitizer|runtime error:' "$OUT/fault.out" | head -4 > "$OUT/fault_first_lines.txt"
grep -E 'ERROR: AddressSanitizer|runtime error:' "$OUT/fault_control.out" | head -4 >> "$OUT/fault_first_lines.txt"
echo "--- first sanitizer lines (fault run, then control run):"
cat "$OUT/fault_first_lines.txt"
