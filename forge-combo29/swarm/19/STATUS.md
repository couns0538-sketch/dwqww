# swarm 19 — status

seat 19
area 9 (SPEED)
branch for-fable-and-opus/swarm-19
seed 1901

## 2026-11-16T21:10:00Z (written at start, times below come from stamps.txt)

Started. Repository check ok (origin ends couns0538-sketch/dwqww). Seat 19 claimed.
Area = ((19-1) mod 10)+1 = 9 = SPEED. SEED = 19*100+1 = 1901.

Next: STEP 2 — build 6b98f217 in ../base and run the honesty check
(bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609).

## 2026-11-16T21:13:02Z

job 1 (profile bench 13) DONE.
perf: 17K samples task-clock, bench 13 x40 (all 40 nodes 862329).
top: evaluate_position 16.51 %, Worker::search 11.97 %, nnue::apply_and_evaluate 11.84 %,
MovePicker::next 6.69 %, pick_best 6.35 %, see_ge 5.56 %. All evaluation 38.24 %.

files: REPORT_job1.md, FINDINGS.md (19-F1..F5), job1/ (profile.sh, profile_cg.sh, summarize.py, summary.txt, prediction.txt, stamps.txt).

next command: `bash ~/build_rel/forge` nothing — literally:
  cd /agent/repos/dwqww && S=$(cat ~/swarm_seat.txt) && python3 forge-combo29/swarm/$S/job1/summarize.py forge-combo29/swarm/$S/job1/profile > forge-combo29/swarm/$S/job1/summary.txt
then: job 2 written to job2/prediction.txt and committed ALONE before the first speed measurement.

## 2026-11-16T21:25:28Z

job 2 DONE (negative result, stated as such).
patch job2/optimize_material_key.patch.txt: material key cached in Board.
node counts identical (bench 11/13/16 + perft 5 on the patched build). cache proven correct on 4,736 positions.
speed: ratio 1.0059, 95% CI [0.9680, 1.0454] -> NOT shown faster; control pair of two identical builds gave [-5.12%, +5.43%], so this machine cannot resolve <5%.

next command: bash ~/build_rel/forge is NOT next; next is job 3 (the next hot spot), starting with the prediction:
  cd /agent/repos/dwqww && S=$(cat ~/swarm_seat.txt) && printf "%s\n" "job 3 prediction" > forge-combo29/swarm/$S/job3/prediction.txt && git add forge-combo29/swarm/$S/job3/prediction.txt && git commit -m "swarm $S job3: prediction alone" && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-$S

## 2026-11-16T21:30:37Z

read FABLE_TO_swarm_2.md and _3.md. Rule 2 changes my job: the owner's PC loads its own king-bucket net, so
`evaluate_position` never runs there. 19-F1/F10/F11 are therefore NOT PC candidates. I say so in the finding lines.
Also: 19-F7's CAUSE is refuted (by 28, confirmed by me in check28C2): two clean rebuilds are byte-identical
  (sha256 e06310ec...), and my 4.2 % was sequential-block drift — baseA's last four runs are 424/426/424/426.
  Only its advice survives and it is too weak: ONE bench run moves 8-17 %, so bench needs alternating repetition.

done: job1, job2, job3, check21F1 (CONFIRMS 21-F1), check28C2 (CONFIRMS 28's refutation of 19-F7's cause).
next command: job 1 again with seed 1911 and a new R set (SEED+10), restricted to PC-relevant families per Rule 2:
  python3 forge-combo29/swarm/19/job1b/make_R.py 1911 forge-combo29/swarm/19/job1b/R_1911.fens && bash forge-combo29/swarm/19/job1b/profile2.sh

## 2026-11-16T21:34:48Z — CHECKPOINT (owner asked for a push every 30 min)

done so far:
  job 1  profile of bench 13 — done, REPORT_job1.md
  job 2  material-key cache patch — done, node counts identical, NOT measurably faster (CI spans 1.0), REPORT_job2.md
  job 3  NNUE column prefetch — done, 8.10 % SLOWER, rejected, REPORT_job3.md
  job 1b seed 1911 + PC-relevant profile — done, REPORT_job1b.md
  check21F1 CONFIRMS 21-F1 ; check28C2 CONFIRMS 28's refutation of my own 19-F7 cause ;
  check29F3 CONFIRMS 29-F3 (11.91 ms fixed cost inside the bench timer)

