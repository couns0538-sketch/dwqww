#!/usr/bin/env bash
# R3-6Q: one repetition of the time-to-depth matrix on a GitHub runner: all 30 positions,
#   off  = defaults                     Threads 1,2,3
#   on   = SmpExactNodes + SmpBestThread + LocklessTT        Threads 1,2,3
#   offP = off + SmpHelpersPastDepth    Threads 2,3 (inert at Threads 1)
#   onP  = on  + SmpHelpersPastDepth    Threads 2,3
# Hash 64, one fresh process per run, positions and (config, threads) runs shuffled (seed 6, rep).
# usage: ci_matrix.sh <forge> <out_dir> <rep 1..3> [depth_offset] [deadline_s]
set -euo pipefail
F=$1; OUT=$2; REP=$3; OFF=${4:-0}; DL=${5:-2700}
H=$(cd "$(dirname "$0")" && pwd)
ON="SmpExactNodes=true,SmpBestThread=true,LocklessTT=true"
mkdir -p "$OUT"
{ echo "rep: $REP"; echo "depth_offset: $OFF"; echo "nproc: $(nproc)"; lscpu; echo; uptime;
  echo "forge sha256: $(sha256sum "$F" | cut -d' ' -f1)"; } > "$OUT/runner_rep$REP.txt"
grep -E '^(nproc|Model name|Thread\(s\) per core|Core\(s\) per socket|CPU\(s\)|forge)' "$OUT/runner_rep$REP.txt" || true
python3 "$H/smp_ttd_linux.py" --positions "$H/../R3-6/positions30.tsv" \
  --config "off=$F" --config "on=$F|$ON" \
  --config "offP=$F|SmpHelpersPastDepth=true" --config "onP=$F|$ON,SmpHelpersPastDepth=true" \
  --config-threads offP=2,3 --config-threads onP=2,3 --threads 1,2,3 \
  --rep $((REP - 1)) --hash 64 --seed 6 --depth-offset "$OFF" --deadline-s "$DL" \
  --out "$OUT/ttd_rep$REP.jsonl" 2>&1 | tee "$OUT/ttd_rep$REP.log"
{ echo; uptime; } >> "$OUT/runner_rep$REP.txt"
