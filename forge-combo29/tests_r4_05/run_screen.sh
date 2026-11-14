#!/usr/bin/env bash
# Sequential UHO screen of NonPawnCorrection on vs off. Same binary.
# Does not modify engine source. Publishes each finished chunk.
set -euo pipefail

REPO=/agent/repos/dwqww
ROOT=/tmp/r4_05
EXE="$ROOT/build/forge"
FAST="$ROOT/src/fastchess/fastchess"
BOOK="$ROOT/src/UHO_Lichess_4852_v1.epd"
BRANCH=grok47/r4-05-screen-npc
TESTS="$REPO/forge-combo29/tests_r4_05"
LIVE="$ROOT/live"
BUDGET=21600
CAP=32400
OPENINGS=500
CONCURRENCY=4
BASE=e04556ddc3a430b2e751159b0d46111ef56c8b89
IMPL=b68d49fedcc8e705484d06fb02cf0a417734839f

mkdir -p "$LIVE" "$TESTS/pgn" "$TESTS/logs" "$TESTS/summary" "$ROOT/chunks"
cd "$REPO"
git checkout "$BRANCH"
if ! git diff --quiet "$BASE" -- forge-combo29/src forge-combo29/include; then
  echo "engine source differs from the base" >&2
  exit 1
fi

commit_and_push() {
  local msg="$1"
  (
    flock 9
    cd "$REPO"
    git add -- forge-combo29/REPORT_r4_05.md forge-combo29/tests_r4_05
    if git diff --cached --name-only | grep -E '^forge-combo29/(src|include)/'; then
      echo "refusing to commit engine source" >&2
      exit 1
    fi
    if git diff --cached --quiet; then
      echo "nothing to commit: $msg"
    else
      git commit -m "$msg"
    fi
    local n=0 delay=4
    while true; do
      if git push -u origin "$BRANCH"; then
        date -u +%s > "$ROOT/last_push"
        break
      fi
      n=$((n + 1))
      if (( n >= 4 )); then
        echo "push failed after retries: $msg" >&2
        exit 1
      fi
      sleep "$delay"
      delay=$((delay * 2))
    done
  ) 9>"$ROOT/git.lock"
}

refresh_report() {
  python3 "$TESTS/screen_stats.py" --repo "$REPO" --meta "$TESTS/meta.json" --state "$TESTS/state.json"
}

write_state() {
  local state="$1" reason="$2" start="$3"
  python3 - "$TESTS/state.json" "$state" "$reason" "$start" "$BUDGET" "$CAP" <<'PY'
import json, sys
path, state, reason, start, budget, cap = sys.argv[1:]
payload = {
    "state": state,
    "stop_reason": reason,
    "match_start": None if start == "-" else start,
    "budget_s": int(budget),
    "cap_s": int(cap),
}
json.dump(payload, open(path, "w"), indent=2)
open(path, "a").write("\n")
PY
}

