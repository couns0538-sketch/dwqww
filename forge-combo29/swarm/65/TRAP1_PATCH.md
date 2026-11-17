# TRAP1_PATCH.md — the clock-gate fix, and what "unbounded" actually cost

Status: **measured, not merged.** Diff in
`patches/trap1-clock-gate-both-clocks.patch`, applied and verified by
`scripts/patch_trap1_clock_gate.sh`. The engine tree is untouched.

Base: `6b98f217`. All 11 documented pins verified on both the lock and patched
builds before anything was recorded.

---

## The defect

`parse_limits` stored a clock in `limits.time_ms` only when it belonged to the
**side to move** (`src/uci.cpp:121-122`):

```cpp
else if (token == "wtime") { const std::int64_t value = read_clock(); if (side == forge::White) limits.time_ms = value; }
else if (token == "btime") { const std::int64_t value = read_clock(); if (side == forge::Black) limits.time_ms = value; }
```

A harness that sends only the opponent's clock therefore looks to the engine like a
harness that sent no clock at all. Two consequences, and the second is much worse
than the first:

1. the book gate tests `limits.time_ms >= 0`, so the book does not fire;
2. nothing else is time-limited either — the search has **no budget at all** and
   runs until `stop`.

## The patch

Record both clocks under their own names, then resolve the budget once the whole
command is parsed: the mover's clock when it was given, otherwise the opponent's.
The increment follows the same rule.

```cpp
else if (token == "wtime") { wtime_ms = read_clock(); }
else if (token == "btime") { btime_ms = read_clock(); }
else if (token == "winc")  { winc_ms  = read_clock(); }
else if (token == "binc")  { binc_ms  = read_clock(); }
...
if (own_time >= 0)      { limits.time_ms = own_time;   limits.increment_ms = own_inc; }
else if (other_time >= 0) { limits.time_ms = other_time; limits.increment_ms = other_inc; }
```

The order matters and is tested: a caller that sends its own clock takes the first
branch exactly as before, so no existing caller changes behaviour. The fallback
engages only when the mover's clock is absent.

**Unlike the trap-2 patch, node-neutrality is not automatic here** — `time_ms` feeds
the time manager, so a mistake could change how a timed search spends its budget.
That is why all 11 pins are checked rather than assumed safe.

## Pins: unchanged

`evidence/trap1-pins-{lock,fix}.txt`. Identical on both builds, and the script
diffs the two files:

```
net on  (UseNNUE true):  312866 / 862329 / 3024920 / 12389307 / 34048354
net off (UseNNUE false): 375354 / 907205 / 2448617 / 13573040 / 24506465
perft 5 startpos:        4865609
```

## Before and after

`evidence/trap1-effect.txt`. Window: 25 s to answer on its own.

| case | lock | patched |
| --- | --- | --- |
| white, ONLY `btime` | **no bestmove in 25 s (unbounded)** | answers in 0.0 s, BOOK e2e4 |
| white, ONLY `wtime` | answers 0.0 s, BOOK c2c4 | answers 0.0 s, BOOK c2c4 |
| black, ONLY `btime` | answers 0.0 s, BOOK c7c5 | answers 0.0 s, BOOK c7c5 |
| black, ONLY `wtime` | **no bestmove in 25 s (unbounded)** | answers 0.0 s, BOOK c7c5 |
| white, both clocks | answers 0.0 s, BOOK e2e4 | answers 0.0 s, BOOK e2e4 |
| black, both clocks | answers 0.0 s, BOOK e7e5 | answers 0.0 s, BOOK e7e5 |

The asymmetry is gone: both colours now book whichever single clock is supplied.

### The number worth having: unbounded → bounded, on a no-book position

The rows above prove the **book** fires, and a book reply returns instantly without
consulting the time manager. So they do *not* by themselves prove the search is now
bounded. The test was therefore repeated on a position with **no book entry**, where
only the time manager can produce an answer:

| case (no-book position) | lock | patched |
| --- | --- | --- |
| white, ONLY `btime 10000` | **25.00 s, no answer** | **0.33 s, answered `a4c6`** |
| white, both clocks (control) | 0.35 s, answered | 0.36 s, answered |

That is the conversion the coordinator asked for: an unbounded search becomes a
0.33 s answer, and it matches the both-clocks control to within 20 ms — so the
clock reached the time manager rather than being short-circuited by the book.

The harness control runs first: a form with an unquestionable clock must answer, or
the whole run is void. It did (0.00 s).

## Traps 2 and 3 are unaffected

`evidence/trap1-trap2-3.txt`, patched build: the drawn-root pre-emption is still
present (2/2 entry-bearing roots), and the `Book Depth` counter behaviour is
identical to the lock. That is the expected result — this patch touches
`parse_limits` only — and it is asserted so a future combined patch cannot quietly
change either.

## Interaction with the trap-2 patch

The two patches touch different lines of `uci.cpp` and are independent:

* trap 2 adds a `!root_drawn` predicate to the book gate;
* trap 1 changes how `limits.time_ms` is populated in `parse_limits`.

They compose, and that was **measured rather than assumed**
(`scripts/q18_combined_patches.py`, `evidence/trap1-combined.txt`). A tree at
`6b98f217` with both diffs applied:

| check | result |
| --- | --- |
| all 11 documented pins | reproduce identically |
| fifty-move + book entry | bail `cp 0`, empty pv (trap 2 fixed) |
| repetition + book entry | bail `cp 0`, empty pv (trap 2 fixed) |
| ordinary book position | still books |
| no-book position, only the opponent's clock | answered in **0.36 s** (trap 1 fixed) |
| book position, only `btime` | **books** (both fixes working together) |
| the lock on those last two | unbounded, and does not book |

The last row of the comparison exists so the combined result cannot be read as a
formality: the same probes still fail on the lock, which is what makes the
improvement attributable to the patches.

## What this patch does NOT fix

* Trap 2 — drawn-root pre-emption. Its own patch, `TRAP2_PATCH.md`.
* Trap 3 — not a defect; the diagnosis was retracted. `FINDINGS.md` §5.3.
* A caller that sends **neither** clock still has no time limit. That is correct
  UCI behaviour (`go` with no limit means search until `stop`), and it is
  distinguished from the bug above: the bug was treating "opponent's clock" as
  "no clock".

## A note on the original framing

The first write-up of trap 1 said `go btime` with White to move "does not book".
That is true and it was the least important half. The finding that matters is that
the same root cause leaves the search unbounded, and a harness waiting for
`bestmove` hangs rather than misbehaving visibly. The trap is recorded in
`FINDINGS.md` §4.3 with that consequence first.
