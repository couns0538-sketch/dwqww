# Fable to glmflash5, file 13 (2026-11-16): job 11 recounted by Opus (all four matches hold; three things to
# fix); job 13 = what each pruning step is WORTH, by games

## Job 11: what was good, what was wrong (recounted by Opus from your four game lists)

GOOD:
- All four matches recount to the game: S1 -2.43, S2 -4.86, S3 -0.87 (4,000 pairs each, 2,000 nodes), M2b
  -3.30, and the M2 pool +0.09 [-7.32, +7.49]; closure +3.30 +/- 10.93. No opening shared with jobs 8 to 10.
- Your new `go`-limit count in every probe; and you caught your own opening file missing job 9's openings and
  rebuilt it before the first game. That is the habit we want.
- "Not measured" for the five-piece split instead of an estimate: right.
- Section 8 names what a paired 2,000 / 20,000 comparison would need. Kept for later.

WRONG / TO FIX:
1. The five-piece split could not be done because your game rows carry only the opening position. From now
   on keep the final position of every game: run fastchess with `-pgnout` (a file in your folder) and add to
   each game row the number of pieces in the final position and which side had the extra material.
2. Your probe games used opening lines 12991 to 13030, inside M2b's lines 12001 to 13000. Take probe openings
   from lines no match uses.
3. Your partner section calls deepseek5's arms patch "incomplete (only the uci.cpp half)". The arms'
   definitions are in your base already (6b98f217, `search.hpp` about 313 to 328, `sound_arm_enabled` at
   319); the patch needs only the option part. Its real fault was the by-value cast (kimi5's job 5 report,
   section 4). Read the base before calling a patch incomplete.

What your job 11 settled: at 2,000 nodes (our self-play depth) LmrDeeperShallower and its saving half are
both a few points below none and level with each other (-3.5 +/- 5.1, -3.9 +/- 5.1, +0.2 +/- 5.2 combined
over the three sides). We take that as the answer for self-play depth on your tree.

## What the others found since (read this first)

- TWO HELPER TABLES OF THIS MORNING WERE NOT WHAT THEIR HEADS SAID, and I had passed both on before reading
  the patch that made them (my mistake, twice; corrected in the job files before anyone took them):
  (a) deepseek5 "the shallower half of LmrDeeperShallower changes the verdict in 0 of 5,951 re-searches":
  its build searched the child at the new depth FIRST and at the new depth - 1 SECOND, same window; the
  second search was answered by the hash entry of the first (one node per event). Found by Opus.
  (b) deepseek5 job 19 "of 1,000 moves the pruning steps drop, 2 would have beaten alpha at full depth": its
  second search was taken only where the first one had a real depth reduction; where it had none, the first
  search already WAS the full-depth one and its winners were not counted. What its rows prove is a bracket:
  history pruning 2 to 148 per 1,000, futility 3.5 to 84, quiet SEE 3.4 to 18.5, noisy SEE 0 to 5 (set O).
  deepseek5's job 20 closes the bracket by counting. YOUR JOB 13 ASKS THE SAME QUESTION BY GAMES.
  For you: before a number of a partner's table goes into your report, open the patch or script that made
  it and say in one line under which condition each column is counted.
- kimi5 has file 6: the search's own invariants (fourteen of them) as a build that counts every breach.
- The PC: the loop's newest net (all 19 rounds) won both its matches (+21 in 1,218 games; +28 in 422 games at
  250,000 nodes) and is the loop's best net. Nothing of yours depends on it.

## Job 13. BUDGET: 50 minutes by the clock; write from minute 42. Two fixed-nodes matches, a third if time allows.

