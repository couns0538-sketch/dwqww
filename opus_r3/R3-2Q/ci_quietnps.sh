#!/usr/bin/env bash
# R3-2Q: paired ABBA NPS of one R3 build switch against the OFF build of the same commit on a quiet GitHub runner
# (.github/workflows/opus-r3-quietnps.yml, one job per config x rep). Build recipe = opus_round1/ci/run_ci.sh release:
# g++-14, CMake Release, Ninja, --target forge, CMAKE_CXX_FLAGS = box flags (x86-64-v3 = AVX2), plus -D<SWITCH>=ON.
# Every job runs, with quiet_nps.py (fresh processes, ABBA, nodes must match, CPU-time NPS, paired t on log ratios):
#   AA  : OFF vs a byte copy of OFF (the A/A control of this runner)
#   SW  : OFF vs the switch build (options off; every switch is node-exact with its options off)
#   OPT : same-exe option effect inside the switch build (S13: TtChildPrefetch=true; LAZY: NnueLazyAcc=true;
#         INT16: NnueInt16=true, tree changes -> NPS only; PROF: bench vs bench_prof = profile counting on)
#   SW_V4 (O2 only, if the runner has AVX-512): OFF_v4 vs O2_v4, both built with -march=x86-64-v4 (O2's AVX2
#         kernels compiled out, as in the PC's znver5 build)
#   config AA additionally builds OFF a second time in another build dir (AA_REBUILD: OFF vs that rebuild).
# usage: opus_r3/R3-2Q/ci_quietnps.sh <AA|NOZERO|O2|SPEEDSTACK|S13|LAZY|INT16|PROF|ALL|DRIFT> <rep> [out_dir]
# env: PAIRS (default 16:10,20:8 = 10 ABBA pairs at bench 16, 8 at bench 20), CXX, PY
set -uo pipefail
CFG=$1
REP=$2
OUT=${3:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
JOB="$ROOT/opus_r3/R3-2Q"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
PY=${PY:-python3}
PAIRS=${PAIRS:-16:10,20:8}
PINS="16=3024920,20=12389307"
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
V4_FLAGS="-march=x86-64-v4 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
status=0

case "$CFG" in
  AA)         SW="" ;;
  NOZERO)     SW="-DFORGE_NOZERO_MOVE_BUFFERS=ON" ;;
  O2)         SW="-DFORGE_NNUE_O2=ON" ;;
  SPEEDSTACK) SW="-DFORGE_SPEEDSTACK=ON" ;;
  S13)        SW="-DFORGE_S13_TT_CHILD_PREFETCH=ON" ;;
  LAZY)       SW="-DFORGE_NNUE_LAZY_ACC=ON" ;;
  INT16)      SW="-DFORGE_NNUE_INT16=ON" ;;
  PROF)       SW="-DFORGE_PROF=ON" ;;
  ALL)        SW="-DFORGE_NNUE_O2=ON -DFORGE_NOZERO_MOVE_BUFFERS=ON -DFORGE_SPEEDSTACK=ON -DFORGE_S13_TT_CHILD_PREFETCH=ON -DFORGE_NNUE_LAZY_ACC=ON -DFORGE_NNUE_INT16=ON -DFORGE_PROF=ON" ;;
  N2)         SW="-DFORGE_NNUE_O2=ON -DFORGE_NOZERO_MOVE_BUFFERS=ON -DFORGE_SPEEDSTACK=ON" ;;  # R5B: the N2 speed build
  DRIFT)      SW="" ;;  # OFF built from R3-2's first-pass head 2432670b (A) vs OFF at this head (B): R3-2's H3DRIFT row
  *) echo "unknown config $CFG"; exit 2 ;;
esac

