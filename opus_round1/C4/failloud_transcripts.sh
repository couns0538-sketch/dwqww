#!/usr/bin/env bash
# Engine transcripts for the fail-loud rule (produced logs/failloud_transcripts.log): stdin script, stdout (uci option list
# elided) and exit status per case.
# usage: failloud_transcripts.sh <engine.exe> <valid_net.fnn2> <work_dir> [kb]
set -u
EXE=$1; NET=$2; WORK=$3; KB=${4:-4}
mkdir -p "$WORK"
cd "$WORK" || exit 1
head -c $(( $(stat -c %s "$NET") - 2 )) "$NET" > truncated.fnn2
show() { # title script
  echo "=================================================================="
  echo "# $1"
  echo "## stdin"
  printf '%s' "$2" | sed 's/^/> /'
  printf '%s' "$2" > in.txt
  "$EXE" < in.txt > out.txt 2> err.txt
  local rc=$?
  echo "## stdout (id/option lines of 'uci' elided)"
  grep -vE '^(id |option name )' out.txt | sed 's/^/< /'
  [ -s err.txt ] && { echo "## stderr"; sed 's/^/! /' err.txt; }
  echo "## exit status $rc"
}
H=$'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n'
show "defaults (no NNUE option): nothing new, exit 0" "${H}isready"$'\ngo depth 5\nisready\nquit\n'
show "NNUEFile missing: ERROR at once and at isready, exit 2 (no readyok)" "${H}setoption name NNUEFile value missing.fnn2"$'\n'"setoption name NNUEKingBuckets value $KB"$'\nisready\ngo depth 5\nquit\n'
show "NNUEFile truncated by 2 bytes: rejected by the size check, exit 2 at go (no bestmove)" "${H}setoption name NNUEFile value truncated.fnn2"$'\n'"setoption name NNUEKingBuckets value $KB"$'\ngo depth 5\nquit\n'
show "wrong king bucket count (NNUEKingBuckets 8 for a $KB-bucket net): exit 2 at isready" "${H}setoption name NNUEFile value $NET"$'\nsetoption name NNUEKingBuckets value 8\nisready\nquit\n'
show "NNUEKingBuckets $KB without NNUEFile: exit 2 at bench" "${H}setoption name NNUEKingBuckets value $KB"$'\nbench 5\nquit\n'
show "valid net, then a failed reload (old behaviour: kept the old net silently): exit 2" "${H}setoption name NNUEFile value $NET"$'\n'"setoption name NNUEKingBuckets value $KB"$'\nisready\nsetoption name NNUEFile value missing.fnn2\nisready\nquit\n'
show "valid net: active line at activation and at every isready, exit 0" "${H}setoption name NNUEFile value $NET"$'\n'"setoption name NNUEKingBuckets value $KB"$'\nisready\ngo depth 5\nisready\nquit\n'
show "UseNNUE false with a v2 request: not an error (hand-crafted eval only), exit 0" "${H}setoption name UseNNUE value false"$'\n'"setoption name NNUEFile value missing.fnn2"$'\n'"setoption name NNUEKingBuckets value $KB"$'\nisready\ngo depth 5\nquit\n'
show "request cleared (NNUEKingBuckets 0, NNUEFile <empty>): compiled-in net, exit 0" "${H}setoption name NNUEFile value $NET"$'\n'"setoption name NNUEKingBuckets value $KB"$'\nsetoption name NNUEKingBuckets value 0\nsetoption name NNUEFile value <empty>\nisready\ngo depth 5\nquit\n'
