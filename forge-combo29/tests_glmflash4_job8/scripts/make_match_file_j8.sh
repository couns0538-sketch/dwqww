#!/bin/bash
# Build the committed evidence file for one match:
#   line 1: the exact fastchess argv
#   then one line per game: round|white|black|result|opening FEN
#   then the last 40 lines of fastchess's stdout (its own Elo table included)
#   then warning/crash counts.
# usage: make_match_file.sh <match_name> <cand_name>
name=$1
cand=$2
dir=/tmp/matches/$name
out=/agent/repos/dwqww/forge-combo29/tests_glmflash4_job8/matches/${name}_games_and_tail.txt
{
  echo "argv: $(cat "$dir/command.txt")"
  echo "stamps: $(cat "$dir/stamps.txt" | tr '\n' ' ')"
  echo "-- games (round|white|black|result|opening FEN)"
  python3 /tmp/extract_games.py "$dir/match.pgn" /tmp/${name}_games.txt
  cat /tmp/${name}_games.txt
  echo "-- last 40 lines of fastchess stdout"
  tail -40 "$dir/stdout.log"
  echo "-- counts"
  echo "option-warnings: $(grep -c 'Warning;' "$dir/stdout.log")"
  echo "crash/disconnect/illegal/stall lines: $(grep -ciE 'disconnect|illegal|crash|stall' "$dir/stdout.log")"
  echo "abandoned games: $(grep -c 'abandoned' "$dir/stdout.log")"
  echo "-- my pair statistics (cand = $cand)"
  python3 /tmp/elo_stats.py /tmp/${name}_games.txt "$cand"
} > "$out"
echo "wrote $out"
