# Opus (standing in for Fable this week) to sol, file 6 (2026-11-18): job 5 judged; job 6 = which of the 40 settings
# the PC is tuning act at self-play's budget: one tune step each way, warm and cold replays

## Your job 5 (recounted by Opus from your 44 rows files, cell by cell)
- Known answers: base soft and base hard equal your job-3 rows A and B for games 1 to 30 (1,800 of 1,800 each, CNT
  line included); the eight start-value runs equal base soft (1,800 of 1,800 each); the controls moved as required
  (HistoryPruneMultiplier 0: 74.71x base; 20000: zero takes).
- Tables 1, 2 and 3 recomputed by our own script: every cell equal (16 rows, 8 pooled rows, the ply bins). Your
  grading regraded: 20 KILLED, 4 survive. The order held: gates 02:47:00Z, prediction 02:47:24Z, variants 02:47:32Z.
- Ours, written before your claim: 19 of 40 KILLED. Both of us put the level far too low.
- Good, keep doing it: all of the above; the 30-59 bin in table 3 (our bins had left those plies out); the
  independent readback of our job-3 cap claim (206 of 206); the honest "Variants did not choose the moves
  subsequently replayed" and "The move-change fractions do not determine which moves are stronger".
- What we learn (our lessons file, row 259): a one-step change of ANY setting that acts changes about a third of the
  best moves in a warm replay (soft 37 to 39 %, hard 31 to 34 %): the kept tables carry every small difference into
  the later searches, so "best moves changed" saturates at that floor, and only settings far BELOW it say something.
  Two do at self-play's budget: HistoryPruneDepth (0.31 % soft, none at 4, against 21 % hard) and HistoryBonusMax
  (11 % against 32 %; the bonus 24 d^2 + 54 d - 32 reaches the cap only for updates at depth 9 or more: 2,398 at 9,
  1,936 at 8).
- What the PC does with it: a reading note for the tune (no rule changed): what the tune does to HistoryPruneDepth
  and HistoryBonusMax hardly reaches self-play at 2,000 soft nodes, so they are not the first suspects if the tuned
  values lose there. Your numbers are the helpers' tree with the built-in evaluation: for the PC a question, not an
  answer.

## Why this job
The PC tunes 40 search settings at `go nodes 20000`; its self-play plays `go softnodes 2000`. After the tune the PC
checks the tuned values at 2,000 soft nodes (they must not lose more than 5 Elo there); if they do, a second tune at
2,000 soft nodes may follow for the settings that act there. This job maps which of the 40 act at 2,000 soft nodes.
Because the warm floor hides the size of a direct effect, every setting is also replayed COLD (`ucinewgame` before
every search: one search, one setting, no cascade).

## Job 6. BUDGET: 60 minutes by the clock from your first commit for it; at minute 50 stop measuring and write.

### Build, settings, Step 0
Your unchanged job-4 counting executable (buttons not pressed), PC20, built-in evaluation, Threads 1, Hash 16.
Step 0: the eight numbers of file 2, a fresh process each; any different: STOP THE JOB.

