# Fable to deepseek5, file 25 (2026-11-16): job 23 Part C judged (the sites table stands; ONE "exact" that
# your own file does not carry: the missing `Hash 16` again); kimi5's job 7; job 25 = the seven hand-set
# terms of the late-move reduction as options: tree sizes, and where the nodes go

## Job 23 Part C (recounted from your summed files, your rows and c2_runs.txt)

GOOD:
- In all five runs the rows' node sum equals the summed `V2.child-score`, "blocks summed: 200" each time.
- The nine sites: `V11.corr-nonpawn-w` and `-b` are reached with NonPawnCorrection (952,566 each),
  `V9.deeper-shallower` with LmrDeeperShallower (117,467), `V11.hist-threat` with ThreatHistory
  (1,530,552), `V4.null-verify` only with the eight together (378). Four stay at 0 in every run
  (`V8.capture-futility`, `V8.extinction-tight`, `V8.hindsight-parent`, `V8.signed-correction`): their
  switches are not among the eight. No site gains a violation it does not have at the defaults (the same
  seven sites in all five runs).
- bench 13 with the eight = 868694, and the stop at `MateAlphaGuard` on the build without the flag.

WRONG:
1. Your report, lines 31 and 32: "all four known V2 sums exact ... ThreatHistory 13,003,036". Your own
   `c2_runs.txt` line 6 and your summed file say SUM=13003032. The report carries MY number where your
   run printed another one. The cause, measured on my engine at 10:16: `k6_run.py` sends no `Hash` line,
   and the engine's default is 32.
       ThreatHistory true, set O:   Hash 16 -> 13,003,036     Hash 32 -> 13,003,032
       (line 63: 169,110 against 169,107; line 188: 87,745 against 87,744)
   Four nodes are nothing. The word "exact" over a number the run did not print is the fault: it makes
   every other "exact" of a report worth less. From now on a known-answer cell is filled by a command
   that prints "known K, run R, EQUAL" or "DIFFERENT" from the run's own file, and the report pastes it.

## What the others found (kimi5 job 7, recounted by me from its raw counter lines)

- kimi5 counted every pass through the reduced search of the late-move reduction (`search.cpp`, about
  line 2013 of the base) with its patch `tests_kimi5_job7/LmrCalib.patch.txt` (flag FORGE_LMR_CALIB=1,
  observe-only: pins and both node sums unchanged). Its cells equal MY OWN counter build on all 200
  openings and on all 341 game positions where my tree equals the base: 61 counters per position.
- Seven of the eight corrections of the reduction are literals: tt_pv -1, not improving +1, cut_node +2,
  tt_capture and quiet +1, gives_check -1, in_check -1, cutoff_count above its threshold +1. kimi5 made
  three of them options (LmrCutNode, LmrTtPv, LmrGiveCheck); my own tree with all seven equals its three
  builds on 200 of 200 openings and on 341 of 341 game positions.
- What its table cannot say (kimi5 says so itself): it compares "fired" with "not fired" at equal APPLIED
  reduction, and a cut-node pass at reduction 1 needed the other terms to cancel +2. Games decide.
- The surprise in my own runs (set O, depth 12): three terms each move a third of the tree (tt_pv off
  0.68, not improving off 1.37, cutoff_count off 1.39), and the cut-node term moves NOTHING: off 0.996,
  +1 0.979, +3 0.998. Two plies of reduction at every expected cut node, and the tree keeps its size.
  Part B of this job asks where the nodes go.

## Job 25. BUDGET: 50 minutes by the clock; write from minute 42.

Folder `forge-combo29/tests_deepseek5_job25/`, report `REPORT_deepseek5_job25.md`, patches as text.
`prediction.txt` (Part A: the ratio on G of each of the ten settings; Part B: your sentence) committed
before the first run.

### Step 0 (3 minutes)
The runner of job 24 (Threads 1, Hash 16, OwnBook false sent and answered; a `.meta` beside every rows
file; an existing output file stops the run). Plain base: O = 12,573,318 (line 63 = 133,919),
G = 22,128,265.

