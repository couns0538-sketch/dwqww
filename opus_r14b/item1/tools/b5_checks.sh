#!/usr/bin/env bash
# b5_checks.sh OUT_DIR - Opus R14-B item 1: every remaining CPU check of candidate b5, one after another on CPUs 2-3
# (BelowNormal). Copy this script into OUT_DIR's parent and run the copy (never edit a running script).
#   1 standard config: old w1 vs fast (1/4 builders): train 1000 batches, validation cyclic 300 + finite
#   2 config matrix on the self-test's synthetic files (cyclic 120 batches + finite), skip settings and shapes
#   3 real data, batch 10000 (batches span windows), 3,100 batches = past the first wrap of the train file
#   4 trainer path: fl_dataset_equal.py old vs fast (200 train + 61 validation batches, every tensor)
#   5 speed: palindromic ABBA, 10 pairs, old w2 vs fast 1 builder (both 3 loader threads), 420 batches (20 warm-up)
set -u
out=${1:?out dir}
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
mkdir -p "$out"
T=/d/grok-pc-data/dwqww/.claude/worktrees/o14b-l1/opus_r14b/item1/tools
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
OLD='D:\o14b\ref\libtraining_data_loader.dll'
NEW='D:\o14b\fl\b5\forge_fastloader.dll'
TRAIN='F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack'
VAL='F:\forge_j1_data\forge_holdout_013-014_j2.binpack'
SYN='D:\o14b\fl\st5\ffl_a.binpack'
LOW='D:\o14b\fl\st5\ffl_low.binpack'
fails=0
eq() {  # eq NAME DATA "args..."  -> old w1 vs fast 2 builders with the same settings
  local name=$1 data=$2; shift 2
  "$PY" -I -B "$T/fl_equal.py" dump --loader old --dll "$OLD" --workers 1 --data "$data" "$@" --out "$out/$name.old.tsv" >/dev/null
  "$PY" -I -B "$T/fl_equal.py" dump --loader fast --dll "$NEW" --workers 2 --data "$data" "$@" --out "$out/$name.fast.tsv" >/dev/null
  if "$PY" -I -B "$T/fl_equal.py" compare "$out/$name.old.tsv" "$out/$name.fast.tsv" > "$out/$name.cmp"; then
    echo "PASS $name: $(head -1 "$out/$name.cmp" | sed 's/^.*compared/compared/')"
  else
    echo "FAIL $name: $(head -3 "$out/$name.cmp" | tr '\n' ' ')"; fails=$((fails + 1))
  fi
}
echo "== 1 standard config $(date '+%H:%M:%S')"
eq std_train "$TRAIN" --batches 1000
"$PY" -I -B "$T/fl_equal.py" dump --loader fast --dll "$NEW" --workers 4 --data "$TRAIN" --batches 1000 --out "$out/std_train.fast4.tsv" >/dev/null
"$PY" -I -B "$T/fl_equal.py" compare "$out/std_train.old.tsv" "$out/std_train.fast4.tsv" | head -1
eq std_val_cyc "$VAL" --batches 300
eq std_val_fin "$VAL" --batches 100000 --finite
echo "== 2 config matrix $(date '+%H:%M:%S')"
for mode in cyc fin; do
  m=""; n=120; [ $mode = fin ] && { m=--finite; n=100000; }
  eq "syn_default_$mode" "$SYN" --batch 700 --window 1500 --batches $n $m
  eq "syn_nofilter_$mode" "$SYN" --batch 700 --window 1500 --batches $n $m --skip soft_early_fen_skipping=0
  eq "syn_random3_$mode" "$SYN" --batch 700 --window 1500 --batches $n $m --skip random_fen_skipping=3
  eq "syn_early8_$mode" "$SYN" --batch 700 --window 1500 --batches $n $m --skip early_fen_skipping=8
  eq "syn_pcy1zero_$mode" "$SYN" --batch 700 --window 1500 --batches $n $m --skip pc_y1=0
  eq "syn_plyy1zero_$mode" "$SYN" --batch 700 --window 1500 --batches $n $m --skip ply_y1=0,ply_x1=2
  eq "syn_spline_$mode" "$SYN" --batch 700 --window 1500 --batches $n $m --skip pc_y0=0.2,pc_y2=0.5,pc_y4=1.0,ply_y2=0.5
  eq "syn_w1024_b5000_$mode" "$SYN" --batch 5000 --window 1024 --batches $((n / 4)) $m
  eq "syn_b16384_$mode" "$SYN" --batch 16384 --batches 20 $m
done
eq low_pcy1zero_fin "$LOW" --batch 512 --window 4096 --batches 100000 --finite --skip pc_y1=0
eq low_default_fin "$LOW" --batch 512 --window 4096 --batches 100000 --finite
echo "== 3 real data, batch 10000, past the first wrap $(date '+%H:%M:%S')"
eq real_b10000 "$TRAIN" --batch 10000 --batches 3100
echo "== 4 trainer path (Dataset -> FixedNumBatchesDataset -> DataLoader) $(date '+%H:%M:%S')"
(
  export CUDA_VISIBLE_DEVICES=-1 HIP_VISIBLE_DEVICES=-1 ROCR_VISIBLE_DEVICES=-1
  export NNUE_DATA_LOADER_LIB="$OLD" FORGE_FAST_LOADER_DIR='D:\o14b\fl\b5_install' PYTHONDONTWRITEBYTECODE=1
  cd /d/o14b/npt
  for arm in old fast; do
    w=1; [ $arm = fast ] && w=4
    powershell -NoProfile -File "$(cygpath -w "$T/lowrun.ps1")" -Mask 0xC -Priority BelowNormal \
      -Exe 'F:\nnue_pytorch\venv\Scripts\python.exe' \
      -ArgLine "-B $(cygpath -w "$T/fl_dataset_equal.py") --loader $arm --workers $w --batches 200 --val-batches 61 --out $(cygpath -w "$out")\\ds_$arm.tsv" \
      -Out "$(cygpath -w "$out")\\ds_$arm.log" -Err "$(cygpath -w "$out")\\ds_$arm.err"
  done
)
if "$PY" -I -B "$T/fl_dataset_equal.py" --compare "$out/ds_old.tsv" "$out/ds_fast.tsv" > "$out/ds.cmp"; then
  echo "PASS dataset: $(cat "$out/ds.cmp")"
else
  echo "FAIL dataset: $(head -3 "$out/ds.cmp" | tr '\n' ' ')"; fails=$((fails + 1))
fi
echo "== 5 ABBA $(date '+%H:%M:%S')"
"$PY" -I -B "$T/fl_abba.py" --out "$out/abba_w2_vs_f1" --pairs 10 --a "old:$OLD:2" --b "fast:$NEW:1" --batches 420 --warmup 20 | tail -3
echo "== 6 one full trainer epoch through the fast loader alone (9,307 batches = 152.5M positions) $(date '+%H:%M:%S')"
"$PY" -I -B "$T/fl_equal.py" dump --loader fast --dll "$NEW" --workers 2 --data "$TRAIN" --batches 9307 --warmup 20 \
  --no-hash --out "$out/full_epoch_fast.tsv" | tail -1
grep '^#' "$out/full_epoch_fast.tsv"
echo "== done $(date '+%H:%M:%S'), failures: $fails"
