#!/usr/bin/env bash
# O4 local speed evidence on the shared PC (machine exclusive: no; nice 19, one thread, no torch):
#   1. evaluation cost on identical walks (forge_nnue_engine_eval --walk, 3M plies, 3 interleaved rounds):
#      compiled-in default (HCE + lock net), lock replica r1 through the v2 path (HCE + lock net) and the same
#      weights flagged stand-alone with PureNnue (lock net alone): r1 vs stand-alone isolates the HCE's cost;
#   2. bench NPS at depth 16 / 20 (opus_round1/C4/nps_ab_options.py, ABBA, fresh processes): O4 options off vs
#      O4 PureNnue with <pure_net.fnn2> (another evaluation searches another tree: nodes are reported).
# usage: local_nps.sh <out_dir> <forge_exe> <forge_nnue_engine_eval_exe> <pure_net.fnn2> [runs (default 10)]
set -uo pipefail
REPO=$(cd "$(dirname "$0")/../.." && pwd)
mixed() { if command -v cygpath > /dev/null; then cygpath -m "$1"; else echo "$1"; fi; }
OUT=$(mixed "$1"); FORGE=$(mixed "$2"); TOOL=$(mixed "$3"); NET=$(mixed "$4"); RUNS=${5:-10}
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT"
echo "machine exclusive: no"
python "$REPO/tools/nnue/forge_nnue_v2.py" from-inc "$REPO/src/nnue_weights.inc" "$OUT/lock_r1.fnn2" --replica r1
python "$REPO/opus_round1/O4/standalone_copy.py" "$OUT/lock_r1.fnn2" "$OUT/lock_r1_standalone.fnn2"
echo "===== 1. evaluation cost, identical walks"
for round in 1 2 3; do
  for cfg in default residual pure; do
    case $cfg in
      default) set -- ;;
      residual) set -- "NNUEFile=$OUT/lock_r1.fnn2" NNUEKingBuckets=1 ;;
      pure) set -- "NNUEFile=$OUT/lock_r1_standalone.fnn2" PureNnue=1 ;;
    esac
    echo "round $round $cfg: $(nice -n 19 "$TOOL" --walk 3000000 20261027 "$@" | grep '^walk')"
  done
done
echo "===== 2. bench NPS, O4 off (A) vs O4 PureNnue + $(basename "$NET") (B)"
nice -n 19 python "$REPO/opus_round1/C4/nps_ab_options.py" "$FORGE" "$FORGE" "$RUNS" 16,20 --b-set "NNUEFile=$NET" --b-set "PureNnue=1"
