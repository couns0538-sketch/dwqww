#!/usr/bin/env bash
# CorrHistPlus SMP evidence on Linux (used by .github/workflows/opus-c2-smp.yml).
#   release : box flags (g++-14, x86-64-v3, no FMA contraction)
#   asan    : -DFORGE_ENABLE_SANITIZERS=ON (ASan + UBSan), recover off
#   tsan    : -fsanitize=thread
# Builds the engine only, then runs opus_round1/C2/smp_smoke.py with Threads 1 (two processes per
# option value: node counts must match) and Threads 8, for CorrHistPlus = 0, 1, 2, 4, 7. Each run has
# its own time limit and is announced before it starts. Any sanitizer report fails the job.
# usage: opus_round1/C2/ci_smp.sh <release|asan|tsan> [out_dir]
set -uo pipefail
MODE=$1
OUT=${2:-ci_smp_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
BD="$OUT/build_$MODE"
LOGDIR="$OUT/sanitizer_logs_$MODE"
mkdir -p "$LOGDIR"
case "$MODE" in
  release) EXTRA=(-DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=$BASE_FLAGS"); DEPTH1=11; DEPTH8=12 ;;
  asan) EXTRA=(-DCMAKE_BUILD_TYPE=RelWithDebInfo -DFORGE_ENABLE_SANITIZERS=ON "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fno-sanitize-recover=all")
        export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
        export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1"; DEPTH1=9; DEPTH8=9 ;;
  tsan) EXTRA=(-DCMAKE_BUILD_TYPE=RelWithDebInfo "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fsanitize=thread -fno-omit-frame-pointer"
               "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread")
        export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:second_deadlock_stack=1"; DEPTH1=8; DEPTH8=8 ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_CXX_COMPILER="$CXX" "${EXTRA[@]}" > "$OUT/configure_$MODE.log" 2>&1 || { cat "$OUT/configure_$MODE.log"; exit 1; }
cmake --build "$BD" --target forge -j"$(nproc)" > "$OUT/build_$MODE.log" 2>&1 || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
status=0
run() { # label limit_s args...
  local label=$1 limit=$2; shift 2
  echo "== $MODE: $label (limit ${limit}s)" | tee -a "$OUT/smp_$MODE.log"
  timeout --kill-after=15 "$limit" python3 "$ROOT/opus_round1/C2/smp_smoke.py" "$BD/forge" "$@" 2>&1 | tee -a "$OUT/smp_$MODE.log"
  local rc=${PIPESTATUS[0]}
  if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then echo "== TIMEOUT: $label" | tee -a "$OUT/smp_$MODE.log"; status=1
  elif [ "$rc" -ne 0 ]; then echo "== FAIL: $label exit $rc" | tee -a "$OUT/smp_$MODE.log"; status=1; fi
}
run "Threads 1, depth $DEPTH1, CorrHistPlus 0/1/2/4/7, determinism" 1200 --threads 1 --depth "$DEPTH1"
run "Threads 8, depth $DEPTH8, CorrHistPlus 0/1/2/4/7" 1200 --threads 8 --depth "$DEPTH8"
if [ "$MODE" = release ]; then
  # The bench pins recorded on the Windows PC build must be reproduced by the Linux build.
  echo "== release: bench pins d11/13/16/20/22 vs the PC pins (limit 1500s)" | tee -a "$OUT/smp_$MODE.log"
  timeout --kill-after=15 1500 python3 "$ROOT/opus_round1/C2/bench_pins.py" "$BD/forge" \
    --line OFF: --line G-B1:CorrHistPlus=1 --line G-B2:CorrHistPlus=2 --line nonpawn:CorrHistPlus=4 --line all:CorrHistPlus=7 \
    --expect OFF=312866,862329,3024920,12389307,34048354 \
    --expect G-B1=318363,915778,2347193,9687762,19269711 \
    --expect G-B2=296553,824640,2914749,13945117,40489211 \
    --expect nonpawn=340927,734347,2794671,12132495,37005405 \
    --expect all=317529,866764,2715911,8754177,26756688 2>&1 | tee -a "$OUT/smp_$MODE.log"
  [ "${PIPESTATUS[0]}" -eq 0 ] || { echo "== FAIL: bench pins" | tee -a "$OUT/smp_$MODE.log"; status=1; }
fi
if [ -n "$(find "$LOGDIR" -type f -size +0 2>/dev/null)" ]; then
  echo "sanitizer reports found:"; cat "$LOGDIR"/* | head -200; status=1
else
  echo "sanitizer reports: 0 ($MODE)" | tee -a "$OUT/smp_$MODE.log"
fi
echo "ci_smp $MODE status=$status" | tee -a "$OUT/smp_$MODE.log"
exit $status
