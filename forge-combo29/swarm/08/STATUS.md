# STATUS — seat 08

seat 08
branch for-fable-and-opus/swarm-08
area 8 (THE CLOCK)
seed 801

## 2026-11-16T21:05Z (start)

Assigned by brief.md. Next: create folder files, STATUS block, push, then STEP 2 engine build.

## next command

    cd /agent/repos/dwqww && S=$(cat ~/swarm_seat.txt) && git worktree add ../base 6b98f2170a3210e71beed04bbd2553972c253ed7

## 2026-11-16T21:22Z
- STEP 2 done: release build of 6b98f217, all four honesty numbers exact (312866 / 862329 / 3024920 / 4865609).
  HONESTY.txt pushed (id name corrected to "Chess Engine Forge 6.4.24 candidate").
- AREA 8 job 1 DONE: 1,000 timed searches (2 x 200 movetime 50 baseline, 200 movetime 500, 200 x wtime 1000 inc10,
  200 x wtime 10000 inc100), 200 positions = first 100 O + first 100 G. REPORT_job1.md pushed.
- Findings 08-F1..08-F4 written to FINDINGS.md (clock tail 5x median past own soft limit; movetime minus
  Move Overhead; a book move inside the timing set; baseline repeatability 0.11 %).
- R set: job1/R_seed801.fens, 500 positions, seed 801.

### next: board read, then whichever comes first — a NEW unconfirmed finding to check, else AREA 8 job 2
exact next command:

    cd /agent/repos/dwqww && git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*/swarm-##' | sort -n | tr '\n' ' '

## 2026-11-16T21:26Z
- Checked seat 06's S-F4 (left-right flip eval): **CONFIRMS** — 08-C1, 453 positions. My own harness.
- AREA 8 job 2 DONE: 2,000 searches at wtime 100/30/10/1/0 x winc 0/10, clean guarded run.
  Findings 08-F5 (reserve-empty = 1-ply 2000-node emergency search, inc does not lift it), 08-F6 (1 ms hard
  limit overrun at wtime 30), 08-F7 (0 of 2,000 ever exceeded the clock, 0 illegal bestmoves).
- INCIDENT DISCLOSED: my first run_job1.sh (hung on a uci/readyok bug) stayed alive and re-ran concurrently
  during the first job-1 and job-2 measurements. Both first sets are kept at job*/raw/ and are NOT used.
  Everything reported uses job1/raw2 and job2/raw2 from run_clean.sh, which refuses to start unless no other
  engine process exists and loadavg < 0.5. Contamination moved medians 0.1-15.1 ms (job1/raw2/contamination_table.txt).
- Also corrected an earlier wrong HONESTY.txt `id name` line.

### next: board read for an unconfirmed NEW finding, else AREA 8 job 3 (movestogo)
exact next command:

    cd /agent/repos/dwqww && for s in $(git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*/swarm-##' | sort -n); do git fetch -q --depth 1 origin "for-fable-and-opus/swarm-$s" 2>/dev/null; git show FETCH_HEAD:forge-combo29/swarm/$s/FINDINGS.md 2>/dev/null | grep -E '\| *[A-Za-z0-9]*-C[0-9]* *\|' | sed "s/^/S$s /"; done

## 2026-11-16T21:32Z
- Checked seat 27's S-F2: **CONFIRMS** (08-C2), and went beyond it — the 26-node dead zone is startpos-only;
  the smallest N printing an info line is 155 on a 51-move position and 394 on kiwipete.
- AREA 8 job 3 DONE: movestogo 1/2/40 at wtime 1000 + same-session control, 800 searches.
  08-F8 (22 of 400 searches at movestogo 1/2 land on the 792 ms hard limit, overshoot ~0.8 ms fixed;
  0 of 800 ever exceeded the 1000 ms clock, 0 illegal moves), 08-F9 (engine spends only 55-79 % of its own
  planned soft limit because of the per-iteration `factor`).
- ALL THREE AREA 8 JOBS DONE (job1 REPORT_job1.md, job2 REPORT_job2.md, job3 REPORT_job3.md).
- 9 findings (08-F1..F9) and 2 checks (08-C1 CONFIRMS seat06 F4, 08-C2 CONFIRMS seat27 F2).

### next: AREA 8 job 1 AGAIN with SEED 811 and a new R set (brief cycle step 2c); say what differs from run 1
exact next command:

    cd /agent/repos/dwqww/forge-combo29/swarm/08/job1b && python3 ../job1/gen_R.py 811 500 R_seed811.fens

## 2026-11-16T21:35Z — HARNESS AUDIT after seat 19's 19-F12 broadcast (fabricated bestmove from piped quit)

Coordinator told every seat to check harnesses for `quit`/stdin-close during a search. I checked all of mine.

**Reproduced the bug on my build** (so the audit is not theoretical):
`{ uci; …; position startpos; go depth 12; quit; } | forge` -> `bestmove a2a3`, 0 info lines.
Same search, `quit` 2 s later -> `info depth 12 … nodes 56720`, `bestmove e2e4`. Matches seat 19 exactly.

**Verdict on my recorded results: CLEAN.** `audit_fabricated.py` reads every committed timing file and checks
the `nlines` field (stdout lines read between `go` and `bestmove`): 38 files, 7,000+ records, **minimum nlines
= 2 everywhere** — a fabricated answer would be 1 (bare `bestmove`). No record is a2a3-with-no-info.
Root cause it is clean: `clock_latency.py`/`clock_latency2.py` block in `read_until("bestmove")` before sending
anything, and `close()` only sends `quit` after the loop. Honesty `bench`/`perft 5` are synchronous commands and
give identical numbers under an immediate piped `quit` (checked both ways).

**One real defect found and fixed:** `job2/probe_reserve.sh` piped `isready\nquit` right after `go`. Its output
is now `job2/probe_reserve_v1_INVALID.txt` and the script is rewritten to read until `bestmove` first. The
claim it supported (08-F5) is NOT based on it: 08-F5 rests on `probe_no_clock.py` and the raw timing files,
both of which wait for bestmove. Re-running the corrected probe.

Not reporting the bug as my own finding — it is seat 19's.

## 2026-11-16T21:36Z — in progress
job1b (AREA 8 job 1 AGAIN, SEED 811, OwnBook false) is running: OG_baseA and OG_baseB done (200 each),
OG_mt500 partway. Partial output pushed with this block, run continues.

next command:

    cd /agent/repos/dwqww/forge-combo29/swarm/08/job1b && cat run.log | grep -v '^{' | tail -3

## 2026-11-16T21:37Z — CHECKPOINT PUSH (owner deadline: findings on GitHub by 22:30)
Everything complete is already pushed. FINDINGS.md holds 9 findings (08-F1..F9) and 2 checks
(08-C1 CONFIRMS seat 06 S-F4, 08-C2 CONFIRMS seat 27 S-F2). All raw job files for job1/job2/job3 are pushed.
No patch files exist in this seat: AREA 8 is measurement, and I wrote no engine patch (nothing to push).
job1b (job 1 again, SEED 811, OwnBook false) is mid-run: 200+200+200+200 done, OG_tc10000 partway; its partial
raw is in this push. It will be analysed and pushed when it finishes, well before 22:30.

next command:

    cd /agent/repos/dwqww/forge-combo29/swarm/08/job1b && cat run.log | grep -v '^{' | tail -3

## 2026-11-16T21:38Z — CHECK AUDIT after seat 19's measurement-integrity warning

Re-audited both CONFIRMS checks for the vacuous-pass failure seat 19 found in their own check (parser found no
line -> NaN -> printed "CONFIRMS" without measuring anything).

**check_s06f4.py (08-C1, seat 06 S-F4)** — already failed loudly on a missing `eval` line (`raise RuntimeError`),
but its two CONTROLS were only PRINTED, not enforced: a stable-but-zero reader could still have passed. Now:
control 1 (same position twice) and control 2 (a moved pawn must differ) RAISE SystemExit if they fail, and a
third check aborts if every eval total is 0. Recorded result was never vacuous — the deltas are large real
numbers (median 20 cp, max 738 cp on a 2705-vs-1967 pair).

**check_s27f2.py (08-C2, seat 27 S-F2)** — had NO assertion at all. Now: control 1 (N=1 twice) must match,
control 2 (`go nodes 700000`) must print an info line AND must not give the same move as N=1, and the RESULT
block aborts if no N ever left a2a3 or never printed an info line on both sides of the boundary.

**Negative control proves the hardening works:** `negative_control.sh` runs check_s06f4.py against a fake engine
that answers readyok/uciok but prints no eval line -> exit code 1, "no eval line", no CONFIRMS.
(negative_control.txt)

Both CONFIRMS stand: neither depended on an absent line, and both now cannot pass without measuring.

## 2026-11-16T21:40Z — seat 16's REFUTES answered (08-F10 + restatements)
- job4 run: reconcile.py, movetime_undershoot.py, mtg_undershoot.py, ladder_test.py. Write-up
  reconcile_seat16_F2.md; new finding 08-F10; 08-F2 and 08-F9 restated planned vs achieved;
  audit_assumptions.md checks all nine findings for a hidden "plan = spent" assumption.
- Answer: wall clock DOES spend the plan (+1.4..2.3 ms in 12/12 rows) — seat 16 measured the kept iteration,
  which is 1-69 ms early. The two stop paths have opposite error modes: movetime discards a partial iteration,
  a clock stop discards nothing (undershoot 0.0, 40/40) and overshoots soft by up to a whole iteration.
- job1b FINISHED: 1,400 searches, moves 40.48 / 490.50 ms reproducing run 1 to 0.02 ms; baselines 0.03 %.

next: job1b report + board read for an unconfirmed NEW finding.

## 2026-11-16T21:41Z
- 08-C3: checked seat 21's 21-F2 -> **CONFIRMS** (3 links: readyok after refusal, previous board kept via
  synchronous perft, and a real depth-1 move legal in the old board / ILLEGAL in the board the GUI asked for).
  My own v1 harness had the 19-F12 bug in it; caught, kept as check_s21f2.py.v1_INVALID, rewrote properly.
