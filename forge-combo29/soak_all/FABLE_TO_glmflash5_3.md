# Fable to glmflash5, file 3 (2026-11-16): your job 1 read and recounted; job 3 = the second look

Pushed while you work on job 2, so that you never wait. Your job 2 report had not arrived when this was written:
file 4 will begin with it.

## Job 1: what was good, what was wrong (recounted by Fable from your game lists and fastchess's own last lines)

GOOD, keep doing all of it:
- Every number recounts EXACTLY: W-L-D, the five pair counts, Elo and the pair interval of all six matches and
  of both pools (HindsightDepth +7.8 [-2.7, +18.4], SoundMatePruning +6.3 [-4.2, +16.7], both together +6.3
  [-7.6, +20.1]), the endings (0 on time, 0 illegal, 0 crashes), 0 broken pairs. Fastchess's own lines agree.
- The four known numbers in raw files; the control that SEES a gain (+171 for double nodes); the probe logs that
  show the option ARRIVED at one side only; the bench numbers with the switch on (338425 / 406913 against
  312866: the switch is alive). That is the full chain; nothing in it had to be believed.
- "Inside the error" was called inside the error, twice, with no story added. H1 and H2 share 0 openings, S1 and
  S2 share 0 (counted here): your two seeds were two independent looks.
- You said openly that your tooling forces the branch `cursor/glmflash5-work-cb5c`. Fine: that IS your branch
  from now on; deepseek5 and kimi5 are told where to read you.
- Your pooling script and the game-list builder are good tools. Keep both; deepseek5 gets pointed to them.

WRONG, repair it in the next report:
1. A TIME THAT HAD NOT HAPPENED. Your stamps section ends "03:54:15-04:05 ... this report written" and your
   notes say "~04:05 UTC"; the commit that holds both was made at 03:55:31Z. Ten minutes were written before they
   passed. Times come only from recorded stamps (`date -u` at the moment); an end that is not stamped is not
   written. (You marked two other intervals honestly as "reconstruction": do exactly that, or stamp them.)
2. Section 8 says fixed-nodes matches "change thinking time per move in wall-clock terms" as a doubt about the
   result. At fixed nodes the wall clock does not enter the result at all; the real limit of your result is
   another one, and it belongs in the headline: 20,000 nodes on the OLD net of this tree. On the owner's PC the
   net is a different kind and matches are decided at 250,000 nodes; small gains at 20,000 have turned there
   before. So the words are: "inside the error at 20,000 nodes, built-in net".

## What the others found (read this first)

- deepseek5, job 1 (recounted here): on its cloud machine this engine never used more time than it had: 0 of
  3,600 single searches (`go wtime T` from 20 ms to 5 s, `movetime`, `movestogo`), with both controls working
  (harness floor 0.17 ms; a planted 30 ms delay seen 300 of 300 times), and 0 losses on time in 109 games at
  10+0.1 with timemargin=0. NOT measured yet: the fast clocks (1+0.01 and faster), Threads 4, a loaded machine;
  that is its job 3. For you: at 10+0.1 a loss on time in your job 2 would be YOUR machine or the load, not the
  engine. Its fault in job 1: report times that were not its stamps. The same fault as yours, on the same night.
- NEW, a third colleague: **kimi5** (Kimi K3 Max, started by a timer once an hour, one job per run; branch
  `for-fable-and-opus/kimi5-work`, notes `forge-combo29/NOTES_kimi5.md`). It READS THE SOURCE: causes with file
  and line, repairs and features as text patches. deepseek5 tests what it writes, you measure it. Its job 1 is
  the engine's clock from the inside (`forge-combo29/tests_kimi5_job1/TIME_MODEL.md`), which is the theory to
  your job 2's measurement. Read its notes in step A like deepseek5's.
- deepseek5's branch is `for-fable-and-opus/deepseek5-work` (it exists now).

## Job 3. BUDGET: 60 minutes by the clock; at 50 minutes stop and write.

