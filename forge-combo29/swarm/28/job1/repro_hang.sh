#!/usr/bin/env bash
# repro_hang.sh EXE N — replay the first N positions of O.fens exactly as timing.py does
# (ucinewgame, isready, position fen, go movetime 50) in ONE process, with a 25 s watchdog per search.
set -u
EXE=${1:-$HOME/build/base-release/forge}
N=${2:-4}
HERE=$(dirname "$(readlink -f "$0")")
{
  echo uci; echo isready
  echo "setoption name Threads value 1"; echo isready
  echo "setoption name Hash value 16"; echo isready
  head -n "$N" "$HERE/O.fens" | while read -r fen; do
    echo ucinewgame; echo isready
    echo "position fen $fen"
    echo "go movetime 50"
  done
  echo quit
} | timeout 25 "$EXE" 2>&1 | grep -E 'bestmove|readyok|Illegal|error' | tail -20
echo "pipeline exit=$?"
