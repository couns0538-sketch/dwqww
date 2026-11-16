LmrFine F-option sanitizer sweep -- prediction (own commit, before the first measuring run)
2026-11-16T16:47:30Z

What runs: LmrFine.patch.txt on a clean 6b98f2170 copy, RelWithDebInfo + ASan/UBSan
(-fsanitize=address,undefined -fno-omit-frame-pointer). Depth 10, S14, sets O (200) and G (353),
sanrun.py + sancount.py as in long 7/8. Ten runs per set: LmrFine=1 alone ("fine1"), and LmrFine=1 with
each of the EIGHT F options moved once from its default:
  LmrRoundF 512->0, LmrTtPvF 1024->2048, LmrNotImprovingF 1024->0, LmrCutNodeF 2048->0,
  LmrTtCaptureF 1024->0, LmrGiveCheckF 1024->0, LmrInCheckF 1024->0, LmrCutoffAddF 1024->0.
The defaults rows already exist (tests_deepseek6_long8/runs/LmrFine_{O,G}_def.rows, 0 sanlines,
3,809,466 / 7,290,580) and are the comparison base; I do not rerun them.

Predictions, each with the range that kills it:
1. EVERY new run finishes with 0 sanitizer lines and exit 0 on all 553 positions.
   Kill: any sanitizer line in any run.
2. fine1 is row-for-row IDENTICAL to the defaults rows on BOTH sets (the fixed-point/integer identity
   also holds at depth 10 and under the sanitizer).
   Kill: any differing row on either set.
3. The four moves long 5c showed wired at depth 12 -- LmrTtPvF 2048, LmrCutNodeF 0, LmrCutoffAddF 0,
   LmrFineHistory... (FineHistory is a switch, moved 0->1) -- differ from the defaults rows in NODES on
   BOTH sets. For the fine1-relative runs the same four differ from fine1.
   Kill: any of these four equal on all positions of either set.
4. Of the four long 5c could NOT show wired (LmrNotImprovingF, LmrTtCaptureF, LmrGiveCheckF,
   LmrInCheckF, each moved to 0): I predict AT LEAST ONE differs somewhere on O or G at depth 10
   (a move to 0 removes the term entirely, a bigger step than the whole-unit moves that failed to show
   wiring). Kill: all four identical to fine1 on both sets -- that would mean the four are dead code,
   which is a kimi5 finding, not a measurement error; either way the prediction is then wrong.
