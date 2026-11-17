# Owner summary — forge-combo29 C++20 chess engine audit

**Audit window:** 2026-11-16T22:20Z → 2026-11-17T10:20Z.
**Assembled by:** seat `swarm-73`, from committed branch content only. **Nothing here was re-measured.**
**Branches read:** **25** (`swarm-01, 02, 03, 04, 05, 06, 07, 08, 10, 11, 12, 13, 15, 16, 17, 19, 20, 21, 23, 24, 25, 27, 28, 29, 30` — every branch under `origin/for-fable-and-opus/` that carries a `FINDINGS.md`).
**Findings synthesised:** **2,283** distinct findings (2,304 table rows; 21 rows are re-runs recorded under an existing id).

That count is a count of *rows I read*, not a claim that 2,283 separate claims are each correct. The consolidated
report cites about ten of them by id. The rest I used to license, bound, or contradict the recommendations below.

Two builds appear throughout and every number names one:
- **base** — the owner's release tree `6b98f217`, default options.
- **PC r15** — build `068f0927`, normally under the **PC20** option set (22 options = S14 + CuckooRep,
  HistReWork, TtPruneV2, CorrHistV2, MateAlphaGuard; `OwnBook false`).

Unless a line says otherwise: `Threads 1`, `Hash 16`, fresh process per cell, positions validated with python-chess
before sending.

---

## 1. What to change

Ordered by what costs you most if you get it wrong. Verdict on each: **ship** / **do-not-ship** / **needs-more-evidence**.

### 1.1 Do not ship the NNUE weight-column prefetch patch — **do-not-ship**

`_mm_prefetch` of the next 16-float block of each of up to six columns in `nnue::fuse_columns` / `nnue::update`.

| measurement | build & conditions | result |
|---|---|---|
| real positions, n=130, `go nodes 50000`, ABBA, fresh process | base `6b98f217` vs base + `prefetch_columns.patch.txt`, g++ 13.3.0, `-DFORGE_MATE_ALPHA_GUARD=1`, `FORGE_MARCH=x86-64-v4` | pooled per-node ratio **1.0980 → 9.80 % slower**; **121/130 = 93.1 %** of positions individually slower; Q1 1.062 / median 1.087 / Q3 1.119; 7.87 % without the single 3.2× outlier |
| bench 13, 48 interleaved ABBA pairs, 2 builds per side | `862,329` nodes asserted every run | **9.43 % slower** (time ratio 1.0943, 95 % CI [1.0734, 1.1155]) |
| bench, 20 alternating pairs | base tree | **8.1 % slower** (0.9190, 95 % CI [0.8841, 0.9552]) |

The real-position arm is the one that decides it, and it is the cleanest control in the run: **both builds pass all
four honesty pins with identical node counts** (`312,866 / 862,329 / 3,024,920 / perft 4,865,609`), so the cost is
pure per-node work, not a different search.

**This is the one case where bench generalised correctly** — and it did so in the direction of *understating* the harm.

**What would overturn it:** a real-position ABBA run at n ≥ 130, same settings, where the per-node ratio's CI
includes 1.0 or lands below 1.0, **or** where the two builds' node counts are not identical. Nothing cheaper is
worth doing; three independent measurements already agree on the sign.

### 1.2 Repair the drawn-root bail — the MOVE, not the score — **ship** (both patches, composed)

Two patches, both validated, and they compose:

- `swarm/12/job1/two_doors_mate.patch.txt` — at a drawn root, scans legal moves and cancels the adjudication if one
  mates immediately. **0 regressions on 12 draw/mate cases; all four honesty pins bit-identical on release *and*
  on ASan+UBSan** (`312,866 / 862,329 / 3,024,920 / 4,865,609`).
- `swarm/27/job1/drawn_root_reporting.patch.txt` — emits one `info` line at depth 1 instead of claiming the whole
  depth ceiling it never reached.
- **Composed, either order, byte-identical `src/search.cpp`:** sha256 `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`,
  verified independently on both seats.

**The trap is the `-p` level, not the order.** Seat 12's hunks name `a/forge-combo29/src/…` (so `-p1` from the repo
root); seat 27's name `a/src/…` (so `-p1` from inside `forge-combo29/`). One flag for both silently skips a hunk —
check every `patch` exit code.

**Do NOT layer the general claimable-draw fix (claim only when no legal move resets the clock) onto the PC build.**
It moves all three bench pins (`312,866 → 353,312`, `862,329 → 979,723`, `3,024,920 → 2,893,009`) and, layered on
r15, turns three correct answers wrong: `cp −1,237` on a losing-side-at-threefold, `cp −501` on a clock-100 root,
and a correct `mate 1` into `cp 488`. **The pin cost is in the repetition half, not the fifty-move half**, so it
must be merged inside the root-drawn path.

**Before you write either patch, re-point one test:**
- `tests_r3fu_17/reused_searcher.cpp:71-76` **passes on base and FAILS under the repair** (`nodes 380`). Its binding
  assertion is `nodes == 0` on a **halfmove-100** position, though its stated purpose is a stale-count guard.
- `tests_r3_13/quiet_extinction.cpp:99-114` never reaches the branch (0 of 200 positions drawn).
- **The repetition arm is tested by neither file.**

**What would overturn it:** any one of the 12 draw/mate cases regressing, or any of the four pins moving under the
composed tree. Both are cheap to re-run and are the exact things already measured.

### 1.3 Consume the engine's output only through an empty-PV check — **ship**

At a drawn root the engine answers with a legal-looking move it never searched, and **the protocol carries no field
saying so**. `go depth 64` on such a position reports `depth 64`, `seldepth 64`, `nodes 0`, cp 0 — a GUI displays
"depth 64, 0.00" on a search that visited no nodes.

| what you receive | what it means |
|---|---|
| `0000` with `mate 0` | checkmate |
| `0000` with `cp 0` | stalemate, **or** an empty `searchmoves` restriction. **In the stalemate case there is no `info string` at all** — treat `0000` as an error unconditionally |
| a legal move, **empty `pv`**, `nodes 0` | adjudicated draw — **do not play the move** |
| zero `info` lines | the search never ran (`go nodes 0/1`, `go` then `quit`) |

**The reliable check is `pv` empty.** It is guaranteed rather than conventional: no `pv` write exists in the bail
branch (`search.cpp:2250-2271`), while every searching path sets it (`:2458`). It holds for a search stopped
mid-iteration (0.8–1.8 ms → 404/1001/1001/1703/1703 nodes, `pv` non-empty every time) and at MultiPV 1, 2 and 3
(10 of 10 bailing cells, no searching cell). **`nodes == 0` also works but is shared with three other unsearched
paths** (`:2275`, `:2301-2308`, `:2321`).

