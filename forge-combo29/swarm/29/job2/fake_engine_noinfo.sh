#!/usr/bin/env bash
# PLANT for the measurement-integrity check: answers uci/isready normally but replies to any `go` with a bare
# `bestmove a2a3` and NO `info depth` line -- the exact fabricated-answer shape seat 19 reported.
while IFS= read -r line; do
  case "$line" in
    uci) echo "id name PLANT no-info fake"; echo "uciok" ;;
    isready) echo readyok ;;
    go*) echo "bestmove a2a3" ;;
    quit) exit 0 ;;
  esac
done
