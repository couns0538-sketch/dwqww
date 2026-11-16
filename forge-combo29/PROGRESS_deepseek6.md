# PROGRESS — deepseek6

## Mon Nov 16 04:11:48 PM UTC 2026
- Every item of THE LONG LIST is done and pushed, plus a long-8 ADDENDUM that closed my own recorded shortfall ("each option moved once"). No job file for deepseek6 has appeared (checked 04:11 UTC).
- Reports pushed: long 1 (base honesty + four known sums all met), long 2 (LmrGiveCheck), long 3 (LmrCutNode + LmrTtPv), long 4 (SoundArms + SoundSteps), long 5a (NodeLiterals), long 6 (IirNoRoot, my own patch), long 7 (ASan+UBSan), long 8 (7 patch sets), long 8 addendum, depth-14 repeat + long 7 at depth 12.
- Key known answers: O/S14 d12 sum 9,500,069, d14 sum 21,812,100, G/S14 d12 sum 18,466,239. All five long-2..4 patch sets are exact identities at d12 and d14 (200 of 200 rows).
- Sanitizers: 0 lines over 14,931 positions across 41 settings in 7 patched builds; the sanitizer build's d12 rows are bit-identical to the release build's (553 of 553).
- Best finding: a restricted root stores no TT entry (`search.cpp:2093`), so `IirRootExclude=1` is inert without searchmoves but +55.0 % with them and +25.8 % under MultiPV 2 (long 6).
- Runs now: nothing. Waiting for `soak_all/FABLE_TO_deepseek6_N.md`, checking every ~20 min.
- Branch for-fable-and-opus/deepseek6-work, at e5e10e8aa. No pull request, as required.

## Mon Nov 16 04:43:40 PM UTC 2026
- New session of deepseek6 resumed at 2026-11-16T16:27:50Z; found the branch already at b02325980 (the whole long list done by the earlier run, ended 16:11 UTC). Adopted that history; did NOT redo longs 1-8.
- Job file FABLE_TO_deepseek6_1.md read and DONE: Step 0 + 3 controls exact, Part 0 settles depth-vs-build (release d10 == sanitizer d10, 200 of 200 both ways), 70 O runs + 70 G runs + Part 3 +4c done; inert set = QsSeeMargin, CaptureFutilityMultiplier, CaptureFutilityDepth on BOTH sets; 64 of 70 runs differ on each set. Report REPORT_deepseek6_job1.md pushed (092080d97).
- No job file 2 yet (checked 16:43 UTC). Running now: closing the recorded gap - LmrFine's F options under the sanitizer.
- Raw files so far: tests_deepseek6_job1/ (150 rows files + metas + logs), tests_deepseek6_long1..long8 (prior run).

## Mon Nov 16 05:19:24 PM UTC 2026 (second run, same branch)
- DONE since the block above: job 2 (its report and mine, both kept — `REPORT_deepseek6_job2.md` and `REPORT_deepseek6_job2_par.md`), job 3 (kimi5's FailHighBlend), long 8b (LmrFine F-options under ASan+UBSan), and the LeakSanitizer positive control that was the last gap.
- Job 2 headline: three of the four Part A settings never reach 20 changed best moves on O even at 4c, and the capture-futility gate wakes the MULTIPLIER (48 and 56 of 200 rows) but not the DEPTH (B3 byte-identical to B0, B4 one node apart).
- Job 3 headline: FailHighBlend applies with zero fuzz, its sha256 equals kimi5's published hash, `FailHighBlend=0` is an exact identity (200/200 O, 353/353 G), all seven non-zero values differ, all seven composition pairs differ, and 10 sanitizer runs over 2,765 positions report 0 lines.
- Leak control: LeakSanitizer IS active — a planted `new int[16]` at the root gave "512 byte(s) leaked in 8 allocation(s)" and the root-call counter measured exactly 8 calls (6 iterations + 2 re-searches).
- Runs now: nothing. No `FABLE_TO_deepseek6_3.md` exists (checked 05:19 UTC); loop step 1 before any further work.
- Branch for-fable-and-opus/deepseek6-work. No pull request, as required.

## Mon Nov 16 05:53:05 PM UTC 2026
- Job file 3 is DONE: `REPORT_deepseek6_job3b.md` (the other session's run) and `REPORT_deepseek6_job3b_par.md` (mine) — two independent counter builds of the same job, agreeing on every count.
- Job 3b answer: with `CaptureFutilityBase 230`, prunes on O are L1 8,051 / L2 1,941 / L3 1,074 / L4 158 / L5 12 (largest L = 5, 88.9 % at L<=2); on G they run to L6 (343) with 71.9 % at L<=2. The depth limit is dead on O, alive on G, and alive on both at multiplier 100 (reaching L9 at depth 9). `lmr_depth = 0` never prunes at all.
- Step 0 for job 3b: counter build's four pins exact AND its rows bit-identical to the plain build on S14 (200/200, 9,500,069) and B0 (200/200, 9,562,828).
- All three known answers met, both arithmetic checks 0 on all 14 runs, the plant (base 0) prunes nothing.
- Runs now: nothing. No `FABLE_TO_deepseek6_4.md` (checked 05:53 UTC).
- Branch for-fable-and-opus/deepseek6-work at b31c1f65d, working tree clean, no pull request.

## Mon Nov 16 06:08:45 PM UTC 2026
- Claiming job file 4 (no 'deepseek6 job 4 prediction' on the branch; the peer's progress note of 17:53 UTC was idle). Repair first: tests_deepseek6_job3b/stamps.txt conflict markers removed, both sides kept, sorted by time (times normalized to ISO).
- Job 4 (LmrFine counter study) starting; prediction commit follows before the first counted run.
