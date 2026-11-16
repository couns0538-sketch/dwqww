# THE PC BUILD'S CLOCK BEHAVIOUR — one page, from measurement only

Engine: PC r15 (`/home/ubuntu/builds/pc/forge`), built from `FABLE_TO_swarm_5.md`'s patch (sha256 d6bd72c531f785f4,
11 files, `patch -p1 --fuzz=0`), with `-DFORGE_MATE_ALPHA_GUARD=1`. Settings **PC20** unless a row says otherwise:
S14 + `CuckooRep true`, `HistRework 2`, `TtPruneV2 true`, `CorrHistV2 true`, `MateAlphaGuard true`, `OwnBook false`,
**Threads 1**, Hash 16. Every search cold (`ucinewgame` before it — verified, `cold_vs_warm.txt`).
Nothing below is inferred from another seat or from the base tree; where a number is the base tree's, the row says so.

---

## 1. `movetime` landings against plan — **CORRECT, and it is the plan that is smaller**

| control | plan (= M − Move Overhead 10) | median wall | median − plan | last completed depth |
|---|---|---|---|---|
| `go movetime 50` | 40 ms | **40.50 ms** | **+0.50 ms** | 13 |
| `go movetime 500` | 490 ms | **490.50 ms** | **+0.50 ms** | 20 |

Two independent 200-search runs at `movetime 50`: 40.50 and 40.50 ms.

Verdict: **correct as designed.** The engine stops 0.5 ms after its own plan, at every M tested. The thing an owner
must know is that the plan is `M − 10`, not `M`: `movetime 50` buys 40 ms of search. A cross-engine "movetime 50"
match gives this engine 20 % less time than a rival that spends the whole 50 ms.
Also measured: the iteration that crosses the deadline is DISCARDED, so the move played usually comes from an
iteration that finished well before the plan (median last-completed-depth time 32.2 ms at `movetime 50`).
Not measured: `movetime` below 20 ms, and `movetime` with Move Overhead other than 10 except the 0/45 probe.

## 2. The soft-plan share at long clocks — **the plan is not a target, and the share shrinks as the clock grows**

On a clock the engine stops at an iteration boundary, so what it ACHIEVES is the last whole iteration:

| clock | planned soft | achieved (median) | achieved / soft |
|---|---|---|---|
| 200 ms | 8 ms | 8.1 ms | 101 % |
| 500 ms | 22 ms | 17.8 ms | 80 % |
| 1000 ms | 45 ms | 34.4 ms | 77 % |
| 3000 ms | 135 ms | 102.1 ms | 76 % |
| 10000 ms | 454 ms | 302.2 ms | 67 % |
| 30000 ms | 1363 ms | 832.8 ms | 61 % |

These are the base-tree sweep (`job5/raw`, 200 searches per clock). The PC build measured 35.05 ms at 1 s and
298.5 ms at 10 s — within 1.4 % of the base tree, so the table describes both builds.

Verdict: **not correct as a target, harmless as a safety property.** The soft plan is an upper bound the engine
approaches from below, never a time it aims at; the shortfall grows with the clock because one iteration is a
larger slice of a larger budget. The consequence is that the engine thinks for less time than its own plan at long
clocks — the opposite of the usual "time loss" worry.
Not measured: clocks above 30 s; `movestogo`'s interaction with the share beyond the 1 s rows below.

## 3. The `movetime`-versus-`wtime` error asymmetry — **real, and the two paths fail in opposite directions**

| path | where the deadline is checked | what it does at the deadline | measured error |
|---|---|---|---|
| `go movetime M` | inside the search (hard limit) | abandons the running iteration | wall = plan **+0.5 ms**; the KEPT iteration is 1–69 ms early |
| `go wtime` | at the END of an iteration (`search.cpp:2612`) | finishes the iteration, then stops | **discards nothing** (undershoot 0.0 ms in 40/40); overshoots soft by up to a whole iteration |

The overshoot at the soft limit, on the PC build, 200 searches each:

| clock | soft | median overshoot | worst overshoot | over soft | over soft by > one whole iteration |
|---|---|---|---|---|---|
| 1000 ms | 45 ms | −9.8 ms | **+92.3 ms** (wall 137.3) | 33 % | 14 % (13 % excluding tiny final iterations) |
| 10000 ms | 454 ms | −154.2 ms | **+1816.7 ms** (wall 2270.7) | 23 % | — |

Verdict: **correct in the sense that matters (no search exceeded its own clock, 0 of 400), and the asymmetry is
benign at the clocks a game actually uses.** At 1 s the worst single move was 137 ms — 13.7 % of the clock from a
4.5 % plan. At 10 s the worst was 2.27 s — 22.7 % of the clock from a 4.5 % plan. So the plan under-states what a
move can cost by roughly one iteration, and the hard limit (5× soft, capped at 60 % of the clock) is what actually
protects the flag.
This reconciles my finding with seat 16's REFUTES: they measured the KEPT iteration, I measured the wall clock; both
are correct about different quantities (`reconcile_seat16_F2.md`).
Not measured: whether a mid-iteration soft check would raise or lower playing strength — that is a match question.

## 4. The reserve-empty branch at ≤10 ms — **BENIGN, measured two ways**

At `wtime 10`, `wtime 1`, `wtime 0` the plan is empty (`time ≤ Move Overhead`) and the engine plays a **one-ply,
≤2,000-node** answer in 0.75–1.13 ms.

| test | result |
|---|---|
| 5 positions with a capture available | one-ply answer **= a 45–64 ply search's move in 5 of 5**, capturing exactly where the real search captured (+8 free queen, +2 knight takes rook) |
| 10 QUIET tactically-loaded positions (the hard case) | one-ply answer **= a depth-20 search in 7 of 10**; on the 3 that differed, the cost of the one-ply choice — measured by playing each move out and scoring the result at depth 16 — was **+1, +49, +60 cp**. No material loss. |

Verdict: **benign.** It is a weak move at worst, never a lost game, on both sets. It is not free: a 60 cp
concession is real in a long game. Reading a raw deep score as "the one-ply move loses 9 pawns" is a trap — those
positions were already lost for both candidate moves.
Also measured: `FORGE_FIX_HARD_LIMIT_EMERGENCY` does **not** change this branch. Its own comment says it targets the
near-overhead case (`wtime 11`, where r9 played an unsearched move); measured, `wtime 11` now answers like a depth-1
search on 2 of 3 positions where the base tree gave an unsearched move, and `wtime 10` is unchanged.
Not measured: clocks between 11 and 20 ms; the increment's effect on the reserve test (a `wtime 10 winc 10` clock is
reserve-empty, which the rule in `REPORT_reserve_empty.md` would not allow — but I did not measure a game to show
the cost).

---

## What is NOT measured here, stated plainly
- No game or match was played: every verdict is about single searches, not about results in games.
- Clocks below 200 ms except the 10/1/0 reserve cases; clocks above 30 s.
- Threads above 1 (forbidden by the swarm rule, and seat 04 shows multi-thread scores are not reproducible).
- The PC's own trained net: not shared, so every evaluation-dependent number here used the built-in net.
- Whether any of this changes playing strength: a match question, not a clock question.

## The one-line answer for the owner
The PC build's clock is **safe but pessimistic at long clocks and slightly generous at short ones**: it never
exceeded a clock in 400 timed searches, it spends `movetime − 10 ms` exactly, it achieves only 61–78 % of its own
soft plan on long clocks because it stops at iteration boundaries, and with ≤10 ms left it plays one ply, which
measurement says is a weak move and not a lost position.