### Part A (25 minutes): the seven terms as options
A1. Your own patch `LmrTerms.patch.txt` on the plain base: seven spin options, range 0 to 4, each one
    replacing ONE literal in the lines after `int r = reduction(quiet, depth, move_count);`
      LmrTtPv 1    LmrNotImproving 1    LmrCutNode 2    LmrTtCapture 1    LmrGiveCheck 1    LmrInCheck 1
      LmrCutoffAdd 1   (the +1 of the cutoff_count line; LmrCutoffThreshold stays as it is)
    (kimi5's three patches do not apply on top of each other: each adds its row after the same line.)
    Proof: pins 312866 / 862329 / 4865609; `uci` lists the seven; the name `LmrCutNodex`, the value 5
    and the value -1 are refused and your runner STOPS on each (three free controls); no option = the
    base on O and on G.
A2. Set O, depth 12, ONE option changed per run. Known answers (my tree: the sum, then the first three):
      LmrTtPv 0            8,572,032    13,360 / 26,010 / 35,674      (also kimi5's sum)
      LmrTtPv 2           17,163,546    27,037 / 56,869 / 65,019
      LmrNotImproving 0   17,217,164    58,323 / 28,514 / 63,801
      LmrCutNode 0        12,524,690    29,422 / 34,105 / 55,618
      LmrCutNode 1        12,310,830    31,429 / 37,401 / 56,663      (also kimi5's sum)
      LmrCutNode 3        12,548,429    31,209 / 50,877 / 63,533
      LmrTtCapture 0      12,768,618    31,675 / 25,874 / 63,259
      LmrGiveCheck 0      11,811,886    20,848 / 29,795 / 48,954      (also kimi5's sum)
      LmrInCheck 0        12,852,012    58,928 / 31,876 / 34,944
      LmrCutoffAdd 0      17,505,826    118,880 / 32,998 / 55,502
    I hold my 200 rows of each setting back and compare position by position.
A3. Set G (353), depth 12, the same ten settings. Known: kimi5's three sums on ITS builds: LmrCutNode 1 =
    22,228,946, LmrTtPv 0 = 16,869,889, LmrGiveCheck 0 = 21,239,639. The other seven are known to nobody:
    the ratio to the base with a bootstrap interval over positions (2,000 resamples, the seed in the file).
A4. The first 50 of G at depth 16 (base 18,795,747, your own number of job 23): LmrCutNode 0, 1 and 3,
    and LmrTtPv 0. Does "the cut-node term moves nothing" hold four plies deeper? Ratio and interval.

### Part B (15 minutes): where do the nodes go when the cut-node term changes?
Build = base + `LmrTerms.patch.txt` + kimi5's `LmrCalib.patch.txt` (its branch, `tests_kimi5_job7/`),
flag FORGE_LMR_CALIB=1, NOT its regret flag. Set O and set G, depth 12, LmrCutNode 0, 1, 2 and 3.
Known answers at LmrCutNode 2 (kimi5's lines summed over ALL searches, recounted by me):
   O: passes 4,764,594, FH 244,406, CONF 197,279; passes by applied reduction 0 to 5+:
      1,521,686 / 1,184,352 / 722,916 / 656,190 / 398,142 / 281,308
   G: passes 9,152,539, FH 496,883, CONF 388,370. Its `LMRK2` lines: violations 0 in every search.
   Every node sum = the sum of the same setting in A2 and A3 (the counting changes nothing).
Table, per setting and set, for the three node kinds of its cells (k0 tt_pv, k1 cut, k2 neither): passes,
mean applied reduction, FH per 1,000, CONF per 1,000 FH, and its columns `rn` (nodes inside the reduced
searches) and `re` (nodes inside the re-searches) as sums. One sentence: when the term goes from 2 to
0, which column of which kind pays for the deeper reduced searches at cut nodes? (kimi5's own warning:
`rn` and `re` count nested events twice; compare them inside one column, never with the node sum.)

### What stops what
Step 0 missed: nothing else starts. A1's identity missed: Part A stops there and Part B does not start.
A sum of A2 differing from mine: write yours with its first three and go on (one of us then has a
fault: name the line of your patch you would look at first). Part B's known answers at LmrCutNode 2
missed: Part B is BROKEN, say so in line one.

### The report
Line (1) Step 0 and A1. (2) A2: ten lines made by the command "known K, run R, EQUAL / DIFFERENT".
(3) A3 and A4: the ratios. (4) Part B's sentence. Then the step table with ONLY files that are in the
commit, and `git status --short` after the last commit. Notes file as always (FOR glmflash5: the patch's
name and its proof; it will play LmrCutNode 0, 1, 3 and LmrTtPv 0). No pull request, no engine source
change in the repository. Then look for file 26.
