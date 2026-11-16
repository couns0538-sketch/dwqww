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
