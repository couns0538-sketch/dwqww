#!/usr/bin/env bash
# A3 acceptance runs after a3_smoke_train.sh: parity 1k+1k, incremental 200k (with and without the refresh
# cache), planted bugs, refeval CLI sample, "no engine patch" check. nice 19, one thread.
# usage: bash a3_acceptance.sh <scratch_dir> <log_dir> <run_prefix>
set -uo pipefail
fail=0
step() { local rc=${PIPESTATUS[0]}; echo "step $1 exit $rc"; [ "$rc" = 0 ] || fail=1; }
S=$1; L=$2; P=$3
HERE=$(cd "$(dirname "$0")" && pwd)
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
SUP=/f/forge_nnue_train/supervisor.log
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP=$S/tmp TEMP=$S/tmp
cd "$S"
RUN=${P}_seed7_r1
PT=$(ls "$RUN"/epoch003-*.pt)
NET=$RUN/epoch003.fnn
echo "supervisor.log 'adopted running job' lines before: $(grep -c 'adopted running job' "$SUP" || true)" | tee "$L/acceptance_supervisor.log"
{ echo "\$ python -I -B a3_parity_1k.py --trainer opus_nnue_smoke_a3trainer.py --ckpt $PT --net $NET --pos inputs/data32_sample_50k/h000.pos --fens inputs/fens_10k.txt --n 1000 --tol-cp 0.05"
  nice -n 19 "$PY" -I -B "$HERE/a3_parity_1k.py" --trainer opus_nnue_smoke_a3trainer.py --ckpt "$PT" --net "$NET" \
    --pos inputs/data32_sample_50k/h000.pos --fens inputs/fens_10k.txt --n 1000 --tol-cp 0.05; } 2>&1 | tee "$L/parity_1k.log"; step parity_1k
{ echo "\$ python -I -B a3_incremental_200k.py $NET inputs/fens_10k.txt --positions 200000 --seed 1"
  nice -n 19 "$PY" -I -B "$HERE/a3_incremental_200k.py" "$NET" inputs/fens_10k.txt --positions 200000 --seed 1; } 2>&1 | tee "$L/incremental_200k.log"; step incremental_200k
{ echo "\$ python -I -B a3_incremental_200k.py $NET inputs/fens_10k.txt --positions 50000 --seed 2 --no-cache"
  nice -n 19 "$PY" -I -B "$HERE/a3_incremental_200k.py" "$NET" inputs/fens_10k.txt --positions 50000 --seed 2 --no-cache; } 2>&1 | tee "$L/incremental_50k_nocache.log"; step incremental_50k_nocache
MT=${P}_mutation_tmp_$(date +%Y%m%d_%H%M%S)
{ echo "\$ python -I -B a3_mutation_check.py --trainer opus_nnue_smoke_a3trainer.py --ckpt $PT --net $NET --pos inputs/data32_sample_50k/h000.pos --fens inputs/fens_10k.txt --tmp $MT"
  nice -n 19 "$PY" -I -B "$HERE/a3_mutation_check.py" --trainer opus_nnue_smoke_a3trainer.py --ckpt "$PT" --net "$NET" \
    --pos inputs/data32_sample_50k/h000.pos --fens inputs/fens_10k.txt --tmp "$MT"; } 2>&1 | tee "$L/mutation_check.log"; step mutation_check
{ echo "\$ python -I -B forge_astra_A3_converter_20261027.py info $NET"
  nice -n 19 "$PY" -I -B "$HERE/forge_astra_A3_converter_20261027.py" info "$NET"
  echo "\$ python -I -B forge_astra_A3_refeval_20261027.py eval $NET inputs/fens_10k.txt 8"
  nice -n 19 "$PY" -I -B "$HERE/forge_astra_A3_refeval_20261027.py" eval "$NET" inputs/fens_10k.txt 8; } 2>&1 | tee "$L/refeval_cli_sample.log"; step refeval_cli
echo "supervisor.log 'adopted running job' lines after: $(grep -c 'adopted running job' "$SUP" || true)" | tee -a "$L/acceptance_supervisor.log"
{ cd "$(git -C "$HERE" rev-parse --show-toplevel)"
  echo "(in $(pwd), HEAD $(git rev-parse --short HEAD))"
  echo "\$ git diff --stat 294dbed HEAD -- src include tests tools bench CMakeLists.txt   (empty = no engine or lock-tree change)"
  git diff --stat 294dbed HEAD -- src include tests tools bench CMakeLists.txt
  echo "\$ git status --short -- src include tests tools bench CMakeLists.txt   (empty = untouched)"
  git status --short -- src include tests tools bench CMakeLists.txt
  echo "\$ git diff --stat 294dbed HEAD   (everything this branch changes vs the lock source commit)"
  git diff --stat 294dbed HEAD
  echo "end of check"; } 2>&1 | tee "$L/no_engine_change.log"
echo "acceptance: $([ $fail = 0 ] && echo ALL STEPS EXIT 0 || echo SOME STEP FAILED)"
exit $fail
