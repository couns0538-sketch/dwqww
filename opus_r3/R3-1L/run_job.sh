#!/usr/bin/env bash
# R3-1L: one GitHub job of the Linux self-play double-check (.github/workflows/opus-r3-sp-linux.yml).
# Builds the exes its configs need (CMake --target forge, g++-14, Ninja, the opus_round1/ci/run_ci.sh recipe of
# the mode), checks bench/perft identity, writes the nets (R3-1_selfplay/make_nets.py) and runs the PC's checker
# (R3-1_selfplay/run_matrix.py + opus_selfplay_check.py, configs_final.json unchanged) on those configs.
#   release : CMake Release, CMAKE_CXX_FLAGS = BASE_FLAGS
#   asan    : RelWithDebInfo, -DFORGE_ENABLE_SANITIZERS=ON (ASan+UBSan), -fno-sanitize-recover=all
#   tsan    : RelWithDebInfo, -fsanitize=thread -fno-omit-frame-pointer
# usage: run_job.sh <job id> <release|asan|tsan> <configs a,b> <games> <seed> <out dir> [max minutes per config]
# Env: TB_DIR (Syzygy 3-4-5 dir, default $HOME/syzygy345), CXX (default g++-14).
# Exit 0 only if every build passes the identity check (and FMA 0 for release), every config ran all its games
# with 0 errors, and no sanitizer report was written.
set -uo pipefail
JOB=$1; MODE=$2; CONFIGS=$3; GAMES=$4; SEED=$5; OUT=$6; MAXMIN=${7:-0}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
HERE="$ROOT/opus_r3/R3-1L"
SP="$ROOT/opus_r3/R3-1_selfplay"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
TB_DIR=${TB_DIR:-$HOME/syzygy345}
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
LOGS="$OUT/logs"; SANLOG="$OUT/sanitizer_logs"
mkdir -p "$LOGS" "$SANLOG" "$OUT/engines" "$OUT/nets" "$OUT/runs"
HEAD=$(git -C "$ROOT" rev-parse --short=8 HEAD 2>/dev/null || echo unknown)
status=0
echo "== R3-1L job $JOB mode $MODE configs $CONFIGS games $GAMES seed $SEED head $HEAD" | tee "$LOGS/job.log"
case "$MODE" in
  release) ;;
  asan)
    export ASAN_OPTIONS="log_path=$SANLOG/asan:detect_leaks=1:abort_on_error=1"
    export UBSAN_OPTIONS="log_path=$SANLOG/ubsan:print_stacktrace=1:halt_on_error=1" ;;
  tsan)
    export TSAN_OPTIONS="log_path=$SANLOG/tsan:halt_on_error=1:second_deadlock_stack=1" ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac

# The all-switch set is read from opus-r3-switches.yml (stays in step with the stack); fallback: the R3 list.
ALLSW=$(grep -oE -- '-DFORGE_[A-Z0-9_]+=[A-Za-z0-9]+' "$ROOT/.github/workflows/opus-r3-switches.yml" 2>/dev/null | tr '\n' ' ')
[ -n "$ALLSW" ] || ALLSW="-DFORGE_NNUE_O2=ON -DFORGE_NOZERO_MOVE_BUFFERS=ON -DFORGE_S13_TT_CHILD_PREFETCH=ON -DFORGE_SPEEDSTACK=ON -DFORGE_NNUE_LAZY_ACC=ON -DFORGE_PROF=ON -DFORGE_NNUE_INT16=ON -DFORGE_DATAGEN=ON -DFORGE_ATTACKS_INIT_ONCE=ON"
switch_args() {
  case $1 in
    base) echo "" ;;
    o2) echo "-DFORGE_NNUE_O2=ON" ;;
    nozero) echo "-DFORGE_NOZERO_MOVE_BUFFERS=ON" ;;
    s13) echo "-DFORGE_S13_TT_CHILD_PREFETCH=ON" ;;
    speedstack) echo "-DFORGE_SPEEDSTACK=ON" ;;
    lazyacc) echo "-DFORGE_NNUE_LAZY_ACC=ON" ;;
    prof) echo "-DFORGE_PROF=ON" ;;
    int16) echo "-DFORGE_NNUE_INT16=ON" ;;
    initonce) echo "-DFORGE_ATTACKS_INIT_ONCE=ON" ;;
    allsw) echo "$ALLSW" ;;
    *) return 1 ;;
  esac
}

