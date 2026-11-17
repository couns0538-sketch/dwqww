# Owner summary — forge-combo29 C++20 chess engine audit

**Audit window:** 2026-11-16T22:20Z → 2026-11-17T10:20Z.
**Assembled by:** seat `swarm-73`, from committed branch content only. **Nothing here was re-measured.**
**Branches read:** **26** (`swarm-01, 02, 03, 04, 05, 06, 07, 08, 10, 11, 12, 13, 15, 16, 17, 19, 20, 21, 23, 24, 25, 27, 28, 29, 30, 75` — every branch under `origin/for-fable-and-opus/` that carries a `FINDINGS.md`).
**Findings synthesised:** **2,302** distinct findings — **2,293** from table rows plus **9** from `swarm-75`, which
records its findings as prose sections (`75-F1`…`75-F9`) rather than table rows and so is invisible to a row count.
2,314 table rows in total; 21 are re-runs recorded under an existing id.

That count is a count of *findings I read*, not a claim that 2,302 separate claims are each correct. The consolidated
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

A refused `position fen` still answers `readyok`, **keeps the last valid board, and a search then returns a
normal-looking result for that board** — legal `bestmove`, plausible ±30 cp score, full PV, correct-looking node
counts. **The engine searches the last valid board, which in a fresh session is the start position.**

**There are TWO fallbacks, not one.** With no predecessor the invalid FEN is answered from **startpos**; with a
predecessor it is answered from **that predecessor**. A four-cell matrix over (isready sent? × predecessor present?),
each cell with a legal control so "absent" cannot mean "never fires", measured identically on both builds:

| isready? | predecessor? | diagnostic? | bestmove |
|---|---|---|---|
| no | no | **YES** | `d2d4` (**startpos**) |
| no | yes | **YES** | `a1a8` (**the predecessor**) |
| yes | no | **YES** | `d2d4` (**startpos**) |
| yes | yes | **YES** | `a1a8` (**the predecessor**) |

**So "the previous position" describes only one of the two cells.** The accurate description — the one to write in a
harness comment or a bug report — is **"the last valid board"**, which covers both.

The diagnostic **is always emitted**; only its **location** moves with where you read:

| your harness | where the diagnostic lands |
|---|---|
| sends `isready` between `position` and `go` (the normal defensive pattern) | in the **position reply**, before `readyok` |
| does not | in the **`go` output**, ahead of the first `info depth` line |

Both hold **in a fresh session as well as after a predecessor**. There is no undetectable first position.

**So: scan BOTH the position reply and the search output, and check before parsing any `info depth`.** A harness
reading only one stream misses it half the time.

**But assert exactly ONE occurrence — it is emitted once, not in both streams.** With `isready` the position reply
carries it and the search output does not (`position=1 go=0`); without, the search output carries it (`go=1`).
**A checker that required it in both streams would always fail**, which is the mirror image of the harness that reads
only one. Scan both; count one.

**Primary defence: validate every FEN before sending it** — `readyok` is not a statement about the position.

**What would overturn it:** an invalid FEN that produces no `info string` on either stream. None found across all
four combinations. **What the occurrence count rules out:** a `position=1 go=1` cell — it would mean the diagnostic
duplicates, and no cell measured that.

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

### 1.7 `MultiPV 1` at any Hash; otherwise cap Hash by line count — **ship** (throughput); *and* distrust near-horizon positions — **needs-more-evidence**

Fixed `go nodes 200000` grid (work constant, time the variable), PC r15 + PC20, Threads 1 — milliseconds:

| Hash | MPV 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 16 | 116 | 140 | 146 | 145 |
| 64 | 113 | 193 | 200 | 227 |
| 256 | 132 | **384** | **557** | **550** |

**113 → 557 ms = 4.9×**, with six cells slower than 1.5× the fastest spanning two Hash values and three MultiPV
values — a diagonal boundary, not one bad cell.

**The practical rule is a per-line cap, and the product form is wrong. Do not use `Hash × MultiPV` as the model.**
- **The cost is not Hash, not MultiPV, and not their product.** **Four cells share `Hash × MPV = 96` and measure
  1.30×, 1.35×, 1.37× and 1.55×** — **no constant separates them.**
- **MultiPV 1 is flat in Hash** (114.0–139.3 ms across Hash 8–256, a 1.22× spread with no trend, 8 of 8 within
  1.5×, **identical node counts**). **So no product form can express it:** `Hash × 1` grows and the measurement does
  not.
- **The product model gets both directions backwards: Hash 64 with 2 lines is NOT fine (1.57×), and Hash 8 with 6
  lines IS fine (1.18×).**
- **What the cost actually is:** `Hash × wipes`, where `wipes = depth × (MPV−1)` — and **depth itself falls as
  MultiPV rises** (14 / 13 / 11 at MPV 1 / 2 / 6). **That coupling is what breaks the product.**

**The measured boundary** — fitted against a 1.5×-unsafe threshold over **48 cells**:

| predicate | misclassified | false-safe |
|---|---|---|
| `Hash × MPV ≤ 144` | 4/48 | 3 |
| `Hash × (MPV−1) ≤ 120` | 3/48 | 3 |
| `Hash ≤ Hmax(MPV)`, Hmax = {1:**256**, 2:**48**, 3:**48**, 4:**24**, 5:**24**, 6:**24**} | 1/48 | 1 |
| the same, capped conservatively (**2 lines ≤ 48 MB; 3–6 lines ≤ 24 MB**) | **1/48** | **0** |

**The recommendation: `MultiPV 1` at any Hash; otherwise cap Hash by line count — 48 MB for 2 lines, 24 MB for 3 to
6 lines.** That is the conservative fitted form, and it is **the one to ship because it has zero false-safe cells out
of 48**.

**The property that matters is zero false-safe, not the misclassification count.** Both forms misclassify 1 of 48, but
a **false-safe** call tells you a slow configuration is fine — the error that costs you throughput silently. A
misclassification in the other direction merely tells you a safe configuration is risky, which costs you caution.

