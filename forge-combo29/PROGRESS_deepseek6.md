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
