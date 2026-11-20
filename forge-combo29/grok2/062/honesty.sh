#!/usr/bin/env bash
# honesty.sh EXE OUTPREFIX
# Fresh process per line. No setoption. Raw stdout+stderr saved.
set -u
EXE="$1"
PREFIX="$2"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDLINE=$(printf 'uci\nquit\n' | "$EXE" | grep '^id name ' | head -n 1)
write_meta() {
  local tag="$1"
  local cmd="$2"
  {
    echo "exe $EXE"
    echo "sha256 $SHA"
    echo "$IDLINE"
    echo "command $cmd"
    echo "options none"
  } > "${PREFIX}_${tag}.meta"
}
run_one() {
  local tag="$1"
  local cmd="$2"
  write_meta "$tag" "$cmd"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "${PREFIX}_${tag}.txt" 2>&1
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
echo "HONESTY_DONE $PREFIX"
