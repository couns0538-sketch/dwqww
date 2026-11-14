#!/usr/bin/env bash
# Sequential UHO chunks. Does not modify engine source.
set -u
ROOT=/agent/repos/dwqww
TEST="$ROOT/forge-combo29/tests_r4_04"
EXE="$ROOT/forge-combo29/build/forge"
FC=/tmp/r4_04/fastchess-linux-x86-64/fastchess
BOOK=/tmp/r4_04/UHO_Lichess_4852_v1.epd
BUDGET=$((6 * 3600))
HARD=$((9 * 3600))

cd "$ROOT"
mkdir -p /tmp/r4_04
echo $$ > /tmp/r4_04/screen_running
trap 'rm -f /tmp/r4_04/screen_running' EXIT

push_repo() {
  "$TEST/push.sh" "$1"
}

date +%s > "$TEST/match_start_epoch"
python3 "$TEST/summarize.py"
chunk=1
start=1
match_start=$(date +%s)
while true; do
  now=$(date +%s)
  elapsed=$((now - match_start))
  if [ "$elapsed" -ge "$BUDGET" ]; then
    echo "budget ${BUDGET}s reached before chunk $chunk"
    break
  fi
  if [ "$elapsed" -ge "$HARD" ]; then
    echo "hard cap reached before chunk $chunk"
    break
  fi
  name=$(printf 'chunk%03d' "$chunk")
  dir="$TEST/$name"
  mkdir -p "$dir"
  {
    echo "status running"
    echo "chunk $chunk"
    echo "start $start"
    echo "rounds 500"
    echo "started_epoch $now"
    echo "started_utc $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$dir/meta.txt"
  echo "BEGIN $name start=$start elapsed=$elapsed"
  (
    cd "$dir"
    stdbuf -oL -eL "$FC" \
      -engine cmd="$EXE" name=ContHist4PlyRead-on nodes=50000 proto=uci restart=on \
        option.Threads=1 option.Hash=16 option.OwnBook=false option.ContHist4PlyRead=true \
      -engine cmd="$EXE" name=ContHist4PlyRead-off nodes=50000 proto=uci restart=on \
        option.Threads=1 option.Hash=16 option.OwnBook=false option.ContHist4PlyRead=false \
      -openings file="$BOOK" format=epd order=sequential start="$start" \
      -rounds 500 -repeat -concurrency 2 -srand 1 \
      -recover -ratinginterval 100 -report penta=true \
      -event "r4-04 ContHist4PlyRead chunk $chunk" -site "screen" \
      -pgnout file=games.pgn notation=san nodes=true \
      -log file=fastchess.log level=warn \
      > stdout.txt 2>&1
  ) &
  fpid=$!
  ec=0
  while kill -0 "$fpid" 2>/dev/null; do
    sleep 20
    if [ $(($(date +%s) - match_start)) -ge "$HARD" ]; then
      echo "hard cap: stopping $name"
      kill "$fpid" 2>/dev/null || true
      sleep 2
      kill -9 "$fpid" 2>/dev/null || true
      ec=75
      break
    fi
  done
  if [ "$ec" -eq 0 ]; then
    wait "$fpid"
    ec=$?
  else
    wait "$fpid" || true
  fi
  ended=$(date +%s)
  {
    echo "status finished"
    echo "chunk $chunk"
    echo "start $start"
    echo "rounds 500"
    echo "exit $ec"
    echo "elapsed_sec $((ended - now))"
    echo "started_utc $(date -u -d "@$now" +%Y-%m-%dT%H:%M:%SZ)"
    echo "ended_utc $(date -u -d "@$ended" +%Y-%m-%dT%H:%M:%SZ)"
  } > "$dir/meta.txt"
  echo "END $name exit=$ec elapsed=$((ended - now))"
  push_repo "r4-04: ContHist4PlyRead screen $name" || echo "push error after $name"
  if [ "$ec" -ne 0 ]; then
    echo "fastchess exit $ec; stopping"
    break
  fi
  chunk=$((chunk + 1))
  start=$((start + 500))
done
date +%s > "$TEST/match_end_epoch"
echo "SCREEN_LOOP_DONE chunks_started_through=$((chunk - 1))"
push_repo "r4-04: ContHist4PlyRead screen update" || true
