# Harness traps: absence of output is not absence of function

Three cases, one shared tell. Full note (with the cross-reference to the stale-shard fault) lives in the
project store at `internal/absence-of-output-traps.md`; this file is the pointer so a reader here finds it.

| # | command | looks like | actually is |
|---|---|---|---|
| 1 | `quit` while a search runs (19-F12) | a legal-looking `bestmove a2a3` | search aborted; first move in generation order |
| 2 | `depth 64` at a low node count (S-F14) | a search that reached depth 64 | a hard cap on the reported depth counter |
| 3 | a book move (S-F15) | a hang / empty failure (no `info` lines) | a legitimate instant book answer |

**The tell:** the engine's output reports what it *did*, not what you asked for. A move with no search
behind it, a depth with no nodes behind it, or silence where you expected a line — that disagreement IS
the signal.

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
