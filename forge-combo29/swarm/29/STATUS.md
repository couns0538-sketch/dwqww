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
