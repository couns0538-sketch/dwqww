# Fable to deepseek3, file 1 (2026-11-15): job 1

Step 0 of this job is the honesty check every helper passes first: three numbers that I know. Everything after it
counts only if they are right.

## Job 1. BUDGET: 75 minutes by the clock (the matches run by themselves); at 65 minutes stop and write the report.

### The question
The engine has switches for search ideas that were written, checked for safety and then NEVER played: each is off
by default and nobody knows whether it helps. You measure 5 of them (another helper measures the others): each
switch ON against OFF, the same engine on both sides, a fixed number of nodes per move and no clock, so your
machine's speed and load do not matter. What I do with it: the switches that show a gain here get a longer test on
the owner's PC with the net that plays there. A wrong "gain" costs an hour there; a missed one costs strength.

### What to fetch and build
Commit `6b98f217` (tip of `for-fable-and-opus/astra-0017-v3-path`), folder `forge-combo29`. Release build with CMake
and g++ (GCC 13 or newer, GCC's own C++ library); on a machine without AVX-512 or BMI2 add
`-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. Built-in net. Nothing of the build is committed.

### Step 0. The known numbers (raw output as a file; a fresh engine process for each group)
    no option set:   bench 11 -> nodes 312866    bench 13 -> nodes 862329    go perft 5 -> nodes 4865609
If one differs: stop and report that; nothing else counts.

### Step 1. Is each switch alive? (one fresh process per switch; report the two numbers)
    setoption name NullThreatVerify value true:   bench 11 -> ?    bench 13 -> ?
    setoption name NullSeeVeto value true:   bench 11 -> ?    bench 13 -> ?
    setoption name AspArmLate value true:   bench 11 -> ?    bench 13 -> ?
    setoption name EvalRule50Damp value true:   bench 11 -> ?    bench 13 -> ?
    setoption name DeadMaterial value true:   bench 11 -> ?    bench 13 -> ?
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
- Control 1 (the tool is fair): `base` against `base`, 600 games, seed 7301. Expected: an Elo difference whose
  error interval contains 0.
- Control 2 (the tool can see a difference): `nodes=20000` against `nodes=10000` (give `nodes` per engine instead
  of under `-each`), no options, 300 games, seed 7302. Expected: the 20,000 side clearly ahead.
- Control 3 (the option reaches the engine): for the first switch, show from a fastchess or engine log of a 2-game
  match that the engine received the `setoption` line.

### Step 3. The matches, in this order, as many as the time allows
    M1   option.NullThreatVerify=true    against no options    1,500 games    seed 7303
    M2   option.NullSeeVeto=true    against no options    1,500 games    seed 7304
    M3   option.AspArmLate=true    against no options    1,500 games    seed 7305
    M4   option.EvalRule50Damp=true    against no options    1,500 games    seed 7306
    M5   option.DeadMaterial=true    against no options    1,500 games    seed 7307

Start a match, then wait for it with ONE sleeping shell command (no polling: a waiting agent costs the owner money
for nothing). For each match, from fastchess's own final output: games, wins, losses, draws, the pair counts
(pentanomial), Elo with its error, and the games lost on a crash, an illegal move or a disconnect (expected: 0).
Save the last 40 lines of each fastchess output as a file. Do not commit PGN files (too large); commit for each
match one text file with one line per game: round, which side had white, the opening's number or FEN, the result.
A match cut short by the time limit is reported with the games it has, marked INCOMPLETE.
With 1,500 games the error is about +/- 13 Elo: say "no difference shown" for anything inside it, never "no effect".

### Part B. While the matches run: a third opinion on pawn endings (about 15 minutes of your own work)
Another helper built a table of king-and-pawn-against-king results that was wrong in places; Fable built a second
one. You build a third, independently (do not look at the other helper's branch): by retrograde analysis, the
result (W, D or L from the side to move's view) of every legal position with one pawn. Deliver:
 - the number of legal positions with the PAWN SIDE to move and how many of them are wins; the number with the
   OTHER side to move and how many of them are losses (count a position once per colour of the pawn, or say how
   you count);
 - `tests_deepseek3_job1/kpk_2000.txt`: 2,000 random legal positions (seed 20261115, either colour may have the pawn,
   either side to move), one per line: the FEN, a semicolon, W, D or L;
 - your verdict for these, with one line of reasoning each: `8/3k4/8/8/8/5p2/8/3K4 b - - 0 1`,
   `4k3/8/4K3/4P3/8/8/8/8 w - - 0 1`, `7k/8/7K/7P/8/8/8/8 w - - 0 1`, `8/8/8/8/8/4k3/4p3/4K3 b - - 0 1`.
Control for your own table: a player that always picks a move keeping the result must never change the result
class over 2,000 random positions; a random mover must change it often. Report both numbers.

### The report, forge-combo29/REPORT_deepseek3_job1.md
 1. First line, in plain words: which switch, if any, shows a gain or a loss outside its error.
 2. Step 0 numbers, expected against printed. 3. Step 1 table. 4. The three controls.
 5. One table of the matches: switch, games, W-L-D, pair counts, Elo +/- error, crashes.
 6. Part B, or "not done" (if your job has a part B).
 7. Which files of the repository you opened. 8. Start and end of each step from recorded stamps.
 9. What you did not do. 10. What you are not sure about. 11. A better way (may be empty).
12. Your model name and version as you know it.
Every "X is in file Y" in the report: open Y first.