**For a technical reader, the fitted ceiling is slightly more permissive:** **48 MB at 2 to 3 lines, 24 MB at 4 to 6**
— `Hmax(MPV)` with 48 admitted at 3 lines (measured 1.49×) — and it carries **1 false-safe cell of 48**. **Recommend
the conservative version; use the fitted one only when you are willing to trade that cell for the extra headroom.**

**Do not use a "per-line cap" or a product, and do not use a flat Hash ceiling for multiple lines.** A flat ceiling is
the coarse form these measurements refuted: it forbids configurations that are safe (Hash 8 with 6 lines is 1.18×)
while permitting ones that are not (Hash 64 with 2 lines is 1.57×).

**Mechanism, and it is two mechanisms, not one.** Between-line `tt.clear()` plus a second full-size alternate table
(nodes/ms 559 → 183 → 2 at MPV 3 versus a flat ~1,500 at MPV 1). A patch removing the redundant clear **rescues 17 of
22 unsafe cells** (22/48 → 5/48), every one at Hash ≤ 128. **The residual 5 are all Hash 256, MPV 2–6, at 1.90–1.99×
and FLAT in MultiPV** — a per-line cost would keep climbing, so it is not per line. **It is the alternate table's
ALLOCATION: ~105 ms of zero-fill, once per search.** Time-to-first-`info`: **1.4 ms at MPV 1 versus 105.9 ms at
MPV 2**, Hash 256 — so the patch is **necessary but not sufficient**, and at Hash 256 the remaining cost is
allocation rather than clearing.

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
node budget **and** whose `Hash × MPV` product differs from a safe cell's by a constant that separates them — the
first half is what "safe" means, the second is what would rescue the product model. Neither was found in 48 cells.
**What would settle the answer claim:** ~2,400 positions with the score-change criterion.

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

**And this advice has one measured exception, which is worth reading because it shows where the rule does not
apply.** "No v3 micro-patch" is a rule about **shares being too small to justify work**; it is not a claim that no v3
work can pay. **§1.19's pair-count dispatch patch is measurably faster (1.2–1.6 %) and identity-exact** — the win came
**not from the share being large but from the function's work being removable without touching the identity.**
So: **do not chase the percentages, but do check whether a specific piece of per-node work can be eliminated outright.
Those are different questions, and this run answered the second one positively.**

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

### 1.17 Fix `is_insufficient_material()` for two knights — **ship** (the smaller, surgical change); the bare-minor scale factor — **needs-more-evidence**

Two evaluation defects, measured separately. **One reaches search; the other does not, and the one that does not is the
larger.**

**The headline: adding a bishop to a bare king LOSES 149 centipawns.** Build `6b98f2170`, `g++-13`, `Threads 1`,
Hash 16, `OwnBook false`, one fresh process per measurement, `DeadMaterial false`, measured on the engine's own `eval`
command so **no search and no movegen are involved**:

| position | FEN | total | hce | nnue |
|---|---|---|---|---|
| K vs K | `4k3/8/8/8/8/8/8/4K3 w - - 0 1` | **+2** | 0 | +2 |
| **KB vs K** | `4k3/8/8/8/8/8/8/2B1K3 w - - 0 1` | **−147** | +16 | **−163** |
| KN vs K | `4k3/8/8/8/8/8/8/1N2K3 w - - 0 1` | **−144** | +9 | −153 |
| KR vs K | `4k3/8/8/8/8/8/8/R3K3 w - - 0 1` | +353 | +442 | −89 |
| KQ vs K | `4k3/8/8/8/8/8/8/3QK3 w - - 0 1` | +768 | +783 | −15 |

**1 inversion in 16 material steps.** The cause is not ambiguous: **the handcrafted term is right (+16 for the bishop);
the NNUE residual is −163 and dominates**, because `scale_factor()` (`src/eval.cpp:389-412`) returns **0 or 12** when
the stronger side has no pawns and leads by at most a bishop, which nearly erases the handcrafted term. Confirmed by
`setoption name UseNNUE value false`, under which the same boards return `0 / +16 / +10` — sane.

**Systematic, not a placement artefact:** the bishop square swept over `a1, c1, d4, h8, b6, e3` and scores
**−127 to −159 at every one**.

**Endgame-only, and the scope is precise:** with pawns present the same ladder is cleanly monotonic
(`18 → 434 → 461 → 859 → 1614`), and in a real middlegame removing Black's f8 bishop from the standard array moves
the score from **+16 to +493 — a normal +477 for a bishop.**

**Why I split the verdict:** the static inversion is real and reproducible, but **search adjudicates KB vs K and
KN vs K as draws**, so the wrong number never reaches play. **A patch to `scale_factor()` therefore changes no game
outcome that was measured** — and its blast radius is every pawnless ending, which is a much larger surface than the
one defect that does reach search. **Fix the search-reachable one; leave the scale factor alone until someone measures
a game-level effect.**

**The one that reaches search: KNN vs K is a draw, but `is_insufficient_material()` (`src/board.cpp:1250-1258`)
requires `knights == 0`**, so two knights are never adjudicated:

| ending | theory | static | search d6 | `is_insufficient_material()` |
|---|---|---|---|---|
| K vs K | draw | +2 | **cp 0** | true |
| KB vs K | draw | −147 | **cp 0** | true |
| KN vs K | draw | −104 | **cp 0** | true |
| **KNN vs K** | **draw** | **+187** | **cp 251** | **false** |
| KBN vs K | win | +237 | cp 272 | false |

**So `+187` static becomes `cp 251` in a real depth-6 search.** Every other wrong bare-minor static is masked by the
insufficient-material verdict; **this one is not.** The engine believes a drawn KNN vs K is a quarter-pawn-plus win and
will steer toward it. **The `DeadMaterial` option does not cover it either**, so enabling that option does not fix it.
KBN vs K is the control proving the tests can tell a win from a draw: a real win, scored +237 static / cp 272 at depth
6, correct.

**What would overturn the KNN verdict:** a search that returns cp 0 for KNN vs K at depth 6 under default options — the
measured value is cp 251 with the verdict `false`. **What would turn the scale-factor item into a ship:**
a game-level measurement — self-play or SPRT — showing the inverted bare-minor score changes move choice or result
often enough to matter. **None was run** (§3).