**All four shapes are present on PC r15 as well as base** — no GUI hazard in this report is a base-only artefact.

**What would overturn it:** a searching path that returns an empty `pv` at MultiPV 1. None found in 10 bailing and
10 searching cells; MultiPV > 1 takes a different emit path (`:2520-2531`).

### 1.4 Treat every refused FEN as fatal, and scan both reply streams — **ship**

A refused `position fen` still answers `readyok`, **keeps the previous board, and a search then returns a
normal-looking result for that previous position** — legal `bestmove`, plausible ±30 cp score, full PV,
correct-looking node counts. Worse than a startpos fallback because it depends on session history.

The diagnostic **is always emitted**; only its **location** moves with where you read:

| your harness | where the diagnostic lands |
|---|---|
| sends `isready` between `position` and `go` (the normal defensive pattern) | in the **position reply**, before `readyok` |
| does not | in the **`go` output**, ahead of the first `info depth` line |

Both hold **in a fresh session as well as after a predecessor**. There is no undetectable first position.

**So: scan BOTH the position reply and the search output, and check before parsing any `info depth`.** A harness
reading only one stream misses it half the time. **Primary defence: validate every FEN before sending it** —
`readyok` is not a statement about the position.

**What would overturn it:** an invalid FEN that produces no `info string` on either stream. None found across all
four combinations.

### 1.5 Keep `Threads 1` for anything you measure or reproduce — **ship**

At `Threads 1` fixed node and depth searches are bit-identical on both builds (40/40 positions; 20/20 in an
independent re-check at depth 12, two fresh processes per position). **Above it, the score is not reproducible.**

- base `6b98f217`, Threads 4, depth 12, fresh process, same FEN `5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1`:
  three runs gave **+2402 cp, `mate 14`, `mate 21`** — three different evaluations of one position — while the
  bestmove was `f3f8` in all three.
- PC r15 under PC20, same FEN, Threads 4: **+2576 cp, `mate 13`, `mate 18`, `mate 16` — four distinct evaluations in
  four runs**, node counts spreading 5.0 M to 31.4 M. At Threads 1 the same settings gave **+2207 cp in 4/4 runs**,
  identical to the node (75,311).

**The move is stable; the score is not — and the score is what a search hands to the clock, the book, and any
game-vs-game comparison.** Neither the aspiration window nor the null-move setting causes it.

**What would overturn it:** a Threads 4 configuration on this build that reproduces its score across ≥ 3 fresh
processes *and* across depths 12 and 14. Widening the aspiration window and disabling null-move were both tried and
did not.

### 1.6 Never use a zero increment — **ship**

The clock floor collapses from **111 ms** to **~10 ms** with no margin. With a 60 ms increment the floor is stable at
111 ms, converged from every start ≥ 111 (hard limit = 60 % of soft, `MoveOverhead 10`). **The clock cannot be lost
by searching** at that setting: 0 forfeits at 12 clocks from 1 to 600 ms, 600 moves, 0 flags on worst boards at
200 ms.

**What would overturn it:** a zero-increment game with a forfeit — none observed; the ~10 ms floor is the mechanism.

### 1.7 `MultiPV 1` at any Hash, or `Hash 16` MB with multiple lines — **ship** (throughput); *and* distrust near-horizon positions — **needs-more-evidence**

Fixed `go nodes 200000` grid (work constant, time the variable), PC r15 + PC20, Threads 1 — milliseconds:

| Hash | MPV 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 16 | 116 | 140 | 146 | 145 |
| 64 | 113 | 193 | 200 | 227 |
| 256 | 132 | **384** | **557** | **550** |

**113 → 557 ms = 4.9×**, with six cells slower than 1.5× the fastest spanning two Hash values and three MultiPV
values — a diagonal boundary, not one bad cell. Mechanism: between-line `tt.clear()` plus a second full-size
alternate table (nodes/ms 559 → 183 → 2 at MPV 3 versus a flat ~1,500 at MPV 1). A patch removing the redundant clear
recovers 3.2× at Hash 64 and 14× at Hash 256 but does not reach MPV 1 rates — **necessary, not sufficient**.

**MultiPV's effect on the ANSWER is conditional, not flat, and is the part that is not settled.** Changing MultiPV
changes the best move in ~18 % of positions overall (44/250 = 17.6 %, replication 47/250 = 18.8 %), split by whether
a free MultiPV-1 search kept its move between depth 12 and 16:

| stratum | R4 | R6 | 95 % CI (R6) |
|---|---|---|---|
| unstable | 16/30 = 53.3 % | **31/58 = 53.4 %** | [40.8, 65.7] |
| stable | 31/220 = 14.1 % | **35/342 = 10.2 %** | [7.5, 13.9] |

The rate held when the stratum nearly doubled and the interval tightened from 33.7 to 24.9 points wide — **still 25
points wide**. ±5 points needs roughly **350 unstable boards ≈ 2,400 positions** at the 14.5 % incidence.

**The usable advice is "distrust near-horizon positions", not "distrust MultiPV".** A display setting can only
change an answer that is not settled; MultiPV does not rescue an unsettled position.

**And "unsettled" measured by a changing best move misses a search that keeps its move and revises its evaluation**
— one board was stable by that rule yet its mate number moved by 3 between depths. A score-change criterion between
depths would capture it; **a later run should select on that.**

**What would overturn the throughput claim:** a Hash/MPV cell where MPV > 1 is within 1.2× of MPV 1 at the same
node budget. **What would settle the answer claim:** ~2,400 positions with the score-change criterion.

### 1.8 Discard mate labels whose PV is too short for the score — **ship** (necessary, not sufficient)

Rule: a mate label is valid iff PV length is `2|N|−1` for a win and `2|N|` for a loss.

- 133 lines: **114 complete all mated, 19 short none mated.** Works at MultiPV 3, both signs, depths 6–20.
- A mate score can be reported with a PV too short to deliver mate at the first depth reporting a mate, and repaired
  one depth later.

**The filter catches only SHORT PVs. It cannot catch a right-length PV that proves a different mate than its score
claims.** Two demonstrations, failing in **opposite directions**, so no direction is claimed:

| board | failing report | true distance | error |
|---|---|---|---|
| R5 222 | depth 12, **MultiPV 3** said mate −6 with a 12-ply PV (MPV 1 said mate −5) | exactly 5 | **over by 1**, on the setting with MORE lines |
| R6 121 | depth 12, **MultiPV 1** said mate 7 (depth 16 said mate 4, same first move) | exactly 4 | **over by 3**, on the single-line search at the shallower depth |

