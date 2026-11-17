#!/usr/bin/env bash
# step0_v3.sh — FABLE file 7 Step 0: the four bench rows x two depths, and the three eval lines.
# Load order per the file: NNUEArchFile FIRST, then NNUEArch true. Fresh process per line. Threads 1, Hash 16.
set -u
EXE="${1:-$HOME/builds/v3/forge}"
NET="${2:-/agent/repos/dwqww/forge-combo29/swarm/08/v3/test_v3.fnn3}"
OUT="${3:-step0_v3.txt}"
: > "$OUT"

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
NETOPTS="setoption name NNUEArchFile value $NET
setoption name NNUEArch value true"

sha256sum "$EXE" | tee -a "$OUT" >/dev/null
{ echo "exe $EXE"; sha256sum "$EXE"; } > "${OUT%.txt}.meta"
{ printf 'uci\nquit\n'; } | "$EXE" | grep -E '^id name' >> "${OUT%.txt}.meta"

run_bench () {  # $1 label, $2 option block, $3 depth
  {
    printf 'uci\n'
    [ -n "$2" ] && printf '%s\n' "$2"
    printf 'setoption name Threads value 1\nsetoption name Hash value 16\n'
    printf 'isready\nucinewgame\nisready\nbench %s\n' "$3"
    sleep 0.1
    printf 'quit\n'
  } | "$EXE" 2>&1 | grep -E 'info string bench|NNUE v3|invalid|unknown|ERROR' | tee -a "$OUT"
}

echo "=== row 1: no net, no setoption ===" | tee -a "$OUT"
for d in 11 13; do run_bench "r1_$d" "" "$d"; done
echo "=== row 2: PC20, no net ===" | tee -a "$OUT"
for d in 11 13; do run_bench "r2_$d" "$PC20" "$d"; done
echo "=== row 3: test net only ===" | tee -a "$OUT"
for d in 11 13; do run_bench "r3_$d" "$NETOPTS" "$d"; done
echo "=== row 4: PC20, then the test net ===" | tee -a "$OUT"
for d in 11 13; do run_bench "r4_$d" "$PC20
$NETOPTS" "$d"; done

echo "=== the three eval lines (PC20 + test net) ===" | tee -a "$OUT"
for fen in "startpos" \
           "fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3" \
           "fen 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40"; do
  {
    printf 'uci\n%s\n%s\nsetoption name Threads value 1\nsetoption name Hash value 16\n' "$PC20" "$NETOPTS"
    printf 'isready\nucinewgame\nisready\n'
    if [ "$fen" = "startpos" ]; then printf 'position startpos\n'; else printf 'position %s\n' "$fen"; fi
    printf 'isready\neval\n'
    sleep 0.2
    printf 'quit\n'
  } | "$EXE" 2>&1 | grep -E 'info string eval|NNUE v3 (loaded|active)' | sed "s|^|[$fen] |" | tee -a "$OUT"
done