### 1.18 A warm transposition table changes fixed-depth scores — **ship** (as a harness rule)

Search scores are **not reproducible when several positions are searched in one engine process.** The same KBN-vs-K
board, depth 6:

| how measured | score |
|---|---|
| 3rd search in a shared process | cp 293 |
| 2nd search in a shared process | cp 285 |
| 1st search in a shared process | cp 274 |
| **fresh process, three separate runs** | **cp 272, 272, 272** |

**The TT carried from the previous search changes move ordering, which changes which reductions and prunings fire, so
a fixed *nominal* depth does not mean a fixed *effective* search.** The horizon ladder drifted the same way: warm
`1257…1282` against cold `1257…1305`.

**This would manufacture a fake depth trend** — a warm-TT comparison could invent a trend that does not exist, or hide
one that does. **Every measurement in this report that compares depths uses one fresh process per cell.**

**What would overturn it:** three in-process searches on one board returning identical scores. They returned
274 / 285 / 293.

### 1.19 Time the v3 pair-count dispatch patch on your own build — **needs-more-evidence**

**This is the first positive performance recommendation in the run**, and its verdict is *not* ship. The patch is
small, identity-exact, and measurably faster on the author's build — and the author's build is not yours.

`v3/v3_pair_count_dispatch.patch.txt` — **67 lines**, applies to file 5's tree (`6b98f217` + `pc_r15.patch`) with
`patch -p1 --fuzz=0`, no rejects. `apply_changes_pair_avx512` re-tested `i < c.count` **inside** the 32-lane `h`
loop, for both perspectives; the patch **dispatches once on `c.count` (1..4**, the ceiling `collect_changes` already
enforces) into unrolled specialisations, so each slot's liveness is decided outside the `h` loop. **Arithmetic per
element, slot order and lanes are unchanged — by construction the results are bit-identical**, and the identity check
tests exactly that.

**Identity is EXACT** on a build from a clean `6b98f217` + file 5 tree, `-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`,
g++ 13.3.0:

| check | required | verified |
|---|---|---|
| bench 11 / 13, no setoption | 312866 / 862329 | **312866 / 862329** |
| bench 11 / 13, PC20 | 278024 / 587276 | **278024 / 587276** |
| bench 11 / 13, test net | 965454 / 4151906 | **965454 / 4151906** |
| bench 11 / 13, PC20 + net | 625258 / 3652372 | **625258 / 3652372** |
| eval | 968 / 1176 / 31 | **968 / 1176 / 31** |
| **200-opening node sum** | **27,944,084** | **27,944,084** |

**Speed, two arms:**

| arm | setting | result |
|---|---|---|
| bench 13, PC20 + net, alternating base/patch, 10 runs each | node counts identical every pair | **2126 → 2092 ms**, ratio **0.9838 (1.6 % faster)** |
| **real positions, n=120, ABBA, fixed `go nodes 200000`**, PC20 + test net | **node counts matched 120 of 120** | median ratio **0.9878 (1.2 % faster)**; 2.5th/97.5th pct **0.961 / 1.026**; **107 of 120 positions faster**; two-sided sign test **p = 1.5e-19** |

**I re-derived the sign test independently and it matches: exact two-sided binomial, 107 of 120, p = 1.4959e-19.**
That is not a formality here — see the caveat in §4, because **107/120 is a share above half, which is precisely the
case this run's own buggy sign test saturated on at p = 1.000.**

**Why needs-more-evidence and not ship:**
- **The author's compiler is g++ 13.3.0 with no `-march`; yours is clang + `-march=znver5` + PGO.** A different
  compiler can turn an explicit unroll into nothing, or into more work. **This is evidence the patch is worth timing
  on the real build — not a substitute for that timing.**
- **+1.2–1.6 % is small enough that the real build decides.** A 1.6 % bench win and a 1.2 % paired median are not a
  reason to ship a change on a build nobody has timed.
- **The net is the shared-shape test net**, not your trained one.

**What would overturn it — in both directions:**
- **Toward ship:** your build, two builds per variant, timed exactly as the report's Step 3 requires, reproducing
  ≥ 1 % with node counts matched. **That converts this to a ship.**
- **Toward do-not-ship:** a real-build timing where the ratio's CI includes 1.0, **or** where node counts are not
  matched (which would mean the patch changed the search, not just its speed).

**And what it does not claim:** **no strength claim.** Node counts are identical by construction, so any strength
difference would be noise.

### 1.20 Opening book: set `OwnBook false` only when it can fire, and know that it pre-empts draw adjudication — **ship** (as a harness rule)

The book's own soundness is clean (§7); **what it does to a harness and to a caller is three separate hazards.**

**1. The condition is narrower than "the clock form": it fires on the SIDE-TO-MOVE'S OWN clock, or on `movetime`.**
The gate is `time_ms >= 0 || movetime_ms >= 0` (`uci.cpp:371`), and `time_ms` is set **only for the side to move**
(`uci.cpp:108-109`). So:

| command | side to move | reaches the book? |
|---|---|---|
| `go btime 10000` | White | **no — searches** |
| `go btime 10000` | Black | **yes — books** |
| `go movetime 100` | either | **yes — always books** |
| `go depth N` / `go nodes N` / `go infinite` | either | **never** |

**So `OwnBook false` is needed only when the moving side's clock is sent** — sending the *opponent's* clock is safe
from the book and unsafe in a different way (§2.7: a one-sided clock is no clock at all).

**2. The book pre-empts drawn-root detection, and it does so silently.** A halfmove-clock-100 startpos still emits
`book move e2e4`, **and so does a threefold-repetition root**: the book decides before any draw adjudication runs.
**So a drawn position ships a book move and a `bestmove` with no `cp 0` and no empty `pv` to warn a caller** — which
defeats the one reliable caller-side check in §1.3. A front end that keys on empty-`pv` will not recognise this case.

**3. `Book Depth` is derived from the FEN's FULLMOVE COUNTER, not from the move count** (`game_ply()`,
`uci.cpp:127-129`). **The same chess position at fullmove 1 versus 21 books versus searches** — so any tool that
writes a FEN without the true move number changes whether the book is consulted at all. **This is the identity trap of
§4 rule 27 in a place you would not look for it.**

