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

## Mon Nov 16 09:55:31 PM UTC 2026
- IMPORTANT negative result recorded (29-N6): my cold deep-search timing of the TT patch first showed an apparent 2.6% speedup (ratio 0.9739), but three repeats of the identical script gave 1.0004, 1.0408, 0.9987. That was NOISE. 29-F12 stands only on its exact instruction count (-0.201%), not on any wall-clock claim.
- This is the third time on this machine that a single timing comparison has produced a fake multi-percent win; the interleaved/repeated design caught it each time.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29 job8: record negative result N6, no wall-clock claim for F12' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 09:55:53 PM UTC 2026
- 29-F12 now has a sensitivity control (Rule 1 satisfied): the stress test at Hash 1 (constant eviction) gives 4/4 IDENTICAL for the real patch, and 4/4 DIFFERENT for a PLANTED wrong replacement rule (<= instead of <). So the equivalence result is a real measurement, not a blind comparison.
- TT patch status: correctness PROVEN by three routes (4 honesty counts, 40/40 depth-10 searches, 4/4 hash-pressure stress + plant). Speed: exact instruction count -0.201%; NO wall-clock claim (29-N6).
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: TT stress equivalence + planted control (29-F13)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 09:56:05 PM UTC 2026
- 29-N7: caught a SECOND 19-F12-class harness fault in my own work. A thread-legality table showed bestmove a2a3 for both positions at all thread counts - the tell was that every entry was identical. Rewrote the driver to drain to bestmove: now d2d4 / e2a6 / e2e4 / e2a6 / g1f3 / e2a6, all legal at Threads 1, 4, 8.
- TT patch (29-F12) is now verified: 4 honesty counts, 40/40 depth-10 bit-identical, 4/4 hash-pressure stress bit-identical with a planted-fault control, and legal moves at 1/4/8 threads.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: thread sanity + N7 second harness-fault catch' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 09:56:33 PM UTC 2026
- 29-N8: I wrote a vectorised TT hit scan that was WRONG - sizeof(TTEntry)==16, so one __m128i load covers ONE slot, not four. Node counts jumped to 347,176 / 700,414 / 2,333,149 and the honesty check caught it immediately; patch reverted, base restored to 862329.
- Lesson recorded: any vectorised cluster scan must use strided gathers for key32 at offsets 0/16/32/48, not a flat 128-bit load. This is the value of running all four honesty numbers on every build.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: record N8 wrong vector TT scan caught by node counts' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 09:58:13 PM UTC 2026
- 29-F14: SECOND TT win, combined with F12: -18,708,563 instructions (-0.414%) per bench 13. All honesty counts identical, 40/40 searches bit-identical, 4/4 hash-pressure identical, legal moves at 1/4/8 threads. Patch saved as job8/tt_slot0_and_vector_probe.patch.txt.
- 29-N9 HONEST LIMIT: my planted-fault control caught the replacement-rule error (4/4 DIFFERENT) but NOT the occupancy-check error (4/4 IDENTICAL, bench still 862329). So my equivalence evidence is strong for replacement logic, weak for occupancy handling. Stated plainly.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: combined TT patch F14 + honest limit N9' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:01:14 PM UTC 2026
- 29-F15 CLOSES the 29-N9 gap: wrote a cluster-level unit test (public interface only) that walks a cluster through fill + eviction and prints every probe result. Base and patched traces are BYTE-IDENTICAL (empty diff). So the TT changes are behaviour-identical at cluster granularity, not merely in search output.
- Two notes on the test itself: (a) my first version asserted an absolute expectation and 'failed' because keys landing in one cluster evict each other - that was my wrong expectation, not an engine bug; (b) the corrected version compares base vs patched behaviour, which is the property under test.
- TOTAL TT result: -18,708,563 instructions (-0.414%) per bench 13, all four honesty counts identical, 40/40 searches bit-identical, 4/4 hash-pressure cases identical, legal at 1/4/8 threads, cluster traces identical.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: TT cluster-level unit test, base==patched byte-identical (F15)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:01:36 PM UTC 2026
- CONSOLIDATION for the 22:30 deadline. FINDINGS.md final: 30 entries (F1-F15 findings, C1-C5 checks of other seats, N1-N9 notes/withdrawals/limits). All 5-column F/N rows and 4-column C rows well-formed; 29-C2 now marked WITHDRAWN at the point of reading, not only in N4.
- Deliverables on the branch: 9 reports (job1-job9), 3 patch files (pinned_only_king_lines, tt_replace_skip_slot0, tt_slot0_and_vector_probe), HONESTY.txt, STATUS.md, and every jobN/ raw output + script.
- Best result of the run: 29-F14 TT patch, -18,708,563 instructions (-0.414%) per bench 13, correctness proven 5 ways (4 honesty counts, 40/40 searches, 4/4 hash pressure, 1/4/8 threads, byte-identical cluster trace vs base). No wall-clock claim (29-N6).
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: final consolidation for deadline' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:02:48 PM UTC 2026
- 29-N10: method limit found while trying to extend the TT result to deep search. bench-13 instruction counts are EXACTLY reproducible (4,513,768,543 twice, to the digit). A single go-depth-12 count is NOT: same build, same position gave 84,270,074 and 84,194,377 (0.09% spread). My deep-search comparison showed both signs across 5 positions and was DISCARDED.
- So the -18,708,563 figure for 29-F14 stands on the deterministic bench measurement only, and I make no deep-search claim for it.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: record N10 callgrind determinism limit' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:04:51 PM UTC 2026
- FINAL PATCH HARDENED for a reader who might apply it. The patch file now opens with a READ-THIS-FIRST block: (1) NO wall-clock claim, (2) NO claim about a search with a loaded NNUE network - the owner's PC uses its own king-bucket net, no network file exists on any branch, so the effect on the PC build is UNMEASURED.
- RISK is machine-enforced, not prose: the four-lane gather reads entries[i].key32 by NAME, so it assumes nothing about sizeof(TTEntry)/padding/byte order (endian-independent); its only dependency (exactly 4 slots) is a static_assert which I PROVED fires on a 5-slot cluster AND on the 8-slot-8-byte case that the existing sizeof==64 assert cannot catch.
- Re-verified after the change: 312866/862329/3024920/4865609 all identical, 40/40 searches bit-identical, 4/4 hash-pressure identical, legal at 1/4/8 threads, patch applies to clean base patch -p1.
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && cat job8/tt_slot0_and_vector_probe.patch.txt | head -25

## Mon Nov 16 10:18:41 PM UTC 2026 CONTINUE: 12 more hours, ends at 2026-11-17T10:18:41Z
- Seat 29 kept (from ~/swarm_seat.txt), branch for-fable-and-opus/swarm-29, area 9 SPEED, seed 2901.
- Next: fetch handoff branch, read EVERY unread FABLE_TO_swarm_N.md from lowest N up; file 5 holds the PC engine as a patch against 6b98f217 (apply in a SEPARATE copy with -DFORGE_MATE_ALPHA_GUARD=1), build it, check its known bench numbers, then re-run my findings on the PC build under settings PC20.
