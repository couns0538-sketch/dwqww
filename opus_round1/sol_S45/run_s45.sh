#!/usr/bin/env bash
# S45 runs (nice 19; the tool runs one compiler or engine process at a time; free RAM >= 6 GB checked before
# each base). Writes only under $OUT.
#   AL1     = the lock tree (d4f4312) as is: the base that confirmed (G120 H1 + G120c H1) -> the real run.
#   e48f006 = the same tree with the e48f006 net: dry run (G104 H1, G104c cap no decision); bench refs from the spec.
#   e48f029 = the same tree with the e48f029 net: dry run (A-e48f029 H1 + confirm H1 vs h256_e12, never locked).
# usage: run_s45.sh <job_dir> <base_tree> <nets_dir> <out_dir>
set -uo pipefail
J=$1; BASE=$2; NETS=$3; OUT=$4
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
T=$J/forge_sol_S45_rebase_ready.py
mkdir -p "$OUT"
free_gb() { powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)"; }
need_ram() { local f; f=$(free_gb); echo "free RAM ${f} GB before: $1"; awk -v f="$f" 'BEGIN{exit !(f>=6.0)}' || { echo "free RAM below 6 GB, stop"; exit 3; }; }
echo "# S45 runs $(date); machine exclusive: no (gate + self-play + training running); nice 19"
need_ram "base AL1"
nice -n 19 $PY -I -B $T run --config $J/candidates_20261027.json --base-name "AL1 s198 (lock, confirmed)" --base-tree "$BASE" \
  --base-ref 312866,862329,3024920,12389307,34048354 --work "$OUT/work_al1" --out-json "$OUT/rebase_al1.json" --out-md "$OUT/rebase_al1.md"
need_ram "base e48f006"
nice -n 19 $PY -I -B $T run --config $J/candidates_20261027.json --base-name "e48f006 on the AL1 tree (dry run)" --base-tree "$BASE" \
  --net "$NETS/e48f006.inc" --base-ref 328459,945640,3024381,9162399,20421972 --work "$OUT/work_e48f006" \
  --out-json "$OUT/rebase_e48f006.json" --out-md "$OUT/rebase_e48f006.md"
need_ram "base e48f029"
nice -n 19 $PY -I -B $T run --config $J/candidates_20261027.json --base-name "e48f029 on the AL1 tree (dry run)" --base-tree "$BASE" \
  --net "$NETS/e48f029.inc" --work "$OUT/work_e48f029" --out-json "$OUT/rebase_e48f029.json" --out-md "$OUT/rebase_e48f029.md"
echo "# done $(date)"