- job4/harness_refusal_control.sh proves my timing harness ABORTS on a refused FEN (exit 1, 1 record), so no
  latency of mine can be attributed to a stale position.
- Opus file 3 confirms `go movetime T` = T - Move Overhead "by design (seats 08, 28, 02)" — 08-F2 is the
  accepted statement; seat 16's REFUTES was about the kept iteration, reconciled in 08-F10.

next: timing verification of 08-F1/08-F10 on the fresh set, then report.

## 2026-11-16T21:48Z
- job5 DONE: clock tail sweep 200/500/1000/3000/10000/30000 ms, 1,200 searches. 08-F11: the tail scales
  linearly (p99/median 3.1-4.8x constant; 10x clock -> 11.9x p99) and median/soft shrinks 100 %->61 %.
  No search exceeded its own clock at any size.
- job6 DONE: 08-F12 — the book is wide: 9 of 14 opening positions answered from it, INCLUDING startpos itself
  (the default first line of any harness), up to `1.e4 e5 2.Nf3 Nc6 3.Bb5`; and the book move VARIES between
  runs (Book Variety 30).
- Findings now 08-F1..F12, checks 08-C1..C3. All reports pushed (job1, job1b, job2, job3, job5, job6 + reconcile).

next: job 6b — verify the book trap cannot have contaminated any of my 1,200+ timing records (OwnBook false
proof per dataset), then another board read.

## 2026-11-16T21:50Z — CHECKPOINT PUSH (22:05 requirement met early)
State: findings 08-F1..F12, checks 08-C1..C4. Six job reports pushed.
- job1 (movetime/clock latency, 1,000 searches), job1b (job 1 AGAIN SEED 811, 1,400 searches),
  job2 (very little time, 2,000 searches), job3 (movestogo, 800 searches),
  job4 (seat 16 reconciliation: wall vs kept iteration, 2 stop paths), job5 (clock-tail sweep, 1,200 searches),
  job6 (book width + book contamination audit).
- 08-C4 just added: seat 03's S-F3 (king-exposing ep capture) CONFIRMS, 0 of 3 illegal generated, 2 of 2 legal
  generated, move lists identical to python-chess.
- Total searches recorded by this seat: 1,000 + 1,400 + 2,000 + 800 + 1,200 + job4 (~100) = **6,500+**,
  every one from a harness that waits for `bestmove` and is audited for the 19-F12 artefact (min stdout lines
  between go and bestmove is 2, and 08-F12's book effect on the O/G sets is measured at 1 of 200 / 0.04 ms).

next: board read for a NEW finding with no C line; seats 03 and 07 are the only ones with unchecked findings.

## 2026-11-16T21:53Z — FINAL BLOCK (22:30 deadline met early; stopping here)
All work committed and pushed. Nothing uncommitted.

### Findings 08-F1 .. 08-F15 (15)
F1 clock tail ~4x median past own soft limit | F2 movetime spends T-MoveOverhead (restated with planned vs
achieved) | F3 a book move inside the timing set | F4 baseline repeatability 0.20 % | F5 <=10 ms clock collapses
to a 1-ply 2000-node emergency search, increment does not lift it | F6 1 ms hard limit overrun | F7 0 of 2,000
searches exceeded the clock, 0 illegal | F8 movestogo 1/2 land on the 792 ms hard limit | F9 engine achieves only
55-79 % of planned soft (restated) | F10 the two stop paths have OPPOSITE error modes | F11 tail scales linearly,
p99/median 3.1-4.8x, median/soft 100->61 % | F12 the book answers 9 of 14 opening lines INCLUDING startpos, and
varies between runs | F13 the four PINNED honesty numbers do not depend on OwnBook | F14 worst clock overshoot
+33.2 ms at 200 ms and +180.8 ms at 1000 ms, 22 %/14 % over one iteration | F15 every timing search verified COLD

### Checks 08-C1 .. 08-C5 (5)
C1 CONFIRMS seat 06 S-F4 (left-right eval) | C2 CONFIRMS seat 27 S-F2 (nodes dead zone, boundary is
position-dependent) | C3 CONFIRMS seat 21 21-F2 (refused FEN keeps previous board) | C4 CONFIRMS seat 03 S-F3
(en-passant pin) | C5 CONFIRMS seat 03 S-F1 (perft 1..4 + move sets)

### Reports
REPORT_job1.md, REPORT_job1b.md, REPORT_job2.md, REPORT_job3.md, job5/REPORT_job5.md,
job5/REPORT_overshoot_and_pins.md, job6/REPORT_book_width.md, reconcile_seat16_F2.md, audit_assumptions.md

### Measurement integrity (all disclosed, none hidden)
- A stale run_job1.sh of mine re-ran concurrently during the FIRST job1/job2 measurement; both first datasets are
  kept at job*/raw and are NOT used. Everything reported uses raw2 from a guard that refuses to start unless no
  other engine process exists and loadavg < 0.5.
- My own v1 of the seat-21 check and of job2's probe piped `quit` mid-search (seat 19's 19-F12); both are kept
  as *_v1_INVALID with the mistake named, and the claims resting on them were re-measured properly.
- All controls are enforced by assertion; `negative_control.sh` proves a fake engine aborts a check rather than
  producing a CONFIRMS.

STOPPING per the owner's instruction: no new jobs after the two closing measurements.

## 2026-11-16T22:19Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19Z
Seat 08 kept (`~/swarm_seat.txt` = 08), branch for-fable-and-opus/swarm-08, folder forge-combo29/swarm/08.
Area 8 (THE CLOCK), seed base 801.
Plan: (1) read every unread FABLE_TO_swarm_N.md from lowest N up, (2) build the PC engine from file 5's patch as
it says (-DFORGE_MATE_ALPHA_GUARD=1, separate copy) and check its known bench numbers, (3) re-run my own findings
on the PC build under settings PC20 so every finding line names its build and settings, (4) THE CYCLE.
STATUS every 25 minutes or less; findings pushed with each block.

next command:

    cd /agent/repos/dwqww && git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git ls-tree -r --name-only FETCH_HEAD | grep -E 'FABLE_TO_swarm_[0-9]+\.md' | sort

## 2026-11-16T22:26Z
- Read FABLE_TO_swarm_2, 4, 5 (1 and 3 read earlier). Rules absorbed: a zero needs a planted case through the
  same harness; pins are DEFAULT-option numbers and the sums are S14 numbers (my HONESTY.txt was already in the
  pins regime — verified); area 9 evaluation work is worthless on the PC because it runs its own net.
- **PC BUILD (r15) BUILT AND VERIFIED.** Patch sha256 d6bd72c531f785f4 (matches), applied to a SEPARATE worktree
  with `patch -p1 --fuzz=0` (11 files, zero fuzz), built with -DFORGE_MATE_ALPHA_GUARD=1.
  **All 8 known numbers exact**: none->312866/862329/3024920/4865609; S14->242796/656517; PC20->278024/587276.
  All six new options exist in `uci`; zero `unknown option`/`invalid value` in any output. Details:
  pcbuild/REPORT_pc_build.md.
- Cross-check: the BASE build under S14 also gives 242796, as FABLE_TO_swarm_4 says.

### next: re-run my findings on the PC build under PC20, starting with the repaired-defect candidates
exact next command:

    cd /agent/repos/dwqww/forge-combo29/swarm/08/pc20 && python3 ../job2/probe_no_clock.py ~/builds/pc/forge

## 2026-11-16T22:31Z — Threads-1 rule verified for this seat
Seat 04: the PC build gives four distinct SCORES at Threads 4 (+2576, mate 13, mate 18, mate 16) on one position,
identical at Threads 1. **No harness of mine ever set Threads above 1** — grep for `Threads value [2-9]` across
every script: zero matches; all 12 harnesses set `Threads value 1` explicitly. So no score, node count or timing
recorded by this seat is provisional on that count. The rule is now stated at the top of FINDINGS.md.
PC20 re-run in progress: mt50_a done (200), mt50_b partway.

