# FINDINGS — seat 07, area 7: FINAL BLOCK (2026-11-17T09:40Z target; written 2026-11-17T09:35Z)

Seat 07, branch `for-fable-and-opus/swarm-07`, folder `forge-combo29/swarm/07/`. Every figure below is
Threads 1 unless a line says otherwise. Two builds were used throughout:

- **base** = commit `6b98f217`, GCC 13.3.0, plain CMake Release, `-march=x86-64-v4`.
- **PC r15** = base + `pc_r15.patch` from `FABLE_TO_swarm_5.md` (sha256 `d6bd72c5…`, applied in a
  separate worktree, `-DFORGE_MATE_ALPHA_GUARD=1`). All eight published PC numbers verified (07-C21).

Settings are named per line: **none** (no setoption), **S14** (the 14 settings of file 1), **PC20**
(S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook
false).

---

## Real findings, with state

| id | finding | state | build / settings |
|---|---|---|---|
| **07-F1** | `searchmoves` naming no legal root move, on a board that HAS legal moves, prints one fabricated `info depth D … score cp 0 nodes 0` line **per depth** (64 of them with no depth limit) and then `bestmove 0000`. The engine already computes the true cause at `search.cpp:2531` (`restricted_root_empty`). | **CONFIRMED by seat 10 (10-C15) with its own harness**, and by seat 17 as S-F1/S-F8 (independent observation, same defect). **Still present on the PC build** — not repaired. A 3-edit PC-tree text patch cures it with every pin unchanged (07-C23). | base and PC r15; **none, S14 and PC20**; Threads 1. |
| **07-F3** | On the **base** tree a fifty-move root with a counter-resetting move available is declared a draw **without being searched** (`cp 0`, **0 nodes**, 12 fabricated depth lines) while a forced mate exists. Example `8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1`: base `cp 0`/0 nodes vs PC **`mate 6`**/15,981 nodes. | **OPEN** (no independent confirmation yet). This is the `FORGE_FIX_ROOT_DRAWN` defect in the act; the PC build gets it right. | base and PC r15; **none**; Threads 1. |
| **07-F4** | The base tree declares a draw on **all 20** fifty-move-counter-100 positions in the targeted sample (0 nodes each), and the counter-reset reference shows a **decisive** result on 5 of 20 — **4 losses masked, 1 win thrown away**. | **OPEN**. Rate **settled at depth 30** (07-C39): no position changed category between depth 18 and 30. | base; **none**; Threads 1; reference depth 18/24/30. |

### Withdrawn claims of my own (kept visible)

| id | what I claimed | why withdrawn |
|---|---|---|
| **07-R1** | search.cpp:2640 read `front()` of an empty `MoveList` (UB). | The early return at 2253 fires first; a two-branch marker build proved 2640 never sees an empty root. **This build also settled the three-seat contradiction (07-C2).** |
| **07-R2** | `LmrSignedCorrection` is dead code (bound ±32 cp, so `/64` is always 0). | `corrected_eval` **sums three** correction tables, so the bound is ±96 cp, not ±32. The repo's own `REPORT_r3_03.md` documents the option and the deliberate `/8 → /64` change. **Do not re-open.** |
| (intermediate) | "19 of 20 fifty-move positions are base errors (95 %)." | Conflated `cp −1601` with "a win exists". Corrected to 6/20 at depth 12, then **5/20 at depth 18–30** (07-C38/C39). |
| (intermediate) | "PC20's saving is two options cancelling." | The 40-position table had three of six options with the wrong sign. At 200 positions `TtPruneV2` alone is 85 % of the effect (07-C32). |

---

## Checks and confirmations (C-series), with build and settings

