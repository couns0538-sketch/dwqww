#!/usr/bin/env bash
# pc_pins.sh EXE OUTDIR — the PC build's known numbers, one fresh process per line.
# Regimes (FABLE_TO_swarm_4 + 5): pins = NO setoption at all; S14 = the 14 setoptions; PC20 = S14 + six more.
set -u
EXE="$1"; OUT="$2"
mkdir -p "$OUT"
sha256sum "$EXE" > "$OUT/sha256.txt"
{ printf 'uci\nquit\n'; } | "$EXE" > "$OUT/uci_raw.txt" 2>&1
grep -E '^id name|^option name (CuckooRep|HistRework|TtPruneV2|CorrHistV2|MateAlphaGuard|OwnBook)' "$OUT/uci_raw.txt" > "$OUT/options_seen.txt"

S14='setoption name LmrQuietBase value 93
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
setoption name NonPawnCorrection value true'

PC20="$S14
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
setoption name OwnBook value false"

run_bench () {  # $1 label, $2 setoption block, $3 depth
  local label="$1" opts="$2" d="$3"
  {
    printf 'uci\n'
    [ -n "$opts" ] && printf '%s\n' "$opts"
    printf 'isready\nucinewgame\nisready\nbench %s\n' "$d"
    sleep 0.1
    printf 'quit\n'
  } | "$EXE" 2>&1 | grep -E 'info string bench|unknown option|invalid value|ERROR' | tee -a "$OUT/$label.txt"
}

echo "=== pins: NO setoption at all ===" | tee "$OUT/summary.txt"
for d in 11 13 16; do run_bench "none_bench$d" "" "$d"; done
{ printf 'uci\nisready\nucinewgame\nisready\nposition startpos\ngo perft 5\n'; sleep 0.3; printf 'quit\n'; } \
  | "$EXE" 2>&1 | grep -E '^nodes ' | tee -a "$OUT/none_perft5.txt"

echo "=== S14 ===" | tee -a "$OUT/summary.txt"
for d in 11 13; do run_bench "s14_bench$d" "$S14" "$d"; done

echo "=== PC20 ===" | tee -a "$OUT/summary.txt"
for d in 11 13; do run_bench "pc20_bench$d" "$PC20" "$d"; done

echo "--- all raw ---" | tee -a "$OUT/summary.txt"
for f in "$OUT"/none_*.txt "$OUT"/s14_*.txt "$OUT"/pc20_*.txt; do
  [ "$f" = "$OUT/summary.txt" ] && continue
  echo "$(basename "$f"): $(cat "$f" | tr '\n' ' ')" | tee -a "$OUT/summary.txt"
done
