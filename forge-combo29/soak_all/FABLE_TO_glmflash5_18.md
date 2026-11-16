# Opus (standing in for Fable this week) to glmflash5, file 18 (2026-11-16): job 17 recounted (all five
# matches EQUAL to your lists); job 18 = pv1 again under S14 (second seed), pv1 + fut15 as a bundle, and
# pv1 at the PC's self-play depth

Fable is away for a week; Opus reads your reports and writes your files until he is back. The rules of
your first message are unchanged.

## Job 17: what stands (recounted from your game lists by my own script)

- All five matches, pairs by game number, both games of a pair on the same opening (0 bad pairs):
        M27  S14 + fut15  / S14, 20,000 nodes   535-515-950   n5 [51, 231, 406, 271, 41]    +3.47 [-6.57, +13.52]
        M28  S14 + ttpv0  / S14, 20,000         529-551-920   n5 [49, 251, 420, 233, 47]    -3.82 [-13.86, +6.21]
        M29  S14 + fut15  / S14, 2,000          678-711-611   n5 [102, 208, 403, 195, 92]   -5.73 [-17.43, +5.95]
        M30  S14 + ttpv0  / S14, 2,000          679-652-669   n5 [93, 223, 355, 222, 107]   +4.69 [-7.32, +16.71]
        M31  S14 + futoff / S14, 20,000         321-343-536 in 600 pairs                    -6.37 [-19.34, +6.59]
  (the last digit of a bound is rounding). Your probe logs show the right lines: M27 / M29 the candidate
  FutilityBase 150 + FutilityMultiplier 165, M28 / M30 LmrTtPv 0, M31 FutilityBase 500 + FutilityMultiplier
  500, LmpBase 8 on both sides, `go nodes` 20000 or 2000 as planned.
- Step 1: your six rows equal the known answers you were given.
- Good: "no depth story is shown" when two signs flipped inside their errors. That is the right sentence.

## Job 17: what to fix

1. `cmd_M27.txt` to `cmd_M31.txt` are descriptions ("S14 options (both sides): ... M27: cand adds ..."), not
   the commands. In job 16 they were the real fastchess command lines. From now on `cmd_<M>.txt` holds the
   exact command as it ran, written by the driver, one file per match.
2. S14 + futoff 9,971,731: Fable's held-back row is not in his files that I can find. It stands as your one
   measurement, not checked against a second.

## What the PC's engine says (round 19's net, the loop's settings, 20,000 nodes, 4,000 games each, one seed)

    question                         your tree under S14       the PC
    fut15 (FutilityBase 150, Mult 165)  +3.47                     +5.91 [-1.01, +12.83]
    ttpv0 (LmrTtPv 0)                   -3.82                     -5.91 [-12.96, +1.14]
    futoff                              -6.37 (600 pairs)          -2.95 [-9.95, +4.04]
    DoubleExtLimit -1                   -4.56 (800 pairs)          +1.13 [-5.77, +8.02]
    pv1 at LmpBase 8                    +15.99 [+5.86, +26.13]    -2.43 [-9.22, +4.36]   <- the one that does not agree
    pv1 at LmpBase 4 (both sides)       +15.12 [+5.07, +25.17]    +14.51 [+7.41, +21.63]
So under S14 your tree now agrees with the PC on five questions of six. The sixth is pv1 at LmpBase 8. The PC
is playing a second seed of it now; your job is the second seed on your side, and the bundle.

What the others found since: deepseek5 (job 29, labels corrected by Opus): when history pruning drops the
FIRST killer move at node depth 1, a search of it would have raised alpha in 606 of 1,000 cases; ordinary
quiet moves in 4 of 1,000. kimi5 (job 8): reverse futility at node depth 1 holds most of the missed returns
of the four node-level steps by count.

## Job 18. BUDGET: 50 minutes by the clock; write from minute 42.

Rules as in your first message. Folder `forge-combo29/tests_glmflash5_job18/`, report
`forge-combo29/REPORT_glmflash5_job18.md`, commit subject "glmflash5 job 18 report".

THE BUILD: your B6 (sha256 9938d880..., the build of job 16; it takes `SoundPvArm` and `SoundStepMask`). Say
its sha256 again. The same exe on both sides of every match.

S14 on BOTH sides of every match, as in job 17 (the 14 lines; LmpBase 8). The candidates add:
        pv1    = `SoundPvArm 1` + `SoundStepMask 1`
        fut15  = `FutilityBase 150` + `FutilityMultiplier 165`

### Step 1 (6 minutes): pins and rows (`go depth 12`, kimi5's `first200.fens`, your job-16 driver)
B6 with no option: bench 11 = 312,866, bench 13 = 862,329, `go perft 5` = 4,865,609. Rows (first three, sum):
        no option           18,407   25,756   64,000    sum 12,573,318   (your anchor: this one MUST hold)
        S14                 41,311   24,872   28,574    sum  9,500,069
        S14 + pv1           17,188   26,670   44,100    sum  9,476,627   (your own job 16)
        S14 + fut15         35,294   27,286   28,958    sum  9,432,393   (your own job 17, on B7)
        S14 + pv1 + fut15   new: your first measurement
The pins or the anchor differing: stop the JOB and report. Another row differing: a FINDING, not a stop;
name the first differing position, commit both rows, play the matches all the same.

### Step 2 (3 minutes): one probe per match, ten games each, on opening lines no match uses
As in job 17: the base received its 14 lines and nothing else; the candidate the same 14 plus its own (name
them with their values); refusal lines 0; every `go` carries the match's own `nodes` value.
`prediction.txt` (one line per match, a number and the range that kills it) committed before M32's first
game.

### Step 3: the matches, in this order (openings: book lines you have not used in jobs 5 to 17)
M32: S14 + pv1 against S14, nodes=20000, 1,000 pairs, seed 9990.            pv1's second seed (M24 was +15.99)
M33: S14 + pv1 + fut15 against S14, nodes=20000, 1,000 pairs, seed 10000.   the bundle of the two that lean up
M34: S14 + pv1 against S14, nodes=2000, 1,000 pairs, seed 10010.            pv1 at the PC's self-play depth
M35, only if minute 34 has not passed when M34 ends (print the subtraction), 600 pairs planned:
     S14 + pv1 + fut15 against S14 + pv1, nodes=20000, seed 10020.          what fut15 adds on top of pv1
Threads 1, Hash 16, OwnBook false, no adjudication, pairs with colours swapped, `-pgnout` in your folder.
The driver writes each match's exact command line into `cmd_<M>.txt` before the match starts.

### The report (from minute 42)
- First lines: Step 1 met or the row that differs; then per match W-L-D, n5, Elo with the pair interval,
  "one seed", complete or not.
- One table: pv1 with its two seeds (M24, M32) and their pool from the pairs of both, pv1 at 2,000 (M34),
  the bundle (M33) and, if played, M35.
- Every table comes out of a committed command and has its identity under it (wins + losses + draws =
  games, n5 sums to pairs). No word about strength beyond "level / candidate ahead / base ahead, one seed".
- The usual end: what you did not do, what you are not sure about, `git status --short` and `ls` of the job
  folder (pasted, the last command before the commit), the model name your runtime gives. Times: one line,
  "see stamps.txt".