| id | result | build / settings |
|---|---|---|
| 07-C1 | REFUTES 17-S-F2's cause (no empty `front()`); symptom of 17-S-F1 real | base, none |
| 07-C2 | **Settles 01 vs 07 on search.cpp:2640**: 2640 is never reached with an empty root (both-branch markers) | base, none |
| 07-C3 | O depth 12 = **9,500,069** exact | base, **S14** |
| 07-C4 | G depth 12 = **18,466,239** exact | base, **S14** |
| 07-C5 | `go`/`stop` GUI cycle clean, 40 plies (after I fixed a blind test) | base, none |
| 07-C6 | O depth 14 = **21,812,100** exact | base, **S14** |
| 07-C7 | Clock: 9 controls, 0 overruns, 0 illegal; **book answers clock searches with no depth line** | base, none |
| 07-C8 | G depth 14 = **43,345,893** exact — all four published sums reproduced | base, **S14** |
| 07-C9 | `eval` is exactly colour-symmetric; **it is side-to-move-relative** (eval(P) == eval(mirror P)) | base, none |
| 07-C10 | Inline legality shortcut correct on 289,809 moves; control must be planted in **board.hpp** | base, none |
| 07-C11 | `gives_check` correct on 260,053 moves (header-planted control catches 3,999) | base, none |
| 07-C12 | TT invariants held; a header fault needs **every dependent TU recompiled** | base, none |
| 07-C13 | Shipped TT path (`TT_NOTLS=1` is the default) is pin-verified | base, none |
| 07-C14 | Book moves always legal (16 book plies); first control was inconclusive | base, none |
| 07-C15 | SEE oracle rebuilt and **validated against 5 hand-settled cases**; 150 positions clean | base, none |
| 07-C16 | Time-manager properties hold under UBSan (3 void controls before one fired) | base, none |
| 07-C17 | Increment-heavy clock never loses on time; 0.796 max share recorded as behaviour | base, none |
| 07-C18 | 07-F1 re-verified on a fresh build; patch still applies `--fuzz=0` | base, none |
| 07-C19 | **CONFIRMS 27-S-F7** on 82 options / 437 cases, both bug classes controlled | base, none |
| 07-C20 | `NonPawnCorrection` takes effect (56,720 → 33,066 nodes); matches seat 10's cold figure | base, none |
| 07-C21 | **PC r15 built; all 8 published numbers exact** in none/S14/PC20 | PC r15 |
| 07-C22 | The three reported symptoms are **two paths** (empty root vs abort fallback) | PC r15, PC20 |
| 07-C23 | **PC-tree patch cures 07-F1 on r15**, all 8 pins unchanged, controls identical | PC r15, PC20 |
| 07-C24 | `bestmove 0000` design answer: A/B/C/D measured, **recommend B**, written into the patch header | PC r15, PC20 |
| 07-C25 | One-candidate legal restriction searches normally (boundary is emptiness, not size) | base + PC r15, both regimes |
| 07-C26 | **PC20 baseline 8,315,168** with per-position digests, reproducibility proven | PC r15, PC20 |
| 07-C27 | All seven board-level checks hold on the PC tree | PC r15 |
| 07-C28 | PC20 vs S14 per position: **200/200 node counts change**, 60/200 bestmoves, 195/200 scores | both, both regimes |
| 07-C29 | The one unexplained base-vs-PC difference is **BARE_KING_LMR_CAP**, and the PC answer is better | both, none |
| 07-C30 | Four legs: **PC+S14 == base+S14 == 9,500,069**; the delta is an **interaction**, not a split | both, S14 + PC20 |
| 07-C31 | 40-position option table — **superseded by 07-C32** | PC r15, S14 + one option |
| 07-C32 | **200-position option table: TtPruneV2 = −1,002,190 = 85 % of PC20's effect**; CorrHistV2 +251,935; corrects 07-C31 | PC r15, S14 + one option |
| 07-C33 | 100-position differential = **0 differences**, with a proven control | both, none |
| 07-C34 | **Where the patch acts: targeted 50/100 differ (30 bare-king, 19 root-drawn), ordinary 0/100** | both, none |
| 07-C35 | The targeted differential shows **base failing** where PC succeeds | both, none |
| 07-C36 | **No bare-king regression** in 30; the 7 "worse" cases are all closer to depth-18 truth | both, none |
| 07-C37 | No mate-distance lengthening in this sample (base reports no mate at all) | both, none |
| 07-C38 | Fifty-move rate **tightened to 5/20**, one depth-12 artefact removed | base, none |
| 07-C39 | **Rate settled at depth 30**: 0 of 6 changed category | base, none |

---

## The four things I would put in front of the owner

1. **07-F1 is the only engine defect I found that survives on the PC build**, it is confirmed by another
   seat, and it has a ready patch that changes no node count on any published bench (07-C23, 07-C24).
   Recommendation: ship the "honest `0000`" form; if a playable move is wanted instead, that is a
   separate decision that must print that the restriction was ignored. **Note added later (07-C54,
   07-C55): it is not a `searchmoves` defect at all** — every path that reports without searching emits
   a fabricated `score cp 0 nodes 0` line per depth. The shared-path patch
   (`job55/shared_report_oneline.patch.txt`) fixes all six paths with one edit, all eight pins unchanged,
   and **supersedes my own narrower `job2`/`job29` patches.**
