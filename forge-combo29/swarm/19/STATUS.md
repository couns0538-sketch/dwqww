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

## 2026-11-17T00:20:46Z

METHOD_INDEX.md written: one page for the four method notes + their shared root, with a
  survived-vs-retracted cross-reference so a reader can tell which numbers to trust.
19-C18: seat 05's S-F64 board is a 4-piece signature (bare king vs king + 4 pawns) -> OUTSIDE the
  oracle, so I could not verify its mate -7 claim and say so instead of a partial check.
Oracle thread closed: covers KQvK/KRvK/KPvK; found 19-F55 and 19-F58; cannot reach 2+ pieces;
  not expanding without symmetry reduction + C.

next command: continue at cadence on area 9 (speed) - the picker/TT lines are exhausted, so the
  remaining PC-relevant lever is quiescence bookkeeping or move generation.

## 2026-11-17T00:21:44Z

19-C19 CONFIRMS seat 29's 29-F4 exactly: refresh_king_lines runs 804,371 times per bench 13 with
  779,027 (96.8 %%) from has_legal_move - seat 29's own integers, digit for digit.
  NEW: bench 16 = 2,826,465/2,731,439 (96.6 %%), bench 13 PC20 = 547,691/532,093 (97.2 %%).
  So the redundancy is marginally WORSE under the owner's settings, and the ratio is unchanged across
  depths = a per-node constant (contrast: the TT grows with depth, 19-F35).
  Could NOT re-check its 0.056 %% instruction figure (valgrind cannot run this build, 19-F41) - only
  the call counts it rests on, and I say so.

next command: continue at cadence; area 9's remaining levers are all measured and the picker/TT/king-lines
  lines are closed. Next is another seat's open finding where my counters or oracle add something.

## 2026-11-17T00:23:05Z

