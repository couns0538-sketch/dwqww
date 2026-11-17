# Owner summary — forge-combo29 C++20 chess engine audit

**Audit window:** 2026-11-16T22:20Z → 2026-11-17T10:20Z.
**Assembled by:** seat `swarm-73`, from committed branch content only. **Nothing here was re-measured.**
**Provenance audited against these branch tips** (`git fetch`, 04:36Z) — **not merely a timestamp, because a figure
from the last few minutes will look unsourced against any fetch.** A provenance count is a statement about these
commits, never about the documents:

| branch | tip | branch | tip | branch | tip |
|---|---|---|---|---|---|
| `swarm-01` | `d65a5b4a6` | `swarm-13` | `bdf138f81` | `swarm-27` | `d5a54c7cd` |
| `swarm-02` | `c210792d6` | `swarm-15` | `943e3674b` | `swarm-28` | `41a28dd01` |
| `swarm-03` | `0c0c5f51f` | `swarm-16` | `38c2b3563` | `swarm-29` | `b7b8270e9` |
| `swarm-04` | `87a058891` | `swarm-17` | `bb0b312ce` | `swarm-30` | `4d8a63fa2` |
| `swarm-05` | `2aa813e74` | `swarm-19` | `f3dc2c059` | `swarm-64` | `6d7488700` |
| `swarm-06` | `28cb02cd0` | `swarm-20` | `0c1d951e4` | `swarm-65` | `03064aae7` |
| `swarm-07` | `a2cf7360e` | `swarm-21` | `528ca6313` | `swarm-66` | `1b275bf2b` |
| `swarm-08` | `cca994f3a` | `swarm-23` | `241d8f0cb` | `swarm-67` | `f0796fb75` |
| `swarm-10` | `68f6f81a0` | `swarm-24` | `45aba7f69` | `swarm-69` | `ffcb95d06` |
| `swarm-11` | `41f2af30b` | `swarm-25` | `2ad1f7072` | `swarm-71` | `1e7ffbd58` |
| `swarm-12` | `d43571175` | | | `swarm-72` | `9f91fe576` |
| | | | | `swarm-74` | `7c0348da2` |
| | | | | `swarm-75` | `858c2496d` |

**Branches read:** **31 that carry a `FINDINGS.md`** — of **63** `swarm-NN` branches on the remote. The other 32 have
no findings file, so their content is cited from `evidence/*.txt`, `STATUS.md` or scripts where used.
**Findings synthesised:** **2,380** = **2,371 distinct table-row ids** + **9 prose findings in `swarm-75`.** There are
**2,392 raw rows**; **21 are re-runs recorded under an existing id**, which is why the row count and the finding count
differ.

**Both totals above were re-derived from the branch files at the tips named here, not carried forward** — the previous
draft said 2,353, and the difference is not an error in either count but five more rounds of swarm output. `swarm-64`,
`swarm-65` and `swarm-74` record findings as **prose sections**, and an **entry count is not a finding count**: those
files contain context sections and summaries too, so only the 9 explicitly-id'd findings in `swarm-75` are counted,
and `swarm-64/65/74` contribute none to this total.

That count is a count of *findings I read*, not a claim that 2,380 separate claims are each correct. The consolidated
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

**The shippability question was "is the repair's per-move scan paid on every search?" It is not, and that is a count
rather than a reading.** *Provenance caveat: the count in the table below is **report-only** — it has no committed
occurrence in any of the 34 branches (§5), while the adversarial-family and depth-contract results around it do.
Re-measuring it on your build is the check that converts it, and it is cheap.*

| question | measurement |
|---|---|
| do ordinary positions enter the scan? | **0 of 125 non-drawn roots** — 5 constructed at 14–48 legal moves, 120 random real positions, **76 of them at 30+ legal moves** |
| do drawn roots enter it? | **13 of 13** — 6 constructed, 7 real KQvK/KRvK endgames at halfmove 100 (mobility 19–31) |
| what does it cost when it runs? | **220–280 ns per legal move = 5–9 µs per drawn root**, against a **20–80 ms** depth-12 search |

**So the shape that would have blocked it — cost on every search for a rarely-firing condition — is not present.** The
scan is paid on drawn roots only, and there it is a rounding error against the search.

**Adversarial families: all seven correct.** The decisive case: halfmove 100 with exactly one mate available →
**base plays `b3b1`, which is not a mate (cp 0, 0 nodes); patched plays `b3a3` with `score mate 1`.** Two-mate roots
likewise (base 0 nodes, patched 192). **Near-misses correctly do NOT cancel** — stalemate-only (the `in_check` test
works), non-mating check, mate-in-2, insufficient material. **And a threefold root that also has a mate is repaired
too**, so the repetition path is covered as well as the fifty-move path.

**Depth contract: 16 observations, no violation.** Base claims **depth 8**, or **depth 64 with 0 nodes** under
`go infinite`/`movetime`/`nodes`; **patched claims depth 1.** Normal searches after a drawn root are **node-identical
(16,646)**.

**Two cosmetic items, neither a blocker:** the patch comment "the adjudication is exactly as before" is slightly too
strong — **with `searchmoves` restricted to a non-mating move on a drawn root, the patched build really searches
(16 nodes, cp 0) where the base adjudicated**, same move and score but different nodes and depth; and
`std::min(1, max_depth)` is inert since `max_depth` is clamped to ≥ 1, so plain `1` would read better.

**The base rate bounds the benefit, and it belongs with the recommendation rather than after it:** **0 drawn roots in
13,707 plies of 60 random games** (random play mates first), but **7 in 1,943 plies of endgames built to reach the
fifty-move rule.** **Rare, and reachable exactly where the rule decides games** — so the fix is worth having and is not
a playing-strength gain you will see in ordinary self-play.

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
| `0000` with `mate 0` | **checkmate** — the game is over, and this is the one `0000` that is a correct answer |
| `0000` with `cp 0` | stalemate, **or** an empty `searchmoves` restriction. **In the stalemate case there is no `info string` at all** — so no diagnostic distinguishes them |
| a legal move, **empty `pv`**, `nodes 0` | adjudicated draw — **do not play the move** |
| zero `info` lines | the search never ran (`go nodes 0/1`, `go` then `quit`) |

**The `0000` advice that is safe to act on, stated precisely so it is not over-applied: treat `0000` as "no move was
played" and consult the score — `mate 0` means checkmate, `cp 0` means a draw or an empty restriction, and the two
`cp 0` cases are indistinguishable from the wire.** A rule of the form "treat `0000` as an error unconditionally" would
also reject the checkmate case, which is a correct answer; **it is the right instruction for a harness that only ever
sends positions with a legal move available, and the wrong one for a GUI.** Both halves matter and they are easy to
compress into a contradiction.

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

**The practical rule is a HASH CEILING KEYED ON LINE COUNT — not a "per-line cap", and not a product.** Do not use
`Hash × MultiPV` as the model, and do not read "per-line cap" into the recommendation: a cap *per line* would scale
the budget with the line count, which is the product form in different words. What is fitted is a **ceiling on Hash
whose value depends on how many lines you asked for.**
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
6 lines.** That is the conservative form of the fit, and it is the one to ship.

**The property to rely on is an INVARIANT, not a count: "the stated ceiling is never more permissive than the fitted
one."** The count of false-safe cells is a snapshot — **a later re-fit invalidates it silently, and nothing tells you
the number moved.** The invariant survives the re-fit, and it is the thing a check can enforce: expand every "N MB at
M lines" clause into an effective per-line ceiling and fail if any stated ceiling exceeds the fitted value. **That
check exists in the report and is proved by planting the permissive version.**

**Why the direction of the error matters.** Both forms misclassify 1 of 48, but a **false-safe** call tells you a
slow configuration is fine — the error that costs you throughput silently. A misclassification in the other direction
merely tells you a safe configuration is risky, which costs caution. **The conservative form is chosen so that the
error, when it comes, is the harmless one.**

**For a technical reader:** the fitted ceiling is `Hmax = {1:256, 2:48, 3:48, 4:24, 5:24, 6:24}` — slightly more
permissive, and it carries **1 false-safe cell of 48 (`Hash 32`, MPV 3, 1.55×)**. **The conservative form differs from
it on exactly 2 of 48 cells**, both at MPV 3 and both straddling the 1.5× line. **Ship the conservative one; the
fitted one is for understanding the boundary, not for setting options.**

**Do not use a "per-line cap" or a product, and do not use a flat Hash ceiling for multiple lines.** A flat ceiling is
the coarse form these measurements refuted: it forbids configurations that are safe (Hash 8 with 6 lines is 1.18×)
while permitting ones that are not (Hash 64 with 2 lines is 1.57×).

**Mechanism, and it is two mechanisms, not one.** Between-line `tt.clear()` plus a second full-size alternate table
(nodes/ms 559 → 183 → 2 at MPV 3 versus a flat ~1,500 at MPV 1). A patch removing the redundant clear **rescues 17 of
22 unsafe cells** (22/48 → 5/48), every one at Hash ≤ 128. **The residual 5 are all Hash 256, MPV 2–6, at 1.90–1.99×
and FLAT in MultiPV** — a per-line cost would keep climbing, so it is not per line. **It is the alternate table's
ALLOCATION**, visible directly in time-to-first-`info`: **1.4 ms at MPV 1 versus 105.9 ms at MPV 2**, Hash 256 — so the
patch is **necessary but not sufficient**, and at Hash 256 the remaining cost is allocation rather than clearing.

**How much of the residual is search? Quote a RATIO, not a subtraction.** Allocation alone predicts **1.72×**
(143.6 + 104 over 143.6); **1.94× is observed**, so **about 0.22× of the total is search.** **That is a bound on a
small residual, not a measurement of it** — and it holds whichever position or sampling convention you use.