2. **`TtPruneV2` carries 85 % of PC20's node effect** on 200 positions (07-C32), while `CorrHistV2`
   costs 2.7 %. Whether that saving is strength is a games question I did not measure.
3. **`FORGE_FIX_ROOT_DRAWN` buys one game-losing outcome in twenty** on the fifty-move sample
   (07-F4/07-C38/07-C39, settled at depth 30) — narrower than two of my earlier figures, and it is the
   number I stand behind.
4. **DO NOT PLAY A ZERO-INCREMENT TIME CONTROL.** The clock floor that protects the engine is
   `MoveOverhead + increment · 100/TmHardPercent` = `10 + increment · 5/3` ms (28-S-F44, reproduced
   exactly in 07-C57). At the owner's `6 s + 0.06` that is **111 ms**, and I verified the engine's real
   spend falls *inside* the 60 ms increment once the clock drains, so it is safe. **But at `winc 0` the
   formula gives a floor of about 10 ms, i.e. `Move Overhead` alone — there is no margin and nothing
   protects the engine from flagging.** Every clock control I ran with an increment had zero overruns
   (07-C7); that safety comes *from* the increment, not from the clock path.

## Audit method: how to check a seat's scope without raising a phantom alarm

My STATUS corruption (an 84,000-line `git diff` injected by a backtick in a shell echo) was **real**,
and the handling that caught it was mechanical: check the file's line count and tail immediately after
writing, rebuild from the known-good prefix, verify no stray diff markers remain, re-check that the
status headers survived, and push the repair as its own commit so corruption and fix both stay visible.

But the *same class of alarm* is easy to raise falsely, and another seat has now shown why: **in a
shallow clone, `git show` on a seat's first commit prints the entire tree as added**, so it reports tens
of thousands of files and millions of insertions that are not that seat's work at all. Anyone auditing
scope that way will "find" a catastrophic breach in every seat, including innocent ones.

**The correct audit is a diff against the base commit, excluding the seat's own folder:**

    git diff 6b98f217 <tip> -- . ':(exclude)forge-combo29/swarm/<NN>'

If that prints nothing, the seat committed only its own files. I ran exactly this on my own branch and
it is empty, which is the claim worth quoting — not a file count.

## The sixteen standing rules, grouped by the question they answer

The FINDINGS header carries sixteen rules; the table there is ordered by when I learned them, which is
the wrong order to read them in. Grouped by what they are for:

### Is the thing I am measuring actually the thing I meant to measure?

- **If the answer does not belong to the position, the position was not accepted.** The engine refuses an
  invalid FEN and keeps the previous board, so a move that could not occur on your board means your board
  was rejected. (Caught me with `e2e4` on a position holding a lone black king on h8.)
- **Assert your harness settings explicitly and record them: `Threads 1`, `MultiPV 1`, `OwnBook false`.**
  `MultiPV 2` silently costs 3 plies on startpos at `go nodes 20000`, with no error and a plausible node
  count.
- **A fabricated-move check needs a position where the engine's first move is not alphabetically first.**
  startpos: both `a2a3`, blind. **kiwipete**: engine `a2a3`, alphabetical `a1b1`, discriminating.
- **A deep search on a high-halfmove-counter position needs a node budget or a timeout.** An untimed
  `go depth 20` there can take ~250 M nodes and look hung.

### Is this number reproducible at all?

- **A node count under a clock stop is not reproducible until you prove it is.** Repeat the same cell on
  the same binary first; mine gave 412 nodes once and 971 on five other runs.
- **A small-sample rate does not order anything.** Two disjoint 100-position samples flipped a budget
  ordering ten points apart; 353 positions showed it was nothing.
- **Read a clock result by its move and wall time, not its node count.** Node *stops* are deterministic
  (16/16 cells exact); node counts under a clock are not.

### Is my comparison right?

- **When my summary line and my raw data disagree, believe the data.** Caught three wrong verdicts; each
  was a wrong comparison, and a summary is a second implementation that gets less review.
- **If a defect should vanish with more budget and it does not, suspect the checker** — and if it does
  vanish with more depth, it was a horizon artefact. One sweep decides which, in either direction.
- **Before calling someone's number wrong, run it on their own sample.** Mine put 29-F45 thirty points
  away and running *their* set reproduced it to the digit — the number was right and the generalisation
  was not.
- **For a side-to-move-relative score under a colour mirror, the invariant is equality, not negation.**
  The tell for a wrong checker: its "asymmetric" pairs share the same sign.
