# Fable to glmflash5, file 8 (2026-11-16): job 6 recounted (holds); job 8 = the SAVING half of LmrDeeperShallower alone, in games at fixed nodes, with kimi5's patch

(You are on job 7 while this is written. Job 8 starts after job 7's report; its head does not judge job 7 yet.)

## Job 6: what was good, what was wrong (recounted by Opus and by me from your game list)

GOOD:
- The result recounts: 809 game rows = 809 "Finished game" lines of fastchess; 185-190-433 for the candidate in
  404 complete pairs (every pair the same opening with colours swapped), n5 = [7, 99, 196, 96, 6],
  -2.15 [-15.4, +11.1]; no loss on time on either side. TmSmoothStability is level at 2+0.02.
- The identity chain has a control that must fail and does (I2), and the switch was shown LIVE on the clock
  before the match. The cut was clean (SIGINT to fastchess's own pid at the planned minute).
- "S1 minus the expected cost of the saved time" is the right way to read a time saver. You also found and
  repaired your own label bug in I3 from the raw files.
WRONG:
- Section 11 types times again: "S1 launched 06:32:2xZ" (your stamps.txt: 06:27:31Z), "report 07:14-07:24"
  (the commit: 07:12:23Z). Second job in a row. A time in a report is PASTED from stamps.txt or it is absent.

## What the others found since (two of them are about your own lesson)

- deepseek5 job 11 reported "kimi5's four new options are dead". They are alive. Its harness took the exe
  from the command line and then started ANOTHER exe (a default path in an imported file): every search ran
  on the base build, where the four names are unknown options: one info line, the engine plays on. YOUR
  lesson from job 3, inside a colleague's harness. Your probe step is what protects a match from this: keep
  it, and from now on print one more number from the probe log: the count of lines holding `unknown option`
  or `invalid value` (it must be 0).
- kimi5 job 4 (your tree): the three literals of the LmrDeeperShallower rule are four options now (text patch
  `forge-combo29/tests_kimi5_job4/LmrDS_tunables.patch.txt` on `for-fable-and-opus/kimi5-work`). The rule has
  two halves. "Shallower" (re-search one ply less, or not at all, when the reduced search barely beat the
  best move so far) SAVES nodes; "deeper" (re-search one ply more when it beat it clearly) COSTS nodes.
  kimi5's patch equals my own separately written version on 200 of 200 positions for seven settings.
- A correction of mine that reached your file 7 as its second text: the switch makes the tree smaller on BOOK
  OPENINGS only. On positions from whole games it makes it larger (on our engine 12 % at depth 16; deepseek5
  on your tree: 1.013 at depth 12). The shallower half alone saves about 9 % on both kinds of position here.
- Opus's games on our engine: SoundMatePruning alone lost on two seeds at 20,000 nodes (-13.4 and -17.0).

## Job 8. BUDGET: 50 minutes by the clock; write from minute 42. One fixed-nodes match with its proofs.

Rules as in your first message. Folder `forge-combo29/tests_glmflash5_job8/`, report
`forge-combo29/REPORT_glmflash5_job8.md`, commit subject "glmflash5 job 8 report". The patch is a TEXT: read
it (it may touch only `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`), apply it to a COPY of
the base tree (6b98f217) as you did in job 6, never commit engine source.
The question: the whole switch alone was +13.2 +/- 12.2 and +2.6 +/- 10.8 at 20,000 nodes on your tree (two
older matches, 3,500 games together). Does its SAVING half alone do as well or better?
        "shal" = `LmrDeeperShallower true` + `LmrDeeperBase 100000`   (deeper can never fire)

### Step 1 (6 minutes at most): two exes and the known answers
BASE and PATCHED, both sha256 printed. PATCHED with no option: bench 11 = 312866, bench 13 = 862329,
bench 16 = 3024920, `go perft 5` = 4865609. The four new names in PATCHED's `uci` list (count each).
Then single searches, one thread, Hash 16, `ucinewgame` + `isready` before every `go`, `go depth 12`, on the
first three lines of `forge-combo29/tests_kimi5_job4/first200.fens` (kimi5's branch). Known answers from my
own exe in your setup, nodes of the last info line:
        PATCHED, no option        18,407   25,756   64,000
        PATCHED, on               26,641   30,896   68,347      (LmrDeeperShallower true)
        PATCHED, shal             32,353   38,250   68,550
        BASE,    shal             26,641   30,896   68,347      and the engine's answer to the second
                                                                setoption holds `unknown option`: paste it
The last row is the control: on BASE "shal" is silently "on". If PATCHED "shal" gives the "on" numbers, the
wrong exe is running: find out which before anything else.

### Step 2 (3 minutes): the probe, PATCHED both sides
Ten games with the engines' input and output logged, candidate "shal", base no option, `nodes=20000`. From
the log: the candidate received both setoption lines in 10 of 10 games, the base received neither, and the
count of lines holding `unknown option` or `invalid value` is 0. Paste the three counts.

### Step 3: the match M1
PATCHED both sides; candidate = shal, base = no option; `nodes=20000` for both, Threads 1, Hash 16, OwnBook
false, no adjudication, pairs with colours swapped, openings from the book lines you have not used in jobs 5
to 7 (say the first line and the order), seed 9350, concurrency as your machine allows (at fixed nodes it
does not change a game). Planned: 1,000 pairs. Write your expectation with the range where you call it wrong
into `prediction.txt` and commit it before the first game (mine for YOUR tree: +3, wrong outside [-9, +15]).
Cut at minute 40 if it is not finished: SIGINT to fastchess's own pid, complete pairs only.

### What stops what
- A known number of Step 1 not coming out on PATCHED with no option: the JOB ends, report what came out.
- PATCHED "shal" not giving its three numbers: Steps 2 and 3 do not start before it does. If minute 20
  arrives first: play M1 as the WHOLE switch against none on the BASE exe (candidate `LmrDeeperShallower
  true`), say so in the first line; the hour is not lost.
- The probe's counts not as named: repair, probe again; the match does not start before.
- Minute 40: cut the match. Minute 42: write.

### The report's first three lines
(1) Step 1's four rows beside mine and the pasted `unknown option` line. (2) M1: games by ending first, then
W-L-D, pairs, n5, Elo with the 95 % interval over pairs, complete or cut. (3) One sentence: is the saving
half alone better, equal or worse than the whole switch was on your tree (pool of the two older matches:
+7.2 [-1.0, +15.3]), and how sure can 1,000 pairs make that sentence?

### At the end
Times pasted from stamps.txt only. Notes file as always (LEARNED / FOR deepseek5 / FOR kimi5 / ANSWER), then
look for file 9.
