# Audit: which findings rest on wall time — and the evidence that settles the timer question

## 1. THE EVIDENCE THAT SETTLES IT: my timer against the engine's own `time` field

| ply | my in-process wall | engine's own `time` | difference |
|---|---|---|---|
| 0 | 331.5 ms | 331 ms | 0.5 ms |
| 1 | 449.9 ms | 449 ms | 0.9 ms |
| 2 | **1051.6 ms** | **1051 ms** | 0.6 ms |
| 3 | 455.6 ms | 455 ms | 0.6 ms |
| 4 | **1439.7 ms** | **1439 ms** | 0.7 ms |
| 5 | 909.1 ms | 908 ms | 1.1 ms |

Six consecutive moves of a real game loop at 6 s + 500 ms increment, PC r15, PC20, Threads 1. **Agreement within
about 1 ms on every move**, and a `time 0` search costs my timer **0.74 / 0.81 / 0.68 ms** — the same as seat 15's
0.83 ms. My timer starts immediately after `readyok` and immediately before `go`, which is the correct placement.
**The 1300 ms I blamed in S-W4 was an outer shell loop timing the whole `python3 harness.py …` invocation.**

## 2. What the engine does against its own plan — no clock defect found

Per-row comparison against `clock_plan.hpp` with the CMake defaults, using the clock *before* each move:

| arm | rows | median | max | rows above their own hard limit | by how much |
|---|---|---|---|---|---|
| owner 6s+0.06 (`/tmp/rep4280`) | 89 | 139 ms | 546 ms | 2 | **0 ms** |
| owner 6s+0.06 (`/tmp/op2`) | 200 | 87 ms | 860 ms | 19 | **0-1 ms** |
| control 6s+0.5 (`/tmp/rep4280`) | 65 | 416 ms | 1674 ms | 8 | **0 ms** |
| control 6s+0.5 (`/tmp/op2`) | 200 | 374 ms | 2910 ms | 9 | **0-1 ms** |

**Every row that looks like an overrun is over by 0 or 1 millisecond, which is integer rounding in the engine's own
`time` field.** The engine stops exactly at its hard limit. Rows exceeding the SOFT limit are expected — the soft
limit decides when to stop starting iterations; the hard limit is the cap.

**So: the engine's time management is consistent with its own plan at the owner's control, and no measurement of
mine shows a clock defect.**

## 3. Still unmeasured, and open

Whether the engine's *internal* bookkeeping would forfeit in the games where my harness recorded a forfeit. My
harness decremented each side's clock by that side's think time, which is self-consistent, but that is not the same
as the engine maintaining its own count. After four revisions on this thread I am not going to imply an answer I
have not measured.

## 4. THE TRANSFERABLE LINE

**A claim in nodes, scores, plies or info-line counts survives a harness error; a claim in milliseconds must be
verified against the engine's own `time` field.**

---

## The three that DO rest on wall time — do not quote these

| finding | what it claimed | why it is wall-dependent | status |
|---|---|---|---|
| **S-C11** (and S-C11a) | seat 15's drain is 105 ms, mine 78.6–81.7 ms; forfeit ply differs | every figure is median **wall** per move, and the reconciliation used wall−10 ms | **WITHDRAWN**. The only part that survives is the arithmetic: `Move Overhead` is 10 ms and must be deducted, which is a fact about `uci.cpp`, not a measurement. |
| **S-C11b** (process policy) | warm table is −4 % to −21 % cheaper in nodes | the **node** half is node-based and fine; the **wall** half (120.8 vs 137.2 ms etc.) is wall | **NODE HALF SURVIVES, WALL HALF WITHDRAWN.** The conclusion "table warmth is about −9 % in nodes" stands because it never used time. |
| **S-C11c/d/e** | 19–32 ms drain, 32 % overspend, ply-78/106 forfeits | all wall | **WITHDRAWN** (S-W4). |

**Do not quote:** 19–32 ms/move, 188–322 plies, 32.9 %/32.0 % overspend, the 4280/2910 ms maxima, the ply-78 and
ply-106 forfeits, my 78.6/81.7 ms medians, or any comparison of my drain against seat 15's.

## The findings that do NOT rest on wall time

These were checked one at a time. Each states its claim in nodes, plies, scores or moves.

| finding | central claim | the measure it uses |
|---|---|---|
| S-F1 | drawn root reports every depth with nodes 0 | **nodes 0, info-line count, bestmove** |
| S-F2 / S-P2 | `go nodes` below one iteration returns the generator's first move | **info-line count, bestmove, nodes** |
| S-F3 / S-P3 | hashfull samples 1000 clusters | **hashfull, nodes** |
| S-F4 / S-P4 | Clear Hash keeps the histories | **bestmove, score, nodes** |
| S-F5 | search order changes the answer | **bestmove, score, nodes** (no timing) |
| S-F7 / S-P1..P6 | PC-build inventory | nodes/scores/moves per row |
| S-F8 / S-F8b | `searchmoves` changes the score | **score, nodes** |
| S-F9 | mid-search `setoption` truncates | **info-line count** |
| S-F10 | `eval` is pure | **hval/nnue/total** |
| S-N1 | softnodes deterministic, overshoot 1.02–1.95× | **nodes/N ratio** |
| S-N2 | smaller limit wins | **nodes, depth, bestmove** |
| S-N3 | labels bit-reproducible 48/48 | **bestmove, score, depth, nodes** |
| S-C12 | `go nodes` undershoots (median 0.740 of N) | **nodes/N** |
| S-C13 | no cp-vs-mate split (refuted premise) | **score kind, plies** |
| S-C14 | pos-90 warm stall does not reproduce | **wall** — but the claim is a 348,000 ms vs 26 ms contrast, 4 orders of magnitude apart, and my 1300 ms overhead cannot create or hide a 348-second stall. **Stands, with the caveat stated.** |
| S-C15 | 05-F58 mate-PV truncation | **score, PV plies vs 2N-1, nodes** |
| S-C16 / S-C16a | base plays a non-mate at counter ≥ 100 | **bestmove, score, nodes** |
| S-C17 | 19-F59 discrepancy | **withdrawn separately** (impossible score on KRvK) |
| S-C9 | bench timer fixed cost ~16.7 ms | **bench's own `time` field vs nodes** — this is the engine's reported time, not my wall. **Stands**, and it is the one timing finding that used the right measure. |

## S-C14's caveat, stated rather than assumed

It contrasts fresh against warm against seat 24's **348,278 ms**. My 1300 ms overhead is larger than the small
numbers, so those absolute wall values are not trustworthy — **but a 1300 ms artefact cannot manufacture a
348-second stall, and the direction cannot be reversed by adding a constant.**

**Re-measured with the ENGINE'S OWN `time` field, 6 repeats in one process, pos 90, `go depth 12`:**

| run in one process | engine time | nodes |
|---|---|---|
| 1 | 23 ms | 79,980 |
| 2 | 2 ms | 7,518 |
| 3 | 2 ms | 7,527 |
| 4 | 1 ms | 3,521 |
| 5 | 0 ms | 1,389 |
| 6 | 0 ms | 1,324 |

**So the conclusion holds on the correct measure: warm repeats get faster (23 ms → 0 ms) and cheaper
(79,980 → 1,324 nodes), not 400× slower.** S-C14 stands with the engine's own numbers; the earlier wall figures
are superseded by this table.

## The rule

**Wall is apparatus time. Nodes, scores, plies and info-line counts are engine facts.** Any finding whose claim is
stated in the second set survives a harness-overhead error; any finding stated in the first set must be
re-measured with the engine's own `time` field.
