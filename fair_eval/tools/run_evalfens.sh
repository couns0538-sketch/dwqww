#!/usr/bin/env bash
# run_evalfens.sh <diag exe> <fen file> <out tsv> [setoption lines...] - JOB D (own code). Paths as the exe sees them.
set -u
exe="$1"; fens="$2"; out="$3"; shift 3
{
  echo uci
  echo "setoption name Threads value 1"; echo "setoption name Hash value 16"; echo "setoption name OwnBook value false"
  for o in "$@"; do echo "$o"; done
  echo isready
  echo "evalfens $fens $out"
  echo quit
} | "$exe" 2>&1 | grep -a -E "evalfens|EvalFileV2|ERROR|invalid" | cut -c1-200