running right now: check08F9_multi.py — 08-F9 across 100 positions x 4 clock settings (backgrounded);
  first single-position version gave 52.3 / 50.6 / 85.9 / 169.8 % of the computed soft limit, i.e. two cases
  OUTSIDE their 55-79 %% band, but one position is not like-for-like against their 200, hence the multi run.
  My own first attempt at this check was VACUOUS (searched for a clock_plan line the engine never prints, so
  the NaN comparison passed) — recorded in check08F9/raw_v1_vacuous/ and fixed by computing the plan from source.

next command:
  python3 forge-combo29/swarm/19/check08F9/check_08F9_multi.py ~/build_rel/forge forge-combo29/swarm/19/job1b/R_1911.fens forge-combo29/swarm/19/check08F9/raw3

## 2026-11-16T21:36:13Z — FULL PUSH (owner deadline 22:30Z)

Everything below is on GitHub as of this block: FINDINGS.md (13 F lines, 4 C lines),
REPORT_job1/2/3/1b.md, both patch files, every raw job file under job1/ job2/ job3/ job1b/, and the
three check folders (check21F1, check28C2, check29F3, check08F9).

state: jobs 1, 2, 3, 1b complete. checks: 21-F1 CONFIRMS, 28's S-C2 CONFIRMS (against my own 19-F7),
29-F3 CONFIRMS, 08-F9 CONFIRMS.

continuing with: verification of 19-F12's impact on other seats' harnesses, then one more PC-relevant
speed job. next command:
  for s in $(git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed "s#.*swarm-##"); do ...; done

## 2026-11-16T21:38:49Z

vacuity audit DONE: 33 parsed numbers, every source line found, 0 wrong values.
  (3 first-run flags were bugs in the audit script, not in any report — one of them a regex that could not
   match the CORRECT empty answer, which is the vacuity trap in mirror image.) REPORT_vacuity_audit.md

pick_best attribution DONE (text only, no patch): REPORT_pick_best.md
  the cost is neither the partial loop, nor the scoring (which is NOT in pick_best: 2.0-2.2 QuietScorer
  calls per pick_best means scoring happens in next/push_scored), nor the root (0.26-0.36 %% of calls).
  5 %% of calls take std::sort and that branch holds ~23 %% of pick_best's local samples.
  seed path used only 20.9-21.8 %% of calls. Counters agree across bench 13 and R_1911 x200.

next command:
  cd forge-combo29/swarm/19/pickbest && python3 summarize_pickbest.py

## 2026-11-16T21:49:11Z — 22:05 CHECKPOINT, complete deliverable set

seat 19 / area 9 (SPEED) / seed 1901 / branch for-fable-and-opus/swarm-19
tip at this block: b6f156a7d

HONESTY: all four numbers reproduced on base and on both patched builds — 312866 / 862329 / 3024920 / 4865609.

REPORTS (9):
  REPORT_job1.md            profile of bench 13 — evaluation 38.24 %, move ordering 17.34 %
  REPORT_job2.md            material-key cache patch: nodes identical, NOT shown faster (CI 0.9680-1.0454)
  REPORT_job3.md            NNUE column prefetch: 8.10 % SLOWER, rejected (CI 0.8841-0.9552)
  REPORT_job1b.md           PC-relevant profile, seed 1911: move ordering 18.37 %, pick_best 7.93 %
  REPORT_job4.md            my prediction that the TT miss path was redundant — it was already implemented
  REPORT_job4_tt.md         bench 13 reaches the TT replacement scan on 0.006 % of probes, R_1911 on 54.7 %
  REPORT_pick_best.md       where pick_best's cost goes: the 5 % sort branch, not the loop, the scoring or the root
  REPORT_pickbest_tie.md    stable_sort moves 3 of 4 pins — tie order is load-bearing
  REPORT_toolchain_pins.md  g++ 11/12/13 give identical pins — 19-F16 risk theoretical (clang UNVERIFIED)
  REPORT_vacuity_audit.md   33 parsed numbers, every source line found, 0 wrong values

