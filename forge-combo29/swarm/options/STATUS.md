# STATUS — option-surface audit

Written at 07:12Z. Run closes 10:08Z. Push deadline 09:30Z.

## One-line state

The **tunables matrix is complete and clean (51/51)**; the **pin sweep is
complete and clean (18/18 preserve perft 5)**; the **interference/no-effect
sweep is a null with a scope limit that is itself the finding**. The **18-switch
five-property table is the part that did not finish** — §4 says exactly how far
it got and why the missing cells must not be read as passes.

## 1. Done and verified

| item | result | evidence |
|---|---|---|
| Honesty pins, baseline | bench 11/13/16 = 312866 / 862329 / 3024920, perft 5 = 4865609, all exact | `evidence/pins-per-switch.json` |
| Perft 5 under each of the 18 switches | **18/18 = 4865609**, baseline reproduces all four pins | `evidence/pins-per-switch.json` |
| **51 tunables × 5 values** | **255 cells: 51/51 rows correct, 0 crashes, 0 failures** | `evidence/tunables.json` |
| Tunables that move the search | **51/51** — none inert | `evidence/tunables.json` |
| Six divisor tunables at their minimum | all search and return; no zero divisor reachable | `evidence/tunables.json` |
| Mate wire-format calibration | mapping measured on 24 fixtures, consistent 24/24 | `evidence/mate-format-calibration.json` |
| Mate prover self-test | 7/7 agree with unpruned minimax, both signs | `scripts/prover_selftest.py` |
| Baseline 5-property run | legality 200/200, mate 24/24 PV-verified 0 unsound, terminal 6/6, bail 4/4 | `evidence/` (see §4) |

## 2. The pin sweep in full, because it is a positive result

Bench node counts move for 15 of 18 switches, which is expected: `bench` is a
search, and a search heuristic changes the search. Reporting that as a pin
violation would drown the real signal.

**Perft is the pin a search switch cannot legitimately move.** It walks every
legal move to a fixed depth and never consults evaluation, history, pruning or
the clock, so a switch that moves perft has touched move generation or the board.
**All 18 leave perft 5 at exactly 4,865,609**, and the baseline reproduces all
four pins before any switch is tried.

Three switches move nothing on either bench: `DeadMaterial`, `TmFinishIteration`,
`TmNodeShare`. `LmrSignedCorrection` moves bench 16 by 207,598 nodes while
leaving bench 11 bit-identical — a reminder that "no change at bench 11" is not
"no effect".

## 3. Why §2's interference null is weaker than it reads

Every option handler is a plain assignment (`src/uci.cpp:383-473`), so setting A
then B leaves the same stored pair as B then A. **Order-independence is true by
construction**, and 0-of-16 order-dependent pairs is the expected result rather
than a discovery.

The report's `UseNNUE > NNUEArch > NnueFile` precedence is **gating on a value**,
not ordering of commands. An order test therefore cannot find a second instance
of it; a value test can. The no-effect sweep is the value test, it ran, and it
found only `OwnBook` (fires on clock forms, not `go depth` — known) and `NnueFile`
(embedded net, `UseNNUE` true — known gating). **No new inert option.**

## 4. NOT done — the 18-switch table

This is stated plainly because a partial table that reads as a full one is the
defect this audit's rules exist to prevent.

**Completed for all 18 switches:**
* 4 honesty pins each, including perft 5 (above).

**Completed for 1 of 18 switches:**
* `ContHist4PlyRead` — full five-property run.

**Completed for 0 of 18 switches:**
* ASan+UBSan per switch. The sanitizer pipeline itself is **built and proved
  live**: the clean binary carries 35 `__asan_` and 15 `__ubsan_` symbols with
  `-fsanitize=address,undefined` in its own `flags.make`, and a control binary
  with planted faults caught a heap-buffer-overflow (exit 1) and a
  signed-integer-overflow (exit 3), each naming its source line. One full
  per-switch sanitizer pass (`QuietExtinction`) ran 200/200 positions with 0
  sanitizer hits. The remaining 17 did not fit in the run.

**What the missing cells mean:** `NOT RUN`. They are rendered as `NOT RUN` in
`FINDINGS.md`, never as PASS. The audit produced no evidence against any switch;
it produced evidence for one.

## 5. Time budget and what happens next

* 07:12Z — this file written; branch pushed with what is verified.
* Remaining time goes to: the interference re-run's control fix, then as many
  switch arms as the clock allows, checkpointing after each so every arm that
  finishes is durable.
* If the switch table is still partial at the push deadline, it ships partial
  with §4 intact rather than being described as complete.

## 6. Honest summary of value

The tunables row is the substantive new result: the largest untouched block,
255 cells, no crash, no silent clamp mismatch, and — the part a clamp-only check
would have missed — **every one of the 51 demonstrably reaches the search**. The
interference section's value is the correction in §3, not its null.