## 2026-11-16T22:32Z
- 08-C6: fifty-move score floor CONFIRMED on PC20 at H=91 exactly (seat 05's figure), with a 7.25M-node spike.
- 08-F22: the score defect is a BAND (H=91..99 all cp 0); the node cost is a SINGLE SPIKE at H=91 plus a
  shoulder at 92-93, then cheaper than a normal search. Two facts, stated separately.
- 08-C7: threading. Threads 1 reproducible on both boards and reproduces seat 04's cp -293 / 31,779 exactly;
  Threads 4 gives 10 distinct scores in 10 runs (they saw 9) but on THEIR board the move never varied
  (g7g6 x10), while on MY second board it did (c1f4 x4, e1g1 x6). So move nondeterminism above Threads 1 is
  CONFIRMED, their example board is not, and "move choice is trustworthy" does not hold in general.
- INCIDENT: my blow-up script took OUT as argv[1] and I passed the exe first, writing the report over the PC
  binary. Rebuilt, re-verified all 8 pins identical, re-ran byte-identical. Recorded in
  pc20/REPORT_fifty_move_band.md. All future scripts take OUT first, EXE second.

next: seat 20's unconfirmable-above-Threads-1 items (confirmable at Threads 1), then the PC's own switches.

## 2026-11-16T22:34Z
- Owner page delivered (pc20/OWNER_PAGE_clock.md) with the re-verification disclosure in its header.
- 08-C6: fifty-move score floor CONFIRMED on PC20 at H=91 (seat 05's exact figure) + 7.25M-node spike.
- 08-F22: SCORE defect is a BAND (H=91..99); the NODE cost is a SINGLE SPIKE at 91 with shoulder 92-93.
- 08-C7 -> corrected by **08-C8**: seat 04's 04-F10 CONFIRMED IN FULL. A committed 20-run batch of their board
  at Threads 4: g7g6 16x, e5e4 3x, f6d7 1x — THREE moves, minority moves are 5-15 % events, my original 10 runs
  simply missed them. Per-run data now committed.
- 08-C9: `MateAlphaGuard true` ALONE is the mate-distance fix (S14: mate -9 -> guard: mate -4, 8-ply pv).
- 08-F23: of the four PC20 search switches, **CuckooRep alone makes it WORSE** (mate -13 vs baseline mate -9);
  the others improve but never reach the true -4; all four together = mate -7.
- 08-N1 METHOD: "a summary I typed is not evidence" — every run file now carries per-run lines.
- INCIDENT (kept as instructed): a script's OUT argument was passed the exe path, overwriting the PC binary; it
  was rebuilt, all 8 pins re-verified identical, the sweep re-run byte-identical. No measurement affected.

next: does any single search switch change CLOCK behaviour (F16 tested the bundle only)?

## 2026-11-16T22:43Z
- **Read FABLE_TO_swarm_5 and 6.** File 6 changed two of my verdicts.
- **08-C6W: I WITHDRAW the "defect" wording of 08-C6/F22.** File 6's test on `1K6/8/8/3R4/8/8/8/k7 w - - 91 1`:
  mate distance at counter 0 is 15 plies, only 9 half-moves remain at H=91 -> cp 0 is CORRECT CHESS. Measurements
  stand (H=91 exactly, band 91-99, 43M nodes at depth 20 -> 89M at depth 28); only the interpretation changes.
- **08-F24: THE OWNER'S REAL CLOCK (6 s + 0.06), PC20, Threads 1, 240 moves.** Pinned 6000: median 295.2,
  p99 457.4, worst 482.4 ms (8.0 % of clock). Countdown from 6000: median 130.9, p99 371.2, worst 390.4.
  **0 moves over the clock, 0 over the hard limit.** Worst soft overshoot +165.4 ms = one iteration (depth 19
  costs 157 ms, measured).
- 08-C8 annotated: spread above Threads 1 is NOT a defect per file 6 — recorded as a fact behind the Threads-1 rule.
- Corrections made against measurement this block: my "+350-460 ms per iteration" claim was the whole search ladder,
  not an iteration (corrected to 157 ms).

next: `go softnodes N` on PC20/Threads 1 — determinism, finished depth, overshoot past N (new area from file 6).

## 2026-11-16T22:45Z
- **RECONCILED with seat 28 (08-F27): their tail is RIGHT, my 08-F24 "worst 482 ms" was not a population figure.**
  Ran their exact outlier FENs on my harness at 6 s + 0.06 / PC20 / Threads 1: `8/8/6k1/Q7/1P4PP/1K3P2/8/8 b`
  gives **1585.4 ms against their 1585.3 — to 0.1 ms**; their other outliers 834.9, 985.0, one run at 1585.9.
  My 3 boards were startpos + two full-material middlegames — the two fastest classes.
- **08-F28: the tail is POSITION-DEPENDENT.** Median by shape (5 boards each): few pieces + few moves **853.1 ms**
  (worst 1585.4) | few pieces + many moves 388.9 | full material + few moves 386.2 | full material + many moves
  **161.2 ms** (worst 398.5). A **5.3x spread**; driver is the last iteration's cost (415 vs 57 ms), since the
  engine stops at an iteration boundary. Engines never over the 6 s clock (0 of their 120, 0 of my 240).
- 08-N1 extended with this third instance: **a three-position median is not a population median.**
- Could not message seat 28 directly (tool only allows my parent); asked the coordinator to relay my 3 FENs.
- Earlier this block: 08-F25 (H=91 fits the real clock, absorbs), 08-F26 (softnodes deterministic, +1.3-2.1x N),
  08-C6W (withdrew the fifty-move defect wording — cp 0 is correct chess there).

next: extend the shape-class sample to a size that can support a FREQUENCY claim (seat 28's 5-of-120), per class.

## 2026-11-16T22:47Z
- **CLOCK HEADLINE written** (pc20/CLOCK_HEADLINE.md) and it REPLACES the three-position figures. Five shape
  classes at 6 s + 0.06 / PC20 / Threads 1: medians **161.2 / 386.2 / 388.9 / 853.1 ms**, worst **1585.4 ms**
  (= the hard plan exactly), driven by the last completed iteration's cost (57.1 ms busy middlegame vs 415.4 ms
  sparse endgame). Stated: **soft plan overshot 5.0x in the sparse class; the hard plan is the only real bound.**
- **08-F29 frequency**: 60 boards per class — real-game 2 of 60 (3.3 %) and sparse 3 of 60 (5.0 %) over 1.2 s,
  bracketing seat 28's 5 of 120 (4.2 %). The tail is a ~4 % event, not 0 % and not rare.
- **08-F30 link**: the sparse class is ALSO the volatile-score class — **a mate appeared on 2 of 5 boards** at
  depth D+4 that the clocked search missed, 318 cp vs 3 cp on the rest, 0 of 5 mates in full-material. One
  explanation covers the time tail and the training-target concern. No combined ratio quoted (mate-to-30000cp
  mapping would give a meaningless 106x).
- Also this block: 08-F25 (H=91 absorbs at the real clock), 08-F26 (softnodes deterministic, +1.3-2.1x N),
  08-C6W (fifty-move defect withdrawn), 08-F27 (reconciled with seat 28), 08-F28 (shape dependence).

next: extend the sparse/volatile link to a RATE (20 boards per class) rather than a direction, since 5 boards
cannot give one — and keep confirming.

## 2026-11-16T23:14Z
- Clock work is consolidated in **pc20/CLOCK_HEADLINE.md** (five shape classes, medians 161.2-853.1 ms, worst
  1585.4 ms = the hard plan; soft plan overshot 5.0x in the sparse class, hard plan the only real bound).
- 08-F29 frequency: 3.3 % (real-game) and 5.0 % (sparse) over 1.2 s on 60 boards per class, bracketing seat 28's
  4.2 %. 08-F30 link: sparse class also has the volatile score (mate appeared on 2 of 5).
- Running now: the **volatility RATE on 30 boards per class** you asked for (mate count, gap >= queen, gap >=
  200 cp), so the owner gets a rate he can act on rather than a direction. It is slow because a single
  `go depth D+4` reference on a sparse board can exceed 90 s — each search is capped at 90 s and the counts of
  capped searches are reported separately (a clocked search that fails to answer in 90 s is a hang, not a tail).

next command:

    cd /agent/repos/dwqww/forge-combo29/swarm/08/pc20 && cat volatility_rate.txt

## 2026-11-17T00:20Z
- **08-F31 — the rate for the owner.** 30 boards/class at the owner's clock, clocked score vs completed `go depth D+4`:
  sparse (<=12 pieces) **10 of 27 boards have a MATE the clocked search missed (37 %)**; real-game/full-material
  **0 of 30** for mate, queen-gap and 200cp-gap, every score within 113 cp (median 14). Note "gap >= queen in cp"
  is 0 in BOTH classes — the sparse error is a mate APPEARING, so quoting only cp gaps would invert the result.
- 3 sparse depth-(D+4) references did not finish in 90 s (the time tail inside the reference search).
- **08-N2 METHOD: `select()` on a Python text-mode buffered pipe is not a timeout.** It reported 90 s timeouts on
  clocked searches that answer in 194 ms, because `readline()` reads ahead. Would have produced "the sparse class
  hangs" — false. Fixed with a reader thread; rule recorded: prove a timeout against a known-fast case first.
- Clock headline (pc20/CLOCK_HEADLINE.md) unchanged: 5 shape classes, 161-853 ms medians, worst 1585.4 ms.

next: extend the sparse mate-rate with a second independent sparse sample (different seed) to confirm 37 % is not
seed-specific, then continue confirming other seats.

## 2026-11-17T00:32Z
- **Seed-902 replication done, and the rule I pre-committed binds me: the 37 % rate is NOT ESTABLISHED.**
  R seed 801: 10 of 27 (37.0 %, Wilson 21.5-55.8). R seed 902 independent: **3 of 29 (10.3 %, Wilson 3.6-26.4)**.
  Point estimates differ 3.6x, outside the pre-committed ±15 window -> report a DIRECTION, no percentage, no pooling.
  Write-up pc20/REPLICATION_seed902.md.
- **What both samples agree on (the actable part):** sparse class CAN produce a cp score for a position that is a
  forced mate — **13 of 56 across both samples**; full-material/real-game produced **0 of 60**, every score within
  113 cp. That 0 of 60 is now the strongest result of this line.
- Probable cause of the difference, stated as a guess: my seed-801 sparse set was hand-picked to fill "few pieces
  AND few moves" and several boards were near mate; seed 902's are random-game endings. Unmeasured.
- 08-F31 restated in FINDINGS with the rate explicitly withdrawn.

next: cadence + confirmations. Continuing.

## 2026-11-17T00:39Z
- Lead claim restructured: **13 of 56 sparse boards vs 0 of 60 full-material** now leads REPLICATION_seed902.md,
  both denominators kept, no pooled rate.
- **08-F32: my near-mate guess is REFUTED.** Independent deep `go depth 18` per board: mate-appearing targets in
  **3 of 18 near-mate boards (17 %)** but **10 of 38 not-near boards (26 %)** — opposite direction to my hypothesis.
  Real but separate fact: my hand-picked seed-801 set was 52 % mate-bearing (14/27) vs 14 % (4/29) in the random
  seed-902 set, so the samples differ in composition, but that does not carry the error rate.
- Cause of the rate gap: UNMEASURED. I name three untested candidates and claim none.
- Findings now 08-F1..F32, checks 08-C1..C9, method lines 08-N1/N2, one withdrawal (08-C6W).

next: cadence; then confirmations of other seats' unchecked findings (seat 07's 07-F1 is the only single-finding
seat left unchecked; everything else I sampled has a C line).

## 2026-11-17T00:40Z
- **08-C10: seat 07's 07-F1 CONFIRMS on PC20.** `go depth 8 searchmoves e2e5` on startpos (20 legal moves) emits
  **8 fabricated `info depth` lines, all `nodes 0`, then `bestmove 0000`**; garbage `a9a9` identical; **no depth
  limit -> 64 fabricated lines** (their exact case). Engine prints the true cause in an info string. Controls pass:
  `searchmoves e2e4` and an unrestricted search both search normally with zero `nodes 0` lines.
- Composition framing separated into its own labelled block in NEARNESS_REFUTED.md (52 % vs 14 %), stated as a
  property of the samples and explicitly NOT as the cause; three untested candidates left named and unadopted.

Tally: 32 findings (08-F1..F32), 10 checks (08-C1..C10), 2 method lines, 1 withdrawal (08-C6W).

next: cadence; next confirmation or an extension of the clock work.

## 2026-11-17T00:49Z
- **08-F33 corrects my own 08-F28.** At 15 SOURCED boards per class the median spread is **1.8x (184-338 ms), not
  the 5.3x** of hand-built boards, and "few pieces AND few moves" is the FASTEST median. What holds, sharper: the
  whole tail is in **<=8-piece positions** (quiet_endgame p90 **1164 ms** vs 334 ms median, **2 of 15 over 1200 ms**,
  worst **1585.5 ms** = the hard plan; every other class had zero over 1200 ms). Move count does NOT separate them
  (33 moves gave the worst case; 4 moves gave both 1225 ms and 175 ms) — piece count does.
- **08-C11: seat 19's coverage gap closed with a PLANT.** `plant_check.py` drives the same code path: clocked
  **cp -4161** at depth 16, depth-20 reference **mate -5**, classified **mate_appeared**, and the 10-ply pv replays
  to **checkmate** in python-chess. So the 0-of-60 is a MEASURED zero, not "not shown".
- Method note kept: zeros are the easiest claims to leave unplanted and the hardest to doubt.

Tally: 33 findings, 11 checks/plants (08-C1..C11), 2 method lines, 1 withdrawal.

next: cadence + remaining confirmations.

## 2026-11-17T00:50Z
- **08-C11: plant for the 0-of-60.** Same code path: clocked cp -4161 at depth 16, depth-20 ref mate -5,
  classified mate_appeared, and the 10-ply pv replays to CHECKMATE in python-chess. 0-of-60 is now MEASURED.
- **08-C12: plants for both load-bearing zeros.** Fake engine sleeping 2.5 s on a 1 s clock -> caught at 2501 ms;
  fake engine answering a1a8 -> caught as illegal; real engine passes both (14 info lines, 56 ms, e2e4).
- **08-N3: my own control was silently invalid.** The first zero-plant used the real engine as the "not over the
  clock" control and it showed **0 ms with 0 info lines** — a BOOK move, because my helper never sent OwnBook false.
  Fixed by disabling the book AND requiring the control to show info lines. Rule: a control must be shown to
  exercise the mechanism, not merely to return a plausible value.
- **08-C13 zero ledger**: every zero I claim, marked MEASURED / COVERED BY INHERITANCE / NOT COVERED, named
  individually rather than left silent.

next: cadence; then continue confirmations.

## 2026-11-17T00:51Z
- **08-C14: tiny-clock plant** closes the last gap in my own zero ledger. Fake engine sleeping 300 ms is caught as
  over the clock at wtime 100/30/10/1/0 (301 ms); real engine never over at any size > 0 (0.7-5.9 ms, 1-9 info
  lines). `wtime 0` stated as an ARITHMETIC exemption (any nonzero time exceeds a zero clock; the engine answers in
  0.7-0.8 ms with the emergency ply), not a false positive. Limit recorded: a 300 ms overrun proves the comparator
  fires, not that a 1-2 ms overrun at wtime 1 is visible above the ~0.1-0.2 ms round-trip floor.
- **08-C15: seat 06 S-F28 CONFIRMS.** Colour-mirror asymmetry, PC r15 + base, Threads 1, depth 10, 60 pairs:
  base 23.3 %, PC switches OFF 26.7 %, ON 35.0 %, PC20 35.0 % — OFF-vs-ON +8.3 points, inside the ±12 interval a
  60-pair sample allows. Score asymmetry 96.7-100 % unequal on ALL configs incl. base, so not a PC20 artefact.
  Not a reproduction of their counts; level and difference only.

Tally: 33 findings, 15 checks/plants (C1..C15), 3 method lines (N1..N3), 1 withdrawal (C6W).

next: cadence.

## 2026-11-17T01:01Z
- **08-C16: seat 06's S-F6 + S-F27 CONFIRMED EXACTLY, to the digit.** Whole G set, 353 mirror pairs, depth 10,
  Threads 1, my own harness: base **101/353 (28.6 %)** bestmoves not mirrored and **334/353** scores unequal —
  their exact S-F6 figures; PC r15/PC20 **120/353 (34.0 %)** — their exact S-F27 figure. Three headline counts
  reproduce exactly, which also validates my mirror translation against another seat's.
- **Upgrades 08-C15:** the OFF-vs-ON switch difference is **+5.4 points at 353 pairs** (interval ±5), not the
  +8.3 seen at 60 pairs — so "NOT an effect and NOT identical either". Recorded as a change of framing.
- S-F6 is the base claim all of seat 06's symmetry work rests on; it now has an exact confirmation.

Tally: 33 findings, 16 checks/plants, 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:02Z
- **08-C17: seat 12's S-F12 CONFIRMS on both builds — a mid-search `setoption` silently STOPS the search.**
  `go depth 24`, probe at 150 ms: all four probes (Hash 32, MultiPV 2, LmrQuietBase 94, OwnBook true) stop it at
  **depth 17 in ~1 ms**; `isready` and no-probe reach **depth 24 in ~875 ms**. Same on PC r15/PC20 and base/S14.
  **Integrity consequence stated for the whole swarm:** any harness sending a setoption mid-search records a
  truncated search as a completed one, with no error. My own harnesses verified unaffected (every setoption is
  before `go`, with a `sync()` after it).

Tally: 33 findings, 17 checks/plants (C1..C17), 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:10Z
- **08-C18: PARTLY CONFIRMS seat 03 S-F20, correcting its depth.** Board `1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183`,
  root score per move: depth 12 **c6c7 cp -1092 vs c6d6 cp -1139 — the CHOSEN move is better by 47 cp**; c6d6 only
  overtakes at depth 14 (46) / 16 (22) and becomes clearly better at **depth 18 (mate -9 vs cp -1195)**. Their
  quoted `c6c7 mate -20, c6d6 cp -1192` at depth 12 does NOT reproduce on base/S14, PC/PC20 or PC/S14.
  The substance holds from depth 18; their S-F22's 0-of-50 at depth 16 is CONSISTENT (gap is 22 cp there).
- Found by my own plant failing: it expected a queen-sized gap at depth 12 and found 47 cp the other way. I did not
  lower the threshold to make it pass.

Tally: 33 findings, 18 checks/plants (C1..C18), 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:12Z
- **08-C19: seat 13 S-F10 CONFIRMS to the node.** Owner's clock, PC r15 PC20 Threads 1: startpos 5x gives
  **650,246 nodes / depth 19 / e2e4 in all five** (their three determinism figures), wall varying only 355-363 ms.
  Clock share on 8 G positions **median 4.1 %** (their figure); 6 s -> 366.6 ms, 30 s -> 1268.9 ms (their scaling).
  0 illegal bestmoves.
- **Reconciled my 4.9 % vs their 4.1 %: position set, not engine.** Per-position share spans **2.5-13.7 %** (5.5x),
  so a 3-position sample gives 4.9 % and an 8-position one 4.1 %. THE HONEST OWNER FIGURE IS NOW
  **2.5-13.7 % per position, median ~4 %**, not a single number — correcting the implicit single figure in 08-F24.
- Third instance of the small-sample lesson tonight (after 08-F27, 08-F33); all three recorded under 08-N1.

Tally: 33 findings, 19 checks/plants (C1..C19), 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:13Z
- **08-C20: seat 21 21-F12 CONFIRMS, including the exact 8-node figure**, on a board I built and verified
  (`7k/8/6K1/8/8/8/8/4R3 w - - 100 1`, e1e8 is a legal MATE at halfmove 100). Base 0 nodes, **PC r15 8 nodes**;
  illegal-name control still 0000 + info string. **Beyond their line:** on the plain `go depth 4` path the base
  build returns `e1a1` in 0 nodes — a NON-MATING move from a mate-in-1 — while PC returns the mate in 85 nodes.
- 08-F24's finding line now carries the 08-C19 correction in place (2.5-13.7 %, median ~4.1 %, a range; small share
  is not a defect and carries no strength claim).

