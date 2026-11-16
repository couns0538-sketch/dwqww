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

## Mon Nov 16 09:45:23 PM UTC 2026
- job4 DONE: checked 19-F13 (nobody else had). 19-F12 was ALREADY confirmed by seats 05, 10, 17 so I did not duplicate it.
- 29-C1 CONFIRMS the probe_body half (4.86% deep vs 1.95% bench = 2.5x). 29-C2 REFUTES the pick_best>next ordering (6.48 vs 6.53 = a TIE; bench gives the opposite order). My own 29-F7 ordering claim is therefore ALSO not established - recorded honestly.
- Also caught my own 19-F12-class harness bug in this job's first run; the guard turned it into INCONCLUSIVE instead of fake zeros.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_4.md   (check for a newer correction), then re-read THE CYCLE for the next job/check.

## Mon Nov 16 09:49:08 PM UTC 2026
- job5 DONE: cycle 2(c) rerun with SEED+10=2911, new 400-FEN R set (seed verified: 0/50 overlap).
- IMPORTANT: I WITHDREW my own 29-C2 and the ordering part of 29-F7. On random-game positions the same engine shows seat 19's ordering (pick_best 8.06% vs next 5.92%). Recorded as 29-N4.
- 29-F10: move-ordering shares are POSITION-DEPENDENT - quote the position set or the claim is meaningless. 29-F11: TT probe 1.38% bench vs 3.65% deep (2.6x), reproducing 29-C1.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_4.md   (newest correction), then look for another unconfirmed NEW finding to check per THE CYCLE 2(a).

## Mon Nov 16 09:52:00 PM UTC 2026
- Warm/cold rule from seat 10 audited: REPRODUCED exactly (same process 56,720/4,951/4,516; fresh processes 56,720x3; ucinewgame restores cold). Written up as WARM_AUDIT.md + 29-C3.
- My S14 known sums (O=9,500,069, G=18,466,239) used ucinewgame per position, so they are COLD and STAND.
- My job4/job5 share tables are WARM and now LABELLED as warm (29-N5); they published no node counts.
- Also finished a 19-F10 check before this: interleaved 48 pairs, 2 builds/side, nodes identical on every run, patch/base time ratio 1.0943 CI [1.0734,1.1155] => CONFIRMS 19-F10's ~8% prefetch slowdown.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: warm/cold audit + 19-F10 check' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 09:52:50 PM UTC 2026
- 19-F6 checked: its 2.71% magnitude is NOT reproducible on my build (the material-key line is 0.153%, ~18x less); the call count cannot be checked because material_key is inlined. Its practical conclusion (caching the key is neutral, 19-F9) is not disputed.
- My attempt to time it by toggling MaterialCorrectionWeight was REFUSED by my own guard: weight 0 changes the node count (792,487 vs 862,329), so no timing comparison is valid there. Recorded rather than fudged.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29 job7: 19-F6 magnitude not reproduced' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 09:55:00 PM UTC 2026
- job8 DONE: a real, provably-safe speed patch (29-F12) in the TT replacement path: -9,081,823 instructions (-0.201%) per bench 13, all four honesty node counts unchanged, 40/40 searches bit-identical, no measurable wall-clock change. Patch: job8/tt_replace_skip_slot0.patch.txt (applies patch -p1, no fuzz).
- This is the second patch I have proved correct; unlike job2's it also REDUCES work measurably in instruction count.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29 job8: TT slot-0 comparison removal (-0.201% instructions, node counts identical)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29
