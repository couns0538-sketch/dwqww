#!/usr/bin/env bash
# pc_honesty.sh EXE OUT : the three honesty regimes for the PC r15 build (FABLE_TO_swarm_5's table).
#   row 1: no setoption at all          -> 312866 / 862329 / 3024920 / 4865609
#   row 2: S14 (14 setoptions)          -> 242796 / 656517
#   row 3: PC20 = S14 + six settings    -> 278024 / 587276
# A fresh process per line (file 4: pins are DEFAULT-option numbers; sums are S14 numbers).
set -u
EXE="$1"; OUT="$2"; : > "$OUT"
go() { printf '%s\nquit\n' "$1" | "$EXE" 2>&1 | grep -E 'nodes|perft' | tail -1; }

S14OPT="setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true"

PC20OPT="$S14OPT
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TpruneV2 placeholder"

echo "=== ROW 1: no setoption at all ===" >> "$OUT"
for b in 11 13 16; do printf 'bench %s\nquit\n' "$b" | "$EXE" 2>&1 | grep 'bench depth' | tee -a "$OUT"; done
echo "perft5: $(go 'position startpos
go perft 5')" >> "$OUT"

echo "=== ROW 2: S14 ===" >> "$OUT"
{ printf '%s\n' "$S14OPT"; printf 'setoption name Threads value 1\nsetoption name Hash value 16\nbench 11\nquit\n'; } \
  | "$EXE" 2>&1 | grep 'bench depth' | tee -a "$OUT"
{ printf '%s\n' "$S14OPT"; printf 'setoption name Threads value 1\nsetoption name Hash value 16\nbench 13\nquit\n'; } \
  | "$EXE" 2>&1 | grep 'bench depth' | tee -a "$OUT"

echo "=== option names the exe lists (for PC20) ===" >> "$OUT"
printf 'uci\nquit\n' | "$EXE" 2>&1 | grep -E '^option name' | sed 's/ type.*//;s/option name //' | tee -a "$OUT" | tr '\n' '|'
echo
cat "$OUT"
