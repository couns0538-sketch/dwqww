#!/usr/bin/env bash
# fl_acceptance.sh TRAINER_COPY OUT_DIR [OLD_LOADER_DLL] [FAST_LOADER_DIR] - Opus R14-B item 1: CPU-only acceptance
# check before the first GPU epoch with --fast-loader. Through the trainer's own data path (Dataset ->
# FixedNumBatchesDataset -> DataLoader, as the patched train.py builds it) it hashes every tensor of 200 training and
# 61 validation batches, once with the old loader (--num-workers 1, the reference stream) and once with the fast
# loader (--num-workers 4, the live line's setting), and compares. GPU hidden: no HIP runtime is loaded next to the
# live npt line. BelowNormal on CPUs 2-3 (lowrun.ps1). Exit 0 = every tensor identical.
#   TRAINER_COPY    a copy of F:\opus_scratch\r6\nnue-pytorch-amd with the switch installed (install_fast_loader.py)
#   OLD_LOADER_DLL  a COPY of the live line's loader DLL; default: the copy's own build\libtraining_data_loader.dll
#                   (a full copy of the live tree has it), else D:\o14b\ref\... (sha256 88c01468..., Opus's copy)
#   FAST_LOADER_DIR folder with forge_fastloader.dll + forge_fastloader.py; default: the trainer copy itself (where
#                   install_fast_loader.py --loader-dll puts them), else D:\o14b\fl\b5_install
set -u
copy=${1:?trainer copy}
out=${2:?out dir}
here=$(cd "$(dirname "$0")" && pwd)   # before any cd: $0 may be relative
T=$(cygpath -w "$here")
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
[ -f "$copy/train.py" ] || { echo "$copy: no train.py" >&2; exit 2; }
grep -q fast_loader "$copy/train.py" || { echo "$copy: --fast-loader switch not installed (install_fast_loader.py)" >&2; exit 2; }
old=${3:-}
if [ -z "$old" ]; then
  if [ -f "$copy/build/libtraining_data_loader.dll" ]; then old=$(cygpath -w "$(cd "$copy" && pwd)/build/libtraining_data_loader.dll")
  else old='D:\o14b\ref\libtraining_data_loader.dll'; fi
fi
fast=${4:-}
if [ -z "$fast" ]; then
  if [ -f "$copy/forge_fastloader.dll" ] && [ -f "$copy/forge_fastloader.py" ]; then fast=$(cygpath -w "$(cd "$copy" && pwd)")
  else fast='D:\o14b\fl\b5_install'; fi
fi
[ -f "$old" ] || { echo "old loader DLL not found: $old (give it as the 3rd argument)" >&2; exit 2; }
{ [ -f "$fast\\forge_fastloader.dll" ] && [ -f "$fast\\forge_fastloader.py" ]; } || {
  echo "no forge_fastloader.dll + .py in $fast (install_fast_loader.py --loader-dll, or give the folder as the 4th argument)" >&2
  exit 2; }
fsha=$(sha256sum < "$fast\\forge_fastloader.dll" | cut -c1-16)
echo "old loader $old ($(sha256sum < "$old" | cut -c1-16)); fast loader folder $fast ($fsha)"
[ "$fsha" = 9eb29b7d134a73eb ] || echo "note: that fast loader DLL is not the b5 candidate (9eb29b7d...) - check which files the folder holds"
mkdir -p "$out"
outw=$(cygpath -w "$(cd "$out" && pwd)")
cd "$copy" || exit 2
export CUDA_VISIBLE_DEVICES=-1 HIP_VISIBLE_DEVICES=-1 ROCR_VISIBLE_DEVICES=-1 PYTHONDONTWRITEBYTECODE=1
export NNUE_DATA_LOADER_LIB="$old" FORGE_FAST_LOADER_DIR="$fast"
for arm in old fast; do
  w=1; [ "$arm" = fast ] && w=4
  t0=$(date +%s)
  powershell -NoProfile -File "$T\\lowrun.ps1" -Mask 0xC -Priority BelowNormal -Exe 'F:\nnue_pytorch\venv\Scripts\python.exe' \
    -ArgLine "-B \"$T\\fl_dataset_equal.py\" --loader $arm --workers $w --batches 200 --val-batches 61 --out \"$outw\\ds_$arm.tsv\"" \
    -Out "$outw\\ds_$arm.log" -Err "$outw\\ds_$arm.err" || { echo "$arm arm failed: see $out/ds_$arm.err" >&2; exit 1; }
  echo "$arm (--num-workers $w): $(( $(date +%s) - t0 )) s; $(tail -2 "$out/ds_$arm.log" | tr '\n' ' ')"
done
/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B "$here/fl_dataset_equal.py" --compare "$out/ds_old.tsv" "$out/ds_fast.tsv"
