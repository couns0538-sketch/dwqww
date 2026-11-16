#!/usr/bin/env bash
# assert_composition.sh <exe>
# ONE assertion a merger can run to prove that BOTH seat 12's two_doors_mate patch and seat 27's
# drawn_root_reporting patch are in effect in the tree they just built.
#
# Position: 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60  (clock 100 = fifty-move claim, White has Ra8#).
#
#   base (no patch)          : bestmove f2f3, score cp 0, every info line has an EMPTY pv
#                              -> the draw adjudication wins and hides the mate  (this FAILS the assert)
#   seat 12's patch only     : bestmove a1a8, score mate 1, real search with a pv
#   seat 12 + seat 27's      : same as above (seat 27 changed the REPORTING of a drawn root, not the
#                              choice here, because finding the mate makes the root not drawn)
#   seat 27's patch only     : bestmove f2f3, score cp 0, but EXACTLY ONE info line instead of eight
#                              (this is the discriminator for seat 27's patch when used alone)
#
# So the assertion for the COMBINED tree is: bestmove is a1a8 AND a `score mate 1` line is present.
# Exit 0 with PASS only then; anything else prints FAIL and exits 1.
#
# stdin stays open past the go line: closing it early makes this build answer a fabricated bestmove
# (seat 19's 19-F12), which would make the assertion meaningless.
set -u
EXE=$(readlink -f "${1:?usage: assert_composition.sh <exe>}")
FEN="6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60"
OUT=$(mktemp)

{ printf 'uci\nisready\nucinewgame\nisready\nposition fen %s\nisready\ngo depth 8\n' "$FEN"
  sleep 4
  printf 'quit\n'
} | timeout 120 "$EXE" > "$OUT" 2>&1

BM=$(grep -E '^bestmove' "$OUT" | tail -1 | awk '{print $2}')
NINFO=$(grep -cE '^info depth' "$OUT")
MATE1=$(grep -cE '^info depth [0-9]+ .*score mate 1 ' "$OUT")
PVDEPTH=$(grep -E '^info depth' "$OUT" | tail -1 | awk '{print $NF}')

echo "exe         : $EXE"
echo "sha256      : $(sha256sum "$EXE" | awk '{print $1}')"
echo "bestmove    : ${BM:-<none>}            (want a1a8)"
echo "score mate 1 lines : $MATE1            (want >= 1)"
echo "info lines  : $NINFO            (8 = a real search; 1 with cp 0 = seat 27's patch alone on a drawn root)"
echo "last pv     : ${PVDEPTH:-<none>}"
echo "raw         : $OUT"
echo "---"
grep -E '^info depth|^bestmove' "$OUT" | tail -4 | sed 's/^/  /'
echo "---"

if [ "${BM:-}" = "a1a8" ] && [ "${MATE1:-0}" -ge 1 ]; then
  echo "PASS: seat 12's mate scan beats the draw adjudication and the search really ran"
  exit 0
fi
echo "FAIL: expected bestmove a1a8 and at least one 'score mate 1' info line"
echo "      (bestmove f2f3 + cp 0 + empty pv = seat 12's patch is NOT in this tree)"
exit 1
