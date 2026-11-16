#!/usr/bin/env bash
# perft2_identity.sh EXE MOVESFILE OUT — proves which position the engine keeps when an
# illegal move follows a long legal list: perft 2 of the full list, of the 999-ply prefix,
# and of "full list + illegal move". If the engine kept the 999-ply prefix the third number
# would equal 1427, not 1485.
set -u
EXE="$1"; MOVES="$2"; OUT="$3"
M=$(tr '\n' ' ' < "$MOVES")
P999=$(head -n 999 "$MOVES" | tr '\n' ' ')
{
  echo "exe: $EXE"
  echo "moves: $MOVES ($(wc -l < "$MOVES") plies)"
  echo
  echo "== full 1000-ply list, go perft 2"
  printf 'uci\nposition startpos moves %s\nisready\ngo perft 2\nquit\n' "$M" | "$EXE" | grep -E '^nodes'
  echo
  echo "== 999-ply prefix, go perft 2"
  printf 'uci\nposition startpos moves %s\nisready\ngo perft 2\nquit\n' "$P999" | "$EXE" | grep -E '^nodes'
  echo
  echo "== full 1000-ply list + illegal move e1e3, go perft 2"
  printf 'uci\nposition startpos moves %s e1e3\nisready\ngo perft 2\nquit\n' "$M" | "$EXE" | grep -E '^nodes|illegal move'
  echo
  echo "== perft 1 of the same three (the ambiguous check the report warns about)"
  for label in full prefix999 full_plus_illegal; do
    case $label in
      full) L="position startpos moves $M";;
      prefix999) L="position startpos moves $P999";;
      full_plus_illegal) L="position startpos moves $M e1e3";;
    esac
    printf 'uci\n%s\nisready\ngo perft 1\nquit\n' "$L" > /tmp/p1.in
    printf '%s perft1: ' "$label"
    "$EXE" < /tmp/p1.in | grep -E '^nodes'
  done
} | tee "$OUT"
