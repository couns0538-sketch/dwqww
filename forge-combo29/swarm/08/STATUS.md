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
