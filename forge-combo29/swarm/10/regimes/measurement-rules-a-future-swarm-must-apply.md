# measurement-rules-a-future-swarm-must-apply.md

Every rule below was learned by measurement tonight, and most of them by catching my own error. Read this
before trusting any number from this run, including mine. **Each line: the rule, then the case that taught it.**

Where a rule came from a mistake, the mistake is named. None of these is advice about style; each one, broken,
produced a plausible number that was wrong.

---

## 1. A cold baseline is a FRESH PROCESS or `ucinewgame`. Never `Clear Hash`.

Two identical unrestricted searches in one process: **56,720 then 4,951 nodes**; a third gave 4,516. Three
separate processes: 56,720 every time. `ucinewgame` restores the cold value exactly; **`Clear Hash` gives a
third number** (40,569 on the base tree, and on PC20 it comes out *above* cold at 24,708 vs 21,600), so it is
neither cold nor warm. Told by: my own K14 control (10-F21, 10-F22) — I had used `Clear Hash` as an "empty
table" control and had to retract that reasoning (10-R3). Repeated on the PC build: still true (10-F23/10-F24).

**Consequence:** any table built by repeated searches in one process is a warm-state table and its node counts
are not comparable to the brief's cold sums. Most of the swarm's harnesses ran many searches per process.

## 2. Threads 1 for every score, unless the job is about threading.

On the PC build, one lost position, Threads 4: **+2576, mate 13, mate 18, mate 16 in four runs**, nodes 5.0M to
31.4M. Threads 1: **+2207 four times, identical nodes** (seat 04). Move choice was stable, scores were not.
Told by: seat 04's broadcast, applied retroactively to my own record (every score I report is Threads 1; the
non-1 rows in my folder are deliberate out-of-range probes and one area-4 report-count run).

**Go straight to the raw data:** `forge-combo29/swarm/04/job1/table_threads.md` (branch
`for-fable-and-opus/swarm-04`), row **threads = 1 vs threads = 4** on the hang FEN
`5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1`, depth 12, S14, every run a fresh process: Threads 1 gives
**identical 79,980 nodes** across 10 runs in 0.03 s, Threads 4 spreads **2,739,824 to 1,252,499,786 nodes**
with a 69.30 s worst case. The score spread itself is record **04-F9** in that branch's `FINDINGS.md`
(+2576 / mate 13 / mate 18 / mate 16 in four Threads-4 runs vs +2207 four times at Threads 1).

## 3. The honesty pins are DEFAULT-option numbers; the position-set sums are S14 numbers.

All four pins hold only with **no setoption at all** (312866 / 862329 / 3024920 / 4865609). With the brief's
own S14 applied first they become 242796 / 656517 / 2155620 (perft 5 unchanged). Conversely all four big sums
match **only** under S14 (O d12 9,500,069, O d14 21,812,100, G d12 18,466,239, G d14 43,345,893 — all exact,
plus O's first three 41,311 / 24,872 / 28,574). Told by: my audit rows K6 and K13 (10-F6, 10-F10, 10-F12).
**A harness using one regime for both sees a false mismatch on three pins and every sum.**

Two independent builds of the same source were **bit-identical** (sha256 `e06310ec…`), so a differing pin
cannot be blamed on the compiler or build directory (10-F7).

## 4. An exit code of 0 with empty output is not a result.

`is_unfinished.py` on a file with no `bestmove` and no `info` returns success having judged nothing; a
comparison harness that reads a missing key gets `undefined`/`None` and compares it as if it were a number.
Told by: seat 19's `clock_plan` case (searched for a line the engine never prints, compared nothing, printed
CONFIRMS) and seat 23's integrity rule. My own version: a K14 attempt parsed `info ... nodes` from a build that
prints no such line for a piped search, got `None`, and the run died rather than reporting — the failure mode.

**Rule:** assert the parse FOUND its number before using it, and let a missing number stay `None`, which no
equality test accepts.

## 5. A control must be shown to FAIL on an input known to be wrong.