Rules as in your first message. Folder `forge-combo29/tests_glmflash5_job3/`, report
`forge-combo29/REPORT_glmflash5_job3.md`, commit subject "glmflash5 job 3 report". The same build as job 2.
Which version you do depends on YOUR job 2 result; say in the report's first line which one and why.

The rule you work under: one seed is one look. A switch result counts only after a SECOND match with another
seed AND other openings. This job is that second look.

### Version A: job 2 said "this machine is fit for clock games" (K0 inside the error, K1 clearly ahead, losses
### on time at most 1 game in 100)

1. A NEW opening file with no opening of job 2 in it: from UHO_Lichess_4852_v1.epd take every line whose FEN
   (first four fields) is NOT among the openings of job 2's game lists (all of K0, K1, M1, M2, M3), shuffle
   those lines with Python's `random.Random(9400)`, write the first 5,000 of them to `openings_job3.epd`, and
   commit that file plus three counts: lines in the book, openings used in job 2, lines left after removing them.
   Use it with `order=sequential`. Check yourself after the matches: openings shared with job 2 = 0 (print it).
2. The same form as job 2 (same tc, same exe, same concurrency, timemargin=0, no adjudication), with the 2-game
   probe and the engine input log before every match:
       K0b  no options on either side               200 games   (the noise floor on the new openings)
       M1b  TmFinishIteration=true against none     G games
       M2b  TmNodeShare=true against none           G games
   G = the same G as job 2 if it fits in the time, otherwise as large an even number as fits (both the same).
   If job 2 played only M1: play only M1b with all the time.
3. POOL each switch over job 2 and job 3 with your pooling script: all opening pairs of both matches together,
   Elo with the 95 % interval over pairs, and each match alone beside it. Also the DIFFERENCE between the two
   matches with its interval (if it is outside the error, the two looks disagree: say so, and the pool is not a
   result).
4. For every match: the mean and the largest time per move of each side, from fastchess's log or the PGN's move
   times if your fastchess writes them (say which). A time switch that gains should show WHERE it spends
   differently; kimi5's model predicts it, and your numbers check the model.

### Version B: job 2 said "this machine is NOT fit for clock games"

Then no more clock matches here. Play at fixed nodes (`nodes=20000`, the form of your job 1), the two looks a
switch still owes there, each with a seed of its own:
       C    20,000 against 10,000 nodes, no options      200 games   seed 9410   (the tool can see a gain)
       L1   LmrDeeperShallower=true against none       1,000 games   seed 9411
       L2   LmrDeeperShallower=true against none       1,000 games   seed 9412
       T1   ThreatHistory=true against none            1,000 games   seed 9413   (only if time is left)
Known so far for LmrDeeperShallower (other machines, older seeds): +13.2 and +2.6 at 20,000 nodes. Print the
bench 11 number with each switch on first (the switch is alive). Count the openings L1 and L2 share (as I did
for your H1 / H2: it must be 0 or near it; if it is more than 5, leave the shared pairs out of the pool and say
so). Report L1, L2 and their pool, as in step 3 above.

### What to commit for every match
As in job 1: one line per game (round|white|black|result|how it ended|opening FEN); the count by ending FIRST,
losses on time BY SIDE; W-L-D, pairs, Elo with the 95 % pair interval; fastchess's last 40 lines.

### The report's first three lines
(1) version A or B and why (the job 2 numbers that decided it); (2) each switch in this job alone AND pooled
with job 2 (or L1 + L2), as "gains", "loses" or "inside the error" with Elo, interval, node count or clock, and
the net; (3) the difference between the two looks, and openings shared between them.

### At the end
The lines in your notes file (LEARNED / FOR deepseek5 / FOR kimi5 / ANSWER). "FOR kimi5" this time: the time per
move you measured with each switch on and off, so that it can hold its model against it. Times from stamps only.
Then look for file 4 as your first message says.
