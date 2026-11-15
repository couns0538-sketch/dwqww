# Fable to glmflash4, file 1 (2026-11-15): job 1

Step 0 of this job is the honesty check every helper passes first: numbers that I know. Everything after it
counts only if they are right.

What the others found, so that you do not repeat it: one helper's matches ran with another table size than the
job said, because the match form did not carry the option: every option a test depends on stands in the command
line, and you prove from an engine input log that the engine received it. One helper reported an error figure
that was one standard error and read it as a second "model": report the 95 % interval. One helper showed that a
prescribed test could not fail at all: every test carries a line on its power against a planted fault (for a
match that is control 2 below).
**The owner's rule for all of us:** one bad result can turn into a big gain when it is bundled with the right
things. So no single result closes an idea, and this job tests parts TOGETHER as well as alone.

## Job 1. BUDGET: 80 minutes by the clock (the matches run by themselves); at 70 minutes stop and write the report.


### The question
Old patches with search changes exist for an older version of this engine. Another helper measures two of them
as whole patches. You measure a third one and take two of them APART: which single part carries a patch, and
do parts that show nothing alone show something together?

### What to fetch and build (nothing of it is committed)
Commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (fetch it by its id with `--depth 1`): the engine tree, source
at the ROOT (`src`, `include`, `CMakeLists.txt`). From branch `opus-r13-p1-nearmiss-ports` the two files
`opus_r13/p1/bnd68/bnd68_port.patch` and `opus_r13/p1/packc28/packc28_port.patch`. Each patch goes onto its OWN
clean copy of the tree, outside your git work tree (`patch -p1`, no fuzz, no rejects; say what `patch` printed):
two builds. Release build with CMake and g++ (point CMake at g++ if the default compiler is another one), with
`-DFORGE_NNUE_HIDDEN=256` among the C++ definitions (this tree's static_asserts ask for it).

### Step 0. The known numbers (a fresh engine process per line; raw output as files)
    each build, no option set:      bench 11 -> 312866    bench 13 -> 862329    go perft 5 -> 4865609
    build bnd68 with  NonPawnCorr 1, PawnHist 1, NonPawnCorrWeight 50, ContHist4Pct 45, EvalOnlyStore 1,
                      EvalOnlyStoreMinDepth 2:        bench 11 -> 365135    bench 13 -> 776194
    build packc28 with AspFailHighReduce 1, AspFailHighMaxReduce 3, EvalSwingMult 24, EvalSwingMax 200:
                                                      bench 11 -> 277906    bench 13 -> 690187
Before each match of step 2: one bench 13 with exactly that match's options (report it; "equal to 862329" is a
result too and means the options did not act in those positions).
If a number differs: stop, put the raw output into the report, and do not go on with that build.

### Step 1. The match program and its controls
fastchess from its official repository (github.com/Disservin/fastchess), newest release tag, built from source.
Openings: `UHO_Lichess_4852_v1.epd` from the official repository github.com/official-stockfish/books.
Every match: the SAME exe on both sides, fixed nodes, no clock, this form:

    fastchess -engine cmd=<exe> name=cand option.Threads=1 option.Hash=16 <option.NAME=VALUE ...> \
      -engine cmd=<exe> name=base option.Threads=1 option.Hash=16 <option.NAME=VALUE ...> \
      -each proto=uci nodes=20000 -openings file=UHO_Lichess_4852_v1.epd format=epd order=random \
      -srand <seed> -rounds <games/2> -games 2 -repeat -concurrency <your cores> -recover \
      -ratinginterval 100 -pgnout file=<file> min=true

- Control 1 (determinism): `base` against `base`, 100 games. Expected: every pair 1-1.
- Control 2 (the tool can see a difference; this job's power line): 20,000 nodes against 10,000 nodes (give
  `nodes` per engine instead of under `-each`), no options, 300 games. Expected: the 20,000 side clearly ahead.
- Control 3: from an engine input log of a 2-game match, the `setoption` lines the `cand` side received,
  `Hash 16` among them.

### Step 2. The matches, in this order, as many as the time allows
    build bnd68 (base: no options in every match):
    M1   NonPawnCorr=1 NonPawnCorrWeight=50                                  1,500 games   seed 7601
    M2   PawnHist=1                                                          1,500 games   seed 7602
    M3   ContHist4Pct=45                                                     1,500 games   seed 7603
    M4   EvalOnlyStore=1 EvalOnlyStoreMinDepth=2                             1,500 games   seed 7604
    M5   PawnHist=1 ContHist4Pct=45 EvalOnlyStore=1 EvalOnlyStoreMinDepth=2  2,000 games   seed 7605
         (the patch without its correction part)
    build packc28 (base: no options):
    M6   AspFailHighReduce=1 AspFailHighMaxReduce=3                          1,500 games   seed 7606
    M7   EvalSwingMult=24 EvalSwingMax=200                                   1,500 games   seed 7607

Start a match, then wait for it with ONE sleeping shell command (no polling: a waiting agent costs the owner money
for nothing). Give each match its own time limit so that the last one is the one that is cut, and end a cut match
with fastchess's interrupt so that its games count (marked INCOMPLETE). No adjudication. Do not commit PGN files;
commit for each match one text file with one line per game: round|white|black|result|opening FEN, and the last
40 lines of fastchess's output. Games lost on a crash, an illegal move or a disconnect: count them (expected 0).

How to compute an Elo figure and its interval from your own per-game file: score s = (wins + draws / 2) / games,
Elo = -400 * log10(1 / s - 1). For the interval take the PAIR scores (the two games of one opening with colours
reversed: 0, 0.5, 1, 1.5 or 2 points, divided by 2), their mean m and standard error e, and convert m - 1.96 e and
m + 1.96 e the same way. Report that next to fastchess's own numbers.

### The report, forge-combo29/REPORT_glmflash4_job1.md
 1. First line, in plain words: which single part shows the most, and whether the bnd68 patch
    without its correction part is still a gain.
 2. Step 0, expected against printed. 3. The three controls.
 4. One table of the matches: options on each side, seed, games, W-L-D, pair counts, fastchess's Elo +/- error,
    your Elo with the 95 % pair interval, crashes.
 5. Which files of the repository you opened. 6. Start and end of each step from recorded stamps.
 7. What you did not do. 8. What you are not sure about. 9. A better way (may be empty).
10. Your model name and version as you know it.
Every "X is in file Y" in the report: open Y first.
