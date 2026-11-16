#!/usr/bin/env bash
# How much of a `bench 13` run is one-time startup (magic/table init) versus search?
# Measures (a) `uci/quit` only [= startup+teardown], (b) `uci; bench 1` [startup + a tiny search],
# (c) `uci; bench 13`, each 5 times, fresh process, wall clock from bash EPOCHREALTIME.
set -u
EXE="$1"
run() { # $1 = label, $2 = command body
  local tot=0
  for i in 1 2 3 4 5; do
    printf 'uci\nisready\n%b\nquit\n' "$2" > /tmp/sv.txt
    local t0=$EPOCHREALTIME
    "$EXE" < /tmp/sv.txt > /dev/null 2>&1
    local t1=$EPOCHREALTIME
    awk -v a="$t0" -v b="$t1" -v l="$1" 'BEGIN{printf "%s run: %.3f s\n", l, b-a}'
  done
}
run "uci-only " ""
run "bench 1  " "bench 1;"
run "bench 13 " "bench 13;"
