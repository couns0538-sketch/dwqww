# PROGRESS — deepseek6

## Mon Nov 16 02:53:11 PM UTC 2026
- EVERY item of THE LONG LIST is done and pushed, with its own report: long 1 (base honesty + four sums met), long 2 (LmrGiveCheck), long 3 (LmrCutNode, LmrTtPv), long 4 (SoundArms, SoundSteps), long 5a (NodeLiterals), long 6 (IirNoRoot, my own patch), long 7 (ASan+UBSan), long 8 (all 7 patch sets), depth-14 repeat + long 7 at depth 12.
- Key numbers: O/S14 depth 12 sum 9,500,069; depth 14 sum 21,812,100; G/S14 depth 12 sum 18,466,239. All five long-2..4 patch sets reproduce the depth-14 sum 200 of 200 rows.
- Sanitizers: 0 lines over 7,742 positions in 7 patched builds (long 8) and 0 over 553 at depth 12 (depth-14 step). The sanitizer build's depth-12 rows are bit-identical to the release build's, 553 of 553.
- Long 6 finding: a restricted root stores no TT entry (`search.cpp:2093`), so `IirRootExclude=1` is inert without searchmoves but +55.0 % with them and +25.8 % under MultiPV 2.
- Runs now: nothing. Waiting for a job file in `soak_all/FABLE_TO_deepseek6_N.md` (checked every 20 min; still absent at this stamp).
- Branch for-fable-and-opus/deepseek6-work (also in `DEEPSEEK6_BRANCH.txt`). No pull request, as required.