{
  echo "config $CFG rep $REP pairs $PAIRS commit $(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo '?')"
  echo "compiler: $($CXX --version | head -1)"
  echo "nproc: $(nproc)"
  lscpu | grep -E 'Model name|^CPU\(s\)|Thread|Core|Socket|L2|L3|MHz' || true
  echo "avx512 (x86-64-v4 set): $(grep -o -w -E 'avx512(f|bw|cd|dq|vl)' /proc/cpuinfo | sort -u | tr '\n' ' ')"
  uptime
} | tee "$OUT/runner_${CFG}_${REP}.txt"

build() {  # build <name> <cxx_flags> [-D... switches]; forge target only, copied to $OUT/forge_<name>
  local name=$1 flags=$2 src=${SRC:-$ROOT}; shift 2
  # shellcheck disable=SC2068
  cmake -S "$src" -B "$OUT/build_$name" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
    "-DCMAKE_CXX_FLAGS=$flags" $@ > "$OUT/configure_$name.log" 2>&1 || { tail -30 "$OUT/configure_$name.log"; exit 1; }
  cmake --build "$OUT/build_$name" --target forge -j"$(nproc)" > "$OUT/build_$name.log" 2>&1 \
    || { tail -60 "$OUT/build_$name.log"; exit 1; }
  cp "$OUT/build_$name/forge" "$OUT/forge_$name"
  echo "build $name: sha256 $(sha256sum "$OUT/forge_$name" | cut -d' ' -f1) bytes $(stat -c %s "$OUT/forge_$name")" \
    "FMA $(objdump -d "$OUT/forge_$name" | grep -cE 'vfn?m(add|sub)' || true)" \
    "warnings $(grep -ci 'warning:' "$OUT/build_$name.log")" \
    "defs [$(grep -oE 'FORGE_[A-Z0-9_]+=1' "$OUT/build_$name/build.ninja" | sort -u | tr '\n' ' ')] flags [$flags] $*" \
    | tee -a "$OUT/builds_${CFG}_${REP}.log"
}

compare() {  # compare <label> <exe_A> <exe_B> [quiet_nps.py args...]
  local label=$1 a=$2 b=$3; shift 3
  local base="$OUT/nps_${CFG}_${REP}_${label}"
  echo "== $(date -u +%H:%M:%S) compare $label: A=$(basename "$a") B=$(basename "$b") $*"
  $PY "$JOB/quiet_nps.py" --a "$a" --b "$b" --label "$label" --config "$CFG" --rep "$REP" --pairs "$PAIRS" \
    --json "$base.json" "$@" > "$base.log" 2>&1 || { echo "quiet_nps $label: FAILED (see $(basename "$base.log"))"; status=1; }
  grep -E '^(NODES|RESULT|R3-2Q .* ok=)' "$base.log" | grep -vE 'cpu_total|wall' || tail -20 "$base.log"
}

build off "$BASE_FLAGS"
cp "$OUT/forge_off" "$OUT/forge_off_copy"
if [ -n "$SW" ]; then
  # shellcheck disable=SC2086
  build sw "$BASE_FLAGS" $SW
  if cmp -s "$OUT/forge_off" "$OUT/forge_sw"; then
    echo "WARNING: the switch build is byte-identical to OFF" | tee -a "$OUT/builds_${CFG}_${REP}.log"
  else
    echo "switch build differs from OFF in $(cmp -l "$OUT/forge_off" "$OUT/forge_sw" | wc -l) bytes" | tee -a "$OUT/builds_${CFG}_${REP}.log"
  fi
fi

