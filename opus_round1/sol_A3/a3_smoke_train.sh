#!/usr/bin/env bash
# A3 smoke net + fixed-seed reproduction (CPU, 1 thread, nice 19). Pipeline check only: the data32 sample is
# synthetic (random boards, board-independent scores); nothing trained here is a candidate net.
# usage: bash a3_smoke_train.sh <scratch_dir> <log_dir> <run_prefix>
#   <scratch_dir> holds inputs/data32_sample_50k (a copy of LA/5_nnue/sample_data/data32_sample/data32_sample_50k).
#   Copies the trainer to <scratch_dir>/opus_nnue_smoke_a3trainer.py (PC rule: never run trainer code under its
#   own name), trains seed 7 twice and seed 8 once into new run folders <run_prefix>_seed7_r1 / _seed7_r2 /
#   _seed8_r1, converts the last epoch of each with the converter, and prints the sha256 of every .pt and .fnn.
#   Paths given to the Windows Python are relative to <scratch_dir> (Git Bash does not convert a POSIX path that
#   contains '*'). Stops if F:\forge_nnue_train\supervisor.log gains an "adopted running job" line.
set -euo pipefail
S=$1; L=$2; P=$3
HERE=$(cd "$(dirname "$0")" && pwd)
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
DATA=inputs/data32_sample_50k
SUP=/f/forge_nnue_train/supervisor.log
case "$P" in runs_*|smoke_kb*) echo "reserved run prefix"; exit 2;; esac
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP=$S/tmp TEMP=$S/tmp
mkdir -p "$L" "$S/tmp"
cp "$HERE/forge_astra_A3_trainer_20261027.py" "$S/opus_nnue_smoke_a3trainer.py"
echo "trainer copy $S/opus_nnue_smoke_a3trainer.py sha256 $(sha256sum "$S/opus_nnue_smoke_a3trainer.py" | cut -d' ' -f1)"
echo "trainer      $HERE/forge_astra_A3_trainer_20261027.py sha256 $(sha256sum "$HERE/forge_astra_A3_trainer_20261027.py" | cut -d' ' -f1)"
(cd "$S" && sha256sum $DATA/*)
base=$(grep -c "adopted running job" "$SUP" || true)
echo "supervisor.log 'adopted running job' lines before: $base"
check_sup() {
  local now; now=$(grep -c "adopted running job" "$SUP" || true)
  echo "supervisor.log 'adopted running job' lines: $now (baseline $base)"
  if [ "$now" != "$base" ]; then echo "STOP: new adopted line"; exit 3; fi
}
train() {  # <run name> <seed>
  [ -e "$S/$1" ] && { echo "$S/$1 exists"; exit 2; }
  echo "== $1: free RAM $(powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)") GB"
  (cd "$S" && nice -n 19 "$PY" -I -B opus_nnue_smoke_a3trainer.py --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" \
     --hce-dir "$DATA" --run-dir "$1" --king-buckets 4 --king-mirror 1 --king-factor 1 --hidden 256 --l1 16 --l2 32 \
     --output-buckets 8 --epochs 3 --batch-size 1024 --lr 1e-3 --warmup-steps 20 --blend-end 0.6 \
     --val-positions 16384 --log-every 50 --threads 1 --seed "$2") 2>&1 | tee "$L/train_$1.log"
  check_sup
  local pt; pt=$(cd "$S" && ls "$1"/epoch003-*.pt)
  (cd "$S" && nice -n 19 "$PY" -I -B "$HERE/forge_astra_A3_converter_20261027.py" convert "$pt" "$1/epoch003.fnn") 2>&1 | tee "$L/convert_$1.log"
}
train "${P}_seed7_r1" 7
train "${P}_seed7_r2" 7
train "${P}_seed8_r1" 8
echo "== sha256 (the smoke net = ${P}_seed7_r1/epoch003.fnn)"
(cd "$S" && sha256sum "${P}"_seed7_r1/epoch00*.pt "${P}"_seed7_r2/epoch00*.pt "${P}"_seed8_r1/epoch00*.pt \
   "${P}"_seed7_r1/epoch003.fnn "${P}"_seed7_r2/epoch003.fnn "${P}"_seed8_r1/epoch003.fnn)
a=$(sha256sum "$S/${P}_seed7_r1/epoch003.fnn" | cut -d' ' -f1)
b=$(sha256sum "$S/${P}_seed7_r2/epoch003.fnn" | cut -d' ' -f1)
c=$(sha256sum "$S/${P}_seed8_r1/epoch003.fnn" | cut -d' ' -f1)
echo "seed 7 rerun reproduces the smoke net: $([ "$a" = "$b" ] && echo YES || echo NO) ($a vs $b)"
echo "seed 8 differs (control): $([ "$a" != "$c" ] && echo YES || echo NO) ($c)"
[ "$a" = "$b" ] && [ "$a" != "$c" ]
