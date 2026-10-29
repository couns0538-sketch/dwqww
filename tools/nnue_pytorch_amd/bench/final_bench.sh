#!/usr/bin/env bash
# R6 final clean A/B at smoke size only (PC rule after the 14:29 incident), every run under guard_exec.py
# (aborts itself below 7 GB free RAM). Usage: final_bench.sh RUNSET   (RUNSET: k32 | full)
source /f/opus_scratch/r6/tools/env.sh
cd /f/opus_scratch/r6/nnue-pytorch-amd || exit 1
export R6_GUARD_LOG=F:/opus_scratch/r6/logs/guard_runs.jsonl R6_EPOCH_TIMER=1 R6_EPOCH_SIZE=204800
export TORCHINDUCTOR_COMPILE_THREADS=1
OUT=/f/opus_scratch/r6/final_bench
mkdir -p $OUT
CLANG=F:/opus_scratch/r6/loader/clang23_msvc/training_data_loader.dll
run() {  # name, env..., then train args after --
  local name=$1; shift
  local envs=()
  while [ "$1" != "--" ]; do envs+=("$1"); shift; done; shift
  local trainer_before
  trainer_before=$(tr '\r' '\n' < "$(ls -t /f/forge_nnue_train/runs/*.log | head -1)" | grep -a "pos/s" | tail -1 | grep -o "[0-9,]* pos/s")
  env "${envs[@]}" nice -n 10 "$PY" -B ../tools/guard_exec.py train.py "$@" \
     --default-root-dir "F:/opus_scratch/r6/final_bench/$name" > "$OUT/$name.log" 2>&1
  local rc=$?
  local summ
  summ=$(grep -a '^\[guard\] {' "$OUT/$name.log" | tail -1)
  local rates
  rates=$(grep -a '^\[guard\] epoch' "$OUT/$name.log" | sed -E 's/.*: ([0-9,]+) pos\/s.*/\1/' | tr '\n' ' ')
  echo "$name rc=$rc trainer_before=[$trainer_before] rates: $rates"
  echo "   $summ"
  if [ $rc -eq 97 ]; then echo "GUARD ABORT - stopping the set"; exit 97; fi
}
K32='.pgo/small.binpack --features K32H3^ --l1 256 --accelerator cuda --batch-size 4096 --epoch-size 204800 --max-epochs 10 --threads 2 --num-workers 1'
FULL='.pgo/small.binpack --features Full_Threats+PP_3Wide+K32H3^ --l1 256 --accelerator cuda --batch-size 4096 --epoch-size 204800 --max-epochs 8 --threads 2 --num-workers 1'
case $1 in
  k32)
    run A1_torch_eager   NNUE_FT_BACKEND=torch NNUE_RANGER_FUSED=0 TORCHDYNAMO_DISABLE=1 -- $K32
    run E1_triton_all_compile NNUE_FT_BACKEND=auto -- $K32
    run B_tritonFT_eager NNUE_FT_BACKEND=auto NNUE_RANGER_FUSED=0 TORCHDYNAMO_DISABLE=1 -- $K32
    run C_triton_all_eager NNUE_FT_BACKEND=auto TORCHDYNAMO_DISABLE=1 -- $K32
    run D_torchFT_compile NNUE_FT_BACKEND=torch NNUE_RANGER_FUSED=0 -- $K32
    run A2_torch_eager   NNUE_FT_BACKEND=torch NNUE_RANGER_FUSED=0 TORCHDYNAMO_DISABLE=1 -- $K32
    run E2_triton_all_compile NNUE_FT_BACKEND=auto -- $K32
    ;;
  full)
    run F1_full_torch_eager NNUE_FT_BACKEND=torch NNUE_RANGER_FUSED=0 TORCHDYNAMO_DISABLE=1 NNUE_DATA_LOADER_LIB=$CLANG -- $FULL
    run F2_full_triton_all_compile NNUE_FT_BACKEND=auto NNUE_DATA_LOADER_LIB=$CLANG -- $FULL
    ;;
esac
