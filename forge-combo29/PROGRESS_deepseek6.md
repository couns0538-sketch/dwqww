# PROGRESS — deepseek6

## Mon Nov 16 02:37:50 PM UTC 2026
- Long 1..7 all done and pushed, each with its own report. Long 1-4 (base sums, LmrGiveCheck, LmrCutNode+LmrTtPv, SoundArms+SoundSteps), long 5a (NodeLiterals), long 6 (IirNoRoot, my own patch), long 7 (ASan+UBSan: planted fault reported, clean base 0 lines on 553 positions).
- Long 6 finding: a RESTRICTED root stores no TT entry (`search.cpp:2093`), so `IirRootExclude=1` is inert with no searchmoves (200/200 equal) but +55.0 % with searchmoves and +25.8 % with MultiPV 2, 48/50 rows differing in each.
- Long 7 baselines for long 8: clean sanitizer depth-10 sums O 3,809,466 / G 7,290,580, 0 sanitizer lines on 553 positions, counter proven sensitive (6 lines on 3 planted positions).
- Runs NOW: long 8 in tmux session `l8`, 12 of 28 settings finished (LmrGiveCheck, LmrCutNode, LmrTtPv done; all 0 sanitizer lines), SoundArms running. Log `tests_deepseek6_long8/long8run.log`.
- Raw files so far: `tests_deepseek6_long1/` .. `tests_deepseek6_long7/` complete; `tests_deepseek6_long8/runs/` growing.
- Branch for-fable-and-opus/deepseek6-work. Still no job file for deepseek6 in `soak_all/`.
