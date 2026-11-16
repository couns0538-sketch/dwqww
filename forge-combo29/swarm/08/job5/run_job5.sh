#!/usr/bin/env bash
# run_job5.sh — the clock-tail scaling sweep. Guarded; OwnBook false; 200 searches per clock.
set -u
EXE="$HOME/builds/release/forge"
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"

if pgrep -f 'clock_latency|builds/release/forge' >/dev/null; then
  echo "GUARD: another engine process is running; refusing to start"; exit 1
fi
LOAD=$(cut -d' ' -f1 /proc/loadavg)
if awk -v l="$LOAD" 'BEGIN{exit !(l > 0.5)}'; then
  echo "GUARD: load $LOAD > 0.5; refusing to start"; exit 1
fi
echo "GUARD ok: load $LOAD, no other engine process"

mkdir -p raw
cp ../job1/OG200.fens .
sha256sum "$EXE" > raw/exe_sha256.txt
{
  echo "exe_started $EXE"
  echo "sha256 $(cut -d' ' -f1 raw/exe_sha256.txt)"
  printf 'uci\nquit\n' | "$EXE" | grep -E '^id name|^option name (Hash|Threads|OwnBook|Move Overhead|TmSoftDivisor)'
  echo "options sent: S14 + Threads 1 + Hash 16 + OwnBook false + ucinewgame per search; Move Overhead default 10"
  echo "guard: load at start $(cut -d' ' -f1-3 /proc/loadavg), no other engine process"
} > raw/.meta
: > stamps.txt
date -u >> stamps.txt
for t in 200 500 1000 3000 10000 30000; do
  python3 ../job1b/clock_latency2.py "$EXE" OG200.fens "wtime $t btime $t winc 0 binc 0" "raw/t${t}.jsonl" "t${t}" \
    || { echo "FAILED t$t"; exit 2; }
  date -u >> stamps.txt
  echo "done t$t load=$(cut -d' ' -f1 /proc/loadavg)"
done
echo DONE_JOB5 >> stamps.txt
