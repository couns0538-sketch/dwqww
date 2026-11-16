# SWARM SEAT 29

seat: 29
area: 9 (SPEED)
seed: 2901
branch: for-fable-and-opus/swarm-29
Mon Nov 16 09:06:21 PM UTC 2026

## Mon Nov 16 09:13:32 PM UTC 2026
- STEP 1+2 done: seat 29, area 9, seed 2901, branch for-fable-and-opus/swarm-29.
- HONESTY.txt: all four numbers match (bench 11/13/16 + perft 5) on /home/ubuntu/build/base/forge.
- job1 (profile bench 13) DONE: two perf runs, top ten listed, all 6 predictions survived. REPORT_job1.md pushed.
- next: job 2 - ONE speed patch that changes no node count, 10x bench 13 alternating base/patch, ratio + 95% interval.

## Mon Nov 16 09:27:50 PM UTC 2026
- job1 DONE and pushed. job2 in progress: profiling deep-dive found the 16 MB TT clear costs 227M instructions ONCE per process (34% of bench 1, 5% of bench 13) - a constant, not a hot spot.
- job2 candidate patches tried: `__restrict` on the eval pawn-cache pointer = DUD (+0.006% instructions, rejected, not kept).
- next command: cd /agent/repos/patched && git checkout -- . && edit src/board.cpp (pinned-only path for has_legal_move), then build twice and run the 10x alternating bench 13 pair test.

## Mon Nov 16 09:33:04 PM UTC 2026
- job2 DONE and pushed: one text patch (pinned_only_king_lines.patch.txt) proved bit-exact (40 positions x depth 10, 130/130 perft) and NEUTRAL in speed (ratio 1.0178, CI [0.984, 1.057]; instructions -0.056%). REPORT_job2.md written honestly, including the false +3.6% from the non-interleaved design.
- new findings 29-F3/F4/F5 pushed.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_1.md   (then THE CYCLE step 1b, then job 3: the next hot spot).

## Mon Nov 16 09:36:23 PM UTC 2026
- CHECKPOINT PUSH (owner 30-min rule). Harness audited after seat 19's broadcast: fault REPRODUCED (pipelined go+quit -> 0 info lines, a2a3), and bench/perft proved SYNCHRONOUS so my honesty numbers and job1/job2 results all stand. Audit in job2/harness_audit.py + raw_harness_audit.txt.
- BONUS VALIDATION: brief's S14 known sums reproduced exactly on the plain build - O depth12 = 9,500,069 and G depth12 = 18,466,239. Also found S14 needs NonPawnCorrection true explicitly (source default is false; with defaults O depth12 = 12,573,318).
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && cat job2/raw_rows_sums.txt  (write REPORT_job3.md for this validation), then start job 3 proper: the next hot spot OUTSIDE the evaluation, per FABLE_TO_swarm_2 Rule 2.

## Mon Nov 16 09:38:07 PM UTC 2026
- job3 DONE and pushed. Honest headline: NO second speed patch - everything bit-exact I found was worth <0.1% of instructions; the real remaining lever (move scoring imbalance, 4.5x) cannot be exploited without changing node counts.
- Predictions: P1 SURVIVED (corrected 6.96x -> 4.5x, self-corrected in 29-N3), P2 SURVIVED, P3 SURVIVED (reported as the outcome, not a win), P4 KILLED (checkers is 11.8% of make_move, not >=40%).
- 29-F9: no NNUE v3 net file exists on ANY branch, so nobody can profile the PC's real path - worth Opus knowing.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_4.md   (re-read the board for a newer correction, then THE CYCLE step 1a/1b: look for an unconfirmed NEW finding of another seat to check).
