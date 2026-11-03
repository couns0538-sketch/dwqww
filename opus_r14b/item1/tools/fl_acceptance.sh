#!/usr/bin/env bash
# fl_acceptance.sh TRAINER_COPY OUT_DIR [OLD_LOADER_DLL] [FAST_LOADER_DIR] - Opus R14-B item 1: CPU-only acceptance
# check before the first GPU epoch with --fast-loader. Through the trainer's own data path (Dataset ->
# FixedNumBatchesDataset -> DataLoader, as the patched train.py builds it) it hashes every tensor of 200 training and
# 61 validation batches, once with the old loader (--num-workers 1, the reference stream) and once with the fast
# loader (--num-workers 4, the live line's setting), and compares. GPU hidden: no HIP runtime is loaded next to the
# live npt line. BelowNormal on CPUs 2-3 (lowrun.ps1). Exit 0 = every tensor identical.
#   TRAINER_COPY    a copy of F:\opus_scratch\r6\nnue-pytorch-amd with the switch installed (install_fast_loader.py)
#   OLD_LOADER_DLL  a COPY of the live line's build\libtraining_data_loader.dll (default D:\o14b\ref\..., sha256 88c01468...)
#   FAST_LOADER_DIR folder with forge_fastloader.dll + forge_fastloader.py (default D:\o14b\fl\b5_install)
set -u
copy=${1:?trainer copy}
out=${2:?out dir}
old=${3:-'D:\o14b\ref\libtraining_data_loader.dll'}
fast=${4:-'D:\o14b\fl\b5_install'}
here=$(cd "$(dirname "$0")" && pwd)   # before any cd: $0 may be relative
T=$(cygpath -w "$here")
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
[ -f "$copy/train.py" ] || { echo "$copy: no train.py" >&2; exit 2; }
grep -q fast_loader "$copy/train.py" || { echo "$copy: --fast-loader switch not installed (install_fast_loader.py)" >&2; exit 2; }
mkdir -p "$out"
outw=$(cygpath -w "$(cd "$out" && pwd)")
cd "$copy" || exit 2
export CUDA_VISIBLE_DEVICES=-1 HIP_VISIBLE_DEVICES=-1 ROCR_VISIBLE_DEVICES=-1 PYTHONDONTWRITEBYTECODE=1
export NNUE_DATA_LOADER_LIB="$old" FORGE_FAST_LOADER_DIR="$fast"
for arm in old fast; do
  w=1; [ "$arm" = fast ] && w=4
  t0=$(date +%s)
  powershell -NoProfile -File "$T\\lowrun.ps1" -Mask 0xC -Priority BelowNormal -Exe 'F:\nnue_pytorch\venv\Scripts\python.exe' \
    -ArgLine "-B $T\\fl_dataset_equal.py --loader $arm --workers $w --batches 200 --val-batches 61 --out $outw\\ds_$arm.tsv" \
    -Out "$outw\\ds_$arm.log" -Err "$outw\\ds_$arm.err" || { echo "$arm arm failed: see $out/ds_$arm.err" >&2; exit 1; }
  echo "$arm (--num-workers $w): $(( $(date +%s) - t0 )) s; $(tail -2 "$out/ds_$arm.log" | tr '\n' ' ')"
done
/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B "$here/fl_dataset_equal.py" --compare "$out/ds_old.tsv" "$out/ds_fast.tsv"