**What the book path emits: exactly two lines and nothing else** (`uci.cpp:385-387`) — `info string book move <uci>`
then `bestmove <uci>`. **No `info depth`, no score, no node count.** A GUI showing a score for that move is showing
its own default.

**And the latency gap is four orders of magnitude, which is why this bites harnesses:** book **p50 0.024 ms**, max
0.44 ms over 200 round trips; off-book **p50 442 ms** in the same harness. **A reader waiting for an `info depth`
line times out on every book move** — proved with a passing off-book control.

**What would overturn it:** a book move on a `go depth`/`go nodes` command (would widen the condition), or a
drawn-root position that emits `cp 0`/empty `pv` instead of a book move (would remove hazard 2).

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

### 2.3 A refused FEN returns a well-formed answer for the last valid board — **broken**

See §1.4 for the defence. **The engine searches the last valid board, which in a fresh session is the start
position** — so this is a defect in a fresh session too, not only after a prior search.

The severity is that **the fabricated row is harder to detect than a duplicate**: where the predecessor differs, the
score differs too, because the re-search runs on a restored board with different TT and history state.

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

**The discriminator that establishes "last valid board" over "always startpos":** send the SAME invalid FEN after two
DIFFERENT valid positions. An always-startpos fallback predicts the same answer both times; a refusal predicts no
`bestmove`; **last-valid-board predicts each predecessor's own answer, differing**. Measured: after A
(`6k1/5ppp/8/8/8/8/5PPP/R5K1 w`) → `a1a8` / mate 1; after B (after 1.e4) → `e7e5`. **They differ, so an always-startpos
fallback is excluded** — and the no-predecessor cells of the §1.4 matrix supply the other half, where the same invalid
FEN *does* answer `d2d4`. Bit-identical 3/3 on PC r15 and identical on base release, so it **predates the patch**.

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

### 2.8 The opening book overrides draw adjudication without a signal — **broken**

Two consumers are affected and neither gets a warning:

- **A drawn position gets a book move.** A halfmove-clock-100 startpos emits `book move e2e4`, **and so does a
  threefold-repetition root.** The book decides before any draw adjudication runs, so the reply carries **no `cp 0`
  and no empty `pv`** — the caller-side check of §1.3 does not fire, and a front end plays a book move in a drawn
  game.
- **`Book Depth` follows the FEN's fullmove counter** (`game_ply()`, `uci.cpp:127-129`), so **the same position at
  fullmove 1 versus 21 books versus searches.** A tool that writes a FEN without the true move number silently gets a
  different code path, with the same two-line reply that carries no score.

**Not a correctness defect in the book itself** — its moves are sound (§7). **It is a defect in what the book tells a
caller about the position**, which is the definition §2 uses.

### 2.9 What is *not* broken, and was claimed to be

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

**From the evaluation audit (§1.17), stated as the measuring seat states it**
- **The bare-minor material inversion has no measured game-level cost.** The static inversion is real and the
  KNN-vs-K case reaches search, but **no game-level cost was measured: no SPRT, no Elo claim.** Anyone who wants to
  prioritise the `scale_factor()` fix over the `is_insufficient_material()` fix has no measurement to prioritise on —
  which is why §1.17 ships one and holds the other.
- **Evaluation symmetry is evidence, not proof.** **0 asymmetric pairs of 420** (20 hand-picked + 400 seeded), in
  `hce` and `nnue` separately, measured on the static evaluator so no movegen is involved. Strong, and **not a proof
  over all positions.**
- **The bare-minor sweep covers six bishop squares**, `a1, c1, d4, h8, b6, e3`, scoring −127 to −159. **Systematic
  across those six; not a proof over all squares.**

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
4. **A warm transposition table changes fixed-depth scores — use one fresh process per measurement.** The same
   KBN-vs-K board at depth 6 scored **cp 274, 285 and 293** as the first, second and third search in one process,
   against **cp 272 three times** cold. The TT carried from the previous search changes move ordering, which changes
   which reductions fire, so a fixed *nominal* depth is not a fixed *effective* search. **This would manufacture a
   fake depth trend** — and hide a real one — which is why every depth comparison in this report uses a fresh process
   per cell (§1.18).
5. **Validate every FEN before sending it, and read the reply.** `readyok` is not a statement about the position.
6. **State, in advance, what result would support the hypothesis and what would refute it** — including for rows whose
   expected value is "unchanged". A table can be arithmetically correct and read backwards.

**While you measure**
7. **Report wins / ties / losses together, and use the SHARE, not the SUM.** "+3 ply over 6 positions" and "+8 ply
   over 130" are the same comparison; the second sounds like progress and is compatible with half the positions being
   identical and a median difference of exactly zero.
8. **A sign-share computed from a QUANTISED measure is a share of that measure's granularity.** Wall time at 1 ms
   resolution on 19 ms searches → **64.6 % exact ties**; integer depth, no timer → **50.0 % exact ties**. Decompose:
   at `go nodes 50000` wins/decided is 65.2 %, at `500000` it is 58.7 % — **once ties are excluded the two budgets
   agree.** Quote a sign-share **with its budget**, never as a bare property of the patch.
9. **Lengthen the measurement rather than redefining the share.** 50k → 500k took ties from 64.6 % to 6.9 % without
   changing the effect's direction.
10. **A sign-share alone cannot classify a claim; the interval decides first.** 50.6 % with no established effect and
   60.5 % with a real pooled effect are closer to each other than either is to 90 %.
11. **"Not established" ≠ "no effect" ≠ "coin flip."** A result whose CI includes 1.0 is **unresolved**. "Coin flip"
    means exactly one thing: a real pooled effect that is per-position random.
12. **Every per-node figure divides by the reported count, not the requested budget.** Otherwise the request cancels
    and you report a time ratio under a per-node label.
13. **A comparison at a fixed node budget cannot show a node saving.** Both engines stop in the same place by
    construction; any residual is the stopping rule's granularity. A 50.6 % sign-share measured there was a correct
    measurement of an effect that does not exist.
