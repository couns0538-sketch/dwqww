#!/usr/bin/env bash
# O6 local speed evidence on the shared PC (machine exclusive: no; nice 19, one thread, no torch): bench NPS at depth
# 16 / 20 (opus_round1/C4/nps_ab_options.py, ABBA, fresh processes), A = the AL1 s198 lock exe:
#   1. B = this branch's exe with NNUEFile = the lock net as a v2 replica plus a threat block of zeros, NNUEThreats 1:
#      it evaluates exactly like the lock, so A and B search the identical tree (node counts are checked) and the
#      difference is the engine cost of the threat inputs (pair lists, multiset differences, extra columns);
#   2. B = this branch's exe with a CPU-trained threat net (another evaluation, another tree: nodes reported).
# usage: local_nps.sh <out_dir> <lock_exe> <o6_exe> <threat_net.fnn2> [runs (default 8)]
set -uo pipefail
REPO=$(cd "$(dirname "$0")/../.." && pwd)
mixed() { if command -v cygpath > /dev/null; then cygpath -m "$1"; else echo "$1"; fi; }
OUT=$(mixed "$1"); LOCK=$(mixed "$2"); EXE=$(mixed "$3"); NET=$(mixed "$4"); RUNS=${5:-8}
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT"
echo "machine exclusive: no"
python "$REPO/tools/nnue/forge_nnue_v2.py" from-inc "$REPO/src/nnue_weights.inc" "$OUT/lock_r1_t0.fnn2" --replica r1 --threats-zero
echo "===== 1. lock (A) vs O6 NNUEThreats 1 with the zero-threat lock replica (B): identical trees"
nice -n 19 python "$REPO/opus_round1/C4/nps_ab_options.py" "$LOCK" "$EXE" "$RUNS" 16,20 --same-nodes \
  --b-set "NNUEFile=$OUT/lock_r1_t0.fnn2" --b-set "NNUEKingBuckets=1" --b-set "NNUEThreats=1"
echo "===== 2. lock (A) vs O6 NNUEThreats 1 with $(basename "$NET") (B): another tree"
nice -n 19 python "$REPO/opus_round1/C4/nps_ab_options.py" "$LOCK" "$EXE" 4 16,20 \
  --b-set "NNUEFile=$NET" --b-set "NNUEKingBuckets=1" --b-set "NNUEThreats=1"