In both, the PVs replay legal, are exactly the length the score implies, and end in checkmate; exhaustive
engine-independent search settled each true distance. **A PV that passes the length filter is "not rejected", never
"verified".**

**What would overturn it:** a board where the filter admits a label that is wrong in a *consistent* direction across
≥ 5 boards. Two boards, opposite directions, cannot establish one.

### 1.9 Self-play variety comes only from openings — **ship**

Ten games from one start produce **one** distinct game, on both builds, at fixed limits. **1,000 openings × 2 colours
= 1,000 independent pairs (2,000 games), not 2,000 samples.**

**What would overturn it:** ≥ 2 distinct games from one start at fixed `Threads 1` limits. None observed on either
build.

### 1.10 Do not spend effort on a v3 micro-patch — **do-not-ship**

`gprof`, bench 13, PC20 + test net, Threads 1. The instrumented `-pg` build reproduces bench 13 = `3,652,372`
exactly, so the profiler does not measure itself.

| group | self % | calls |
|---|---|---|
| search proper | **38.41 %** | — |
| all `nnue::v3` | 21.46 % | — |
| movegen / legal / make / see | 15.80 % | — |
| update `apply_changes_pair` | 8.47 % | 2,382,071 |
| forward `evaluate` | 7.34 % | 2,556,881 |
| refresh `refresh_from_pieces` | 6.78 % | — |

**No single v3 function exceeds 8.5 %.** A perfect v3 kernel caps at **~1.26×** on this engine, and that is not a
bench artefact: the net is **20.85 %** on bench 13 and **20.65 %** on 200 real openings at depth 12 — agreement within
0.2 points. **The picker plus generation is the larger lever in both arms (~37 % and ~34 %).**

The predicted 35–50 % for the incremental update was killed by the **call counts**, not the percentage: `evaluate` is
called 2,556,881 times against the update's 2,382,071, because the v3 path evaluates at nearly every node rather than
only at leaves. **The premise was false, not the estimate.**

**On real positions the patch target is the shared accumulator walk, not either symbol alone** — on bench
`apply_changes_pair` is hottest, but on real positions `evaluate` (6.18 %) overtakes it (5.98 %). Optimising
`apply_changes_pair` in isolation chases a bench artefact.

**If you do touch it, reproduce `27,944,084` nodes exactly** — seat 08's Step 1b arm, `swarm/08/v3/profile/openings_baseline.txt`
(200 per-position rows), `go depth 12`, Threads 1, Hash 16, PC20 + test net, **first 100 of O + first 100 of G**,
`OG200.fens`. A reproduction on a different 200 positions gives `27,762,950` — a 0.65 % gap that is the position
set, not a discrepancy. **A node-sum identity without its position set named cannot be reproduced.**

### 1.11 Quote PC20's two components separately; never a "PC20 speedup" — **needs-more-evidence** (net speed)

| claim | value | 95 % CI | sign-share | reading |
|---|---|---|---|---|
| PC20 per-node cost | +6.4 % | [1.0670, 1.0876] | **90.0 %** (162/180) | **real — a per-position tax** |
| PC20 node count, aggregate | 0.9131 (−8.7 %) | [0.8752, 0.9528] | ~60 % | **real pooled saving, session-level per position** |
| **PC20 net wall time** | 0.9715 | **[0.9273, 1.0151]** | ~53 % | **NOT ESTABLISHED — CI includes 1.0** |

All n=464 (quadrupled from n=119), PC r15 + PC20 vs S14, Threads 1, real positions, ABBA, fresh process. The
decomposition `wall_ratio = node_ratio × per_node_ratio` closes: `0.9131 × 1.0640 = 0.97154` against observed
`0.9715`.

**The shrinkage is why these are quoted rather than the earlier row:** node saving **12.4 % → 8.7 %** as the sample
quadrupled, while the per-node cell did not move. **A true 7 % speedup would have been detected at n=464; it was
not, so no larger n is worth buying.**

**The node saving is session-level.** It holds as an average over positions and does **not** license a per-position
prediction — which is exactly what a fixed-node depth comparison is built from. For all four switches, "PC20 will be
cheaper here" is ~50/50.

**What would overturn it:** a wall-time run at n ≥ 464 whose CI on the ratio excludes 1.0. The nearly-cancelling
components are why a larger sample keeps failing to establish a net gain — that failure is the prediction the
decomposition makes, not evidence against it.

### 1.12 PC20's "+3 ply at 20,000 nodes" is wrong by 8× per position — **do-not-ship** (that figure, and any match planned on it)

| budget | PC20 deeper | tie | shallower | ply/position | wins/decided |
|---|---|---|---|---|---|
| `nodes 20000` | 44 | **65 (50.0 %)** | 21 | **+0.062** | 67.7 % |
| `nodes 50000` | 46 | **55 (42.3 %)** | 29 | **+0.031** | 61.3 % |

n=130, PC20 vs S14, Threads 1. **Median depth difference is exactly 0.0 at both budgets.** The original figure came
from **six** positions and read as +3 ply in total (+0.5/position).

**The defensible statement is "PC20 is rarely shallower", not "PC20 is deeper"** — same depth on about half, deeper on
about a third, shallower on about a sixth, deeper-or-equal on ~84 % while averaging +0.06 ply.

**What would overturn it:** a median depth difference materially above 0 at n ≥ 130. Half of all pairs are exact ties
because depth is an integer, so this needs a share, not a mean.

### 1.13 Keep or drop `CorrHistV2` — nothing measured changes — **needs-more-evidence** (it is neutral, not beneficial)

Both ablation designs run on the same 120 positions, PC r15 + PC20, depth 12:

| switch | ADD to S14 | DROP from PC20 |
|---|---|---|
| TtPruneV2 | 0.8992 (saves 10 %) | 1.0853 (removing costs 8.5 %) |
| **CorrHistV2** | **0.9368 (saves 6.3 %)** | **0.9998 (removing changes NOTHING)** |

**CorrHistV2 does real work alone and is fully redundant inside the bundle.** "How much does TtPruneV2 save" has two
true answers, and two seats' 5 % and 10 % figures were never in conflict — they measure different ablations.

**`MateAlphaGuard` does nothing on ordinary positions** — the branch is unexecuted because alpha must be mate-valued.

**What would overturn it:** a bundle ablation that keeps CorrHistV2 and one that drops it, on the same positions, with
a wall-time or depth difference whose CI excludes zero.

### 1.14 `searchmoves` — three distinct uses, only one of which is sound — **ship** (as a harness rule)

25 PC20 positions, depth 10, three arms (free search / all legal moves named / the single bestmove pinned):