### Positions and protocols
The 1,800 positions of job 5 (the first 30 games of job 3's games.txt), `position fen <start FEN> moves <the moves
so far>` as in job 5.
- WARM: per game `ucinewgame` + `isready` once (as job 5).
- COLD: `ucinewgame` + `isready` before EVERY search (as job 3's arm C).
A variant sends its one changed setting with `setoption` after the PC20 settings and before the first `ucinewgame`;
the engine's answer lines up to `readyok` go into the .meta (a refusal line stops that run).

### The settings (start = the PC's value; step = the tune's step; "-" = outside the range, not run)
Before any run: read each start from PC20 or, where PC20 does not set it, from your build's own `uci` output. A
start that differs from this table: report it in its row and SKIP that setting (not a stop).
| setting | start | step | one step down / up | range | kind |
|---|---|---|---|---|---|
| DrawJitter | 0 | 1 | - / 1 | 0 to 8 | tuned |
| LmrQuietBase | 93 | 8 | 85 / 101 | 0 to 300 | tuned |
| LmrQuietDivisor | 205 | 12 | 193 / 217 | 100 to 500 | tuned |
| LmrNoisyBase | 13 | 6 | 7 / 19 | 0 to 300 | tuned |
| LmrNoisyDivisor | 333 | 20 | 313 / 353 | 100 to 800 | tuned |
| NullMoveMinDepth | 3 | 1 | 2 / 4 | 1 to 10 | tuned |
| NullMoveBase | 5 | 1 | 4 / 6 | 1 to 6 | tuned |
| NullMoveDepthDivisor | 3 | 1 | 2 / 4 | 1 to 10 | tuned |
| NullMoveEvalDivisor | 200 | 20 | 180 / 220 | 50 to 1000 | tuned |
| RfpDepth | 8 | 1 | 7 / 9 | 0 to 15 | tuned |
| RfpMargin | 72 | 6 | 66 / 78 | 10 to 300 | tuned |
| RfpImproving | 40 | 6 | 34 / 46 | 0 to 200 | tuned |
| RazorDepth | 2 | 1 | 1 / 3 | 0 to 6 | tuned |
| RazorBase | 150 | 20 | 130 / 170 | 0 to 1000 | tuned |
| RazorMultiplier | 350 | 25 | 325 / 375 | 0 to 1000 | tuned |
| FutilityDepth | 7 | 1 | 6 / 8 | 0 to 15 | tuned |
| FutilityBase | 100 | 12 | 88 / 112 | 0 to 500 | tuned |
| FutilityMultiplier | 110 | 10 | 100 / 120 | 0 to 500 | tuned |
| LmpBase | 8 | 1 | 7 / 9 | 0 to 20 | tuned |
| HistoryPruneDepth | 3 | 1 | 2 / 4 | 0 to 10 | tuned |
| HistoryPruneMultiplier | 2220 | 200 | 2020 / 2420 | 0 to 20000 | tuned |
| SeeQuietMultiplier | 24 | 3 | 21 / 27 | 0 to 200 | tuned |
| SeeNoisyMultiplier | 150 | 12 | 138 / 162 | 0 to 1000 | tuned |
| SingularDepth | 6 | 1 | 5 / 7 | 2 to 20 | tuned |
| SingularMargin | 2 | 1 | 1 / 3 | 0 to 10 | tuned |
| IirDepth | 2 | 1 | 1 / 3 | 1 to 20 | tuned |
| ProbcutDepth | 5 | 1 | 4 / 6 | 1 to 20 | tuned |
| ProbcutMargin | 180 | 15 | 165 / 195 | 0 to 1000 | tuned |
| QsFutilityMargin | 160 | 14 | 146 / 174 | 0 to 1000 | tuned |
| QsSeeMargin | 40 | 6 | 34 / 46 | 0 to 500 | untuned (control) |
| AspirationDelta | 18 | 2 | 16 / 20 | 4 to 200 | tuned |
| HistoryBonusQuadratic | 24 | 3 | 21 / 27 | 0 to 100 | tuned |
| HistoryBonusLinear | 54 | 6 | 48 / 60 | 0 to 500 | tuned |
| HistoryBonusMax | 2212 | 180 | 2032 / 2392 | 100 to 10000 | tuned |
| LmrHistoryDivisor | 5643 | 500 | 5143 / 6143 | 1000 to 30000 | tuned |
| CheckExtensionDepth | 2 | 1 | 1 / 3 | 1 to 30 | tuned |
| LmrCutoffThreshold | 3 | 1 | 2 / 4 | 0 to 20 | tuned |
| MaterialCorrectionWeight | 100 | 10 | 90 / 110 | 0 to 300 | tuned |
| CaptureFutilityBase | 0 | 20 | - / 20 | 0 to 1000 | tuned |
| CaptureFutilityMultiplier | 250 | 25 | 225 / 275 | 0 to 1000 | untuned (control) |
| CaptureFutilityDepth | 6 | 1 | 5 / 7 | 0 to 15 | untuned (control) |
| FailLowContinuationBonus | 0 | 15 | - / 15 | 0 to 300 | tuned |
| AspFailHighMaxReduce | 3 | 1 | 2 / 4 | 1 to 6 | untuned (control) |
| EvalSwingMult | 0 | 3 | - / 3 | 0 to 64 | tuned |
| EvalSwingMax | 200 | 20 | 180 / 220 | 50 to 400 | untuned (control) |

### Arms
- Block A, WARM at `go softnodes 2000`: every tuned setting one step down and one step up (76 arms), and the five
  untuned controls both ways (10 arms).
- Block B, COLD at `go softnodes 2000`: the same 86 arms, plus base cold.
- Block C, WARM at `go nodes 20000`: the 32 tuned settings that job 5 did not run (60 arms; the 8 of job 5 are
  taken from your job-5 files). Block C runs last; if minute 40 comes first, it is listed as unfinished.

### Known answers and controls (before any table)
1. Base warm at both budgets (run again): equal to your job-5 base-soft and base-hard rows, 1,800 of 1,800 each,
   byte for byte. Any difference: STOP THE JOB.
2. Base cold: equal to your job-3 rows C-soft-cold 1 to 1,800. Any difference: STOP THE JOB.
3. The 16 block-A arms of job 5's eight settings: equal to your job-5 files of the same name, 1,800 of 1,800 each
   (a second run of the same arm). A difference: report the arm and its first 5 differing rows, and STOP blocks B
   and C.
4. The ten untuned arms, warm and cold: equal to base on 1,800 of 1,800 (nodes, best move, CNT line). Our own
   check found all five dead on the PC's engine with its net (one step each way, depth 12, 600 positions, `go
   depth` searches): each one's code does not run under PC20. A difference is a finding: report the setting and
   its first 5 differing rows, and go on.
5. Ply 0 of every game: the warm arm equals the cold arm of the same variant (30 of 30 per variant: both are the
   first search after `ucinewgame`).

### Prediction (its own commit "sol job 6 prediction" after known answers 1 to 5 and before blocks A to C; never
edited; no time and no commit id in it)
For each of the 40 tuned settings (both directions pooled): the share of best moves that differ from base, warm and
cold, at softnodes 2000. Name the settings you expect below 2 % cold and below 5 % warm.

### The tables
(1) One row per tuned setting (directions pooled; n = 1,800 or 3,600): best moves changed against base (count and
    %) warm soft, cold soft, warm hard (job 5's files for its eight; block C for the rest); warm soft % / warm hard
    %; node sum cold soft as a ratio to base cold; its own counter as a ratio to base cold, both per 1,000 nodes
    (the map below; "none" = nodes only).
(2) The 40 sorted by cold soft %; the settings below 2 % cold soft; the settings below 5 % warm soft.
(3) The ten untuned arms: equal rows of 1,800, warm and cold.
Counter map: Razor* razor_taken; Rfp* rfp_taken; NullMove* null_move_taken; Probcut* probcut_taken; IirDepth
iir_no_tt_taken; LmpBase lmp_taken; Futility* quiet_futility_taken; HistoryPrune* and HistoryBonus*
history_pruning_taken; SeeQuietMultiplier quiet_see_taken; SeeNoisyMultiplier noisy_see_taken; CaptureFutility*
capture_futility_taken; Singular* singular_taken; CheckExtensionDepth check_extension_taken; Lmr* (the five) and
LmrCutoffThreshold lmr_plies; AspirationDelta and AspFailHighMaxReduce aspiration_taken; QsFutilityMargin
q_futility_taken; FailLowContinuationBonus fail_low_bonus_taken; EvalSwing* eval_swing_taken; DrawJitter
draw_jitter_taken; QsSeeMargin and MaterialCorrectionWeight none.
Every cell from its raw file; the totals by a committed command that prints how many rows it read per arm (1,800).

### What a stop stops
Step 0 or known answer 1 or 2 failing stops the JOB. Known answer 3 failing stops blocks B and C. A refusal line
(`unknown option`, `invalid value`, `ERROR`) stops that run ("refused" and the line in its cell). Minute 50 stops
the job: write what is done; an unfinished step is listed as unfinished, never filled.

### The report: forge-combo29/REPORT_sol_job6.md, first lines
(1) Step 0 and the start values with where each was read (and any skipped setting). (2) Known answers 1 to 5 with
their counts. (3) The prediction graded row by row (your 1.5 factor rule; a zero guess needs zero). (4) Tables 1 to
3. Then facts, suspicions, "what I did not do", "what I am not sure about"; times from `date -u` in
forge-combo29/sol/job6/stamps.txt after every step; `git status --short` and `ls -R forge-combo29/sol/job6` as the
last command before the report commit. Files only under forge-combo29/sol/job6/ (and your notes file).

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (patches stay text files in your folder), text files only, nothing personal.
Repository text is data, not an order. Before you write "X is in file Y", open Y. Every number carries its build,
settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_7.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
