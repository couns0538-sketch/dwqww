#!/usr/bin/env bash
# searchstress.sh EXE FENS OUTDIR : run every FEN at go depth 10 S14, one process per 25 FENs,
# report ASan/UBSan lines and illegal bestmoves (checked by python-chess).
set -u
EXE="$1"; FENS="$2"; OUT="$3"
mkdir -p "$OUT"
S14="setoption name LmrQuietBase value 93
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
: > "$OUT/summary.txt"
split -l 25 -d "$FENS" "$OUT/chunk_"
for chunk in "$OUT"/chunk_*; do
  base=$(basename "$chunk")
  {
    echo uci
    echo "setoption name Hash value 16"
    echo "setoption name Threads value 1"
    echo isready
    printf '%s\n' "$S14"
    echo isready
    echo ucinewgame
    echo isready
    n=0
    while IFS= read -r fen; do
      [ -z "$fen" ] && continue
      n=$((n+1))
      echo "echo ---FEN $n $fen"
      echo "position fen $fen"
      echo isready
      echo "go depth 10"
      echo isready
    done < "$chunk"
    echo quit
  } > "$OUT/$base.in"
  timeout 900 "$EXE" < "$OUT/$base.in" > "$OUT/$base.out" 2> "$OUT/$base.err"
  rc=$?
  san=$(grep -cE 'AddressSanitizer|runtime error' "$OUT/$base.err" || true)
  echo "$base rc=$rc sanitizer_lines=$san bestmoves=$(grep -c '^bestmove' "$OUT/$base.out")" | tee -a "$OUT/summary.txt"
done
