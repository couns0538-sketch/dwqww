#!/usr/bin/env bash
# S45 extra dry run: the Opus O/C candidates (all built on AL1 d4f4312) rebuilt on the e48f006 base (AL1 tree + the
# e48f006 net). nice 19, one compiler or engine process at a time (the tool), free RAM >= 6 GB checked first.
# Patches: regenerate with  git diff d4f4312 <commit> -- src include tests CMakeLists.txt  (sha256 pinned in the config).
# usage: run_s45_opus.sh <job_dir> <base_tree> <nets_dir> <out_dir>
set -uo pipefail
J=$1; BASE=$2; NETS=$3; OUT=$4
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
mkdir -p "$OUT"
f=$(powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)")
echo "# S45 Opus candidates on e48f006 (dry run) $(date); machine exclusive: no; nice 19; free RAM ${f} GB"
awk -v f="$f" 'BEGIN{exit !(f>=6.0)}' || { echo "free RAM below 6 GB, stop"; exit 3; }
nice -n 19 $PY -I -B $J/forge_sol_S45_rebase_ready.py run --config $J/candidates_opus_20261027.json \
  --base-name "e48f006 on the AL1 tree (dry run, Opus candidates)" --base-tree "$BASE" --net "$NETS/e48f006.inc" \
  --base-ref 328459,945640,3024381,9162399,20421972 --work "$OUT/work_opus_e48f006" \
  --out-json "$OUT/rebase_opus_e48f006.json" --out-md "$OUT/rebase_opus_e48f006.md"
echo "# done $(date)"
