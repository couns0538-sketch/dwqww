#!/usr/bin/env bash
# R3-1L: collect one run of the opus-r3-sp-linux workflow on the PC. Downloads every sp-* artifact not yet in
# F:/opus_scratch/r3/R3-1L/run_<id>/arts (finished jobs only: run it again to add later ones), rebuilds the summary
# table with summarize.py (jobs still running show "no artifact") and copies the small evidence of each job
# (job.tsv, builds, matrix log, MATRIX.md, per-config summaries, matrix_summary.json with the sha256 of the big
# logs) into opus_r3/R3-1L/logs/run_<id>/. The big logs (games.jsonl, pgn, transcripts) stay in F:/opus_scratch.
# usage (Git Bash, from the opus-r3-sp-linux worktree): bash opus_r3/R3-1L/collect.sh <run id> [python exe]
set -uo pipefail
RUN=$1
PY=${2:-C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
ARTS=/f/opus_scratch/r3/R3-1L/run_$RUN/arts
EV=$ROOT/opus_r3/R3-1L/logs/run_$RUN
mkdir -p "$ARTS" "$EV"
gh api "repos/{owner}/{repo}/actions/runs/$RUN" --jq '"run \(.id) \(.name) head \(.head_sha) status \(.status) conclusion \(.conclusion) created \(.created_at) updated \(.updated_at)"' > "$EV/run_state.txt"
gh api "repos/{owner}/{repo}/actions/runs/$RUN/jobs?per_page=100" --jq '.jobs[] | "\(.name)\t\(.status)\t\(.conclusion)\t\(.started_at)\t\(.completed_at)"' >> "$EV/run_state.txt"
for name in $(gh api "repos/{owner}/{repo}/actions/runs/$RUN/artifacts?per_page=100" --jq '.artifacts[].name'); do
  [ -d "$ARTS/$name" ] && continue
  gh run download "$RUN" -n "$name" -D "$ARTS/$name" || echo "download failed: $name"
done
nice -n 19 "$PY" -I -B "$ROOT/opus_r3/R3-1L/summarize.py" --jobs "$ROOT/opus_r3/R3-1L/jobs.json" --arts "$ARTS" --out "$EV" > /dev/null
rc=$?
for d in "$ARTS"/sp-*/; do
  j=$(basename "$d")
  if [ "$j" = sp-summary ]; then
    mkdir -p "$EV/summary_job"; cp "$d"/SUMMARY.md "$d"/summary.json "$EV/summary_job/" 2>/dev/null; continue
  fi
  mkdir -p "$EV/$j"
  cp "$d"/job.tsv "$d"/builds.tsv "$d"/job_configs.json "$EV/$j/" 2>/dev/null
  cp "$d"/logs/builds.txt "$d"/logs/job.log "$d"/logs/make_nets.log "$EV/$j/" 2>/dev/null
  cp "$d"/runs/MATRIX.md "$d"/runs/matrix.log "$d"/runs/matrix_summary.json "$d"/runs/*.summary.json "$EV/$j/" 2>/dev/null
  [ -d "$d/sanitizer_logs" ] && [ -n "$(ls -A "$d/sanitizer_logs" 2>/dev/null)" ] && cp -r "$d/sanitizer_logs" "$EV/$j/"
done
echo "run $RUN: $(grep -c . "$EV/run_state.txt") state lines; table $EV/SUMMARY.md (summarize exit $rc: 0 = every expected row PASS)"
exit $rc
