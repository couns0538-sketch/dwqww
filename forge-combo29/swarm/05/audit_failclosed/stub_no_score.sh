#!/usr/bin/env bash
# stub_no_score.sh — a fake "engine" for the missing-parse negative control.
# It answers UCI correctly but NEVER emits an `info ... pv ... score` line, so any parser looking for a score
# finds nothing. It always answers "bestmove 0000".
while IFS= read -r line; do
  case "$line" in
    uci) printf 'id name STUB no-score engine\nuciok\n' ;;
    isready) printf 'readyok\n' ;;
    position*) : ;;
    go*) printf 'bestmove 0000\n' ;;
    quit) exit 0 ;;
    *) : ;;
  esac
done
