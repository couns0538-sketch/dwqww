#!/usr/bin/env bash
# play.sh: chunks of 250 openings (500 games) from the top of ~/mine.epd, one after another, until minute 95 or
# ~/STOP_PLAY; a chunk counts only when fastchess ended it ("Finished match") and its games were written as a .tsv
set -u
S=$(cat ~/grok2_seat.txt); D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$S"
T0=$(date -u -d "$(head -n 1 "$D/stamps.txt" | cut -d' ' -f1)" +%s)
c=$(ls "$D"/chunk_*.tsv 2>/dev/null | wc -l)
while true; do
  c=$((c + 1))
  [ -e ~/STOP_PLAY ] && { echo "stop file"; exit 0; }
  [ $(( ($(date -u +%s) - T0) / 60 )) -ge 95 ] && { echo "minute 95: no new chunk"; exit 0; }
  sed -n "$(( (c - 1) * 250 + 1 )),$(( c * 250 ))p" ~/mine.epd > ~/chunk_$c.epd
  bash ~/match.sh ~/chunk_$c.epd 250 ~/chunk_$c.pgn > ~/chunk_$c.out 2>&1; rc=$?
  if [ $rc -eq 0 ] && grep -q "Finished match" ~/chunk_$c.out && python3 ~/games_tsv.py tsv ~/chunk_$c.pgn "$D/chunk_$c.tsv"; then
    cp ~/chunk_$c.out "$D/chunk_$c.out"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) chunk $c done" >> ~/play.log
  else
    rm -f "$D/chunk_$c.tsv"; echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) chunk $c FAILED rc $rc" >> ~/play.log; exit 1
  fi
done