setup() {
  local pins_log="$TESTS/pins.log"
  local bench_log="$TESTS/bench13_alternating.log"
  {
    echo "setoption name Threads value 1"
    echo "setoption name Hash value 16"
    echo "setoption name OwnBook value false"
    echo "setoption name NonPawnCorrection value false"
    echo "bench 11"
    echo "bench 13"
    echo "position startpos"
    echo "go perft 5"
    echo "quit"
  } | "$EXE" | tee "$pins_log"
  {
    echo "setoption name Threads value 1"
    echo "setoption name Hash value 16"
    echo "setoption name OwnBook value false"
    for i in 1 2 3 4 5; do
      if (( i % 2 == 1 )); then
        echo "setoption name NonPawnCorrection value false"
      else
        echo "setoption name NonPawnCorrection value true"
      fi
      echo "isready"
      echo "bench 13"
    done
    echo "quit"
  } | "$EXE" | awk '
    /bench depth 13/ {
      n += 1
      opt = (n % 2 ? "false" : "true")
      print "RUN " n " option=" opt
      print
    }
  ' | tee "$bench_log"
  python3 - "$TESTS/meta.json" "$pins_log" "$bench_log" <<PY
import hashlib, json, pathlib, re, subprocess, sys
meta_path, pins_path, bench_path = sys.argv[1:]
pins = pathlib.Path(pins_path).read_text()
bench = pathlib.Path(bench_path).read_text().splitlines()
def nodes(text, depth):
    match = re.search(rf"bench depth {depth} nodes (\\d+)", text)
    if not match:
        raise SystemExit(f"missing bench {depth}")
    return int(match.group(1))
perft = int(re.search(r"^nodes (\\d+)", pins, re.M).group(1))
bench11, bench13 = nodes(pins, 11), nodes(pins, 13)
if (bench11, bench13, perft) != (312866, 862329, 4865609):
    raise SystemExit(f"pin mismatch {(bench11, bench13, perft)}")
runs = []
expect = None
for line in bench:
    if line.startswith("RUN "):
        parts = line.split()
        expect = {"run": int(parts[1]), "option": parts[2].split("=", 1)[1]}
    elif "bench depth 13" in line and expect is not None:
        nums = {key: int(value) for key, value in re.findall(r"(nodes|time|nps) (\\d+)", line)}
        expect.update(nodes=nums["nodes"], time_ms=nums["time"], nps=nums["nps"])
        runs.append(expect)
        expect = None
if [r["run"] for r in runs] != [1, 2, 3, 4, 5]:
    raise SystemExit(f"bench runs missing: {runs}")
if [r["option"] for r in runs] != ["false", "true", "false", "true", "false"]:
    raise SystemExit(runs)
for run in runs:
    if run["option"] == "false" and run["nodes"] != 862329:
        raise SystemExit(f"off bench moved: {run}")
    if run["option"] == "true" and run["nodes"] != runs[1]["nodes"]:
        raise SystemExit(f"on bench unstable: {run}")
on_nodes = runs[1]["nodes"]
def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()
compiler = subprocess.check_output(["g++", "--version"], text=True).splitlines()[0]
cmake = subprocess.check_output(["cmake", "--version"], text=True).splitlines()[0].replace("cmake version ", "")
flags = pathlib.Path("/proc/cpuinfo").read_text()
if "avx512f" not in flags or "bmi2" not in flags:
    raise SystemExit("CPU is missing AVX-512F or BMI2; owner build is not valid")
command = """$FAST \\\\
  -recover \\\\
  -repeat \\\\
  -games 2 \\\\
  -rounds 500 \\\\
  -concurrency $CONCURRENCY \\\\
  -ratinginterval 250 \\\\
  -scoreinterval 250 \\\\
  -report penta=true \\\\
  -event \"r4-05 NonPawnCorrection chunk CHUNK openings START-END\" \\\\
  -site \"grok47/r4-05-screen-npc\" \\\\
  -openings file=CHUNK_EPD format=epd order=sequential start=1 \\\\
  -engine name=NonPawnCorrectionOn cmd=$EXE option.NonPawnCorrection=true \\\\
  -engine name=NonPawnCorrectionOff cmd=$EXE option.NonPawnCorrection=false \\\\
  -each proto=uci option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 \\\\
  -pgnout file=CHUNK_PGN notation=san append=false"""
meta = {
    "base": "$BASE",
    "implementation_commit": "$IMPL",
    "branch": "$BRANCH",
    "engine_id": "Chess Engine Forge 6.4.24 candidate",
    "compiler": compiler,
    "cmake": cmake,
    "march": "x86-64-v4",
    "build_kind": "owner (AVX-512F and BMI2 present; FORGE_PORTABLE=OFF)",
    "cpu": "Intel Xeon with AVX-512F and BMI2, 4 threads",
    "fastchess": subprocess.check_output(["$FAST", "-version"], text=True).strip(),
    "fastchess_commit": "pending",
    "book_name": "UHO_Lichess_4852_v1.epd",
    "book_lines": 2632036,
    "book_url": "https://github.com/official-stockfish/books/raw/master/UHO_Lichess_4852_v1.epd.zip",
    "binary_sha256": sha("$EXE"),
    "fastchess_sha256": sha("$FAST"),
    "book_sha256": "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a",
    "book_zip_sha256": "4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07",
    "pins": {"bench11": bench11, "bench13": bench13, "perft5": perft},
    "bench13_on_nodes": on_nodes,
    "bench13_runs": runs,
    "conditions": {
        "nodes": 50000,
        "threads": 1,
        "hash": 16,
        "ownbook": False,
        "concurrency": $CONCURRENCY,
        "openings_per_chunk": $OPENINGS,
        "games_per_opening": 2,
    },
    "command_template": command,
    "owner_prior": "+6.8 ± 7.2 in 4000 games",
}
# fastchess commit is filled by the shell after this script if the placeholder remains.
meta["fastchess_commit"] = open("$ROOT/src/fastchess.commit").read().strip()
pathlib.Path(meta_path).write_text(json.dumps(meta, indent=2) + "\\n")
print(json.dumps({"pins": meta["pins"], "bench": runs, "binary": meta["binary_sha256"]}, indent=2))
PY
  write_state setup "setup recorded; match not started" "-"
  refresh_report
  commit_and_push "r4-05: record pins, alternating bench 13, and screen setup"
}

