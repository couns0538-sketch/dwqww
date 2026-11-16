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
