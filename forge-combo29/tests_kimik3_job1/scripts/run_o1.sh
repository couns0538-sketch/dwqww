#!/bin/bash
# O1: node counts for bench 11/13/16/20 x {no option, HistRework 2, B1, HistRework 1, HistRework 3} + perft 5.
# Usage: run_o1.sh <binary> <outdir>
set -u
B="$1"; OUT="$2"; mkdir -p "$OUT"
run() { # name, stdin-script
  local name="$1" script="$2"
  printf '%s\nquit\n' "$script" | "$B" > "$OUT/$name.txt" 2>&1
}
for cfg in noopt hr2 b1 hr1 hr3; do
  case $cfg in
    noopt) pre="";;
    hr2)   pre="setoption name HistRework value 2";;
    b1)    pre="setoption name BundlePreset value B1";;
    hr1)   pre="setoption name HistRework value 1";;
    hr3)   pre="setoption name HistRework value 3";;
  esac
  for d in 11 13 16 20; do
    if [ -z "$pre" ]; then run "${cfg}_b${d}" "bench ${d}"; else run "${cfg}_b${d}" "${pre}
bench ${d}"; fi
  done
done
run perft5 "position startpos
go perft 5"
echo DONE_O1 "$B"