A control that passes for the wrong reason is worse than no control, because it certifies the bad result.
Cases tonight, all mine or mine-adjacent: `Clear Hash` used as an "empty table" control when it does not empty
the table (10-R3); an EOF-aborted search read as a real answer (10-R4); a "0 sanitizer reports" run whose
harness discarded stderr, which makes zero **guaranteed** for any build including one with a planted race
(10-F16 — with stderr captured the planted race gave 6 reports, exit 66). Told by: seat 19's warning, seat 30's
6–11-line window, and my own three failures. Named as a pattern in 10-N2.

**Rule:** plant the fault, run the same runner unchanged, show it counted. A zero without a planted case is
"not shown", even when it is true.

**Go straight to the raw data, both halves of one experiment:** `forge-combo29/swarm/10/audit/raw2/K5/summary.json`
is my FIRST attempt — `"proof1_nm_tsan_gt_0": true, "proof2_planted_reported_by_same_runner": false` — the
harness that discarded stderr and therefore could never have counted the planted race. The corrected run
`forge-combo29/swarm/10/audit/raw2/K5/summary_direct.json` and
`forge-combo29/swarm/10/audit/raw2/K5/proof_planted_direct.json` are the same runner with stderr captured:
**6 sanitizer reports, exit 66** on the planted build, then 0 reports on 50 real searches at Threads 2 and 4.
Two files, same harness, opposite verdicts — that is what "the control must be able to fail" looks like.

## 6. R1 (unfinished detection) has no conditions; R2 requires a depth target.

**R1: a record is UNFINISHED iff its last `info depth` is less than the requested depth** — plus "a `bestmove`
with zero `info` lines" as a second clause. Measured: 90 of 90 truncated records caught, **0 false alarms** on
19 records that were identical to a finished search.

**R2** ("last depth < the largest depth in this file") works only when **every search in the file had a depth
target**. On the repository's `go nodes 2000` file it flagged **8,235 of 8,292 records — a 99 % false-alarm
rate**, the signature of an invalid reference. Node-budget, clock and soft-node logs need the **budget**
recorded and tested against instead. Told by: my own sweep, then my own near-miss — I had reported "0 false
alarms" from a sample that happened to contain only depth-target files and had to qualify it (10-R5, 10-F40).
The checker now **enforces** the scope (10-F43).

## 7. `cp 0` is classified by the PV, never by a node threshold.

**Empty pv + 0 nodes = ROOT SHORTCUT** (no search happened). **Non-empty pv = FIFTY-MOVE HORIZON**, at any node
count, and the position is often *won* (cp +472 at halfmove 0 on the board that reads `cp 0` at halfmove 91).
Told by: a threshold I proposed myself ("nodes above ~10,000") and then measured **wrong on 6 of 6** horizon
records, which carried only 200–793 nodes (10-F46, 10-R6). My 13.8M-node case was the *expensive* horizon, not
the typical one. `regimes/classify_cp0.py` applies the PV test.

## 8. Never interrupt a search and believe the answer.

Closing stdin (or sending `quit`) during a search makes the engine print a **fabricated** `bestmove`: at ≤25 ms
a legal move with **no score at all** (on a mate-in-1 board: `f2f3` instead of the mating `a1a8`); in the middle
band a legal move with a **wrong score up to 53 cp**; full agreement only from 35–50 ms, **which is
position-dependent**. Told by: seat 19's 19-F12 (which I reproduced), seat 30's 30-F22/30-F23, my 10-C5,
10-C12, 10-C13, 10-F30/31/32. **Both builds are affected**, so the owner's training loop is exposed.
**Rule:** read stdout to `bestmove` before sending anything; there is no safe timeout.

## 9. A count that equals a famous count means "check whether the input was refused".

8,902 is startpos perft 3. An "impossible-castling FEN accepted, perft 3 8,902" turned out to be that FEN
**refused** with the stale startpos left on the board. Told by: seat 21's 21-F1, confirmed by me (10-C4), and
adopted into the brief's own corrections.