HARNESS_TRAPS.md: one list of all seven harness defects from this run, each with what it looks like,
  the tell, the test and the fix (terminator-fabricates-move, select-on-buffered-pipe, warm state,
  malformed setoption, bench's hardcoded 16MB, play-out-as-solver, oracle-missing-halfmove-window).
  Linked from METHOD_INDEX.md as the companion. Two of the seven were caught only by another seat.
19-C20: audited 08-N2 across seats - 17 and 10 exposed (select+readline), 01 and 28 safe (select+os.read);
  latent not exercised (10's timeout is 1800 s); my own drivers have the opposite gap (no timeout at all).

next command: continue at cadence.

## 2026-11-17T00:24:37Z

19-C21 CORRECTION to my select audit: both files VERIFIED at branch tips (seat 17 tip bb0b312ce
  has unbounded_check.py with select+readline at 68/71 and 88/91; seat 10 tip 68f6f81a0 has
  forge_io.py at 37/39) - no path mix-up. Seat 17's empty 'git ls-files' is ALSO right: ls-files
  lists the working tree index, not another branch -> trap 8: use git ls-tree on the ref.
  My 'EXPOSED' was too strong (trap 9): a file containing a bug is not a harness that has one -
  seat 17 reports its CURRENT harnesses use a reader thread + queue + deadline. Corrected entry:
  'one committed file contains the pattern; currency not verified'.
  HARNESS_TRAPS.md now has nine traps; scoreline updated: TWO of nine were caught only by another
  seat's push-back.

next command: continue at cadence.

## 2026-11-17T00:36:22Z

19-C22/19-C23 counter effect: 19-C11's 'one ply' scoped to the 0-vs-12 pair I compared.
  INDEPENDENTLY CONFIRMED seat 25 at depth 24: counter 0 -> mate -16 at 7,608,471 nodes;
  counter 1 -> mate -16 at 15,702,225 nodes = 2.06x, same score. Node counts are NOT a proxy
  for search equality when the counter differs.
  NEW QUALIFIER: at depth 20 counters 0/1/12/50 ALL give cp -490 at exactly 232,803 nodes -
  identical - and only 99 differs (cp 0 at 100 nodes). So the counter is INERT at shallow depth
  and only bites once the fifty-move horizon gate is reachable. A shallow sweep would have
  concluded the opposite of seat 25.
HARNESS_TRAPS.md is now TEN traps; scoreline: three of ten caught only by another seat.

next command: continue at cadence.

## 2026-11-17T00:36:49Z

19-C24: seat 05's S-F66 boards (both KRvK) give oracle best DTM **27 plies for BOTH**, so
  'mate +20' (39 plies) EXCEEDS KRvK's theoretical max of 31 = IMPOSSIBLE outright, and
  'mate +16' (31) claims 4 plies more than the 27 available. Stronger than a PV-length failure:
  the SCORE cannot be right on that material, not just the line.
  Could not reproduce its engine runs - both a truncated search and a bad driver produce this,
  and I attribute neither.

trap 10 now carries 'the counter is inert until the search can reach the horizon' as the
  reconciling sentence; HARNESS_TRAPS.md is ten traps, three caught only by another seat.

next command: continue at cadence.

## 2026-11-17T00:45:19Z

19-R2 RETRACTION: my DTM oracle is WRONG for black-as-strong. Brute force gives mate in 5 plies for
  8/8/4k3/6q1/8/8/8/1K6 b; my table said 9. So 19-F55, 19-F58 and 19-C24 are WITHDRAWN - and 19-C24
  was BACKWARDS (the engine's mate +5 was closer to truth than my instrument).
  Lesson at the top of the retraction: 'A single brute-force spot check on one position would have
  caught it, and I had a brute force written all along.' Validating a MAXIMUM does not validate a table.
  All three oracle-based reports now carry a WITHDRAWN banner so no reader hits a retracted distance unmarked.
  Still standing: 19-F56's depth trace, 19-F59's depth-24 engine observation, and everything not
  oracle-based (19-F44-F53 softnodes/nodes/clock, 19-F15/F20/F26 tie order, 19-C19 king lines,
  19-C13/C15 sweeps, the eleven-trap list).
  Not repairing the solver tonight: a repaired one needs per-position brute-force validation first.

next command: continue at cadence on non-oracle work.

## 2026-11-17T00:45:47Z

19-C25 CONFIRMS seat 21's 21-F12 exactly: FEN 6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60,
  go searchmoves e1e8 depth 4 -> PC r15: 8 nodes / mate 1 / e1e8 ; base: 0 nodes / cp 0.
  Beyond it: the BASE build emits 4 info lines at depths 1-4 with pv EMPTY and nodes 0 - it
  announces depth progress while searching nothing, so the right harness check is 'nodes>0 and
  PV non-empty', not 'an info line appeared'.

state of my thread: oracle WORK closed and retracted (19-R2, trap 11, three reports bannered).
  Since then: exact-integer confirmations of other seats (19-C19 king lines, 19-C25 searchmoves)
  and harness audits (19-C20 select trap, traps 1-11). That mix is deliberate - counters and
  reproductions, not derived tables.

next command: continue at cadence with counter-based confirmations of other seats' open findings.

## 2026-11-17T00:46:16Z

trap 1b added (sibling of trap 1): info lines that EXIST but describe nothing - base tree emits 4 depth
  lines with nodes 0 and EMPTY pv on the drawn-root path. Closing check of the list: a search happened
  only if nodes > 0 AND the PV is non-empty; neither an info line nor a bestmove is sufficient.
  HARNESS_TRAPS.md = twelve traps, four caught only by another seat.

19-C26 replicated seat 24's 24-F31: base tree, S14, Threads 1, Hash 16, OwnBook false, depth 12,
  first 40 of G, two fresh processes each -> 40 of 40 identical in move AND node count. Supports my
  own 19-F24 (Threads-1 regime) from the other direction.

confirmed-for-others tally, all exact integers: 19-C19 king-lines 804,371/779,027 ; 19-C25 searchmoves
  8 vs 0 nodes ; 19-C26 40/40 ; 19-C23 counter 2x nodes 7,608,471 vs 15,702,225.

next command: continue at cadence with counter/reproduction confirmations only.

## 2026-11-17T00:46:34Z

19-C27 reproduced seat 05's S-F58 digit for digit: go nodes 50000 -> mate +11, 44,749 nodes, 18-of-21 PV,
  depth 11 (SHORT 3); go nodes 250000 -> mate +7, 138,869 nodes, 13/13, depth 14; go depth 20 -> mate +7.
  This independently confirms the refutation of S-F57's '0 truncated at 50,000 nodes' - at a budget the
  owner's matches actually use.

confirmed-for-others tally (all exact integers): 19-C19 king-lines 804,371/779,027 ; 19-C23 counter 2x
  nodes ; 19-C25 searchmoves 8 vs 0 ; 19-C26 Threads-1 40/40 ; 19-C27 S-F58 five-for-five.
HARNESS_TRAPS.md = twelve traps; the closing check is nodes>0 AND non-empty PV.

next command: continue at cadence with counter/reproduction confirmations.

## 2026-11-17T00:46:45Z

TALLY_confirmations.md written: five exact-integer confirmations (19-C19 29-F4 king lines, 19-C23 counter
  2x nodes, 19-C25 21-F12 searchmoves, 19-C26 24-F31 Threads-1 40/40, 19-C27 05's S-F58 five figures).
  None depends on a derived table - deliberate, after my oracle retraction (19-R2).
19-C26 restated as the strongest reproducibility result of the night: it supports my own 19-F24 (Threads-1)
  from the OTHER direction - two seats, two harnesses, same conclusion, so 'assumed' became 'verified'.

next command: continue at cadence, adding to the tally with counter/reproduction work only.

## 2026-11-17T00:47:36Z

19-C28: 08-F31's '0 of 60' full-material zero has NO plant through its own harness (Rule 1 gap).
  Its evidence report and volatility_rate.py contain 0 hits for plant/control/fake/Rule 1. Seat 08 DOES
  own two good controls (/bin/cat fake engine, both non-zero exit) but they cover DIFFERENT scripts -
  so a coverage gap in a disciplined seat, not carelessness, and the zero is not thereby wrong.
  Why it matters: this harness's failure mode (missing the deep mate) produces exactly 0 of 60, so a
  plant is what separates 'no defect' from 'cannot see the defect'. And it is the claim 08 foregrounds
  as 'the actable result' while declining to quantify the sparse rate - zeros feel solid and get less
  scrutiny.

next command: continue at cadence.

## 2026-11-17T00:48:12Z

19-C29 PLANTED MY OWN ZERO. After using Rule 1 on seat 08, I found 19-F54's '0 of 40' had no plant either -
  its one mate board exercised only the 'no defect' path because the engine played the mate.
  Built the plant on 6K1/8/1r4k1/8/8/2p5/8/8 b (18 legal, exactly 1 mates): the SAME code returns
  False for the mating move and TRUE for a legal non-mating move (g6h6). The harness CAN see a defect,
  so the zero survives - but only because I checked.
HARNESS_TRAPS.md closing sentence (Rule 1 in one line): 'a planted case is the only thing that
  distinguishes I looked and found none from I could not have found one.'
  Twelve traps; traps 11 and 12 each carry their own failure as the specimen.

next command: continue at cadence.

## 2026-11-17T00:48:39Z

19-C30 POSITIVE CONTROL for my own 40/40 zero: same harness, 12 set-G positions, two runs each -
  Threads 1: 0 of 12 differed ; Threads 4: 12 of 12 differed. So the comparator CAN see a difference and
  19-C26 is a measurement, not a blind comparison. It also confirms the swarm's Threads rule from the
  other side (above Threads 1 every position differs).
  Three of my zeros are now planted: 19-F54 (mate vs non-mate), 19-C26 (Threads 1 vs 4), 19-C13 (read files).

next command: continue at cadence.

## 2026-11-17T00:49:21Z

19-C31 self-audit of my 15 zero/null findings found 19-F9's null had only a NOISE-FLOOR control, no
  positive control. Built one: go depth 16, Threads 1 median 154 ms vs Threads 4 median 117 ms =
  ratio 0.765 (23.5 %% faster, DETECTED). So F9's null means 'below resolution', not 'method blind'.
  First attempt failed informatively: bench 13 at Threads 1 vs 4 gave 0.988 because bench builds its
  own Searcher(16) so Threads never reaches it (19-F37) - a positive control must use a workload the
  setting affects.
  FOUR zeros now planted, each costing an extra round: F54 (mate vs non-mate), C26 (Threads 1 vs 4),
  C13 (read the files), F9 (23.5 %% detected).

next command: continue at cadence.

## 2026-11-17T00:49:47Z

19-C32 systematic self-audit FINISHED: 58 F-findings -> 43 positive (self-evident), 15 null-shaped.
  Of the 15: 4 real absences (F54, C26, F9 - all planted; F19 withdrawn), 11 were my filter's false
  alarms (F17's stability claim carries its contrast in stable_sort; F22/F23 contrast warm vs cold).
  GENERALISABLE: soft nulls hide better than hard zeros. '0 of 40' announces itself and got Rule 1;
  'not measurably faster' reads like a finding and escaped the question entirely.
  Also kept: my first F9 control (bench at Threads 1 vs 4, 0.988) would have produced a FALSE NEGATIVE
  about my own instrument - bench builds its own Searcher(16) so Threads never reaches it (19-F37).

next command: continue at cadence.

## 2026-11-17T00:50:03Z

trap 12 now LEADS with 'the nulls that hide best are the ones phrased as conclusions', with the
  58-findings / 15 null-shaped / 4 real / 11 false-alarms classification behind it, and the hard-zero
  case (seat 08's unplanted 0-of-60) following as the weaker instance.
HARNESS_TRAPS.md = twelve traps; traps 11 and 12 each carry their own failure as the specimen; closing
  line pairs Rule 1's purpose with the one check every harness needs (nodes>0 and non-empty PV).

next command: continue at cadence on counter/reproduction work.

## 2026-11-17T00:55:10Z

19-C33 third sweep: the nodes-0/empty-PV check is MECHANICALLY ROBUST (immune to readyok interleaving)
  but SEMANTICALLY BLIND - nodes 0 is the engine's CORRECT answer on drawn/terminal roots. Verified on
  seat 21's asan_raw_031.txt (drawn root, score cp 0 nodes 0, empty pv, real bestmove) - and 21 is the
  terminal-position seat, so its 469/6770 majority is by design. NO defect count reported.
  The distinguishing information is the POSITION, not the output.
  Three sweeps, three instructive failures, all kept: input-file (19-C13) flags suspicion only +
  committed!=used (19-C21) ; output sweeps broke on indentation then block boundaries (19-C14/C16) ;
  this one sound but blind. Sweep line CLOSED.

next command: continue at cadence on counter/reproduction work only.

## 2026-11-17T00:55:21Z

trap 13 added: a zero in an output file cannot be classified without the input (drawn root and aborted
  search are byte-identical: nodes 0 + empty PV). Tell: the sweep's LARGEST count was seat 21, the
  terminal-position seat - if the biggest cluster of 'defects' sits on the expert, you are measuring the
  expertise. Closing line: 'a sweep of outputs can tell you where to look; only a replay can tell you what
  you found.'
HARNESS_TRAPS.md = fourteen traps; the three sweep failures are recorded in sequence inside trap 13.

next command: continue at cadence on counter/reproduction work.

## 2026-11-17T01:03:21Z

19-C34 PC r15 vs base, like-for-like: WORK IS IDENTICAL (node counts equal at every position:
  723,141 / 1,119,081 / 299,476 / 196,793) but SPEED IS UNRESOLVED - 6 positions at d18 gave 1.017,
  then 5 positions x 12 alternating rounds = 60 runs each gave 1.0040 with 95%% CI [0.8517,1.1564]
  = +/-15%%. Cause: 73 ms per search is too shallow for 60 runs; my +/-2.29%% floor (19-F21) was
  measured on 8-second-per-sample sweeps (~100x more work per sample).
  Also record: my first run printed 'note the NODE counts differ' WITHOUT CHECKING - they were identical.
  Trap 11's shape again, caught only by reading the table I had just printed.

UNRESOLVED tonight (recorded as such, not dressed up): clock class ordering (19-F51), per-search sweep
  (19-C16/C33), 2-piece DTM (19-C17), mirror rate beyond 8 positions, and this speed comparison.

next command: continue at cadence.

## 2026-11-17T01:03:40Z

NOTE_floor_is_workload_property.md: a noise floor belongs to the WORKLOAD, not the machine.
  My two attempts: 10 rounds on an 8.3 s/sample sweep -> +/-2.29%% ; 60 rounds on a 73 ms/sample search
  -> +/-15.2%%. 48x more runs, 7x worse resolution, because fixed per-run costs dominate short samples.
  Correct procedure (one extra run): A-vs-A, compute the half-width, scale rounds by (current/target)^2,
  and if the count is unreasonable for that duration say 'not resolvable' instead of quoting a number.
  Generalised with trap 10 (floor depends on depth) and trap 11 (a maximum does not validate a table):
  a number measured on one thing is not evidence about another.

next command: continue at cadence.

## 2026-11-17T01:08:03Z

19-C35 BUILD-SPEED QUESTION RESOLVED (third attempt): bench 16, 10 alternating rounds, ~1.15 s/sample,
  node count identical 2,155,620 in ALL 20 runs -> mean base 1142 ms vs pc 1155 ms, ratio 1.0119,
  95%% CI [0.9997, 1.0241] = +/-1.22 %%. Resolution 12x better than the 73 ms workload at HALF the
  rounds - NOTE_floor_is_workload_property demonstrated on the experiment that produced it.
  WORDING: PC r15 is AT MOST ~1.2 %% slower, interval lower bound 0.9997 (one ten-thousandth under 1.0)
  -> 'no measurable speed advantage, ~1 %% penalty at worst', NOT 'significantly slower'.
  Good outcome for the owner: adopting PC r15 costs nothing at the search, and its value is the fixes.

next command: continue at cadence.

## 2026-11-17T01:08:32Z

19-C36 confirmed 07-F4/07-C76 AND added the fix side. Three counter-100 roots with a reset available:
  BASE 0 nodes / cp 0 on all three (reproduces C76 mechanically);
  PC r15 -> 15,981 nodes mate 6 ; 252 nodes mate 1 ; 4,899 nodes cp 0.
  So on 2 of 3 boards the base build was masking a MATE, not just a quiet score - a stronger
  statement of the fix's value than a 20-position rate. And FORGE_FIX_ROOT_DRAWN does what its name
  says, unlike FORGE_FIX_ABORT_PUBLISH (defaults 0, does not cover its own case).

next command: continue at cadence.

## 2026-11-17T01:08:49Z

19-C37 threshold found: the fifty-move root shortcut fires at EXACTLY counter 100. Mate-in-1 board:
  base gives 252 nodes / mate 1 / a1a8 at counters 0,50,98,99 - then 0 nodes / cp 0 / f2f3
  at 100,101,150,9999. PC r15 unaffected at every counter including 9999.
  The 99->100 step turns a FOUND MATE into a fabricated quiet move - the substitute move is not just
  unscored, it is wrong (f2f3 instead of a1a8).
  Three independent angles now agree: seat 07's 20-of-100 rate, my 19-C36 fix side, this threshold.

next command: continue at cadence.

## 2026-11-17T01:09:48Z

19-C38 threshold is SETTINGS-INDEPENDENT: under PC20 (all 15 options) base gives exactly the same
  numbers as default options - 252/mate 1/a1a8 at ctr 99, 0/cp 0/f2f3 at 100/101/9999. So the fault
  is in the drawn-root shortcut itself, not in any tunable - no configuration avoids it on base.
COMPLETE BOUND on the fault (three angles): below 100 cannot fire ; at 100+ always fires on base and the
  substitute move is WRONG (f2f3 where a1a8 mates) ; PC r15 never fires under either regime.

next command: continue at cadence.

## 2026-11-17T01:10:20Z

REPORT_fifty_move_bound.md consolidates the twenty-one/twenty-two thread into ONE file: the three-angle
  bound in FINAL form (below 100 cannot fire / at 100+ always fires with a wrong substitute / PC r115
  never fires under either regime), plus threshold (19-C37), settings-independence (19-C38), fix side
  (19-C36) and severity (19-C39: throws away a mate, castling rights, +369 with 0 nodes).
  Attribution in the report: fault + mechanism + rate + two self-corrections = seat 07; threshold shared
  with seat 21; my contribution = threshold precision, settings-independence, fix side, severity.

next command: continue at cadence.

## 2026-11-17T01:10:33Z

trap 14 added: identical answers from unrelated inputs mean the INPUT is wrong (my invalid-FEN severity
  run returned e2e4 from all three boards, incl. a KPvK where e2e4 is illegal).
  It GROUPS four traps under 'the engine answered a question you did not ask': no info lines / info with
  nodes 0 + empty PV / refused FEN leaving the previous board / this. One defence covers all four:
  assert the engine's move is legal in THAT row's position.
HARNESS_TRAPS.md = fourteen traps, now cohering into three families: 'no search happened' (1/1b/13/14),
  'a number that is not evidence about what you think' (10/11/12), 'auditing the wrong thing' (8/9).

next command: continue at cadence.

## 2026-11-17T01:11:00Z

19-C40 PC20 changes the SEARCH in BOTH directions: same 5 set-G positions at depth 14, S14-only vs
  S14+PC20 -> node ratios 1.1893 / 0.4979 / 0.5722 / 1.0977 / 1.0904. One position HALVES, another
  rises 19%%. So PC20 is six different engines, not one tuned engine.
  It explains (a) why bench's seven PC20 aggregates cannot be read as 'same search cheaper' - on a
  given position it can be 2x cheaper - and (b) my own 19-F32/F33 puzzle: CorrHistV2 gave only a 4.3%%
  bench node change but changed 22%% of bestmoves, because bench's 8 positions average the reshaping away.
  Guidance: compare S14 vs PC20 PER POSITION and report the spread; an aggregate can be ~0 while
  individual positions differ 2x. (Trap 10's shape: the setting changes the question.)

next command: continue at cadence.

## 2026-11-17T01:12:20Z

19-C41 attributed the PC20 per-position swings: one option at a time, depth 14, 4 set-G positions:
  CuckooRep 1.296/0.854/1.050/0.860 ; HistRework 1.631/0.724/0.975/0.721 ;
  TtPruneV2 0.760/0.501/1.200/1.151 ; CorrHistV2 1.449/0.568/1.009/0.756 ;
  ** MateAlphaGuard 1.000/1.000/1.000/1.000 - EXACTLY unchanged on every position **.
  So: (a) MateAlphaGuard does not touch the search tree, so no PC20 node effect can be attributed
      to it; (b) the swings come from TtPruneV2 (0.50-1.20) and HistRework (0.72-1.63) - each can
      halve or +60%% a given position. Guide: compare S14 vs PC20 PER POSITION, report the spread.

next command: continue at cadence.

## 2026-11-17T01:12:43Z

19-C42 MECHANISM for MateAlphaGuard's exact 1.000: read from source - declared false at
  search.cpp:183, referenced at ONLY two places (2134, 2159), each a futility-pruning guard
  '(!tune::MateAlphaGuard || !is_mate_score(alpha))'. So it only fires when alpha is a MATE
  score; otherwise NO different code executes. Not 'below resolution' - an UNEXECUTED BRANCH.
  Burden on any contrary claim: exhibit a node where alpha is mate-valued.
THIRD time tonight reading source turned a zero into a mechanism (19-F37 hardcoded bench table,
  19-F23 self-clearing bench, this). A uniform result is a reason to read the code, not to sample more.

next command: continue at cadence.

## 2026-11-17T01:12:58Z

trap 15 added: a uniform result is a reason to read the code, not to run a bigger sample.
  Three of my own instances: MateAlphaGuard exactly 1.000 (unexecuted branch - only fires when alpha
  is a mate score), bench's Hash never applying (hardcoded Searcher(16)), bench self-clearing
  (five lines all 862,329). Sharpest form: an unexecuted branch and a sub-resolution effect look
  IDENTICAL in data and are OPPOSITE in meaning.
HARNESS_TRAPS.md = fifteen traps in FIVE families (A no-search four disguises / B number not evidence /
  C auditing wrong thing / D harness mechanics / E the code says why). Family E is the one I would
  put first on a rewrite - its instances are all cases where more data would have made it worse.

next command: continue at cadence.

## 2026-11-17T01:13:17Z

19-C43 contrast: CuckooRep/TtPruneV2/CorrHistV2/HistRework are UNCONDITIONAL boolean gates so they fire on
  ordinary positions (ratios 0.50-1.63); only MateAlphaGuard requires alpha to be a mate score, hence
  exactly 1.000. So the null is proved to be an unexecuted branch, not uninformative.
Family E promoted to the TOP of HARNESS_TRAPS.md with its rule and the rationale (its three instances
  are the cases where more data would have made the answer worse). Page finished at 15 traps / 5 families.

next command: continue at cadence on measurements; traps page closed.

## 2026-11-17T01:13:44Z

19-C44/C45 PC20 depth by BUDGET (6 set-G positions, summed depth):
  go nodes 20000: S14 59 vs PC20 62 = +3 ply
  go nodes 50000: S14 71 vs PC20 72 = +1
  go nodes 250000: S14 95 vs PC20 96 = +1
  go softnodes 2000 (SELF-PLAY): S14 45 vs PC20 43 = ** MINUS 2 **
  => PC20 wins at MATCH budgets and LOSES at the self-play budget. Likely mechanism: at 2000 nodes the
     per-node overhead (corrhist/cuckoo/rework) does not compound into an extra ply; at larger budgets it does.
  => No single 'PC20 better/worse' claim is meaningful without naming the budget - trap 10's shape a
     third time, on the budget axis. Found by sweeping the parameter, not by testing one value.

next command: continue at cadence.

## 2026-11-17T01:19:44Z

19-C46 located the reversal: soft-budget sweep on 6 set-G positions, summed depth:
  2000: 45 vs 43 = -2 ; 3000: 47 vs 48 = +1 ; 5000: +2 ; 8000: +5 ; 12000: +3 ; 20000: +3.
  => flips between 2000 and 3000; the self-play budget sits 1000 nodes on the wrong side.
  CULPRIT: one-at-a-time at softnodes 2000 -> CuckooRep +0, HistRework +0, **TtPruneV2 -1**, CorrHistV2 +0.
  So TtPruneV2 alone costs the ply; its pruning needs >2000 nodes to pay for itself.
  RECOMMENDATION: raising self-play from 2000 to ~3000 makes PC20's switches pay (+1 there, +5 by 8000),
  at the cost of 50%% more nodes per self-play move - a concrete trade the owner can decide on.
  CAVEAT: 6 positions, 1 run each - the TREND is the finding, not any single row.

next command: continue at cadence.

## 2026-11-17T01:26Z

19-C47 sharpened on review: the vacuous test now leads the FINDING, not just my message.
  The rule, generalised: **A zero needs a plant. A UNIFORM zero needs a better metric.**
  - plant answers "could the harness have seen one?"; it does NOT answer "could the METRIC have shown one?"
  - `0 of 8` in one arm = candidate null, plant it. `0 of 8` in EVERY arm = the metric's floor.
  - my score-vs-depth-18 test was the second kind: a 2k search legitimately disagrees with a depth-18 score,
    so no engine at any setting could have scored above zero. The engine was never under test.
  - detector is uniformity across arms - trap 15's tell applied to zeros.
  Written up as **trap 12b** in HARNESS_TRAPS.md; METHOD_INDEX companion note updated (the file has outgrown
  its "seven traps" wording, which was already stale).
  Budget sweep itself: nothing further owed - 19-C46 depth result stands, quality claim stays open.

next command: continue at cadence - pick the next area-9 job (speed), or cross-check a seat's new finding.

## 2026-11-17T01:52Z

19-C48: independent check of seat 29's 29-F55 (their file says no second seat had checked it).
  My slice: odd lines of R_2911.fens (200 positions, NOT theirs), PC r15 vs base, depth 14, Threads 1, Hash 16,
  every search guarded on nodes>0 and pvlen>0, disagreements judged under NEUTRAL S14 at depth 17.
  RESULT: agreement 169/200 = 84.5 %, 31 disagreements -> PC20 16, S14 13, tie 2. Sign test **p = 0.711**.
  Pooled with theirs (19-10-2): 35-23 over 58, p = 0.148. **Neither reaches significance.**
  => CONFIRMS "no disadvantage for PC20 at depth 14". Does NOT confirm "possibly a small advantage".
  Prediction had said 80-90 % agreement and 45-65 % for PC20 - both hit.

  Two things worth carrying:
  1. **My totals were IDENTICAL to theirs (169/200, 31) from a different position set.** Only 5 of 31
     disagreement positions coincide. Headline-matching looked like replication and was a coincidence;
     the per-position rows are what distinguish the two.
  2. **Trap 1 caught me on my first command of this job** - piped stdin, EOF mid-search, fabricated bestmove
     at 95 ms with score=None/pv=0. Knowing the trap did not prevent it; an executable guard did. Recorded in
     NOTE_trap_caught_me_first.md.

next command: continue at cadence - next cross-check or area-9 job; candidates are seats 07/21's fifty-move
lines or a fresh speed measurement on the v3 path (seat 29's file 7 work).

## 2026-11-17T02:30Z

19-C49: RECONCILIATION with seat 27. Answer in three quantities, not one (200 positions, guarded harness):
  1. S14 vs PC20 @ softnodes 2000: PC20 deeper 17 / S14 deeper 24 / equal 159 -> +9 for S14, p = 0.349. NULL.
  2. S14 vs PC20 @ softnodes 3000: +10 for S14, p = 0.392. NULL.
  3. 2000 -> 3000 WITHIN an engine: S14 +134 ply, PC20 +133 ply. REAL, LARGE, ENGINE-INDEPENDENT.
  => **the flip I attributed to PC20 was the BUDGET. 19-C46's attribution WITHDRAWN.**
     Budget is worth +0.67 ply/pos to BOTH engines at ~1.45x the nodes per move. That is the trade.

MECHANISM (new, applies to every seat using softnodes): softnodes N is NOT a budget of N.
  hard cap 4N (search.cpp:2499); soft test only after a COMPLETED iteration (search.cpp:2932).
  mean spend @2000 = 3185/3234 (59-62 % overrun); @3000 = 4711/4536; ratio 1.40-1.48 not 1.5.
  **46.5-47.0 % of positions return the IDENTICAL search at both budgets** - the 2000-vs-3000 question is
  ill-posed on half the sample. 1/200 degenerate (4N cap, no completed iteration, unsearched bestmove).

SEAT 27'S CONTROL POINT APPLIED: same-move restriction does NOT collapse the budget effect - it absorbs 84 % of
  it (+112 of +134). It DOES dissolve the engine comparison (+5 of +9). Right instrument, other conclusion.

STILL DISAGREE: seat 27 67.9 % PC20-favoured (127/187) vs my 41.5 % (17/41); z = 3.18 -> genuinely different
  populations, not just sample size. A +0.063-ply mean is inside the sub-one-ply band needing the restriction.

SELF-CORRECTION: my first degenerate-position demo was a SHELL artefact (printf dropped the FEN -> malformed
  position -> nodes 0). The 0 was mine, not the engine's. Recorded in the report.

next command: continue at cadence - carry 19-C49's softnodes granularity to the seats using softnodes, and
re-examine which of my remaining PC20 claims used softnodes rather than `go nodes`.

## 2026-11-17T01:58Z

19-C51 (seat 01's catch): 19-C49 cited seat 29's `R_2911.fens`, which is NOT on my branch - not reproducible
  from my branch as written. FIXED: committed `checks/softgran/positions_used_200.fens` (exact 200) and re-ran
  from my branch alone - every number reproduced exactly. Seat 01's independent 44.0 % [37.3, 50.9] agrees.
  THREE position sets now give the identical-search fraction: 46.5/47.0 (mine), 44.0 (seat 01), 44.5/44.7
  (seat 27's 600, measured by me from its JSON).

19-C50 - THE NON-OVERLAP WITH SEAT 27 IS SETTLED, and I concede the direction:
  Ran MY harness on SEAT 27's own 600 positions (same build sha256 068f0927):
    identical d_depth 600/600 = 100.0 %; identical S14 cell 600/600; identical PC20 cell 600/600;
    both tallies all +38 / same-move -11, to the ply.
  => NO harness difference, NO build difference. Its first hypothesis (set property) was right.
  MY SLICE: 43.5 % rook-or-more material imbalance vs its 22.0 % (z = 5.91); mean pieces 20.63 vs 23.86.
    I took odd lines of a 400-FEN file and never checked that half was representative. It is not.
  BUT composition is NOT the mechanism: reweighting its strata (quiet 63.6 %, sharp 52.4 %) into my 43.5 %
    gives 58.7 %, not my 41.4 %. Its effect SURVIVES reweighting.
  THE ACTUAL CAUSE: my same-move decided cells n = 29; EXACT POWER to detect p = 0.615 is 0.15.
  WITHDRAWN: my z = 3.18 "genuinely different populations" - it set THEIR same-move rate against MY
    UNRESTRICTED rate; like-for-like z = 1.94.
  THREE ARITHMETIC CORRECTIONS for seat 27: (1) my 12/29 CI is [0.255,0.593], not [0.278,0.566] - so
    "CIs do not overlap" fails (overlap 0.072); (2) its 2000 CI [0.586,0.767] is inconsistent with 67/109
    ([0.521,0.701]); midpoint 0.676 matches 67/99, so denominator and interval came from different counts
    (its 3000 CI is correct); (3) +38 vs -11 are DIFFERENT SUBSETS (all-600 vs same-move-406), not before/
    after mate exclusion - same-move minus mate is also +38, which is why it went unnoticed.

next command: run the proposed discriminator - my quiet (|material|<=4) subset against their quiet stratum
63.6 % - which is a 20-minute job and the only thing that could still separate composition from noise.

## 2026-11-17T02:08Z

19-C52: THE QUIET-SUBSET RUN IS DONE AND IT DOES NOT DISCRIMINATE - my own proposal was underpowered.
  MINE     all   29 decided -> 12 = 41.4 % [0.255, 0.593]
  MINE     quiet 14 decided ->  7 = 50.0 % [0.268, 0.732]   <-- exact 50 %, maximally uninformative
  SEAT 27  all  109 decided -> 67 = 61.5 %
  SEAT 27  quiet 88 decided -> 56 = 63.6 % [0.532, 0.729]
  My quiet CI [0.268, 0.732] CONTAINS BOTH 41.4 % and 63.6 %.
  EXACT POWER at n=14: 0.033 (for 41.4 %) and 0.069 (for 63.6 %). The separator I called decisive had a
  3-7 % chance of answering its own question.
  To separate those two at 80 % power needs ~48 decided QUIET cells => ~600-700 quiet positions, i.e. what
  seat 27 already has. No further run on 200 positions can close it.

  THE TELL I MISSED: 103 same-move quiet cells but only 14 decided - an 86 % tie rate. When ties dominate,
  the effective n is the DECIDED count, not the row count. I quoted the row count as the sample size.
  Balance was the wrong lever; the DEPTH-BOUNDARY rate is what sets the decided count.

  THREAD CLOSED: no harness difference (600/600), my slice unrepresentative (43.5 % vs 22.0 %, z=5.91), my
  41.4 % on 29 decided cells at 0.15 power. Seat 27's 63.6 % on 88 decided cells is the only figure with the
  power to support a direction. Conceded, and this run adds nothing either way - I will not dress 7/14.

next command: continue at cadence - back to area 9's own job list; the PC20 quality question needs no more
work from me (it needs 600+ quiet positions, which seat 27 has), so next is a speed measurement that does not
depend on it.

## 2026-11-17T02:34Z

Trap 16 + `NOTE_power_before_decisive.md` recorded per the close of the quality thread (power rule + tie-rate
  tell: count DECIDED cells not rows; 103 cells but 14 decided).

19-C53 - SPEED: the 12 % node saving is only ~2.8 % of wall time.
  depth 12, Threads 1, Hash 16, ABBA, 119/120 positions:
    nodes 0.9090 (12.39 % fewer) ; engine time ratio 0.9728 [0.9014, 1.0497] ; external wall 1.0070.
  DIRECT per-node at fixed `go nodes 50000`, n=180:
    nodes 6,721,052 vs 6,591,407 (0.9807 budget-matched) ; ms/1M nodes 51.66 vs 55.24
    **RATIO 1.0693, per-position 1.0773 CI [1.0670, 1.0876]**
  RECONCILIATION EXACT: 0.9090 x 1.0693 = 0.9720 predicted vs 0.9728 observed.

  **QUALIFIES MY OWN 19-C35.** It reported per-node 1.0119 [0.9997,1.0241] from `bench 16` - that interval does
  NOT overlap 1.0773 [1.0670,1.0876]. `bench` is not a representative workload for per-node cost. 19-C35 was
  correct for bench and I published it as a general claim. Corrected form: ~7 % per-node penalty on real
  positions, ~1.2 % on bench.

  POWER FIRST: 29-F56's n=40 implies sd(ln)=0.401 -> 12 % needs n=87, so its null was uninformative - and it was
  RIGHT that no 12 % effect exists. My own prediction (0.88-0.93) was WRONG.
  Fixed-overhead hypothesis tested and REFUTED: per-node ratio RISES with budget (1.038@2k -> 1.083@100k).

  FOR THE OWNER: at matched NODES PC20 spends ~7 % more TIME for the same node count - an equal-node
  S14-vs-PC20 match is not an equal-time match. That is the number to weigh against its 8k-20k depth edge.

next command: continue at cadence - check whether 19-C35's bench-vs-real divergence generalises to the other
  per-node claims in my record, and report the corrected figure to whoever used 19-C35.

---

# FINAL CORRECTION — SPEED, PER-NODE AND BENCH (2026-11-17T03:05Z)

## RULE FIRST, because everything below depends on it
> **Use `bench` for pins, determinism, ablation DIRECTION, structural counters, and the pooled node effect of one
> isolated toggle. Never use `bench` for per-node cost or for the aggregate PC20 set. Always report the
> per-position spread — a pooled ratio can hide a coin flip.**

Why, measured: the PC20 node effect is **bench 11 +14.5 %, bench 13 −10.6 %, bench 16 +8.7 %, real positions
−9.1 %**. **The sign flips across benches**; only bench 13 agrees with real search, and only in direction.

## 1. The cleanest per-node figure — no modelling assumption
Pairs where the two engines' node counts agree **within 2 %** (n = 16), so the time ratio *is* the per-node ratio:

| | per-node ratio (PC20/S14) |
|---|---|
| **node-matched pairs, n=16** | **median 1.074**, IQR 0.076 |
| time ratio, same pairs | 1.073 — identical, as it must be |

**PC20 costs ~7 % more per node.** This cell needs no inference and is the one to trust.

## 2. The full distribution (n = 180, fixed `go nodes 50000`)
| | min | Q1 | **median** | Q3 | max |
|---|---|---|---|---|---|
| **per-node ratio** | 0.751 | **1.044** | **1.071** | **1.110** | 1.837 |
| node ratio, same pairs | 0.336 | 0.809 | 0.997 | 1.208 | 2.731 |

- per-node **IQR 0.065**, sd 0.090, **90.0 % (162/180) above 1.0**, single peak at 1.05–1.10
- pooled 1.0643 / mean 1.077 / geometric 1.074 / **median 1.071** — all within 1.3 %
- **removing the top 5 % of pairs by node ratio moves pooled 1.0643 → 1.0665** (the tail contributes nothing)
- **correlation(node ratio, per-node ratio) r = 0.044** — independent quantities
- **the bimodality is in the NODE ratio, not the per-node ratio.** Do not merge them.

| claim | value | where |
|---|---|---|
| **19-C35 (SUPERSEDED)** | per-node **1.0119** [0.9997, 1.0241] → "at most ~1.2 % slower" | `bench 16` only |
| **19-C53/C54 (CURRENT)** | per-node **median 1.071** [IQR 1.044–1.110] | real positions, n=180 |

**Both figures stay in the record: 1.2 % on bench, 7 % on real positions.** Bench understates ~6×.

## 3. The bench node-sign flip (19-C55)
| bench | S14 | PC20 | ratio |
|---|---|---|---|
| 11 | 242,796 | 278,024 | **1.145** (MORE) |
| 13 | 656,517 | 587,276 | **0.894** (FEWER) |
| 16 | 2,155,620 | 2,343,893 | **1.087** (MORE) |

Deterministic (identical across 3 reps); S14 values match the brief's S14 sums exactly. **Qualifies 19-F34**
("flat per-node tax, 5.75 % bench 13 / 5.77 % bench 16"): equal shares across two benches with **opposite-sign**
node effects is not evidence of a flat real-position tax.

## 4. Audit of every bench-based node claim — `checks/realnode/AUDIT_bench_claims.md`
**Mine:** 19-C35 **SUPERSEDED**; 19-F32 **SURVIVES as magnitude** (bench 4.3 % → real **5.2 %**, n=120) but
**QUALIFIED as meaning** — see the coin-flip note below; 19-F34 **QUALIFIED**; **19-C58 confirms 19-F10's prefetch
penalty is GENERAL (9.80 % on real positions, n=130)**; 19-F33, 19-C40, 19-F42, 19-C19, 19-F26, 19-C3,
19-F16/F17 **SURVIVE**.

### The 54.2 % coin flip — a property of the SWITCH, not of the measurement
`CorrHistV2` saves **5.2 % of nodes pooled** but uses fewer on only **54.2 % of positions** (65 of 120), with an
interquartile range of 0.767–1.180 — **28 times the effect size**. **This is not a measurement artefact and more
data will not remove it: it is what the switch does.** The switch saves nodes *on average across a game* and is a
coin flip *on any given position*. **So "saves 5 % of nodes" is true of a session and unusable for predicting any
single move's cost.** Anyone budgeting nodes per position should not apply this figure per position.
**Others:** 29-F42/F53 **SURVIVE and are corroborated** (real positions: 10.7–11.9 % vs my 12.4 %); 29-F59
**SURVIVES**; 29-F56 **QUALIFIED** (right conclusion, underpowered n=40); 29-F58 is a **bench-13 profile** and must
be quoted as such; seat 27's 600-cell series **SURVIVES** (I reproduced 600/600); 07's IIR `searchmoves` pin
**SURVIVES**. **Open action: 29's `_mm_prefetch` 9.43 % bench-13 wall-time result needs a real-position re-check
before anyone reads it as a general speed claim.**

**Note on my own rule — it took three revisions, and each was forced by a measurement:**
1. "never use bench for magnitude" — **too broad**: 19-C56 shows a bench magnitude transferring (4.3 % → 5.2 %).
2. "bench understates per-node cost" — **wrong as a generalisation**: I assumed the bias had a direction, and
   19-C58 refuted it (**prefetch: bench 9.43 %, real 9.80 % — bench was accurate**).
3. **Current: bench's bias is PATCH-SPECIFIC, not directional.** Bench may understate (19-C35: 1.2 % vs 7 %),
   overstate, or match (19-C58). **There is no safe blanket rule — measure on real positions once if the number
   matters.** Bench stays valid for pins, determinism, ablation direction and structural counters, which do not
   depend on the position distribution.

### Small samples in this harness overstate effects — the observed rate
Three instances in this seat, all caught before publication:
| instance | small-n result | truth | factor |
|---|---|---|---|
| 19-C56 smoke | 21.5 %, n=6 | 5.2 %, n=120 | **4.1×** |
| 19-C58 smoke | 13.19 %, n=6 | 9.80 %, n=130 | 1.35× |
| 19-C52 subset | 7/14 = 50 % | — | power 0.03–0.07 |
**The honest statement is that both smoke overstatements ran the same direction (up), at 1.35× and 4.1× — but
that is TWO observations, not a rate, and a "factor of four" would itself be a small-sample claim.** What can be
said without overreaching: **6-position smoke tests in this harness erred upward twice out of two, once by 4×,
and both were caught only because the full run was already queued. Treat any n<10 speed number as a hypothesis,
never a result.**

## THE REASON SUMMARIES FAIL (read this before the two rules below)
> **The claim most likely to violate a rule is the summary of the rule, because summaries are where hedges get
> dropped.**
>
> **A summary is a compression, and compression removes exactly the qualifiers that made the claim true.**

**This happened five times in this record, and the sharpest form is not about hedging:**

> **A rule that sorts claims into categories is itself an unclassified claim until someone applies it.**
>
> **So: when you write a rule that sorts claims into categories, immediately sort the sentence you just wrote with
> it.**

**The compression framing explains why summaries lose qualifiers. This second form explains why the RULES
themselves are unreliable on arrival** — a classification rule has to be run before it means anything, including on
its own statement. In this record the reordering rule and the ambiguity rule **each caught the other's summary
inside one section**, and the CI-first rule then reclassified **five rows** in the table that stated it.

**Concretely, the five:** the owner one-liner (led with the fragile saving); the wall-time row labelled COIN FLIP
(no established effect — UNRESOLVED); CorrHistV2's row called a real pooled effect (CI includes 1.0); the
"opposite worlds" claim (52.9 % is not the opposite of 50.6 %, it is a third case); and three C60 rows labelled by
share instead of by interval.

**Read any rule below — including this one — as unclassified until it has been applied to its own sentence.**

## PREREQUISITE (read this first): a 50 % sign-share is ambiguous, and that is why the sign-share needs a prior question
> **A 50 % sign-share cannot distinguish "a real effect that is per-position random" from "no effect, and this is
> the noise floor."**
>
> **The prerequisite separates them. The sign-share alone cannot.** No amount of extra sampling resolves it either,
> because both cases produce the same number.

**This ambiguity, not the fixed-budget example, is the primary argument for the ordered pair.** Whenever a share
comes out near 50 %, you do not know which of the two you are looking at, and the two demand opposite advice:
one says *"the effect is real but unusable per position"*, the other says *"there is nothing here at all."*

**The worked example that produces the ambiguity, caught inside this very table (19-C54).** I had listed as an
efficiency claim: *"PC20 fewer nodes at a fixed 50k node budget — 1.9 % fewer, 50.6 % sign-share."*
**That cannot be an efficiency claim. At a fixed node budget both engines stop in the same place by construction**,
so any residual node difference is the **stopping rule's granularity**, not a saving. **The 50.6 % was a correct
measurement of an effect that does not exist.**

**Concretely, which numbers are which — and my first attempt at this sentence got it wrong:**

| share | pooled figure | what it is |
|---|---|---|
| **50.6 %** | −1.9 %, no CI (fixed budget) | **NO EFFECT** — by construction; the stopping rule's granularity |
| **52.9 %** | −2.7 %, **CI [0.9014, 1.0497] includes 1.0** | **NOT ESTABLISHED** — cannot be called real *or* null at n=119 |
| **60.5 %** | −12.4 %, a large pooled effect | **REAL but session-level** — a big mean that only ~60 % of positions share |

**I originally wrote that 50.6 % and 52.9 % "come from opposite worlds". That was wrong**: 19-C53's wall-time CI
includes 1.0, so 52.9 % is a third case, not yet resolved either way. **The genuine contrast is 50.6 % (no effect)
against 60.5 % (a real effect that is per-position weak)** — and those two shares are closer together (10 points)
than either is to 90 %. **This is exactly why the share alone cannot classify a claim.**

**So the two rules form an ordered pair:**
1. **Can the comparison vary?** (fixed budgets, pinned node counts, identical searches → it cannot, and no share is
   meaningful. A near-50 % share here means "nothing to measure", not "random effect".)
2. **If it can vary, report the sign-share beside the pooled figure** — and if it is near 50 %, say which of the two
   readings you believe and on what evidence.

## REQUIREMENT (after the prerequisite): a sign-share beside every pooled effect
**Rule: a pooled effect size says nothing about the fraction of cases sharing its sign. Report both, or state that
a sign-share is unavailable and why.**

| claim | pooled figure | **sign-share (cases agreeing)** | class |
|---|---|---|---|
| **19-C54** PC20 per-node cost | **+7.1 %** (median 1.071) | **90.0 %** (162/180 dearer) | **PER-POSITION, a tax** |
| **19-C58** prefetch slowdown | **+9.80 %** | **93.1 %** (121/130 slower) | **PER-POSITION, a tax** |
| **19-C53** PC20 fewer nodes at depth 12 | **−12.4 %** | **60.5 %** (72/119) | **SESSION-LEVEL** — weak lean |
| **19-C53** PC20 faster in wall time | **−2.7 %** (0.9728), CI **[0.9014, 1.0497] includes 1.0** | **52.9 %** (63/119) | **UNRESOLVED** — no established effect either way |
| **19-F32/C56** CorrHistV2 saves nodes | **−5.2 %**, bootstrap 95 % CI **[0.8887, 1.0108] includes 1.0** | **54.2 %** (65/120) | **UNRESOLVED** — *correction: 19-C56 called this a real pooled effect; at n=120 its CI includes 1.0, so it is not established* |
| **19-C60** TtPruneV2 | −4.7 %, CI **[0.8814, 1.0307] includes 1.0** | 60.8 % (73/120) | **UNRESOLVED** |
| **19-C60** CuckooRep | −0.9 %, CI **[0.9376, 1.0487] includes 1.0** | 52.5 % (63/120) | **UNRESOLVED** |
| **19-C60** HistRework | +3.1 %, CI **[0.9567, 1.1106] includes 1.0** | 46.7 % (56/120) | **UNRESOLVED** |
| **19-C35** bench per-node | +1.2 % | *not computable* | see caption |
| **19-C55** bench node sign flip | +14.5 / −10.6 / +8.7 % | *not computable* | see caption |
| **19-C44/45** PC20 +3 ply at 20k | +3 ply | *not computable from 6 positions* | **session-level** |
| **19-C19 / 19-F42** counters | counts, not effects | n/a | the requirement does not apply |

**Caption — the "not computable" rows are structural, not missing values.** They are not gaps to be filled in:
**19-C35 measured whole-bench runs and therefore never had a per-position distribution to report at all.** That is
**a reason to distrust the figure, not a shortcoming of the table** — a per-node cost claim that cannot produce a
sign-share was never a per-position measurement. Likewise 19-C55's three bench numbers are **deterministic pins**,
single values with no distribution, and 19-C44/45 ran on six positions. **An effect claim that cannot produce a
sign-share should say so, and the absence is evidence about the claim.**

**CLASSIFY IN THIS ORDER — the share cannot do it alone:**
1. **Does the pooled 95 % CI exclude 1.0?** If **no** → **UNRESOLVED**, full stop. The share is then
   *uninterpretable*, not merely weak: near 50 % it cannot distinguish "real but per-position random" from
   "nothing to measure".
2. **If yes, then the share decides:** high (≥85 %) → **PER-POSITION**; ~60 % → **SESSION-LEVEL**; ~50 % →
   **PER-POSITION RANDOM**.

**Applying that order changed five of the rows above.** CorrHistV2, TtPruneV2, CuckooRep, HistRework and the
wall-time figure are **all UNRESOLVED** — every one of their bootstrap intervals on the pooled ratio includes 1.0
(TtPruneV2 [0.8814, 1.0307], CuckooRep [0.9376, 1.0487], CorrHistV2 [0.8887, 1.0108], HistRework [0.9567, 1.1106]),
and the geometric-mean intervals agree. **Including CorrHistV2, which 19-C56 called a real pooled effect — that was
wrong.** With four switches, the honest statement is: **none of them is established as a node saving at n=120 on
this set, individually.** Their *aggregate* effect (19-C53, −12.4 %) is a separate and larger measurement.

**What survives the reclassification, and it is the opposite of what the earlier findings implied:** the two claims
that hold **per position** are both **taxes** — per-node cost (90.0 %, a large pooled effect) and prefetch (93.1 %).
**Every efficiency claim about an individual switch is UNRESOLVED; the aggregate saving is session-level at 60.5 %.**

**Requirement doing real work on the document that states it:** applying this rule caught the category error in its
own table (see the prerequisite above). **That is the strongest evidence that the rule is worth having.**

## What the owner should be told about PC20, in one line

**Three statements, each classified by its own CI, in the order the rules require:**

1. **PC20 costs ~7 % more per node, on 90 % of positions — REAL, and per-position.** (median 1.071,
   IQR [1.044, 1.110], 162/180 pairs; the pooled CI excludes 1.0.)
2. **PC20 searches fewer nodes — REAL at the pooled level** (0.8761, bootstrap CI **[0.8196, 0.9364]**, excludes
   1.0), **but only ~60 % of positions share the sign**, so it is a **session-level** fact, not a per-position one.
3. **The net WALL-TIME gain is NOT ESTABLISHED.** Pooled time ratio 0.9343, bootstrap CI **[0.8676, 1.0082]**,
   **includes 1.0.** So "PC20 is ~2.8 % faster" is **not a claim I can support** at n=119.

**Note what the classification order did to this sentence — for the third time.** The previous version asserted
"net wall-time gain is ~2.8 %", which its own CI does not support; and before that it led with the fragile 12 %
saving and called the per-node tax "consistent". **A summary written before the rule was applied to it was wrong on
the two figures most likely to be quoted.** The reliable numbers are the two taxes and the pooled node reduction;
**the wall-time gain is the one the owner should not act on.**

## 2026-11-17T02:25Z — cadence

Both items confirmed in place and unchanged:
  1. `checks/prefetchreal/RESULT.md` opens the control section with the pin table (bench 11 312,866 / 13 862,329 /
     16 3,024,920 / perft5 4,865,609, IDENTICAL both builds) and the sentence "the patched build walks the same
     tree as the control and reaches the same node count, so every millisecond of the difference is per-node
     cost, with no node-count difference to confound it". Kept verbatim.
  2. `NOTE_bench_bias_is_patch_specific.md` keeps all three revisions with what killed each, and the line
     "each revision was forced by a measurement, not by a preference for caution" plus the distinction that
     three cases "kill version 2 without confirming the strong form".

CURRENT STATE OF THE SPEED THREAD (all committed):
  19-C53 node saving 12.4 % but only ~2.8 % wall time
  19-C54 per-node median 1.071 IQR [1.044,1.110], 90 % of 180 pairs, tail contributes nothing
  19-C55 bench node-effect SIGN flips across benches 11/13/16
  19-C56 CorrHistV2 4.3 %->5.2 % transfers, but 54.2 % coin flip per position
  19-C57 audit of every bench-based node claim
  19-C58 prefetch 9.80 % on real positions - GENERAL, my prediction wrong
  19-C59 coin flip is a property of the switch; two smokes are n=2, not a rate

next command: continue at cadence. Remaining area-9 surface: the two open items from the audit that no seat has
  picked up - (a) whether the 54.2 % coin-flip shape holds for TtPruneV2/CuckooRep/HistRework individually or is
  specific to CorrHistV2, and (b) a real-position re-check of the ONE remaining bench-only speed claim in my
  record, 19-F9's material-key cache ("not measurably faster", null with a plant).
