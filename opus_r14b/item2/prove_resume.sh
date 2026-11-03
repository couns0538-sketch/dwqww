#!/usr/bin/env bash
# prove_resume.sh STEP BASE_DIR - Opus R14-B item 2: the 1M-row kill / resume proof of relabel2.py, step by step
# (each step is one command so that a kill can be done from outside between steps; nothing is deleted).
#   prepare : two identical jobs A and B from the same self-play files, whole games, <= 1,000,000 rows
#   runA    : job A uninterrupted (1 probe, CPU 2 = mask 0x4, Idle)
#   runB1   : job B, first session; it hard-exits itself after KILL1_S seconds (os._exit from a watchdog thread at an
#             arbitrary point: no cleanup, no flush - like TerminateProcess)
#   runB2   : job B, second session, same with KILL2_S (the second kill)
#   runB    : job B, the session that resumes to the end
#   (An external stop is not used: on this PC `kill` / Stop-Process are blocked by the session permissions, and
#   stopping a background task ends only its outer shell, so the Python process would keep running.)
#   finish  : assemble A and B, compare the md5 of train.txt / val.txt / labels.tsv, list the kept interrupted attempts
# Settings: 20,000 nodes, Hash 1 MB, 1 thread per probe (the R13 job1 settings), shards of 10,000 rows.
set -u
step=${1:?step}
base=${2:?base dir}
PY=${PY:-/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
R=$(cd "$(dirname "$0")" && pwd)/relabel2.py
P=${PROBE:-'C:\o13\p5\forge_data_probe.exe'}
SP=/d/grok-pc-data/selfplay_out
NODES=${NODES:-20000}
case $step in
  prepare)
    mkdir -p "$base"
    for j in A B; do
      "$PY" -I -B "$R" prepare --job "$base/job$j" --run-id "r14b-proof-$j" --rows 1000000 \
        --selfplay "$SP/forge_selfplay_001.txt" "$SP/forge_selfplay_002.txt" "$SP/forge_selfplay_003.txt" \
        "$SP/forge_selfplay_004.txt" || exit $?
    done
    cmp "$base/jobA/rows.tsv" "$base/jobB/rows.tsv" && echo "rows.tsv A = B" ;;
  runA)
    "$PY" -I -B "$R" run --job "$base/jobA" --run-id r14b-proof-A --probe "$P" --nodes "$NODES" --workers 1 --mask 0x4 ;;
  runB1)
    "$PY" -I -B "$R" run --job "$base/jobB" --run-id r14b-proof-B --probe "$P" --nodes "$NODES" --workers 1 --mask 0x8 \
      --test-kill-after-seconds "${KILL1_S:?KILL1_S}"
    echo "runB1 exit=$? (137 = the planned hard exit)" ;;
  runB2)
    "$PY" -I -B "$R" run --job "$base/jobB" --run-id r14b-proof-B --probe "$P" --nodes "$NODES" --workers 1 --mask 0x8 \
      --test-kill-after-seconds "${KILL2_S:?KILL2_S}"
    echo "runB2 exit=$? (137 = the planned hard exit)" ;;
  runB)
    "$PY" -I -B "$R" run --job "$base/jobB" --run-id r14b-proof-B --probe "$P" --nodes "$NODES" --workers 1 --mask 0x8 ;;
  finish)
    for j in A B; do "$PY" -I -B "$R" assemble --job "$base/job$j" --run-id "r14b-proof-$j" || exit $?; done
    differ=0
    for f in train.txt val.txt labels.tsv; do
      a=$(md5sum < "$base/jobA/final/$f" | cut -c1-32); b=$(md5sum < "$base/jobB/final/$f" | cut -c1-32)
      echo "$f A=$a B=$b $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
      [ "$a" = "$b" ] || differ=$((differ + 1))
    done
    "$PY" -I -B "$R" status --job "$base/jobB" | tail -1
    grep -h 'run start\|run end' "$base/jobB/sessions.log"
    exit $((differ > 0)) ;;  # DIFFERENT used to end with exit 0 (bug hunt #15)
  *) echo "unknown step $step" >&2; exit 2 ;;
esac