**A published figure I do not carry, and the reason is instructive.** An earlier version of that paragraph read
**"135.4 ms = 104.5 allocation + 31 search"**. It overstated the evidence in two unstated ways: **the two terms come
from different samples** (a median over cell medians against one position's time-to-first-`info`), and **the excess is
not position-independent** — per position it ranges **135.0 to 195.6 ms, median 140.5**, which puts the search residual
at **~36 ms, not ~31**. **Both values sit inside the safe region, so nothing downstream changes** — but **"31 ms" reads
as a measurement to three significant figures when it is the difference of two noisy quantities.** §4 has this as a
rule, because the shape recurs.

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
— one board was stable by that rule yet its mate number moved by 3 between depths. **So the move criterion is known
to be incomplete; what to do about it is not established.**

**Select on MOVE change. Do not select on score change, and do not treat score change as harmful either.** The move
signal is overwhelming — **Fisher p < 1e-6**, replicated on a second position set *(the report's exact counts for this
comparison are in `forge-findings.md` §3; I verified the two score-test p-values below independently and could not
locate a committed branch source for the move comparison's counts, so I quote its p-value only)*. **The score signal is
not:**

| comparison | result |
|---|---|
| published, 7/109 vs 21/156 | **Fisher p = 0.0712** — **not significant at 0.05**, overlapping intervals |
| replication, 4/23 vs 7/53 | **p = 0.726, pointing the other way**, but its strata are **4.7× smaller**, so the honest reading is **"this sample could not detect an inversion of that magnitude"**, not "the inversion fails to reproduce" |

**I recomputed both p-values from the counts: 0.07117 and 0.72592. They match the report.** That is the one part of
this claim I can vouch for from first principles, and it is the part that carries the verdict.

**So score change is UNESTABLISHED IN EITHER DIRECTION** — neither a better selector nor a harmful one. **The
mechanism that motivated it is real** (one board kept its move and revised its mate number by 3); **what is missing is
evidence about how it behaves as a selection criterion.** A summary that recommends it is over-reading its own
motivating anecdote.

**What would overturn the throughput claim:** a Hash/MPV cell where MPV > 1 is within 1.2× of MPV 1 at the same
node budget **and** whose `Hash × MPV` product differs from a safe cell's by a constant that separates them — the
first half is what "safe" means, the second is what would rescue the product model. Neither was found in 48 cells.
**What would settle the score-change question:** a comparison on sets of comparable size — the published one is
underpowered at p = 0.0712 and the replication's strata are 4.7× smaller than its own, so **neither settles it.**

### 1.8 If you have any labelled data, check it for `go mate N` rows — **ship** (as a data audit)

**This sits high in the document because it silently corrupts a training set, and it applies to any row the owner
produced with a mate limit.** If none of your data came from `go mate N`, nothing to do — but check rather than assume,
because the label looks clean.

**`go mate N` is NOT a depth cap with a few extras — it is a DIFFERENT SEARCH, and its labels are not comparable with
`go depth` labels.** It **reports** depth `2N−1`, but `mate_moves_ > 0` **switches off seven heuristics plus the TT
cutoff**, so a `go mate N` search and a `go depth 2N−1` search are not the same search at the same depth.

| measurement | result |
|---|---|
| 12 real positions, `go mate N` vs `go depth 2N−1` | **11 of 12 cells differ** |
| one board, `c2c3` at depth 3 | **`go mate 2` gives cp −53, `go depth 3` gives cp +117** — **sign flip at identical reported depth, same move** |
| one board, `go mate 4` vs `go depth 7` | **556,387 vs 3,411 nodes — a 163× ratio at the same reported depth** |

**The owner-facing line: a corpus labelled under `go mate N` is labelled by a mate-hunting search, not by depth
`2N−1`, and mixing those labels with `go depth` labels mixes two incomparable searches. If any of your training data
came from a mate limit, those rows are NOT depth-matched to the rest.**

**And a caller expecting "search until you find a mate in N" gets a truncated search:** `go mate 1` on startpos
returns `d2d4` at depth 1, a non-mate. The reported depths are last-depth **1, 3, 5, 7, 9** for N = 1…5 — exactly
`2N−1` — so the *reported* number is honest about the cap and dishonest about the search.

**What would overturn it:** a board where `go mate N` and `go depth 2N−1` agree in score, move and nodes. Eleven of
twelve cells disagree, one flips sign, and one differs by 163× in nodes.

### 1.9 Discard mate labels whose PV is too short for the score — **ship** (necessary, not sufficient)

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

### 1.10 Self-play variety comes only from openings — **ship**

Ten games from one start produce **one** distinct game, on both builds, at fixed limits. **1,000 openings × 2 colours
= 1,000 independent pairs (2,000 games), not 2,000 samples.**

**What would overturn it:** ≥ 2 distinct games from one start at fixed `Threads 1` limits. None observed on either
build.

### 1.11 Do not spend effort on a v3 micro-patch — **do-not-ship**

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

**If you do touch it, the identity check is seat 08's Step 1b arm** — `swarm/08/v3/profile/openings_baseline.txt`
(200 per-position rows), `go depth 12`, Threads 1, Hash 16, **first 100 of O + first 100 of G**, `OG200.fens`. A
reproduction on a different 200 positions gives `27,762,950` — a 0.65 % gap that is the position set, not a
discrepancy. **A node-sum identity without its position set named cannot be reproduced.**

**But do NOT adopt `27,944,084` as an exact acceptance gate — and this caveat has to travel with the number,
because the report states the requirement without it.** On this branch that figure **is not reproducible for a reason
unrelated to any patch** (`swarm-71`):

| check | result |
|---|---|
| three pinned evals (startpos 968, Italian 1176, rook endgame 31) | **all three reproduce exactly** |
| bench rows using **no** options: no-net bench 11 = `312,866`, test-net-only bench 11 = `965,454` | **both reproduce exactly** |
| bench rows using the **PC20 set**: row 2 gives `242,804` vs pinned `278,024`; row 4 gives `471,702` vs pinned `625,258` | **neither reproduces** |
| the 200-opening sum | **`29,791,805` against `27,944,084` — a 6.6 % gap**, and row 1 is `62,951` where the committed row says `110,540` |

**The cause is that four of PC20's twenty options do not exist on this branch:** `CuckooRep`, `HistRework`,
`TtPruneV2`, `CorrHistV2` are each rejected with `info string unknown option`. **So "PC20's 20 option values" cannot
be applied here — 16 apply and 4 are dropped silently by any harness not checking for `unknown option`.** Setting the
14 that *are* S14 reproduces the documented S14 figures to the digit (`242,796` / `656,517`), which confirms the
options that exist are behaving.

**And the four are not merely unadvertised — they are ABSENT.** Each returns `unknown option`, and **none appears
anywhere in the source** of this branch. That distinction matters for how you read the gap: an option the engine
advertises but ignores is a configuration error you can fix by reading the reply; **an option that does not exist is
behaviour this branch does not have**, so the PC20 configuration is not expressible here at all rather than
misapplied. **It is the concrete reason the figure cannot be reproduced, and it is not a defect in any patch.**

**So the correct gate is an S14-configuration identity, not a PC20 one.** A patch held to "reproduce `27,944,084`
exactly" **will fail for a reason unrelated to the patch** — which is the worst kind of gate, because a false failure
teaches you to ignore the check. **Reproduce the S14 numbers, and treat the PC20 figures as unavailable here.**

**And this is the run's own harness trap landing on its primary identity check:** a `setoption` naming an option the
engine does not advertise is **silently ignored** unless the reply is read. Two seats recorded that trap; the
acceptance criterion for v3 inherited it anyway.

**And this advice has one measured exception, which is worth reading because it shows where the rule does not
apply.** "No v3 micro-patch" is a rule about **shares being too small to justify work**; it is not a claim that no v3
work can pay. **§1.20's pair-count dispatch patch is measurably faster (1.2–1.6 %) and identity-exact** — the win came
**not from the share being large but from the function's work being removable without touching the identity.**
So: **do not chase the percentages, but do check whether a specific piece of per-node work can be eliminated outright.
Those are different questions, and this run answered the second one positively.**

### 1.12 PC20's net speed is a small LOSS on the full population — **do-not-ship** (as a speed win); the components are real

**The headline changed, and this is the version to use: the node saving is real, the per-node tax is real, and on the
full population the tax outweighs the saving — so the best estimate is a small loss.**

| quantity | value | source |
|---|---|---|
| **PC20 node count, population** | **median 0.9618** (−3.8 %) | population run over the game set, 2,643 pairs and climbing |
| **PC20 net wall time, population** | **median 1.0351 — about 3.5 % SLOWER** | same run |
| PC20 per-node cost | **+6.4 %**, pooled ratio **1.0643**; **90.0 %** of positions (163/180 at or above 1.0, one exact tie) | direct, fixed `go nodes`, n=180 |
| *earlier stride sample (116 pairs)* | wall **0.9698**, about 3 % faster | **superseded — the sign flips** |

**The per-node row carries its estimator, because a cold recheck found that an earlier version of it paired two
different ones.** The `+6.4 %` is the **pooled ratio (1.0643)**; the interval `[1.0670, 1.0876]` is a **mean-of-log**
interval **centred on 1.0736** — so **the pooled estimate lay outside its own interval.** Neither bound reproduced
exactly under the other estimator (mean-of-log gives [1.0613, 1.0861]; pooled bootstrap gives [1.0531, 1.0748]).
**The conclusion survives because every construction excludes 1.0** — so this is a pairing fault, not a dead finding —
**but a point estimate and an interval from two different estimators cannot be quoted as one row** (§4 rule 51).

**The identity closes on the population, which is what makes this a measurement rather than two numbers:**
**0.9618 × 1.0709 = 1.0299 against an observed wall median of 1.0353** — a 0.5 % gap. So the loss is **not a
contradiction between two estimates of the same thing; it is the two components composing exactly as the decomposition
predicts.**

**This is consistent with the n=464 arm's "not established" rather than contradicting it.** That arm's interval
included 1.0; the population puts the point estimate on the slower side with the node saving now measured accurately.
**Both readings agree that no speed gain is demonstrated — the population adds that the best estimate is a small
loss.**

**The mechanism, and it is the stronger statement — lead with this.** **Per-node cost is a property of the CODE and is
stable to 0.3 % in every game phase; the node ratio is the SEARCH interacting with the POSITION.** Measured on **six
slices of 4,135 pairs**, which is the resolution needed to separate a small factor from a larger one:

| term | six slice values | spread across the population |
|---|---|---|
| **per-node** | 1.0696 / 1.0719 / 1.0699 / 1.0720 / 1.0690 / 1.0721 | **0.29 %** |
| node | 0.9489 / 0.9618 / 0.9618 / 0.9618 / 0.9588 / 0.9618 | 1.36 % |
| wall | 1.0000 / 1.0476 / 1.0204 / 1.0476 / 1.0238 / 1.0175 | 4.76 % |

**So per-node cost is nearly a CONSTANT of the engine, and the phase dependence lives in the node ratio.** That is why
**three samples across two builds agree at 1.0640, 1.0693 and 1.0709** — **it is the one term that does not depend on
what you sampled**, which is what makes it the trustworthy component and the node ratio the one that needs a large
sample.

**Why the stride sample misled, and it is a general lesson:** the node median is **identical to four decimals across
thirds** (0.9618 in all three) while the wall median drifts. **A 1 % stride sample can land in one phase and report the
wrong sign** — and that drift is **not** the per-node factor, which barely moves. *An earlier reading of this
document said "only the per-node factor moves with game phase"; that is **withdrawn** — thirds were too coarse to
separate a 0.3 % factor from a 1.3 % one, so the answer came out backwards.*

**One caution on the table: individual slice MEDIANS do not multiply through.** Slice 2 gives
**0.9618 × 1.0719 = 1.0310 against a wall median of 1.0476** — because **a median of a product is not the product of
medians.** **The identity closes on the aggregate only**, which is the level at which it was measured.

**And the mean must not carry a claim about this distribution.** On a heavy-tailed distribution
**the mean's error was four times the median's, and it was unstable in both directions** — the population gives node
median 0.9618 but **mean 1.0941**, while the stride sample gave 0.9305. **On a heavy-tailed distribution a claim must
not be carried by its mean** (§4 rule).

**What would overturn it:** a population-scale wall run whose interval excludes 1.0 *on the fast side*. The current
evidence is a 3.5 % loss with the identity closing, so the burden has shifted to anyone claiming a gain.

### 1.13 PC20's "+3 ply at 20,000 nodes" is wrong by 8× per position — **do-not-ship** (that figure, and any match planned on it)

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

### 1.14 Keep or drop `CorrHistV2` — nothing measured changes — **needs-more-evidence** (it is neutral, not beneficial)

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

### 1.15 `searchmoves` — three distinct uses, one of which is sound only under a narrow condition — **ship** (as a harness rule)

25 PC20 positions, depth 10, three arms (free search / all legal moves named / the single bestmove pinned):

| use of a pinned score | verdict |
|---|---|
| recording an **absolute** score | **unusable** — wrong 25/25, \|Δ\| ≥ 10 cp in 14 of 25, range −32 to +31 |
| verifying that a **move** is best | **vacuous** — the restriction makes it the only option (same bestmove 25/25 by construction) |
| **comparing two candidates, both pinned identically, at a gap ≥ 100 cp** | **usable** — 313/317 = **0.987** |
| comparing **three** candidates, both pinned | **not established** — 142/159 = 0.893, CI **0.835–0.932** |
| comparing **five** candidates, both pinned | **not established** — 486/530 = 0.917, CI **0.890–0.938** |
| comparing two candidates at a gap of only **10 cp** | **not established** — 478/511 = 0.935, and the k=2 interval reaches 0.959, so a true 0.95 is **not excluded** |

**A correction to an earlier version of this table, which said "rank order preserved 8 of 8" as a general property.**
**That was a large-gap sample.** Measured properly, **pinning does NOT preserve rank order beyond two candidates** —
both the 3-candidate and 5-candidate intervals **exclude 1.0**, so the effect is real and the direction is worse than
chance.

**The usable rule is therefore narrow and it has two conditions: TWO candidates, both pinned, at a gap of at least
100 cp.** Anything wider — more candidates, or a smaller gap — is not established.

**And there is no "pin just the winner" escape.** One pin alone is already fully distorted: pinning each of the top 5
alone makes the plain bestmove the top-scoring candidate in only **49 of 60**, and in **11 of 60** some other candidate
beats it. So the distortion is not avoided by restricting what you compare to — it is only **cancelled** when both arms
carry the identical pin and the gap is wide.

**`searchmoves <all legal moves>` is not a no-op control.** It changed the reported best move in **6 of 25 at depth
10 and 5 of 15 (33 %) at depth 12** — the effect grows with depth — and two of the depth-10 cases were score-tied and
still picked differently. Its failure is silent: the baseline *looks* like the unrestricted search and is not.

**What would overturn it:** a 3- or 5-candidate arm whose agreement interval includes 1.0, or a two-candidate arm at a
10 cp gap that clears 0.95 with an interval excluding it. Neither was observed.

### 1.16 `softnodes` — a soft budget is bounded by the tree on both ends — **ship** (as a harness rule)

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

### 1.17 Do not compare a hard-budget result with a soft-budget result — **ship**

- `go nodes N` picks the last completed iteration **at or below** N; median spend **74 %** of N.
- `go softnodes N` picks the first iteration **at or above** N; hard cap 4N.
- **A soft budget of N is not N:** identical search at 2000 vs 3000 in **44–47 %** of positions.

**Every per-node figure must divide by the reported count, not the requested budget** — otherwise the request cancels
and you report a time ratio under a per-node label.

**What would overturn it:** a position where `go nodes N` and `go softnodes N` return the same node count and the same
depth. They pick different iterations by construction.

### 1.18 Two evaluation defects: a bare-minor score inversion, and a wrong score in a playable ending — **needs-more-evidence** (both)

**A withdrawn recommendation is corrected here, and the correction is the actionable part.** An earlier version of this
section recommended fixing `is_insufficient_material()` for two knights — **do not do that.** The engine is right and
the recommendation was wrong.

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

**Why both verdicts are needs-more-evidence rather than ship, and the reason is the same for each:** the static
inversion is real and reproducible, but **search adjudicates KB vs K and KN vs K as draws**, so the wrong number never
reaches play there. **A patch to `scale_factor()` therefore changes no game outcome that was measured** — and its blast
radius is every pawnless ending. **Neither defect has a measured game-level cost**, so **neither is worth a surgical
change until someone measures one** — and the KNN case below is the reason "fix the search-reachable one" is not the
right framing either: what reaches search there is a **wrong score**, not a wrong verdict.

**The one that reaches search is a wrong static score in a genuinely playable position — NOT a missed adjudication.**
**An earlier version of this summary said KNN vs K is a draw and the engine was wrong to decline to adjudicate it. That
is withdrawn, and the withdrawal is itself the lesson.**

**Two knights CAN mate.** I verified the witness independently:
`8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1` is **valid, checkmate, and not insufficient material** — `result 1-0`. **FIDE 5.2.2
draws only when neither side can mate by any legal series, and here a legal mate exists**, so the engine's
`knights == 0` requirement (`src/board.cpp:1250-1258`) is **correct**. Nine material sets were decided by **searching
for a mate witness** rather than by argument, and **all nine agree with the engine** — KNN vs KN, KB vs KN and
KNN vs KB included.

**So the sentence to carry is this: the static score for two knights is wrong, and because there is correctly no draw
verdict, that wrong score reaches search unmasked.**

| ending | theory | static | search d6 | adjudicated as draw? |
|---|---|---|---|---|
| K vs K | draw | +2 | **cp 0** | yes |
| KB vs K | draw | −147 | **cp 0** | yes |
| KN vs K | draw | **−104** | **cp 0** | yes |
| **KNN vs K** | **not a draw — it is playable** | **+187** | **cp 251** | **no, correctly** |
| KBN vs K | win | +237 | cp 272 | no |

**Read the two KN rows as different placements, not a contradiction — and note that the source does not say so.**
The first table's KN is on `b1` (FEN given, **−144**); this table's is **−104** and **names no square**. That is a
**−40 cp spread from the knight's square alone**, a small instance of the same bare-minor instability the bishop sweep
shows.

**What the defect is not, and why the distinction matters for what you fix.** It is **not** that the engine fails to
declare a draw — declaring one would be wrong, and the `knights == 0` test is right. It is that **a playable position
carries a static score 187 cp from the truth (cp 251 in a depth-6 search)**, so the engine will steer toward a
dead-drawn ending believing it is winning. **`DeadMaterial` does not cover it**, so enabling that option does not fix
it. **KBN vs K is the control that shows the tests can tell the two apart:** a real win, +237 static / cp 272 at depth
6.

**What would overturn the re-scoping:** a legal series of moves in which Black mates — there is none, because the
witness above is already mate. **What would turn the score item into a ship:** a game-level measurement showing the
187 cp error changes move choice or result often enough to matter. **None was run** (§3).

### 1.19 A warm transposition table changes fixed-depth scores — **ship** (as a harness rule)

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

### 1.20 Time the v3 pair-count dispatch patch on your own build — **needs-more-evidence**

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

**Note the build: this is file 5's tree — `6b98f217` + `pc_r15.patch` — where all twenty PC20 options DO exist.**
That is why the PC20 rows and the `27,944,084` sum reproduce here and not on `combo29` (§1.11). **The two statements
are consistent, and the difference is exactly the four missing options** — so this table is the positive control for
§1.11's caveat rather than a contradiction of it.

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

### 1.21 A second v3 patch was REJECTED with numbers — and the reason is a transferable distinction — **do-not-ship**

**Recorded because a rejection with numbers is worth as much as a ship, and because it corrects a category the shipped
patch could easily have created.**

A second v3 patch removed a 32-lane store-and-scalar-sum tail (`output_sum_avx512`, a **7.34 % profile share**):

| check | result |
|---|---|
| bit-identical? | **yes** |
| speed | ratio **0.9995, CI [0.9984, 1.0005] — includes 1.0** |
| against the pre-registered bar | **+0.05 %, under the 0.5 % bar → REJECTED with numbers** |

**The cost estimate behind it was wrong by an order of magnitude, for an instructive reason:** 82 M adds were costed
at 0.3 ns each — **3.3 adds/ns, which corresponds to no real machine limit.** Because the 32 lanes are
**independent**, the ceiling is **ALU port throughput (~4 adds/cycle)**, giving **0.26–0.40 %**, not 1.2 %. **Measured
0.05 % — below even that ceiling, because the tail overlaps surrounding work.**

**So "removable per-lane work" is NOT one category, and this is the sentence to keep:** a per-lane **BRANCH** with
misprediction and dispatch overhead — which is what the shipped patch removes, dispatching once on the count 1..4 — is
worth **orders of magnitude more** than a per-lane **ADD** on independent lanes, which is a few cycles of a 4-wide
port. **The shipped patch's success (§1.20) does not generalise to "remove per-lane work"; it generalises to "remove
per-lane CONTROL flow."**

**And the first attempt at that rejected patch was NOT bit-identical** — bench `965,454` → `201,580` — because a
`_mm512_shuffle_i32x4` fold selected the wrong 128-bit quarters. **It compiled clean, ran the full bench and returned
a plausible number; only the identity gate caught it.** A timing run alone would have reported **a speedup for a
different engine** — which is the strongest argument in this document for running identity before timing.

**What would overturn the rejection:** a timing on your build where the CI excludes 1.0 and clears 0.5 %. The measured
headroom is 0.26–0.40 % even under ideal assumptions, so this is unlikely to be worth the attempt.

### 1.22 Opening book: apply the one-hunk `!root_drawn` patch, and set `OwnBook false` only when it can fire — **ship**

The book's own soundness is clean (§7); **what it does to a harness and to a caller is three separate hazards.**
**All three were re-verified on the base commit `6b98f217` with the pin checked (bench 11 = 312,866) on the same
binary** — the seat that first found them had built from a disjoint branch, so these are base-verified rather than one
seat's measurement on a different engine.

**1. The condition is narrower than "the clock form": it fires on the SIDE-TO-MOVE'S OWN clock, or on `movetime`.**
The gate is `time_ms >= 0 || movetime_ms >= 0` (`uci.cpp:371`), and `time_ms` is set **only for the side to move**
(`uci.cpp:108-109`). Measured on the base build:

| command | side to move | result |
|---|---|---|
| `go btime 10000` | White | **no book — no bestmove within the window** |
| `go wtime 10000` | White | **books `c2c4`** |
| `go movetime 100` | either | **books `e2e4`** |
| `go depth N` / `go nodes N` / `go infinite` | either | **never** |

**So `OwnBook false` is needed only when the moving side's clock is sent** — sending the *opponent's* clock is safe
from the book and unsafe in a different way (§2.7: a one-sided clock is no clock at all).

**2. The book pre-empts drawn-root detection — and this is now a MEASURED FIX, not a diagnosis.** A halfmove-100
startpos with `OwnBook true` emits `info string book move c2c4` and `bestmove c2c4` **with no `info depth` line at
all**; **the same position with `OwnBook false` gives `cp 0 / nodes 0 / bestmove a2a3`** — the bail's signature. **So
the book decides before any draw adjudication runs**, and a drawn position ships a book move with **none of the
warnings a caller uses to detect a drawn root.**

**The patch is one hunk and it is a PREDICATE, not a reordering: add `!root_drawn` to the book condition, using the
same three tests as the bail** (repetition, halfmove ≥ 100, insufficient material). **Because it only gates the book,
`search.cpp` is untouched and node counts cannot move** — which is why the pin check is a real test rather than a
formality: **all 11 documented pins reproduce on both builds** — **five depths × two net settings, plus perft 5** (a
different and larger set than the **four honesty pins** cited elsewhere in this document; both are pinned, and the
patch moves neither).

| root | lock | patched |
|---|---|---|
| fifty-move **with** a book entry | book move | **bail, cp 0, empty pv — FIXED** |
| repetition **with** a book entry | book move | **bail — FIXED** |
| insufficient material | bail | unchanged |
| fifty-move **with no** entry | bail | unchanged |
| ordinary book position | books | **still books** |
| opening with no entry | searches | **still searches, cp 91** |

**Pre-emption goes from 2 to 0.** **The two controls are what make it a fix rather than a removal:** a patch that
simply disabled the book **would pass the first four rows and fail the fifth**, so the test can tell a fix from a
lobotomy. **Traps 1 and 3 are unchanged on the patched build** — checked rather than assumed.
- **But bare kings already escaped pre-emption, because it has no book entry** — with `OwnBook true` it still returns
  the `cp 0 / nodes 0` bail with `bestmove e3d2`. **So the pre-emption needs the position to be in the book, and the
  dangerous case is a drawn position the book happens to cover** — not drawn positions generally. That is the accurate
  and much narrower exposure.

**Two decisions are yours, and they are policy rather than measurement:**
1. **Should a drawn root EVER book?** A repetition at move 8 in a forced-draw line is arguably a book situation, so
   "always report drawn instead" is **a choice**, not a correction. The patch assumes report-drawn is right.
2. **Should the predicate be shared with `search.cpp`?** **The same three conditions now exist in two copies that
   agree today with nothing enforcing it** — so they can silently diverge on the next edit to either. Sharing it is
   the maintenance answer; duplicating it is the lower-risk-now answer.

**3. `Book Depth` is derived from the FEN's FULLMOVE COUNTER, not from the move count** (`game_ply()`,
`uci.cpp:127-129`) — **and it is not merely a books-or-searches switch.** Sweeping the counter on an identical board:
fullmove **1, 5 and 10 book `e2e4`**, **15 books `c2c4`**, and **20 and 21 do not book at all.** **So the counter
selects WHICH book move is played at intermediate values.** The sharper consequence: **the same position played at two
counters gets two different opening moves**, and at a high counter the book is off entirely — a tool that writes a FEN
without the true move number changes both. **This is the identity trap of §4 rule 44 in a place you would not look for
it.**

**What the book path emits: exactly two lines and nothing else** (`uci.cpp:385-387`) — `info string book move <uci>`
then `bestmove <uci>`. **No `info depth`, no score, no node count.** A GUI showing a score for that move is showing
its own default.

**And the latency gap is orders of magnitude, which is why this bites harnesses.** The committed evidence
(`swarm-65/evidence/cost_deadlock.txt`, `go_matrix.txt`, build `/tmp/build65/forge`) gives single-shot wall times:

| arm | command | wall ms | `info depth` lines |
|---|---|---|---|
| **BOOK** | `go wtime 10000 btime 10000 winc 100 binc 100` | **0.2** | **0** |
| **BOOK** | `go movetime 100` | **0.1** | **0** |
| NOBOOK | `go wtime 10000 btime 10000 winc 100 binc 100` | **346.2** | 19 |
| NOBOOK | `go movetime 100` | **91.0** | 15 |

**A reader waiting for an `info depth` line times out on every book move**, proved with a passing off-book control.

**One figure in the consolidated report I could not source, and it is in this sentence.** The report states book
**p50 0.024 ms / max 0.44 ms over 200 round trips** and off-book **p50 442 ms**. **`swarm-65` ships the script that
would produce those percentiles (`scripts/q2b_latency.py`, which does exactly the 200-round-trip measurement) but
commits no latency output file** — I checked all 36 files in the seat, and no branch anywhere contains `p50` in prose.
The single-shot times above are what the committed evidence actually shows. **They support the same conclusion — the
gap is four orders of magnitude and the reader hazard is real — but they are not the p50 figures**, so I quote the
committed ones and flag the others (§5).

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

**The trigger is THREE occurrences, not two — and an ordinary twofold is harmless.** At exactly **2** prior
occurrences both builds agree with the FEN form; at **3** they diverge. So a twofold repetition in a move list — the
common case in any real game — does not expose you. **This matters because "repetition" sounds like one condition and
is two.**

**And the exposure is MIDDLEGAMES, not endgames — which corrects the impression every earlier fixture gave.** A real
opening (`e2e4…e8g8`) plus a legal knight-and-queen cycle, **32 pieces still on the board at 24 plies**: the base
answers **`0 nodes`, `cp 0`, `a2a3`** at `go depth 8`, `12`, `14` **and at `go nodes 50000` and `500000`**. **The same
board as a bare FEN answers `b3e6` / cp 32 on both builds, and the repaired build answers `b3e6` from the move list
too.** So **the base is 32 cp out and playing the wrong move in a position nobody would call an endgame** —
deterministic, 1 distinct result across 3 runs per build.** **Every earlier fixture in this report was sparse, which
is exactly why the endgame impression formed.**

**Who is actually exposed — and it is narrower than "any harness", so say it precisely.** **0 threefolds in 600 random
games** (60/120/200 plies) **and 0 in 4,000 further 160-ply seeds.** So:
- **A harness sampling random positions is essentially never affected.** This is not a general hazard.
- **A harness REPLAYING REAL GAMES to a threefold IS affected**, and gets **a silently wrong move with no error.**
  That is the exposure: game replay, silent when it hits.
- **The self-play figure is not in tension with the 0-in-600 and the two must be read apart:** **8 of 10** clock
  self-play games reached a genuine threefold **over up to 250 plies with ten distinct openings** — self-play seeks
  draws where random play mates first. **Different populations, different rates: "common among long engine games,
  essentially never among random ones."**

**And the defect is DETECTABLE rather than merely discoverable — this is the check to use.** The bail's signature is
**64 `info` lines all scoring `cp 0` with `nodes 0` and an empty `pv`, climbing to depth 64.** A real search emits
**about 11 lines with populated nodes and a `pv`.** **So `nodes 0` plus an empty `pv` means discard the cell** — no
need to reason about repetition counts at all.

**The cost is in the MOVE, and it is a forfeited mate, not just material.** On a genuine threefold root where the side
to move has mate in one, the base reports `cp 0`, searches nothing and plays `f2f3` — **forfeiting the mate** — while
PC r15 reports `mate 1` and mates. Verified as one chain on **6 of 6** boards: `go perft 1` on the searched position
names the first generated move, and the bail returns **exactly that move** (`f2f3` on all six), while the mates being
ignored were `b1b8`, `a1a8`, `c1c8`, `e1e8`. **The forfeit is the mechanism doing exactly what it says.**

**Provenance caveat on every PC r15 column in this document, and it is a gap rather than a doubt.** The PC r15 numbers
— `cp 425`, `mate 1`, `mate 8`, `mate 9` and the mate-in-one fix — **trace to a handoff document, not to a
reproducible artifact.** The flag that disarms the guard, **`FORGE_FIX_ROOT_DRAWN`, is not committed as source in any
branch** — I verified this across **all 63 `swarm-NN` branches** (of 94 `for-fable-and-opus` and 609 remote branches in
total): it appears **only in prose, findings documents and check scripts**, and **never in a `src/` or `include/`
path**.
- **This is not evidence the numbers are wrong.** They are **mutually consistent**, and `swarm/23` records the patch's
  sha256 prefix.
- **But the repair cannot be independently rebuilt from the record** — and that is exactly what the shipped patches
  close: seat 12's and seat 27's patches **are committed as text**, compose to a byte-identical file, and have a
  measured ship verdict (§1.2). **So apply those; do not try to re-derive r15.**
- **A trap that looks like it would let you rebuild it:** **`-DFORGE_MATE_ALPHA_GUARD=1` is NOT the repair.** A build
  with only that flag is **byte-identical to a control and still bails on a threefold root.** The flag gates
  `MateAlphaGuard`, a search-pruning switch (`search.hpp:310`), which is a different mechanism entirely.

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

**The self-play rate, with its interval, because the point estimate over-claims:** **8 of 10** clock self-play games
reached a genuine third occurrence, but the 95 % Wilson interval is **49 % to 94 %** — so quote the interval. The
frequency is **"common", not "four in five"**, and it is a **self-play** rate over up to 250 plies, not a rate you
should project onto any other population (§ above, where random play gives 0 in 600).

**And a counterweight that bounds who is exposed, which belongs with the forfeit rather than after it:** **an organised
match never plays the move**, because the match program ends the game at the third occurrence. **So the exposure is not
match play — it is tooling:** analysis front ends and game-replay harnesses that ask the engine about a position and
use what comes back. **Quoting the mate-in-one forfeit without this reads as a playing-strength defect, which it is
not** — and the honest version is narrower and more actionable: **a silent wrong move in a replay pipeline.**

### 2.1b A waivable draw claim suppresses a deliverable mate — **broken, and this one IS a strength loss**

**A separate defect from §2.1, and the more serious of the two**, because it costs a win the engine already has rather
than an answer about a position it did not search. **The threshold is right; the consequence is wrong.**

**FIDE 9.2 (threefold) and 9.3 (fifty moves) are CLAIMS belonging to the player to move**, and **5.1.1 ends the game the
moment a mate is delivered.** A player who can mate declines the claim and mates. **The engine instead returns 0 before
generating a single move, so it cannot see the mate at all** (`swarm-72`):

| position | halfmove | mate available | engine score | engine move |
|---|---|---|---|---|
| `7k/8/6K1/8/8/8/8/R7 w - - 0 60` | 0 | `a1a8` | `mate 1` | **`a1a8`** |
| same | 98 | `a1a8` | `mate 1` | **`a1a8`** |
| same | 99 | `a1a8` | `mate 1` | **`a1a8`** |
| same | **100** | `a1a8` | **`cp 0`** | **`a1a2`** |
| same | 101 | `a1a8` | **`cp 0`** | **`a1a2`** |
| same | 149 | `a1a8` | **`cp 0`** | **`a1a2`** |
| **threefold root** (`a1a8` available) | 8 | `a1a8` | **`cp 0`** | **`a1a2`** |

**The break lands exactly at the documented 99 → 100 boundary**, which is what shows the trigger is right and only the
consequence is wrong. **And it is not confined to the fifty-move rule**: a threefold root with the mate available does
the same thing, so **both claim types suppress it**.

**Independent confirmation that these are claims and not terminal states** — python-chess:
`Board('7k/8/6K1/8/8/8/8/R7 w - - 0 1').outcome()` → `None`; the same at halfmove 100 → `None`, while
**`can_claim_fifty_moves()` → `True`.** So the position is **not over**, and an engine returning `cp 0` is reporting a
result that has not happened.

**A correct engine may still treat a repetition it can force as a draw when it is the weaker side**, and may treat a
fifty-move position as a draw when no progress is possible — **but it must not do so when a mate is deliverable.** The
minimal fix is at the root only: **do not return 0 at `ply == 0` before generating moves, or check for an immediate
mate first.**

**Impact: in any won position that reaches halfmove 100 or a threefold, the engine stops converting and starts
shuffling.** That is a genuine strength loss, not a bookkeeping nit — and it is the opposite classification from §2.1,
where the match counterweight bounds the damage. **Here there is no counterweight: a won game is thrown away.**

**What would overturn it:** an engine score of `mate 1` and a mating move at halfmove 100 in the table above. It
returns `cp 0` and `a1a2`.

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
info lines, 0 nodes, `bestmove 0000`, **and nothing else on the wire**. **A diagnostic therefore cannot be relied
on** — the `info string` that accompanies the illegal-restriction case is absent here.

**So the instruction is "`0000` means no move was played — branch on the score", with one exception that matters:**
**`0000` with `mate 0` is checkmate and is a correct answer.** A front end that treats every `0000` as an error will
reject a legitimate checkmate; one that treats every `0000` as a move will play a null against a stalemate. **Neither
blanket rule is right, and the distinguishing field is the score.** The safe form for a harness that only sends
positions with a legal move available is to fail on any `0000`; a GUI needs the `mate 0` branch.

### 2.5 Mate scores that are wrong at the depth reported — **broken**

- `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`, depth 12, S14, base: reports **`mate −12`** (a promise of mate in 24 plies)
  with an **18-ply PV that does not end in checkmate**. Plain minimax proves White is mated in exactly **4** moves
  (and not 3). The engine's own depth-22+ answer is correctly `mate −4`. **The depth-12 score is wrong by 8 moves.**
  - PC r15: no options `mate −7` (14/14 plies, consistent); S14 `mate −9` (14 of 18 plies, **inconsistent**).
- A separate class at the right PV length, §1.9: two boards, opposite directions.

### 2.6 Multi-threaded scores are not reproducible — **broken for any consumer of the score**

§1.5. `Threads 4` gave **four distinct evaluations in four runs** on PC r15 under PC20 (+2576 cp, mate 13, mate 18,
mate 16) with node counts spanning 5.0 M to 31.4 M. The move was stable; **the score is what a search hands to the
clock, the book, and any game-vs-game comparison.**

### 2.7 A partial clock is an unbounded search with no diagnostic — **broken (silent)**

`go wtime` on a black-to-move board, or `go btime` on a white-to-move board, searches **indefinitely** and emits **no
`info string`**: the GUI sees a hang, not an error. Confirmed on both builds with controls; the both-clocks control
answers in 0.16 s. **Padding the opponent's value does not help** — a large opponent clock has zero effect. The
engine is right to ignore the opponent's clock; it should print an `info string` instead of searching forever.

**Status: a patch is being prepared with the same gate as §2.8's book fix** — so this is likely to move from "broken"
to "fixed" after this document closes. **Treat it as pending rather than settled**, and the check when it lands is the
same one: the both-clocks control must still answer, and a one-sided clock must produce the diagnostic rather than a
hang.

### 2.8 The opening book overrides draw adjudication — **broken, and the FIX IS MEASURED**

**All three claims below were re-verified on the base commit `6b98f217` with the pin checked (bench 11 = 312,866) on
the same binary** — the seat that first found them had built from a disjoint branch, so these are base-verified rather
than one seat's measurement.

Two consumers are affected and neither gets a warning:

- **A drawn position gets a book move, and the contrast is exact.** Halfmove-100 startpos with `OwnBook true` emits
  `info string book move c2c4` and `bestmove c2c4` **with no `info depth` line at all**; **the same position with
  `OwnBook false` gives `cp 0 / nodes 0 / bestmove a2a3`** — the bail's signature. **So the book decides before any
  draw adjudication runs**, and a drawn position ships a book move with none of the warnings a caller uses to detect a
  drawn root.
  - **A bare-kings position ESCAPES, and the reason matters:** it is an automatic draw with **no book entry**, so with
    `OwnBook true` it still returns the `cp 0 / nodes 0` bail. **The pre-emption needs the position to be in the book**
    — so **the dangerous case is a drawn position the book happens to cover**, not drawn positions generally.
- **`Book Depth` follows the FEN's fullmove counter** (`game_ply()`, `uci.cpp:127-129`), and the sweep shows it is
  **not merely a books-or-searches switch.** On an identical board: fullmove **1, 5 and 10 book `e2e4`**, **15 books
  `c2c4`**, and **20 and 21 do not book at all** and fall through to a search.
  - **So the counter selects WHICH move is played at intermediate values, not only whether the book fires** — and that
    is the sharper consequence: **the same position played at two counters gets two different opening moves**, and at
    a high enough counter the book is off entirely. A tool that writes a FEN without the true move number changes both.

**Not a correctness defect in the book itself** — its moves are sound (§7). **It is a defect in what the book tells a
caller about the position**, which is the definition §2 uses.

**And it is the one item in this section with a measured fix rather than a recommendation.** The `!root_drawn`
predicate takes pre-emption from **2 roots to 0**, leaves `search.cpp` untouched so node counts cannot move, and
reproduces **all 11 documented pins on both builds** — with two controls that would fail a patch which simply disabled
the book. **So the owner can take this as settled rather than as work to schedule**; the two open questions in §1.22
are **policy choices about what the patch should say**, not about whether it works.

### 2.9 Asking for a neural arch with no usable net hangs the process — **broken**

**Asking for the neural network architecture with no usable net prints an error and then exits — without answering
`isready` and without sending a `bestmove`.** A GUI waiting for readiness **hangs forever**; a harness waiting for
`bestmove` blocks on a read that never completes.

**This is the fifth member of the "well-formed answer to a question that was not asked" family (§7b), and it is the
one that fails loudest in the log and quietest on the wire** — there *is* an error message, and then nothing. **A
reader with a timeout reports a hang; a reader without one never returns.**

**Sourcing status: SOURCED, and my first search for it was wrong.** An earlier version of this section said the defect
came from the consolidated report only and that "I could not find it in any branch's committed markdown". **That was a
search failure on my part, not an unsourced claim** — the finding is in **`swarm-71`'s `STATUS.md`**, not its
`FINDINGS.md`, which is why a findings-file search missed it. **The seat records the exit status (`2`) and the
fail-loud justification** — the engine never falls back to the hand-crafted eval, and the bench proves the net is
genuinely in use (`312,866` → `965,454` nodes) — **so the mechanism is theirs and the behaviour is measured, not
inferred.**

**The mechanism is also the right one in spirit and wrong in its execution:** failing loud beats silently evaluating
with the hand-crafted net, **but it kills the process mid-protocol** rather than reporting a usable error.

**What would overturn it:** a net-less `NNUEArchFile` request that answers `readyok` and then a `bestmove`. The seat's
record shows exit 2 with neither.

### 2.10 What is *not* broken, and was claimed to be

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
- **"A FEN with the wrong number of fields is refused in total silence and searches startpos" — WITHDRAWN, and it was
  measured on the wrong build.** It came from `integrate/combo29-all`, **which does not contain the audit's base commit
  `6b98f217`**, so the binary was a different engine. On the correctly built base, **short FENs are refused with a
  diagnostic and long ones are accepted with the surplus dropped** (§4 rule 11). **"Malformed is silent" is false in
  both directions.** The corrected behaviour is in the rules; the withdrawn form is here so you do not act on it.

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
- **The base-vs-PC lone-king divergence, second mechanism.** The boundary is **confirmed at population scale**:
  `go depth 12`, Threads 1, **0 differing of 200** (set O) and **0 of 341** (set G) on non-lone-king roots — **in node
  counts AND best moves** — with the lone-king control **12 of 12 differing**, reproducing at `go nodes 200000`
  (`swarm-69` 69-F13/F15). Cause isolated at the switch: **`BARE_KING_LMR_CAP` off restores the base move on 11 of
  11**; `BARE_KING_ONE_THREAD` on restores 6 of 11; ordering was hypothesised and killed. Cap-off visits fewer nodes
  on 9 of 11 boards (by 3,356–14,040) and more on 2 (+621, **+10,981**). **But the gate fires on 100 % of nodes in
  every tree**, so it cannot be what distinguishes the two counter-cases. **A second, uncharacterised mechanism
  remains.** The instrument that would find it — a build printing per-depth reduction counts — was never built.
  - **So the population result sharpens what is open.** "The builds diverge only on lone-king roots" is now
    established over 541 non-lone-king positions at two budgets. **What is *not* established is why the cap changes
    the choice on the two counter-cases** — that is a mechanism question inside a characterised class, and it should
    not be read as doubt about the class boundary.

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

**From the evaluation audit (§1.18), stated as the measuring seat states it**
- **The bare-minor material inversion has no measured game-level cost.** The static inversion is real, and the
  **KNN-vs-K case reaches search as a wrong static score in a playable ending** — but **no game-level cost was
  measured: no SPRT, no Elo claim.** **That is why §1.18 holds BOTH items at needs-more-evidence**: there is no
  measurement that would justify preferring one surgical change over the other, and the
  `is_insufficient_material()` change I once recommended has been **withdrawn entirely** — the engine is right about
  that verdict.
- **Evaluation symmetry is now verified on BOTH evaluation paths, and that is stronger than either half alone.**
  - **Built-in net: 0 asymmetric pairs of 420** (20 hand-picked + 400 seeded), `hce` and `nnue` separately, measured on
    the static evaluator so no movegen is involved.
  - **A loaded FORGENN3 net through the v3 path — the path your PC actually runs, and which had never been tested:
    0 asymmetric pairs of 353** (`set_G`, colour flip + board flip with side preserved, 353 pairs evaluated, 0
    skipped), for `hce`, `nnue` **and** total.
  - **Together these are a property of the ENGINE, not of one net.** Symmetry is a property of the **weight layout**
    as much as of the code — `feature_index` reindexes by king bucket and flips squares by perspective — so a net
    written for one convention could be asymmetric where the two kings sit in different buckets. **And startpos cannot
    show it**, since both sides are identical there; the test has to run on real positions.
  - **The equality test is proven able to fail:** two different positions evaluate 968 vs 1320, so **0 of 353 is a
    measurement rather than a broken equality check.**
  - **And this result survives the ep-fen hazard, which is worth checking rather than assuming** — see §4 rule 13.
    The failure mode is that a symmetry test re-emitting `fen()` to build its mirror **loses the ep square on one side
    only**, manufacturing an asymmetry the engine does not have. **Here the fix (reading the ep field from
    `board.ep_square` rather than `fen()`'s decision) was a no-op on the data — 0 of 60 changed** — because the path
    was closed **before** any corpus with ep used it. **So the 0-of-353 stands as measured.**
  - **Still evidence, not proof** over all positions — but it is now evidence on the path that ships, not only on the
    reference one.
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
3. **A build whose PROVENANCE was assumed rather than checked produces a confident wrong measurement — and `BUILD_OK`
   is not evidence that you built the right commit.** This is the highest-severity rule in the list, because it
   invalidates every number downstream while leaving them all looking normal.
   - **The case, measured:** a coordinator measurement of FEN field counts contradicted a seat's. **The cause was that
     the coordinator had built `integrate/combo29-all`, which does not contain the audit's base commit `6b98f217`** —
     so the binary was **a different engine wearing the same name**. The rebuild **verified bench 11 = 312,866 on the
     same binary before recording a single row**, and then agreed with the seat.
   - **The check is one command and it is the same one every harness trap ends at: confirm the artefact is what you
     think it is, before interpreting what it says. A build is an INPUT, not a given.** Verify a pin (a bench value, a
     perft count) **on the same binary** that produces your rows — not on a sibling build.
   - **And the tempting shortcut when two measurements disagree is to prefer the more recent or the more
     authoritative-looking one. Both would have been wrong here** — the seat's version was right, and the
     coordinator's was measured on the wrong commit **with a plausible-looking `BUILD_OK`.** A success message from
     your build system is a claim about the build succeeding, never about *what* it built.
4. **`Hash 16` and `Hash 64` are interchangeable only BELOW about 200,000 nodes — the equivalence is a budget
   condition, not a Hash fact.** Fresh process, `Threads 1`, cells differing between the two sizes:

   | budget | cells differing |
   |---|---|
   | `go nodes 50000` | **0 of 24** |
   | `go nodes 200000` | **2 of 24** |
   | `go nodes 500000` | **17 of 24** |
   | `go nodes 1000000` | **24 of 24** |

   **Of 178 differing cells across the sweep, 15 also changed the best move** (`swarm-69` 69-F11, computed from
   `job4/hash_sensitivity.json`). **So a harness fixing a node budget below ~200k may treat them as equivalent, and
   anything larger may not** — and **a search over a million nodes differs every time.** `Hash 1` differs even at 50k
   (11 of 24), so shrinking Hash to save memory silently changes the measurement.
   - **What I could not verify:** the report also states **40 of 40 at 2,000,000 nodes**. `swarm-69`'s committed
     sweep stops at 1,000,000, and its `40/40` figure is a *different* comparison (warm vs fresh at every Hash size).
     **The 2M row is unsourced here** (§5), and it does not change the recommendation — **1M already differs 24 of 24.**
5. **`ucinewgame` is a TRUE cold reset; `Clear Hash` is NOT.** Measured on 25 cells: **`ucinewgame` 0 of 25 differ**
   from a fresh process, **`Clear Hash` 24 of 25 differ.** The source says why — `ucinewgame` calls
   `Searcher::clear()` (`search.cpp:2679`), wiping histories **and** the table; `Clear Hash` calls `clear_hash()`
   (`:2667`) then `clear_caches()`, which is only `evaluator_.clear()` (`search.hpp:452`). **The same drift reproduces
   on the pattern a real harness uses — walking games: 5 of 6 positions differ, and `ucinewgame` restores 0 of 6.**
   - **And the drift is REPRODUCIBLE: 3 of 3 independent processes replayed identically.** **So a reused process does
     not give you noise — it gives you a stable-looking wrong number you can reproduce indefinitely.** That is worse
     than noise, because noise is visible in a variance report and this is not. (§7c)
6. **A piped harness measures nothing, and it is perfectly reproducible — so it looks like a measurement.**
   `printf '…go depth 8\n' | forge` gives **zero `info depth` lines and a fabricated `bestmove`**, because **EOF
   aborts the search.** (`swarm-69` 69-F1, `fault_proof.py`.) **Do not let EOF reach a running search** — same class
   as a silently refused FEN, and the same fix.
   - **And the fabrication is NOT detectable by its move — this corrects a natural assumption.** Measured: **13
     distinct fabricated moves across 60 positions, ALL 60 LEGAL, and 0 of 60 equal to the real answer.**
     **A legality check accepts 60 of 60.** The fabrication is also **budget-independent** — the same moves for the
     same positions at every depth tried.
     - **Only an `info`-depth line count of zero detects it.** So the detector is not "is the move plausible" but "was
       there a search" — which is why §4's rule to wait for `bestmove` is not sufficient on its own: **a piped run
       delivers `bestmove` and never searched.**
7. **A python-chess validator does not make a harness safe; validation and acceptance are different gates.**
   `4k3/8/8/8/8/8/8/R3K2R w K - 0 0` — **fullmove `0` — is VALID to python-chess and REFUSED by the engine.** A harness
   that treats "python-chess accepts it" as "the engine accepted it" has validated the wrong gate.
   (`swarm-69` 69-F3.) **Check both: the validator, and the engine's own reply.**
8. **A warm transposition table changes fixed-depth scores — use one fresh process per measurement.** The same
   KBN-vs-K board at depth 6 scored **cp 274, 285 and 293** as the first, second and third search in one process,
   against **cp 272 three times** cold. The TT carried from the previous search changes move ordering, which changes
   which reductions fire, so a fixed *nominal* depth is not a fixed *effective* search. **This would manufacture a
   fake depth trend** — and hide a real one — which is why every depth comparison in this report uses a fresh process
   per cell (§1.19). **At every Hash size, 40 of 40 warm-vs-fresh cells differ**, so a larger table does not rescue it.
9. **An unknown `go` token is silently ignored, with nothing printed — so `go` is not a place to set an option.**
    `go depth 16 multipv 3` means **MultiPV 1**, because MultiPV is a `setoption` on this engine and the trailing
    token is discarded. **The report's supporting measurement is that `go depth 10` and
    `go depth 10 nonsense_token 3` give identical depth, nodes and score (10, 9,575, cp 21); I could not find that
    measurement in any branch** — `nonsense_token` appears in none of the 28 — so **treat the specific numbers as
    unverified and the behaviour as reported** (§5).
    - **This caused a real near-miss, and it is the cleanest example of a configuration error that produces clean
      data:** two arms of a replication ran **identical configuration**, so they produced **0 disagreements in all
      three strata** — a perfectly consistent null. **Only a "must be non-zero" sensitivity control caught it.** Without
      that control the result would have been published as "MultiPV never changes the move."
    - **So assert the configuration from the engine's own reply before comparing two arms**, and include at least one
      check whose correct answer is **non-zero**. **A comparison of two identical arms is the one failure a
      consistency check cannot see, because consistency is exactly what it produces.**
10. **Validate every FEN before sending it, and read the reply.** `readyok` is not a statement about the position.
11. **An unparseable `go` VALUE is replaced by a DEFAULT, silently — and the reply is indistinguishable from a correct
   one.** Seven malformed requests — `go depth abc`, `go depth` (no value), `go nodes abc`, `go nodes`,
   `go movetime abc`, `go movetime 0`, `go wtime abc` — **all land on one identical search: depth 5, 1,001 nodes, a
   legal bestmove, nothing on the wire.** **`go depth abc` produces IDENTICAL `info depth` lines to `go depth 5`,
   so a harness cannot recover the difference even in principle.**
   - **This is an IMPROVISATION, not a silence, and the contrast is what makes it a finding.** The `setoption`
     parser **reports every malformed form** — bad value, out of range, missing `value` keyword, unknown name — **and
     keeps the old value.** So the engine already knows how to refuse; **`parse_limits` simply has no else branch.**
     **A refused option preserves intent and shows an error; an improvised limit runs on a number the caller never
     supplied.**
   - **The harm is two experiment arms silently becoming one**, with no error and no after-the-fact detection —
     the same mechanism as `go depth 16 multipv 3` meaning MultiPV 1 (rule 8).
12. **The parser surfaces are NOT uniform — and after the move-list correction the split is three that report
   truthfully and two that improvise silently, with `position fen` doing both depending on the direction of the
   error.** Know which one you are talking to before you trust a refusal:

   | surface | malformed input | what happens | verdict |
   |---|---|---|---|
   | `setoption` | bad value, out of range, no `value`, unknown name | **reports it, keeps the old value** | **truthful** |
   | `position fen` — **too few fields** (5, 4, 3, 2) | short FEN | **reports `invalid FEN: FEN must contain six fields`**, but the previous board is then searched | **truthful, then dangerous** |
   | `position fen` — **too many fields** (7, 8) | surplus tokens | **nothing printed; surplus DROPPED, board loaded — the position you meant** | **silent, harmless** |
   | `position fen` — illegal position | adjacent kings | **reports it**, previous board searched | **truthful, then dangerous** |
   | `position TYPE` | unrecognised keyword | **nothing printed; re-searches the previous board** | **improvises** |
   | `go` limits | unparseable value | **nothing printed; substitutes a default** | **improvises** |
   | **`moves` list** | illegal token | **reports `illegal move …` and truncates at that token** | **truthful — trust it** |
   | **`searchmoves`** — all-illegal or empty | every named move illegal, or none named | **`0000` + `info string` + 0 nodes** | **truthful** |
   | **`searchmoves`** — mixed list | one legal + one illegal move | **byte-identical to pinning the legal move alone; NO diagnostic on either stream** | **improvises — and undetectable after the fact** |

   **The arithmetic, counted from the rows rather than asserted: 9 rows, of which 5 report the fault and 4 do not.**
   **Two surfaces disagree with themselves and each appears once per branch** — `position fen` (short/illegal report,
   surplus is silent) and `searchmoves` (all-illegal reports, mixed is silent) — **which is why the row count exceeds
   the surface count by three.**
   - **A surface whose branches disagree NEEDS one row per branch, and collapsing them under-counts the table.** An
     earlier version of this table had `searchmoves` as a single row carrying only the **mixed** case, which hid that
     the all-illegal branch **does** report — **so the same table both under-counted the truthful side and lost the
     distinction that makes `searchmoves` worth a row at all.**
   - **The `searchmoves` mixed row is the worst of the silent ones**, because it is **byte-identical** to a valid
     command: same bestmove, same score, same node count, nothing on either stream. **So the check has to live in the
     client** — intersect your own token list against the legal move set before sending, because the reply cannot tell
     you.
   - **An earlier version of this paragraph said "three report and two improvise", which double-counted `position fen`
     to reach a total the rows never supported**; the heading before that said "two of five … and one does both", which
     did not add up either. **Both were arithmetic asserted in prose instead of computed from the table.**

   **Field count splits in two directions and the halves must not be merged** — this row was wrong in an earlier
   draft of this document, which is why it is spelled out: **a 5-field FEN is refused loudly and then the previous
   board is searched** (the dangerous half — you get a warning and then an answer about a board you did not send),
   **while an 8-field FEN is honoured** with the surplus dropped (the harmless half — the position you meant). Measured
   on base `6b98f217` with **bench 11 = 312,866 verified on the same binary first.**

   **So validate the field count yourself.** Neither branch of the engine's behaviour protects you: the short case
   warns and proceeds on the wrong board, the long case is silent because it is fine. **Counting the fields is one
   line and it is the only check that covers both.**

   **An unrecognised `position` TYPE re-searches the previous board with nothing on the wire** — the type keyword is
   never validated, so the FEN validator never runs.

   **A corrupted move list TRUNCATES at the bad token, and the warning is real.** `position startpos moves e2e4 zzzz
   e7e5` reports `illegal move zzzz` **and searches the legal prefix before it** — not the intended position, and not a
   splice past the error. **Confirmed at perft 3, where every prefix has a distinct count:**
   **8902 / 13160 / 24825 / 23193 / 24079** (startpos, then after `e2e4`, `e7e5`, `g1f3`, `b8c6`). **An illegal token
   inserted at index 0, 1, 2, 3 or 4 returns exactly the prefix value for that index, five for five.**

   **So the practical consequence REVERSES the earlier advice: the warning is TRUTHFUL, and a harness can trust it.**
   `illegal move zzzz` means *the position is the legal prefix* — **not the intended position, and not a splice.** That
   makes it **a usable signal rather than a hazard**: fail the row, or record the prefix knowingly, but do not treat the
   reply as untrustworthy. **An earlier version of this document called it a hazard and told you to distrust the
   position; that was the splice reading, and it was wrong.**
   - **A SPLICE reading of this was published twice and withdrawn twice, and the reason is a perft-2 collision.**
     `e2e4 e7e5` and `e2e4 e7e5 g1f3 b8c6` **both give perft 2 = 835** — two different boards, one count. **So at
     perft 2 a spliced four-move line and a two-move prefix are indistinguishable**, and the fingerprint confirmed
     whichever hypothesis was already believed. **Perft 3 separates them and reverses the conclusion.**
     - **The general rule: a fingerprint test needs a depth at which the candidate hypotheses make DIFFERENT
       predictions** — otherwise its agreement is evidence for nothing. **Check that the test can distinguish the two
       answers before you run it**, which here meant checking that the five prefixes had five distinct counts.
     - **And a claim that reverses twice deserves a note in the document, not a silent edit.** The version above is the
       third; the reason it took three is that the first two tests could not separate the answers. **A reversal count
       is information about the test, not only about the claim.**

   **And junk BEFORE the `moves` keyword behaves differently: it is skipped and the moves still apply.** On the base
   build, `position fen <K6k> moves a1a2` gives **perft 2 = 15**, and **`position fen <K6k> bogus moves a1a2` also
   gives 15** — the moves were applied. The board-only form gives **9.** **So the junk token is discarded and the list
   applies** — a different behaviour from the truncation above, and **the two must not be merged.**
   - **Whether that is a defect is a judgement, and I am recording the behaviour rather than the verdict.** Discarding
     an unrecognised token before a keyword is ordinary leniency; what a consumer needs to know is that **the moves
     still apply**, so a harness cannot rely on a junk token invalidating the command. **The report calls it a defect;
     the measurement supports "the command is honoured with the junk dropped", which is the part that changes behaviour.**
   - **A `perft 1` fingerprint cannot see this:** bare K6k has **3** moves, and after `a1a2` it is Black to move with a
     lone king, which also has **3** — **identical by construction.** **Perft 2 separates them (9 vs 15).**
   - **And on the older tree the behaviour is the opposite** — the whole command is dropped and the engine stays on
     startpos (perft 2 = 400). **So this one is tree-specific**, and a "junk drops the board" reading was the older
     tree's behaviour, not the base's.
13. **A GENERATED en-passant fixture can lose the edge on the way to the engine and pass vacuously.**
   `python-chess`'s `Board.fen()` **silently drops the ep square when no legal ep capture exists** — which is
   **precisely the ep-exposes-king position** the test is trying to build. So the fixture arrives **without its ep
   square**, the engine correctly finds no ep capture, and **the test passes without ever testing the edge.**
   - **Hand-written FEN literals are safe; generated ones are not.** Measured: the engine accepts the square when
     present and agrees with the reference (`nodes 6`).
   - **The general form: a fixture generator that normalises its own output can delete the condition under test.**
     When the thing you are testing is a *legal-edge* position, assert the edge survives serialisation before you
     trust the result — a passing test over a lost edge is indistinguishable from a passing test over a live one.
   - **AND IT CAN MANUFACTURE A FALSE ASYMMETRY IN A SYMMETRY CHECK — this is a live instance, not a latent one.**
     A test that re-emits `fen()` to build a mirror **can lose the ep square on one side and not the other**, because
     a mirrored position has a **different king-safety situation** and `fen()`'s rule for keeping the ep square
     depends on whether a legal ep capture exists. **So a check whose entire job is detecting asymmetry reports an
     asymmetry the engine does not have** — a false positive from the fixture, in the one test designed to catch a
     real one.
     - **The seat found this in its own symmetry check, after another seat's caveat about generated fixtures.** That
       provenance matters: **the caveat travelled between seats before it bit**, which is the only reason it was
       caught rather than published as an evaluation defect.
     - **The lesson is narrower than "be careful with fixtures": a mirror is a DERIVED position, so anything the
       serialiser normalises is normalised independently on the two sides.** Build both sides from the same
       hand-written literal and flip the fields yourself, or assert that each side's FEN round-trips to what you
       wrote.
14. **`go perft` ends with a bare `nodes N` line, not `bestmove`.** A reader waiting for `bestmove` blocks on it; a
   harness that checks for one **reports the perft as a hang.** §4's general rule is to wait for `bestmove` — **this is
   the documented exception**, and it is the reason a timeout must be reported as a harness fact rather than assumed
   to be a slow search.
   - **And a refused FEN manufactures false movegen bugs.** After a kiwipete position, a refused FEN answered
     `go perft 1` with **`nodes 48`** — **kiwipete's count, for the wrong board**, one `info string` earlier. **Any
     perft harness without a board-identity check reports that as a movegen defect.** The gate: `go perft 1` must match
     the reference in **count AND move set**, plus `go perft 2` at depth ≥ 3.
15. **State, in advance, what result would support the hypothesis and what would refute it** — including for rows whose
   expected value is "unchanged". A table can be arithmetically correct and read backwards.

**While you measure**
16. **Report wins / ties / losses together, and use the SHARE, not the SUM.** "+3 ply over 6 positions" and "+8 ply
   over 130" are the same comparison; the second sounds like progress and is compatible with half the positions being
   identical and a median difference of exactly zero.
17. **A sign-share computed from a QUANTISED measure is a share of that measure's granularity.** Wall time at 1 ms
   resolution on 19 ms searches → **64.6 % exact ties**; integer depth, no timer → **50.0 % exact ties**. Decompose:
   at `go nodes 50000` wins/decided is 65.2 %, at `500000` it is 58.7 % — **once ties are excluded the two budgets
   agree.** Quote a sign-share **with its budget**, never as a bare property of the patch.
18. **Lengthen the measurement rather than redefining the share.** 50k → 500k took ties from 64.6 % to 6.9 % without
   changing the effect's direction.
19. **A sign-share alone cannot classify a claim; the interval decides first.** 50.6 % with no established effect and
   60.5 % with a real pooled effect are closer to each other than either is to 90 %.
20. **"Not established" ≠ "no effect" ≠ "coin flip."** A result whose CI includes 1.0 is **unresolved**. "Coin flip"
    means exactly one thing: a real pooled effect that is per-position random.
21. **Every per-node figure divides by the reported count, not the requested budget.** Otherwise the request cancels
    and you report a time ratio under a per-node label.
22. **A comparison at a fixed node budget cannot show a node saving.** Both engines stop in the same place by
    construction; any residual is the stopping rule's granularity. A 50.6 % sign-share measured there was a correct
    measurement of an effect that does not exist.
23. **`go nodes N` does not fix the workload once `MultiPV > 1`.** The node budget is **shared across the alternate
    lines**, so raising MultiPV *lowers* the reported work: **N = 200,000 spends 52,472 to 199,619 reported nodes,
    falling as MultiPV rises.** So a fixed-nodes arm is not "the same amount of search" when the MultiPV setting
    differs between its arms — and a throughput comparison across MultiPV settings is measuring two things at once.
    **State which quantity is being held constant, and check it held.** (The grid in §1.7 holds time and lets nodes
    vary; that is why it can measure throughput across MultiPV at all.)
24. **Report median and geometric mean labelled, side by side.** Three statistics on one distribution gave three
    different conclusions, and the distribution was the finding.
25. **On a heavy-tailed distribution a claim must NOT be carried by its MEAN — the mean's error was four times the
   median's, and it was unstable in both directions.** Measured on the same PC20 node ratios: **median 0.9618 but mean
   1.0941** on the population run, against **0.9305** from the 1 % stride sample. **The two samples disagree in sign
   on the mean and agree to four decimals on the median.**
   - **So the choice of statistic decides the answer, and the mean is the one that flips.** A heavy tail is exactly the
     case where a mean is dominated by a few positions, so a change in which positions land in the sample moves it.
   - **The tell to look for: a median that is stable across subsamples while the mean is not.** Split the population
     into first / middle / last thirds — **the node median was 0.9618 in all three, while the wall median drifted.** A
     statistic that does not move when the sample is partitioned is a property of the population; one that does is
     reporting where it was measured. **It is why a 1 % stride sample can report the wrong sign.**
26. **A SLICE COUNT is a resolution, and too few slices can invert a conclusion.** "Which factor moves with phase"
   answered **backwards on thirds**, because **a 0.3 % factor cannot be separated from a 1.3 % one at that
   resolution.** Six slices of 4,135 pairs separated them: **per-node spread 0.29 %, node 1.36 %, wall 4.76 %** — so
   **per-node cost is nearly a constant of the engine and the phase dependence lives in the node ratio.**
   - **The wrong answer was not sloppiness; it was the resolution.** The thirds were a reasonable partition and
     produced a confident, coherent, backwards mechanism. **Before answering "which of these factors moves", ask
     whether the partition can resolve their ratio** — here the factors differed by roughly 4×, so a 3-way split
     could not, and a 6-way split could.
   - **The corrected version is also the one that explains a cross-seat agreement:** per-node came out **1.0640,
     1.0693 and 1.0709** across two builds and three sample sizes because **it is the one term that does not depend on
     what you sampled.** A mechanism that predicts its own replication is worth more than one that merely fits.
27. **A MEDIAN of a product is not the product of medians — a per-slice identity does not hold, only the aggregate
   one does.** Slice 2 gives **0.9618 × 1.0719 = 1.0310 against a wall median of 1.0476**, a 1.6 % gap, on data where
   the aggregate closes to 0.5 %.
   - **So check a decomposition at the level it was derived, and say which level that is.** A reader who multiplies
     the slice medians will conclude the identity fails; it does not, and **the table needs the caution beside it** or
     it manufactures a doubt about a sound result.
   - **The general form: any claim of the shape "A × B = C" inherits the aggregation of its terms.** Products of
     medians, sums of means, and ratios of percentiles are all statistics that do not distribute over a partition.
28. **Put the per-position spread on the headline line.** A pooled 5 % saving that wins on 54.2 % of positions with an
    IQR 28× the effect size is a real effect and an unusable per-position predictor. **More data will not remove
    this — it is what the switch does.**
29. **Any speed number from fewer than ten positions is a hypothesis, never a result.** Two out of two small samples
    in this harness erred upward, once by 4×.
30. **A p-value must be recomputable from the counts printed in its own row.** Three of four published sign-test
    p-values read `1.000` when the counts beside them give 0.022, 0.648 and 0.411. The cause was a **missing
    `min(k, n−k)` reflection**, so the test saturated for every share above half and was correct only below it —
    **the one correct row was the below-half one, which made a broken function look validated.** Commit the test, not
    the answer, and give it a symmetry self-test: `p(k, n) == p(n−k, n)`.
31. **A control must be demonstrated to fail when the input is wrong**, not merely to pass when it is right. Three
    natural ways to write one all pass vacuously: `max()` of nothing, `all()` of nothing, a lookup falling through to
    a default. **A control that returns a plausible wrong number is worse than one that crashes.**
32. **An ABSENCE in the engine's favour needs the same proof as a defect — find the WITNESS.** A claim that the engine
   is *wrong not to do something* is a claim that the thing cannot be done, and it is proved or disproved by
   **exhibiting a case**, not by reading a rule.
   - **The case, and I verified it independently:** "KNN vs K is a draw and the engine should adjudicate it" was
     **false**. `8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1` is **valid, checkmate, and not insufficient material**
     (`result 1-0`). **FIDE 5.2.2 draws only when neither side can mate by any legal series, and here a legal mate
     exists** — so the engine's `knights == 0` requirement is correct and the finding was wrong.
   - **It took an exhaustive placement search, and the instrument is the point:** nine material sets were settled by
     **searching for a mate witness**, and all nine agreed with the engine. **An argument about what FIDE means is not
     a proof; a position is.**
   - **The general form: "X cannot happen here" is a universally quantified claim**, and one example refutes it. **Ask
     for the witness before accepting the absence** — the same standard a defect claim has to meet, which is what makes
     absences so easy to get wrong: nobody asks a claim that flatters the engine for its evidence.
33. **A perpetual-repetition fixture must keep MATERIAL constant, or the line is a winning capture rather than a
   repetition.** A cycle that lets one side win material is not a repetition of the same position at all — the
   material changes, so the FENs differ, so it is not a threefold.
   - **This is a fixture-validity rule, not a measurement rule:** a "repetition" line that changes material will
     produce plausible node counts and a confident result about a position that never recurred. **Assert material
     constant across the cycle, and assert the occurrence count with `is_repetition(n)` rather than a hand count.**
   - **The same family as the ep fixture that loses its edge (rule 13):** a generator or a hand-built line can silently
     delete the condition under test, and the measurement runs cleanly on the wrong thing.
34. **A control cell proves only what its axis can see.** When you quote one, **say which axis it controls for.**
35. **A check that fires on CORRECT usage is worse than no check, because it trains you to ignore it.** A guard's
   false-positive rate is part of its cost, and the cost lands on every future reader of its output.
   - **The measured instance:** a leak guard had to become fence-aware because it fired on documentation *describing*
     the leak; an extremum check had to be narrowed to rows that actually make an extremum claim. **The tell is that
     the offending line is always one you just wrote.**
   - **And the same logic makes a gate that fails for an unrelated reason dangerous:** a gate that fails when its
     subject is fine teaches the operator that its failures are noise — **so a false failure and a false pass cost the
     same thing, which is the gate's credibility.** That is why §6.6 treats an unreachable acceptance gate as
     consequential rather than cosmetic.
   - **A narrowed check that is not re-proved is indistinguishable from a removed one**: narrowing is the operation
     that looks like progress and can silently disable, so re-prove every direction after.
36. **A cap test needs a rising-series control.** "Respected the cap" is equally consistent with "ignored the budget
    and searched a fixed amount" unless rising budgets produce rising work.
37. **A control on which the parameter CANNOT BIND cannot distinguish "it works" from "it is ignored".** Testing
   whether `go mate N` respects N on a **mate-in-1 board** gives **depth 1 for N = 1, 2, 5 and 10** — because the mate
   is found immediately regardless of the cap. **Run only that control and the conclusion is "N is ignored", the
   opposite of the truth**; the parameter binds only on a board where the search would otherwise run past the cap.
   - **When testing whether a LIMIT is honoured, pick an input that would EXCEED it.** The control needs the parameter
     to be the binding constraint, not merely present. This is the same family as a cap test without a rising series
     (rule 36), one step further: there the budget never bound because it was never exceeded; here the *parameter*
     never bound because the position made it irrelevant.
38. **A PARSER fault is silent unless the ROW COUNT is asserted — and a guard in one script but not another is what
   makes it visible.** A bulk re-indent left `rows.append(...)` **outside** its `if m:`, so two scripts parsed
   **1 and 8 rows instead of 180 and 464** — and one of them **still printed a complete, plausible set of ratios from
   the survivors.** The script with `expected 180` caught it; the other had **no row-count assertion at all**.
   - **Any script parsing a committed artefact should assert its `n` as a literal**, and prove the assertion with a
     truncated fixture. This is the declines-to-evaluate-reads-as-a-pass rule at the parsing layer: **a parser that
     silently kept 1 row produced a full-looking result table, and nothing in the output said how few rows survived.**
   - **The re-indent is worth noting as the mechanism**, because it is an edit that cannot change logic in the
     author's head — moving a line one level is a formatting act — and it changed the control flow of both scripts at
     once.
39. **Separate a confound from a refutation:** run the same cell with the variable under test removed. If the outcome
    persists, you measured the confound. (Bare kings return 0 nodes at two occurrences only because insufficient
    material is an automatic draw.)
40. **`$?` after a pipe is the LAST command's status.** `cmd | tail` reports `tail`'s exit code. Use `cmd > out; rc=$?`
    or `set -o pipefail`.
41. **A reader that waits for `info depth` deadlocks on every fast path** — the opening book answers with zero info
    lines, and `go nodes 0`/`1` emit none either. **Wait for `bestmove`** (60 of 66 committed harnesses did, and are
    safe) **and put a timeout on every read.**
42. **`go infinite` is bounded by `stop` or depth 64, whichever comes first — and on a real position it is `stop` that
    matters.** Startpos ran a 75-second cap and reached only depth 30 (`cp 7`, 93,981,191 nodes). `stop` returns a
    legal move in 0–1 ms. **Send `stop` and assert the reply.**
43. **The opening book fires on the SIDE-TO-MOVE'S OWN clock, or on `movetime` — not on "the clock form".** The gate
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
44. **Fullmove number and halfmove counter are part of a position's identity** — 5 different mate values across
    counters 0–99, and a 2× node swing for an identical score.
45. **In a paired design, between-subject spread is context and the sign test is the test.** Say **which** variation a
    number describes before comparing two variances.
    - **The error this prevents, measured:** the v3 patch's author first ruled it **NOT MEASURABLE** on the reasoning
      *"the per-position spread (1.30×) is much larger than the median effect (1.2 %), so it cannot be separated from
      position variation."* **That is a category error.** The spread describes how positions differ from **each
      other**; a paired ABBA design **cancels exactly that**, because each position is its own control. The right
      question is *"does the patch win within positions?"* — a sign test on the paired outcomes. It won **107 of 120**,
      p = 1.5e-19 (§1.20).
    - **Rejecting a result looks like rigour, which is why this error survives review.** The seat called it the
      seventh reasoning failure of its night and **the first that would have discarded a true finding rather than
      overstated one** — the safe-sounding direction. **A conservative error is still an error, and it costs a real
      result.**
    - **The tell is grammatical, so it is catchable while writing:** if the statistic you are comparing an effect
      against describes **variation between subjects**, and your design is **within-subject**, you are comparing two
      different things. State the design first, then choose the test.
46. **A motivating ANECDOTE is not evidence about a SELECTOR.** The two are different claims and the first is
    usually much easier to get.
    - **The case:** one board demonstrably kept its move while revising its mate number by 3 between depths, which
      correctly motivated a "select on score change" criterion. **But the criterion's own evidence is a p = 0.0712
      comparison (7/109 vs 21/156, overlapping intervals) and a replication at p = 0.726 pointing the other way.**
      **The mechanism was real; the selector was unsupported.** (§1.7)
    - **The distinction to write down explicitly:** *"X happens"* is established by one case. *"Selecting on X
      separates positions"* needs a comparison, a power calculation, and an interval that excludes the null.
    - **The usable form is asymmetric and that asymmetry is the deliverable:** **select on move change** — its
      direction is established at **p < 1e-6** and replicated; **treat score change as unestablished in either
      direction** — not harmful, not useful. **A summary that upgrades "the mechanism is real" into "use it as a
      criterion" has over-read its own example.**
    - **And the honest report of a failed replication names its power.** "4/23 vs 7/53, p = 0.726" reads as a
      refutation until you notice **the strata are 4.7× smaller** — so the correct statement is **"this sample could
      not detect an inversion of that magnitude"**, not "the inversion fails to reproduce".

**After you measure**

47. **Adjacency is a check.** A claim and its correction must sit next to each other; separation is what let
    contradictions survive. Reordering three sections of one report exposed three contradictions the long layout had
    hidden.
48. **A correction that adds without removing is not a correction.** Adding is an authoring act; removing is a search
    act, and the search only works if you look for what you wrote. **Write both in one edit**, then grep for the
    phrase you contradicted.
49. **After correcting an entry, READ IT TOP TO BOTTOM AS A STRANGER — the editor's eye skips the sentence it did not
   touch.** This is the failure mode that survives rule 48, because the grep finds the phrase you *wrote* and not the
   sentence you *left standing*.
   - **The measured instance, in a defect entry about parser behaviour:** the heading and the new perft-3 evidence both
     said TRUNCATES, while the old sentence three lines above still read "**and then applies `e7e5` anyway**" — the
     withdrawn splice claim. **A reader who stopped at the first sentence got the opposite answer from a reader who
     continued**, and every individual sentence was true of *some* version of the claim.
   - **Why the tell is specifically "as a stranger":** the author reads what they intended in that slot, so the stale
     sentence is filled in from memory and never actually parsed. **The only reliable read is one where you do not know
     what the paragraph is going to say.**
   - **Three instances of the same shape in this document alone**, which is why it is a rule and not a note: a false
     cross-reference that survived several rounds, two stale count paragraphs asserting different totals in the same
     header, and a §3 sentence still claiming a section "ships one and holds the other" after it had been changed to
     hold both. **None was caught by any check; all three were caught by reading the passage cold.**
50. **A claim that reverses twice is evidence about the TEST, not only about the claim — and the reversal count
   belongs in the document.** The corrupted-move-list behaviour reversed three times (splice → truncate → splice →
   truncate); **the first two tests could not separate the hypotheses**, which is why the answer kept following the
   experimenter's belief. **Record the withdrawal path and its cause**, so the next reader knows the third version was
   reached by a test that could distinguish, not by a further guess.
51. **When a claim is corrected, re-run every number inside the corrected passage in the same edit.** Revising a
    figure feels like changing evidence; revising the sentence feels like editing — so the prose moves and the number
    stays. **The correction is exactly the moment a figure is least likely to be looked at again.**
52. **A decomposition is only as good as the pairing of each term to its column, and that pairing needs a LABEL
    check, not an arithmetic one.** A fabricated node ratio (`0.9090`) closed the identity to 0.1 % and appeared in
    *neither* of the source's columns. **A number that makes the identity work is the most dangerous kind, because
    the identity's own closure is what it was manufactured to satisfy.**
53. **A point estimate and an interval from two DIFFERENT ESTIMATORS cannot be quoted as one row.** The result is a
   row whose **point estimate sits outside its own confidence interval** — which is arithmetically impossible for a
   correct pairing and therefore a *readable* defect once you look for it.
   - **The case:** the PC20 per-node row paired a **pooled ratio (1.0643)** with a **mean-of-log interval
     [1.0670, 1.0876] centred on 1.0736** — so the pooled estimate fell **below the lower bound of the interval quoted
     beside it.** Neither bound reproduced under the other estimator (mean-of-log [1.0613, 1.0861]; pooled bootstrap
     [1.0531, 1.0748]).
   - **The conclusion survived because every construction excludes 1.0**, so it was a pairing fault rather than a dead
     finding — **which is exactly why it could sit in a report unnoticed.**
   - **The check is trivial and it is the same one §4 rule 50 needs: ask whether the point estimate is inside the
     interval.**
     If it is not, you have two estimators in one row, not a surprising measurement. **Name the estimator in the row** —
     and bootstrap the estimate you actually quote.
54. **"I could not evaluate this" must never be reported as "this is fine."** A check that declines to evaluate has
    cleared nothing; it is a third verdict, not a pass. Any finite vocabulary has a boundary, and past it the check
    reports PASS rather than UNKNOWN.
54a. **"Reported by the other party, unverified on my side" is its own verdict, and it is what stops a tidy
   explanation from becoming a finding.** When a collaborator offers a mechanism you cannot check, the honest label is
   that one — **not adoption because it is persuasive, and not silence because you cannot confirm it.**
   - **Used repeatedly in this document, and the count matters less than the shape:** `929` and the latency percentiles
     (no committed output), the two-estimator CI row, and **— the instance that produced this rule — a mechanism the
     coordinator offered for our own exchange**, that the prose total had selected the table's rows. **They checked
     their side and found it unverified there too:** the table and its sentence were written in the same edit, so the
     failure was **a collapsed row, not an ordering.** **The explanation fit the evidence and was not a mechanism
     either of us could demonstrate.**
   - **And one case where the label was WRONG in the other direction, which is why the category needs care:** I once
     marked the neural-arch hang "reported, not corroborated" after failing to find it in any branch — **and it was
     committed all along, in `swarm-71`'s `STATUS.md` rather than its `FINDINGS.md`.** **A failed search is not the
     same verdict as an unverified claim**, and labelling my own search failure as a sourcing gap would have thrown out
     a sourced finding. **Say which one you mean: "I looked and it is not there" or "I could not look".**
   - **The tell is that the explanation is BETTER than the evidence.** A story that accounts for every observation is
     the one to interrogate — "it fit" and "it was demonstrated" produce the same confident sentence.
   - **And the thing to keep is the part that survives the mechanism being wrong.** Here the remedy — *write the prose
     total FROM the table, never beside it* — **does not depend on the ordering claim at all**, because a total stated
     first is a hypothesis about the table either way. **State that independence explicitly: it is why a rule outlives
     a retracted reason.**
   - **Turning this standard on a colleague's just-offered sentence is the hard case and the one that matters** — the
     courtesy is not to accept a good story, it is to label it accurately and say what would settle it.
55. **A count printed is not a count checked**, and a count must be compared against the prose, not merely printed.
    **Assert the exact expected count as a literal**, never computed from the list it guards.
56. **A counting claim about a table must be COMPUTED, and a counting dispute is decidable by script in one command —
   so neither party to one should settle it by reading.** This is the rule the run ended on, and it is narrower and
   more useful than "count carefully".
   - **The measured case:** two documents each carried a parser-surface table with a prose total. **One prose total was
     wrong because it reached its figure by double-counting a surface that appears on both sides** (7 rows became
     "three report, two improvise, and `position fen` counts in both"). **The other was correct — and I called it
     inverted, having compared its sentence against MY table's row count rather than its own.** Two errors, both
     arithmetic, both in the same exchange, **and one command settled it.**
   - **The check is: parse the table, group the rows BY SUBJECT, count the verdicts, parse the prose total, compare.**
     It takes a second and it cannot be argued with. **A dispute about a number is evidence that the number was never
     computed** — if either party had run the count, there would have been nothing to dispute.
   - **TWO failures look identical in prose, and summing answers only one of them.** A total that disagrees with its
     table can come from a **mistyped number** or from a **missing row** — and **adding the rows up detects only the
     first**, because a collapsed row makes the sum agree with the prose while both are wrong. **Grouping detects the
     second:** group by subject and **flag any surface that appears once when it is known to have disagreeing
     branches.**
     - **Both failures occurred in this run, in the same table, in opposite directions.** One document's total came
       from **double-counting** `position fen`; the other **collapsed `searchmoves` to a single row**, losing the
       branch that reports. **The first over-counted the reporting side by one; the second under-counted it by one.**
     - **The mechanism the coordinator reports from their own side, and I cannot verify it on mine: the prose total
       SELECTED the row rather than the rows producing the total.** Each table kept the branch that happened to match a
       number already written — **so the disagreement may not have been carelessness on either side, but a written
       total acting as a filter on which branches got a row.** **That explanation is consistent with both tables and my
       own commit history cannot confirm or refute it** — in my case the row and the total landed in the same commit,
       so the ordering is not recoverable. **Recorded as a plausible mechanism, not a measured one.**
     - **The remedy holds either way, and it is the actionable half: write the prose total FROM the table, never beside
       it.** If a total must be stated first, it is **a hypothesis about the table, not a report of it** — and a
       hypothesis is exactly the thing that will quietly select the rows which confirm it.
   - **And the dispute itself is a defect signal one level up:** I was confident, the coordinator was confident, and
     **the disagreement was decidable by script the whole time.** Confidence on both sides of an arithmetic question is
     a reason to compute, not a reason to press the argument politely.
57. **A checker is tested by giving it a case whose answer you already know, never by reviewing its logic.** Every
    checker failure in this run that was caught, was caught that way; none was caught by reading the checker.
58. **A script cited as evidence must be tested for its EXIT CODE, not just its output.** Two scripts the report told
    a reader to run printed `FAIL` and exited 0. **Prove a gate once per checker it invokes, not once per gate.**
59. **A verdict that depends on where you stand is not a verdict.** Five scripts depended on the run directory; one
    compared an empty string to an empty string and reported verbatim agreement. **Anchor to `__file__` and run each
    script twice — from its own directory and from `/tmp`.**
60. **A settings NAME is not evidence the settings were sent.** One harness's option list was named `S14` while
    containing the five PC20 switches. **Have a tool print the option list at run time and paste that output into the
    finding.**
61. **Bench is not a proxy for real positions, and its bias is patch-specific, not directional.** Three measured
    failure modes: per-node cost ~1.2 % on bench vs **~6.4 %** on real positions (6× optimistic); aggregate node-count
    sign **+14.5 / −10.6 / +8.7** across benches 11/13/16 against **−8.7 %** on real positions; a profile self-time
    share 2.71 % on bench vs **0.66 %** real. **A self-time percentage is not a transferable cost unless someone
    removes the code and measures it.**
    - **Bench IS valid for** pins, determinism, ablation direction, structural counters, and the pooled effect of one
      isolated toggle. **Not valid for** per-node cost or the aggregate PC20 set. **Always report the per-position
      spread.**
62. **Cold reading is the highest-yield instrument on the class the checks cannot reach.** Four defects in six blocks
    — a joining phrase doing the work of three results, ordinals running backwards, a table row implying a control
    that never existed — **all invisible to every automated check, all found by reading.** Not a substitute for the
    checks; it covers what they structurally cannot.
63. **A figure "found" by matching digits inside a DIFFERENT sourced number is how a presence check imitates a
    provenance check.** The most dangerous form of a false pass, because it returns **FOUND** and ends the search.
    - **Three measured instances in one audit, all caught only by reading the context:**
      `0.024` matched `"seconds": 0.024` in unrelated search JSON; `0.44` matched `loadavg 0.44 on 4 cores`; `442`
      matched a table row reading `1442.0`. **None of the three occurrences was the claim being checked.** All three
      were book-latency percentiles that appear in no committed file.
    - **The mechanism: a large corpus makes false positives the dominant risk, not misses.** Widening from 8.5 MB of
      `.md` to 167 MB of `.md` + `.txt` resolved every genuine figure — and simultaneously manufactured three
      matches. **Enlarging the corpus trades false-negative risk for false-positive risk, and the false positive is
      worse because it produces a clean verdict.** So "widen the corpus" is not unambiguously the safer direction.
    - **Measured, and it settles the question: five figures, five corpora hit counts, zero of them the claim.**
      `0.024` occurs 39 times, `0.44` 115, `442` 4,831, `929` 3,136, and **`42` occurs 88,888 times in the corpus and
      is never the quantity claimed.** **A token that occurs 88,888 times makes "found" a meaningless verdict**, and
      every one of the five would have returned FOUND.
    - **The repair is not a better pattern, it is a context read per hit.** For every figure whose provenance
      matters, print the matching line and check that **the quantity in the line is the quantity in the claim.** A
      match is a candidate, never a resolution.
    - **Its companion, and the reason a count like §5's is a floor: a provenance check against the remote cannot see
      a branch that has not landed.** A figure from the last ten minutes will always look unsourced — I reported four
      such figures that landed minutes later and were all genuine. **Record the COMMIT each branch was audited at, not
      the clock** — a timestamp is unverifiable after the fact and invites the reading that the document is at fault
      when the snapshot is. **The count is a property of the tips named in the header, and nothing else.**
64. **A DERIVED claim is where a plausible figure outruns its evidence — and it is the single most reusable thing in
    this run's method record.** **Every other claim here is one comparison against one threshold and has one number to
    check; a decomposition has three numbers, two samples and one subtraction — and it is the derived part that gets
    quoted to three significant figures.**
    - **The shape of the failure:** `135.4 ms = 104.5 allocation + 31 search` reads as a measurement. It is the
      **difference of two noisy quantities from different samples** (a median over cell medians, against one
      position's time-to-first-`info`), and the excess is not position-independent — **per position it ranges 135.0 to
      195.6 ms, median 140.5**, which puts the residual at **~36 ms, not ~31**.
    - **The repair is to state a RATIO and label it a bound.** "Allocation alone predicts **1.72×**; **1.94×** is
      observed; **~0.22×** of the total is search" **holds whichever position or sampling convention is used**, and it
      says what it is: **a bound on a small residual, not a measurement of it.**
    - **Why it survives review: the arithmetic is right.** The subtraction closes, the three numbers are individually
      sourced, and the sum is correct — **the error is in the precision the form implies, not in any term.** That is
      why it is the same class as a fabricated pairing (rule 50's label check) and needs the same defence: **ask what
      each term's own uncertainty is before you quote the derived one.**
    - **The checkable discipline: a derived figure must name its operands, their samples, and their spread.** If any
      of the three is missing, **quote the ratio or the direction, never the point estimate.** A bound that is honest
      about being a bound is worth more than a measurement that is not one.

---

## 5. Unsourced in the consolidated report

**Count of figures with no source anywhere — in the 34 branches or the working tally: 9.**

Every numeric token in the consolidated report — **284** distinct percentage, ratio, large-integer and fraction
forms — was checked against a corpus of **167 MB**: every tracked `.md` **and `.txt`** under
`forge-combo29/swarm/NN/` for the **31** finding-bearing branches read, **plus `internal/swarm/tally.md`**. **The audit is against the
branch tips named in the header**, which is the only form of this claim that stays checkable: a timestamp says when I
looked, a commit says what I looked at.

**And the count has now been wrong twice in the direction this guards against, which is why the tips are named.**
Two rounds ago I reported four figures as unsourced; all four were in `swarm-64`, **which pushed minutes after my
fetch.** `13.2 %` and `54,379` came off the list in later rounds for the same reason. **All were timing artefacts, not
defects in the report** — so read the count below as **a statement about these tips**, and **re-run the audit against
new tips before treating any of them as a defect in the document.**

**The unsourced set, by cause — and this round it moved onto a recommendation's load-bearing evidence:**

| figure | where it appears | what it measures | cause |
|---|---|---|---|
| `0.024` | trap 19, book latency | book path p50, ms | **no committed output** |
| `0.44` | trap 19, same bullet | book path max, ms | **no committed output** |
| `442` | trap 19, same bullet | off-book p50, ms | **no committed output** |
| `929` | trap 19a, book soundness | false material flags the SEE checker first reported | **no committed occurrence** |
| `42` | trap 19a, book soundness | noise floor, cp | **contradicted** — evidence says 66 |
| `40 of 40` (at 2,000,000 nodes) | §3, the Hash 16-vs-64 sweep | cells differing at the largest budget | **budget not in the committed sweep** |
| **`0 of 125`** | **§1.2, the SHIP verdict** | **non-drawn roots entering the scan** | **no committed occurrence** |
| **`13 of 13`** | **§1.2, the SHIP verdict** | **drawn roots entering the scan** | **no committed occurrence** |
| **`220–280 ns`** | **§1.2, the SHIP verdict** | **per-legal-move scan cost** | **no committed occurrence** |
| `13,707` | §1.2, base rate | plies of 60 random games | **no committed occurrence** (the `1,943` half **is** sourced) |

**Nine figures against these tips, and three of them are the count that licenses the run's headline recommendation.**
That is a materially different risk from the supporting-figure misses above, and §5's closing paragraph says what to do
about it.

**`13.2 %` came off this list this round, and the way it did is the method working.** It was unsourced when I checked
against the tips named two rounds ago; `swarm-27`'s `S-C108` now carries it — *"move-unstable 8/24 = 33.3% vs
remainder 13.2%, their p < 1e-6"*. **Same figure, same claim, now sourced: it was a timing artefact of my own fetch,
which is exactly what rule 60's companion warns about.**

**And `54,379` came off it in the same way, one round later.** `swarm-71` has moved and now carries it directly —
*"54,379 distinct positions compared against a fresh refresh: 0 mismatches."* **So the accumulator aggregate is
sourced**, and the earlier note that `swarm-71` commits only fixtures and commands is **stale**. **Two figures
recovered by refetching is the argument for naming tips rather than reporting a bare count.**

**What is left unsourced in this block is a different and more uncomfortable case: the shippability count itself.**

| figure | where | cause |
|---|---|---|
| `0 of 125` non-drawn roots entering the scan | §1.2, headline | **no committed occurrence** |
| `13 of 13` drawn roots | §1.2, headline | **no committed occurrence** — the `13 of 13` cells in the corpus are unrelated pair comparisons |
| `13,707` plies / `1,943` plies (base rate) | §1.2 | **`1,943` sourced**; `13,707` appears only as unrelated node counts |
| `220–280 ns` per legal move | §1.2 | **no committed occurrence** |

**This is the first time the unsourced set has landed on a recommendation's load-bearing evidence rather than on a
supporting figure**, and it deserves saying plainly: **the SHIP verdict in §1.2 rests on a count I cannot check from
the branches.** The adversarial-family results (`b3b1` vs `b3a3`, the near-misses, the 16 node-identity observations)
**are** sourced — so the verdict's direction is supported — **but the specific claim "the scan is paid on drawn roots
only, 0 of 125 / 13 of 13" is report-only.** I have carried it because the shape of the argument is complete and the
supporting results are committed; **treat re-measuring that count on your build as the check that converts it.**

**`40 of 40` at 2M is the mildest and worth distinguishing.** `swarm-69`'s committed `hash_sensitivity.json` **stops
at `go nodes 1000000`**, where Hash 16 vs 64 differs **24 of 24** — so the 2M claim is plausible and **adds nothing
the 1M row does not already establish.** Its `40/40` in `FINDINGS.md` is a **different comparison** (warm vs fresh at
every Hash size), which is exactly the digit-match hazard of rule 60 rather than support. **I use the 1M row in §4
rule 3 and note that the 2M row is unreproduced.**

**And one that is not counted: `0.0712`, which I verified by arithmetic.** The Fisher p-value recomputes to 0.071172
from the counts, matching the report exactly — but its *digits* appear in the corpus only as a substring of
`pernode1.07126`. **So it is verified from first principles and unsourced by provenance.** I exclude it from the
count above because **an independent recomputation is a stronger guarantee than a citation**, but not the guarantee
this section measures.

### Cause 1: the latency percentiles — a script shipped, its output not

`swarm-65` **ships the script that would produce `0.024` / `0.44` / `442`** (`scripts/q2b_latency.py`: "200 consecutive
`go` commands … wall time of each `go`-to-`bestmove` round trip") **but commits no latency output file.** I checked all
36 files in that seat, and no branch contains `p50` in any prose file.

**What the committed evidence does support, and it is enough for the recommendation:** single-shot wall times of
**0.1–0.4 ms** for book moves against **91–346 ms** off-book, with **0 `info depth` lines** on the book arm
(`evidence/cost_deadlock.txt`, `go_matrix.txt`). **Four orders of magnitude and the reader hazard are both
established; the percentile figures are not**, so §1.22 quotes the committed times.

### Cause 2: `929` and `42` — one unsourceable, one contradicted, both flattering

**`929` has no committed occurrence.** The only `929` in `swarm-65` are hex-hash fragments inside `book_walk.tsv`.

**`42` is worse than unsourced: it is contradicted.** `evidence/noise_floor.txt` gives **max |delta| 66 cp** (mean
−1.2, median −1, 111 samples). **The report states a smaller floor than the committed measurement.**

**Both point the same direction, and that is the finding.** The `929` makes the checker's initial failure sound worse
than anything on record; the `42` makes the noise floor sound smaller than measured. **Each is more flattering to the
conclusion than the evidence** — the direction that costs a result its credibility the moment someone checks.

**And the `42` case shows the flattering number was unnecessary.** The claim is that the `1 of 2,520 above 100 cp` gaps
are horizon artefacts against a noise floor. **With a 66 cp floor that argument is easier**, not harder — 103 cp sits
closer to the floor, and `noise_floor.txt` itself reports **`0 of 111` above 100 cp**, which is the direct support.
**The honest number strengthens the claim; the report did not need the better-sounding one.** §6.5 carries this in the
mis-pairing section, since a contradicted figure belongs there as well as here.

### Cause 3: `13.2 %` — the move-change comparison's denominator

The report states move-unstable boards disagree **33.3 % (8 of 24) against 13.2 %** for the remainder, `p < 1e-6`.
**I could not find those counts in any branch**, and `33.3 %` in the corpus appears only as a *confidence-interval
bound* in unrelated work (`28.6 %, CI 23.9–33.3 %`). **So the move comparison's exact counts are unsourced here**,
which is why §1.7 quotes its **p-value only** and says so. **The direction of that result is not in doubt** — it is
replicated and the report is emphatic — **but I cannot reproduce its table from committed branch content, and a
p-value alone is not a check.**

### The method limits that produced these

**Limit 1 — a check against the remote cannot see a branch that has not landed.** Last round I reported four figures
as unsourced (`52,472`, `199,619`, `4/48`, `14/13`); **all four are sourced** and `swarm-64` had simply not been
pushed when I ran. **The count is a floor, and the `git fetch` time belongs beside it.**

**Limit 2 — the corpus vocabulary.** The token audit examines four patterns; **`929` and `42` are bare integers outside
all four**, so it reported no opinion and its silence read as a pass. **Cold reading found them.**

**Limit 3 — and it is the one that nearly produced a false all-clear this round.** With the corpus widened to 167 MB,
**the audit now returns `0 unresolved`** — because `0.0712` matches `pernet1.07126` and `13.2%` matches something
similar once separators are stripped. **A large corpus in which every digit string occurs somewhere converts the
audit's only output into a constant `clean`.** §4 rule 60 records the hit counts: five figures, **39 / 115 / 4,831 /
3,136 / 88,888** raw occurrences, **zero of them the claim**.

### The naive pass, and the boundary of the token audit itself

A literal substring pass — no normalisation — flags **26 of the 252**. **23 are formatting; 3 are unsourced** (the
latency percentiles):

| category | count | example | why the literal pass missed it |
|---|---|---|---|
| spacing before `%` | 18 | `50.6%` | branches write `50.6 %` |
| thousands separators | 5 | `979,723`, `353,312`, `2,893,009`, `1,237`, `52,472` | branches write `979723` |
| **unsourced** | **3** | `0.024`, `0.44`, `442` | the latency percentiles — no committed output |

**But the audit covers 3 of the 5 unsourced figures, not 5, and the gap is a vocabulary boundary I have to state
rather than let the count imply otherwise.** The token audit examines four patterns: percentages, thousands-separated
integers, decimals of ≥2 places, and `n/m` fractions. **`929` and `42` are bare integers outside all four** — so the
check could not see them, reported no opinion, and **that silence read as a pass.** I found them only by reading the
new book section against `swarm-65`'s evidence files, which is not a repeatable instrument.

**This is the run's own rule applied to my own tool: "any finite vocabulary has a boundary, and past it the check
reports PASS rather than UNKNOWN."** My audit is exactly that check. **The honest statement of coverage: 252 tokens
examined, 5 unsourced, of which the instrument found 3 and cold reading found 2.** An untested instrument is not a
clean one, and I would rather report the 5 with the split than the 3 with a clean sheet.

**And the scale of the false-match problem is worth stating numerically, because it settles how much a presence check
is worth here.** Raw occurrences in the 167 MB corpus:

| token | occurrences in corpus | occurrences that are the claim |
|---|---|---|
| `0.024` | **39** | 0 |
| `0.44` | **115** | 0 |
| `442` | **4,831** | 0 |
| `929` | **3,136** | 0 |
| `42` | **88,888** | 0 |

**A token that occurs 88,888 times and is never the claim makes "found" a meaningless verdict.** The check that
matters is not *does this string exist* but *does the line containing it state the same quantity my sentence states* —
and that is a reading, not a query. **Five figures, five zero-per-cent hit rates, and every one of them would have
returned FOUND.**

**Publishing the naive count is what makes any of this mean anything.** A clean zero from a single pass is
indistinguishable from a pass that could not have found anything — *every absence looks like success*. The number that
carries weight is **"26 candidates examined, 23 explained, 3 with no source — plus 2 outside the instrument's
vocabulary"**.

**The corpus grew three times, and the growth is where the method improved:**

| corpus | size | what it added | effect |
|---|---|---|---|
| `FINDINGS.md` only | 2.2 MB | the obvious subject | missed everything in `STATUS.md` / evidence files |
| all `.md` per branch | 8.5 MB | `STATUS.md`, `HARNESS_TRAPS.md`, reports | most figures resolved |
| **all `.md` + `.txt`** | **167 MB** | **evidence files** — `soundness.txt`, `GRID.md`, grid JSONs, `gap_depth10.txt` | **`2,429` and the whole book-soundness block resolved** |

**The third widening is the one that matters and it is a named gap closing.** `2,429` is a polyglot-key count that
lives in `swarm-65/evidence/soundness.txt` — an evidence file, not a findings file. **My corpus was `.md`-only**, so
the entire book-soundness block looked unsourced when it was committed all along. **This is exactly the
selector-too-narrow failure the run catalogues** (`a *.md glob while evidence is *.txt`), and I committed it in the
audit written to catch it.

**And the widening has a second edge that the 3 unsourced figures expose:** a 167 MB corpus contains so many numbers
that **false matches become the dominant risk**, not misses. `0.024` matched `"seconds": 0.024` in unrelated search
JSON; `0.44` matched `loadavg 0.44 on 4 cores`; `442` matched a row reading `1442.0`. **A bigger corpus trades
false-negative risk for false-positive risk, and the false positive is the more dangerous one because it produces a
clean verdict.** That is rule 60.

**The counts moved six times while I worked, and every move is stated rather than smoothed:**

| pass | tokens | naive misses | unsourced | what changed |
|---|---|---|---|---|
| first | 226 | 52 | 0 | report as it stood at the start |
| after the three-population table | 228 | 34 | 0 | 2 **derived** values (`0.067`, `0.672`) the report had introduced |
| after the report's §9b + the v3 patch | 231 | 32 | 0 | **the derived category emptied** — the seat recorded the arithmetic on the branch |
| after the book + MultiPV rewrite | 252 | 38 | 4 → **0** | I reported four; **all four were sourced** and `swarm-64` had simply not landed |
| corpus widened to `.txt` evidence | 252 | 26 | 3 | `2,429` and the book block resolved; three latency percentiles did not |
| **cold-read of the new book section** | **252** | **26** | **5** | **`929` and `42` added by reading, not by the instrument** |

**Two of those rows are my errors and both are worth reading as errors.** The fourth: I reported four unsourced figures
with a confident explanation — an unpushed seat — and **the explanation was right while the conclusion was wrong**: the
branch landed minutes later and contained all four. **A provenance check is a snapshot of the remote, not a property
of the figure.** Recording "4" and then "0" in the same slot is what keeps the number honest.

**The sixth is the more useful one, because it is a limit I did not know my instrument had.** The token audit examines
four patterns and **`929` and `42` are bare integers outside all four** — it had no opinion on them, and its silence
read as a clean result for that part of the document. **I only found them by reading the new section against the
evidence files.** So the count went *up* on the pass where the method improved, which is the correct direction and the
one a summariser is most tempted to hide. **The five are the honest total; the three is what my instrument can see.**

**The limit of the check, stated because the run itself states it:** this proves **presence**, not **pairing**. "The
audit checks that SOME path resolves, not that the path supports the claim." A figure can appear in a branch and still
be attached to the wrong quantity here — and **a presence check reported the document clean while §6.1's mis-pairing
was live.** That is the sharpest thing this audit demonstrates about itself.

**And its companion limit: presence is also not proof that the OCCURRENCE is the claim.** A 167 MB corpus will contain
almost any digit sequence somewhere. **`0.024`, `0.44` and `442` were each "found" — in `"seconds": 0.024`, `loadavg
0.44`, and a row reading `1442.0`.** A pattern check called all three resolved. **A
provenance check that reports "present" has established only that the digits exist somewhere in the corpus.**

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

### 6.5 The book-soundness block: two figures the report states and the evidence does not

The report's book-soundness entry is now its own section with all the counts, and **five of its figures check out
exactly against committed evidence files** (`2520/2520` legal, `2429/2429` keys, `2230/2230` walked, `0/135` verified,
`max gap 103`). **Two do not:**

| report says | committed evidence says | verdict |
|---|---|---|
| the checker "first reported **929** false material losses" | **no file in `swarm-65` contains `929` as a count.** The only occurrences in the seat are hex-hash fragments inside `book_walk.tsv` (`2d02292962c29c44`, `b8929259491f7812`) | **unsourced** |
| noise floor "up to **42 cp**" | `evidence/noise_floor.txt`: **max \|delta\| 66 cp**, mean −1.2, median −1, over 111 samples | **the evidence gives a LARGER floor** |

**Both errors point the same way, and that is the part worth your attention.** The `929` makes the checker's initial
failure sound *worse* than anything on record; the `42` makes the noise floor sound *smaller* than measured. **Each is
more flattering to the finding than the committed evidence**, which is the direction that costs a result its
credibility if anyone checks.

**And in the `42-vs-66` case the correct figure strengthens the argument rather than weakening it.** The claim is that
the `1 of 2,520 above 100 cp` gaps are horizon artefacts against a noise floor — **with a 66 cp floor that argument is
*easier* to make**, since 103 cp sits closer to the floor than 42 cp suggested, and the report's own `0 of 111 above
100 cp` in the noise sample supports it directly. **So this is not a case where the honest number hurts the claim; it
is a case where the flattering number was unnecessary.**

**The `929` I cannot resolve in either direction.** It may be real and simply never committed — the seat's
`see_selftest.txt` shows **6 hand-computed cases with `0/6` failures**, which is consistent with a self-test existing
but not with a `929` count. **I have kept the qualitative point (§7) and marked the number as unsourced**, because the
point survives without it: a checker was falsified once and that is why `0 of 135` is believable.

### 6.6 The identity baseline is stated as an acceptance gate that this branch cannot meet

**This is the most consequential item in §6, because it is an instruction rather than a figure.** The report says
**"any future patch must reproduce `27,944,084` exactly."** On this branch that is **impossible for a reason unrelated
to any patch**, and the report does not say so (`swarm-71`):

- **The three pinned evals reproduce exactly** (968 / 1176 / 31), and **the no-option bench rows reproduce exactly**
  (no-net bench 11 = `312,866`; test-net-only bench 11 = `965,454`).
- **The PC20 bench rows do not:** row 2 gives `242,804` against a pinned `278,024`; row 4 gives `471,702` against
  `625,258`.
- **The 200-opening sum gives `29,791,805`, a 6.6 % gap**, with row 1 at `62,951` against a committed `110,540`.
- **Cause: four of PC20's twenty options are absent here** — `CuckooRep`, `HistRework`, `TtPruneV2` and `CorrHistV2`
  each return `unknown option`, **and none appears anywhere in the source**, so the behaviour is absent rather than
  merely unadvertised. Setting the 14 that *are* S14 reproduces `242,796` / `656,517` to the digit.

**A gate that fails for a reason unrelated to the thing it gates is worse than no gate**, because the first false
failure teaches the operator to ignore the check — the same class as a control that fires on correct usage (§4
rule 35). **The instruction should be an S14-configuration identity, and the PC20 figures should be marked
unavailable here.** My §1.11 says this and carries the caveat with the number, as requested.

**And the harness trap landed on the run's own acceptance criterion.** A `setoption` naming an unadvertised option is
**silently ignored** unless the reply is read — rule 9 and §4 — and two seats recorded it. **The v3 acceptance test
inherited exactly that defect, which is why the four options were dropped without anyone noticing.**

### 6.7 The PC r15 columns have a provenance gap, and it is the widest one in the report

**This is the only item in §6 that affects how a reader should treat a whole set of columns**, so it is stated once
here and cross-referenced at every place the columns appear (§2.1).

- **The numbers — `cp 425`, `mate 1`, `mate 8`, `mate 9`, the mate-in-one fix — trace to a handoff document, not to a
  reproducible artifact.**
- **The flag that disarms the guard, `FORGE_FIX_ROOT_DRAWN`, is not committed as source in any branch.** I verified
  this across all 63 `swarm-NN` branches: it appears **only in prose, findings documents and check scripts**, and
  **never in a `src/` or `include/` path.**
- **`-DFORGE_MATE_ALPHA_GUARD=1` is NOT the repair**, and this is the trap that would waste an afternoon: a build with
  only that flag is **byte-identical to a control and still bails on a threefold root.** It gates `MateAlphaGuard`, a
  search-pruning switch (`search.hpp:310`) — a different mechanism.

**What follows, and both halves matter:**

1. **This is a provenance gap, not evidence the numbers are wrong.** They are **mutually consistent**, and `swarm/23`
   records the patch's sha256 prefix. **Do not read "unsourced" as "incorrect" here** — the distinction §5 exists to
   draw.
2. **The repair cannot be independently rebuilt from the record** — and that is precisely what the shipped patches
   close. **Seat 12's and seat 27's patches are committed as text, compose to a byte-identical file, and have a
   measured ship verdict (§1.2).** **So apply those; do not try to re-derive r15.**

**The general form, which is why this is a §6 item rather than a footnote:** **a measurement whose *instrument* is
uncommitted is not reproducible even when its *numbers* are internally consistent** — and unlike a missing figure,
nothing in the output looks unusual. **The shipped patches are the record's answer to this: the repair that can be
applied is the one that can be read.**

---

## 7. What the book gets right — the soundness result

Recorded in the closing section rather than the recommendations, because **it is a clean bill and the defects around
it (§1.22, §2.8) are about signalling rather than about the moves.**

**No book move is illegal, and none loses material.** Build `/tmp/build65/forge`, `swarm-65`. Every row cites the
committed evidence file, so each is checkable without re-running anything:

| check | result | evidence |
|---|---|---|
| book moves legal, against python-chess | **2520 / 2520** | `evidence/soundness.txt` |
| polyglot keys match `chess.polyglot` | **2429 / 2429** | `evidence/soundness.txt` |
| book keys reached by the walk | **2230 / 2230** (of 2616 entries) | `evidence/census.txt` |
| material-loss flags surviving engine verification at depth 12 | **0 / 135** | `evidence/soundness_verified.txt` |
| exhaustive gap sweep, depth 10 | **max gap 103 cp**, 1/2520 above 100, **0/2520 above 150** | `evidence/gap_depth10.txt` |

**The material-loss check is the one worth reading twice, because its first version was wrong and said so loudly.**
The seat's own SEE implementation tested capture legality **against the wrong side** and reported a large number of
false "loses material" flags; the committed `evidence/see_selftest.txt` shows the repair — **6 hand-computed cases,
`failures: 0/6`**, including a deliberate regression case. **So "0 of 135 survive verification" is a claim about a
checker that was itself falsified once first**, which is what makes it worth more than a clean number from an
unchecked tool. **The specific count of initial false flags the report states (`929`) has no committed source and I do
not carry it** (§6.5) — **the qualitative point survives without the number.**

**What this does and does not mean.** The book's *contents* are sound: the moves are legal and material-safe. **It says
nothing about whether the book is a good book** — soundness is not move quality, and no move-quality measurement of
the book was made. **And it does not touch the signalling defects:** a sound book move in a drawn position is still a
reply that tells a caller nothing about the draw (§2.8).

---

## 7b. The property that outlives every individual finding

**This engine has FIVE documented ways of returning a well-formed answer to a question that was not asked.** Each was
measured separately; collected, they are one property of the protocol surface rather than five anecdotes:

| # | mechanism | what you asked | what you got |
|---|---|---|---|
| 1 | **`bestmove 0000`** | a move | no move — for **checkmate** (correct), **stalemate**, or an empty restriction (§2.4) |
| 2 | **zero `info depth` lines** | a search | a `bestmove` with no search behind it (§2.4, §1.3) |
| 3 | **a refused FEN searching the last valid board** | about position B | a legal move, plausible score and full PV **about A** (§2.3) |
| 4 | **an unknown `go` token silently ignored** | `mpv 3` | **MultiPV 1** — the setting you asked for, absent (§4 rule 9) |
| 5 | **a neural arch with no usable net** | a loaded net | an error, **then exit with no `readyok` and no `bestmove`** — a GUI hangs (§2.9) |

**In four of the five the protocol says nothing that a consumer will act on. In three the output looks exactly like a
success, and in the fifth the process simply stops answering.**

**And the surfaces are not uniform, which is the part that makes "handle it" hard to write as a checklist:** counting
the rows of the table in §4 rule 12, **9 rows — 5 report the fault and 4 do not**, with **two** self-disagreeing
surfaces each appearing once per branch (`position fen`, `searchmoves`). **A harness that has verified one surface's
refusal behaviour has learned nothing about the others** — §4 rule 12.

**And `position fen` refuses in one direction while improvising in the other**, which is the case that breaks the
checklist most cleanly: **too few fields is refused loudly and then the previous board is searched; too many fields is
accepted silently and is the position you meant.** Same command, opposite behaviours, and only one of them is
dangerous. **That is why the rule is to count the fields yourself rather than to read the diagnostic** — rule 11.

**Why this belongs in the summary as one thing rather than five:** the individual defects are separately fixable and
separately severe, **but the property is what a consumer has to defend against, and it does not go away when any one
of them is fixed.** A front end built to handle (1) alone will still be fooled by (3). **The correct posture is not
"handle these cases" but "never trust an engine reply without an independent check of the input that produced it"** —
validate the FEN, assert the configuration from the engine's own reply, and check `pv` before believing a move.

**And it is the reason §1.3's empty-`pv` check is necessary but not sufficient.** That check resolves (3) and (4)
**not at all** and (2) only partly. **Each of the five needs its own defence, and the defences do not compose.**

---

## 7c. The reuse trap, which is the one that silently corrupts a whole measurement

**`Clear Hash` is not a cold reset, and the resulting error is REPRODUCIBLE — so a reused harness does not get noise,
it gets a stable-looking wrong number.**

| reset regime | cells differing from a fresh process |
|---|---|
| `ucinewgame` | **0 of 25** — a true cold reset |
| `Clear Hash` | **24 of 25** |

**The source says exactly why.** `ucinewgame` calls `Searcher::clear()` (`src/search.cpp:2679`), wiping **histories
and** the table. `Clear Hash` calls `clear_hash()` (`:2667`) and then `clear_caches()`, which is **only**
`evaluator_.clear()` (`include/forge/search.hpp:452`) — so the histories survive, and they are what steers the next
search.

**Why this is worse than a noisy harness, and it is the whole point:**
- **The drift reproduces on 3 of 3 independent processes, identically.** **Re-running the harness confirms it.** A
  reader who checks gets the same wrong number twice and concludes it is real.
- **Noise is visible in a variance report; this is not.** The tell that normally saves you — inconsistent results —
  has been removed.
- **It bites the pattern real harnesses use.** Walking games: **5 of 6 positions** reached by random legal games
  differ from a fresh process, under both `position startpos moves` and `position fen`, with and without
  `Clear Hash`. **`ucinewgame` restores 0 of 6.**
- **And it grows.** Four consecutive searches of one position in one process drifted deterministically — 37,135 /
  41,762 / 39,116 / 30,366 nodes, cp 72 / 37 / 44 / 35 — **the error increasing with the number of prior searches**
  (`swarm-69` 69-F6…F8b).
- **A larger Hash does not rescue it:** warm-vs-fresh differs on **40 of 40** cells at **every** Hash size.

**The rule, and it is the cheapest one in the document: send `ucinewgame` between searches, or use a fresh process —
and prefer the fresh process, because it also removes the failure mode where you forget.**

**One thing the reuse trap does *not* do, which is worth knowing:** nine machine-environment inputs change nothing at
a fixed budget — working directory, locale/TZ, environment-variable order, CPU affinity, `nice`, and several
`ulimit` settings all gave **0 of 40 differing** at two budgets, on both builds. **A fixed-budget answer is a property
of the (build, position, budget) triple, not of the process environment** (`swarm-69` 69-F5/F5c). **So the environment
is not your problem; the TT state is.**

---

## 7d. The v3 incremental accumulator is correct at scale — 54,379 distinct positions, 0 mismatches

**The second clean bill in this report, and the one that covers the code path your PC actually runs.** Every
incremental update was compared against a **fresh full refresh**:

| check | result |
|---|---|
| distinct positions compared | **54,379** |
| mismatches | **0** |
| coverage per position | every unit of both perspectives (2×512), both king keys, both king squares, and the net output against a reference — **at every ply of every sequence** |
| **king-key transitions** | **5,012, 0 mismatches** — the one branch quiet games never reach |
| independent arm: the engine's own verification build (aborts search on disagreement) | 200 positions, depth 12, **37.5 M nodes, 0 mismatches** |

**The coverage point is why this is worth believing.** Quiet games almost never cross a **king-bucket boundary**,
which is the only branch where the incremental path abandons the update and rebuilds the bitboards by undoing later
plies. **Purpose-built walks produced 5,012 of those transitions — a branch a normal position set leaves untested.**
So the result is not "we compared a lot of positions"; it is **"we reached the branch that a normal position set
cannot reach."**

**Corrupt nets are refused with specific reasons:** 12 damage cases, **11 refused**, and the one accepted is a bit
flip with a **recomputed checksum** — which must load, because **a checksum detects accident, not intent.** Nothing
loads and silently produces garbage.

**A method note that belongs with the number, because the number was wrong once.** **The per-run counts cannot be
added.** The three sequence fixtures are **nested** — each takes the first N rows of the same corpus with the same
40-ply prefix — so the largest already contains both smaller ones entirely. **The distinct total is a UNION:
54,379 = `seq_deep` 47,418 ∪ `kingwalk` 6,961.** An earlier count of **57,720** was the sum, and the seat caught it
after pushing.

**This is §4 rule 61's shape at the aggregate level** — a derived figure whose operands were right and whose
combination was wrong — and the repair is the durable part: **the count is now machine-computed and enforced by a
script wired into the run, so the literal cannot drift.** And the coverage claim is unaffected, which is the thing to
keep precisely: **the 5,012 king-key transitions are all inside the union and disjoint from every other fixture**
(`kingwalk`'s overlap with every other fixture is 0), so they are the part of the result that nothing else reaches.

---

## 7e. Move generation is clean over 5,075 comparisons — and the coverage is measured, not assumed

**The third clean bill, and the one whose method is worth copying.** Base `6b98f217`, unmodified; **zero mismatches
anywhere**, against published counts and an independent generator:

| stage | compared | mismatches |
|---|---|---|
| standard suite (7 positions × depths 1–7) | 42 cells | **0** |
| special-move fixtures | 11 fixtures / 33 cells | **0** |
| uniform random play | 2,000 positions | **0** |
| directed en-passant / castling | 500 + 500 | **0** |
| **targeted:** ep discovers check; ep exposes king; castling rights lost by rook capture; underpromotion giving check | **500 each** | **0** |
| **total** | **5,075** | **0** |

**The reason this is credible rather than just large is the coverage table, and it is the sentence to reuse:**

| edge | positions where it was AVAILABLE, uniform random play |
|---|---|
| en-passant capture | **8 / 2,000** |
| **promotion** | **19 / 2,000** |
| castling | 67 / 2,000 |
| side to move in check | 85 / 2,000 |
| a pinned piece present | 171 / 2,000 |

**A green result over 19 promotions says almost nothing about promotion handling.** So the fuzz was extended with
**four targeted 500-position families, each carrying a predicate that proves the edge was live** — the underpromotion
row verifies "only the knight gives check" by **pushing each promotion and querying `board.is_check()`**, not by
asserting it. **That is the difference between "we ran 5,000 positions" and "we reached the branches": a coverage
count per edge, computed rather than assumed.**

### And the OTHER movegen clean bill has a scope limit — state it, or it reads as complete

**A separate result — 353 positions × 2 builds = 706 comparisons, 0 parser mismatches, 0 movegen disagreements with an
independent generator — is a clean bill for move generation EXCLUDING en passant.** That is not a hedge; it is a
measurement about the population:

> **Zero of the 353 `set_G` positions carry an ep square at all** — checked rather than assumed.

**So the population never exercised the ep edge, even where the code preserved it.** "353 of 353 agreed" reads as
complete coverage and is not: **en passant is covered by the four targeted 500-position families above, and by
nothing else in the run.** The two results complement each other; **neither implies the other**, and a summary that
quotes only the 353 can be read as claiming something the run did not test.

**This is the same distinction as §7e's coverage table, at the level of a whole result rather than one edge** — and
it is the sharper instance, because 353 of 353 sounds like a universal while 19 of 2,000 does not.

---

## 8. How this document was assembled

- **Read in full:** `docs/forge-findings.md` (re-read after each of your revisions — nine of them) and
  `internal/swarm/tally.md`.
- **Read:** the `FINDINGS.md` of all **30** finding-bearing branches, plus **every other `.md` and `.txt`** under
  `forge-combo29/swarm/NN/` for those seats — **167 MB** of branch content in total. The `.txt` half was added late
  and it is what resolved the book-soundness figures (§5).
- **Branches with no `FINDINGS.md`, not counted as findings:** `swarm-09, 14, 18, 22, 26, 31, 33, 34, 37–42, 47, 48,
  51–53, 55–58, 60–62, 70`, plus the non-`swarm-NN` branches. **`swarm-65` ships evidence and scripts but no
  `FINDINGS.md`** — so its material is cited from `evidence/*.txt`, which is also why the `.txt` widening mattered.
  **`swarm-69` gained a `FINDINGS.md` late in the run** and supplies the determinism, reuse-trap and cross-build
  material in §7c and §4.
- **`git fetch --all` was run five times.** Corrections and whole branches landed *after* preceding fetches —
  the softnodes scope run, the v3 pair-count patch result, the arithmetic note, **and `swarm-64` in full**. **A summary
  assembled from a live swarm is a snapshot**; the tips are named in the header and **the §5 count is a statement
  about those commits, not about the documents.**
- **Nothing was run.** No engine invocation, no script execution, no re-measurement. Where a figure is quoted, it is
  quoted from a branch, its evidence files, or the tally, with that source's conditions.
- **No other seat's branch was modified.** `swarm-27` `S-C88` is stale (§6.3) and was left alone, at the coordinator's
  direction, for the owning seat to amend.
- **Counts printed as literals, re-derived from the branch files at the tips named in the header:** **31** branches with a `FINDINGS.md` (of 63 `swarm-NN` branches), **2,380** distinct findings,
  **9** unsourced figures from **284** numeric tokens, **7** mis-pairings or contradictions found, **3** sourcing
  defects of which **2 are now fixed upstream**.

**What I could not source, summarised: 9 figures.**

The number you need for the coordinator's tally:

> **Unsourced figures: 9** — of **284** distinct numeric tokens, against the tips named in the header. **Four
> causes, and one of them is new and more serious than the others:**
> **(a) three book-latency percentiles** (`0.024`, `0.44`, `442`) — `swarm-65` ships the script that would produce
> them and **commits no output file**;
> **(b) two book-soundness figures** — `929` has **no committed occurrence**, and `42` is **contradicted** (the
> evidence gives a 66 cp noise floor);
> **(c) `40 of 40` at 2,000,000 nodes** — `swarm-69`'s committed Hash sweep **stops at 1,000,000**, where the same
> comparison already differs 24 of 24, so the 2M row adds nothing;
> **(d) THE SHIPPABILITY COUNT** — `0 of 125`, `13 of 13`, `220–280 ns` and `13,707` all have **no committed
> occurrence**, and these are the numbers that license the run's headline **SHIP** verdict in §1.2.
> **`13.2 %` and `54,379` came OFF the list in later rounds** — `swarm-27`'s `S-C108` and `swarm-71` now carry them,
> so both were timing artefacts of earlier fetches, not defects in the report.
> **My token instrument can see only the first three**: the rest are bare integers or differently-formatted numbers
> outside its four patterns, and **came from reading** (§5).

**About (d), stated plainly rather than buried:** the adversarial-family results, the near-miss set and the 16
node-identity observations behind §1.2 **are** sourced, so the verdict's direction is supported. **What is
report-only is the specific claim that the scan fires on drawn roots only** — the count that answers the shippability
question. **Re-measuring that count on your build is the check that converts it**, and it is cheap: the same 125
non-drawn and 13 drawn roots, timing the scan.

**And the six I reported unsourced in earlier rounds were all sourced** — `swarm-64` had not landed, then `swarm-27`
moved, then `swarm-71` did. **My errors, recorded rather than deleted.** **That has now happened three times, which is
why the header names commits rather than a timestamp** — a bare count against a live swarm is a claim about the
fetch, not about the document.

**Separately, 3 sourcing defects** — of which **2 are now fixed upstream**. **Their disposition as it now stands:**
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

**And 2 book-soundness figures that are mis-paired or contradicted (§6.5):** `929` (no committed occurrence) and
`42` (the committed evidence gives a **66 cp** noise floor, and the report states the smaller one). **Both point in
the direction that flatters the finding** — the `929` makes the checker's initial failure sound worse, the `42` makes
the noise floor sound smaller. **In the `42` case the honest number strengthens the argument**, since a 66 cp floor
makes the 103 cp maximum easier to call a horizon artefact, and `noise_floor.txt` reports `0 of 111` above 100 cp
directly.
