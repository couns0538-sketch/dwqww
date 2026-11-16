#!/usr/bin/env bash
# run_job1b.sh — AREA 8 job 1 AGAIN, SEED 811, OwnBook false. Guarded.
set -u
EXE="$HOME/builds/release/forge"
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"

if pgrep -f 'clock_latency|builds/release/forge' >/dev/null; then
  echo "GUARD: another engine process is running; refusing to start"; exit 1
fi
LOAD=$(cut -d' ' -f1 /proc/loadavg)
if awk -v l="$LOAD" 'BEGIN{exit !(l > 0.5)}'; then
  echo "GUARD: load average $LOAD > 0.5; refusing to start"; exit 1
fi
echo "GUARD ok: load $LOAD, no other engine process"

mkdir -p raw
# SEED 811 -> new R set
python3 ../job1/gen_R.py 811 500 R_seed811.fens 2>&1 | tail -1
# first 100 of O + first 100 of G as before, then the new R's first 100 replacing G in the mix
cp ../job1/O100.fens .

head -100 ../job1/set_G.epd | cut -d' ' -f1-6 > G100.fens
head -100 R_seed811.fens > R100.fens
cat O100.fens G100.fens > OG200.fens
cat O100.fens R100.fens > OR200.fens
wc -l O100.fens G100.fens R100.fens OG200.fens OR200.fens > raw/setup_counts.txt

sha256sum "$EXE" > raw/exe_sha256.txt
echo "$EXE" > raw/exe_path.txt
{
  echo "exe_started $EXE"
  echo "sha256 $(cut -d' ' -f1 raw/exe_sha256.txt)"
  printf 'uci\nquit\n' | "$EXE" | grep -E '^id name|^option name (Hash|Threads|OwnBook|Move Overhead)'
  echo "options sent: S14 + Threads 1 + Hash 16 + OwnBook false (every search) + ucinewgame per search"
  echo "seed 811 for the R set; S14 is the same as run 1 so differences are the position set and noise"
  echo "guard: load at start $(cut -d' ' -f1-3 /proc/loadavg), no other engine process"
} > raw/.meta
: > stamps.txt
date -u >> stamps.txt

python3 clock_latency2.py "$EXE" OG200.fens "movetime 50" raw/OG_baseA.jsonl "OG_baseA" && date -u >> stamps.txt
python3 clock_latency2.py "$EXE" OG200.fens "movetime 50" raw/OG_baseB.jsonl "OG_baseB" && date -u >> stamps.txt
python3 clock_latency2.py "$EXE" OG200.fens "movetime 500" raw/OG_mt500.jsonl "OG_mt500" && date -u >> stamps.txt
python3 clock_latency2.py "$EXE" OG200.fens "wtime 1000 btime 1000 winc 10 binc 10" raw/OG_tc1000.jsonl "OG_tc1000" && date -u >> stamps.txt
python3 clock_latency2.py "$EXE" OG200.fens "wtime 10000 btime 10000 winc 100 binc 100" raw/OG_tc10000.jsonl "OG_tc10000" && date -u >> stamps.txt
# the new-set half: O + the NEW R set, same four controls at the two movetime points plus the 1 s clock
python3 clock_latency2.py "$EXE" OR200.fens "movetime 50" raw/OR_mt50.jsonl "OR_mt50" && date -u >> stamps.txt
python3 clock_latency2.py "$EXE" OR200.fens "wtime 1000 btime 1000 winc 10 binc 10" raw/OR_tc1000.jsonl "OR_tc1000" && date -u >> stamps.txt
echo DONE_JOB1B >> stamps.txt