| use of a pinned score | verdict |
|---|---|
| recording an **absolute** score | **unusable** — wrong 25/25, \|Δ\| ≥ 10 cp in 14 of 25, range −32 to +31 |
| verifying that a **move** is best | **vacuous** — the restriction makes it the only option (same bestmove 25/25 by construction) |
| **comparing two candidates, both pinned identically** | **usable** — rank order preserved 8 of 8 |

**`searchmoves <all legal moves>` is not a no-op control.** It changed the reported best move in **6 of 25 at depth
10 and 5 of 15 (33 %) at depth 12** — the effect grows with depth — and two of the depth-10 cases were score-tied and
still picked differently. Its failure is silent: the baseline *looks* like the unrestricted search and is not.

**What would overturn it:** an all-legal-moves arm that returns the unrestricted bestmove and score on ≥ 25/25
positions at depth 12.

### 1.15 `softnodes` — a soft budget is bounded by the tree on both ends — **ship** (as a harness rule)

> The ratio is bounded by the tree: 0.07x to 3.50x across the populations measured. On 60 real-game positions at
> softnodes 2000 it never undershot (min 1.022), and the floor only appears on sparse/mating boards where the
> depth-64 clamp arrives first.

Settings for the floor: PC r15 `068f0927`, PC20 (22 options asserted), Threads 1, Hash 16, `OwnBook false`. On the
K+R v K board `6k1/5ppp/8/8/8/8/5PPP/R5K1 w` the engine reaches **depth 64 at 1,344 nodes and stops**, so
`softnodes 20000` and `softnodes 100000` both return **1,344 nodes** — a **14.9× under-shoot, with the correct answer
(`mate 1`, a1a8)**. At 1,344 the ratio is 1.000; at 1,345 it is already 0.997 and it never rises again.

For the scope half: `go softnodes 2000`, PC20, Threads 1, 60 python-chess-validated positions from `tests_r3fu_12` —
ratio min **1.022**, p10 1.097, median 1.567, p90 2.417, max 3.987; **0 of 60 undershot**, **0 of 60 came near the
depth-64 clamp**.

**So the 14.9× under-shoot is confined to sparse/mating positions, where the tree is small enough that depth 64
arrives before the budget is spent. For your self-play use — `softnodes 2000` on real game positions — the budget
always buys at least 2,000 nodes.** A harness that raises the budget to get more work on a mating position will
measure no change.

**What would overturn the scope half:** a real-game position at `softnodes 2000` reporting fewer than 2,000 nodes.
**What would overturn the floor half:** a sparse board where a budget above 1,344 still returns more nodes.

### 1.16 Do not compare a hard-budget result with a soft-budget result — **ship**

- `go nodes N` picks the last completed iteration **at or below** N; median spend **74 %** of N.
- `go softnodes N` picks the first iteration **at or above** N; hard cap 4N.
- **A soft budget of N is not N:** identical search at 2000 vs 3000 in **44–47 %** of positions.

**Every per-node figure must divide by the reported count, not the requested budget** — otherwise the request cancels
and you report a time ratio under a per-node label.

**What would overturn it:** a position where `go nodes N` and `go softnodes N` return the same node count and the same
depth. They pick different iterations by construction.

---

## 2. What is broken

Defined narrowly, as you asked: **a consumer receiving a well-formed answer that does not describe the input, or an
outright wrong result.** Not "slow", not "misconfigured".

### 2.1 The drawn-root bail answers about a position it did not search — **broken, both builds' consumers**

**The base returns 0 nodes iff the position at the END of the sent move list has occurred at least three times in
that list.** The verdict follows the **searched position's own count**, not the root's:

- 1 ply past a repetition (searched position once) → searches, **12,978 nodes**
- 3 plies past (searched position 3×) → **bails, 0 nodes**
- 5 plies past (once) → searches, **11,691 nodes**

It returns **0 nodes, cp 0, and the head of the generated move list** as `bestmove`. Monotone in occurrence count: 2
occurrences searches (7,581 nodes); 3, 4, 5 and 6 all bail at 0. Confirmed at a realistic branching factor (dense
middlegame, ~30 legal moves: 2 → **29,994 nodes**; 3 and 4 → 0) and on a 10-ply preamble (2 → **17,399 nodes**;
3/4/5 → 0). **List length and root position are irrelevant.**

**The cost is in the MOVE, and it is a forfeited mate, not just material.** On a genuine threefold root where the side
to move has mate in one, the base reports `cp 0`, searches nothing and plays `f2f3` — **forfeiting the mate** — while
PC r15 reports `mate 1` and mates. Verified as one chain on **6 of 6** boards: `go perft 1` on the searched position
names the first generated move, and the bail returns **exactly that move** (`f2f3` on all six), while the mates being
ignored were `b1b8`, `a1a8`, `c1c8`, `e1e8`. **The forfeit is the mechanism doing exactly what it says.**

**Material cost, measured on two disjoint 12-position samples, deterministically sampled:** median **roughly
600–1,000 cp**, nine or ten of twelve at or above 300 cp, **worst 2,222**, **0/12 equal to the searched best**, one
missed forced mate.

**Three qualifications, each blocking a specific misreading:**
- **It is a cost of the MOVE, not of the score.** The `cp 0` is defensible under a rule that lets a draw be claimed;
  the move it pairs with is not. **`cp 0` is right about the rule and wrong about the position.**
