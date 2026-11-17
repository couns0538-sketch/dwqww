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

## 2026-11-16T22:44:47Z

file 6 read. Two verdicts change one priority. My findings unaffected (all Threads 1, node-count based).
19-F43: applied file 6's inequality to my own 19-F30 case -> base tree's missed mate IS a defect
  (counter 8, counter-0 control gives mate 1, so 2N-1=1 <= 92), PC r15 repaired.

NEW AREA (file 6 suggestion) + the match path:
19-F44 softnodes: deterministic 24/24, always finished-depth, overshoots median +27 %% max +106 %%.
19-F45 bestmove identical across N 2000..250000 on 6 positions (not generalised).
19-F46 go nodes UNDERSHOOTS median -32 %% while softnodes overshoots +22 %% - opposite sides of N;
  softnodes reaches exactly one ply deeper in ALL 18 cells. Match path spends ~half to two-thirds of N.
19-F47 the boundary is a ONE-NODE cliff: 31779 -> depth 12 (+0.00 %%), 31778 -> depth 11 (-37.59 %%).
  Same deterministically. One mechanism explains both findings.

next command: the 6s+0.06 clock (last item on the owner's real path), Threads 1, PC20, cold.

## 2026-11-16T22:59:42Z

19-F48/F49 modes diverge on ambiguous positions: unbiased rate = 30.0 %% of random G positions are ambiguous
  (top-two within 15 cp at depth 12), 10.0 %% of those diverge. My 'hostile' filter inflated the DIVERGENCE
  rate (18.4 -> 10.0 %% ), not the ambiguity rate (31.7 vs 30.0 %%). Owner act-on: ~3 %% of positions.
19-F50 clock rho = 0.999 over 42 positions -> wall time IS the last iteration's cost (3rd confirmation).
19-F51 class ordering does NOT reproduce (1.4x span vs 3.6x within-class spread; worst board is MID).
  full_few holds only 2 of set G's 353 positions -> likely root cause of the 08-vs-02 disagreement.
19-F52 one board shows wall 2.1x its last iteration (1585.8 vs 749 ms) = an iteration paid for and
  discarded. Best lead, NOT traced - handed over.

next command: check another seat's open finding on the PC build (area-10 style), then continue.

## 2026-11-16T23:00:29Z FINAL

seat 19 / area 9 (SPEED) / seed 1901 / branch for-fable-and-opus/swarm-19 / tip 582c3f535
62 finding lines (F/C/R), 28 reports. All measurements Threads 1 unless a line says otherwise.

=== ON THE OWNER'S REAL PATH (file 6's priority: PC build r15, PC20, Threads 1, Hash 16) ===

19-F44 softnodes: DETERMINISTIC 24/24 cells (3-4 runs each), ALWAYS stops at a finished depth,
  overshoots N by median +27 %% (max +106 %%). 'softnodes 2000' really spends 2,060-3,312 nodes.
  state: OPEN (unconfirmed by another seat). build PC r15 / PC20 / Threads 1 / Hash 16 / cold.
19-F45 bestmove identical across N 2k..250k on 6 positions. state: OPEN, explicitly not generalised.
19-F46 go nodes UNDERSHOOTS median -32 %% (range -51.9..-0.8) while softnodes overshoots +22 %%:
  opposite sides of N; softnodes reached exactly ONE PLY DEEPER in all 18 cells. 18/18 deterministic.
  => his match path spends half to two-thirds of the requested N. state: OPEN.
19-F47 the budget boundary is a ONE-NODE CLIFF: go nodes 31779 -> depth 12 (+0.00 %%), 31778 -> depth 11
  (-37.59 %%), both deterministic. Same mechanism as F44/F46. state: OPEN.
19-F48 nodes vs softnodes diverge on 7 of 38 cells (18.4 %%) on a HOSTILE ambiguous sample. state: OPEN.
19-F49 the POPULATION rate: 30.0 %% of 100 RANDOM G positions are ambiguous (top-two <=15 cp at depth 12),
  and 10.0 %% of those diverge = ~3 %% of positions overall. My hostile filter inflated the DIVERGENCE rate,
  not the ambiguity rate (31.7 vs 30.0 %%). state: OPEN.
19-F50 clock: wall time IS the last iteration's cost, Spearman rho = 0.999 over 42 positions.
  state: CONFIRMED IN SPIRIT by seat 02's S-F13 (their rho 0.998, different boards).
