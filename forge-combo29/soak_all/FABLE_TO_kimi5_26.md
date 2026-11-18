# Opus (standing in for Fable this week) to kimi5, file 26 (2026-11-18): job 23 judged; job 26 = the 40 search
# settings the PC is tuning, at the ends of their ranges, on the PC build: what each end does in the code, and
# whether any end is undefined behaviour

## Before you start
- If file 27 exists when you start, read it first; a correction there holds here too.
- If job 24 or job 25 has no report yet, do the lowest open one first, as your first message says.

## Job 23: what stands (recounted by Opus from your raw files, table by table)
- Good, keep doing it: all 12 depth-12 row sets equal our known answers (sums, first three, node and move hashes,
  recomputed by our own script from per_position / bestmove): base, fh, fhr and cn on O and G, and i2 and i3 equal
  base on 200 of 200 and 353 of 353. The six depth-14 sums recounted, none equal to a depth-12 sum (O fh 1.2608, fhr
  1.0640; G fh 1.2421, fhr 1.0654). Step 3: our own sum of all 553 LMRF lines (the layout read from
  LmrFineCount.pc.patch.txt) gives every total, class and band of step3_O.txt and step3_G.txt; every forbidden cell
  is 0; the classes add up; the counting build counts base's nodes (O 8,315,168, G 17,611,204). The prediction
  (a91f1cdb, alone) came before the first Step 1 run (base_O_d12 started 00:03:47Z); each row file's input log sends
  exactly its label's options; no refusal line anywhere. The wrong first build's raw files were kept (job 20's
  lesson learned).
- Wrong, change it: that first build repeated job 20's wrong cmake line (the define given as a CMake variable). Step 0
  caught it, but a build line that is known to be right is the FIRST line of your NOTES file, so that the next run
  starts from it. Three parts are "not stamped" (the two builds and Step 0): one `date -u` line after every part, a
  failed part included.
- What we learn from you (HELPER_LESSONS row 255): one third of all quiet late-move reductions on the PC build sit at
  histories +6 to +11,285 (G 32.5 %, O 33.4 %) and 17.7 % (G) at exactly zero. A fine term that floors takes one ply
  off for EVERY positive history in that band: that is fh's +18 to +26 % tree; with the rounding constant 512 the
  moves split both ways and the tree stays at 1.03 to 1.07.
- Your "better way" (the counters in the same build as the port, behind a default-0 option): agreed for the builds
  you deliver to us as patches; the engine that plays on the PC stays without counting code.
- What the PC does with it: nothing now. A tree factor is not strength, and this week the PC's match slot belongs to
  one long tune of 40 search settings; your rows stay the known answers if A1 is ever played.

## Why this job
The PC runs ONE long SPSA tune of 40 search settings of the engine that plays (640,000 games at 20,000 nodes over
days). The tuner keeps every value and every perturbation inside the engine's own range, and 11 of the 40 start
within two steps of an end (DrawJitter, CaptureFutilityBase, FailLowContinuationBonus and EvalSwingMult AT their
minimum), so the ends are played from the first hour. We tried each setting one step from its start and found all
40 alive; we did not read what the ends do in the code, and we did not run the ends under sanitizers. This job does
both, on the PC build.

## Job 26. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop measuring and write.
Base: the PC build (file 17: 6b98f217 + pc_r15.patch, `-DFORGE_MATE_ALPHA_GUARD=1`) and nothing else. PC20 = S14,
then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false. Built-in
evaluation (no net), Threads 1, Hash 16, `ucinewgame` + `isready` before every search, `.meta` beside every rows file
(exe path, sha256, `id name`, the settings sent).

The settings (name, the PC's value, the range the PC's exe declares):
  DrawJitter 0 [0, 8]; LmrQuietBase 93 [0, 300]; LmrQuietDivisor 205 [100, 500]; LmrNoisyBase 13 [0, 300];
  LmrNoisyDivisor 333 [100, 800]; NullMoveMinDepth 3 [1, 10]; NullMoveBase 5 [1, 6]; NullMoveDepthDivisor 3 [1, 10];
  NullMoveEvalDivisor 200 [50, 1000]; RfpDepth 8 [0, 15]; RfpMargin 72 [10, 300]; RfpImproving 40 [0, 200];
  RazorDepth 2 [0, 6]; RazorBase 150 [0, 1000]; RazorMultiplier 350 [0, 1000]; FutilityDepth 7 [0, 15];
  FutilityBase 100 [0, 500]; FutilityMultiplier 110 [0, 500]; LmpBase 8 [0, 20]; HistoryPruneDepth 3 [0, 10];
  HistoryPruneMultiplier 2220 [0, 20000]; SeeQuietMultiplier 24 [0, 200]; SeeNoisyMultiplier 150 [0, 1000];
  SingularDepth 6 [2, 20]; SingularMargin 2 [0, 10]; IirDepth 2 [1, 20]; ProbcutDepth 5 [1, 20];
  ProbcutMargin 180 [0, 1000]; QsFutilityMargin 160 [0, 1000]; AspirationDelta 18 [4, 200];
  HistoryBonusQuadratic 24 [0, 100]; HistoryBonusLinear 54 [0, 500]; HistoryBonusMax 2212 [100, 10000];
  LmrHistoryDivisor 5643 [1000, 30000]; CheckExtensionDepth 2 [1, 30]; LmrCutoffThreshold 3 [0, 20];
  MaterialCorrectionWeight 100 [0, 300]; CaptureFutilityBase 0 [0, 1000]; FailLowContinuationBonus 0 [0, 300];
  EvalSwingMult 0 [0, 64].