run_chunk() {
  local chunk="$1"
  local start_line=$(( (chunk - 1) * OPENINGS + 1 ))
  local end_line=$(( chunk * OPENINGS ))
  local id
  id=$(printf "%03d" "$chunk")
  local epd="$ROOT/chunks/chunk_${id}.epd"
  local live_pgn="$LIVE/chunk_${id}.pgn"
  local live_log="$LIVE/chunk_${id}.log"
  echo "$id" > "$TESTS/current_chunk.txt"
  sed -n "${start_line},${end_line}p" "$BOOK" > "$epd"
  local lines
  lines=$(wc -l < "$epd")
  if (( lines != OPENINGS )); then
    echo "chunk $id has $lines openings" >&2
    return 2
  fi
  rm -f "$live_pgn"
  local began
  began=$(date +%s)
  set +e
  stdbuf -oL -eL "$FAST" \
    -recover \
    -repeat \
    -games 2 \
    -rounds 500 \
    -concurrency "$CONCURRENCY" \
    -ratinginterval 250 \
    -scoreinterval 250 \
    -report penta=true \
    -event "r4-05 NonPawnCorrection chunk ${id} openings ${start_line}-${end_line}" \
    -site "grok47/r4-05-screen-npc" \
    -openings "file=${epd}" format=epd order=sequential start=1 \
    -engine name=NonPawnCorrectionOn cmd="$EXE" option.NonPawnCorrection=true \
    -engine name=NonPawnCorrectionOff cmd="$EXE" option.NonPawnCorrection=false \
    -each proto=uci option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 \
    -pgnout "file=${live_pgn}" notation=san append=false \
    > "$live_log" 2>&1
  local ec=$?
  set -e
  local wall=$(( $(date +%s) - began ))
  echo "$wall" > "$LIVE/chunk_${id}.wall"
  if (( ec != 0 )); then
    echo "fastchess exit $ec on chunk $id" >&2
    return 1
  fi
  if ! grep -q "Finished match" "$live_log"; then
    echo "chunk $id did not finish" >&2
    return 1
  fi
  local events
  events=$(grep -c '^\[Event ' "$live_pgn" || true)
  if (( events != OPENINGS * 2 )); then
    echo "chunk $id has $events games" >&2
    return 1
  fi
  local now_sha
  now_sha=$(sha256sum "$EXE" | awk '{print $1}')
  local want_sha
  want_sha=$(python3 -c 'import json; print(json.load(open("'"$TESTS/meta.json"'"))["binary_sha256"])')
  if [[ "$now_sha" != "$want_sha" ]]; then
    echo "binary sha changed" >&2
    return 1
  fi
  (
    flock 9
    cp "$live_pgn" "$TESTS/pgn/chunk_${id}.pgn"
    cp "$live_log" "$TESTS/logs/chunk_${id}.log"
    echo "$wall" > "$TESTS/logs/chunk_${id}.wall"
    local start_iso
    start_iso=$(python3 -c 'import json; print(json.load(open("'"$TESTS/state.json"'"))["match_start"])')
    write_state running "chunk ${id} published; match still inside the time box" "$start_iso"
    refresh_report
    cd "$REPO"
    git add -- forge-combo29/REPORT_r4_05.md forge-combo29/tests_r4_05
    if git diff --cached --name-only | grep -E '^forge-combo29/(src|include)/'; then
      echo "refusing to commit engine source" >&2
      exit 1
    fi
    git commit -m "r4-05: NonPawnCorrection screen chunk ${id} (${start_line}-${end_line})"
    local n=0 delay=4
    while true; do
      if git push -u origin "$BRANCH"; then
        date -u +%s > "$ROOT/last_push"
        break
      fi
      n=$((n + 1))
      if (( n >= 4 )); then
        echo "push failed for chunk $id" >&2
        exit 1
      fi
      sleep "$delay"
      delay=$((delay * 2))
    done
  ) 9>"$ROOT/git.lock"
}