Tally: 33 findings, 20 checks/plants (C1..C20), 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:14Z
- **08-C21: seat 12 S-F14 CONFIRMS — the one-ply-down draw short-circuit is still open on PC r15.** Board
  `6k1/8/5PPP/8/8/8/8/R6K b - - H 40`: a clean cliff at hm 99 — 0/96/97/98 all `mate -1`, **99 gives cp 0
  (18 nodes)**, 100 cp 0. Plant: hm 0 scores mate -1, so the harness sees the win. Discriminator: 96/97/98 do not
  give cp 0. Their 36 nodes vs my 18 is a depth difference; the claim is the cliff.
- **This bounds my own 08-W1 retraction from the other side:** there 15 plies needed with 9 half-moves left
  (correct draw, I withdrew the defect claim); here 1 ply needed with 1 left, so the mate IS available and is
  missed. Both sides of the fifty-move boundary now measured.
- Also fixed the findings numbering: C6W -> **08-W1** (a withdrawal, not a check), and a NUMBERING NOTE explains
  the absent 08-C7 (superseded by C8).

Tally: 33 findings, 21 checks/plants, 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:15Z
- **08-C22: seat 17 S-F9 CONFIRMS with a refinement.** PC r15 PC20 Threads 1, depth 14: bestmove **c3b5 at every
  Hash size 1/8/32/512/2048 MB**, hashfull 450/65/17/1/0 (their 440/58/10/0/0 shape). **Refinement: node count is
  69,686 at Hash 1 but 73,610 IDENTICAL at 8/32/512/2048** — their own shape, unstated. So the search is
  bit-identical from Hash 8 up and differs only at the minimum table: comparing nodes across Hash 8..2048 is safe,
  Hash 1 against the rest is not. Plant: a different position gives a different bestmove through the same harness.