- **"Hangs a piece" is the wrong verb.** On the −805 board the piece is the **queen on b6** and **it was already
  attacked before Black moved** (White's knight a4 attacks b6 at the root). But the queen is capturable after **both**
  moves: after the bail's `e6e5` White takes with the **knight** and Black recaptures with a **pawn**, net **+6**;
  after the repair's `b6b4` White takes and Black recaptures with the **bishop** — a queen **trade**, net **+0**.
  **The cost is the RECAPTURE BALANCE, not the queen's safety.** And it **does not generalise in either direction**:
  across five fixtures the reply captures an already-attacked piece twice, a **not-attacked** pawn once (a genuinely
  new hang), and nothing twice. **Check the verb per fixture.**
- **On one of two measured boards the repair is material-neutral**, so what the repair demonstrably buys is **the
  removal of the 0-node path**, not reliable material safety.

**How often, honestly:** **8 of 10** clock self-play games reached a genuine third occurrence — but the 95 % Wilson
interval is **49 % to 94 %**, so quote the interval. The frequency is "common", not "four in five".

**Counterweight that bounds who is exposed: an organised match never plays the move.** The match program ends the game
at the third occurrence. **The exposure is to analysis tools and other front ends** that ask the engine about a
position and play what comes back. Quoting the mate-in-one forfeit without this reads as a playing-strength defect,
which it is not.

### 2.2 At halfmove 99 the draw rule fires one ply too early — **broken, and no repair fixes it yet**

`6k1/8/5PPP/8/8/8/8/R6K b - - 99 40` — Black has two moves and both allow `Ra8#`. At halfmove 99 the base answers
**`cp 0` in 36 nodes**, where counters 97 and 98 give the true `mate −1`. **It is still `cp 0` / 36 nodes on PC r15,
still `cp 0` on the composed seat 12 + seat 27 tree, and no depth fixes it** (depth 24 still `cp 0`).

The control proves it is the missing escape and not the counter: `6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40` is correctly
`cp 0`, because Black there has six pawn moves that reset the clock and the draw is real. **A root-only repair leaves
a real miss one ply down.** The leaf rule is `search.cpp:1302`.

### 2.3 A refused FEN returns a well-formed answer for the previous position — **broken**

See §1.4 for the defence. The severity is that **the fabricated row is harder to detect than a duplicate**: where the
predecessor differs, the score differs too, because the re-search runs on a restored board with different TT and
history state.

Measured over five predecessors — invalid FEN sent after each, PC r15, `go depth 8`:

| predecessor | its answer | invalid-FEN answer | |
|---|---|---|---|
| K+R v K mate | `a1a8` / mate 1 | `a1a8` / mate 1 | **DUPLICATE** |
| middlegame A | `f1e2` / cp 95 | `f1e2` / cp 100 | differs |
| middlegame B | `e1g1` / cp 28 | `e1g1` / cp 28 | **DUPLICATE** |
| endgame K+P | `e1f2` / cp 200 | `e1f2` / cp 209 | differs |
| startpos | `d2d4` / cp 14 | `d2d4` / cp 24 | differs |

**Comparing a row against its predecessor would catch about 40 % of these and miss 60 %.** Predecessor-comparison is
the clever mitigation someone will reach for, and **it is unreliable**. The only defence that works on all cases is
**confirming every FEN was accepted** before trusting any output from the position.

**The discriminator that proves it is "previous position" and not "startpos":** send the SAME invalid FEN after two
DIFFERENT valid positions. A startpos fallback predicts the same answer both times; a refusal predicts no `bestmove`;
"previous position" predicts **each predecessor's own answer, differing**. Measured: after A (`6k1/5ppp/8/8/8/8/5PPP/R5K1 w`)
→ `a1a8` / mate 1; after B (after 1.e4) → `e7e5`. **They differ, so startpos is excluded.** Bit-identical 3/3 on PC
r15 and identical on base release, so it **predates the patch**.

### 2.4 `bestmove 0000` reaches a consumer with no diagnostic — **broken, and it is a crash hazard**

`searchmoves e2e4` on a board where that move is illegal gives `bestmove 0000` + `info string`. **A null move will
crash or silently drop a turn in a naive front end, and the only signal distinguishing it from the ordinary bail is
that `info string`** — `pv` is empty and score is cp 0 in both cases. Identical structured fields, differing only in
free text.

Worse: **a stalemated root with an unsatisfiable `searchmoves` emits `bestmove 0000` with no `info string` at all.**
Base, `go depth 10 searchmoves e2e4` on `7k/5Q2/6K1/8/8/8/8/8 b` (verified `is_stalemate()` true, 0 legal moves): 10
info lines, 0 nodes, `bestmove 0000`, **and nothing else on the wire**. **So `0000` must be treated as an error
unconditionally** — a diagnostic cannot be relied on.

### 2.5 Mate scores that are wrong at the depth reported — **broken**

- `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`, depth 12, S14, base: reports **`mate −12`** (a promise of mate in 24 plies)
  with an **18-ply PV that does not end in checkmate**. Plain minimax proves White is mated in exactly **4** moves
  (and not 3). The engine's own depth-22+ answer is correctly `mate −4`. **The depth-12 score is wrong by 8 moves.**
  - PC r15: no options `mate −7` (14/14 plies, consistent); S14 `mate −9` (14 of 18 plies, **inconsistent**).
- A separate class at the right PV length, §1.8: two boards, opposite directions.

### 2.6 Multi-threaded scores are not reproducible — **broken for any consumer of the score**

§1.5. `Threads 4` gave **four distinct evaluations in four runs** on PC r15 under PC20 (+2576 cp, mate 13, mate 18,
mate 16) with node counts spanning 5.0 M to 31.4 M. The move was stable; **the score is what a search hands to the
clock, the book, and any game-vs-game comparison.**

### 2.7 A partial clock is an unbounded search with no diagnostic — **broken (silent)**

`go wtime` on a black-to-move board, or `go btime` on a white-to-move board, searches **indefinitely** and emits **no
`info string`**: the GUI sees a hang, not an error. Confirmed on both builds with controls; the both-clocks control
answers in 0.16 s. **Padding the opponent's value does not help** — a large opponent clock has zero effect. The
engine is right to ignore the opponent's clock; it should print an `info string` instead of searching forever.

### 2.8 What is *not* broken, and was claimed to be

Recording these so you do not inherit a withdrawal as a fact:
- **The repair is not depth-limited.** 14 validated roots 14/14 correct at depth 10 and nodes 200,000 (13/14 at
  20,000); 8 validated boards search at depth 4 on all 8, minimum 38 nodes, three reporting mate 1 at depth 4.
- **The repaired build does not decline repetition draws.** On a winless repetition draw both builds return cp 0
  with a searched move. **It finds the win where one exists and reports the draw where none does.** Both earlier
  claimable roots had a forced mate available, so "found the mate" and "declined to claim" were indistinguishable —
  a confound, not a finding.
- **PC20's depth-14 mate-4 result is an improvement, not a defect.** Exhaustive engine-independent search:
  `h3h4` forces mate in ≤ 4 against every defence (1,829,749 positions memoised, stalemate returns False so it cannot
  pass itself off as mate) and no mate in 3 exists (5-ply, 118,780 positions). PC20 reports mate 4 from depth 12; the
  base reports mate 6 first and converges two plies later.
- **A decreasing `mate N` is not a defect.** On `8/5K2/7Q/4k3/8/8/8/8 w` the true DTM is 6, and base+S14 reports
  13 → 10 → 8 → 6, converging. These were real but slower mates.
- **The bail is not budget-specific** and it is not a bypass: the depth field is a default reported once per depth.
  **Never infer "the search reached depth N" from a line count on a bailed root** — 10 lines at `go depth 10`, but
  **64 lines under both `go nodes 1000` and `go nodes 100000`**.

---

## 3. What is not established

Each item with the reason it could not be settled. **Do not read a closed behaviour as a closed mechanism.**

**Measured as untestable within the run**
- **Whether the base also forfeits a mate that needs SEARCH.** Very likely by the same mechanism, but **repetition
  cycles live in quiet positions and short mates live in busy ones** — the two requirements are structurally opposed.
  Quiet positions admitting a clean neutral cycle have no forced mate within 7 plies; positions with short mates
  rarely admit a clean shuttle. **Thirteen candidates across two rounds, all defeated.** Recorded as untested with a
  reason, not as a negative result.
- **The count-vs-spacing question on the bail.** Count and spacing are not independently variable when one position
  anchors both: A+B+A always yields four occurrences, not three, for all ten neutral fillers tried. A retry needs an
  anchor reachable by two paths of different length. **A busier board is necessary but not sufficient.**

**Open as mechanism**
- **Why the drawn-root bail exists, and which of three candidate code paths produced it.** Its trigger, threshold,
  score and move are all measured; `root_candidates.front()` (`search.cpp:2265`) explains why it publishes the
  generator's head. **But "why the guard exists at all" is not ranked.** Do not read the behaviour as a diagnosis.
- **The base-vs-PC lone-king divergence, second mechanism.** The boundary is confirmed at 100 % outside its
  condition: **11 of 40** lone-king roots differ, **0 of 60** non-lone-king roots differ. Cause isolated at the
  switch: **`BARE_KING_LMR_CAP` off restores the base move on 11 of 11**; `BARE_KING_ONE_THREAD` on restores 6 of 11;
  ordering was hypothesised and killed. Cap-off visits fewer nodes on 9 of 11 boards (by 3,356–14,040) and more on 2
  (+621, **+10,981**). **But the gate fires on 100 % of nodes in every tree**, so it cannot be what distinguishes the
  two counter-cases. **A second, uncharacterised mechanism remains.** The instrument that would find it — a build
  printing per-depth reduction counts — was never built.

**Known scope limits that a reader might otherwise over-read**
- **The mate-in-one forfeit's breadth.** 6 of 6 fixtures across two mate types (back-rank and adjacent queen mate) —
  and **all six have Black's king on g8 or h8 with pawns intact.** Breadth beyond two structures was not tested.
- **The MultiPV instability split.** The rate held when the stratum nearly doubled and the interval is still 25 points
  wide; ±5 points needs ~350 unstable boards ≈ 2,400 positions.
- **The right-length-wrong-mate class.** Two boards, **opposite directions**, so the class is established and no
  direction is. **One failing case came from a single-line search at the shallower depth**, so it is not a MultiPV
  artefact.
- **The 8-of-10 threefold frequency.** Interval 49 % to 94 %. "Common", not "four in five".
- **PC20's depth advantage.** +0.062 ply/position at n=130 with the median difference exactly 0.0. "Rarely
  shallower", not "deeper" — and a six-position sample overstated it 8×.
- **`searchmoves` rates.** 25 positions, depth 10, one build. Direction unambiguous; **exact rates at depth 12+ are
  not established** beyond the single 5-of-15 measurement.
- **The MultiPV throughput boundary.** A timing surface, not a wrong-answer claim. **A slow cell is not a wrong
  cell.**
- **The identity baseline.** `27,944,084` on the O+G set; a reproduction on a different 200 positions gives
  `27,762,950`, so **the number is meaningless without its position set**.
- **Every individual PC20 switch as a node saving.** All four paired-effect CIs include 1.0. The aggregate is
  established and the components are not. **TtPruneV2's direction is significant (61 %, p = 0.022; replication
  61.7 %, p = 0.013) while its magnitude is not** (CI [0.8814, 1.0307]).