heartbeat_loop() {
  while true; do
    local now last wait_s
    now=$(date -u +%s)
    last=0
    if [[ -f "$ROOT/last_push" ]]; then
      last=$(cat "$ROOT/last_push")
    fi
    wait_s=$(( last + 1800 - now ))
    if (( wait_s < 30 )); then
      wait_s=30
    fi
    sleep "$wait_s"
    now=$(date -u +%s)
    if [[ -f "$ROOT/last_push" ]]; then
      last=$(cat "$ROOT/last_push")
    fi
    if (( now < last + 1800 )); then
      continue
    fi
    local chunk="none" games=0 utc
    utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    if [[ -f "$TESTS/current_chunk.txt" ]]; then
      chunk=$(cat "$TESTS/current_chunk.txt")
    fi
    local live_log="$LIVE/chunk_${chunk}.log"
    if [[ -f "$live_log" ]]; then
      games=$(grep -c '^Finished game ' "$live_log" || true)
    fi
    cat > "$TESTS/HEARTBEAT.md" <<EOF
# Heartbeat

- UTC: ${utc}
- Current chunk: ${chunk}
- Finished-game lines in the live log: ${games}
- Note: in-progress screen. Not a final result.
EOF
    commit_and_push "r4-05: heartbeat ${utc}" || true
  done
}

match_loop() {
  local start_epoch start_iso elapsed chunk
  if [[ -f "$TESTS/state.json" ]] && python3 -c 'import json,sys; s=json.load(open(sys.argv[1])); raise SystemExit(0 if s.get("match_start") else 1)' "$TESTS/state.json"; then
    start_iso=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["match_start"])' "$TESTS/state.json")
    start_epoch=$(date -u -d "$start_iso" +%s)
  else
    start_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    start_epoch=$(date -u +%s)
    write_state running "match started" "$start_iso"
    refresh_report
    commit_and_push "r4-05: start NonPawnCorrection screen"
  fi
  heartbeat_loop &
  local heart_pid=$!
  trap 'kill "$heart_pid" 2>/dev/null || true' EXIT
  chunk=1
  if compgen -G "$TESTS/pgn/chunk_[0-9][0-9][0-9].pgn" > /dev/null; then
    local last
    last=$(basename "$(ls "$TESTS/pgn"/chunk_[0-9][0-9][0-9].pgn | sort | tail -1)" .pgn)
    chunk=$((10#${last#chunk_} + 1))
  fi
  while true; do
    elapsed=$(( $(date -u +%s) - start_epoch ))
    if (( elapsed >= CAP )); then
      write_state complete "stopped before a new chunk because the 9 hour cap was reached after ${elapsed}s" "$start_iso"
      refresh_report
      commit_and_push "r4-05: close NonPawnCorrection screen at the 9 hour cap"
      break
    fi
    if (( elapsed >= BUDGET )); then
      write_state complete "stopped before a new chunk because the 6 hour match budget was reached after ${elapsed}s" "$start_iso"
      refresh_report
      commit_and_push "r4-05: close NonPawnCorrection screen at the 6 hour budget"
      break
    fi
    echo "starting chunk $chunk at elapsed ${elapsed}s"
    if ! run_chunk "$chunk"; then
      local id
      id=$(printf "%03d" "$chunk")
      mkdir -p "$TESTS/failed"
      cp -f "$LIVE/chunk_${id}.log" "$TESTS/failed/chunk_${id}.log" 2>/dev/null || true
      cp -f "$LIVE/chunk_${id}.pgn" "$TESTS/failed/chunk_${id}.pgn" 2>/dev/null || true
      write_state complete "stopped because chunk ${id} failed" "$start_iso"
      refresh_report
      commit_and_push "r4-05: stop NonPawnCorrection screen after chunk ${id} failed"
      exit 1
    fi
    chunk=$((chunk + 1))
  done
}

git -C "$ROOT/src/fastchess" rev-parse HEAD > "$ROOT/src/fastchess.commit"
case "${1:-}" in
  setup) setup ;;
  match) match_loop ;;
  *)
    echo "usage: $0 setup|match" >&2
    exit 2
    ;;
esac