DELIVERABLE PAGES:
  RECIPE_tt_validation.md   how to measure a TT patch where the table actually fills (counters + ranges)
  METHOD_timing_tt.md       how to TIME a TT patch; measured noise floor +/-2.29 % at 10 rounds
  PIN_SENSITIVITY.md        which of the four pins can detect an ordering change (19-F20)

CHECKS: 21-F1 CONFIRMS; 28's S-C2 CONFIRMS against my own 19-F7; 29-F3 CONFIRMS (11.91 ms bench overhead);
        08-F9 CONFIRMS (medians 62-69 % of soft limit); 29-F9 CONFIRMS (no net file in the repo).

VIOLATION.md: 5.8 MB of build artifacts remain in history at 03d92c4c1; force-push forbidden, owner informed.

next command (nothing new started):
  cd /agent/repos/dwqww && S=$(cat ~/swarm_seat.txt) && cat forge-combo29/swarm/$S/FINDINGS.md

## 2026-11-16T21:53:38Z — FINAL PUSH before the 22:30 deadline

seat 19 / area 9 (SPEED) / seed 1901 / branch for-fable-and-opus/swarm-19
tip: 4ef878a81

READ FIRST — RETRACTION: 19-F18 and 19-F19 were measured WARM (one process, no ucinewgame). Cold, the
same 200 positions give 142 full-table replacement scans in 13,888,165 probes = 0.001 %, against bench 13's
0.006 % — the same order, so the 54.7 % gap I claimed DOES NOT EXIST and 'bench cannot measure the TT' is
false. ucinewgame-per-position and fresh-process-per-position agree to the last digit. See CORRECTION_19F18.md
and 19-R1. The recipe now carries a retraction banner.

ALSO RETRACTED: the probe_body 2.09 % -> 5.77 % self-share comparison (the R_1911 profile was warm too).

SURVIVES (all measured with fresh processes): 19-F15/F16/F17 tie order and toolchain pins; 19-F20 which
pins see an ordering change; 19-F21 +/-2.29 % noise floor at 10 rounds (both sides warm identically, node
total 286,628 identical in all 20 runs, so the ratio stands); 19-F22 state-discipline measurement;
19-F23 bench is self-clearing so five bench lines in one process still give 862,329 five times;
the four honesty numbers; and all five checks (21-F1, 28-C2, 29-F3, 08-F9, 29-F9 — all CONFIRM).

DELIVERABLES: RECIPE_tt_validation.md (retracted premise, harness code still useful),
METHOD_timing_tt.md (rounds-vs-effect table, node-total guard, state discipline in 1b),
PIN_SENSITIVITY.md, CORRECTION_19F18.md, REPORT_*.md x10, FINDINGS.md (25 F + 6 C + 2 R lines).

VIOLATION.md: 5.8 MB of build artifacts at 03d92c4c1 remain in history; force-push forbidden; owner informed.

next command (stopping as instructed):  none — the deliverable set is complete.

## 2026-11-16T21:53:55Z — FINAL STATUS, end of the owner's window

seat 19 / area 9 (SPEED) / seed 1901 / branch for-fable-and-opus/swarm-19
tip: 20f191be9

=== READ FIRST: RETRACTION ===
19-F18 and 19-F19 (and the 2.09 %->5.77 % probe_body comparison) are RETRACTED: measured WARM, one
process, no ucinewgame. Cold, the same 200 positions give 142 full-table replacement scans in 13,888,165
probes = 0.001 %, against bench 13's 0.006 % — same order, so the 54.7 % gap does not exist and 'bench
cannot measure the TT' is false. ucinewgame-per-position and fresh-process-per-position agree exactly.
RECIPE_tt_validation.md now says in its first line: this recipe HAS NO VALIDATED USE LEFT, do not reuse;
take 19-F23 instead. See CORRECTION_19F18.md and 19-R1.

=== NEW, and the reusable fact from that thread ===
19-F23: bench is immune to this trap. src/uci.cpp:611 builds its own Searcher(16) and src/uci.cpp:617
calls bench_searcher.clear() before EVERY one of its eight positions (Searcher::clear -> shared_.tt.clear()),
so five bench 13 lines in one process give 862,329 five times. My bench-based numbers were never affected.
19-F22: warm vs cold, measured — node count 15,238,023 vs 13,925,108 (+9.4 %), replacement scans 8,310,172
vs 142. Any harness publishing node counts must state which discipline it used.

