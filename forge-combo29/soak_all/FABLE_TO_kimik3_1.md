# Fable to kimik3, file 1 (2026-11-15): job 1

Step 0 of this job is the honesty check every helper passes first: numbers that I know. Everything after it
counts only if they are right.

## Job 1. BUDGET: 60 minutes; at 50 minutes stop and write the report with what you have.

### The task in one sentence
Make one piece of a chess engine's search FASTER without changing a single result of it, and prove both.

### Why
Four search changes were ported into today's engine on the owner's PC as switches. Together they are worth +17
Elo at a fixed number of nodes (2,000 games), but they cost speed: with all four on the engine searches about
7.6 % fewer nodes a second, and one of them alone, `HistRework`, about 10 %. On the clock that eats about half
of the gain. The same code exists in public for an older tree of the engine, and that is where you work. What
you find is ported to today's engine by me, after I have read every line, so the patch must be small and plain.

### What to fetch and build
- Commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (fetch it by its id with `--depth 1`): the engine tree, source
  at the ROOT (`src`, `include`, `CMakeLists.txt`).
- From branch `opus-r13-p1-nearmiss-ports` the file `opus_r13/p1/b1/b1_port.patch`.
Export the tree into a folder outside your git work tree, apply the patch (`patch -p1`, no fuzz, no rejects): that
is the BASELINE. Your work is a second copy with your change on top. Release build with CMake and g++ (point CMake
at g++ if the machine's default compiler is another one), `-DCMAKE_BUILD_TYPE=Release`, with
`-DFORGE_NNUE_HIDDEN=256` among the C++ definitions (this tree's static_asserts ask for it). Use the same flags
for both copies and write them down. Nothing of either copy is committed; your change is committed as ONE text
file, a unified diff against the baseline: `tests_kimik3_job1/speed.patch.txt`.

### Step 0. The known numbers, on the BASELINE (a fresh engine process per line; raw output as files)
    no option set:                           bench 11 -> 312866   bench 13 -> 862329   go perft 5 -> 4865609
    setoption name BundlePreset value B1:    bench 11 -> 280182   bench 13 -> 758456   bench 16 -> 3357587
    setoption name TtPruneV2 value true:     bench 11 -> 309157   bench 13 -> 736967
If one differs: stop and report that.

### The code
`BundlePreset B1` = `CorrHistPlus 1`, `HistRework 2`, `CuckooRep true`, `TtPruneV2 true`. The expensive one is
`HistRework` (`include/forge/hist_rework.hpp` and its hooks in `src/search.cpp`): a second history table for quiet
moves, indexed by whether the move's from-square and to-square are attacked by a LESSER enemy piece. For that it
builds, at every node before the move loop, a set of attack maps (`lesser_threats`: pawn attacks, plus knight and
bishop attacks, plus rook attacks, with the current occupancy). One thing I can already tell you: the maps are
built at every node whether or not a quiet move is ever scored or updated there, and many nodes end on the hash
move or on a capture. Start there, then look for more (the maps themselves, the table lookups, the update, and
the other three switches' paths).

### The oracle (what "no result changed" means; all of it must hold for your patched copy against the baseline)
 O1. Node counts of `bench 11`, `bench 13`, `bench 16` and `bench 20` are IDENTICAL for each of: no option;
     `HistRework 2` alone; `BundlePreset B1`; `HistRework 1`; `HistRework 3`. (Record the baseline's numbers first;
     for B1 at depth 20 the known value is 11208630.) `go perft 5` = 4865609.
 O2. 2,000 positions (from the official opening file `UHO_Lichess_4852_v1.epd` of
     github.com/official-stockfish/books, the first 2,000 lines, or random legal positions with a seed if you
     cannot fetch it; say which): `ucinewgame`, `position fen ...`, `go depth 9`, with `BundlePreset B1`: best
     move, score and node count of every position identical between baseline and patched copy. Then the same
     2,000 in ONE process without `ucinewgame` between them (the history tables carry over, so an update that
     differs anywhere shows up later): identical again.
 O3. Power of the oracle: plant a small real fault in a third copy (for example: the map of the wrong side, or one
     update skipped) and show that O1 or O2 reports a difference. Without this line a clean O1 and O2 count for
     nothing.
 O4. AddressSanitizer + UBSan build of the patched copy: `bench 13` with B1 and 200 of the O2 positions, nothing on
     stderr; first a tiny planted-fault program to show the build reports faults.

### The measurement (what "faster" means)
 M1. Noise first: the baseline against ITSELF, `bench 16` with `BundlePreset B1`, 20 interleaved pairs (A B, B A, ...),
     each a fresh process, on one pinned core if your machine allows it: the median, smallest and largest ratio of
     nodes per second. That spread is what any gain must clear.
 M2. Patched against baseline, the same way, 20 pairs each for: `BundlePreset B1`; `HistRework 2` alone; no option
     (the switched-off path must not get slower). Median, smallest and largest ratio.
 M3. Baseline with no option against baseline with `HistRework 2` (how much the switch costs before your change)
     and the same for your patched copy (how much it costs after). Those two numbers are the result of the job.
 A gain smaller than the spread of M1 is reported as "not shown".

### Rules for the patch
Bit-exact or nothing: if a faster variant changes any node count, it is out, however good it looks; describe it in
the report instead ("would be faster but changes results because ..."). No reformatting, no renaming, no drive-by
changes. Each idea as its own hunk group with one comment line saying what it does. If you find several
independent ideas, also commit them as separate patch files (`speed_1_lazy_maps.patch.txt`, ...) with their own
M2 numbers, so that each can be taken alone.

### The report, forge-combo29/REPORT_kimik3_job1.md
 1. First line, in plain words: by how much the cost of `HistRework 2` fell (M3 before and after), and whether
    every result stayed identical.
 2. Step 0, expected against printed.
 3. The ideas, one paragraph each: what, where (file and lines), why it cannot change a result, its own speed number.
 4. The oracle: O1 table, O2 counts, O3 (the planted fault and what reported it), O4.
 5. M1, M2, M3 with every ratio.
 6. Ideas that were NOT bit-exact, and ideas you did not have time for.
 7. Which files of the repository you opened. 8. Start and end of each step from recorded stamps.
 9. What you did not do. 10. What you are not sure about. 11. A better way (may be empty).
12. Your model name and version as you know it.
