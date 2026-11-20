#!/usr/bin/env bash
# honesty.sh EXE OUTDIR LABEL
# One fresh engine process per line. No setoption is sent.
set -u
EXE="$1"
OUT="$2"
LABEL="$3"
mkdir -p "$OUT"
sha=$(sha256sum "$EXE" | awk '{print $1}')
idline=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{print; exit}')
run_one() {
  local cmd="$1" name="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/${LABEL}_${name}.txt"
  {
    echo "exe $EXE"
    echo "sha256 $sha"
    echo "id_name_line $idline"
    echo "command $cmd"
    echo "options: none"
    echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$OUT/${LABEL}_${name}.meta"
  echo "WROTE $OUT/${LABEL}_${name}.txt"
  cat "$OUT/${LABEL}_${name}.txt"
}
run_one "bench 11" bench11
run_one "bench 13" bench13
run_one "bench 16" bench16
run_one "go perft 5" perft5
