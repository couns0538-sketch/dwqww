# Fable to glmflash3, file 1 (2026-11-15): job 1

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
Four bundles of search changes were tried on an older version of this engine. Two failed their strength test on
the clock (B2, B3), two passed (B1, B4). All four exist as one-word presets in ONE old tree. Measure them per
node on one scale, and then test the part that the failed bundles had in common (`LmrTableV2`) ON TOP of the
bundle that passed. If a part that lost in one company wins in another, we want to see it.

### What to fetch and build (nothing of it is committed)
Commit `b7c177222038e9332965a95ec53ea3b94e90dbc9` (it is on branch `opus-r7-nps`; fetch the commit by its id with
`--depth 1`). The engine source is at the ROOT of that commit (`src`, `include`, `CMakeLists.txt`). Release build
with CMake and g++ (GCC 13 or newer; point CMake at g++ if the machine's default compiler is another one). An
older tree of this family needed `-DFORGE_NNUE_HIDDEN=256` among the C++ definitions; if the static_asserts of
this one ask for it too, add it and say so. The file `BUNDLES.md` at the root describes the presets; it is data.

### Step 0. The known numbers (a fresh engine process per line; raw output as files)
    no option set:                              bench 11 -> 312866    bench 13 -> 862329    go perft 5 -> 4865609
    setoption name BundlePreset value B1:       bench 11 -> 280182    bench 13 -> 758456
    setoption name BundlePreset value B2:       bench 11 -> 255626    bench 13 -> 564279
    setoption name BundlePreset value B3:       bench 11 -> 211646    bench 13 -> 463170
    setoption name BundlePreset value B4:       bench 11 -> 276131    bench 13 -> 985600
    setoption name CorrHistV2 value true:       bench 11 -> 282082    bench 13 -> 1001737
    setoption name LmrTableV2 value true:       bench 11 -> 245666    bench 13 -> 494753
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
    M1   cand: BundlePreset=B4                     base: no options          3,000 games   seed 7501
    M2   cand: BundlePreset=B4, then LmrTableV2=true   base: BundlePreset=B4     2,000 games   seed 7502
         (the failed bundles' common part on top of the bundle that passed; BOTH sides carry B4)
    M3   cand: BundlePreset=B2                     base: no options          2,000 games   seed 7503
    M4   cand: BundlePreset=B3                     base: no options          2,000 games   seed 7504
    M5   cand: LmrTableV2=true                     base: no options          1,500 games   seed 7505
    M6   cand: BundlePreset=B4                     base: BundlePreset=B1     2,000 games   seed 7506
For M2 check with a bench 13 that `BundlePreset B4` followed by `LmrTableV2 true` gives a number different from
B4's 985600 (the later option must override the preset, as BUNDLES.md says); report the number.

Start a match, then wait for it with ONE sleeping shell command (no polling: a waiting agent costs the owner money
for nothing). Give each match its own time limit so that the last one is the one that is cut, and end a cut match
with fastchess's interrupt so that its games count (marked INCOMPLETE). No adjudication. Do not commit PGN files;
commit for each match one text file with one line per game: round|white|black|result|opening FEN, and the last
40 lines of fastchess's output. Games lost on a crash, an illegal move or a disconnect: count them (expected 0).

How to compute an Elo figure and its interval from your own per-game file: score s = (wins + draws / 2) / games,
Elo = -400 * log10(1 / s - 1). For the interval take the PAIR scores (the two games of one opening with colours
reversed: 0, 0.5, 1, 1.5 or 2 points, divided by 2), their mean m and standard error e, and convert m - 1.96 e and
m + 1.96 e the same way. Report that next to fastchess's own numbers.

### The report, forge-combo29/REPORT_glmflash3_job1.md
 1. First line, in plain words: which bundles are stronger per node and by how much, and whether
    `LmrTableV2` helps or hurts when it is added to B4.
 2. Step 0, expected against printed. 3. The three controls.
 4. One table of the matches: options on each side, seed, games, W-L-D, pair counts, fastchess's Elo +/- error,
    your Elo with the 95 % pair interval, crashes.
 5. Which files of the repository you opened. 6. Start and end of each step from recorded stamps.
 7. What you did not do. 8. What you are not sure about. 9. A better way (may be empty).
10. Your model name and version as you know it.
Every "X is in file Y" in the report: open Y first.
