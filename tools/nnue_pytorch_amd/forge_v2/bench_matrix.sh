#!/usr/bin/env bash
# R7 J1 A/B matrix: plain (Grok Bot's embedding_bag path) vs the Triton path for Forge's v2 net, smoke size
# (batch 4096, 1 loader thread), two interleaved rounds, every run inside the R6 RAM guard (7 GB floor).
# usage: bench_matrix.sh <data.binpack> <out_dir> [rounds=2]
# Writes <out_dir>/<round>_<name>.{log,json} and <out_dir>/matrix.tsv (round, name, pos/s, guard min free GB).
set -uo pipefail
DATA=$1; OUT=$2; ROUNDS=${3:-2}
source /f/opus_scratch/r7/tools/env_r7.sh
HERE=$(cd "$(dirname "$0")" && pwd -W 2>/dev/null || pwd)
T="$HERE/train_forge_v2_fast.py"
SETUP_DLL="F:/opus_scratch/r6/nnue-pytorch-amd/build/libtraining_data_loader.dll"
CLANG_DLL="F:/opus_scratch/r6/loader/clang23_msvc/training_data_loader.dll"
mkdir -p "$OUT"
TSV="$OUT/matrix.tsv"
[ -f "$TSV" ] || printf 'round\tname\tpos_per_s\tguard_min_free_gb\ttrainer_last\n' > "$TSV"
run() {  # run <round> <name> <dll> <args...>
  local r=$1 name=$2 dll=$3; shift 3
  local pre; pre=$(bash /f/opus_scratch/r7/tools/precheck.sh)
  echo "$pre" > "$OUT/${r}_${name}.log"
  NNUE_DATA_LOADER_LIB="$dll" nice -n 10 "$PY" -B "$GUARD" "$T" --data "$DATA" --batch 4096 --threads 1 \
    --json "$OUT/${r}_${name}.json" "$@" >> "$OUT/${r}_${name}.log" 2>&1
  local rate; rate=$(grep -o 'RESULT .*: [0-9]* pos/s' "$OUT/${r}_${name}.log" | grep -o ': [0-9]* pos/s' | grep -o '[0-9]*')
  local minfree; minfree=$(grep -o '"min_free_gb": [0-9.]*' "$OUT/${r}_${name}.log" | grep -o '[0-9.]*$')
  local post; post=$(bash /f/opus_scratch/r7/tools/precheck.sh)
  echo "$post" >> "$OUT/${r}_${name}.log"
  printf '%s\t%s\t%s\t%s\t%s\n' "$r" "$name" "${rate:-FAIL}" "${minfree:-?}" "$(echo "$post" | grep -o '[0-9,]* pos/s$')" >> "$TSV"
  echo "$r $name ${rate:-FAIL} pos/s (min free ${minfree:-?} GB)"
  if grep -q '"aborted": true' "$OUT/${r}_${name}.log"; then echo "guard aborted: stopping the matrix"; exit 3; fi
}
for r in $(seq 1 "$ROUNDS"); do
  run "$r" loader_setup "$SETUP_DLL" --mode loader --steps 1500 --warmup 50
  run "$r" plain_adam "$SETUP_DLL" --backend plain --steps 600 --warmup 50
  run "$r" triton_adam "$SETUP_DLL" --backend triton --steps 600 --warmup 50
  run "$r" triton_fused "$SETUP_DLL" --backend triton --fused-adam 1 --steps 600 --warmup 50
  run "$r" triton_fused_compile "$SETUP_DLL" --backend triton --fused-adam 1 --compile 1 --steps 600 --warmup 80
  run "$r" synth_plain "$SETUP_DLL" --backend plain --mode synthetic --steps 400 --warmup 50
  run "$r" synth_triton_fused "$SETUP_DLL" --backend triton --fused-adam 1 --mode synthetic --steps 400 --warmup 50
  run "$r" loader_clang "$CLANG_DLL" --mode loader --steps 1500 --warmup 50
  run "$r" triton_fused_clang "$CLANG_DLL" --backend triton --fused-adam 1 --steps 600 --warmup 50
done
echo "matrix done: $TSV"
