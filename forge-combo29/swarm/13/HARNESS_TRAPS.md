# Harness traps: absence of output is not absence of function

Five cases, four instrument lessons, one shared tell. Full note (with the cross-reference to the stale-shard fault) lives in the
project store at `internal/absence-of-output-traps.md`; this file is the pointer so a reader here finds it.

| # | command | looks like | actually is |
|---|---|---|---|
| 1 | `quit` while a search runs (19-F12) | a legal-looking `bestmove a2a3` | search aborted; first move in generation order |
| 2 | `depth 64` at a low node count (S-F14) | a search that reached depth 64 | a hard cap on the reported depth counter |
| 3 | a book move (S-F15) | a hang / empty failure (no `info` lines) | a legitimate instant book answer |
| 4 | a third-occurrence repetition passed as a bare `position fen` (S-F17) | a green test | a vacuous one: a FEN carries no occurrence history, so it could never fail |
| 5 | an illegal FEN refused, then answering from the PREVIOUS board (S-F18) | an illegal move from the ending you set up | a legal move from startpos: the FEN was refused and the old board stayed |

**The tell:** the engine's output reports what it *did*, not what you asked for. A move with no search
behind it, a depth with no nodes behind it, or silence where you expected a line — that disagreement IS
the signal. And when expected and observed *agree* on a test that could not have failed, that agreement
is not evidence either.

**The generalising fix (cases 4 and 5):** assert the INPUT CONSTRUCTION, not just the outcome — that the
position really occurs three times (counted the way the engine counts: pieces, side, castling, ep — not by
full FEN), that the halfmove clock really is >= 100, that the search really ran (nodes > 0), that a
`book move` line was really present, and that the FEN was ACCEPTED (`is_valid()` and not
`STATUS_OPPOSITE_CHECK` in python-chess). A guard that raises on a bad construction turns a silent false
pass into a loud failure.

**The rule:** make absence loud. If a line you need does not arrive, fail and print "not shown". Never
fall through to a count of zero, and never print a verdict from a run in which the thing you were
measuring never happened.

Verified on the PC r15 build on 2026-11-16:
```
printf 'uci\nisready\nposition startpos\ngo depth 12\nquit\n' | ./forge | tail -1     # bestmove a2a3
{ printf 'uci\nisready\nposition fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1\ngo nodes 20000\n';
  sleep 2; printf 'quit\n'; } | ./forge | grep -c 'info depth'                        # 64
{ printf 'uci\nisready\nsetoption name OwnBook value true\nisready\nposition fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\ngo movetime 200\n';
  sleep 2; printf 'quit\n'; } | ./forge | grep -E 'book|bestmove'                    # book move e2e4 / bestmove e2e4
```

## Two lessons about the INSTRUMENTS

**A. A markdown table is not validated by looking at it.** Seven rows of this project's FINDINGS.md became
malformed because literal pipes inside shell commands (`grep 'a|b'`) and arithmetic (`2|M|-1`) split table
cells — and a broken markdown table renders identically to a working one in a terminal. Caught only by
`FINDINGS_check.py`, which asserts every S-F row has 7 columns, every S-C row 6, and no missing ids. If you
edit a document programmatically and someone else will read it, assert its structure; renderability is not
something you can eyeball.

**B. A checker that disagrees with itself is the checker working.** When I mis-set that checker's own
expectation to 5 columns, it flagged all four S-C rows — correctly, given the wrong assumption it had been
handed. The output looked like "all my rows are broken". Same disposition as case 4: suspect the instrument
before believing its verdict, and when a check flags *everything* uniformly, suspect its assumption rather
than each row independently.

**C. The comment can be wrong while the measurement is right.** In the over-65535 counter check, the
printed value `perft 1 = 17` was correct but the hand-typed annotation beside it said "the mate board gives
38" when the board has 17 legal moves. That is the inverse of the usual failure — normally the number is
wrong and the label right, so you read the label and miss the number. Here a plausible annotation lends a
trustworthy figure an authority the annotation never earned. Either compute the expected value or keep it
out of the output line; never hand-type an expectation next to a measurement.

**D. A rate needs a non-zero denominator.** My first truncation check used 28 ordinary positions that produced
zero mate claims at every budget, so "0 truncated" was the same number a clean engine gives — the test could
not fail. Rebuilt mate-rich, it gave 20 claims with 1 truncated. Print the denominator beside every rate:
"0 truncated" means nothing without "N mate claims" next to it.