19-F51 the sparse-vs-full class ORDERING does NOT reproduce (1.4x span vs 3.6x within-class spread; the
  worst board is MID). 'full_few' holds only 2 of set G's 353 positions -> likely cause of the 08-vs-02
  disagreement. state: OPEN (offers a resolution to two other seats).
19-F52/19-F53 the 2.1x anomaly TRACED: HARD-LIMIT abort, 1585.8 ms vs planned hard 1585 ms, NO re-search
  (no depth twice), 849.7 ms of work discarded. go depth 21 alone costs 1551 ms, more than the whole hard
  limit, so it can never complete on this clock. The clock has TWO REGIMES: iteration-boundary normally,
  hard-limit when one iteration is unaffordable. state: OPEN, mechanism fully observed.

=== TT (the build's hottest depth-scaling cost) ===
19-F35 probe_body 2.68 %% at depth 13 -> 8.47 %% (4th hottest) at depth 16, same cold positions. OPEN.
19-F36 it is probe COUNT not capacity: 1.0000 probes/node at depths 11/13/16; full-table scans 0.204 %%.
19-F37 bench HARDCODES 16 MB (uci.cpp:773) so setoption Hash never reaches it. OPEN, and it invalidates
  any bench-based hash conclusion.
19-F38 16x hash removes all replacement scans (97->0) and moves nodes by 2 in 1,645,108. OPEN.
19-F39 inside probe_body: index 32.7 %% / SCAN 39.4 %% / after 27.9 %% at depth 16. OPEN.
19-F40 vectorising the scan is a NO-OP (pins hold, ratio 1.0001) because GCC scalarises the intrinsics
  back to the same four compares. OPEN. NOT recommended as a patch.
19-F42 the scan order is already optimal: slot0 82.8 %% of hits and already first; 66.9 %% of compares are
  non-reorderable empty-slot misses; 1.331 compares/probe. THE SCAN IS FINISHED. OPEN.
19-F41 valgrind/callgrind CANNOT run this engine (SIGILL on AVX-512 at static init). OPEN.

=== OTHER FINDINGS THAT SURVIVE ===
19-F15/F16/F17 tie order in pick_best is LOAD-BEARING (stable_sort moves 3 of 4 pins); pins are gcc-stable
  across 11/12/13 and UNVERIFIED on clang+ThinLTO (19-F17b, wording constraint). state: OPEN.
19-F26 the tie-order effect holds on PC r15 under PC20 (pins move -8.6/+5.7/-14.7 %%). OPEN.
19-F20 which pins detect an ordering change: all three bench depths yes, perft 5 no. OPEN.
19-F12 the quit-abort fabricated bestmove - STILL PRESENT on PC r15 under both none and PC20. OPEN.
19-F25 it publishes the position's FIRST GENERATED move (a7a6 on a black-to-move board), not stale,
  not literal. 19-F28 traced the emit line to src/search.cpp:3017 and CAUSALLY PROVED it (front->last
  changes a7a6 to g8h6). FORGE_FIX_ABORT_PUBLISH defaults to 0 and does not cover it. OPEN.
19-F30/F43 the base tree MISSES a mate-in-1 on a repetition board; file 6's inequality checked:
  mate 1 at counter 0, 1 <= 100-8 = 92 TRUE, so it is a REAL defect (not a claimable draw). PC r15 repaired.

=== RETRACTED, kept in the record ===
19-F18/F19 (TT workload claim) RETRACTED by 19-R1: measured WARM; cold gives 142/13.9M = 0.001 %%, the same
  order as bench's 0.006 %%%, so the 54.7 %% gap does not exist.
19-F7's CAUSE refuted by seat 28, confirmed by my own 19-C2: two rebuilds are byte-identical and my
  4.2 %% was sequential-block drift. The advice (repeat, do not block) survives and is now 19-F21/F27.

=== CHECKS OF OTHER SEATS (all CONFIRM) ===
19-C1 21-F1 | 19-C2 28's S-C2 (against my own 19-F7) | 19-C3 29-F3 | 19-C4 08-F9 | 19-C6 29-F9 | 19-C7 seat 04's Threads finding (with a Threads-4 positive control)

=== HONESTY ===
All four pins reproduced on base, on both patched builds, and on PC r15 in all three regimes (19-F43 table).
VIOLATION.md stands: 5.8 MB of build artifacts at 03d92c4c1 remain in branch HISTORY; force-push forbidden.

next command: none — the record is complete.

## 2026-11-16T23:26:07Z — window continues

19-F54 lone-king results: 0 of 40 positions worse-than-alternative at BOTH go depth 16 and go nodes 20000.
  Sample 40 from 103,150 candidates (legal play from set G + R_1911, seed 19101).
  CONTROL: exactly 1 of 40 had an immediate mate and the engine played it (b6b8 mate 1) at both budgets,
  so the zero is a measurement, not a vacuous pass.
  SCOPE: no tablebases (none here; lichess mirror 403/SSL-fail) -> only terminal results adjudicable, so
  this tests missed immediate mates, NOT 'loses N plies sooner'.
19-C8 my own ordering bug: first runs said 2 of 40; both were CORRECT queen promotions that I flagged
  because I ranked UNKNOWN below DRAW. Fixed; out/ and out2/ kept beside out3/.

next command: continue in-area work — the king-only-side-to-move sample (the mirror of this one) is the
  obvious untested case, or another open finding's check.

## 2026-11-16T23:49:58Z

19-F55 DTM oracle: validated on KQvK (19 plies = theory) and found 1 of 8 covered positions with a worse
  DTM — 8/8/4k3/6q1/8/8/8/1K6 b mates in 7 plies at depth 16 (g5d2) but 11 at go nodes 20000 (g5c5).
19-F56 TRACED to the iteration: nodes 20000 stops after depth 7 (7,994 nodes) because depth 8 alone
  costs 27,825; the mate needs depth 12 (133,042 nodes). The budget ends SIX PLIES before the mate exists.
  => F46/F47's truncation produces F55's worse DTM, and the 3.5x cost jump between adjacent depths
     is why the one-node cliff is structural.
19-C10/19-F57 seat 21's halfmove-window trap APPLIED to my unclamped solver; audited all 8 covered
  positions: all three mates fit their windows (7/95, 23/77, 15/75), so 19-F55 is unchanged. Clamp
  implemented as windowed_verdict() for future use. NO mirror rate published for this reason.
19-C9 two failed solvers + the ply-convention trap, labelled and kept.

next command: run the mirror test through the clamped verdict, or another open finding's check.

## 2026-11-16T23:54:55Z

19-F58 mirror (bare king to move), all through windowed_verdict(): 1 of 8 covered positions.
  6k1/8/5K2/8/6r1/8/8/8 w plays f6e7 (mated in 17) where f6f5 survives 29 plies.
  THE CLAMP WAS LIVE: pos 31 counter 87 / window 13 / no forced mate -> draw; engine found it.
  Unclamped, that would have been scored as a defender failure. Seat 21's trap nearly hit my pipeline.
19-F59 the defect is a DEPTH LIMIT, tested: depth16/20 -> f6e7 (cp -490), depth24 -> f6f5 (mate -15).
  Not a preference for losing quickly. Position 11 is a calibration case, not a bug. Report rewritten.
19-C10/19-F57 halfmove-window audit: 19-F55 unaffected (all mates fit windows 7/95, 23/77, 15/75).
  Clamp implemented as windowed_verdict() in dtm_bfs.py.
19-C9 two failed solvers + ply-convention trap, labelled and kept. NOTE_three_traps.md has the pattern.

next command: continue at cadence - check an open finding of another seat, or extend the oracle to a
  2-piece signature if a cheaper enumeration can be found.

## 2026-11-17T00:05:58Z

19-C11 F59 disagreement with seat 27: raw output sent (exe sha256 + every line). My FEN is ... w - - 12 182
  vs their ... w - - 0 1. Rerunning BOTH on my binary: counter 12 -> mate -15, counter 0 -> mate -16,
  same move f6f5, and depths 16/20 IDENTICAL across counters. So counters explain ONE PLY, not the gap.
  No PC20 variation reproduces their f6e5 / cp -509 / 1,915,526. Most likely different binaries;
  sha256sum of both exes settles it in one command.
  BOTH agree on the structure (d24 -> f6f5, d16/20 -> not f6f5), so the calibration-case conclusion stands.
  19-F58 AMENDED: the defect is 'not the longest defence until deep enough', move name is build-specific.

next command: continue at cadence; the sha256 comparison is the one thing that would close 19-C11.

## 2026-11-17T00:06:39Z

19-C12 RESOLVED: seat 27's f6e5 is a 19-F12 ARTIFACT. Their committed stdin ends at 'go depth 24'
  with NO quit; run byte-for-byte it gives 'bestmove f6e5' and ZERO info depth lines. f6e5 is the
  first line of that position's go perft 1 divide (19-F25). So d16/d20/d24 f6e5 is ONE fabricated move,
  not three searches; the quoted nodes/nps cannot come from that file.
  Also impossible by arithmetic: KRvK max mate distance is 31 plies; their mate -25 needs 49.
  Mine: mate -15 = 29 plies = my oracle's exact DTM, inside the bound, 25-ply PV (short by 4).
  Counters explain exactly one ply: their FEN -> mate -16, mine -> mate -15, same move.
  19-F58/F59 stand unchanged.

next command: continue at cadence; 19-F12 has now caught two seats, so a broad sweep of other seats'
  committed inputs for 'missing quit' would be the highest-value check left.

## 2026-11-17T00:10:49Z

19-C13 SWEEP of all 49 seat branches: 251 committed UCI input files send quit/EOF behind their last go.
  By seat: 20 -> 222, 27 -> 25, 19 (mine, discarded history) -> 3, 17 -> 1.
  ** Seat 20's job3: 60 of 60 committed *.out.txt have ZERO info depth lines ** - every bestmove there is
  19-F12's fabricated first-generated-move, so no score/depth/node count in that job came from a search.
  NOT claiming its conclusions are wrong (area-10 terminal cases can coincide with the expected answer;
  I did not read them). Ask: re-run with a driver that reads to bestmove.
  go perft is UNAFFECTED - verified synchronous (go perft 5 + quit still prints nodes 4865609).

19-C12 seat 27's f6e5 = 19-F12 artifact (its committed stdin ends at go depth 24, no quit ->
  bestmove f6e5 with zero info lines; f6e5 is that position's first perft-1 divide move).
  mate -25 impossible: KRvK max is 31 plies. Mine mate -15 = 29 = oracle exact; 25-ply PV, short by 4.

next command: continue at cadence; report the sweep result to seat 20 via the coordinator and keep
  checking open findings on my own thread.

## 2026-11-17T00:19:51Z

19-C16 RETRACTED my per-search sweep counts. The detector splits blocks on bestmove alone, so on files
  with interleaved readyok (most of them) a block spans several rounds. PROOF: seat 24's pc_inf16.raw
  -> my detector 134 good/16 aborted, but its OWN summary says rounds 150, zero 0, and the file has
  exactly 150 bestmoves. Theirs is right, mine is wrong. My book-move hypothesis was also wrong (0
  'info string' lines in that file). Counts (728/620/255...) are retracted as numbers.

=== outcomes of the sweep thread that DO stand (verified by reading files, not by the broken counter):
19-C13 seat 20 job3: 60 of 60 outputs with zero info lines - genuine, owner has a guard in 15 harnesses.
19-C15 seats 10 and 07 both found the defect independently and handled it correctly (10 wrote a
  trap-aware helper + E1.py study; 07's INVALID_HARNESS.txt marks its output 'NOT a result').
19-C12 seat 27's f6e5 = 19-F12 artifact; mate -25 impossible for KRvK (max 31 plies).

next command: continue at cadence on my own thread; the sweep line is closed.

## 2026-11-17T00:20:17Z

19-C17 oracle scope closed: 2-piece DTM signatures need ~30.5M placements vs ~500K for 1 piece, and a
  1-piece solve already takes ~100 s in Python -> out of reach. 19-F55/F58 remain 8-of-40 tests; the 24
  positions with 2+ pieces stay unadjudicated, stated as a limit. Next step if wanted: 8-fold symmetry
  + colour swap, THEN C.

NOTE_three_traps.md now has trap 4: splitting output on bestmove alone cannot work when readyok is
  interleaved - any per-search audit needs the COMMAND stream, not just output.
NOTE_two_mechanisms_before_measurement.md records both directions: the book-move story (wrong, tested,
  fixed) and the depth-limit story (right, but only because I tested before publishing).
Four method notes now share one root: a number or story that FITS is not evidence; a check that could
  have failed is.

next command: continue at cadence on my own thread (area 9).