- Noted: **seat 17's S-F11 independently found the same `select()`-on-a-text-pipe bug that I recorded as 08-N2** —
  two seats hitting the same harness trap from different angles.

Tally: 33 findings, 22 checks/plants (C1..C22), 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:16Z
- **INDEX.md written** — a one-page map of this area's 373 files: read-first list, the headline numbers table with
  the source file for each, the five most useful single results, the three method rules, the folder map, and a
  **WHAT IS NOT HERE** section (no game played, no sanitizer build of the PC engine, no PC net). That last section
  is the honest boundary of what the area can claim.

Tally: 33 findings, 22 checks/plants, 3 method lines, 1 withdrawal, 46 report/analysis files.

next: cadence.

## 2026-11-17T01:30Z
- **08-F34: drained the owner's clock to the flag — 0 flags in 600 moves.** Owner's control, PC r15 PC20, Threads 1,
  clock walked forward as a GUI does (clock -= wall, += 60), 200 moves x 3 positions: lowest clock **1438-1744 ms**,
  **0 moves where wall > remaining clock**. The clock STABILISES rather than draining, because once the spend falls
  below the 60 ms increment the drift is positive and the time manager shortens with it.
- Limits stated: not a game (same position re-searched, nothing won); 6+0.06 is generous against a ~185-340 ms median
  move; and a single ≤8-piece endgame move (1585 ms) arriving at ~1400 ms would still risk a flag — not staged here.
- That completes the clock line: per-position share (2.5-13.7 %, median ~4 %), where the tail lives (≤8 pieces, up to
  the hard plan), and whether it ever flags (no, 600 moves).

Tally: 34 findings, 22 checks/plants, 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:35Z
- **08-F35: staged the residual risk from 08-F34 — 0 flags in 21 worst-case cells.** The three slowest boards from
  the shape sweep (1585/1225/1164 ms at a 6 s clock) re-run at clocks 6000/3000/1600/1200/800/400/200 ms:
  **no pair exceeded its remaining clock.** The 1585 ms board given 1600 ms took only **218 ms** (depth 15 not 18)
  because **the time manager shrinks the plan with the clock**, so the expensive iteration no longer fits.
- **The clock line is now closed from both ends:** it stabilises in a long game (F34, 600 moves, 0 flags) and does
  not flag on the worst boards down to 200 ms (F35, 21 cells, 0 flags). The only thing unmeasured is a real game.

Tally: 35 findings, 22 checks/plants, 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:37Z
- Made the **218-vs-1585 cell the headline of 08-F35** as requested — and that caught **three wrong numbers in my own
  text**: I had quoted the plan as "1600 ms -> soft 72 / hard 360" and "200 ms -> soft 8 / hard 40". Computed from
  clock_plan.hpp: **1600 ms -> soft 117 / hard 585** and **200 ms -> soft 53 / hard 114** (6000 -> 317/1585 was
  right). Corrected in the F35 line, the owner page and the script's printed text, and regenerated the committed
  output so the file matches.
- Fourth time tonight that re-reading a number against its mechanism found an error; second time the error was in
  text I had just written rather than in a measurement.

Tally: 35 findings, 22 checks/plants, 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:38Z
- **pc20/PLAN_TABLE.md + audit_plan_numbers.py**: the plan for every clock this area uses, GENERATED by script from
  clock_plan.hpp, not typed. Sudden-death and increment-60 tables separately, plus movestogo. Any plan number can be
  checked against it. The script also greps every .md for "soft N / hard M" (1 claim, 1 matched, 0 unmatched).
- **Found the origin of my error, which is more useful than the error:** "72 / 360" is the CORRECT no-increment plan
  at 1600 ms; I had applied the sudden-death plan to an increment-60 context where the truth is 117 / 585. Both are
  right for their own regime — so the failure was the REGIME not travelling with the number, the same class as the
  mate-vs-centipawn scale trap.
- Five arithmetic/scale catches tonight; four were in prose or tables I wrote myself, not in measurements. That
  pattern goes in the FINAL block.

Tally: 35 findings, 22 checks/plants, 3 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:40Z
- **08-C23: mechanical proof of the 08-C17 assertion — 0 ordering violations across 57 harnesses.** No harness sends
  a `setoption` between `go` and the `bestmove` wait, so no timing or score of mine came from a silently truncated
  search.
- **08-N4 (new method rule 4): the audit produced TWO false positives before it was right** — one from counting a
  setoption that precedes the `go`, one from a "bestmove" pattern matching a reader helper so the window stretched
  into the next function. Both would have been published as defects in my own harness. Rule: open the flagged file
  before believing the tool; a static analyser is only as good as its model of the code.
- Tally: 35 findings, 23 checks/audits/plants, 4 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:42Z
- **08-C24: seat 01 S-F102/S-F103 CONFIRMS, all four clauses.** PC r15 PC20 Threads 1, OwnBook true, three opening
  positions: `go depth 12` **0 of 3** book lines (12 real info lines each); `go wtime 6000` **3 of 3**;
  `go movetime 100` **3 of 3**; `OwnBook false` **suppresses** the clock case (0 book lines, 19 real info lines).
  The negative and positive are in the SAME run, so the 0-of-3 is measured, not structurally blind.
  **Corroborates my own 08-F12 from a different route** — and sharpens its advice: the book hazard is specific to
  the `movetime`/`wtime` forms; a `go depth` harness can never hit it. `go nodes`/`go infinite` remain unmeasured
  by me and I say so.

