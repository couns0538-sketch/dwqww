#!/usr/bin/env bash
# run_clean.sh — re-runs job 1 and job 2 with a hard guard: refuses to start if any other forge or
# clock_latency process exists, and refuses if the load average is above 0.5. Writes into fresh
# directories (raw2) so the contaminated run is preserved, not overwritten.
set -u
EXE="$HOME/builds/release/forge"
B="$(cd "$(dirname "$0")/.." && pwd)"   # forge-combo29/swarm/08
cd "$B"

if pgrep -f 'clock_latency.py|builds/release/forge' >/dev/null; then
  echo "GUARD: another forge/clock_latency process is running; refusing to start"; exit 1
fi
LOAD=$(cut -d' ' -f1 /proc/loadavg)
if awk -v l="$LOAD" 'BEGIN{exit !(l > 0.5)}'; then
  echo "GUARD: load average $LOAD > 0.5; refusing to start"; exit 1
fi
echo "GUARD ok: load $LOAD, no other engine process"
date -u > job1/stamps2.txt
date -u > job2/stamps2.txt

mkdir -p job1/raw2 job2/raw2
sha256sum "$EXE" > job1/raw2/exe_sha256.txt
cp job1/raw2/exe_sha256.txt job2/raw2/exe_sha256.txt
echo "$EXE" > job1/raw2/exe_path.txt
{
  echo "exe_started $EXE"
  echo "sha256 $(cut -d' ' -f1 job1/raw2/exe_sha256.txt)"
  printf 'uci\nquit\n' | "$EXE" | grep -E '^id name|^option name (Hash|Threads|Move Overhead)'
  echo "options sent: S14 (LmrQuietBase 93, LmrQuietDivisor 205, LmrNoisyBase 13, LmrNoisyDivisor 333,"
  echo "              LmrHistoryDivisor 5643, NullMoveBase 5, LmpBase 8, HistoryPruneMultiplier 2220,"
  echo "              HistoryBonusQuadratic 24, HistoryBonusLinear 54, HistoryBonusMax 2212,"
  echo "              SingularDepth 6, IirDepth 2, NonPawnCorrection true)"
  echo "              + Threads 1 + Hash 16 + ucinewgame before every search"
  echo "guard: no other engine process, load average below 0.5 at start"
  echo "run under: /proc/loadavg at start = $(cut -d' ' -f1-3 /proc/loadavg)"
} > job1/raw2/.meta
cp job1/raw2/.meta job2/raw2/.meta

cd "$B/job1"
for spec in "base_a|movetime 50" "base_b|movetime 50" "mt500|movetime 500" \
            "tc1000|wtime 1000 btime 1000 winc 10 binc 10" \
            "tc10000|wtime 10000 btime 10000 winc 100 binc 100"; do
  name="${spec%%|*}"; mode="${spec#*|}"
  python3 clock_latency.py "$EXE" OG200.fens "$mode" "raw2/${name}.jsonl" "$name" || { echo "FAILED $name"; exit 2; }
  date -u >> stamps2.txt
  echo "job1 done $name  load=$(cut -d' ' -f1 /proc/loadavg)"
done
echo DONE_JOB1 >> stamps2.txt

cd "$B/job2"
for t in 100 30 10 1 0; do
  for inc in 0 10; do
    python3 ../job1/clock_latency.py "$EXE" OG200.fens "wtime $t btime $t winc $inc binc $inc" \
      "raw2/w${t}_i${inc}.jsonl" "w${t}i${inc}" || { echo "FAILED w${t} i${inc}"; exit 2; }
    date -u >> stamps2.txt
  done
done
echo DONE_JOB2 >> stamps2.txt
echo "job2 done, load=$(cut -d' ' -f1 /proc/loadavg)"