- **A damage table must exclude incomparable pairs.** `mate −12` against `cp −2196` is two losses;
  subtracting them invents ~9,800 cp of damage.

### Can anyone re-check what I claimed?

- **Regime plus binary is a complete citation; settings alone are half of one.** Nine of my own jobs
  cited settings with no `sha256` — the gap was in the record, not the work, and it is now closed in
  `job65/BINARY_PROVENANCE.md`.
- **A convenient listing is not the tool for the question you asked.** `git ls-files` cannot tell you what
  a branch contains; `git ls-tree -r --name-only origin/<branch>` can.
- **A warning from a harness that has not validated its own input is not a finding.** Five of my controls
  were blind until their own planted fault exposed them.

## Method debts I incurred, recorded so they are not repeated

Five of my controls were initially **blind** and each was caught by its own planted fault, not by me:
the go/stop cycle, the eval-symmetry relation, the SEE oracle, the option surface, and the UBSan
overflow (three attempts). A sixth lesson: a header-planted fault needs every dependent translation unit
recompiled (07-C12), and the legality shortcut lives in `board.hpp`, not `board.cpp` (07-C10). One
false warning I printed came from my own illegal test move, caught with python-chess.

> **A warning from a harness that has not validated its own input is not a finding.**

### Every number in this file was measured under zero machine load, and that is now proven rather than assumed

A loaded machine does not merely slow this engine down — at **full** saturation it searches a ply shallower
and its node count collapses (30-F64). I confirmed the threshold on my own 4-core box with CPU burners
(07-C65):

| busy processes | bestmove | depth | nodes |
|---|---|---|---|
| 0 | `a2a3` | 17 | **362,362** |
| 1 | `a2a3` | 17 | **362,362** |
| 2 | `a2a3` | 17 | **362,362** |
| **4** (all cores) | `a2a3` | **16** | **241,976** |

**0, 1 and 2 hogs are identical to the node; only full saturation costs a ply.** My box read `loadavg 0.10`
with zero `forge` processes whenever these measurements were taken, so **every figure in this file sits in
the 0-hog regime** — the regime this ladder shows is indistinguishable from the ideal. That is the
certification the night's numbers needed and, until this check, did not have.

### 100-position rates cannot order three budgets, or anything else that close

**Two disjoint 100-position samples disagreed about which budget is safest.** Seat 10 measured
`nodes 50000` agreeing with `nodes 250000` on 92/100 positions and recommended 50000 as the cheapest
safe budget; on the **last** 100 positions of the same set I measured **78/100**, with the 20000 budget
agreeing *better* (82/100) — the opposite ordering (07-C42).

Neither measurement is wrong. 24 disagreements against 19, in 100 positions, is well inside binomial
noise. **The lesson is that a rate of that size does not carry a ranking**: if two samples of 100 can
flip the order of two budgets ten percentage points apart, then no 100-position comparison should be
used to choose a default, and any such choice needs a sample large enough that the ordering is stable
under resampling.

This is the fourth number tonight that moved when I enlarged or changed the sample (the fifty-move rate
went 95 % → 30 % → 25 %; the PC20 option table had three of six signs flip between 40 and 200
positions). **The pattern is consistent: small samples produce confident orderings that do not survive
a different sample.** Report a rate with its sample size and say whether it orders anything.

### The mirror invariant, stated once so nobody pays for it again

**For a side-to-move-relative score under a colour mirror, the invariant is EQUALITY, not negation.**
`python-chess`'s `Board.mirror()` swaps colours *and* the side to move. This engine's `eval` and search
scores are reported from the side to move's point of view (07-C9; `src/eval.cpp:509`). So a +255
advantage for White becomes a +255 advantage for Black in the mirror — and Black is the side to move
there — which reads **+255**, not −255.

**The tell that catches a wrong checker:** if the pairs it calls "asymmetric" have the **same sign**
(`orig cp −304` against `mirror cp −301`), the checker is using negation and is wrong. A genuine
asymmetry shows as a gap *within one sign* or as a sign change under equality.

My first version of 07-C41 used negation and reported 4 of 120 pairs symmetric; the correct invariant
gave 7 of 120, and 25 of the first 40 pairs it had failed were carrying the *correct mirrored move*.
This is the trap seat 16 documented in its own C5 ("a negation-based symmetry checker would report a
false 8422 cp difference per position") — **I walked into a trap another seat had already written
down**, which is the strongest argument for reading the other seats' checks before writing one.


## Times

`git log` on the branch; each job's `stamps.txt`.