- **Root-specific vs history-wide on the bail: UNDECIDED.** No board satisfies both arms — the sparse board makes the
  unrepeated-final-position arm structurally impossible, the richer board fails the bail arm. Gate rule stated in
  advance and applied, not waived: a failed arm voids the other.
- **The material-key cache.** 0.7 % on real positions (not the 1.5–3.5 % predicted). Not worth shipping; the
  per-node-cost question it answered is superseded because **your PC evaluates through the v3 path.**

---

## 4. The measurement rules this run produced

These are the transferable output. Each is a rule the run paid for with a defect it caught in its own work.

**Before you measure**
1. **`Threads 1` for anything reproducible.** Above it, the score is not reproducible even when the move is (§1.5).
2. **Every number carries its build, settings, and workload.** "PC20 saves 7.4 % of nodes" is true of depth 12 on one
   position set and false as a statement about the engine. **Workload joins build, Threads, Hash and settings on the
   list a number cannot be quoted without.**
3. **`ucinewgame` is the cold reset; `Clear Hash` is not.** Warm process state shifts scores by up to 55 cp on
   identical requests.
4. **Validate every FEN before sending it, and read the reply.** `readyok` is not a statement about the position.
5. **State, in advance, what result would support the hypothesis and what would refute it** — including for rows whose
   expected value is "unchanged". A table can be arithmetically correct and read backwards.

**While you measure**
6. **Report wins / ties / losses together, and use the SHARE, not the SUM.** "+3 ply over 6 positions" and "+8 ply
   over 130" are the same comparison; the second sounds like progress and is compatible with half the positions being
   identical and a median difference of exactly zero.
7. **A sign-share computed from a QUANTISED measure is a share of that measure's granularity.** Wall time at 1 ms
   resolution on 19 ms searches → **64.6 % exact ties**; integer depth, no timer → **50.0 % exact ties**. Decompose:
   at `go nodes 50000` wins/decided is 65.2 %, at `500000` it is 58.7 % — **once ties are excluded the two budgets
   agree.** Quote a sign-share **with its budget**, never as a bare property of the patch.
8. **Lengthen the measurement rather than redefining the share.** 50k → 500k took ties from 64.6 % to 6.9 % without
   changing the effect's direction.
9. **A sign-share alone cannot classify a claim; the interval decides first.** 50.6 % with no established effect and
   60.5 % with a real pooled effect are closer to each other than either is to 90 %.
10. **"Not established" ≠ "no effect" ≠ "coin flip."** A result whose CI includes 1.0 is **unresolved**. "Coin flip"
    means exactly one thing: a real pooled effect that is per-position random.
11. **Every per-node figure divides by the reported count, not the requested budget.** Otherwise the request cancels
    and you report a time ratio under a per-node label.
12. **A comparison at a fixed node budget cannot show a node saving.** Both engines stop in the same place by
    construction; any residual is the stopping rule's granularity. A 50.6 % sign-share measured there was a correct
    measurement of an effect that does not exist.
