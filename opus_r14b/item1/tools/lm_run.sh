#!/usr/bin/env bash
# lm_run.sh ARM OUT_DIR [extra train.py args] - Opus R14-B item 1: one arm of the CPU loss match.
#   ARM = old  -> trainer copy with the default loader, --num-workers 1 (the deterministic reference)
#   ARM = fast -> same trainer copy with --fast-loader --num-workers 2
# Recipe = the npt line (K32H3^, L1 1024, batch 16384, seed 5117, lr 8.75e-4, gamma 0.72, lambda 1.0,
# --no-filtered --no-wld-filtered) on the CPU with 1 epoch = 64 batches (one shuffle window) and 10 validation
# batches. GPUs hidden exactly like the keeper's exports (no HIP device next to the live npt line); R6 RAM guard
# (7 GB floor, JSON summary); BelowNormal on CPUs 2-3 via tools/lowrun.ps1. OUT_DIR must not exist.
set -euo pipefail
arm=${1:?arm old|fast}
out=${2:?out dir}
shift 2
here=$(cd "$(dirname "$0")" && pwd)
npt=${NPT_COPY:-/d/o14b/npt}
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
mkdir -p "$out"
case $arm in
  old) extra="--num-workers 1" ;;
  fast) extra="--num-workers 2 --fast-loader" ;;
  *) echo "arm must be old or fast" >&2; exit 2 ;;
esac
outw=$(cygpath -w "$out")
export CUDA_VISIBLE_DEVICES=-1 HIP_VISIBLE_DEVICES=-1 ROCR_VISIBLE_DEVICES=-1
export NNUE_DATA_LOADER_LIB='D:\o14b\ref\libtraining_data_loader.dll'
export NNUE_FT_BACKEND=torch TORCHDYNAMO_DISABLE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
export R6_MIN_FREE_GB=7 R6_GUARD_LOG="$outw\\guard.jsonl"
args="-B opus_tools\\guard_exec.py train.py F:\\forge_j1_data\\forge_train_001-039_ex013-014_j2.binpack"
args="$args --validation-datasets F:\\forge_j1_data\\forge_holdout_013-014_j2.binpack --validation-size 163840"
args="$args --default-root-dir $outw\\run --features K32H3^ --l1 1024 --batch-size 16384 --threads 2"
args="$args --epoch-size 1048576 --max-epochs 1 --network-save-period 1 --save-last-network False"
args="$args --swa-start-epoch -1 --seed 5117 --lr 0.000875 --start-lambda 1.0 --end-lambda 1.0"
args="$args --no-filtered --no-wld-filtered --accelerator cpu --gamma 0.72 $extra $*"
cd "$npt"
echo "$(date '+%F %T') arm=$arm args: $args" > "$out/command.txt"
powershell -NoProfile -File "$(cygpath -w "$here/lowrun.ps1")" -Mask 0xC -Priority BelowNormal \
  -Exe 'F:\nnue_pytorch\venv\Scripts\python.exe' -ArgLine "$args" -Out "$outw\\stdout.log" -Err "$outw\\stderr.log"
echo "exit=$?" >> "$out/command.txt"
