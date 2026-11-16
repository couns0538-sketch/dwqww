#!/usr/bin/env bash
# run_job1.sh — seat 08 area 8 job 1: 200 searches x 4 time controls, movetime-50 baseline twice first.
set -u
EXE="$HOME/builds/release/forge"
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"
mkdir -p raw
# first 100 of O and of G
head -100 first200.fens > O100.fens
head -100 set_G.epd | cut -d' ' -f1-6 > G100.fens
wc -l O100.fens G100.fens > raw/setup_counts.txt
cat O100.fens G100.fens > OG200.fens
sha256sum "$EXE" > raw/exe_sha256.txt
echo "$EXE" > raw/exe_path.txt
{
  echo "exe_started $EXE"
  echo "sha256 $(cut -d' ' -f1 raw/exe_sha256.txt)"
  printf 'uci\nquit\n' | "$EXE" | grep -E '^id name|^option name (Hash|Threads)'
  echo "options sent: S14 (14 setoption lines) + Threads 1 + Hash 16 + ucinewgame per search"
} > raw/.meta
date -u >> stamps.txt

# two identical baseline runs first (movetime 50), so their difference can be reported
python3 clock_latency.py "$EXE" OG200.fens "movetime 50" raw/base_mt50_a.jsonl "base_a" && date -u >> stamps.txt
python3 clock_latency.py "$EXE" OG200.fens "movetime 50" raw/base_mt50_b.jsonl "base_b" && date -u >> stamps.txt
python3 clock_latency.py "$EXE" OG200.fens "movetime 500" raw/mt500.jsonl "mt500" && date -u >> stamps.txt
python3 clock_latency.py "$EXE" OG200.fens "wtime 1000 btime 1000 winc 10 binc 10" raw/tc1000.jsonl "tc1000" && date -u >> stamps.txt
python3 clock_latency.py "$EXE" OG200.fens "wtime 10000 btime 10000 winc 100 binc 100" raw/tc10000.jsonl "tc10000" && date -u >> stamps.txt
echo DONE_JOB1_RUN >> stamps.txt