13. **Report median and geometric mean labelled, side by side.** Three statistics on one distribution gave three
    different conclusions, and the distribution was the finding.
14. **Put the per-position spread on the headline line.** A pooled 5 % saving that wins on 54.2 % of positions with an
    IQR 28× the effect size is a real effect and an unusable per-position predictor. **More data will not remove
    this — it is what the switch does.**
15. **Any speed number from fewer than ten positions is a hypothesis, never a result.** Two out of two small samples
    in this harness erred upward, once by 4×.
16. **A p-value must be recomputable from the counts printed in its own row.** Three of four published sign-test
    p-values read `1.000` when the counts beside them give 0.022, 0.648 and 0.411. The cause was a **missing
    `min(k, n−k)` reflection**, so the test saturated for every share above half and was correct only below it —
    **the one correct row was the below-half one, which made a broken function look validated.** Commit the test, not
    the answer, and give it a symmetry self-test: `p(k, n) == p(n−k, n)`.
17. **A control must be demonstrated to fail when the input is wrong**, not merely to pass when it is right. Three
    natural ways to write one all pass vacuously: `max()` of nothing, `all()` of nothing, a lookup falling through to
    a default. **A control that returns a plausible wrong number is worse than one that crashes.**
18. **A control cell proves only what its axis can see.** When you quote one, **say which axis it controls for.**
19. **A cap test needs a rising-series control.** "Respected the cap" is equally consistent with "ignored the budget
    and searched a fixed amount" unless rising budgets produce rising work.
20. **Separate a confound from a refutation:** run the same cell with the variable under test removed. If the outcome
    persists, you measured the confound. (Bare kings return 0 nodes at two occurrences only because insufficient
    material is an automatic draw.)
21. **`$?` after a pipe is the LAST command's status.** `cmd | tail` reports `tail`'s exit code. Use `cmd > out; rc=$?`
    or `set -o pipefail`.
22. **A reader that waits for `info depth` deadlocks on every fast path** — the opening book answers with zero info
    lines, and `go nodes 0`/`1` emit none either. **Wait for `bestmove`** (60 of 66 committed harnesses did, and are
    safe) **and put a timeout on every read.**
23. **`go infinite` is bounded by `stop` or depth 64, whichever comes first — and on a real position it is `stop` that
    matters.** Startpos ran a 75-second cap and reached only depth 30 (`cp 7`, 93,981,191 nodes). `stop` returns a
    legal move in 0–1 ms. **Send `stop` and assert the reply.**
24. **The opening book fires on exactly the clock and movetime `go` forms.** A depth, nodes or infinite harness can
    never hit it; only a clock or movetime harness needs `OwnBook false`.
25. **Fullmove number and halfmove counter are part of a position's identity** — 5 different mate values across
    counters 0–99, and a 2× node swing for an identical score.

**After you measure**
26. **Adjacency is a check.** A claim and its correction must sit next to each other; separation is what let
    contradictions survive. Reordering three sections of one report exposed three contradictions the long layout had
    hidden.
27. **A correction that adds without removing is not a correction.** Adding is an authoring act; removing is a search
    act, and the search only works if you look for what you wrote. **Write both in one edit**, then grep for the
    phrase you contradicted.
28. **When a claim is corrected, re-run every number inside the corrected passage in the same edit.** Revising a
    figure feels like changing evidence; revising the sentence feels like editing — so the prose moves and the number
    stays. **The correction is exactly the moment a figure is least likely to be looked at again.**
29. **A decomposition is only as good as the pairing of each term to its column, and that pairing needs a LABEL
    check, not an arithmetic one.** A fabricated node ratio (`0.9090`) closed the identity to 0.1 % and appeared in
    *neither* of the source's columns. **A number that makes the identity work is the most dangerous kind, because
    the identity's own closure is what it was manufactured to satisfy.**
30. **"I could not evaluate this" must never be reported as "this is fine."** A check that declines to evaluate has
    cleared nothing; it is a third verdict, not a pass. Any finite vocabulary has a boundary, and past it the check
    reports PASS rather than UNKNOWN.
31. **A count printed is not a count checked**, and a count must be compared against the prose, not merely printed.
    **Assert the exact expected count as a literal**, never computed from the list it guards.
32. **A checker is tested by giving it a case whose answer you already know, never by reviewing its logic.** Every
    checker failure in this run that was caught, was caught that way; none was caught by reading the checker.
33. **A script cited as evidence must be tested for its EXIT CODE, not just its output.** Two scripts the report told
    a reader to run printed `FAIL` and exited 0. **Prove a gate once per checker it invokes, not once per gate.**
34. **A verdict that depends on where you stand is not a verdict.** Five scripts depended on the run directory; one
    compared an empty string to an empty string and reported verbatim agreement. **Anchor to `__file__` and run each
    script twice — from its own directory and from `/tmp`.**
35. **A settings NAME is not evidence the settings were sent.** One harness's option list was named `S14` while
    containing the five PC20 switches. **Have a tool print the option list at run time and paste that output into the
    finding.**
36. **Bench is not a proxy for real positions, and its bias is patch-specific, not directional.** Three measured
    failure modes: per-node cost ~1.2 % on bench vs **~6.4 %** on real positions (6× optimistic); aggregate node-count
    sign **+14.5 / −10.6 / +8.7** across benches 11/13/16 against **−8.7 %** on real positions; a profile self-time
    share 2.71 % on bench vs **0.66 %** real. **A self-time percentage is not a transferable cost unless someone
    removes the code and measures it.**
    - **Bench IS valid for** pins, determinism, ablation direction, structural counters, and the pooled effect of one
      isolated toggle. **Not valid for** per-node cost or the aggregate PC20 set. **Always report the per-position
      spread.**
37. **Cold reading is the highest-yield instrument on the class the checks cannot reach.** Four defects in six blocks
    — a joining phrase doing the work of three results, ordinals running backwards, a table row implying a control
    that never existed — **all invisible to every automated check, all found by reading.** Not a substitute for the
    checks; it covers what they structurally cannot.

---

## 5. Unsourced in the consolidated report

**Count of figures with no source anywhere in the 25 branches: 0.**

Every numeric token in the consolidated report — 226 distinct percentage, ratio, large-integer and fraction forms —
appears in at least one branch's committed markdown (8.4 MB across the 25 branches, not just `FINDINGS.md`). The
audit was comma- and separator-insensitive and ran over the whole tracked `forge-combo29/swarm/NN/*.md` tree.

**The limit of that check, stated because the run itself states it:** this proves **presence**, not **pairing**. "The
audit checks that SOME path resolves, not that the path supports the claim." A figure can appear in a branch and still
be attached to the wrong quantity here. That is what §6 is for, and it found four.