14. **`go nodes N` does not fix the workload once `MultiPV > 1`.** The node budget is **shared across the alternate
    lines**, so raising MultiPV *lowers* the reported work: **N = 200,000 spends 52,472 to 199,619 reported nodes,
    falling as MultiPV rises.** So a fixed-nodes arm is not "the same amount of search" when the MultiPV setting
    differs between its arms — and a throughput comparison across MultiPV settings is measuring two things at once.
    **State which quantity is being held constant, and check it held.** (The grid in §1.7 holds time and lets nodes
    vary; that is why it can measure throughput across MultiPV at all.)
15. **Report median and geometric mean labelled, side by side.** Three statistics on one distribution gave three
    different conclusions, and the distribution was the finding.
16. **Put the per-position spread on the headline line.** A pooled 5 % saving that wins on 54.2 % of positions with an
    IQR 28× the effect size is a real effect and an unusable per-position predictor. **More data will not remove
    this — it is what the switch does.**
17. **Any speed number from fewer than ten positions is a hypothesis, never a result.** Two out of two small samples
    in this harness erred upward, once by 4×.
18. **A p-value must be recomputable from the counts printed in its own row.** Three of four published sign-test
    p-values read `1.000` when the counts beside them give 0.022, 0.648 and 0.411. The cause was a **missing
    `min(k, n−k)` reflection**, so the test saturated for every share above half and was correct only below it —
    **the one correct row was the below-half one, which made a broken function look validated.** Commit the test, not
    the answer, and give it a symmetry self-test: `p(k, n) == p(n−k, n)`.
19. **A control must be demonstrated to fail when the input is wrong**, not merely to pass when it is right. Three
    natural ways to write one all pass vacuously: `max()` of nothing, `all()` of nothing, a lookup falling through to
    a default. **A control that returns a plausible wrong number is worse than one that crashes.**
20. **A control cell proves only what its axis can see.** When you quote one, **say which axis it controls for.**
21. **A cap test needs a rising-series control.** "Respected the cap" is equally consistent with "ignored the budget
    and searched a fixed amount" unless rising budgets produce rising work.
22. **Separate a confound from a refutation:** run the same cell with the variable under test removed. If the outcome
    persists, you measured the confound. (Bare kings return 0 nodes at two occurrences only because insufficient
    material is an automatic draw.)
23. **`$?` after a pipe is the LAST command's status.** `cmd | tail` reports `tail`'s exit code. Use `cmd > out; rc=$?`
    or `set -o pipefail`.
24. **A reader that waits for `info depth` deadlocks on every fast path** — the opening book answers with zero info
    lines, and `go nodes 0`/`1` emit none either. **Wait for `bestmove`** (60 of 66 committed harnesses did, and are
    safe) **and put a timeout on every read.**
25. **`go infinite` is bounded by `stop` or depth 64, whichever comes first — and on a real position it is `stop` that
    matters.** Startpos ran a 75-second cap and reached only depth 30 (`cp 7`, 93,981,191 nodes). `stop` returns a
    legal move in 0–1 ms. **Send `stop` and assert the reply.**
26. **The opening book fires on the SIDE-TO-MOVE'S OWN clock, or on `movetime` — not on "the clock form".** The gate
    is `time_ms >= 0 || movetime_ms >= 0` (`uci.cpp:371`) and `time_ms` is set only for the side to move
    (`uci.cpp:108-109`), so **`go btime 10000` with White to move searches, and the same command with Black to move
    books.** `movetime` always books. A depth, nodes or infinite harness can never hit it. **`OwnBook false` is needed
    only when the moving side's clock is sent.**
    - **The book path emits exactly TWO lines** (`uci.cpp:385-387`): `info string book move <uci>` then
      `bestmove <uci>`. **No `info depth`, no score, no node count.** A GUI showing a score for a book move is showing
      its own default.
    - **The latency gap is four orders of magnitude:** book **p50 0.024 ms**, max 0.44 ms over 200 round trips;
      off-book **p50 442 ms** in the same harness. **A reader waiting for an `info depth` line times out on every book
      move** — proved with a passing off-book control.
    - **And `Book Depth` is derived from the FEN's fullmove counter** (`game_ply()`, `uci.cpp:127-129`), so the same
      position at fullmove 1 versus 21 books versus searches. **A tool writing a FEN without the true move number
      changes whether the book is consulted.**
27. **Fullmove number and halfmove counter are part of a position's identity** — 5 different mate values across
    counters 0–99, and a 2× node swing for an identical score.
28. **In a paired design, between-subject spread is context and the sign test is the test.** Say **which** variation a
    number describes before comparing two variances.
    - **The error this prevents, measured:** the v3 patch's author first ruled it **NOT MEASURABLE** on the reasoning
      *"the per-position spread (1.30×) is much larger than the median effect (1.2 %), so it cannot be separated from
      position variation."* **That is a category error.** The spread describes how positions differ from **each
      other**; a paired ABBA design **cancels exactly that**, because each position is its own control. The right
      question is *"does the patch win within positions?"* — a sign test on the paired outcomes. It won **107 of 120**,
      p = 1.5e-19 (§1.19).
    - **Rejecting a result looks like rigour, which is why this error survives review.** The seat called it the
      seventh reasoning failure of its night and **the first that would have discarded a true finding rather than
      overstated one** — the safe-sounding direction. **A conservative error is still an error, and it costs a real
      result.**
    - **The tell is grammatical, so it is catchable while writing:** if the statistic you are comparing an effect
      against describes **variation between subjects**, and your design is **within-subject**, you are comparing two
      different things. State the design first, then choose the test.

**After you measure**
29. **Adjacency is a check.** A claim and its correction must sit next to each other; separation is what let
    contradictions survive. Reordering three sections of one report exposed three contradictions the long layout had
    hidden.
30. **A correction that adds without removing is not a correction.** Adding is an authoring act; removing is a search
    act, and the search only works if you look for what you wrote. **Write both in one edit**, then grep for the
    phrase you contradicted.
31. **When a claim is corrected, re-run every number inside the corrected passage in the same edit.** Revising a
    figure feels like changing evidence; revising the sentence feels like editing — so the prose moves and the number
    stays. **The correction is exactly the moment a figure is least likely to be looked at again.**
