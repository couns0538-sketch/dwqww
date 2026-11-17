# THE ENGINE REFUSES AN ILLEGAL FEN AND THEN SEARCHES THE PREVIOUS POSITION, SILENTLY

Build: **PC r15** `068f0927` (and base behaves the same). Threads 1, Hash 16, OwnBook false.

## What happens

```
position fen 8/8/8/8/8/8/1k6/K7 w - - 0 1        <- kings on b2 and a1: ADJACENT, illegal
go depth 12
```

The engine's complete response:

```
info string invalid FEN: kings may not be adjacent
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
...
info depth 12 seldepth 23 score cp 30 nodes 56720 ... pv e2e4 c7c5 g1f3 ...
bestmove e2e4
```

**It diagnoses the FEN correctly, prints one `info string` line, and then searches THE PREVIOUS POSITION.**
In a fresh session the previous position is startpos, which is why the PV above is a real startpos line
(`d2d4 d7d6`, `e2e4 c7c5 g1f3`) and the bestmove is `e2e4` — the answer to a different question.

## The mechanism, pinned down: it is the PREVIOUS position, not startpos

A second test settles which position is substituted, and it is worse than a startpos fallback because it
depends on session history:

```
position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 60     <- VALID K+R v K
go depth 4        ->  bestmove a1a8

position fen 8/8/8/8/8/8/1k6/K7 w - - 0 1             <- INVALID (adjacent kings)
go depth 4        ->  info string invalid FEN: kings may not be adjacent
                      info depth 1 ... score mate 1 nodes 21 pv a1a8
                      bestmove a1a8
```

**The refused FEN left the K+R v K position in place and the engine answered it** — `mate 1`, `a1a8`, the same
answer as the valid position before it. So:

- in a **fresh** session, an invalid FEN silently searches **startpos**;
- in a **long-running** session, it silently searches **whatever position was last set successfully**.

**The second is the more dangerous**, because a harness that measures 200 positions and has one malformed FEN
gets **the previous position's answer recorded under the malformed one** — a duplicate row that looks like a
genuine measurement, with no startpos signature to give it away.

## Why this is severe

**The failure is a diagnostic followed by a result, and the result looks completely valid.** Every harness that
parses `info depth` lines and takes the last one gets:

- a legal bestmove,
- a plausible score (±30 cp is a normal middlegame score),
- a full PV with sensible opening moves,
- correct-looking node counts.

**Nothing in the parsed output says "this is not your position".** The only signal is one `info string` line at
the top — and `info string` is exactly the line class most harnesses skip, because it is conventionally
informational.

Consequences for the run:

1. **A harness that does not check for `invalid FEN` silently measures startpos** and records it under the
   position's name. Its numbers are not wrong-looking; they are *another position's* numbers.
2. **It is worse than a refusal.** A refusal leaves no bestmove and the harness crashes or aborts. **A silent
   substitution produces a complete, publishable row about the wrong board.**
3. It compounds with everything else in `METHOD_NOTES`: a node figure that does not name its search, a depth
   that does not name its position.

## How it was found, which is the point

I was testing whether `go depth 200` exceeds the `max_depth <= 64` clamp that seat 23 documented. I picked
`8/8/8/8/8/8/1k6/K7 w` as a near-empty board where deep search would be fast. **Three different commands —
`go depth 70`, `go depth 200`, and `go infinite` — all returned exactly 34 lines and identical timings**, which
is impossible for three different limits.

That "impossible" was the tell. The cause was not the clamp: **all three were searching startpos**, which takes
~34 lines to reach depth 34 in my time budget. The near-empty board would have finished depth 70 trivially.

**The general lesson: when two different limits produce identical output, suspect that the input never arrived.**
A command-line limit that has no effect is more likely a refused position than a broken limit — and the engine
told me so on line 1, in a line I was not reading because I was counting `info depth` lines.

## The guard, which I already had and did not apply

My own `pc/sign_test_19c46.py` and `pc/forced_mate.py` call `chess.Board(fen).is_valid()` before measuring,
because of S-C59. **The ad-hoc probes I wrote for this test did not** — I typed FENs directly into a subprocess
and validated nothing. The rule was written, proven, and then skipped in the ad-hoc path, which is the
"guard you have to remember to run" failure for the third time tonight.

**Two fixes, both mechanical:**

1. **Validate every FEN with python-chess before it reaches the engine** (what my main harnesses already do).
2. **After sending `position`, read the reply lines and abort on `invalid FEN`.** The engine gives a per-position
   verdict; a harness that ignores it has no defence at all. `check_08c33_matrix.py` does this; the ad-hoc code
   did not.

## What the engine does right, and what is arguable

- It **does** detect the error and **does** say so. `info string invalid FEN: kings may not be adjacent` is a
  specific, correct message, and the board validation (board.cpp) is doing its job.
- **The arguable part is what follows.** Continuing with the previous position is a defensible design for a GUI
  (the GUI has usually not changed anything and the old position is still valid), but **for a UCI consumer it
  is indistinguishable from success.** A `bestmove` that answers a different position is the same class as the
  drawn-root defect: a legal answer to a question nobody asked.

**This should be reported to the owner as a harness hazard rather than an engine bug**, because the engine's
behaviour may be intentional while every harness's silent acceptance of it is not. But it belongs next to the
`bestmove 0000` and empty-`info depth` findings, because it is the third way this engine can return a
well-formed answer that does not describe the position you sent.

## Limit of this report

- **PC r15** only for the transcript above; I did not re-run base, though the parser is shared (`board.cpp`
  validation plus the same UCI loop), so the behaviour is very likely identical. Stated as unverified.
- **Now tested and answered**: the engine keeps the *previous* position (see "The mechanism, pinned down"
  above). The remaining untested question is whether a FEN invalid in a *different* way (bad rank count,
  wrong field count) follows the same path — one example of each would settle it, and I have not run them.
- The engine's behaviour may be **deliberate** (a GUI usually still holds a valid position). The hazard is
  every harness's silent acceptance, not necessarily the engine's choice.