---

## 6. Sourced but mis-paired — where the report and its own sources disagree

Not "unsourced", but **the same defect class the report polices in others**, so it belongs in front of you.

### 6.1 The `softnodes` low bound is spliced from a different measurement — **corrected in this document**

The consolidated report's ¶ gives the 80-cell sweep's span as **`0.07×` to 3.50×**. The branch that ran it
(`swarm-27` S-C96) reports the 80-cell sweep as **`1.008×` to `3.503×`**. The `0.07×` cannot come from that sweep at
all — its budgets are 500 and 2,000, and a floor of 1,344 nodes against a 2,000 budget is `0.672`, not `0.07`.
`0.07` is `1,344 / 20,000`, from the separate floor probe at budgets 200…100,000 (S-C99). A later row, S-C100,
splices the two into one sentence — "spans 0.07x to 3.50x across 40 positions x 2 budgets" — and the consolidated
report inherits that sentence.

**This document uses the wording supplied by the seat that measured both directions**, which does not claim the two
bounds come from one population: *"0.07x to 3.50x across the populations measured."* The 60-position scope run
(S-C101) is separate again and is quoted with its own settings. **If you re-derive the range yourself, keep the three
populations apart: floor probe (200…100,000), 40×2 sweep (500/2,000), and the 60-position scope run (2,000).**

### 6.2 A "3 of 5" reads as a correction but states a different quantity — **no contradiction once parsed**

`internal/swarm/tally.md` (and `swarm-27` S-C95) say: *"it is 3 of 5, NOT absolute."* On first read that looks like a
duplicate count of 3 of 5, which would contradict the table beneath it. **It does not.** "3 of 5" counts the rows that
*carry no signature*; the table records **2 of 5 exact duplicates** (K+R v K, middlegame B) and 3 of 5 differing in
score. The 40 % / 60 % split follows from 2 of 5 and is correct.

**I am recording the ambiguity rather than the error:** a correction whose number counts the complement of the thing
being corrected reads as its own contradiction. Anyone quoting "3 of 5" for duplicates — including me, on a first
pass — gets the sign backwards. **The figures I use are 2 of 5 duplicate / 40 % caught / 60 % missed.**

### 6.3 Two stale absolutes survive in the sources the report was built from

Both were withdrawn, and both are still standing where a future reader will meet them:

- **`internal/swarm/tally.md`, S-C87 bullet** — "…confirm **there is no duplicate signature at all**." That is **four
  lines below** the S-C95 correction and directly contradicts it. It is the sentence you asked me not to carry; it is
  still live in the tally. (The branch row it summarises, `swarm-27` S-C87, says the weaker but still-overstated
  "**there is no duplicate signature**" — while its own table, three rows later, lists two.)
- **`swarm-27`'s `FINDINGS.md`, row S-C88** — "**A fresh session with no previous position gives NO diagnostic at
  all** — it silently searches startpos, so the first position in a run is the one failure undetectable from the
  reply." **The four-combination measurement refutes this:** the diagnostic is always emitted; only its location
  moves. **No row on the branch records the four-combination result** — I searched all 25 branches' markdown for
  "four combinations" and for the always-emitted wording and found neither. `S-C93` on the same branch proves the
  *other* half (that without `isready` the diagnostic lands in the `go` output, before the first `info depth`) with a
  non-vacuous control — which is what makes S-C88's absolute untenable — **but the retraction sentence itself exists
  only in the consolidated report.**

**I did not edit either file.** Both are other seats' branches or the coordinator's tally. **The owner-facing
consequence: the withdrawn claim is the one that will be found first by anyone reading the branch history, so the
corrected version should be carried in the branch, not only in the report.**

### 6.4 A verification claim in the tally is wider than what was run

`tally.md` records that `frontpage_check.py` now validates three leading claims (PASS, PASS, PASS) and that
`final_recheck.py`'s "11 of 11 agreeing" is "a sentence no code produced" until it was given a failing exit path.
**Both statements are about scripts that were fixed after failing to exit non-zero.** The fixes are described and
re-proved; **I did not re-run either script**, and this summary does not rely on their output. Flagged so you know the
claim's status is "fixed and described", not "independently re-verified in this assembly."

---

## 7. How this document was assembled

- **Read in full:** `docs/forge-findings.md` (1,429 lines) and `internal/swarm/tally.md` (637 lines).
- **Read:** the `FINDINGS.md` of all 25 branches that carry one, plus every other `.md` under
  `forge-combo29/swarm/NN/` for the 25 seats where a figure needed a home — 8.4 MB of branch markdown in total.
- **Branches with no `FINDINGS.md`, not counted as read:** `swarm-09, 14, 18, 22, 26, 31, 33, 34, 37–42, 47, 48,
  51–53, 55–58, 60`, plus the non-`swarm-NN` branches.
- **`git fetch --all` was run twice.** Two corrections you sent (`S-C101`/`S-C102`, and the `S-C96`…`S-C100`
  softnodes block) landed on `swarm-27` *after* the first fetch; the second fetch is why the softnodes section quotes
  the 60-position scope run at all. **Any figure here dated before 03:47Z on that branch was re-read after it.**
- **Nothing was run.** No engine invocation, no script execution, no re-measurement. Where a figure is quoted, it is
  quoted from a branch, with that branch's conditions.
- **No other seat's branch was modified.** Two files in the sources are stale (§6.3) and were left alone.
- **Counts printed as literals, from the artifact:** **25** branches read, **2,283** distinct findings synthesised
  (2,304 rows), **0** unsourced figures, **3** sourcing defects.

**What I could not source, summarised: 0 figures.**

The number you need for the coordinator's tally:

> **Unsourced figures: 0.**
> Every numeric token in the consolidated report — 226 distinct percentage, ratio, large-integer and fraction forms —
> resolves to committed content in at least one of the 25 branches.

**Separately, 3 sourcing defects** — none of them an unsourced figure, all of them the mis-pairing class the report
polices in others (§6):
1. **The `softnodes` low bound is spliced across two populations** — `0.07×` is from the 200…100,000 floor probe and
   is not in the 40×2 sweep (which spans `1.008×`–`3.503×`). This is in the consolidated report; I use the measuring
   seat's own wording instead (§6.1).
2. **`swarm-27` S-C88 still asserts an absolute that the four-combination measurement refutes** — and **no branch row
   carries the four-combination result** (§6.3).
3. **The tally's `S-C87` bullet still asserts "no duplicate signature at all"** four lines below the correction
   (§6.3).

Plus one **readability** defect that is not an error: the tally's "3 of 5" counts the complement, and reads as its own
contradiction (§6.2).
