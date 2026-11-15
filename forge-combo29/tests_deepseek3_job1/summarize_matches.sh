#!/bin/bash
# Collect the fastchess summary block of every match plus fault counts.
# Reads only fastchess's own final output; nothing is recomputed by hand.
cd "$(dirname "$0")/logs" || exit 1
for d in M1_* M2_* M3_* M4_* M5_*; do
  [ -d "$d" ] || continue
  echo "===== $d"
  if [ -f "$d/last40.txt" ]; then
    grep -E '^(Results of|Elo:|Games:|Ptnml|LOS:)' "$d/last40.txt" | sed 's/^/  /'
    echo "  faults: crash=$(grep -ci 'crash' "$d/full.txt") disconnect=$(grep -ci 'disconnect' "$d/full.txt") illegal=$(grep -ci 'illegal' "$d/full.txt") time_forfeit=$(grep -ci 'loses on time' "$d/full.txt")"
    echo "  games_in_games_txt: $(wc -l < "$d/games.txt")"
    echo "  stamps: $(tr '\n' ' ' < "$d/stamps.txt")"
  else
    echo "  INCOMPLETE (no summary yet); games finished so far: $(grep -c '^Finished game' "$d/full.txt" 2>/dev/null)"
  fi
done
