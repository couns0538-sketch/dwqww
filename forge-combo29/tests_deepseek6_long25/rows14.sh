#!/bin/bash
# deepseek6 long 25 harness: rows run at a given depth over a FEN set.
# usage: rows14.sh <tag> <exe> <fens> <depth> <outdir> <setoption lines file>
set -u
TAG="$1"; EXE="$2"; FENS="$3"; DEPTH="$4"; OUT="$5"; OPTS="$6"
ROWS="$OUT/$TAG.rows"
LOG="$OUT/$TAG.run.log"
META="$ROWS.meta"

: > "$ROWS"; : > "$LOG"
{
  echo "exe_path_started=$EXE"
  echo "exe_sha256=$(sha256sum "$EXE" | cut -d' ' -f1)"
  echo "id_name=$(printf 'uci\nquit\n' | "$EXE" 2>/dev/null | grep '^id name' | head -1)"
  echo "fens=$FENS"
  echo "fen_count=$(grep -c . "$FENS")"
  echo "depth=$DEPTH"
  echo "--- setoption lines sent, in order:"
  while IFS= read -r o; do [ -n "$o" ] && echo "setoption $o"; done < "$OPTS"
} > "$META"

N=0
while IFS= read -r FEN; do
  [ -z "$FEN" ] && continue
  N=$((N+1))
  {
    echo "uci"
    echo "isready"
    while IFS= read -r o; do [ -n "$o" ] && echo "setoption $o"; done < "$OPTS"
    echo "ucinewgame"
    echo "isready"
    echo "position fen $FEN"
    echo "go depth $DEPTH"
  } | timeout 3600 "$EXE" > "$OUT/.$TAG.$N.tmp" 2>&1
  RC=$?
  if grep -qiE 'unknown option|invalid value|No such option' "$OUT/.$TAG.$N.tmp"; then
    echo "STOP_REFUSED row=$N tag=$TAG line=$(grep -iE 'unknown option|invalid value|No such option' "$OUT/.$TAG.$N.tmp" | head -1)" | tee -a "$LOG"
    cat "$OUT/.$TAG.$N.tmp" >> "$LOG"
    rm -f "$OUT/.$TAG.$N.tmp"
    echo "$N|REFUSED|REFUSED" >> "$ROWS"
    break
  fi
  if [ $RC -ne 0 ]; then
    echo "STOP_RC row=$N tag=$TAG rc=$RC" | tee -a "$LOG"
    rm -f "$OUT/.$TAG.$N.tmp"
    echo "$N|RC$RC|RC$RC" >> "$ROWS"
    break
  fi
  NODES=$(grep -oE 'nodes [0-9]+' "$OUT/.$TAG.$N.tmp" | tail -1 | awk '{print $2}')
  BM=$(grep -oE '^bestmove [^ ]+' "$OUT/.$TAG.$N.tmp" | tail -1 | awk '{print $2}')
  [ -z "$NODES" ] && NODES="NONODES"
  [ -z "$BM" ] && BM="NOBM"
  echo "$N|$NODES|$BM" >> "$ROWS"
  cat "$OUT/.$TAG.$N.tmp" >> "$LOG"
  rm -f "$OUT/.$TAG.$N.tmp"
done < "$FENS"
echo "DONE tag=$TAG rows=$(grep -c . "$ROWS")" >> "$META"
