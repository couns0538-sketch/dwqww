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
