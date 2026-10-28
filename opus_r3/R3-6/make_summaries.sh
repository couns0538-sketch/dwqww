#!/usr/bin/env bash
# R3-6: regenerate the summary tables and per-position / per-run TSVs from the raw run files.
# usage: make_summaries.sh <run_dir with ttd_main.jsonl and ttd_trace.jsonl> <out_dir (job logs/)>
set -euo pipefail
R=$1; O=$2
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
H=$(cd "$(dirname "$0")" && pwd)
nice -n 19 "$PY" -I -B "$H/summarize.py" "$R/ttd_main.jsonl" --by-class \
  --t1-from offP=off --t1-from onP=on \
  --pair on:off --pair on2:off --pair offP:off --pair onP:on --pair onP:off \
  --tsv "$O/ttd_per_position.tsv" > "$O/ttd_summary.md"
nice -n 19 "$PY" -I -B "$H/trace_summary.py" "$R/ttd_trace.jsonl" --tsv "$O/trace_per_run.tsv" > "$O/trace_summary.md"
echo "wrote $O/ttd_summary.md $O/ttd_per_position.tsv $O/trace_summary.md $O/trace_per_run.tsv"