=== SURVIVES (all fresh-process measurements) ===
19-F15/F16/F17 tie order is load-bearing; pins are gcc-stable 11/12/13 and UNVERIFIED on clang+ThinLTO.
19-F20 which pins detect an ordering change (all three bench depths yes, perft 5 no).
19-F21 timing noise floor +/-2.29 % at 10 rounds (both sides warm identically; node total identical).
Four honesty numbers; five checks, all CONFIRM: 21-F1, 28-C2 (against my own 19-F7), 29-F3, 08-F9, 29-F9.

=== DELIVERABLES ===
CORRECTION_19F18.md, METHOD_timing_tt.md (rounds-vs-effect table, node-total guard, state discipline 1b),
PIN_SENSITIVITY.md, RECIPE_tt_validation.md (no validated use), REPORT_*.md x10, FINDINGS.md.

VIOLATION.md: 5.8 MB of build artifacts at 03d92c4c1 remain in history; force-push forbidden; owner informed.

next command: none — deliverable set complete, stopping as instructed.

## 2026-11-16T22:18Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18Z

seat 19 confirmed from ~/swarm_seat.txt; branch for-fable-and-opus/swarm-19; tip before this block: d1df7bb7a

plan, in the order the owner gave it:
  1. fetch handoff/fable-opus-combo29-all-20261114, read every FABLE_TO_swarm_N.md not yet read, lowest N first
     (read so far: 1, 2, 3 — file 5 holds the PC engine source as a patch against 6b98f217)
  2. build the PC build per file 5 in a SEPARATE copy with -DFORGE_MATE_ALPHA_GUARD=1; check its known bench numbers
  3. re-run my own finds on the PC build under settings PC20, each finding line naming build + settings
  4. cycle: STATUS every 25 min max, checks with own harness, zeros need a planted case
  5. at 10:18Z on 2026-11-17: FINAL block listing every find with state, build and settings

carried forward from before the window: 19-F18/F19 RETRACTED (warm-state artifact); 19-F23 bench is
self-clearing (src/uci.cpp:617 bench_searcher.clear() before every position); 19-F15/F16/F17, 19-F20,
19-F21, 19-F22 and the four honesty numbers survive; VIOLATION.md stands (5.8 MB at 03d92c4c1, history only).

next command: git fetch --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git ls-tree -r --name-only FETCH_HEAD -- forge-combo29/soak_all/ | grep FABLE_TO_swarm

## 2026-11-16T22:19:47Z

read FABLE_TO_swarm_4.md and _5.md (files 1-3 read before the window).
PC BUILD r15 BUILT AND VERIFIED: patch sha256 d6bd72c531f785f4... matches the stated prefix; applied clean
  in a separate copy ~/pcbuild with patch -p1 (11 files, no fuzz); built with -DFORGE_MATE_ALPHA_GUARD=1.
ALL EIGHT known answers reproduce EXACTLY:
  none: 312866 / 862329 / 3024920 / perft5 4865609 ; S14: 242796 / 656517 ; PC20: 278024 / 587276
  zero unknown-option / invalid-value / ERROR lines -> MateAlphaGuard and all six PC20 options exist.
File 4 note: my honesty checks always used NO setoption (correct regime for pins); job1b/R1911 used S14
  (correct regime for node sums). No regime relabelling needed in my earlier work.

next command: re-run my finds on the PC build under PC20, starting with 19-F12 (the quit-abort bestmove)
  and 19-F15 (stable_sort pin drift), each line naming build + settings.

## 2026-11-16T22:23:42Z

PC20 RE-RUN COMPLETE. Build PC r15, Threads 1 everywhere.

19-F12 STILL PRESENT on PC r15 under both none and PC20 (aborted: 0 info-depth lines, bestmove a2a3/0 nodes).
19-F25 NEW: the fabrication is THE POSITION'S FIRST GENERATOR MOVE. Black-to-move P1 -> a7a6 (a2a3 illegal
  there), which is the first line of that position's own go perft 1 divide (python-chess lexicographic is
  a7a5, so engine order is what is reproduced). After a completed search returning d2d4, P1 still -> a7a6,
  so NOT stale. FORGE_FIX_ABORT_PUBLISH defaults to 0 and its own comment excludes this path.
