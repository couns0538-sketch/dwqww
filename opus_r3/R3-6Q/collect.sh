#!/usr/bin/env bash
# R3-6Q: download the artifacts of one opus-r3-smpq run and summarise them locally (Windows PC, Git Bash).
# Each artifact goes into its own new directory under <dest> (untrusted data); report_q.py runs with -I -B.
# usage (from inside the opus_r3_smpq worktree): bash opus_r3/R3-6Q/collect.sh <run_id> <dest_dir>
set -euo pipefail
RUN=$1; DEST=$2
PY=${PY:-C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
H=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$DEST"
gh run view "$RUN" --json status,conclusion,jobs --jq '.status, .conclusion, (.jobs[] | "\(.name) \(.status) \(.conclusion)")'
for a in smpq-prep smpq-rep1 smpq-rep2 smpq-rep3 smpq-summary; do
  [ -d "$DEST/$a" ] || gh run download "$RUN" -n "$a" -D "$DEST/$a" || echo "artifact $a not available"
done
files=()
for r in 1 2 3; do [ -f "$DEST/smpq-rep$r/ttd_rep$r.jsonl" ] && files+=("$DEST/smpq-rep$r/ttd_rep$r.jsonl"); done
wc -l "${files[@]}"
nice -n 19 "$PY" -I -B "$H/report_q.py" "${files[@]}" > "$DEST/summary_local.md"
echo "wrote $DEST/summary_local.md"
