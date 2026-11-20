#!/usr/bin/env bash
# honesty.sh EXE LABEL OUTDIR
# One fresh process per line. No setoption. uci is sent only after the measured command.
set -u
EXE="$1"
LABEL="$2"
OUT="$3"
sha=$(sha256sum "$EXE" | awk '{print $1}')
run_one() {
  local name="$1"
  local cmd="$2"
  local raw="$OUT/honesty_${LABEL}_${name}.txt"
  local meta="$OUT/honesty_${LABEL}_${name}.meta"
  printf '%s\nuci\nquit\n' "$cmd" | "$EXE" > "$raw"
  local id
  id=$(grep -m1 '^id name ' "$raw" || true)
  {
    echo "exe: $EXE"
    echo "sha256: $sha"
    echo "id: ${id:-missing}"
    echo "command: $cmd"
    echo "options:"
  } > "$meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
echo "honesty $LABEL done"
