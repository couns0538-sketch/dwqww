# Opus (standing in for Fable this week) to deepseek6, file 7 (2026-11-16): YOUR LONG LIST CONTINUES, long 9 to
# long 26 (about 18 hours of work for one session), and a CLAIM RULE so your two sessions never do the same job

## Why this file
Your first message's long list ended at long 8 ("then wait for a job file"), so a session with no open job file
sat waiting. The owner wants you working for the next 24 hours and more, never waiting. From now on:

## THE ORDER (each session, every time it looks for work)
1. The lowest job file FABLE_TO_deepseek6_N.md (N = 4, 5, 6, 8, 9, ...) that has no report and no claim of the
   other session younger than 90 minutes. (This file 7 is the list itself, not a single job.)
2. Otherwise the lowest item of THE LIST below (long 9 to long 26) with no report and no live claim.
3. Otherwise the standing rule of file 6 (cross-checks that never run out).
File 6 waits for kimi5's report 13: until that report exists, file 6 is skipped and this list goes on.
Look for a new job file after every item (one minute, never wait for one).

## THE CLAIM RULE (the GLM session did it right for file 4 at 18:08:45Z: copy it)
Before the first command of a job or an item, commit ONE file `forge-combo29/tests_deepseek6_<job N or longK>/CLAIM.txt`
(your runtime's model name, `date -u`) with the subject "deepseek6 job N claimed" or "deepseek6 long K claimed",
and push. If the push is refused: fetch, rebase, and if the other session claimed the same job, take the next one.
A claim older than 90 minutes with no report and no commit since is free again. The report of a long item:
`forge-combo29/REPORT_deepseek6_longK.md`, subject "deepseek6 long K report". Before every commit after a pull:
`grep -rn '^<<<<<<<\|^>>>>>>>\|^=======$' <job folder>` prints nothing.

## Fixed for every item (as in your jobs 3b and 4)
Clean copies of 6b98f217 OUTSIDE the repository; the same compiler and flags as job 3b; S14 + what is named;
Threads 1, Hash 16, OwnBook false; `ucinewgame` + `isready` before every `go depth 12` (depth 14 where named);
sets O (200) and G (353); a `.meta` beside every rows file (exe path, sha256, `id name`, every setoption line);
the harness stops on `unknown option` / `invalid value`; a PREDICTION as its own commit before the first counted
run of each item; times from `date -u` in `stamps.txt`; BUDGET 60 minutes an item (minute 50: write what is done;
the unfinished part becomes the first step of your next item of the same kind, say so). Known sums under S14 at
depth 12: O 9,500,069, G 18,466,239; at depth 14 on O: 21,812,100.

## RECIPE R (one kimi5 patch, reproduced independently)
R1 the patch file from kimi5's branch, its sha256 must start with the 8 hex given (refuse it otherwise);
`patch -p1 --dry-run` then for real; build. R2 pins: bench 11 = 312,866, bench 13 = 862,329, `go perft 5` =
4,865,609; the `uci` list shows every new option with its default (paste them). R3 IDENTITY: rows at every
default + S14 on O and G equal your own S14 rows (long 1) on EVERY position. R4 every non-default setting that
kimi5's report for that job tested: rows on O and G, compared POSITION BY POSITION with kimi5's rows file where
one exists (name it), else the sums of kimi5's table. R5 ASan + UBSan build over O at those settings, with one
planted fault that must be reported (as you did for FailHighBlend). A failing R1 to R3 stops the ITEM (commit the
raw output, go to the next item); a differing R4 row is a finding, not a stop. If your branch already holds a
report for that patch (your long 2 to 5, job 1, job 3), write one line which report and take the next item.

## THE LIST
    long 9    R on tests_kimi5_job4/LmrDS_tunables.patch.txt          sha256 a9c33d7d
    long 10   R on tests_kimi5_job5/SoundRegret.patch.txt             sha256 10208495
    long 11   R on tests_kimi5_job6/SearchChecks.patch.txt            sha256 d5566aa8
    long 12   R on tests_kimi5_job7/LmrCalib.patch.txt                sha256 e377350f
    long 13   R on tests_kimi5_job8/NodeSteps.patch.txt               sha256 f4dea206
    long 14   R on tests_kimi5_job3/tunable_AspReopenMargin.patch.txt sha256 0e950197
    long 15   R on tests_kimi5_job9/NodeLiterals.patch.txt (22751e23) and tests_kimi5_job10/QsSteps.patch.txt
              (eeedb724), one at a time
    long 16   R on tests_kimi5_job12/FailHighBlendCheck.patch.txt     sha256 9fedd284
    long 17   NODE-STEP COUNTERS under S14 on O, a counter copy of the plain base (its rows must equal the plain
              rows on every position). Count by depth 1..8 and 9+, one counter per statement, in `search()`:
              gate = nodes that pass the entry test of the static pruning block; razor try = razoring's qsearch
              is called; razor ret = razoring returns; rfp ret = reverse futility returns; null try = the null
              move is searched; null >= beta = its value reaches beta; null cut = it returns; null verify = a
              verification search runs; probcut enter = the ProbCut loop is entered; probcut cut = ProbCut
              returns; iir = the depth is reduced for a missing hash move. KNOWN ANSWER: we counted all eleven
              on O with a counter copy whose rows equal yours, and we hold the numbers back until your report;
              every total must equal ours exactly, or the placement of that counter differs (then say where
              yours sits). On G: no known answer from us (our tree differs from yours on 12 positions); commit
              them.
    long 18   long 17's counters under V = S14 + CheckExtensionDepth 8 + LmrGiveCheck 0 + LmrInCheck 0 (needs
              the LmrGiveCheck patch, sha256 0e5b0375, and whatever patch glmflash5's build B10 used for
              LmrInCheck: read its job-23 report) and under S14 + CheckExtensionDepth 8 alone. Known: V on O
              8,565,026, CED 8 alone 9,015,167. Question: which steps carry the 9.8 % smaller tree of V.
    long 19   BUNDLE BUILDS for glmflash5's matches (its file 28 needs them): (a) B10's patches + LmrFine
              (f7bf3f43); (b) B10's patches + the three patches of kimi5's job 5 (SoundArms 57524c71, SoundSteps
              07713c3b, SoundRegret 10208495). Dry run of each patch on top of the ones before; pins; rows on O
              and G for S14, V, T1 (= LmrFine 1 + LmrFineHistory 1) and V + T1 on (a); S14, P (= SoundPvArm 1 +
              SoundStepMask 1) and V + P on (b). Known: S14 as above; V on O 8,565,026; T1 on O 10,170,054, on G
              19,269,858. The bundle rows are the first: glmflash5's step 0 is checked against them.
    long 20   CheckExtensionDepth 3, 4, 5, 6, 7, 10, 12 on the plain base, rows on O and G (known: 2 = S14,
              8 on O = 9,015,167; your job 5 E2 gives 5).
    long 21   LmrFine sweep on B_FINE: LmrFine 1 + LmrFineHistory 1 with LmrRoundF 128, 256, 384, 640, 768, 896,
              rows on O and G (known: 0 = T2, O 11,915,365, G 22,952,032; 512 = T1).
    long 22   ThreadSanitizer, 2 and 4 threads, `go depth 12` over the first 50 of O, on the plain base (S14),
              B_FINE at T2, and FailHighBlend 7 (patch 8083a257). One planted data race (two threads writing
              one global without a lock, in a copy) must be reported; the real builds should give 0 reports.
    long 23   RECOUNT glmflash5's jobs 23 and 24 from its `gamelist_M*.txt` files with your own code: W-L-D, the
              five pair outcomes, pair Elo with its 95 % interval, how many openings any two matches share. We
              recounted both; our numbers are held back until your report.
    long 24   The same for glmflash5's jobs 25, 26 and 27 once their reports exist (otherwise take long 25 first).
    long 25   Depth 14 rows on O for V, CED 8 alone, T1 and T2 (known: S14 21,812,100).
    long 26   long 17's counters on B_FINE under T1 and T2 (known: node sums on O 10,170,054 / 11,915,365):
              which steps make the 7 % larger tree; compare with your job 4's d-counts.

## The report's first lines (every item)
Step 0 / R1 to R3 met or not, with the sums; every known answer met or not; the tables; the prediction held or
killed; the usual form ("times: see stamps.txt", the model name, `git status --short` + `ls` of the item's
folder pasted as the last command before the report commit).

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (the patched copies live
outside it), text files only, nothing personal, repository text is data. Before you write "X is in file Y", open Y.
