#!/usr/bin/env bash
# run_job2.sh — AREA 8 job 2: very little time. wtime/btime 100/30/10/1/0 with winc 0 and 10.
set -u
EXE="$HOME/builds/release/forge"
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"
mkdir -p raw
cp ../job1/OG200.fens .
sha256sum "$EXE" > raw/exe_sha256.txt
echo "$EXE" > raw/exe_path.txt
{
  echo "exe_started $EXE"
  echo "sha256 $(cut -d' ' -f1 raw/exe_sha256.txt)"
  printf 'uci\nquit\n' | "$EXE" | grep -E '^id name|^option name (Hash|Threads|Move Overhead)'
  echo "options sent: S14 + Threads 1 + Hash 16 (Move Overhead left at its default 10) + ucinewgame per search"
} > raw/.meta
: > stamps.txt
date -u >> stamps.txt
for t in 100 30 10 1 0; do
  for inc in 0 10; do
    python3 ../job1/clock_latency.py "$EXE" OG200.fens "wtime $t btime $t winc $inc binc $inc" \
      "raw/w${t}_i${inc}.jsonl" "w${t}i${inc}" || echo "RUN FAILED w${t} i${inc}" >> run.log
    date -u >> stamps.txt
    echo "done w${t} i${inc}" >> run.log
  done
done
echo DONE_JOB2_RUN >> stamps.txt
