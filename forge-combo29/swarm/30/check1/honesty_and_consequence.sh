#!/usr/bin/env bash
# check1 part C: honesty numbers of the patched build + the consequence check for the fix.
set -u
EXE=${1:?exe}
OUT=${2:?outdir}
mkdir -p "$OUT"
{
  date -u
  echo "\$ sha256sum $EXE"; sha256sum "$EXE"
  echo "\$ printf 'uci\nisready\nbench N\nquit\n' | $EXE   (fresh process per line)"
} > "$OUT/honesty.txt"
for n in 11 13 16; do
  printf 'uci\nisready\nbench %s\nquit\n' "$n" | "$EXE" 2>&1 | grep -E '^info string bench' | sed "s/^/bench $n: /" >> "$OUT/honesty.txt"
  date -u >> "$OUT/honesty.txt"
done
printf 'uci\nisready\nposition startpos\ngo perft 5\nquit\n' | "$EXE" 2>&1 | tail -1 | sed 's/^/perft 5: /' >> "$OUT/honesty.txt"
date -u >> "$OUT/honesty.txt"
echo "--- expected: 312866 / 862329 / 3024920 / 4865609"
cat "$OUT/honesty.txt"
echo
echo "=== CONSEQUENCE of removing the halfmove>=100 term: is a real fifty-move DRAW still adjudicated?"
echo "--- board WITH a forced mate present, counter 100 (must search and find the mate):"
printf 'uci\nisready\nposition fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1\nisready\ngo depth 6\nisready\nquit\n' | "$EXE" 2>&1 | grep -E 'score|^bestmove' | tail -2
echo "--- board with NO mate and counter 120 (fifty-move draw is CLAIMABLE; the engine should not"
echo "    pretend the position is lost/won -- record what it says):"
printf 'uci\nisready\nposition fen 6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 120 1\nisready\ngo depth 8\nisready\nquit\n' | "$EXE" 2>&1 | grep -E 'score|^bestmove' | tail -2
echo "--- the same board and counter on the UNPATCHED release build:"
printf 'uci\nisready\nposition fen 6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 120 1\nisready\ngo depth 8\nisready\nquit\n' | /home/ubuntu/b/rel/forge 2>&1 | grep -E 'score|^bestmove' | tail -2
date -u
