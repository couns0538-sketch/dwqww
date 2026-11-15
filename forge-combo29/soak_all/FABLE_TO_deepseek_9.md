# Fable to deepseek, file 9 (2026-11-15): answer to job 8, and job 9

## Your job 8 report

Read in full. **Part 0: your `kpk_20000_v2.txt` against my solver: 20,000 of 20,000 equal.** Two solvers written
apart now agree on the whole sample, so both tables can be used as truth. Your power line was exactly right
(6,735 before, 0 after, nothing else moved).

**The sweep:** 16,800 searches, every one searched, every one found the mate; an answer later than the clock only
at clocks of 0 to 2 ms. For one and eight threads that settles it: there is no clock at which the engine moves
blind. What was good: you caught your own timing error (the cost of `ucinewgame` at 512 MB charged to the search),
re-measured, and said so; the stopwatch control made the millisecond figures readable; and you named the one
limit yourself (64 threads on a 4-core machine would have measured the machine, so you left it out and said that
it is the reviewer's case). That is the right call. The 35 ms of `ucinewgame` at 512 MB is noted.

From the other helpers: glmflash measured the bundle of old search changes at +18.9 Elo per node on the old tree
(3,000 games); the same four changes, written into today's engine, gave +21.2 +/- 7.1 on the PC at 2,000 nodes
(6,000 games). deepseek2 showed that a stored result does not hide a draw in the cases that reach the path, and
measured the power of each test with a build in which the guard was deleted.

How to compute an Elo figure and its error from your own per-game file (you will need it below): score
s = (wins + draws / 2) / games, Elo = -400 * log10(1 / s - 1). For the error take the PAIR scores (the two games
of one opening, colours reversed: 0, 0.5, 1, 1.5 or 2 points, divided by 2), their mean m and standard error e, and
convert m - 1.96 e and m + 1.96 e the same way. Pairs, not games, because the two games of an opening are not
independent.

## Job 9. BUDGET: 75 minutes by the clock (the matches run by themselves); at 65 minutes stop and write the report.

Rules: those of your first message. No engine source change. Folder `forge-combo29/tests_deepseek_job9/`, report
`forge-combo29/REPORT_deepseek_job9.md`, commit subject "deepseek job 9 report". After pushing, wait for file 10 with
the sleeping command of your first message; do not end your run.
Power lines for this job: control 2 is the planted difference for the match tool (it must show the 20,000-node
side ahead); for your own Elo arithmetic, recompute control 2 from your per-game file and get fastchess's number.

### The question
The engine has switches for search ideas that were written, checked for safety and then NEVER played: each is off
by default and nobody knows whether it helps. You measure 5 of them (two other helpers measure eleven more). The first two are ON in the settings the owner's PC
plays with, so for them the question is whether they pay for themselves: each
switch ON against OFF, the same engine on both sides, a fixed number of nodes per move and no clock, so your
machine's speed and load do not matter. What I do with it: the switches that show a gain here get a longer test on
the owner's PC with the net that plays there. A wrong "gain" costs an hour there; a missed one costs strength.

### What to fetch and build
Commit `6b98f217` (tip of `for-fable-and-opus/astra-0017-v3-path`), folder `forge-combo29`. Release build with CMake
and g++ (GCC 13 or newer, GCC's own C++ library); on a machine without AVX-512 or BMI2 add
`-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. Built-in net. Nothing of the build is committed.
Add `-DFORGE_MATE_ALPHA_GUARD=1` to the C++ flags: without it the option `MateAlphaGuard` does not exist (check that
`uci` lists it; the three known numbers must still hold, the guard is off by default).

### Step 0. The known numbers (raw output as a file; a fresh engine process for each group)
    no option set:   bench 11 -> nodes 312866    bench 13 -> nodes 862329    go perft 5 -> nodes 4865609
If one differs: stop and report that; nothing else counts.

### Step 1. Is each switch alive? (one fresh process per switch; report the two numbers)
    setoption name MateAlphaGuard value true:      bench 11 -> ?    bench 13 -> ?
    setoption name NonPawnCorrection value true:   bench 11 -> ?    bench 13 -> ?
    setoption name ContHist4PlyRead value true:    bench 11 -> ?    bench 13 -> ?
    setoption name QuietExtinction value true:     bench 11 -> ?    bench 13 -> ?
    setoption name DrawJitter value 2:             bench 11 -> ?    bench 13 -> ?
A switch whose two numbers equal 312866 and 862329 did not change the search in these positions: say so (it may
still act in rarer positions; play its match anyway, last).

### Step 2. The match program and its controls
- fastchess from its official repository (github.com/Disservin/fastchess), newest release tag, built from source.
  Openings: `UHO_Lichess_4852_v1.epd` from the official repository github.com/official-stockfish/books.
- Every match: both sides the SAME exe; `Threads 1`, `Hash 16`; fixed nodes, no clock. The form we use on the PC:

      fastchess -engine cmd=<exe> name=cand option.Threads=1 option.Hash=16 <option.NAME=VALUE> \
        -engine cmd=<exe> name=base option.Threads=1 option.Hash=16 \
        -each proto=uci nodes=20000 -openings file=UHO_Lichess_4852_v1.epd format=epd order=random \
        -srand <seed> -rounds <games/2> -games 2 -repeat -concurrency <your cores> -recover \
        -ratinginterval 100 -pgnout file=<file> min=true

  No adjudication. Report your machine's core count and the concurrency you used.
- Control 1 (the tool is fair): `base` against `base`, 600 games, seed 7401. Expected: an Elo difference whose
  error interval contains 0.
- Control 2 (the tool can see a difference): `nodes=20000` against `nodes=10000` (give `nodes` per engine instead
  of under `-each`), no options, 300 games, seed 7402. Expected: the 20,000 side clearly ahead.
- Control 3 (the option reaches the engine): for the first switch, show from a fastchess or engine log of a 2-game
  match that the engine received the `setoption` line.

### Step 3. The matches, in this order, as many as the time allows
    M1   option.MateAlphaGuard=true       against no options    1,500 games    seed 7403
    M2   option.NonPawnCorrection=true    against no options    1,500 games    seed 7404
    M3   option.ContHist4PlyRead=true     against no options    1,500 games    seed 7405
    M4   option.QuietExtinction=true      against no options    1,500 games    seed 7406
    M5   option.DrawJitter=2              against no options    1,500 games    seed 7407

Start a match, then wait for it with ONE sleeping shell command (no polling: a waiting agent costs the owner money
for nothing). For each match, from fastchess's own final output: games, wins, losses, draws, the pair counts
(pentanomial), Elo with its error, and the games lost on a crash, an illegal move or a disconnect (expected: 0).
Save the last 40 lines of each fastchess output as a file. Do not commit PGN files (too large); commit for each
match one text file with one line per game: round, which side had white, the opening's number or FEN, the result.
A match cut short by the time limit is reported with the games it has, marked INCOMPLETE.
With 1,500 games the error is about +/- 13 Elo: say "no difference shown" for anything inside it, never "no effect".

### The report, forge-combo29/REPORT_deepseek_job9.md
 1. First line, in plain words: which switch, if any, shows a gain or a loss outside its error.
 2. Step 0 numbers, expected against printed. 3. Step 1 table. 4. The three controls.
 5. One table of the matches: switch, games, W-L-D, pair counts, Elo +/- error, crashes.
 7. Which files of the repository you opened. 8. Start and end of each step from recorded stamps.
 9. What you did not do. 10. What you are not sure about. 11. A better way (may be empty).
12. Your model name and version as you know it.
Every "X is in file Y" in the report: open Y first.
