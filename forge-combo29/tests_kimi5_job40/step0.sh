#!/usr/bin/env bash
# kimi5 job 40 step 0: the eight numbers of file 30, one fresh engine process per line.
# Usage: step0.sh <exe> <outdir>   (opt files are read from ../opt_src relative to this script)
set -u
EXE="$1"
OUT="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
OPTSRC="$HERE/opt_src"
mkdir -p "$OUT"

run_line() { # tag, then commands on stdin
  local tag="$1"
  cat > "$OUT/${tag}_input.log"
  ( cd "$OUT" && "$EXE" < "${tag}_input.log" > "${tag}.txt" 2>&1 )
}

opt_lines() { # optfile -> setoption lines
  grep -v '^\s*#' "$1" | grep -v '^\s*$' | while read -r line; do
    name="${line% *}"; value="${line##* }"
    printf 'setoption name %s value %s\n' "$name" "$value"
  done
}

for n in 11 13 16; do
  { printf 'isready\nucinewgame\nisready\nbench %s\nquit\n' "$n"; } | run_line "none_bench$n"
done
{ printf 'isready\nucinewgame\nisready\ngo perft 5\nquit\n'; } | run_line "none_perft5"
for set in s14 pc20; do
  for n in 11 13; do
    { opt_lines "$OPTSRC/$set.opt"; printf 'isready\nucinewgame\nisready\nbench %s\nquit\n' "$n"; } | run_line "${set}_bench$n"
  done
done
sha256sum "$EXE" > "$OUT/exe.sha256"
echo "step0 done -> $OUT"
