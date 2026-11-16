## 2026-11-16T21:07:00Z (seat claim)

branch for-fable-and-opus/swarm-24
folder forge-combo29/swarm/24/
area 4 (THREADS under ThreadSanitizer)
seed 2401

Next: STEP 2, build commit 6b98f217 release in ../base and run the four honesty numbers.

## 2026-11-16T21:13:30Z
done: STEP 1 seat 24; STEP 2 build (Release, gcc 13.3, x86-64-v4, sha256 e06310ec...) honesty check ALL FOUR MATCH
      (bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609) -> HONESTY.txt.
      TSan build (RelWithDebInfo + -fsanitize=thread, nm __tsan_ = 21) in /agent/repos/base/forge-combo29/build-tsan.
      job1 prediction pushed alone before measuring. Planted-fault control PASSES: 102 TSan reports through the
      same runner (job1/run_planted.sh), so "0 reports" will count.
runs: job1 threads sweep (Threads 2/4/8/16, first 100 of G, depth 12, S14) under TSan, t2 at 90/100, 0 TSan lines.
next: finish t4/t8/t16, analyse.py table, REPORT_job1.md, then job 2 (option churn between searches).
