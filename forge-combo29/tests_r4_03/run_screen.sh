#!/bin/bash
# On-versus-off screen of the existing LmrDeeperShallower option.
# Does not modify engine source. Pushes PGN and the report on each chunk
# and at least every 30 minutes.
set -u
REPO=/agent/repos/dwqww
OUT=$REPO/forge-combo29/tests_r4_03
BIN=/tmp/forge-r4-build/forge
FC=/tmp/r4tools/fastchess-linux-x86-64/fastchess
BOOK=/tmp/r4tools/UHO_Lichess_4852_v1.epd
BRANCH=grok47/r4-03-screen-lds
ORCH=$OUT/orchestrator.log
PY=$OUT/summarize.py
LOCK=/tmp/r4-git.lock
START_EPOCH=$(date +%s)
DEADLINE_EPOCH=$((START_EPOCH + 6 * 60 * 60))
STARTS=(1 501 1001 1501 2001 2501 3001 3501 4001)
STALL_SEC=720
STARTUP_GRACE_SEC=180
mkdir -p "$OUT"
exec >>"$ORCH" 2>&1
echo "orchestrator start $(date -u +%Y-%m-%dT%H:%M:%SZ) deadline_epoch $DEADLINE_EPOCH"

write_status() {
  local state=$1
  local note=$2
  local stopped=${3:-}
  python3 - "$state" "$note" "$stopped" << 'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
state, note, stopped = sys.argv[1], sys.argv[2], sys.argv[3]
path = Path("/agent/repos/dwqww/forge-combo29/tests_r4_03/status.json")
data = {}
if path.exists():
    data = json.loads(path.read_text())
data["state"] = state
data["note"] = note
if stopped:
    data["stopped_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
path.write_text(json.dumps(data, indent=2) + "\n")
PY
}

commit_and_push() {
  local msg=$1
  flock "$LOCK" bash -c '
set -u
cd /agent/repos/dwqww || exit 1
python3 forge-combo29/tests_r4_03/summarize.py || exit 1
git add -- forge-combo29/REPORT_r4_03.md forge-combo29/tests_r4_03
if git diff --cached --quiet; then
  echo "nothing to commit"
  exit 0
fi
git commit -m "$1" || exit 1
n=0
d=4
while [ "$n" -lt 4 ]; do
  if git push -u origin grok47/r4-03-screen-lds; then
    exit 0
  fi
  n=$((n + 1))
  echo "push failed attempt $n"
  sleep "$d"
  d=$((d * 2))
done
echo "push failed after retries"
exit 1
' _ "$msg" || echo "commit_and_push failed: $msg"
}

count_results() {
  local pgn=$1
  if [[ ! -f $pgn ]]; then
    echo 0
    return
  fi
  grep -c '^\[Result "' "$pgn" || true
}

run_fastchess() {
  local log=$1
  shift
  local pidfile=$OUT/fastchess.pid
  set -m
  if command -v stdbuf >/dev/null 2>&1; then
    stdbuf -oL -eL "$FC" "$@" >>"$log" 2>&1 &
  else
    "$FC" "$@" >>"$log" 2>&1 &
  fi
  local pid=$!
  echo "$pid" >"$pidfile"
  echo "fastchess pid $pid"
  local pgn=""
  for arg in "$@"; do
    case "$arg" in
      file=*.pgn) pgn=${arg#file=} ;;
    esac
  done
  # Resume loads the pgn path from the config. Fall back to the newest chunk pgn.
  if [[ -z $pgn ]]; then
    pgn=$(ls -1t "$OUT"/chunk_*.pgn 2>/dev/null | head -1 || true)
  fi
  local last_size=0
  if [[ -n $pgn && -f $pgn ]]; then
    last_size=$(stat -c %s "$pgn")
  fi
  local last_change
  last_change=$(date +%s)
  local chunk_began
  chunk_began=$(date +%s)
  DEADLINE_HIT=0
  STALL_HIT=0
  while true; do
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    local proc_state
    proc_state=$(ps -o stat= -p "$pid" 2>/dev/null | tr -d '[:space:]' || true)
    if [[ -z $proc_state || $proc_state == Z* ]]; then
      break
    fi
    local now
    now=$(date +%s)
    if (( now >= DEADLINE_EPOCH )); then
      echo "deadline reached, SIGINT $pid at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      kill -INT "$pid" 2>/dev/null || true
      DEADLINE_HIT=1
      local i
      for i in $(seq 1 180); do
        if ! kill -0 "$pid" 2>/dev/null; then
          break
        fi
        proc_state=$(ps -o stat= -p "$pid" 2>/dev/null | tr -d '[:space:]' || true)
        if [[ -z $proc_state || $proc_state == Z* ]]; then
          break
        fi
        sleep 1
      done
      proc_state=$(ps -o stat= -p "$pid" 2>/dev/null | tr -d '[:space:]' || true)
      if kill -0 "$pid" 2>/dev/null && [[ -n $proc_state && $proc_state != Z* ]]; then
        echo "SIGINT did not exit, SIGTERM $pid"
        kill -TERM "$pid" 2>/dev/null || true
        sleep 5
      fi
      if kill -0 "$pid" 2>/dev/null; then
        echo "SIGKILL $pid"
        kill -KILL "$pid" 2>/dev/null || true
      fi
      break
    fi
    local size=0
    if [[ -n $pgn && -f $pgn ]]; then
      size=$(stat -c %s "$pgn")
    fi
    if (( size != last_size )); then
      last_size=$size
      last_change=$now
    fi
    if (( now - chunk_began > STARTUP_GRACE_SEC && now - last_change > STALL_SEC )); then
      echo "stall, SIGINT $pid size=$size"
      kill -INT "$pid" 2>/dev/null || true
      STALL_HIT=1
      break
    fi
    if (( now - LAST_PUSH_EPOCH >= 1800 )); then
      write_status running "heartbeat during chunk"
      commit_and_push "r4-03: heartbeat screen progress"
      LAST_PUSH_EPOCH=$(date +%s)
    fi
    if [[ ! -f /tmp/r4-early-push-done && -n $pgn ]]; then
      local games
      games=$(count_results "$pgn")
      if (( games >= 20 )); then
        write_status running "early push after $games games"
        commit_and_push "r4-03: first games of the screen"
        LAST_PUSH_EPOCH=$(date +%s)
        touch /tmp/r4-early-push-done
      fi
    fi
    sleep 20
  done
  wait "$pid" || true
  echo "fastchess exit wait done deadline=$DEADLINE_HIT stall=$STALL_HIT"
}

cat >"$OUT/command.txt" << 'EOF'
/tmp/r4tools/fastchess-linux-x86-64/fastchess -recover -concurrency 3 -games 2 -rounds 500 -openings file=/tmp/r4tools/UHO_Lichess_4852_v1.epd format=epd order=sequential start=S -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_03/chunk_S.pgn -config outname=/agent/repos/dwqww/forge-combo29/tests_r4_03/chunk_S.json -report penta=true -engine cmd=/tmp/forge-r4-build/forge name=LmrDeeperShallower option.LmrDeeperShallower=true -engine cmd=/tmp/forge-r4-build/forge name=default option.LmrDeeperShallower=false -each proto=uci nodes=50000 option.Threads=1 option.Hash=16 option.OwnBook=false
EOF

python3 - << PY
import json
from datetime import datetime, timezone
from pathlib import Path
path = Path("$OUT/status.json")
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
deadline = datetime.fromtimestamp($DEADLINE_EPOCH, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
path.write_text(json.dumps({
    "state": "running",
    "started_utc": now,
    "deadline_utc": deadline,
    "note": "screen started",
}, indent=2) + "\n")
print(now, deadline)
PY

LAST_PUSH_EPOCH=$START_EPOCH
DEADLINE_HIT=0
STALL_HIT=0

for S in "${STARTS[@]}"; do
  now=$(date +%s)
  if (( now >= DEADLINE_EPOCH || DEADLINE_HIT == 1 )); then
    echo "not starting chunk $S: deadline"
    break
  fi
  # Leave a few minutes so a new chunk is not launched as the clock expires.
  if (( DEADLINE_EPOCH - now < 180 )); then
    echo "not starting chunk $S: under 3 minutes left"
    break
  fi
  pgn=$OUT/chunk_${S}.pgn
  log=$OUT/chunk_${S}.log
  cfg=$OUT/chunk_${S}.json
  echo "===== chunk S=$S $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  attempts=0
  while (( attempts < 6 )); do
    attempts=$((attempts + 1))
    now=$(date +%s)
    if (( now >= DEADLINE_EPOCH )); then
      DEADLINE_HIT=1
      break
    fi
    if [[ -f $cfg ]]; then
      echo "resume attempt $attempts chunk $S"
      run_fastchess "$log" -config "file=$cfg" -recover
    else
      # No saved config means this attempt is a new tournament. Drop a partial
      # PGN so a crash before the first autosave cannot duplicate games.
      if [[ -f $pgn ]]; then
        echo "dropping partial pgn with no config: $pgn"
        rm -f "$pgn"
      fi
      echo "fresh attempt $attempts chunk $S"
      run_fastchess "$log" \
        -recover \
        -concurrency 3 \
        -games 2 \
        -rounds 500 \
        -openings "file=$BOOK" format=epd order=sequential "start=$S" \
        -pgnout "file=$pgn" \
        -config "outname=$cfg" \
        -report penta=true \
        -engine "cmd=$BIN" name=LmrDeeperShallower option.LmrDeeperShallower=true \
        -engine "cmd=$BIN" name=default option.LmrDeeperShallower=false \
        -each proto=uci nodes=50000 option.Threads=1 option.Hash=16 option.OwnBook=false
    fi
    games=$(count_results "$pgn")
    echo "chunk $S games_with_result $games after attempt $attempts"
    if (( DEADLINE_HIT == 1 )); then
      write_status stopped "deadline during chunk $S with $games result tags"
      break
    fi
    if (( games >= 1000 )); then
      echo "chunk $S complete ($games result tags)"
      break
    fi
    # Confirm the log tail. A clean finish with fewer than 1000 tags is still done
    # if fastchess says so and was not interrupted.
    if tail -n 30 "$log" | grep -q "Finished match" && ! tail -n 30 "$log" | grep -q "Tournament was interrupted"; then
      echo "chunk $S clean finish with $games result tags"
      break
    fi
    if (( STALL_HIT == 1 )); then
      echo "stall on chunk $S, will resume if config exists"
      STALL_HIT=0
      sleep 2
      continue
    fi
    echo "chunk $S incomplete ($games), resuming"
    sleep 2
  done
  write_status running "pushed after chunk $S"
  commit_and_push "r4-03: chunk $S PGN and screen summary"
  LAST_PUSH_EPOCH=$(date +%s)
  if (( DEADLINE_HIT == 1 )); then
    break
  fi
done

python3 "$PY" || true
final_state=finished
if (( DEADLINE_HIT == 1 )); then
  final_state=stopped
fi
write_status "$final_state" "screen loop ended" now
commit_and_push "r4-03: final LmrDeeperShallower screen summary"
echo "orchestrator done $(date -u +%Y-%m-%dT%H:%M:%SZ) state=$final_state"
exit 0