32. **A decomposition is only as good as the pairing of each term to its column, and that pairing needs a LABEL
    check, not an arithmetic one.** A fabricated node ratio (`0.9090`) closed the identity to 0.1 % and appeared in
    *neither* of the source's columns. **A number that makes the identity work is the most dangerous kind, because
    the identity's own closure is what it was manufactured to satisfy.**
33. **"I could not evaluate this" must never be reported as "this is fine."** A check that declines to evaluate has
    cleared nothing; it is a third verdict, not a pass. Any finite vocabulary has a boundary, and past it the check
    reports PASS rather than UNKNOWN.
34. **A count printed is not a count checked**, and a count must be compared against the prose, not merely printed.
    **Assert the exact expected count as a literal**, never computed from the list it guards.
35. **A checker is tested by giving it a case whose answer you already know, never by reviewing its logic.** Every
    checker failure in this run that was caught, was caught that way; none was caught by reading the checker.
36. **A script cited as evidence must be tested for its EXIT CODE, not just its output.** Two scripts the report told
    a reader to run printed `FAIL` and exited 0. **Prove a gate once per checker it invokes, not once per gate.**
37. **A verdict that depends on where you stand is not a verdict.** Five scripts depended on the run directory; one
    compared an empty string to an empty string and reported verbatim agreement. **Anchor to `__file__` and run each
    script twice — from its own directory and from `/tmp`.**
38. **A settings NAME is not evidence the settings were sent.** One harness's option list was named `S14` while
    containing the five PC20 switches. **Have a tool print the option list at run time and paste that output into the
    finding.**
39. **Bench is not a proxy for real positions, and its bias is patch-specific, not directional.** Three measured
    failure modes: per-node cost ~1.2 % on bench vs **~6.4 %** on real positions (6× optimistic); aggregate node-count
    sign **+14.5 / −10.6 / +8.7** across benches 11/13/16 against **−8.7 %** on real positions; a profile self-time
    share 2.71 % on bench vs **0.66 %** real. **A self-time percentage is not a transferable cost unless someone
    removes the code and measures it.**
    - **Bench IS valid for** pins, determinism, ablation direction, structural counters, and the pooled effect of one
      isolated toggle. **Not valid for** per-node cost or the aggregate PC20 set. **Always report the per-position
      spread.**
40. **Cold reading is the highest-yield instrument on the class the checks cannot reach.** Four defects in six blocks
    — a joining phrase doing the work of three results, ordinals running backwards, a table row implying a control
    that never existed — **all invisible to every automated check, all found by reading.** Not a substitute for the
    checks; it covers what they structurally cannot.

---

## 5. Unsourced in the consolidated report

**Count of figures with no source anywhere — in the 26 branches or the working tally: 4.**

Every numeric token in the consolidated report — **252** distinct percentage, ratio, large-integer and fraction
forms, as the report stands at the time of this assembly — was checked against a corpus of 8.5 MB: every tracked
`.md` under `forge-combo29/swarm/NN/` for the **26** branches read (not just `FINDINGS.md`), **plus
`internal/swarm/tally.md`** as a fallback for figures that live only in the coordinator's working record.

### The four that have no source

| figure | where it appears in the report | what it measures |
|---|---|---|
| `52,472` | §4, the `go nodes`/MultiPV budget row | the low end of reported nodes at `MultiPV > 1`, N = 200,000 |
| `199,619` | §4, same row | the high end |
| `4/48` | §3, the `Hash × MPV ≤ 144` row | misclassified cells for the product predicate |
| `14/13` | §5b, the depth-falls-with-MultiPV clause | depth at MPV 1 / 2 in the `14/13/11 at MPV 1/2/6` ladder |

**All four belong to the same block: the new MultiPV/Hash boundary work and the MultiPV budget measurement.** That
work is attributed in the tally's own roster to **`swarm-64`** ("Hash x MultiPV boundary as an exact inequality, plus
the `tt.clear` patch"), and **`swarm-64` is not among the pushed branches** — `git branch -r` returns nothing for it
at the time of this audit. So these are not fabricated: they are **figures from a seat whose branch has not been
pushed**, and they are unsourceable for a mechanical reason rather than a provenance one.

**On `14/13`, a correction to something I nearly wrote.** I first described the `11` in that ladder as sourced. **It
is not:** the whole sequence `14/13/11 at MPV 1/2/6` appears in no branch and not in the tally. What *is* sourced is a
**different** ladder measuring the same phenomenon — the clean Hash-16 control `MPV 1/2/3/4 → 16/15/13/11` — and the
coincidence of a `13` and an `11` in both is exactly the kind of match that makes a presence check look like a
provenance check. **The claim "depth falls as MultiPV rises" is independently supported by that sourced ladder; the
specific `14/13/11` triple is not.**

**What that means for you, and it is not nothing.** The four are consistent with their surrounding text and the rest
of the same paragraph's figures (`1/48`, `22/48`, `5/48`, `3/48`, the 1.30/1.35/1.37/1.55× quartet) **are** sourced —
so the block was derived from real measurements. **But a reader of the report cannot check these four, and this audit
cannot vouch for them.** The recommendation in §1.7 is unaffected in substance — it rests on the `Hmax` table, which
is sourced — **and it should be re-checked when `swarm-64` lands.**

### The naive pass, published beside the result

A literal substring pass — no normalisation — flags **38 of the 252**. **34 are accounted for by formatting; 4 are the
unsourced figures above:**

| category | count | example | why the literal pass missed it |
|---|---|---|---|
| spacing before `%` | 30 | `50.6%` | branches write `50.6 %` |
| thousands separators | 4 | `979,723`, `353,312`, `2,893,009`, `1,237` | branches write `979723` |
| **unsourced** | **4** | `52,472` | see above — `swarm-64` not pushed |

**Publishing the naive count is what makes any of this mean anything.** A clean zero from a single pass is
indistinguishable from a pass that could not have found anything — *every absence looks like success*. The number that
carries weight is **"38 candidates examined, 34 explained, 4 traced to an unpushed branch"** — and the four are
reported as unsourced rather than absorbed into a formatting bucket, which is exactly the distinction this section
exists to make.

