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