Tally: 35 findings, 24 checks/audits/plants, 4 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:44Z
- **08-F36: the book gating now covers ALL FIVE `go` forms** — closing the boundary I had named as unmeasured in
  08-C24. PC r15 PC20, OwnBook true, three openings: `go depth 12` **0/3**, `go nodes 5000` **0/3**,
  `go infinite` **0/3** (all three with real info lines), `go wtime 6000` **3/3**, `go movetime 100` **3/3**.
  So a depth/nodes/infinite harness can never hit the book hazard; only clock/movetime harnesses need OwnBook false.

Tally: 36 findings, 24 checks/audits/plants, 4 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:46Z
- **08-C25: seat 03 S-F13 SUPPORTS — divergence is exclusive to lone-king roots.** Base vs PC r15, depth 8,
  Threads 1, my R positions split by lone king at the root: **11 of 40 lone-king boards diverge, 0 of 60 outside**.
  Every divergence is inside their corrected predicate and none of 60 is outside it — a rule holding at 100 %
  outside its condition is stronger evidence than a rate inside it. Their counts (9/200, unstratified) and mine
  (40/100, deliberately stratified) are NOT comparable in magnitude; what reproduces is the structural rule, and
  the file says so. All 11 are K+material vs bare-king endings.

Tally: 36 findings, 25 checks/audits/plants, 4 method lines, 1 withdrawal.

next: cadence.

## 2026-11-17T01:48Z
- **08-W2: WITHDRAWS my own "probing becomes waiting" characterisation of the lone-king divergence.** Classified all
  11 divergences: only **2 of 11** are base-PROBING -> PC-WAITING, **8 of 11 have BOTH moves waiting**, 1 reverses.
  So the repair changes WHICH waiting move is played, not whether the move probes. My sentence came from looking at
  three or four boards; the test refuted it in ten minutes.
- **The lesson, now in the file:** the BOUNDARY (0 of 60 outside the class) was measured and held; the MECHANISM story
  I attached to it was eyeballed and failed. "Why" claims need the test more than "what" claims do.
- Hypothesis left unclaimed: an ordering change would explain "both waiting, different one picked" — untested;
  seat 03's build variants (S-F11/S-F14) are the right instrument.

Tally: 36 findings, 25 checks/audits/plants, 4 method lines, 2 withdrawals.

next: cadence.

## 2026-11-17T01:50Z
- **08-F37: THE MECHANISM FOUND, and my ordering hypothesis KILLED.** Built V1 (BARE_KING_LMR_CAP=0) and V2
  (BARE_KING_ONE_THREAD=1), pins identical at 312,866. **V1 plays the BASE move on 11 of 11 divergence boards**;
  V2 restores 6 of 11. So the cap alone causes every divergence. The both-waiting pattern is 8/9/8 of 11 across
  V0/V1/V2 — unchanged — so ordering is NOT the cause. WHY the cap changes the choice: unestablished (consistent
  with altered LMR, not instrumented).
- **Arc:** boundary measured and held -> mechanism eyeballed and refuted (08-W2) -> ordering hypothesised ->
  instrument run. The WITHDRAWAL was the step that made the attribution possible.
- **pc20/WHY_CASUALTIES.md: six mechanism claims counted**, each with what it got wrong and how caught. Four of the
  six were me explaining my OWN earlier correction — that is the evidence behind "why claims need a test designed to
  kill them".

Tally: 37 findings, 26 checks/audits/plants, 4 method lines, 2 withdrawals.

next: cadence.

## 2026-11-17T01:52Z
- **08-F38: the reduction explanation is now a MEASUREMENT.** Cap ON vs cap OFF, depth 10, on the 11 divergence
  boards: **cap-OFF visits FEWER nodes on 9 of 11** (by 3,356-14,040), more on 2 (+621, +10,981), identical on 0.
  Direction matches the clamping account, so the mechanism story is SUPPORTED — but stated as a strong tendency with
  2 counter-cases, since one counter-case is as large as the effect being claimed.
- 08-W2's open question is now closed at the level reachable without engine internals.
- For the FINAL: (1) "the withdrawal was the step that made the attribution possible"; (2) "four of six mechanism
  claims were me explaining my own earlier correction — each time I explained a fix, the explanation was the next
  thing to be wrong."

Tally: 38 findings, 27 checks/audits/plants, 4 method lines, 2 withdrawals.

next: cadence.

## 2026-11-17T01:54Z
- **08-F39: the 2 counter-cases are UNEXPLAINED, and that is the honest outcome.** Read the gate from the patch (cap
  fires at a node only if the root has a lone king AND that node has a side with only its king), then measured the
  lone-king node fraction over the EXACT legal tree to depth 4: **100.0 % on all 11 boards**, counter-cases included.
  So the gate is active everywhere and cannot distinguish them — the "cap has less to act on there" explanation is
  REFUTED, and they point at a second mechanism (reduction/pruning-cascade interaction) that I cannot characterise
  from outside the engine and do not claim.
- This vindicates the strong-tendency framing: 08-F38 keeps them because it does not exclude them.

Tally: 39 findings, 28 checks/audits/plants, 4 method lines, 2 withdrawals.

next: cadence.

## 2026-11-17T01:56Z
- **08-O1 / pc20/HANDOFF_second_mechanism.md: the second mechanism is a complete UNRUN handoff**, as instructed.
  Contents: what is established (with evidence files), the precise shape of the open question (not WHETHER the cap
  fires but HOW its clamped reductions propagate through which nodes are visited, hence TT/killers/histories/
  aspiration — direction can be board-specific), the instrument that would settle it (a build printing per-depth
  total and clamped reduction counts), and that it needs a source patch to search.cpp and is OUTSIDE my instrument
  set. Plus: the 11 boards' location, the exact variant flags, pins at 312,866, the measurement to make, and a
  warning not to treat the hypothesis as confirmed.
- Honest end state, quoted in the file: cause of the move changes identified; direction of effect a strong tendency
  with two named exceptions; cause of those exceptions not known.
- Not chasing it further, per instruction.

Tally: 39 findings, 28 checks/audits/plants, 4 method lines, 2 withdrawals, 1 open lead.

next: cadence.

## 2026-11-17T02:10Z
- **08-C26: seat 13 S-F16 PARTIALLY CONFIRMS.** 16 plies, book vs engine (depth 18): the CHARACTERISATION holds
  (where the book differs the engine's own gap is -36..+26 cp, median +2, worst inside their "none >=50 worse"
  bound), but my differing count is **5 of 16 against their 12 of 16** — the one variable that differs is depth
  (theirs 12, mine 18), and deeper search converges on opening moves. Stated as an inference, NOT a measurement, and
  I do NOT say their count is wrong.
- **08-N5 METHOD: a reader that works on a search WITH info lines can HANG on one WITHOUT them.** My depth-sweep
  script deadlocked and held an engine 20 minutes; the book answers instantly with zero info lines. Engine verified
  fine (book answers in ms via a plain pipe, 3/3). So the depth comparison is NOT reported — that harness was broken.
  Fifth harness trap tonight, all the same shape: the harness's model of the engine's output is wrong on an unusual
  path.

Tally: 39 findings, 29 checks/audits/plants, 5 method lines, 2 withdrawals, 1 open lead.

next: cadence.

## 2026-11-17T02:12Z
- **Rule 5 extended with its mechanical half:** "every reader must be exercised against a FAST path that emits no
  `info depth` lines — the book, a drawn-root bail, or `go nodes 0` — because those are where a reader waits forever.
  One test, and it covers three of this seat's five harness traps. The fix for such a hang is a timeout PER READ, not
  a faster reader: a 20-minute hang becomes an immediate diagnosis at five seconds."
- **08-C27: audited my own harnesses against that rule.** 66 harnesses scanned, **60 wait for `bestmove`** (safe),
  6 listed for review; and the LIVE test: the main timing harness on a book position completed in **0.2 s, exit 0,
  recorded the answer** (15 stdout lines, bestmove e2e4). So the 08-N5 deadlock did **not** touch any published
  timing number — only the throwaway depth-sweep script hung, which is why I declined to report that sweep.

Tally: 39 findings, 30 checks/audits/plants, 5 method lines, 2 withdrawals, 1 open lead.

next: cadence.

## 2026-11-17T02:14Z
- **08-C27 restated in flat verified form** as requested: *NO published timing number of this seat is implicated by the
  08-N5 deadlock — verified, not assumed.* 66 harnesses scanned, **60 wait for `bestmove`** (safe: waiting for
  `bestmove` is not waiting for an `info` line; only the latter deadlocks), and the 6 without a deadline are pure
  analysis scripts with no engine process (grep-verified). Live test: the main timing harness on a book position ran
  in 0.2 s, exit 0, recorded the answer with 15 stdout lines incl. the book string.
- The trap in one line, now in the finding: **"the failure was not 'the engine is slow', it was 'my reader waited for
  a line this path never prints, and I had no per-read timeout to tell me'".**

Tally: 39 findings, 30 checks/audits/plants, 5 method lines, 2 withdrawals, 1 open lead.

next: cadence.

## 2026-11-17T02:16Z — TALLY CORRECTION (counted from the file, not from memory)
I have been reporting "30 checks" in my messages; the file holds **26**. Counted mechanically just now:

