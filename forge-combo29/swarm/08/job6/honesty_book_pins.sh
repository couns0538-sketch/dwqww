#!/usr/bin/env bash
# honesty_book_pins.sh — do the four PINNED honesty numbers depend on OwnBook? One fresh process per line,
# raw output kept, run twice: OwnBook true (default) and OwnBook false.
set -u
EXE="$HOME/builds/release/forge"
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"
OUT=honesty_book_pins.txt
: > "$OUT"

sha256sum "$EXE" | tee -a "$OUT"

for ob in true false; do
  echo "" | tee -a "$OUT"
  echo "## OwnBook $ob" | tee -a "$OUT"
  echo '```' | tee -a "$OUT"
  for b in 11 13 16; do
    {
      printf 'uci\nsetoption name OwnBook value %s\nisready\nucinewgame\nisready\nbench %s\n' "$ob" "$b"
      sleep 0.1
      printf 'quit\n'
    } | "$EXE" 2>&1 | grep -E 'info string bench' | tee -a "$OUT"
  done
  # perft 5: synchronous, so a piped quit cannot corrupt it (verified earlier)
  {
    printf 'uci\nsetoption name OwnBook value %s\nisready\nucinewgame\nisready\nposition startpos\ngo perft 5\n' "$ob"
    sleep 0.3
    printf 'quit\n'
  } | "$EXE" 2>&1 | grep -E '^nodes ' | tee -a "$OUT"
  echo '```' | tee -a "$OUT"
done

cat >> "$OUT" <<'EOF'

## the four pins, both settings, side by side
EOF
grep -E 'info string bench|^nodes ' "$OUT" | sed 's/.*nodes /nodes /;s/ time .*//;s/^nodes /perft5 nodes /' | tee -a "$OUT"
