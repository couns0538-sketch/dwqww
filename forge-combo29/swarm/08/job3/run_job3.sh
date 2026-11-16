#!/usr/bin/env bash
# run_job3.sh — AREA 8 job 3: movestogo 1, 2, 40 with wtime 1000. Guarded like run_clean.sh.
set -u
EXE="$HOME/builds/release/forge"
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"

if pgrep -f 'clock_latency.py|builds/release/forge' >/dev/null; then
  echo "GUARD: another forge/clock_latency process is running; refusing to start"; exit 1
fi
LOAD=$(cut -d' ' -f1 /proc/loadavg)
if awk -v l="$LOAD" 'BEGIN{exit !(l > 0.5)}'; then
  echo "GUARD: load average $LOAD > 0.5; refusing to start"; exit 1
fi
echo "GUARD ok: load $LOAD, no other engine process"

mkdir -p raw
cp ../job1/OG200.fens .
sha256sum "$EXE" > raw/exe_sha256.txt
echo "$EXE" > raw/exe_path.txt
{
  echo "exe_started $EXE"
  echo "sha256 $(cut -d' ' -f1 raw/exe_sha256.txt)"
  printf 'uci\nquit\n' | "$EXE" | grep -E '^id name|^option name (Move Overhead|TmSoftDivisor|TmIncrementPercent|TmHardPercent|TmHardSoftMultiple)'
  echo "options sent: S14 + Threads 1 + Hash 16, Move Overhead left at its default 10, ucinewgame per search"
  echo "guard: load average at start $(cut -d' ' -f1-3 /proc/loadavg), no other engine process"
} > raw/.meta
: > stamps.txt
date -u >> stamps.txt

for mg in 1 2 40; do
  python3 ../job1/clock_latency.py "$EXE" OG200.fens "wtime 1000 btime 1000 movestogo $mg" \
    "raw/mtg${mg}.jsonl" "mtg${mg}" || { echo "FAILED mtg $mg"; exit 2; }
  date -u >> stamps.txt
  echo "done mtg $mg load=$(cut -d' ' -f1 /proc/loadavg)"
done
# the no-movestogo control, re-measured in the same session so the comparison is same-machine same-hour
python3 ../job1/clock_latency.py "$EXE" OG200.fens "wtime 1000 btime 1000 winc 0 binc 0" \
  "raw/mtg_none.jsonl" "mtg_none" || { echo "FAILED control"; exit 2; }
date -u >> stamps.txt
echo DONE_JOB3 >> stamps.txt
