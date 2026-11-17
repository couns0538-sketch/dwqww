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

## Mon Nov 16 10:20:23 PM UTC 2026
- THREADS RULE (seat 04) audited against all my results: every score and every node count I have ever reported was Threads 1. grep over all my scripts finds exactly ONE non-1 usage: job8/tt_threads_sanity.sh at Threads 1/4/8, which by design asserts no score and no node count (legality + completion only). So nothing of mine is provisional; 29-F14's 'legal at Threads 1/4/8' is a legality claim only. Recorded as 29-N12.
- PC r15 build: patch sha256 verified d6bd72c531f785f4..., applied to a SEPARATE worktree (/agent/repos/pc), built with -DFORGE_MATE_ALPHA_GUARD=1. Known-answer verification running.
- next command: tail -25 /home/ubuntu/.cursor/projects/agent-repos-dwqww/terminals/758550.txt   (PC build known-number verification)

## Mon Nov 16 10:25:00 PM UTC 2026
- PC r15 BUILD VERIFIED (29-F16): patch sha256 matches, 11 files apply clean from inside forge-combo29/, builds with -DFORGE_MATE_ALPHA_GUARD=1, 92 options all PC20 options present, and ALL EIGHT known numbers match: none 312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276. Threads 1, fresh process per line. REPORT_pc0.md.
- Apply-path note for other seats: the patch paths are a/include/... relative to forge-combo29/, so patch -p1 must run INSIDE forge-combo29/ (or git apply --directory=forge-combo29 from the root); running from the repo root without the hint fails at file 2.
- Files 4 and 5 read. File 4 confirms my 29-F6 independently (defaults give O depth12 = 12,573,318, exactly my control).
- next command: cd /agent/repos/dwqww/forge-combo29/swarm/29 && python3 job2/rows_sum.py ~/build/pc/forge job2/O.fens 12 S14   (check the PC build reproduces the S14 sums)

## Mon Nov 16 10:27:15 PM UTC 2026
- 29-F17: FIRST profile of the PC build under PC20 (Threads 1, 200 random-game positions, depth 12): evaluate_position 14.19, Worker::search 12.54, apply_and_evaluate 9.46, pick_best 7.24, next 6.01, probe_body 5.61, corrected_eval 5.11, see_ge 4.05, qsearch 3.95, fill_pseudo_legal 2.09.
  -> The pick_best > next ordering from my 29-F10 random-game result REPRODUCES on the PC build (7.24 vs 6.01).
  -> probe_body 5.61% is HIGHER than either base-tree figure I had (1.38 bench / 3.65 deep), so my TT patch targets a hotter path on the PC build than my base measurements suggested.
- 29-F18: the PC build reproduces the S14 O depth-12 sum EXACTLY (9,500,069), so S14 numbers are comparable across both builds.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: PC20 profile F17 + S14 sum reproduced on PC build F18' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:31:47 PM UTC 2026
- 29-F19 IMPORTANT REVERSAL: my TT patch (F12+F14) is a WIN on the base tree (-18.7M instructions) but a LOSS on the PC r15 build under PC20 (+11.3M; slot-0 half alone +19.7M). Node counts identical, all 8 known numbers still match. It must NOT be quoted as a PC-build speedup. Threads 1 throughout.
- Swarm warning 29-N13: the PC patch must be applied with 'patch -p1' FROM INSIDE forge-combo29/ (its paths are relative to it). I silenced the output once and the patch was silently skipped, which briefly looked like a behaviour change. Confirm applied state by checking the option list, never by absence of an error.
- General lesson for every seat: a base-tree instruction saving is NOT evidence about the PC build. Re-measure there.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: TT patch reverses on PC build (F19) + patch-apply warning (N13)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:32:36 PM UTC 2026
- 29-F20/F21: measured QUALIFICATION of file 2 Rule 2. On the PC r15 build the hand-written eval IS on the search path in every configuration reproducible here: NNUEArch defaults false, and with 'NNUEArch true' but NO net file, v3::active() is still false (requested && loaded()!=nullptr), so evaluate_runtime is called 357,740 times during bench 13 under PC20 - identical with and without NNUEArch. The build's 'eval' also prints a residual split (hce 18 + nnue 20).
- NOT a refutation of Rule 2: I could not test the owner's real configuration (the net file is not shared). With a net loaded, loaded()!=nullptr and Rule 2 may be exactly right. Stated as a qualification with that limit explicit.
- Practical consequence for area 9: on the PC build I CAN build, eval optimisation is not worthless - but nobody should act on that for the owner's PC until a net is available to test.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: measured qualification of Rule 2 (F20/F21), TT reversal (F19), apply warning (N13)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:33:22 PM UTC 2026
- 29-C6 CONFIRMS seat 05's S-F23, checked with my own harness on the PC r15 build at depth 12, Threads 1, using THEIR two truncated boards: under S14 both are truncated (O+G/192 mate -9, R/120 mate -13 with a 12-move PV against 26 needed); under PC20 neither is, and R/120 reports exactly cp -2713, the figure they published. Their 0-of-27 vs 2-of-28 rate reproduces.
- This is the first finding of another seat I have confirmed on the PC build under PC20, which is the regime TEXT 2 asks for.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: 29-C6 confirms 05 S-F23 on PC build under PC20' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:39:46 PM UTC 2026
- CALLGRIND AUDIT ANSWER (29-N14/N15): the numbers are SOUND. The challenge is right that valgrind cannot run the AVX-512 LOCK build - I hit that in job 2 myself (Illegal instruction, exit 132, preamble-only file; still in job2/raw_callgrind.txt). Every published instruction count comes from a separate FORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 build with ZERO zmm instructions (objdump on all four binaries = 0), where callgrind completes with exit 0 and 'Trigger: Program termination'.
- Re-verified now, side by side: portable exit 0 / PROGRAM TOTALS; lock build exit 132 SIGILL.
- Rule 1 control (29-N15): planted 8 extra increments per eval -> 2,052,702,072 vs clean 2,052,508,756, i.e. +193,316 DETECTED. The tool measures and responds to a planted change.
- One correction to the challenge: the two numbers it names are from TWO experiments - 4,513,768,536/-0.056% is the job-2 __restrict DUD (reported as no effect, rejected); -0.414%/18.7M is job 8/9 (4,513,768,543 -> 4,495,059,980/987). Both portable-build counts.
- TT patch status unchanged: F12/F14 instruction claim STANDS; the bit-identical-search and legal-move evidence was never load-bearing on it.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: callgrind audit - portable vs lock build, exit statuses, Rule 1 planted control' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:40:30 PM UTC 2026
- FILE 6 READ. Took its suggested new area, since my own area's 3 jobs are done. REPORT_soft.md + 29-F22/F23/F24:
  - 29-F22 DETERMINISM: 24/24 fresh-process runs identical (depth, nodes, score, move) across N=2000/20000/50000/250000. Holds.
  - 29-F23 FINISHED DEPTH: 9/9 cases reproduce exactly under a plain 'go depth D' at the reported depth, so no mid-iteration truncation.
  - 29-F24 OVERSHOOT: median 1.20-1.42x N, worst 3.01x, and the documented 4x hard stop NEVER bound (0 of 48). Bounded by iteration granularity, not by the backstop.