build() {   # exe key
  local key=$1 bd="$OUT/build/$1" sw exe="$OUT/engines/opus_r3sp_$1.exe" fma=- ident=FAIL t0
  sw=$(switch_args "$key") || { echo "unknown exe key $key"; return 1; }
  t0=$(date +%s)
  echo "== build $key ($MODE) switches: ${sw:-<none>}" | tee -a "$LOGS/job.log"
  case "$MODE" in
    release) cmake -S "$ROOT" -B "$bd" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
               "-DCMAKE_CXX_FLAGS=$BASE_FLAGS" $sw ;;
    asan) cmake -S "$ROOT" -B "$bd" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER="$CXX" \
            -DFORGE_ENABLE_SANITIZERS=ON "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fno-sanitize-recover=all" $sw ;;
    tsan) cmake -S "$ROOT" -B "$bd" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER="$CXX" \
            "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fsanitize=thread -fno-omit-frame-pointer" \
            "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread" $sw ;;
  esac > "$LOGS/configure_$key.log" 2>&1 || { tail -30 "$LOGS/configure_$key.log"; return 1; }
  cmake --build "$bd" -j"$(nproc)" --target forge > "$LOGS/build_$key.log" 2>&1 || { tail -50 "$LOGS/build_$key.log"; return 1; }
  cp "$bd/forge" "$exe"
  [ "$MODE" = release ] && fma=$(objdump -d "$exe" | grep -cE 'vfn?m(add|sub)' || true)
  python3 "$ROOT/opus_round1/ci/uci_check.py" "$exe" > "$LOGS/identity_$key.log" 2>&1
  grep -q "^ALL OK" "$LOGS/identity_$key.log" && ident="ALL OK"
  {
    echo "exe $key: sha256 $(sha256sum "$exe" | cut -d' ' -f1) bytes $(stat -c %s "$exe") mode $MODE"
    echo "  CMAKE_CXX_FLAGS: $(grep -E '^CMAKE_CXX_FLAGS:' "$bd/CMakeCache.txt" | cut -d= -f2-)"
    echo "  CMAKE_BUILD_TYPE: $(grep -E '^CMAKE_BUILD_TYPE:' "$bd/CMakeCache.txt" | cut -d= -f2-)  switches: ${sw:-<none>}"
    echo "  asan/ubsan/tsan symbols: $(nm "$exe" 2>/dev/null | grep -c '__asan_' || true)/$(nm "$exe" 2>/dev/null | grep -c '__ubsan_' || true)/$(nm "$exe" 2>/dev/null | grep -c '__tsan_' || true)"
    echo "  FMA instructions (release must be 0): $fma"
    echo "  identity (uci_check quick: bench 11/13/16 + perft5 startpos/kiwipete): $ident"
    sed 's/^/    /' "$LOGS/identity_$key.log"
    echo "  build+check seconds: $(( $(date +%s) - t0 ))"
  } | tee -a "$LOGS/builds.txt"
  printf '%s\t%s\t%s\t%s\t%s\n' "$key" "$(sha256sum "$exe" | cut -d' ' -f1)" "$MODE" "$fma" "$ident" >> "$OUT/builds.tsv"
  [ "$ident" = "ALL OK" ] || return 1
  if [ "$MODE" = release ] && [ "$fma" != 0 ]; then return 1; fi
  return 0
}

printf 'job\t%s\n' "$JOB" > "$OUT/job.tsv"
printf 'mode\t%s\nconfigs\t%s\ngames\t%s\nseed\t%s\nhead\t%s\nmax_minutes\t%s\n' "$MODE" "$CONFIGS" "$GAMES" "$SEED" "$HEAD" "$MAXMIN" >> "$OUT/job.tsv"
: > "$OUT/builds.tsv"
KEYS=$(python3 -I -B "$HERE/job_configs.py" "$SP/configs_final.json" "$CONFIGS" "$TB_DIR" "$OUT/job_configs.json") || exit 2
for key in $KEYS; do
  build "$key" || { echo "== build/identity FAILED for $key" | tee -a "$LOGS/job.log"; status=1; }
done

# Nets: replicas from src/nnue_weights.inc + the O4 material-trained stand-alone net (committed copy).
python3 -I -B "$SP/make_nets.py" "$ROOT" "$OUT/nets" "$HERE/nets/o4_material_epoch004-step000000780.fnn2" \
  2>&1 | tee "$LOGS/make_nets.log" || status=1
(cd "$OUT/nets" && sha256sum *.fnn2) | tee -a "$LOGS/make_nets.log"

EXTRA=()
[ "$MAXMIN" != 0 ] && EXTRA+=("--harness-arg=--max-minutes=$MAXMIN")
python3 -I -B "$SP/run_matrix.py" --engines "$OUT/engines" --nets "$OUT/nets" --out "$OUT/runs" --git-head "$HEAD" \
  --configs "$OUT/job_configs.json" --games "$GAMES" --seed "$SEED" --epd "$ROOT/tools/openings/forge-10000.epd" \
  --log-name matrix.log "${EXTRA[@]}"
rc=$?
echo "== run_matrix exit status $rc" | tee -a "$LOGS/job.log"
[ "$rc" -eq 0 ] || status=1

san=$(find "$SANLOG" -type f -size +0 2>/dev/null | wc -l)
printf 'sanitizer_reports\t%s\nmatrix_exit\t%s\n' "$san" "$rc" >> "$OUT/job.tsv"
if [ "$san" -gt 0 ]; then
  echo "== $san sanitizer report file(s):"; find "$SANLOG" -type f -size +0 -print -exec head -60 {} \;
  status=1
else
  echo "== sanitizer reports: 0 ($MODE)" | tee -a "$LOGS/job.log"
fi
[ -f "$OUT/runs/MATRIX.md" ] && { echo; cat "$OUT/runs/MATRIX.md"; } | tee -a "${GITHUB_STEP_SUMMARY:-/dev/null}" > /dev/null
python3 -I -B "$HERE/summarize.py" --single "$OUT" | tee -a "${GITHUB_STEP_SUMMARY:-/dev/null}"
printf 'status\t%s\n' "$status" >> "$OUT/job.tsv"
echo "== R3-1L job $JOB status=$status"
exit $status