**The counts moved four times while I worked, and every move is stated rather than smoothed:**

| pass | tokens | naive misses | unsourced | what changed |
|---|---|---|---|---|
| first | 226 | 52 | 0 | report as it stood at the start |
| after the three-population table | 228 | 34 | 0 | 2 were **derived** values (`0.067`, `0.672`) the report had introduced |
| after §9b + the v3 patch | 231 | 32 | 0 | **the derived category emptied** — the owning seat recorded the arithmetic on the branch |
| **current** | **252** | **38** | **4** | the rewritten opening-book section and the MultiPV/Hash boundary work |

**Two of those moves are worth naming.** The third is the good kind: the two derived values stopped being
derived-in-the-report because **`swarm-27` now carries `1344/20000=0.0672, 1344/2000=0.6720` in its own notes.** That
category emptied not because I reclassified it but because **the source caught up** — which is the outcome to prefer,
since **a figure that needs the summariser to vouch for its arithmetic is a figure the owning seat should be
carrying.**

**The fourth is the bad kind, and it is the first non-zero result this summary has produced.** It is not a
regression in the report; it is **work that has not been pushed yet** (§5's table). The distinction matters for how you
read the number: **four unsourceable figures is a publishing gap, not four fabrications.**

**The limit of the check, stated because the run itself states it:** this proves **presence**, not **pairing**. "The
audit checks that SOME path resolves, not that the path supports the claim." A figure can appear in a branch and still
be attached to the wrong quantity here — and **a presence check reported the document clean while §6.1's mis-pairing
was live.** That is the sharpest thing this audit demonstrates about itself.

---

## 6. Sourced but mis-paired — and its current status

Not "unsourced", but **the same defect class the report polices in others**, so it belongs in front of you. **Two of
these four were fixed upstream after I reported them; the section records both the finding and its disposition**, so
that neither the defect nor the fix is invisible.

### 6.1 The `softnodes` low bound was spliced from a different measurement — **FIXED upstream**

As I found it, the consolidated report gave the 80-cell sweep's span as **`0.07×` to 3.50×**. The branch that ran it
(`swarm-27` S-C96) reports the 80-cell sweep as **`1.008×` to `3.503×`**. **The `0.07×` cannot come from that sweep:**
its budgets are 500 and 2,000, and a floor of 1,344 nodes against a 2,000 budget is `0.672`, not `0.067`. `0.07` is
`1,344 / 20,000`, from the separate floor probe at budgets 200…100,000 (S-C99). A later row (S-C100) spliced the two
into one sentence — "spans 0.07x to 3.50x across 40 positions x 2 budgets" — and the consolidated report inherited it.

**Fixed in two places.** In the **report**, as a three-population table rather than a silent correction, stating
explicitly that a sentence spanning "0.07× to 3.50×" splices two populations — *which is how a range that sounds like
one measurement comes from three.* And **on the branch**, where `swarm-27` now records the arithmetic itself
(`1344/20000=0.0672, 1344/2000=0.6720`) and states that the floor probe is a separate measurement on a different
board at a different budget, with that cell's ratio depending on the budget it is compared against.

**The branch fix is the one that matters more.** A table in the report tells a reader how to read the range; a note on
the branch means the **next** summariser does not have to derive it. **That is why §5's derived-value category is now
empty** — not because I reclassified it, but because the source caught up.

**This document used the wording supplied by the seat that measured both directions** — *"0.07x to 3.50x across the
populations measured"* — which does not claim one population for two bounds. **If you re-derive the range yourself,
keep the three apart:** floor probe (200…100,000), 40×2 sweep (500/2,000), 60-position scope run (2,000).

### 6.2 A "3 of 5" reads as a correction but states a different quantity — **not an error; a readability hazard**

`swarm-27` S-C95 and the tally say: *"it is 3 of 5, NOT absolute."* On first read that looks like a duplicate count of
3 of 5, which would contradict the table beneath it. **It does not.** "3 of 5" counts the rows that **carry no
signature**; the table records **2 of 5 exact duplicates** (K+R v K, middlegame B) and 3 of 5 differing in score. The
40 % / 60 % split follows from 2 of 5 and is correct.

**Recorded as an ambiguity, not an error:** a correction whose number counts the complement of the thing being
corrected reads as its own contradiction. Anyone quoting "3 of 5" for duplicates — including me, on a first pass —
gets the sign backwards. **The figures this document uses are 2 of 5 duplicate / 40 % caught / 60 % missed.**

### 6.3 The stale absolutes — **one FIXED upstream, one being fixed by the owning seat**

- **`internal/swarm/tally.md`, S-C87 bullet — FIXED.** It asserted "…confirm **there is no duplicate signature at
  all**", four lines below the S-C95 correction that contradicts it. It now reads *"superseded by S-C95 (2 of 5
  duplicate, 3 of 5 do not), so do not quote 'no duplicate signature at all' from this bullet."* **The superseded
  sentence is retained as a quotation with an instruction not to use it** — which is the right form, because deleting
  it would have left later readers unable to recognise a claim they had already seen.
- **`swarm-27`'s `FINDINGS.md`, row S-C88 — DEFERRED to the owning seat at the coordinator's direction, not left
  unowned.** It asserts "**A fresh session with no previous position gives NO diagnostic at all** — it silently
  searches startpos, so the first position in a run is the one failure undetectable from the reply." **Two separate
  measurements refute it:**
  - **The diagnostic is always emitted; only its location moves** (§1.4).
  - **There are two fallbacks, not one** — startpos with no predecessor, the predecessor's board with one. So even
    S-C88's own description of the fallback is half right: "it silently searches startpos" is true only of the
    no-predecessor cells. **The accurate description is "the last valid board".**
  - **`S-C93` on the same branch proves the other half** — that without `isready` the diagnostic lands in the `go`
    output, before the first `info depth` — with a non-vacuous control (it drives the engine by hand and fails against
    a fake engine that omits the line). **That is what makes S-C88's absolute untenable:** the two rows cannot both
    hold, and the newer one is the measured one.
  - **No branch row records either correction.** I searched all 25 branches' markdown (plus `swarm-75`, read this pass)
    for "four combinations", "four-cell", "last valid board" and the always-emitted wording: **the only hits for "last
    valid board" were unrelated audits in seats 08 and 29.** **The coordinator's explanation is that both corrections
    post-date the branch rows**, and the owning seats are being asked to record them.

**I edited neither file.** The tally is the coordinator's; `S-C88` lives in an active seat's branch. **The owner-facing
consequence while the deferral stands: the withdrawn claim is what a reader of the branch history meets first, so
until S-C88 is amended the corrected version lives only in the consolidated report.**

### 6.4 A verification claim in the tally is wider than what was run

`tally.md` records that `frontpage_check.py` now validates three leading claims (PASS, PASS, PASS) and that
`final_recheck.py`'s "11 of 11 agreeing" is "a sentence no code produced" until it was given a failing exit path.
**Both statements are about scripts that were fixed after failing to exit non-zero.** The fixes are described and
re-proved; **I did not re-run either script**, and this summary does not rely on their output. Flagged so you know the
claim's status is "fixed and described", not "independently re-verified in this assembly."

---

## 7. What the book gets right — the soundness result

Recorded in the closing section rather than the recommendations, because **it is a clean bill and the defects around
it (§1.20, §2.8) are about signalling rather than about the moves.**

**No book move is illegal, and none loses material.** Measured against independent generators:

| check | result |
|---|---|
| book moves legal, against python-chess | **2520 / 2520** |
| polyglot keys match `chess.polyglot` | **2429 / 2429** |
| book keys reached by the walk | **2230 / 2230** |
| material-loss flags surviving engine verification at depth 12 | **0 / 135** |
| exhaustive gap sweep, depth 10 | **max gap 103 cp**, 1/2520 above 100, **0/2520 above 150** |

**The material-loss check is the one worth reading twice, because its first version was wrong and said so loudly.**
The seat's own SEE implementation tested capture legality **against the wrong side**, and **silently reported 929 of
2520 moves as "loses material"** — a false-positive rate of 37 %. It was caught by a hand-computed self-test, not by
review. **So "0 of 135 survive verification" is a claim about a checker that was itself falsified once first** — which
is what makes it worth more than a clean number from an unchecked tool.

**What this does and does not mean.** The book's *contents* are sound: the moves are legal and material-safe. **It says
nothing about whether the book is a good book** — soundness is not move quality, and no move-quality measurement of
the book was made. **And it does not touch the signalling defects:** a sound book move in a drawn position is still a
reply that tells a caller nothing about the draw (§2.8).

---

## 8. How this document was assembled

- **Read in full:** `docs/forge-findings.md` (1,429 lines, re-read after each of your revisions) and
  `internal/swarm/tally.md` (637 lines).
- **Read:** the `FINDINGS.md` of all **26** branches that carry one, plus every other `.md` under
  `forge-combo29/swarm/NN/` for the 26 seats where a figure needed a home — 8.5 MB of branch markdown in total.
- **Branches with no `FINDINGS.md`, not counted as read:** `swarm-09, 14, 18, 22, 26, 31, 33, 34, 37–42, 47, 48,
  51–53, 55–58, 60–62, 65, 69`, plus the non-`swarm-NN` branches. **`swarm-64` does not exist on the remote at all**
  — which is the mechanical reason for §5's four unsourced figures.
- **`git fetch --all` was run four times.** Several corrections landed on `swarm-27` and `swarm-08` *after* the
  preceding fetch — the softnodes scope run (`S-C101`/`S-C102`), the v3 pair-count patch result, and the arithmetic
  note that emptied §5's derived-value category. **A summary assembled from a live swarm is a snapshot; every figure
  here was re-read after the last fetch that touched its branch.**
- **Nothing was run.** No engine invocation, no script execution, no re-measurement. Where a figure is quoted, it is
  quoted from a branch or the tally, with that source's conditions.
- **No other seat's branch was modified.** `swarm-27` `S-C88` is stale (§6.3) and was left alone, at the coordinator's
  direction, for the owning seat to amend.
- **Counts printed as literals, from the artifact:** **26** branches read, **2,302** distinct findings synthesised,
  **4** unsourced figures from **252** numeric tokens, **38** naive-pass candidates (**34** formatting, **4**
  unsourced), **1** real mis-pairing found, **3** sourcing defects of which **2 are now fixed upstream**.

**What I could not source, summarised: 4 figures.**

The number you need for the coordinator's tally:

> **Unsourced figures: 4.**
> Of **252** distinct numeric tokens in the consolidated report, **248 resolve** to branch markdown or to the working
> tally. **Four do not** — `52,472`, `199,619`, `4/48`, `14/13` — and **all four belong to the MultiPV/Hash boundary
> work attributed to `swarm-64`, which is not among the pushed branches.** They are a **publishing gap, not four
> fabrications**: the rest of the same paragraph's figures are sourced, so the block came from real measurement.
> **The naive literal pass flagged 38 of the 252; 34 are formatting, 4 are these** (§5).

**Separately, 3 sourcing defects** — none of them an unsourced figure per the count above, all of them the
mis-pairing class the report polices in others (§6). **Their disposition as it now stands:**
1. **The `softnodes` low bound was spliced across two populations** — `0.07×` is from the 200…100,000 floor probe
   and is not in the 40×2 sweep (which spans `1.008×`–`3.503×`). **FIXED upstream** as a three-population table that
   names the splice as the lesson (§6.1).
2. **`swarm-27` S-C88 still asserts an absolute that the four-combination measurement refutes**, and **no branch row
   carries the four-combination result** — **DEFERRED to the owning seat at the coordinator's direction**, not
   unowned. Until amended, the corrected form lives only in the consolidated report (§6.3).
3. **The tally's `S-C87` bullet asserted "no duplicate signature at all"** four lines below the correction —
   **FIXED upstream**, and retained as an explicit quotation marked *do not quote* (§6.3).

Plus one **readability** defect that is not an error: the tally's "3 of 5" counts the complement, and reads as its own
contradiction (§6.2).
