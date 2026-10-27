#!/usr/bin/env bash
# S29 speed stack: PC evidence driver (Git Bash, MSYS2 ucrt64 g++ 15.2). Writes logs to <out_dir>, builds to
# /f/opus_scratch/build/s29_pc (never on D:). Steps:
#   1. PC lock recipe (b/tools/build_pc.sh): default build and -DFORGE_SPEEDSTACK=1 build; sha256 + FMA count
#   2. default exe vs lock exe: differing bytes (cmp -l) and whole-binary disassembly
#   3. identity: uci_check.py --full (bench d11/13/16/20/22, perft5 startpos + kiwipete) for default and stack-on
#   4. UCI option list: stack-on exe vs lock exe
#   5. codegen: codegen_compare.sh lock vs stack-on; prefetch instructions in Worker::search
#   6. ctest of the CMake builds (s29_cm_off, s29_cm_on) + known-failure check
# usage: run_s29_evidence.sh <out_dir>
set -uo pipefail
OUT=$1
mkdir -p "$OUT"
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
JOB="$ROOT/opus_round1/sol_S29"
TOOLS=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
LOCK=/d/grok-pc-data/dwqww/.claude/worktrees/b/base/forge_h256_s198.exe
B=/f/opus_scratch/build/s29_pc
mkdir -p "$B"
export PATH=/c/msys64/ucrt64/bin:$PATH
{
  echo "# step 1: PC recipe builds ($(date '+%Y-%m-%d %H:%M:%S') PC clock); machine exclusive: no"
  nice -n 19 bash "$TOOLS/build_pc.sh" "$ROOT" "$B/forge_s29_default.exe"
  nice -n 19 bash "$TOOLS/build_pc.sh" "$ROOT" "$B/forge_s29_on.exe" -DFORGE_SPEEDSTACK=1
  echo "lock exe sha256 $(sha256sum "$LOCK" | cut -d' ' -f1)"
} > "$OUT/step1_builds.log" 2>&1
{
  echo "# step 2: default exe vs lock exe"
  echo "differing bytes (cmp -l | wc -l): $(cmp -l "$LOCK" "$B/forge_s29_default.exe" | wc -l)"
  cmp -l "$LOCK" "$B/forge_s29_default.exe" | head -20
  a=$(objdump -d "$LOCK" | tail -n +3 | sha256sum); b=$(objdump -d "$B/forge_s29_default.exe" | tail -n +3 | sha256sum)
  echo "whole-binary disassembly vs lock: $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
} > "$OUT/step2_default_vs_lock.log" 2>&1
for t in default on; do
  { echo "# step 3: identity, $t build ($B/forge_s29_$t.exe)"; nice -n 19 python "$ROOT/opus_round1/ci/uci_check.py" "$B/forge_s29_$t.exe" --full; } > "$OUT/step3_identity_$t.log" 2>&1
done
{
  echo "# step 4: UCI option list, stack-on exe vs lock exe"
  printf 'uci\nquit\n' | "$LOCK" | tr -d '\r' | grep -E '^(option|id) ' > "$OUT/uci_options_lock.txt"
  printf 'uci\nquit\n' | "$B/forge_s29_on.exe" | tr -d '\r' | grep -E '^(option|id) ' > "$OUT/uci_options_on.txt"
  if cmp -s "$OUT/uci_options_lock.txt" "$OUT/uci_options_on.txt"; then echo "IDENTICAL ($(wc -l < "$OUT/uci_options_on.txt") lines)"; else echo DIFFERENT; diff "$OUT/uci_options_lock.txt" "$OUT/uci_options_on.txt"; fi
} > "$OUT/step4_uci_options.log" 2>&1
{
  echo "# step 5: codegen, lock exe vs stack-on exe (codegen_compare.sh), and prefetch instructions in Worker::search"
  bash "$JOB/codegen_compare.sh" "$LOCK" "$B/forge_s29_on.exe"
  for exe in "$LOCK" "$B/forge_s29_on.exe"; do
    n=$(objdump -d -C --no-show-raw-insn "$exe" | awk '/^[0-9a-f]+ <forge::Worker::search\(forge::Board&/{f=1;next} /^[0-9a-f]+ </{f=0} f' | grep -c prefetch)
    echo "$(basename "$exe"): prefetch instructions in Worker::search(Board&, ...) = $n"
  done
} > "$OUT/step5_codegen.log" 2>&1
for t in off on; do
  { echo "# step 6: ctest, CMake build s29_cm_$t"; (cd "/f/opus_scratch/build/s29_cm_$t" && nice -n 19 ctest --output-on-failure --timeout 900 -j1) 2>&1 | tee "$OUT/ctest_$t.raw"
    python "$ROOT/opus_round1/ci/check_known_failures.py" "$OUT/ctest_$t.raw"; } > "$OUT/step6_ctest_$t.log" 2>&1
done
grep -h -E "ALL OK|FAIL|IDENTICAL|DIFFERENT|differing bytes|FMA|prefetch instructions|KNOWN-FAILURE" "$OUT"/step*.log