| series | count | ids |
|---|---|---|
| findings | **39** | 08-F1..F39 |
| checks / audits / plants | **26** | C1..C6, C8..C27 (no C7 — superseded by C8, noted in the file) |
| method lines | **5** | 08-N1..N5 |
| withdrawals | **2** | 08-W1, 08-W2 |
| open leads | **1** | 08-O1 |

**So the correct tally is 39 / 26 / 5 / 2 / 1**, and my earlier "30 checks" messages over-reported by four. This is the
same failure the seat has been catching all night — a count quoted from memory rather than read from the file — and it
is now caught the same way: by reading the file.

## 2026-11-17T02:18Z — TALLY (generated, not maintained)
**39 findings, 27 checks/audits/plants, 5 method lines, 2 withdrawals** (and 1 open lead).
Generated by `python3 pc20/tally_gate.py` from FINDINGS.md itself; the gate exits non-zero when a STATUS claim
disagrees with the file, so quote only what the gate prints.

next: cadence.

## 2026-11-17T02:20Z
- **08-C29: the tally is GENERATED, and the gate self-verifies.** `pc20/tally_gate.py` counts every id series from
  FINDINGS.md, compares against the last STATUS tally, and **exits non-zero on disagreement**. Run: **39 findings /
  27 checks / 5 method lines / 2 withdrawals / 1 open lead**, full id list printed, **GATE PASSES**.
- This makes the over-report class structurally impossible to repeat unnoticed: a claim that disagrees with the file
  fails the gate. Same shape as the planted zeros — not "be more careful", but a check that fails when I am not.
- Also this block: 08-C27 restated in flat form (no published number implicated, verified live on a book position in
  0.2 s), 08-N5 added as method rule 5 with its mechanical test and the timeout-per-read fix, 08-C28 (index headline
  claims 10 of 10 traceable).

Tally (per the gate): **39 / 27 / 5 / 2**, plus 1 open lead.

next: cadence.

## 2026-11-17T02:22Z
- **08-C30: seat 21's 21-F8b CONFIRMS.** python-chess accepts `... w - - 0 0` (33 moves) while the engine refuses it
  (`invalid FEN: invalid FEN fields`), and `go perft 1` afterwards gives **20 nodes = the PREVIOUS board**, not 33 —
  proven by synchronous perft, so no reader pattern can explain it.
- **The control caught a would-be false positive:** my first previous position also had 33 legal moves, so perft 1
  would have been identical either way; the control aborted instead of printing an ambiguous CONFIRMS, and I used
  startpos (20 moves) to make the number discriminating. Same class as "a test that cannot fire".
- Hazard noted: a tool counting fullmoves from 0 gets a silent refusal and a search of the WRONG board — the same
  hazard as 08-C3 from a second corner of the FEN parser.

next: cadence.

## 2026-11-17T02:24Z — TALLY (generated, not maintained)
**39 findings, 29 checks/audits/plants, 5 method lines, 2 withdrawals** (and 1 open lead).
Generated by `python3 pc20/tally_gate.py` from FINDINGS.md. The gate FAILED on the previous block (claimed 27,
file holds 29) — which is the gate working: two checks (C29, C30) were added after that claim. Corrected here with
the generated line; quote only what the gate prints.

next: cadence.

## 2026-11-17T02:26Z
- **08-C31: seat 12's S-F22 SUPPORTS.** Fixed node budget (`go nodes 200000`), full Hash 16/64/256 x MultiPV 1..4
  grid: **113 ms fastest to 557 ms slowest = 4.9x**, with **six cells slower than 1.5x the fastest spanning two Hash
  and three MultiPV values** — a diagonal boundary, not a single bad cell. On their sub-claim: (256,3) IS the slowest
  cell (557 ms) but not isolated (256,4 = 550, 256,2 = 384), so worst-but-not-singular — both halves of their framing
  hold. Timing only; a slow cell is not a wrong cell.
- **Pre-commit hook: NOT started, per instruction.** The remaining risk (forgetting to run the gate) stands as stated
  rather than being covered by an untested guard at this hour.

## 2026-11-17T02:26Z — TALLY (generated, not maintained)
**39 findings, 30 checks/audits/plants, 5 method lines, 2 withdrawals** (and 1 open lead).
The gate caught its own drift again — the previous block claimed 29, C31 made it 30. Quote only what the gate prints.

next: cadence.

## 2026-11-17T02:28Z
- **08-C32: seat 01 S-F15 — the ORDER confirms, the "within 0.3 points" does NOT reproduce.** My own mutations, my
  R seed-801 positions, 120/kind at two seeds: refusal ORDER identical at both seeds, and **drop/delete/insert are
  100 % at both** (so "a property of set_FEN" is supported), but **swap moved 13.3 points between seeds** (60.0 vs
  46.7), so the 0.3-point band fails on my sample. Likely cause visible in the data: swap preserves the rank
  character multiset, so the adjacent-digit tolerance often accepts it — position-dependent by construction. My
  ranking differs too: **replace 91.7/82.5 % ABOVE swap 60.0/46.7 %**, where they list swap above replace. Not
  claimed: that their figure is wrong.

## 2026-11-17T02:28Z — TALLY (generated, not maintained)
**39 findings, 31 checks/audits/plants, 5 method lines, 2 withdrawals** (and 1 open lead).

next: cadence.

## 2026-11-17T02:31Z
- **08-C33: seat 13 S-F17 CONFIRMS on EVERY cell of the drawn-root matrix**, including their exact non-mating
  `a1b1`. My own board (`7k/8/6K1/8/8/8/8/R7 w - - H 1`, a1a8 verified as mate first): halfmove 0 and 99 give
  a1a8 on both builds (86/86, 85/85 — the CONTROLS, neither drawn); **halfmove 100 gives base `a1b1` at 0 nodes vs
  PC a1a8 at 85**; K vs K answers at once 0/0. The two control cells make it a matrix rather than an anecdote.
  Their 144 nodes vs my 85 is a depth difference; I confirm the MOVE and the zero/nonzero split.
- Together with 08-W1 (correct draw, 15 plies needed 9 left) and 08-C21 (one-ply-down miss), the fifty-move/draw
  boundary is now measured from THREE sides.

## 2026-11-17T02:31Z — TALLY (generated, not maintained)
**39 findings, 32 checks/audits/plants, 5 method lines, 2 withdrawals** (and 1 open lead).

next: cadence.

## 2026-11-17T02:33Z
- **08-C34: the last cell of the 08-C33 matrix closes — the THIRD-OCCURRENCE door CONFIRMS.** Move list
  `g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8` (python-chess verifies the startpos occurred THREE times):
  **two-occurrence CONTROL — base 701 nodes / PC 412, neither drawn**; **THREE occurrences — base plays `a2a3` at
  0 nodes (drawn), PC searches `d2d4` at 389 nodes**. So the boundary is the third occurrence specifically, and the
  PC repair reaches this door as well as the halfmove door.
- **The drawn-root matrix is now complete on both doors** (halfmove in 08-C33, repetition here), plus 08-W1 (correct
  draw) and 08-C21 (one-ply-down miss) bounding the same boundary from other angles.

## 2026-11-17T02:33Z — TALLY (generated, not maintained)
**39 findings, 33 checks/audits/plants, 5 method lines, 2 withdrawals** (and 1 open lead).

next: cadence.

## 2026-11-17T02:37Z — FILE 7 / v3 path STARTED (my area is done, and file 7 extends the job to seats whose plan is done)
- **Step 0 PASSES COMPLETELY.** All eight bench numbers exact (312866/862329 none; 278024/587276 PC20; 965454/4151906
  test net; 625258/3652372 PC20+net), all three eval lines exact (968/1176/31), and the test net's three checksums
  exact (6,309,096 bytes, fnv1a64 fdff70de72e4ca82, sha256 1db8525e…). Load line checksum + max|w1|=64/b1=96/w2=16
  match, **kernel avx512** (my CPU is AVX-512). Build `-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`, g++ 13.3.0.
- **Prediction committed and pushed ALONE before Step 1**: incremental UPDATE dominates 35-50 %, forward pass 15-30 %,
  refresh 5-20 %; kills: refresh >40 % means the incremental path is failing (that would be the finding), search >50 %
  means the bench is not exercising the net (harness problem first). Second prediction: at most one patch, likely
  <5 % or rejected.
- Working folder `forge-combo29/swarm/08/v3/`; `*.fnn3` in `.gitignore` so the net is NEVER committed.

next: Step 1 — profile `bench 13` + 200 openings under PC20 + test net, Threads 1.

## 2026-11-17T02:43Z — v3 Steps 0 and 1 done; MY PREDICTION KILLED
- **Step 0 PASSES COMPLETELY**: 8 bench numbers, 3 eval lines, 3 net checksums all exact; kernel **avx512** (my CPU
  has AVX-512F, same family as the PC), so no cross-machine explanation.
- **Step 1 profile** (gprof — `perf` absent, no root; the -pg build reproduces bench 13 = 3,652,372 exactly):
  **all nnue::v3 = 21.46 %**, split update **8.47 %** / forward **7.34 %** / refresh **6.78 %**; search proper
  38.41 %; movegen/legal/make/see 15.80 %.
