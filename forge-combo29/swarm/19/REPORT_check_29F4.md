# Verifying 29-F4: the king-lines waste reproduces exactly, and holds under the settings it did not test

seat 19 · area 9 · build **PC r15** + call counters · PC r15 default **and PC20** · Threads 1 · cold.

## 1. The three lines

**What was asked** — nothing specific; this is a check of another seat's finding, in my area, using a counter
build. 29-F4 claims `Board::refresh_king_lines()` runs **804,371 times per `bench 13`** and that **779,027** of
those come from `has_legal_move()`, which reads only the `pinned` set — so the discoverer set and five magic
check-square sets computed there are discarded on that path.

**The answer.** **Both numbers reproduce exactly, digit for digit**, and the ratio is the same under settings seat
29 did not test: **804,371 total / 779,027 from `has_legal_move` = 96.8 %** on bench 13 default; **2,826,465 /
2,731,439 = 96.6 %** on bench 16 default; **547,691 / 532,093 = 97.2 %** on bench 13 under **PC20**.

**How sure.** Exact. I instrumented `refresh_king_lines()` with a call counter and a flag set inside
`has_legal_move()`, built the PC r15 tree with it, and read the counters from the engine's own stderr at exit. The
match to seat 29's 804,371/779,027 is not approximate — it is the same integers.

## 2. The numbers

| run | total refreshes | from `has_legal_move()` | share |
|---|---|---|---|
| bench 13, default | **804,371** | **779,027** | **96.8 %** |
| bench 16, default | 2,826,465 | 2,731,439 | 96.6 % |
| **bench 13, PC20** | 547,691 | 532,093 | **97.2 %** |

Seat 29's committed figures for bench 13 default were **exactly** 804,371 and 779,027 — reproduced.

**What is new here:** seat 29 measured only the default regime. **The waste is if anything slightly worse under
PC20** (97.2 % vs 96.8 %), so its conclusion is not weakened on the settings the owner actually uses. And at
bench 16 the total scales with nodes (2.83 M vs 0.80 M) while the ratio is unchanged — so this is a per-node cost,
not a depth-dependent one, unlike the transposition table (19-F35).

## 3. On seat 29's own judgement

29-F4 says removing the waste is "provably bit-exact but worth only **0.056 % of instructions**, so it is not a
speed win". I did not re-measure the instruction share (valgrind cannot run this engine — 19-F41), but the
call counts and the ratio both support the *shape* of that conclusion: a 97 %-redundant call that costs 1.47 % of
runtime self time can only be freed by making each call cheaper, not by removing calls, unless the cheaper path
is a different function. **Seat 29's decision to record it and not chase it looks right**, and its honesty in
quantifying a fix it then declined to make is the standard the brief asks for.

## 4. Finding

**19-C19 — CONFIRMS seat 29's 29-F4 exactly, and extends it to the settings it did not test.** `refresh_king_lines()`
runs **804,371** times per bench 13 with **779,027 (96.8 %)** from `has_legal_move()`; **2,826,465 / 2,731,439
(96.6 %)** at bench 16; and **547,691 / 532,093 (97.2 %)** on bench 13 under PC20. The redundancy is a **per-node
constant** (ratio unchanged across depths) and is marginally *worse* under the owner's settings, so 29-F4's "not
a speed win" conclusion is not weakened by the regime it did not test.

### What I did NOT do

- I did not re-measure the 0.056 % instruction share; `valgrind` cannot run this build (19-F41), so I cannot
  independently confirm that figure — only the call counts it rests on.
- I did not write the bit-exact patch. Seat 29 already argued it is not worth it, and my counters agree with the
  premise rather than adding a reason to do it.
- Only bench 13/16 default and bench 13 PC20; not a `go`-driven workload.

## 5. Files

`checks/klines/verify.txt`; the instrumented tree is `~/klines` (scratch, not committed) with the counter
inserted at `src/board.cpp`'s `refresh_king_lines` and a flag set in `has_legal_move`.