# A/A control first, then the switch, then the same-exe option effect.
compare AA "$OUT/forge_off" "$OUT/forge_off_copy" --pins "$PINS" --note "OFF vs byte copy of OFF"
case "$CFG" in
  DRIFT)
    OLD=2432670b7cc02121fcf79594b02a444554134a33
    git -C "$ROOT" fetch -q --depth 1 origin "$OLD" || { echo "fetch of $OLD failed"; exit 1; }
    mkdir -p "$OUT/src_old"
    # -m: archived files get the current time (ninja loops on future mtimes)
    git -C "$ROOT" archive "$OLD" | tar -x -m -C "$OUT/src_old"
    SRC="$OUT/src_old" build old "$BASE_FLAGS"
    compare SW "$OUT/forge_old" "$OUT/forge_off" --pins "$PINS" \
      --note "OFF built from 2432670b (R3-2 first pass) vs OFF at this head (= 330237f3 engine, R3-2 base_h3)"
    ;;
  AA)
    build off2 "$BASE_FLAGS"
    if cmp -s "$OUT/forge_off" "$OUT/forge_off2"; then echo "rebuild of OFF is byte-identical" | tee -a "$OUT/builds_${CFG}_${REP}.log"
    else echo "rebuild of OFF differs in $(cmp -l "$OUT/forge_off" "$OUT/forge_off2" | wc -l) bytes" | tee -a "$OUT/builds_${CFG}_${REP}.log"; fi
    compare AA_REBUILD "$OUT/forge_off" "$OUT/forge_off2" --pins "$PINS" --note "OFF vs a second OFF build (other build dir)"
    ;;
  *)
    compare SW "$OUT/forge_off" "$OUT/forge_sw" --pins "$PINS" --note "OFF vs $CFG build, options off"
    ;;
esac
case "$CFG" in
  S13)   compare OPT "$OUT/forge_sw" "$OUT/forge_sw" --pins "$PINS" --opt-b TtChildPrefetch=true \
           --note "S13 build: TtChildPrefetch false vs true (same exe)" ;;
  LAZY)  compare OPT "$OUT/forge_sw" "$OUT/forge_sw" --pins "$PINS" --opt-b NnueLazyAcc=true \
           --note "LAZY build: NnueLazyAcc false vs true (same exe)" ;;
  INT16) compare OPT "$OUT/forge_sw" "$OUT/forge_sw" --pins "$PINS" --opt-b NnueInt16=true --expect-node-diff \
           --note "INT16 build: NnueInt16 false vs true (same exe); the tree changes, NPS only" ;;
  PROF)  compare OPT "$OUT/forge_sw" "$OUT/forge_sw" --pins "$PINS" --cmd-b bench_prof \
           --note "PROF build: bench (counting off) vs bench_prof (counting on), same exe" ;;
  N2)
    # R5B: with -march=x86-64-v4 the N2 build uses the O2 512-bit accumulator kernels (the PC's znver5 build).
    if [ "$(grep -o -w -E 'avx512(f|bw|cd|dq|vl)' /proc/cpuinfo | sort -u | wc -l)" -eq 5 ]; then
      build off_v4 "$V4_FLAGS"
      # shellcheck disable=SC2086
      build sw_v4 "$V4_FLAGS" $SW
      compare SW_V4 "$OUT/forge_off_v4" "$OUT/forge_sw_v4" --pins "$PINS" \
        --note "x86-64-v4 (AVX-512) OFF vs N2: O2 512-bit kernels + NOZERO + SPEEDSTACK"
    else
      echo "runner has no AVX-512 (x86-64-v4): SW_V4 row skipped" | tee -a "$OUT/builds_${CFG}_${REP}.log"
    fi
    ;;
  O2)
    if [ "$(grep -o -w -E 'avx512(f|bw|cd|dq|vl)' /proc/cpuinfo | sort -u | wc -l)" -eq 5 ]; then
      build off_v4 "$V4_FLAGS"
      build sw_v4 "$V4_FLAGS" -DFORGE_NNUE_O2=ON
      compare SW_V4 "$OUT/forge_off_v4" "$OUT/forge_sw_v4" --pins "$PINS" \
        --note "x86-64-v4 (AVX-512) OFF vs O2: O2's AVX2 kernels are compiled out, as in the PC znver5 build"
    else
      echo "runner has no AVX-512 (x86-64-v4): SW_V4 row skipped" | tee -a "$OUT/builds_${CFG}_${REP}.log"
    fi
    ;;
esac
$PY "$JOB/analyze_quietnps.py" "$OUT" --md "$OUT/table_${CFG}_${REP}.md" || status=1
echo "ci_quietnps $CFG rep $REP status=$status"
exit $status
