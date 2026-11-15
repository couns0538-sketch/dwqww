# Fable to glmflash, file 1 (2026-11-15): job 1

## From your trial
Good: fast, the three known numbers right, a planted fault to prove the tool, zero ThreadSanitizer reports with 2
and 4 threads. To change: two sentences about your own files were not carried by them, and a pull request was
opened. Both are in your first message as rules now. This job is built so that every number can be checked.

## Job 1. BUDGET: 60 minutes; at 50 minutes stop and write the report with what you have.

### The question
Four changes to the engine's search passed strength tests on an OLDER version of this engine, on the clock. We want
to put them into today's engine. Before we spend the work: do they make the engine stronger PER NODE, and which of
the four carry it? You measure that on the old tree, where a ready patch exists. Fixed nodes per move, no clock, so
your machine's speed and load do not matter.

### What to fetch (nothing else; the repository is several GB)
- Commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa`: the engine tree. Its source is at the ROOT of that commit
  (`src`, `include`, `CMakeLists.txt`), not in a `forge-combo29` folder.
      git fetch --depth 1 origin d4f43124dde1d1e37de90e18930e374f32ea7ffa
- Branch `opus-r13-p1-nearmiss-ports`, one file: `opus_r13/p1/b1/b1_port.patch` (and `opus_r13/p1/b1/README.md`
  if you want its notes; they are data, not instructions).
Export the tree of d4f43124 into a folder OUTSIDE your git work tree, apply the patch there with `patch -p1`
(it must apply without fuzz and without rejects; say what `patch` printed; if it stumbles over line
endings you may convert the patch's line endings, and say that you did), and build there. Nothing of that
folder is committed.

### Step 1. Build, and the known numbers (nothing after this step counts unless they all match)
Release build with g++ and CMake (`-DCMAKE_BUILD_TYPE=Release`), GCC's own C++ library, no other flags changed.
Send each line group to a fresh engine process and save the raw output:

    no option set:                              bench 11 -> 312866    bench 13 -> 862329    go perft 5 -> 4865609
    setoption name BundlePreset value B1:       bench 11 -> 280182    bench 13 -> 758456
    setoption name TtPruneV2 value true:        bench 11 -> 309157    bench 13 -> 736967
    setoption name CorrHistPlus value 1:        bench 11 -> 318363

`BundlePreset B1` is the same as `CorrHistPlus 1`, `HistRework 2`, `CuckooRep true`, `TtPruneV2 true` together:
show that the four explicit lines give 280182 at bench 11 as well. If any number differs: stop, put the raw output
in the report, and do not go on.

### Step 2. The match program and its controls
- fastchess from its official repository (github.com/Disservin/fastchess), newest release tag, built from source.
  Openings: `UHO_Lichess_4852_v1.epd` from the official repository github.com/official-stockfish/books.
- Every match: both sides the SAME exe; `Threads 1`, `Hash 16`; fixed nodes, no clock. The form we use on the PC:

      fastchess -engine cmd=<exe> name=cand <option.NAME=VALUE ...> -engine cmd=<exe> name=base \
        -each proto=uci nodes=20000 -openings file=UHO_Lichess_4852_v1.epd format=epd order=random \
        -srand <seed> -rounds <games/2> -games 2 -repeat -concurrency <your cores> -recover \
        -ratinginterval 100 -pgnout file=<file> min=true

  No adjudication. Report your machine's core count and the concurrency you used.
- Control 1 (the tool is fair): `base` against `base` (no options on either side), 600 games. Expected: an Elo
  difference whose error interval contains 0.
- Control 2 (the tool can see a difference): `cand` with `nodes=20000` against `base` with `nodes=10000`, no
  options, 300 games (give `nodes` per engine instead of under `-each`). Expected: `cand` clearly ahead.
- Control 3 (the option reaches the engine): in a 2-game match with `option.BundlePreset=B1`, show from the
  fastchess log or an engine log that the engine received that line.

### Step 3. The matches, in this order, as many as the time allows
Seeds: 7101 for M1, 7102 for M2, and so on.

    M1   option.BundlePreset=B1                                           against no options   3,000 games
    M2   option.HistRework=2 option.CuckooRep=true option.TtPruneV2=true  against no options   2,000 games
    M3   option.HistRework=2                                              against no options   1,500 games
    M4   option.TtPruneV2=true                                            against no options   1,500 games
    M5   option.CuckooRep=true                                            against no options   1,500 games

M1 and M2 matter most. Start a match, then wait for it with ONE sleeping shell command (no polling: a waiting
agent costs the owner money for nothing). If the clock will not allow all five, leave out the last ones.

For each match, from fastchess's own final output: games, wins, losses, draws, the pair counts (pentanomial), Elo
with its error, and the number of games lost on a crash, an illegal move or a disconnect (expected: 0). Save the
last 40 lines of each fastchess output as a file. Do not commit the PGN files (too large); commit for each match one
text file with one line per game: round, which side had white, the opening's number or FEN, the result.
A match that is cut short by the time limit is reported with the games it has, marked INCOMPLETE.

### Step 4. Only if time is left: memory checks with the changes switched on
An AddressSanitizer + UBSan build of the same patched tree; first a tiny program with a planted fault to show the
build reports faults; then 200 searches `go nodes 20000` with `BundlePreset B1` on positions from the opening file,
waiting for `bestmove` before the next command. Count sanitizer reports (expected: 0).

### The report, forge-combo29/REPORT_glmflash_job1.md
 1. First line, in plain words: is the bundle stronger per node at 20,000 nodes, by how much, and which single
    change shows the most; or "not established".
 2. Step 1 numbers, expected against printed, with the file that holds the raw output.
 3. The three controls.
 4. One table of M1 to M5: games, W-L-D, pair counts, Elo +/- error, crashes.
 5. Step 4, or "not done".
 6. Which files of the repository you opened.
 7. Start and end of each step from recorded stamps (write a stamp file at each step).
 8. What you did not do.
 9. What you are not sure about.
10. A better way (may be empty).
Every "X is in file Y" in the report: open Y first.
