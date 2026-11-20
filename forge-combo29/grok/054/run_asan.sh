#!/usr/bin/env bash
# Same runner for the sanitizer proof and the deliberate-error proof.
# usage: run_asan.sh <exe> <fen-file> <depth> <out-prefix> [extra Name=value] [limit]
set -u
EXE="$1"
FENS="$2"
DEPTH="$3"
OUT="$4"
EXTRA="${5:-}"
LIMIT="${6:-0}"
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
COUNT=$(nm -C "$EXE" | grep -c __asan_ || true)
echo "nm_asan_count ${COUNT}"
ARGS=(python3 "forge-combo29/grok/$S/search_set.py" --exe "$EXE" --fens "$FENS" --depth "$DEPTH" --out "$OUT")
if [ "$LIMIT" != "0" ]; then
  ARGS+=(--limit "$LIMIT")
fi
if [ -n "$EXTRA" ]; then
  ARGS+=(--extra "$EXTRA")
fi
set +e
"${ARGS[@]}"
CODE=$?
set -e
{
  echo "nm -C ${EXE} | grep -c __asan_ ${COUNT}"
  echo "runner_exit ${CODE}"
} >> "${OUT}.meta"
echo "runner_exit ${CODE}"
exit "$CODE"