- File 6's two verdict changes noted: draw-scored-0 and >1-thread variation are NOT defects (I have no such findings to withdraw: my N12 audit showed every score I published is Threads 1, and my only >1-thread use asserted no score).
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29 soft: softnodes determinism, finished-depth and overshoot (F22-F24)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:41:00 PM UTC 2026
- PC-path clock work (file 6 names 6s+0.06 as what the PC's strength matches do), 2 new findings:
  - 29-F25: at a FIXED node budget the search is exactly deterministic (go nodes 300000 -> depth 16 / 285,420 / cp 1125 / b2d1 in 4 of 4 runs). On the 6000ms CLOCK the same position alternated depth 16 (285,420, cp 1125) and depth 17 (820,149, cp 1230) across 6 runs - but the MOVE was b2d1 in all 6. So the variation is the stop timer, not search nondeterminism.
  - 29-F26: on 6s+0.06 the engine uses a median of 210 ms of its 6000 ms budget (~3.5%), 0 of 40 overran, 0 illegal moves, no rep-to-rep move changes.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29 soft: clock determinism vs node-budget determinism (F25), clock budget use (F26)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:41:13 PM UTC 2026
- 29-F27 explains 29-F26 so it cannot be misread as wasted time: the per-depth cost grows ~1.4x per ply (182 ms at depth 16), so against a 1204 ms soft budget the engine finishes depth 16 early and declines to START depth 17. That is disciplined depth-boundary time management; the consequence is that it uses ~210 ms median of a 6000 ms clock.
- Clock plan for wtime 6000 winc 60 with default divisors (computed from include/forge/clock_plan.hpp): available 5990, soft 1204, hard 4792 ms.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29 soft: mechanism behind low clock usage (F27)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:43:18 PM UTC 2026
- (1) NAMED RULE 29-N16 added at the TOP of FINDINGS.md with my own patch as the worked example: base tree -0.414%, PC r15 build under PC20 +0.320%, and each half worse alone (+0.558% slot-0, +0.634% vector). Consequence: re-measure on the build you intend to recommend.
- (2) REVERSAL MECHANISM FOUND (29-F28): ran a proper 2x2 factorial (base / slot-0 only / vector only / both) on the PC build. BOTH halves reverse, the effect is NON-ADDITIVE (-0.872% interaction), node counts identical in all four builds, and the two probe bodies are byte-identical between base and PC trees. Where it lands: Worker::search self cost 4.88% -> 7.03% while probe_body's own symbol SHRINKS (31.5M -> 15.5M) => the compiler re-inlines part of the probe into search. So it is inlining/layout, not logic. REPORT_pc2.md.
- (3) go nodes path next (the job I already have data for: 0 nondeterministic of 24, 0 illegal).
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: named rule N16 + 2x2 factorial mechanism for the PC reversal (F28)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:43:35 PM UTC 2026
- 29-F29 hard-budget path settled: go nodes N (20000/50000/250000) on PC r15 under PC20 Threads 1, 12 positions x 3 N x 2 reps = 36 runs: 0 nondeterministic, 0 NOT reproducible by go depth D, 0 illegal, and 0 runs exceeded N (node use 0.54-0.99 of N). So the hard budget is respected exactly.
- 29-F30 the two modes have OPPOSITE contracts, both honoured: go nodes never exceeds N and always ends on a completed iteration; go softnodes finishes the iteration that passes N and overshoots (median 1.2-1.4x, worst 3.01x, never past 4x). Harnesses wanting exact reproducibility should use go nodes.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29 soft: go nodes hard-budget path (F29) and the two modes contracts (F30)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:44:48 PM UTC 2026
- 29-F31 + 29-N17: I made the inlining explanation a MEASUREMENT and it REFUTED my own 29-F28 mechanism. probe_body<false> is 119 -> 140 instructions (LARGER) after the patch, identically on both trees; probe_owned collapses 116 -> 18 insns on both. So 'a more expensive inlined copy' is wrong. What the code shows: the sign is set by whole-program outlining/layout - on the base tree the hot Worker::search(Board&,SearchStack*,...) keeps its EXACT size (15,693 bytes) patched, while on the PC tree a stable_sort instantiation inside search(Board,limits,...) grows +639 bytes.
- 29-N17 lesson: profiler self-cost shares are NOT object-code evidence. Work moving between symbols is not the same as work getting cheaper or dearer.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: disassembly refutes my own inlining mechanism (F31/N17)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 10:46:33 PM UTC 2026
- 29-F32 THIRD CLOCK MEASUREMENT (the ask): 6s+0.06, PC r15 build, PC20, Threads 1, Hash 16, 60 real positions. min 1.4 / median 203 / p99 474 / max 945 ms. 0 of 60 past the computed SOFT limit (1204 ms), 0 of 60 past HARD (4792 ms). Median uses 3.4% of the clock.
- This does NOT reproduce seat 08's 46-of-200 past soft, but the regimes differ (08: 10 s clock, base tree; mine: 6 s+inc, PC r15 under PC20), so I do NOT claim 08 is wrong - I state the conditions and leave the comparison to the reader.
- 29-F33: 3 of the 60 reach depth 64 (finished/terminal boards, 1.4-78.5 ms) which inflates the depth tail; excluding them depths are 12-27. Same class as seat 05's S-F7 seen from the clock side.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29 soft: third clock measurement at 6s+0.06 (F32) and terminal-root depth tail (F33)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 11:20:25 PM UTC 2026
- 29-C7 CONFIRMS 19-F19 on my own instrumentation (counters inside probe_body, PC r15 build, Threads 1, Hash 16):
  bench 13  : 587,244 probes / 203,057 hits -> slot0 96.0%, slot1 3.8%, slot2 0.2%, slot3 0.0%, gen writes 0.
  real games: 17,568,527 probes / 6,084,620 hits -> 26.3 / 25.3 / 24.7 / 23.7 %, gen writes 16,811 (0.28%).
  Direct bench run reproduced their exact total: 285,437 hits, 265,609 in slot 0 = 93.06%, 0 gen writes. Mine reads 96.0% because my run is PC20.
- CONSEQUENCE FOR MY OWN PATCH: bench concentrates hits on slot 0, so a slot-0 optimisation is flattered by bench and NOT transferable to real games. That is a direct caveat on my 29-F12/F14 story and I have recorded it.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29 slots: confirm 19-F19 and record the consequence for my own patch' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 11:21:32 PM UTC 2026
- 29-F34 picker split on the PC build under PC20 (bench 13, Threads 1, exact callgrind instructions, denominator = PROGRAM TOTALS): scoring 102,907,864 = 2.91%, selection 27,060,838 = 0.77%, dispatch 21,943,328 = 0.62%, generation 896,256 = 0.03%. Scoring costs 3.8x selection; the biggest single line is the stage switch (0.62%), then the two continuation-history reads and the main history read.
- Two harness bugs of mine caught in this job and fixed: (a) callgrind_annotate with --auto=yes repeats every line across sections so my attributed sum was 13.6B against a 3.5B total - switched to --auto=no; (b) I was dividing by the SUM OF PICKER ROWS instead of PROGRAM TOTALS, which inflated every share ~4x. Both now guarded (the script ABORTS if PROGRAM TOTALS is missing).
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29 slots: picker stage split on PC20 (F34)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 11:21:36 PM UTC 2026
- 29-N18 CAVEAT ON MY OWN 29-F12, derived from the 29-C7 slot data: bench puts 96% of TT hits in slot 0 but real games spread them 26.3/25.3/24.7/23.7%. My slot-0 change is weighted almost entirely to the slot-0 case, so bench OVERSTATES its benefit by ~3.7x in opportunities. Combined with F19/F28 (no saving on the PC build), the honest status of 29-F12/F14 is: behaviour-neutral, instruction-count only, flattered by bench, NOT a PC speedup - a code-cleanliness change, not a performance win.
- That closes the loop on my own headline patch with three independent reasons not to recommend it for speed: (1) it reverses on the PC build, (2) the win is bench-weighted, (3) its only evidence is instructions, never wall time.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: caveat N18 on my own F12 from the slot distribution' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 11:22:34 PM UTC 2026
- 29-F35 generalised the slot finding into its own rule: bench 13 puts 96.0% of TT hits in slot 0 (203,057) while a real-game set at d12 spreads 26.3/25.3/24.7/23.7% (6,084,620 hits), so a slot-0-sensitive change looks ~3.7x better under bench purely from workload shape; and bench hits the age/depth replacement path 0 times against 16,811 generation writes on real games. RULE: any TT optimisation must be measured on real-game positions, never on bench.
- 29-F36 the recommendation, stated and closed: scoring 2.91% vs selection 0.77% (3.8x), largest lines are the two continuation-history reads (21.5M, 20.6M) and the main history read (17.2M) => the lever is FEWER HISTORY READS PER MOVE, not a faster sort (19-F15 shows the sort is load-bearing). Picker family is ~4.3% of the run = second-order behind the evaluation.
- next command: cd /agent/repos/dwqww && git add -A forge-combo29/swarm/29 && git commit -m 'swarm 29: bench-is-not-representative rule (F35) and the move-ordering recommendation (F36)' && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-29

## Mon Nov 16 11:22:43 PM UTC 2026
- Housekeeping: the NAMED RULE block at the top of FINDINGS still carried the inlining explanation that my own disassembly refuted (F31). Corrected it in place and added the -0.872% interaction + the 29-N17 lesson. Both named rules now sit together at the top: (1) instruction-count savings do not transfer between builds, (2) bench is not a representative workload for slot-sensitive optimisations.
- Row-format audit of all 62 FINDINGS rows: clean.
- next: continuing on the PC path.

## Mon Nov 16 11:23:11 PM UTC 2026
- 29-F35 extended as asked: one paragraph now carries BOTH bench objections in one place - (1) the slot distribution it samples (96.0% slot0 vs 26/25/25/24% on real games, 0 vs 16,811 generation writes) and (2) the code paths it never enters (the age/depth replacement scan). Conclusion stated once: bench is the wrong instrument for TT work on both grounds.
- Attribution made precise while doing it: the '0.006% of probes reach the replacement scan' figure is seat 19's (19-F18) and I have NOT re-measured it, so it is labelled as theirs with my own supporting direction (0 vs 16,811 generation writes) named separately. A rule block should not launder someone else's unverified number as my own.
- next: continuing on the PC path.

## Mon Nov 16 11:24:15 PM UTC 2026
- 29-C8 CONFIRMS 19-F18's bench half TO THE DIGIT with my own instrumentation: bench 13 has 861,904 probes (their exact total), 576,467 enter the replacement scan, 576,417 find an empty slot, leaving exactly 50 (0.0058%) that do an age/depth comparison. Real games (20 positions, depth 12): 2,501,519 probes -> 457,712 (26.5%) do age/depth work, same direction as their 54.7% but a smaller set.
- This is the second independent bench objection now inside the 29-F35 rule, and it is no longer labelled 'unverified by me' because I have now measured it.
- next: continuing on the PC path.

## Mon Nov 16 11:32:37 PM UTC 2026
- 29-F37 answers the 26.5% vs 54.7% question WITH DATA, and corrects my own 29-C8 caveat. Measured the rate as a function of set size (20 -> 200 positions, running rate every 20):
    default options: 26.5% at 20 positions -> 19.5% at 200 (small set OVERSAMPLES by 7 points)
    PC20           : 13.6% at 20 -> 11.1% at 200, flat from 40 positions on
- So: (a) my 29-C8's 26.5% was measured under DEFAULT options, which is why it disagreed with the 11.1% I now get under PC20 - SETTINGS were the difference, not set size; (b) the LARGER set is the more representative one, and the honest PC20 figure is ~11%; (c) seat 19's 54.7% is not reproduced in either regime on my positions (my maximum is 19.5%), so that gap is not a set-size effect and likely reflects a different position distribution (theirs R_1911).
- next: continuing on the PC path.

## Mon Nov 16 11:32:48 PM UTC 2026
- Corrected the superseded figures in two places so no reader meets 26.5% as current: 29-C8's row is annotated 'SUPERSEDED IN PART by 29-F37' and the 29-F35 rule block now quotes 11.1% (PC20, 200 positions) with 19.5% (defaults) as the alternative, and states plainly that I do NOT reproduce 19-F18's 54.7% in either regime.
- 29-N19 records the abort-on-zero habit as you asked: two failed instrumentation attempts in one night caught by guards rather than reporting '0.0% of probes reach the scan' - which would have been a spectacular false confirmation of the very claim under test.
- next: continuing on the PC path.

## Mon Nov 16 11:33:12 PM UTC 2026
- 29-N19 'a zero must always be a measurement, never a default' is now THE FIRST RULE at the top of FINDINGS, with the four worked cases (0-probe binary, --auto=yes double count, wrong denominator, checkout mid-build) and the implementation rules (assert anchors, assert parsed fields, assert the denominator is PROGRAM TOTALS, print NOT FOUND/INCONCLUSIVE never 0).
- 29-F38 states the FINAL figure plainly: 11.1% age/depth replacement rate under PC20 (200 positions, depth 12, Threads 1, Hash 16); 13.6% at 20 positions; 19.5% under defaults; bench 0.006%. Seat 19's 54.7% is a DIFFERENT POSITION DISTRIBUTION, not an error - their bench 50 reproduces to the digit on my counters.
- FINAL_NOTES.md prepared so the required '## <time> FINAL' block at 10:18Z can be written quickly and completely.
- next: continuing on the PC path.

## Mon Nov 16 11:36:06 PM UTC 2026
- 29-F39 IMPORTANT, and it partially OVERTURNS the figure I was about to put in the FINAL: the replacement-scan age/depth rate is NOT ~11% - it swings 0.1% to 44.8% with depth and Hash on the same binary. Sweep (PC20, Threads 1, 60 positions): Hash16/d10 6.3%, Hash16/d12 44.8%, Hash64/d10 0.1%, Hash64/d12 2.4%.
- Probes are IDENTICAL per depth across Hash sizes (1,372,713 at d10; 4,087,859 at d12), so table size does not change the search at all - it only changes how many scans find an EMPTY slot, i.e. whether the table is saturated. That is the real mechanism.
- 29-N20: FINAL must quote the four-cell table plus the one robust claim (bench 50 of 861,904 = 0.006%), NOT '11.1%'. Correcting before the deadline rather than shipping a number a two-line sweep contradicts.
- next: rewriting FINAL_NOTES.md accordingly, then continuing.

## Mon Nov 16 11:36:54 PM UTC 2026
- 29-N21 percentage audit done as asked: grep for 11.1/26.5/19.5/54.7/44.8 across all 13 REPORT_*.md returns ZERO hits. FINDINGS keeps the four-cell table, explicitly SUPERSEDED rows, and the counter-instruction; FINAL_NOTES leads with the correction. Every instance mapped file:line in slots/AUDIT_percentages.md.
- Deliberate exception stated rather than silently fixed: STATUS.md is append-only, so its earlier blocks still contain my then-belief (11.1% as the figure). Rewriting them would destroy the record of what I concluded when; the later blocks correct them. I say so in the audit rather than quietly tidying history.
- next: continuing on the PC path.

## Mon Nov 16 11:39:08 PM UTC 2026
- 29-F40: PC20 is not cosmetic - measured on the PC r15 build, 30 real-game positions at depth 12, Threads 1, Hash 16: S14 = 3,078,383 nodes (102,612/position) vs PC20 = 2,478,658 (82,621/position), i.e. PC20 searches 19.5% FEWER nodes at the same depth on the same positions. Matches the bench pins (656,517 -> 587,276) and explains why base-vs-PC20 comparisons are comparisons of different tree sizes, not just different ordering.
- Audit amended as asked: the append-only exception now sits at the TOP of slots/AUDIT_percentages.md, not only in the table.
- next: continuing on the PC path.

## Mon Nov 16 11:40:08 PM UTC 2026
- 29-F41 CORRECTS MY OWN 29-F40, caught before it reached a summary: the PC20 tree-size advantage is DEPTH-DEPENDENT and changes sign. depth 10: S14 861,000 vs PC20 880,419 = +2.3% MORE nodes; depth 12: -19.5%; depth 14: 5,888,909 vs 5,061,004 = -14.1%. So the switches only pay from about depth 12 up; at shallow depth they cost slightly more.
- 29-N22 withdraws '19.5% fewer nodes' as a general statement (it is the d12 row). The qualitative half stands at match depths: base/S14 and PC20 are trees of different SIZE, not merely different ordering. Same error class as 29-F39 - one cell presented as a constant - caught this time BEFORE it reached a summary.
- next: continuing on the PC path.

## Mon Nov 16 11:41:29 PM UTC 2026
- 29-N24 keeps the lint lesson in the record: a checker wrong in EITHER direction is worse than none, and twice the bug was my expectation rather than the data (demanded 4 fields for C rows that carry a 5th tag; then demanded 5 when the two oldest C rows use the brief's 4-column form). A blocked-but-correct file trains people to ignore the checker, which is as bad as a checker that passes everything. It now accepts both legitimate shapes and rejects all others.
- next: continuing on the PC path with the sweep discipline applied by default.

## Mon Nov 16 11:41:43 PM UTC 2026
- 29-F42 swept F41 onto a SECOND position set and it changed again: the depth-10 sign flip is R_2911-SPECIFIC. On G, PC20 saves 15.9% at depth 10 and 12.7% at depth 12; on R_2911 it costs +2.3% at 10 and saves 19.5% at 12. So the effect depends on BOTH depth AND position set; the only stable claim is that at match depths PC20 searches a smaller tree on both sets.
- 29-N25 withdraws F41's generalisation. That is the THIRD single-cell correction of the hour (F38->F39, F40->F41, F41->F42), each caught by sweeping one more axis - which is precisely why 29-N23 makes sweeping the default rather than a response to being asked.
- next: continuing on the PC path.

## Mon Nov 16 11:42:07 PM UTC 2026
- 29-N26: FINDINGS now OPENS with the 29-F42 table (above the named rules), not a single figure. Order is: FIRST RULE (zero must be a measurement) -> THE TABLE for PC20 tree size -> the three named rules. Any PC20-vs-S14 number of mine quoted anywhere should come from that table; a single number in a row is a pointer to it, not a result.
- The table carries both position sets, the reading guide, and the one stable claim you relayed (PC20 smaller on BOTH sets at match depths: -12.7% G, -19.5% R_2911 at depth 12).
- next: continuing on the PC path.

## Mon Nov 16 11:45:42 PM UTC 2026
- 29-F43 closes the F40-F42 thread's open question: is PC20's smaller tree sound or lossy? PC r15, 40 real-game positions, depth 12, Threads 1, Hash 16: SAME bestmove 34/40 = 85.0%. Of the 6 disagreements, each move judged under the NEUTRAL S14 regime at depth 15: PC20's move scores better 4 of 6, S14's 2 of 6, no ties.
- Caveat stated in the finding: 4-of-6 cannot prove PC20 plays BETTER, but it rules out the pruning losing moves (unsound pruning would give 0 or 1 of 6). Claim is 'smaller tree, no detected loss of move quality on 40 positions'.
- next: continuing on the PC path.

## Mon Nov 16 11:49:41 PM UTC 2026
- 29-F44 SUPERSEDES 29-F43's '4 of 6': at 100 positions the comparison is a DEAD HEAT. 83 of 100 same bestmove (83.0%); of the 17 disagreements judged under the neutral S14 regime at depth 13: PC20 better 7, S14 better 7, tie 3. So the regimes are indistinguishable in move quality on this sample and my earlier 4-of-6 was small-sample noise. Stable claim stays 'no detected loss of move quality', and the 4-of-6 must NOT be quoted as PC20 choosing better moves.
- 29-N27: the bug was MINE - my first tally regex matched only cp scores and silently dropped 4 of 17 rows, all mate judgements. The rewritten tally requires every row to parse and aborts otherwise. That flipped the conclusion. Lesson: a tally whose denominator is smaller than the rows visible in the raw file is a parse bug, not a result.
- next: continuing toward the close.

## Mon Nov 16 11:50:02 PM UTC 2026
- As asked: the sentence 'when a tally's denominator is smaller than the number of rows visible in the raw file, it is a parse bug, not a result' is now in FINDINGS immediately beside the FIRST RULE, as a sub-section 'The same rule one level up (29-N27)', with my own 13-of-17 mate-row drop and the 5-7 -> 7-7-3 flip as the worked case.
- FINDINGS document order is now: FIRST RULE + the denominator corollary -> THE PC20 TABLE -> three named rules -> the rows. A reader hits the method before any result.
- next: continuing at cadence on the PC path.

## Mon Nov 16 11:53:55 PM UTC 2026
- 29-F45 answers the question F44 left open: agreement is FLAT across depth (87.5% d8, 87.5% d10, 85.0% d12, 92.5% d14; 40 positions each, Threads 1, Hash 16). No upward trend, so the ~12% disagreements are NOT shallow-horizon noise - they are genuine differences in preference.
- With F44's dead heat (7-7-3), the honest description of PC20 is: it reaches a DIFFERENT move of comparable value on about one position in eight, at every depth. Not 'same move', not 'better moves'.
- Caveat stated: 40 positions/depth is ~+-5 points per share, so the flatness is the claim, not the percentages.
- next: continuing at cadence.

## Mon Nov 16 11:54:22 PM UTC 2026
- FINAL_NOTES updated for the deadline: the sweep rule now lists FOUR worked self-corrections from one hour (scan rate F38->F39, tree size F40->F41, the flip being set-specific F41->F42, move quality 4-of-6 -> 7-7-3 F43->F44), and the headline list gains the PC20 arc as one sentence backed by F42/F44/F45, carrying the exact caveat asked for: 'the flatness is the claim, not the individual percentages' (40 positions/depth ~ +-5 points).
- Also added 29-F45 to the headline list - agreement flat across depth (87.5/87.5/85.0/92.5 % at d8/10/12/14), which is what rules out horizon noise.
- next: continuing at cadence; FINAL block at 10:18Z.

## Mon Nov 16 11:55:05 PM UTC 2026
- 29-N28 records the STATE of every find for the FINAL's required state column (checked against the other seats' FINDINGS, not assumed):
  CONFIRMED by another seat: 29-F3 (seat 19 with a least-squares intercept of 11.91 ms vs my 14 ms, AND seat 27 on the PC build under PC20) and 29-F9 (seat 19, 13,289 tracked files / 0 .nnue or .bin / 0 over 1 MB).
  WITHDRAWN OR REFUTED BY ME: 29-C2 + the ordering half of F7 (N4), F40's generalisation (N22), F41's generalisation (N25), F43's 4-of-6 (F44), and N16's mechanism (F31/N17).
  OPEN: all PC20 move-quality work (F42/F44/F45) - no second seat has checked it.
- This makes the FINAL block a fill-in job: findings already carry build + settings in each row, and state now has a source.

## Mon Nov 16 11:55:28 PM UTC 2026
- Wrote REPRODUCE_pc20_quality.md: a short, self-contained recipe for the OPEN PC20 work (F42/F44/F45) so any seat can confirm or refute it in minutes with THEIR harness and THEIR binary. It states the three claims, my exact numbers to beat, the explicit falsification condition for each, and the two traps I fell into (dropped tally rows; one cell != the finding).
- Reasoning: my strongest work currently carries the weakest label (open, unconfirmed). The best fix I can offer is making it cheap for a second seat to check, rather than asking anyone to trust my scripts. If their numbers differ materially that is MORE valuable than agreement - a set-dependence I have not found is exactly what my own sweeps kept turning up.
- Cross-linked from N28 so a reader of the state index finds it.
- next: continuing at cadence.

## Mon Nov 16 11:55:49 PM UTC 2026
- 29-N29: the FINAL instruction is now WRITTEN DOWN rather than remembered. FINAL_NOTES.md has a 'MUST APPEAR IN THE FINAL BLOCK' section with the exact wording to use if no seat picks up the PC20 work: F42/F44/F45 are open and unconfirmed by any second seat, the recipe is named, and it says explicitly that the recipe lowers the cost of checking and NOT the uncertainty. It also carries the N28 state summary so the FINAL's state column has one source.
- Reasoning: a deadline is exactly when a careful caveat gets dropped in favour of the stronger-sounding result. Writing the caveat down now, with its wording, removes that risk.
- next: continuing at cadence.

## Mon Nov 16 11:59:48 PM UTC 2026
- 29-N30 SCOPES DOWN my own 29-C6. Tried to widen C6 from its 2 boards to a proper sample (100 positions, depth 12, both regimes): S14 shows 0 truncated of 19 mate scores, PC20 0 of 20 - i.e. on this set there is NO truncation for PC20 to remove, so the mechanism does not generalise.
- 29-C6 still stands as written (on seat 05's exact two boards the difference reproduces), but it must be quoted as 'on the two boards seat 05 identified', NOT as 'PC20 fixes mate-PV truncation'. Consistent with seat 05's own S-F21/S-F23 that the effect is per-position.
- This is the first time tonight a broadening attempt made one of my confirmations WEAKER rather than stronger - recorded with the sample caveat (19-20 mate positions per regime is thin).
- next: continuing at cadence.

## Tue Nov 17 12:06:56 AM UTC 2026
- 29-F46: I took the caveat's own suggestion and built a MATE-HEAVY set (40 positions, deterministic, kept only where S14 reports a mate score at depth 12 - 148 candidates screened). Result: S14 truncates 2 of 40 = 5.0% (PVs 13/17 at mate 9, 16/19 at mate 10); PC20 truncates 0 of 40. So the S-F23 mechanism DOES generalise, and my 29-N30 scoping was right that the random set could not settle it - a mate-heavy set settles it in favour of the mechanism.
- Both runs now stand and are reconciled in the table: random games show no truncation either side (not mate-heavy); mate-heavy shows S14 5%, PC20 0%. Truncation is a property of mate-heavy positions, and PC20 removes it there.
- Caveat kept: 2 of 40 spans roughly 1.5-12%, so the RATE is imprecise; the DIRECTION is the claim.
- next: continuing at cadence.

## Tue Nov 17 12:07:16 AM UTC 2026
- Verified both requested forms are in the committed files: FINDINGS carries the interval ('2 of 40 spans roughly 1.5-12 %') and 'the DIRECTION is what this establishes'; the raw table carries the reconciliation section stating both runs stand and why neither contradicts the other.
- FINAL_NOTES updated: the C6 line now reads as 'seat 05's two boards reproduce exactly, AND on a purpose-built set of 40 mate-reporting positions S14 truncates 2 of 40 while PC20 truncates 0 of 40', with the instruction to keep the interval and treat direction (not rate) as the claim.
- next: continuing at cadence.

## Tue Nov 17 12:07:52 AM UTC 2026
- 29-F47 re-tested my own 29-F45 on the mate-heavy set (a deliberately different distribution): agreement 82.5/85.0/85.0/90.0 % at depths 8/10/12/14 - again FLAT, and close to the random-game 87.5/87.5/85.0/92.5 %. So the flatness is not an accident of one set.
- Stated honestly in the row: this STRENGTHENS F45 but does NOT confirm it (same harness, same binary, my sets). A second seat is still needed, which is why N28 keeps F42/F44/F45 OPEN and REPRODUCE_pc20_quality.md exists. It also does not touch F44, which is about the QUALITY of disagreements rather than their frequency.
- next: continuing at cadence.

## Tue Nov 17 12:08:26 AM UTC 2026
- 29-F48 THE THREE-SET PICTURE (I checked seat 07's file rather than relaying second-hand, and it is richer than reported):
    R_2911        : 87.5 / 87.5 / 85.0 / 92.5 %  (spread 7.5, FLAT) - mine, reproduced BY SEAT 07 TO THE DIGIT
    mate-heavy 40 : 82.5 / 85.0 / 85.0 / 90.0 %  (spread 7.5, FLAT) - my F47
    last 40 of G  : 55.0 / 60.0 / 77.5 / 70.0 %  (spread 22.5, +15 pt UPWARD) - seat 07's 07-C56
- So agreement is SET-DEPENDENT: on my two sets the disagreements are genuine preference differences at every depth; on late G a substantial share are shallow-horizon artefacts that dissipate with depth. My F45 is CONFIRMED ON ITS SET and its GENERALISATION IS REFUTED by the same check.
- 29-N31 state update: F45 now has a SECOND SEAT (confirmed to the digit) and is scoped; only F42 and F44 remain open. FINAL_NOTES corrected accordingly - it previously listed all three as open, which would have been out of date at the deadline.
- Seat 07's method note preserved in the finding: they ran my ORIGINAL sample before judging, so their report is 'confirmed on its set, set-dependent' rather than a bare REFUTES. A number can be right on its own sample and wrong as a generalisation - different faults, different reports.
- next: continuing at cadence.

## Tue Nov 17 12:08:45 AM UTC 2026
- Seat 07's frame is now in BOTH the FINAL notes and FINDINGS (29-N32), in their words: 'a number can be right on its own sample and wrong as a generalisation, and those are different faults needing different reports.' The FINAL section lists all five set-dependences of my hour that share that shape (F38/39, F40/41, F41/42, F43/44, F45/48) - in every one the measurement was sound on its own sample and the GENERALISATION was the fault.
- next: continuing at cadence.

## Tue Nov 17 12:09:03 AM UTC 2026
- 29-F49: tested F44 (quality dead heat) on the ONE set where agreement does not stay flat - the last 40 of G, seat 07's set - because that is where PC20's pruning would show damage if it does any. Result: agreement drops to 15/20 = 75.0% (consistent with seat 07's lower G figures and with F48's set-dependence), and of the 5 disagreements judged under the neutral S14 regime at depth 13: PC20 better 2, S14 better 2, tie 1. Dead heat again.
- So the coherent pair is: agreement FREQUENCY is set-dependent (F48), disagreement QUALITY is a dead heat on both R_2911 (7-7-3 over 17) and late G (2-2-1 over 5).
- Caveat stated because it bites: 2-2-1 over FIVE disagreements cannot ESTABLISH a dead heat - it shows no sign of PC20 being worse on the set most likely to expose it. A confident claim needs far more late-G positions than 20.
- next: continuing at cadence.

## Tue Nov 17 12:09:22 AM UTC 2026
- 29-N33 WORDING FIX on my own F49: I had written 'dead heat on both R_2911 (7-7-3) and late G (2-2-1)', which applies 'dead heat' to a FIVE-disagreement sample. Corrected to: dead heat on R_2911 (7-7-3 over 17); on late G only 'no sign of PC20 being worse' (2-2-1 over 5).
- The summary pair, in the coordinator's own honest form: FREQUENCY is set-dependent; QUALITY shows no sign of damage on either set.
- next: continuing at cadence.

## Tue Nov 17 12:09:47 AM UTC 2026
- 29-N33 named precisely in the method note and in FINAL_NOTES: THE failure mode is 'writing the caveat and then contradicting it in the same row' - the caveat makes it read as careful while the claim stays strong. Three instances tonight (F31 refuted mechanism, F44 '4 of 6', F49 'dead heat' on a five-sample), each caught only by re-reading for the WORD not the number.
- Mechanical fix carried forward: let the weak sample keep the weaker word ('no sign of X', never 'X'), and put any generalisation in its own sentence that names its scope.
- FINDINGS method order is now: FIRST RULE (zeros) + denominator corollary -> THE FAILURE MODE (caveat contradicting itself) -> THE PC20 TABLE -> three named rules -> rows.
- next: continuing at cadence.

## Tue Nov 17 12:14:02 AM UTC 2026
- 29-F50 is the first sample in my data where the quality evidence TURNS AGAINST PC20, and it weakens my own F44. At depth 14 (30 positions, R_2911, Threads 1, Hash 16): 27/30 same bestmove (90.0%); of the 3 disagreements, judged under the neutral S14 regime at depth 17, ALL 3 FAVOUR S14 - pos 4 by 33 cp, pos 9 by 109 cp, and pos 27 categorically: S14's move lets the opponent mate in 6, PC20's in 7.
- 29-N34: F44 can no longer be summarised as 'quality shows no sign of damage'. Accurate: dead heat at depths 10-12 (7-7-3, 2-2-1), but at depth 14 all 3 of 3 favour S14. n=3 is a SIGNAL not a result - but it is the axis where PC20's pruning would show, and depth 14 is where the PC actually plays.
- This is more useful to the owner than a clean bill of health. NEXT MEASUREMENT flagged: 100+ positions at depth 14 and depth 16.
- next: continuing at cadence with the wider depth-14 run.

## Tue Nov 17 12:22:47 AM UTC 2026
- 29-F51: I ran the wider depth-14 test immediately instead of leaving it as a note, and it REVERSES my own F50. 80 positions at depth 14: 67/80 same bestmove (83.8%); of the 13 disagreements PC20 better 8, S14 better 4, tie 1. So F50's 'all 3 favour S14' was SMALL-SAMPLE NOISE.
- 29-N35: withdraws F50's signal-against-PC20 and RESTORES F44's 'no sign of damage' for depths 10-12 AND 14. Across all my samples the tally has swung 7-7 (n=17), 2-2 (n=5), 0-3 (n=3) and 8-4 (n=13) - that is what noise looks like, and no sample shows PC20 systematically worse.
- FOURTH time tonight a small tally pointed the wrong way (with the 4-of-6 in F43 and the two single-cell percentages). Rule now heavily evidenced: widen the sample before reporting a sign; treat any tally under ~20 outcomes as a hint at most.
- next: continuing at cadence.

## Tue Nov 17 12:23:09 AM UTC 2026
- Installed the four-sample tally as the worked example beside the sweep rule in FINDINGS, and in FINAL_NOTES: 17 outcomes -> 7-7-3 (dead heat); 5 -> 2-2-1 (dead heat); 3 -> 0-3 AGAINST PC20 (published as F50, withdrawn 20 min later); 13 -> 8-4 mildly pro-PC20. The same configuration produced opposite signs at n=3 and n=13.
- Operational form kept verbatim: 'any tally under about twenty outcomes is a hint at most' - treat a small one-sided tally as a reason to collect more, never as a finding.
- next: continuing at cadence.

## Tue Nov 17 12:23:46 AM UTC 2026
- 29-F52: applied my own sample-size rule to MY OWN tree-size table, which was built on 25-30 positions per cell. Re-ran at 100 per cell:
    R_2911 d10: +2.3% -> +0.3%  (the 'sign flip' is now INSIDE NOISE - switches are approximately FREE at depth 10, not a clear cost)
    R_2911 d12: -19.5% -> -11.9%
    G      d12: -12.7% -> -10.7%
- Direction of every claim unchanged; three published MAGNITUDES were inflated in the same direction the flip was. Top-of-file table now shows the n=100 figures as current and keeps the old row only to show what small samples did.
- 29-N36 pattern for the FINAL: the DIRECTION of every surviving claim has been stable; the NUMBERS have all moved toward smaller effects as samples grew (fifth instance). Quote direction with confidence, magnitude only with its n.
- next: continuing at cadence.

## Tue Nov 17 12:24:14 AM UTC 2026
- 29-N36 is now a STATED FINDING in the FINAL with a five-instance table (scan rate, tree-size-vs-depth, set-specificity, move quality, tree-size magnitudes), and the headline sentence: quote the DIRECTION with confidence, a MAGNITUDE only with the n it came from.
- 29-N37 SELF-CHECK: I first wrote that table's sample sizes from memory and got TWO WRONG (said the scan-rate run was '60 -> 200' when it was 20 -> 200 plus a separate 60-position 2x2; and labelled the depth row '30 -> 30' when the widening there was an AXIS change, not an n change). Corrected by reading six raw files instead of trusting recall.
- Worth noting because N36 is a rule about quoting n - a table quoting n wrongly would discredit the very rule it evidences.
- next: continuing at cadence.

## Tue Nov 17 12:24:35 AM UTC 2026
- As asked: the misquoted-n correction now sits INSIDE the 29-N23 rule row itself, not only in the separate N37 note - 'the five-instance table written to evidence this rule first misquoted two of its own n values from memory (29-N37), corrected by reading six raw files. A rule about quoting n whose own table misquotes n is the clearest possible argument for the rule.'
- next: continuing at cadence on the PC path.

## Tue Nov 17 12:25:06 AM UTC 2026
- 29-F53: closed the LAST TWO un-verified cells, so the whole tree-size table is now n >= 60 everywhere.
    R_2911 depth 14: n 20 -> 60, -14.1% -> -11.0%
    G      depth 10: n 25 -> 100, -15.9% -> -15.3% (essentially unchanged - this cell always held)
- Final verified picture: match depths PC20 searches 10.7-11.9% FEWER nodes on both sets; at depth 10 it is SET-DEPENDENT (R_2911 approx neutral +0.3%, G clearly better -15.3%); NOTHING supports PC20 being slower anywhere.
- Three of five magnitudes had been inflated by small samples, every one in the direction of a stronger story (R d12 by 7.6 points, d14 by 3.1, G d12 by 2.0), and the one cell that looked like a COST (+2.3%) was a wash (+0.3%).
- next: continuing at cadence.
