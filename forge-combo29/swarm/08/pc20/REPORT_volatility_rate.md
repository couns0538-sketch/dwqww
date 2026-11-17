# How often is a self-play target materially wrong? — seat 08, PC r15 under PC20, Threads 1

The rate the owner can act on. Owner's clock **6 s + 0.06/move**, PC20, Threads 1, Hash 16. Per board: the clocked
search's score at its stop depth D, compared with a COMPLETED `go depth D+4` (a deeper, finished search).

30 boards per class requested; the sparse class yielded 27 usable plus 3 whose depth-(D+4) reference did not finish
in 90 s, and those are reported rather than dropped.

## The counts (counts, not ratios, as asked)

| class | boards | **mate involved** | gap ≥ queen (≥900 cp) | gap ≥ 200 cp | **either (mate or ≥200 cp)** |
|---|---|---|---|---|---|
| **sparse (≤12 pieces)** | 27 | **10** | **0** | **0** | **10 of 27 = 37 %** |
| **real-game set G / full material (≥20 pieces)** | 30 | **0** | **0** | **0** | **0 of 30 = 0 %** |

Also reported by the harness:
| class | clocked searches that did not answer in 90 s | depth-(D+4) references that did not finish in 90 s |
|---|---|---|
| sparse | **0** | **3** |
| full material | 0 | 0 |

## What this says, plainly

- **In the sparse class, 10 of 27 boards (37 %) have a MATE that the clocked search has not found at the depth the
  clock buys.** Not a 200 cp difference, not a pawn: the score the self-play would record is a centipawn evaluation
  of a position that is actually a forced mate.
- **Zero of those 10 were "gap ≥ queen"** in the centipawn sense — because a mate score and a centipawn score are
  different kinds of number, and I count them as an event, not a magnitude. The 10 ARE the material-error cases; they
  simply express as `cp …` → `mate …` rather than as a large centipawn delta. Quoting "0 boards with a queen gap"
  without the mate count would understate the problem completely, so both are in the same table.
- **On the real-game / full-material class the answer is 0 of 30 for everything.** The clocked score was within
  113 cp of the deeper score on every board, median 14 cp. So the training-data risk is **class-specific**, not a
  general property of the engine.
- **The sparse class's cp-only movement is modest** (median 171 cp, largest 171 cp, 1 board moved). So the sparse
  class's error is almost entirely the mate case, not gradual drift.

## The rate in one sentence for the owner

If his self-play samples positions with **12 pieces or fewer**, roughly **one board in three records a score for a
position whose true evaluation is a forced mate** — so those targets are not merely noisy, they are the wrong kind of
number. If his self-play positions come from **real games at full material**, the measured error is **zero in 30
boards**, and the training-target risk does not appear at all.

## Three references that did not finish in 90 s

Three sparse boards' `go depth D+4` searches ran past 90 s and were killed. Those are the boards where four extra
plies are enormously expensive — the same phenomenon as the time tail (08-F28), now appearing in the reference
search. They are counted as "not finished", not as successes and not as failures.

## A harness bug I hit and fixed, because it would have inverted this result

My first version used `select()` on a text-mode buffered pipe to enforce the 90 s cap. On Python's buffered text
streams `readline()` reads ahead, so `select` can report "not ready" while complete lines sit in the process's own
buffer — the harness hung and reported **clocked searches as 90 s timeouts** on boards that actually answer in
**194 ms** (verified by hand). Had I trusted it, this report would have said "the sparse class hangs", which is
false. Fixed by replacing `select` with a reader thread and a deadline; the committed script is the fixed version,
and every per-board row is in `volatility_rate.txt.jsonl`.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 volatility_rate.py /tmp/vr.txt 30
    # per-board rows: /tmp/vr.txt.jsonl ; skipped boards with reason: /tmp/vr.txt.skip