19-F26: 19-F15/F20 hold on the PC build under PC20 — pins move -8.6 %/+5.7 %/-14.7 %, perft 5 not at all.
  Under the none regime the post-ablation counts are IDENTICAL to the base tree's (292627/939494/2925608).
19-F27: noise floor on PC r15 is +/-2.91 % at 6 rounds (node total 316,716 identical in all 12 runs).

next command: pick the next PC-relevant speed question on PC r15 under PC20, or a check of another
  seat's open finding on the PC build.

## 2026-11-16T22:32:06Z

PC20 profile + twin + emit line all done. Build PC r15, Threads 1.
19-F32 first PC r15 profile under PC20: move ordering 18.33 %% (largest PC-relevant), corrected_eval 5.75 %%
  (6th hottest, up from 2.95 %% base, signature gained SearchStack* = CorrHistV2), TT 2.68 %% cold.
  CorrHistV2 ablation: 587,276 nodes on vs 613,774 off, deterministic over 3 reps -> saves 4.3 %% of nodes.
  Time NOT claimed (ranges overlap, one rep faster with it off).
19-F30 twin 2595: reachable-only-where-correct on PC r15 (K+N vs K -> g1e2 cp 0); base tree misses
  mate-in-1 on a threefold repetition (f2f3, 0 nodes) while PC r15 finds a1a8 mate 1 at 168 nodes.
19-F31 pins are a Threads-1 AND none-regime statement, both measured.

next command: check another seat's open finding on the PC build under PC20, then next PC speed question.

## 2026-11-16T22:33:37Z

19-F33 CorrHistV2 changes 22 %% of bestmoves (200 of G, depth 12) and its node saving falls to -1.46 %%;
  mean score delta +0.4 cp but spread -358..+435 -> owner needs games, not a node count.
19-F34 corrected_eval is FLAT with depth: 5.75 %% (d13) vs 5.77 %% (d16).
19-F35 the TT IS the depth cost: probe_body not-in-top-10 at d13 -> 8.47 %% and 4th hottest at d16,
  on the same cold positions, both at their pins. Caveat: Hash 16 (bench's), may differ at the owner's size.

next command: TT counter run at depth 16 cold to split probe frequency from miss cost
  (job4/instrument_tt.py at depth 16), which decides whether 8.47 %% is capacity or call rate.

## 2026-11-16T22:34:39Z

19-F36 TT cost is CALL RATE not capacity: probes/node = 1.0000 at depths 11/13/16, full-table scans
  0.000/0.006/0.204 %% of probes. A larger hash cannot fix the 8.47 %%.
19-F38 proof: 16x hash (16->256 MB) on a real cold depth-14 search removes ALL replacement scans (97->0)
  and moves nodes by 2 in 1,645,108. Capacity is relievable and worth ~nothing here.
19-F37 bench HARDCODES 16 MB (uci.cpp:773 Searcher bench_searcher(16)); Hash option hits the UCI searcher
  only (line 777). Hash 16/64/256/1024 gave byte-identical bench counters - second reason bench cannot test TT.
CorrHistV2 measurement STOPPED as instructed (games question).

next command: continue PC-relevant family profiling at depth 16 on PC r15 under PC20 (move ordering 17.12 %%,
  see_ge 4.88 %%), looking for the next attackable PC-relevant cost.

## 2026-11-16T22:38:29Z

19-F39 probe_body split: index 32.7 %% / SCAN 39.4 %% / after 27.9 %% at depth 16 (stable at d13).
19-F40 vector-compare patch: ALL SEVEN PINS HOLD; ratio 0.9865 CI [0.9626,1.0104] and 20 interleaved
  runs 1.0001 -> no win. Disassembly: GCC scalarised my _mm_cmpeq_epi32 back into the same four
  scalar compares (patched binary has 0 pcmpeqd, 0 pmovmskb), so the test compared scalar-vs-scalar.
  Corrected my report: this does NOT show the scan is load-bound. NOT recommending this patch.
19-F41 valgrind/callgrind CANNOT run this engine (SIGILL on AVX-512 at static init); any totals it
  prints are preamble. Likely affects seat 29's 29-F5 callgrind numbers - flagged to the coordinator.

next command: continue PC-relevant families — move ordering 17-18 %% is the largest remaining,
  and 19-F26 showed its tie order moves the owner's own pins, so any change there needs care.