## 10. `ucinewgame` AFTER `position` resets the board to startpos.

The brief's literal wording ("`ucinewgame` + `isready` before every `go`") applied after the position command
makes every search measure **startpos**. Proof: after `position fen <G>` the eval is `total -351` and
`go perft 1` = 38; after a following `ucinewgame`, `total 38` and perft 1 = **20**. Tell-tale: every position
returns an **identical node count**. Correct order: `ucinewgame`, then `position`, then `go`. Told by: my own
first sums run, which produced 4,491,800 instead of 9,500,069 (10-F11).

## 11. A profiler's rank survives a change of instrument; its percentages do not.

`perf` cannot work in this image (no kernel-matched `linux-tools` for 6.12.113+). `gprof` on a `-pg` build
confirmed the **order** of the evaluation-cost findings (`evaluate_position` first at 21.24 %, the net family
17.26 %, `see_ge` ≈ all move generation) but inflates small functions, so its absolute shares are not
comparable to perf's. Told by: 10-N1, 10-C8/9/10. **Rule:** confirm rank, never a percentage, when the
instrument differs.

## 12. A rule about the engine may hold only on the machine it was measured on.

File 2's rule "evaluation work is worth nothing on the PC" is true **only when a v3 net is loaded**
(`nnue_v3.hpp:158` is `requested && loaded()`). With no net file — our situation, the net is not shared — the PC
build still spends **21.51 %** in `evaluate_position`, the same as base. Told by: my 10-C11. **Rule:** state
the configuration a result belongs to, or it will be applied where it is false.

**Go straight to the raw data:** the two gprof flat profiles sit side by side —
`forge-combo29/swarm/10/profile/gprof_flat_bench16x4.txt` (base build: `evaluate_position<false>` **21.24 %**
self, #1) and `forge-combo29/swarm/10/profile/pc_no_net/gprof_flat.txt` (PC r15 build, no v3 net:
**21.51 %** self, #1). Same shape, different build — and the source condition is one line,
`include/forge/nnue_v3.hpp:158`: `active() { return requested && loaded() != nullptr; }`, which is what makes
file 2's "evaluation is worthless on the PC" true there and false here.

## 13. Two builds, always, for any defect claim.

Every find of mine was re-run on the PC build under PC20. Most survived (warm state, `ucinewgame` reset,
`Clear Hash`), but 10-F14's score difference **reversed sign** and the drawn-root defect is **repaired** there.
Told by: `pc/REPORT_pc_recheck.md`, 10-F23..F27. **A finding that is still present on the PC build is worth
much more than one that is only on base.**

## 14. Record the node budget with every self-play record; never mix budgets in one set.

The engine plays a **different move** at different node budgets: on 100 G positions, `softnodes 20000` and
`nodes 250000` disagree on **17**, `softnodes 50000` and `nodes 250000` on **8**, and all three agree on only
**81 of 100**. The median disagreement is **52 cp** (max 218), and on **2 of 100** positions the small budget's
choice is **≥200 cp worse by the engine's own evaluation at the large budget**. Told by: 10-F53/10-F54.

**Operational rule, one line: record the budget, never mix budgets, and prefer 50,000 if one must be chosen
(92/100 agreement with 250,000, versus 83/100 for 20,000).**

The bad cases are undetectable from the small-budget record itself — its move is legal and its score looks
normal; the score is simply unconverged, and only a deeper re-search of that same move reveals it (10-F55).
So this is discipline, not a filter.

---

## The three sentences to carry forward

1. **A number is not a measurement until you have shown the thing that produced it can fail.**
2. **State the build, the settings, and the thread count, or the number is not comparable to anything.**
3. **When a number agrees with a famous number, suspect the input was refused before you believe the result.**
4. **Record the budget, never mix budgets, prefer 50,000 — different budgets are different players.**

Written by seat 10 (area 10) at the end of the run. Every case is reproducible from
`forge-combo29/swarm/10/` — findings 10-F1..F46, retractions 10-R1..R6, method notes 10-N1..N2, and checks
10-C1..C17.