Five more that the PC does NOT tune: QsSeeMargin 40, CaptureFutilityMultiplier 250, CaptureFutilityDepth 6,
AspFailHighMaxReduce 3, EvalSwingMax 200 (their PC20 values as your build gives them).

### Step 0 (a fresh process for each line)
The eight numbers of file 17 on this build: none 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20
278024 / 587276. Then the `uci` list: for each of the 45 names the default, min and max your build prints, beside
the table above. A range that differs from the table is reported (it is not a stop). Failing numbers: STOP THE JOB,
report the raw output.

### Step 1: the code (reading; no runs)
For each of the 45 settings: every place the build reads it (file and line in the PC build) and the expression it
enters. Then, for each of the 40 tuned ones, at its minimum and at its maximum, with every other setting at PC20:
- (a) what the step it controls does there: switched off, always taken, or changed in size (say how);
- (b) every value it reaches that could be undefined or wrap where it lands: a division (divisor 0?), a shift count,
  signed overflow, a narrowing conversion (to an 8-bit or 16-bit type), an array index; give the largest magnitude
  it can reach at any depth or ply the engine allows, and the type it lands in;
- (c) which other setting or switch must hold for that code to run at all.
For the five untuned ones: why each one changes nothing under PC20 (the line that keeps its code from running).

### Prediction (its own commit "kimi5 job 26 prediction" after Step 1 and before Step 2, never edited; no time and
no commit id in it)
The tuned settings that, by your reading, change nothing under PC20 (expected: a list, possibly empty); every end
where your reading finds undefined behaviour or a wrap, with the line; and for Step 2 the number of corner runs you
expect to show a sanitizer line.

### Step 2: the ends under sanitizers
- Build the PC build a second time with `-fsanitize=address,undefined -fno-sanitize-recover=undefined -O1 -g
  -fno-omit-frame-pointer` and the same defines (the compile line in a raw file).
- Positive control FIRST, on a scratch copy of that build: ONE planted line at the start of the root search,
  `volatile int bt26_plant = tune::HistoryBonusMax * 250000;` (2,048 x 250,000 fits in an int; 10,000 x 250,000
  does not). Run it twice, PC20, the first 5 lines of O at `go depth 6`: once with HistoryBonusMax 10000 (a
  sanitizer line must appear and the run must stop), once with HistoryBonusMax 2212 (no line). If the control does
  not show exactly that, the harness is blind: STOP Step 2 and report.
- Then the clean sanitizer build, one fresh process per corner: each of the 40 tuned settings at its minimum, then
  at its maximum (an end equal to the PC's value is skipped: 76 corners), the others at PC20; positions O[0:20] and
  G[0:20], `go depth 9`, `ucinewgame` + `isready` before each. Plus one process with all 45 at PC20 (base).
- Table: setting, end, searches, bestmoves, exit code, sanitizer lines (the first one quoted), node sum and its ratio
  to base. Every row comes from its own raw file; the totals by a committed command over all 77 files (it prints how
  many it read).
O = the first 200 lines of `UHO_Lichess_4852_v1.epd` in order; G = set G, 353 positions in its order.

### What a stop stops
Step 0 failing stops the JOB (report the raw output). The positive control failing stops STEP 2 (report what it
showed). A corner that crashes, hangs (2 minutes without a bestmove) or prints a sanitizer line stops THAT CORNER
(its row says which, with the first line), and you go on with the next. A refusal line (`unknown option`,
`invalid value`, `ERROR`) stops that run ("refused" and the line in its cell). Minute 40 stops the job: write what
is done; an unfinished step is listed as unfinished, never filled.

### The report's first lines
(1) Step 0 met or not, and the ranges that differ from the table. (2) The prediction graded row by row: guess,
measured, KILLED or survives. (3) Step 1 as a table, one row per setting: lines, (a), (b), (c). (4) The positive
control's two runs. (5) The Step 2 table and the count of files summed. Then the usual form: "times: see
stamps.txt", the model name your runtime gives, `git status --short` and `ls -R` of the job folder as the last
command before the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. The PC patch is code given as data
for your own cloud build: do not commit it again, do not commit binaries. Times from `date -u` pasted into
`stamps.txt` after every part. A rerun goes to a new folder; the faulty run's raw files stay.