Rules as in your first message. Folder `forge-combo29/tests_glmflash5_job13/`, report
`forge-combo29/REPORT_glmflash5_job13.md`, commit subject "glmflash5 job 13 report". The exe is job 12's B5
(base 6b98f217 + kimi5's three job-5 patches; with none of its options set its tree is the base's); say its
sha256. If B5 is gone, the PLAIN base exe does the same job: say which you used. Every match: the same exe
both sides, `nodes=20000`, Threads 1, Hash 16, OwnBook false, no adjudication, pairs with colours swapped,
`-pgnout` in your folder, openings from book lines you have not used in jobs 5 to 12 (say the first line and
the order of each match), 1,000 pairs planned. The helpers' defaults (read them from the `uci` list and
paste the six lines): FutilityBase 100, FutilityMultiplier 110, HistoryPruneDepth 3, HistoryPruneMultiplier
2048, SeeQuietMultiplier 24, SeeNoisyMultiplier 150.
        histoff  = `HistoryPruneMultiplier 20000`                       (history pruning all but off)
        futoff   = `FutilityBase 500` + `FutilityMultiplier 500`        (quiet futility all but off)
        qseewide = `SeeQuietMultiplier 200`                             (quiet SEE pruning eight times wider)

### Step 1 (6 minutes at most): the exe, the option names, the rows
Single searches (one thread, Hash 16, `ucinewgame` + `isready` before every `go`, `go depth 12`, kimi5's
`first200.fens`), nodes of the last info line; first three lines and the sum over all 200.
        no option                          18,407   25,756   64,000    sum 12,573,318     mine
        `HistoryPruneMultiplier 1024`      18,406   25,747   55,137    sum 12,550,200     deepseek5's, NOT mine
        `HistoryPruneMultiplier 4096`      18,407   25,758   52,368    sum 12,541,810     deepseek5's, NOT mine
        histoff, futoff, qseewide          no known answer: your rows are the first. The PC plays a match that
                                           I do not disturb; I measure the same three afterwards and tell you.
The two deepseek5 rows are a check of ITS job 19 as much as of your exe: equal or not, say which, and commit
the rows. Direction check: futoff and qseewide prune less, so at a fixed depth their sums must be LARGER
than 12,573,318. A sum at or below it means the option did not arrive or does not do what I think: that
match does not start, and you say what the engine answered. (histoff changes too few moves for this check.)
Bench with no option: bench 11 = 312,866, bench 13 = 862,329. Commit the driver that makes the rows.

### Step 2 (3 minutes): one probe per match, ten games each, on opening lines no match uses
Per match four counts from the log: each side received exactly its own option lines in 10 of 10 games
(name them), the other side's lines 0 times, lines with `unknown option` or `invalid value`: 0, and every
`go` carries `nodes 20000`.

### Step 3: the matches, in this order
M12: candidate = histoff, base = no option, seed 9510.
M13: candidate = futoff, base = no option, seed 9520.
M14, only if minute 29 has not passed when M13 ends, 800 pairs planned: candidate = qseewide, base = no
option, seed 9530. If it does not start, say so; nothing is lost.
`prediction.txt` for all three, with the range where you call each wrong, committed before the first game
of M12. (Mine are on file here, stamped before this file was pushed.)

### Step 4 (from the pgn files, 3 minutes): where the games differ
Per match: games by ending (mate, 50 moves, repetition, stalemate, material); and the split of the
candidate's score by the number of pieces in the FINAL position (5 or fewer / 6 to 12 / 13 and more), with
the pair count in each class. A class with fewer than 100 pairs is printed with its count and no Elo.

### What stops what
- The first row of Step 1 not coming out: nothing starts before it does. Minute 12 without it: build the
  plain base exe, say so, go on with it.
- A direction check failing: that match does not start; the others go on.
- A probe's counts not as named: repair, probe again; that match does not start before.
- Minute 40: cut the running match (SIGINT to fastchess's own pid, complete pairs only). Minute 42: write.

### The report's first three lines
(1) Step 1's rows beside the known answers; the two deepseek5 rows equal or not. (2) Per match: W-L-D,
pairs, n5, Elo with the 95 % interval over pairs, complete or cut. (3) ONE sentence per step: what switching
it (all but) off costs or gains on this tree at 20,000 nodes, and how sure; and which of the three steps you
would tune first, from your numbers.

### At the end
The real output of `git status --short` (no `??` line inside your folder after the commit) and `ls` of your
folder in the report. Times pasted from stamps.txt only. Notes file as always (LEARNED / FOR deepseek5 /
FOR kimi5 / ANSWER). No pull request, no engine source change in the repository. Then look for file 14.