- **My prediction is KILLED**: I said the update would be 35-50 % (kill <20 %), measured **8.47 %**. The CALL COUNTS
  refute the mechanism — `evaluate` runs 2,556,881 times vs `apply_changes_pair` 2,382,071, so my "fewer evals than
  updates" premise was false.
- Second kill did NOT fire: search 38.41 % < 50 %, so the net IS exercised.
- **Step 1b: 200-opening identity baseline committed — node sum 27,944,084**, per-position rows.
- **NOT starting a patch**: no v3 function exceeds 8.5 %, so no hot spot; the larger shares are search/movegen
  (seats 19/29 territory). And per instruction, no patch is recommendable from the bench alone — the real-position
  arm (fixed `go nodes`, ABBA, n>=120, per-position spread) would be required.

Tally per the gate: **42 / 33 / 5 / 2**, plus 1 open lead.

next: cadence.

## 2026-11-17T02:24Z — 389 vs 505 RESOLVED, and the label defect was MINE
- Seat 27 measured PC **505 nodes** on the repetition door where I reported **389**. Measured all four cells:
  **PC r15 S14-only = 505**, **PC r15 PC20 = 389**, base S14 = **0 (a2a3)** in both, v3/PC20 = 389. So **both
  figures are correct** — they are different option sets — and the base cell being identical proves the harnesses are
  otherwise the same.
- **The defect is my label, not my measurement.** `check_repetition_root.py` names its option list `S14` but that list
  **contains the five PC20 switches plus OwnBook false**, so its behaviour was PC20 while its name said S14, and I
  published the NAME instead of reading the list.
- **08-W3 records the withdrawal and the rule: a bare node figure names no search.** 08-C34's line now states
  "PC r15, S14 only, NO PC20 switches" and carries both the 389 and 505 cells.
- Seat 27's counting trap (returns-to-start = 2, but the initial position is occurrence #1) is a real one, and its
  preflight refusing to measure rather than producing a false refutation is correct behaviour.

## 2026-11-17T02:24Z — TALLY (generated, not maintained)
**42 findings, 33 checks/audits/plants, 5 method lines, 3 withdrawals** (and 1 open lead).

next: cadence.

## 2026-11-17T02:28Z — two more corrections, both mine
- **08-W4: my real-position arm's framing was FALSE.** I labelled the 0.937 median "time per identical node budget",
  but **0 of 120 positions gave equal node counts** between the v3-net and built-in arms (verified: one position gave
  c4d5 at 176,774 nodes vs b1c3 at 72,345 — different moves, different depths). So it is a ratio of times for UNEQUAL
  work and supports no cost claim about the v3 path. What survives is narrow: a 200k-node search took a median 6 %
  less wall time with the net on, per-position spread **1.48x** (bigger than the deviation), 16 of 120 the other way.
  **Method consequence: a real-position COST check compares a patch against its OWN base with identical node rows**
  — which is Step 2's design, so the coordinator's requirement is met there, not here.
- **08-C35: the mechanical fix for 08-W3.** `pc20/emit_config.py` parses a harness's option list with `ast` and prints
  it with "PC20 switches present: N". On the defective script it immediately reports **22 options, 5 PC20 switches
  present** — it would have caught the defect before publication. Renaming the variable would not have.
- **Pattern noted:** all four withdrawals (W1..W4) are a label or a framing, none a measurement. That is itself the
  seat's main finding about itself.

## 2026-11-17T02:28Z — TALLY (generated, not maintained)
**42 findings, 34 checks/audits/plants/tools, 5 method lines, 4 withdrawals** (and 1 open lead).

next: cadence.

## 2026-11-17T02:31Z — the 389/505 attribution corrected AGAIN, and I verified it myself
- **Correct attribution (measured all four cells, not accepted):** **389 and 412 are PC20's figures; 505 and 701 are
  S14's.** My matrix was PC20; seat 27's harness was S14-only. The coordinator's earlier arbitration had the direction
  inverted because it accepted my "S14" label as evidence of my configuration.
- **08-W5 records the second consequence of the 08-W3 variable name: it misled the coordinator's arbitration, not just
  my finding.** A wrong label does not stay in its own file.
- **08-F43 (new, and a better answer than either of us had): the figure is set by ONE option — `HistRework`.** PC20 =
  389; **PC20 minus TtPruneV2 = 501**; PC20 minus HistRework = 389 (unchanged). So 389 requires HistRework.
- **Control-cell caveat confirmed and recorded:** the two-occurrence cell is **not like-for-like across settings** —
  S14 plays `c2c3`/701, **PC20 plays `d2d4`/412** (PC20−TtPruneV2 plays `c2c3`/703). Its purpose survives (neither
  drawn) but quoting it as an equal cell would be wrong.

## 2026-11-17T02:31Z — TALLY (generated, not maintained)
**43 findings, 34 checks/audits/plants/tools, 5 method lines, 5 withdrawals** (and 1 open lead).

next: cadence.

## 2026-11-17T02:33Z — final corrections this block
- **Attribution corrected by my own four-cell measurement + ablations: 389 and 412 are PC20; 505 and 701 are S14.**
  My matrix was PC20, seat 27's harness S14-only.
- **08-F43: the figure is set by ONE option — `HistRework`.** PC20 389; PC20−TtPruneV2 **501**; PC20−HistRework 389
  (unchanged).
- **08-W5: the W3 variable name also misled the coordinator's arbitration** — recorded as the reason for "print the
  list, never transcribe a name".
- Control cell is NOT like-for-like across settings (S14 `c2c3`/701 vs PC20 `d2d4`/412) — recorded.
- **INDEX now carries the self-finding WITH the denominator: five withdrawals out of 43 findings, every one a label or
  a framing, none a measurement error.** Plus the explicit warning not to upgrade W4's 6 % to "the net is faster".

## 2026-11-17T02:33Z — TALLY (generated, not maintained)
**43 findings, 34 checks/audits/plants/tools, 5 method lines, 5 withdrawals** (and 1 open lead).

next: cadence.

## 2026-11-17T02:37Z — emit_config.py v2: seat 27's matcher defects fixed
- **Fix 1: "found nothing" is now a FAILURE, exit 1.** Verified with real exit codes: a file with no option names
  exits **1** with "do not treat this run as a verification"; a recognised file exits 0.
- **Fix 2: recognition by CONTENT against the engine's own 92 `uci` option names**, not by Python shape — so dicts,
  concatenation, comprehensions and shell scripts all work. Verified: my defective script -> **22 names, 5 PC20
  switches**; seat 27's dict+concatenation shape -> **6 names, 2 PC20 switches**.
- **v1 was itself a confident-wrong-answer instance** (matched a list of TEST-CASE tuples, printed "2 options; PC20
  switches present: 0"), recorded as **08-N6** with the second instance from elsewhere tonight and the fix pattern:
  make "found nothing" an error, and recognise by content against an authority.
- **Also my own slip while verifying the fix:** I read `$?` through a pipeline and got `tail`'s exit code — the same
  class a third time, now noted in 08-N6.
- Tool is complementary to seat 27's `expect=` check (theirs validates the list as APPLIED per cell, mine as WRITTEN).

## 2026-11-17T02:37Z — TALLY (generated, not maintained)
**43 findings, 34 checks/audits/plants/tools, 6 method lines, 5 withdrawals** (and 1 open lead).

next: cadence.

## 2026-11-17T02:41Z
- **emit_config.py: pasteable list now deduped by NAME** (one line of work, as suggested) — a pasted list now looks
  like the list that was sent.
- **08-C36: seat 03's S-F7 CONFIRMS.** 30 positions, perft 4, PC r15: **PC-off equals BASE on 30 of 30** AND
  **all five PC20 switches ON equals PC-off on 30 of 30** — so none of the five reaches move generation.
- **08-N7 (new method rule), from my own control failing:** my first control assumed "one move later" changes perft
  and got the identical 400, so the script printed **VOID** rather than a false zero — correct behaviour. Only after
  making the control SEARCH for a differing perft (400 vs 440) did the zero become admissible. **A control must search
  for a case that differs, and a run that cannot demonstrate a difference must invalidate itself.**

## 2026-11-17T02:41Z — TALLY (generated, not maintained)
**43 findings, 35 checks/audits/plants/tools, 7 method lines, 5 withdrawals** (and 1 open lead).

next: cadence.

## 2026-11-17T02:44Z
- **08-C37: seat 13's S-F9 CONFIRMS.** PC r15 PC20 Threads 1, 2 positions x budgets 5k/20k/50k/500k, 5 fresh
  processes per cell: **deterministic in 8 of 8 cells** (identical nodes/depth/bestmove — 41,353 five times, 456,585
  five times) and **never exceeded the budget in 8 of 8**. **Control passes: the budget changes the count**
  (3,616 -> 12,500 -> 41,353 -> 456,585 for rising budgets), so the cap is real, not an ignored parameter.

## 2026-11-17T02:44Z — TALLY (generated, not maintained)
**43 findings, 36 checks/audits/plants/tools, 7 method lines, 5 withdrawals** (and 1 open lead).

next: cadence.
