#!/usr/bin/env bash
# C5 local export parity: engine side with the merged build's forge_nnue_v2_tool, PyTorch side with the scratch copy
# opus_v2_parity.py (= tools/nnue/v2_parity.py importing opus_nnue_smoke instead of train_resid_v3b), 1 torch thread,
# nice 19, CPU torch venv. Every output stays under F:/opus_scratch/c5.
# usage: run_parity.sh <tool.exe> <name>
set -u
S=/f/opus_scratch/c5
V=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
TOOL=$1; name=$2
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$S" || exit 1
[ -f parity_positions.fen ] || nice -n 19 "$TOOL" positions F:/opus_scratch/c5/parity_positions.fen 10000 20261026
NET=$(ls smoke_$name/epoch003-*.fnn2)
{
  echo "# C5 export parity, net smoke_$name/$(basename "$NET") (sha256 $(sha256sum "$NET" | cut -c1-16)...), 10000 positions (forge_nnue_v2_tool positions ... 10000 20261026, sha256 $(sha256sum parity_positions.fen | cut -c1-16)...)"
  echo "\$ forge_nnue_v2_tool eval $NET parity_positions.fen cpp_$name"
  nice -n 19 "$TOOL" eval "F:/opus_scratch/c5/$NET" F:/opus_scratch/c5/parity_positions.fen "F:/opus_scratch/c5/cpp_$name" 2>&1
  echo "tool exit status $?"
  echo "\$ python opus_v2_parity.py ${NET%.fnn2}.pt $NET parity_positions.fen cpp_$name --json parity_$name.json"
  nice -n 19 "$V" run1t.py opus_v2_parity.py "F:/opus_scratch/c5/${NET%.fnn2}.pt" "F:/opus_scratch/c5/$NET" F:/opus_scratch/c5/parity_positions.fen \
    "F:/opus_scratch/c5/cpp_$name" --json "F:/opus_scratch/c5/parity_$name.json" 2>&1
  echo "parity exit status $?"
} > "parity_$name.log" 2>&1
cat "parity_$name.log"
