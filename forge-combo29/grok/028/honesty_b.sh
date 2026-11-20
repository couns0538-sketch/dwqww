#!/usr/bin/env bash
# Fresh process per line. No setoption. Raw engine stdout is the .txt file.
set -u
EXE="$1"
OUT="$2"
TAG="${3:-B}"
mkdir -p "$OUT"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | sed -n 's/^id name //p' | head -n 1)

write_meta() {
  local stem="$1"
  {
    echo "exe $EXE"
    echo "sha256 $SHA"
    echo "id_name $IDNAME"
    echo "options (none)"
  } > "$OUT/${stem}.meta"
}

run_cmd() {
  local stem="$1"
  local body="$2"
  printf '%s\nquit\n' "$body" | "$EXE" > "$OUT/${stem}.txt"
  write_meta "$stem"
}

run_cmd "bench11_$TAG" "bench 11"
run_cmd "bench13_$TAG" "bench 13"
run_cmd "bench16_$TAG" "bench 16"
run_cmd "perft5_$TAG" "go perft 5"

{
  echo "exe $EXE"
  echo "sha256 $SHA"
  echo "id_name $IDNAME"
  echo "bench11 $(sed -n 's/.*bench depth 11 nodes \([0-9][0-9]*\).*/\1/p' "$OUT/bench11_$TAG.txt" | head -n 1)"
  echo "bench13 $(sed -n 's/.*bench depth 13 nodes \([0-9][0-9]*\).*/\1/p' "$OUT/bench13_$TAG.txt" | head -n 1)"
  echo "bench16 $(sed -n 's/.*bench depth 16 nodes \([0-9][0-9]*\).*/\1/p' "$OUT/bench16_$TAG.txt" | head -n 1)"
  echo "perft5 $(awk '/^nodes /{n=$2} END{print n}' "$OUT/perft5_$TAG.txt")"
} > "$OUT/HONESTY_$TAG.txt"
cat "$OUT/HONESTY_$TAG.txt"
