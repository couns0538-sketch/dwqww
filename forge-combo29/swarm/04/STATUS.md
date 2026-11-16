seat: 04
branch: for-fable-and-opus/swarm-04
area: 4
seed: 401

## 2026-11-16T21:06:29Z
seat claimed. next: STEP 2 build of 6b98f217 + honesty check.

## 2026-11-16T21:20:30Z
STEP 2 done: 4/4 honesty numbers match (forge-combo29/swarm/04/honesty/HONESTY.txt). TSAN build built (nm __tsan_ = 21).
Sanitizer proof (1) done: planted unlocked-global counter on a scratch copy at /home/ubuntu/planted (search.cpp:2154)
is reported by TSan through THE SAME RUNNER (job1/planted_proof_raw.txt). Proof (2) done.
job1 running: Threads 1,2,4,8,16 x 100 G positions x depth 12 x 2 reps = 1000 searches, one process each.
Progress: 2026-11-16T21:20:30Z rep1_t1=100 rep1_t1.log= rep1_t2=100 rep1_t2.log= rep1_t4=90 rep1_t4.log= 

## 2026-11-16T21:36:19Z CHECKPOINT PUSH
HARNESS AUDIT after seat 19's warning: my runner (job1/run_searches.py) writes `quit` at exactly one place
(line 91, inside Engine.close()) and only AFTER read_until("bestmove") returned; every search is its own
process. audit_harness.py over the records written so far: 0 records with no node count, 0 with 0 nodes,
0 with a2a3-at-0-nodes, 100 % of bestmoves legal (job1/audit_harness.txt). My job1 records are NOT
pipelined-quit records; no re-run is needed for that reason.
quit/EOF probe (job1/quit_eof.py, CHECK of 19-F12, not my own finding): control A on startpos = e2e4 at
56,720 nodes / 12 info lines; B (`quit` immediately) and C (EOF) = bestmove a2a3 with 0 info lines.
So 19-F12 reproduces on my release build. Full 3-position x 8-case table running now.
job1 sweep (TSAN, Threads 1/2/4/8/16 x 100 G positions x 2 reps): rep1 t1/t2/t4/t8 done, t16 running.
Next command: cd /home/ubuntu/runs && tail -3 stamps.txt; python3 /agent/repos/dwqww/forge-combo29/swarm/04/job1/analyse.py /home/ubuntu/runs
