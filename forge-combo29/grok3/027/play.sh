#!/usr/bin/env bash
# play.sh: chunks from the top of ~/mine.epd, one after another, until minute 46, ~/STOP_PLAY, or the 300 lines kept
# for the controls; a chunk counts only when fastchess ended it ("Finished match") and its games were written as a
# .tsv; every counted chunk is committed and pushed at once
set -u
S=$(cat ~/grok3_seat.txt); R="$(cat ~/grok3_repo.txt)"; D="$R/forge-combo29/grok3/$S"; CH=$(cat ~/grok3_chunk.txt)
T0=$(date -u -d "$(head -n 1 "$D/stamps.txt" | cut -d' ' -f1)" +%s)
LAST=$(( $(wc -l < ~/mine.epd) - 300 ))
c=$(ls "$D"/chunk_*.tsv 2>/dev/null | wc -l)
while true; do
  c=$((c + 1))
  [ -e ~/STOP_PLAY ] && { echo "stop file"; exit 0; }
  [ $(( ($(date -u +%s) - T0) / 60 )) -ge 46 ] && { echo "minute 46: no new chunk"; exit 0; }
  [ $(( c * CH )) -gt "$LAST" ] && { echo "openings used up"; exit 0; }
  sed -n "$(( (c - 1) * CH + 1 )),$(( c * CH ))p" ~/mine.epd > ~/chunk_$c.epd
  bash ~/match.sh ~/chunk_$c.epd "$CH" ~/chunk_$c.pgn > ~/chunk_$c.out 2>&1; rc=$?
  if [ $rc -eq 0 ] && grep -q "Finished match" ~/chunk_$c.out && python3 ~/games_tsv.py tsv ~/chunk_$c.pgn "$D/chunk_$c.tsv"; then
    cp ~/chunk_$c.out "$D/chunk_$c.out"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) chunk $c done" | tee -a ~/play.log >> "$D/stamps.txt"
    ( cd "$R" && git add "forge-combo29/grok3/$S/chunk_$c.tsv" "forge-combo29/grok3/$S/chunk_$c.out" \
        "forge-combo29/grok3/$S/stamps.txt" && git commit -q -m "grok3 $S chunk $c" \
        && git push -q origin "HEAD:refs/heads/for-fable-and-opus/grok3-$S" ) \
      || echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) chunk $c: commit or push FAILED" >> ~/play.log
  else
    rm -f "$D/chunk_$c.tsv"; echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) chunk $c FAILED rc $rc" >> ~/play.log; exit 1
  fi
done
