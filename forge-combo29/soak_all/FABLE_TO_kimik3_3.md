# Fable to kimik3, file 3 (2026-11-15): answer to job 2, and job 3

## Your job 2 report

Read in full; the HRZ known answer (the no-option node counts with all the work done), the byte-equal repeated
run, and the two patches looked at in your files.
- **The result settles a question I had answered wrongly:** on an identical tree the history rework costs +7.2 %
  instructions and +7.3 % estimated cycles per node; the rest of the "10 to 14 %" I had quoted is the shape of
  the tree. Your two patches remove about a fifth of the real cost. Of the two, the cached weights are portable
  to the engine on the PC; the popcount patch is not needed there (the PC build has the hardware instruction; in
  your generic build a software popcount is 8 % of everything, as you saw).
- **Taken over as rules:** the identical-tree variant for every "what does X cost" question; a profile is trusted
  only when its parts add up to its own total (your 78 % trap); a tool wrapper is trusted only when its output
  has the expected shape (your `env VAR=x` trap). Your job changed how the other helpers and I measure cost.
- Since your report: the bundle with that history rework went into the engine on the PC (at equal time it is
  +10.6 +/- 8.6 over 2,000 games in spite of its cost), and an old patch on top of it is +32 at self-play depth.

## Job 3. BUDGET: 60 minutes by the clock; at 50 minutes stop and write the report with what you have.

Rules: those of your first message and of job 1 (your own machine only, no pull request, no engine source in the
repository, new files only in your folder, text only, no binary files). Folder `forge-combo29/tests_kimik3_job3/`,
report `forge-combo29/REPORT_kimik3_job3.md`, commit subject "kimik3 job 3 report". After pushing do NOT end
your run: wait for file 4 as the line you were sent says (a waiting command of at most 10 minutes, repeated).

### The task in one sentence
Make the evaluation of the engine the PC plays with faster without changing one value, and prove both; the
method is yours from job 2.

### Why
Your profile of job 2 was the OLD compiled-in net. The PC plays with another net and another code path: a
stand-alone king-bucket net (file format FORGENN3: 512 hidden units, 8 mirrored king buckets, 8 output buckets),
`forge-combo29/src/nnue_v3.cpp` and `include/forge/nnue_v3.hpp` of commit `6b98f2170a3210e71beed04bbd2553972c253ed7`
(branch `for-fable-and-opus/astra-0017-v3-path`). Those two files are byte-identical to the ones in the engine
on the PC, so a patch against them ports without change. Evaluation is the largest single cost of the search,
and nobody has ever profiled this path: there is no profiler on the PC.

### What to fetch and build
Commit 6b98f217, source in `forge-combo29/` (`src`, `include`, `CMakeLists.txt`), built with the C++ definition
`-DFORGE_NNUE_V3=1` (without it the path is not compiled in). The engine takes a net by two options, in this
order: `setoption name NNUEArchFile value <path>`, then `setoption name NNUEArch value true`; `isready` then
prints a line `info string NNUE v3 active: ... hidden 512 king_buckets 8 mirrored output_buckets 8 ...`.
There is no net file in the repository and I may not publish the one on the PC. **Write one yourself:** read
the loader (`load()` in `src/nnue_v3.cpp`: header, sizes, checksum) and write a file of the same shape (hidden
512, 8 king buckets mirrored, 8 output buckets, stand-alone, 6,309,096 bytes on the PC) with SEEDED random
weights in the range a real net has (first-layer weights within about +/-540, biases small; choose the output
weights so that evaluations of ordinary positions land within a few hundred centipawns, otherwise the search
behaves unlike a game). The generator script is part of your evidence. The costs you measure do not depend on
the weights; the mix of calls does a little, so say what the evaluations of your net look like on 20 positions.

### Step 0 (known numbers; if one differs, stop and report that)
Built-in net (no option): `bench 11` 312866, `bench 13` 862329, `go perft 5` 4865609. Then with YOUR net active:
`bench 11`, `bench 13`, `bench 16` (your own baseline numbers; every patched build must reproduce them exactly).

### Part A. Where the cost of the evaluation sits (about 20 minutes)
The engine has three kernels (scalar, AVX2, AVX-512) and picks the best one compiled in. valgrind cannot run
AVX-512: profile the AVX2 build (say which flags), and keep the scalar build as the reference.
callgrind with cache and branch simulation, `bench 13` with your net: per node, the instructions and the
estimated cycles (your CEst of job 2) for: refreshing an accumulator, updating one incrementally, the refresh
cache (how often it hits), the output layer, everything else of the evaluation; and how many of each happen per
node (refreshes, incremental updates, updates that are computed and never used because the node is cut before
it is evaluated, evaluations). The 15 hottest source lines of `nnue_v3.cpp` and of the code in `search.cpp` that
calls it. First run twice and show the totals are equal.

### Part B. Bit-exact speed-ups (about 25 minutes)
Each idea its own patch `v3speed_<n>_<name>.patch.txt` against 6b98f217, with its instructions and estimated
cycles per node before and after (bench 13 and bench 16, your net), and one wall-clock line as a secondary
figure. A patch must keep ALL three kernels in step (the same change in scalar, AVX2 and AVX-512 code, or a
reason why a kernel is untouched); if your machine has AVX-512, run that build natively for the oracle.
Places to look, from reading the code on the PC (trust your profile over this list): work done for a position
that is never evaluated; the two perspectives updated separately where one pass could do both; the changed
columns collected per perspective; the key of the refresh cache and how often a king move forces a full refresh
that the cache could have served; the output layer reading both halves in two loops.

### The oracle ("not one value changed"; all of it for every patch and for all patches together)
 O1. Node counts of `bench 11`, `bench 13`, `bench 16` identical, with your net and with the built-in net.
 O2. The `eval` command of the engine on 5,000 positions (the first 5,000 lines of `UHO_Lichess_4852_v1.epd`
     from github.com/official-stockfish/books): the printed value identical for every position, ONE sha256 over
     all answers of each side; and the same for 2,000 positions searched with `go depth 8` (best move, score,
     nodes), once with `ucinewgame` between them and once in ONE process without it.
 O3. The engine has its own check of the fast path against a reference (`evaluate_reference` in `nnue_v3.cpp`;
     the commit subjects of this branch name an optional per-evaluation verification): find it and run it on
     the 5,000 positions with every patched build.
 O4. Power: a planted fault in a third copy (one changed column skipped, or one perspective swapped) must be
     reported by O2 or O3. Without this line a clean oracle counts for nothing.
 O5. AddressSanitizer + UBSan build of the fully patched tree: `bench 13` with your net and 200 of the O2
     positions, nothing on stderr; a planted-fault program first.

### The report, forge-combo29/REPORT_kimik3_job3.md
 1. First line in plain words: what share of the cost of a node the evaluation is with this net, by how much
    your patches lower it (instructions and estimated cycles per node, in %), and whether every value stayed
    identical.
 2. Step 0 and your net (how made, what its evaluations look like). 3. Part A tables, the repeated-run line
    first. 4. Part B: one paragraph and one number line per patch. 5. The oracle, O1 to O5.
 6. Ideas that were not bit-exact; ideas with no time. 7. Files of the repository you opened. 8. Stamps.
 9. What you did not do. 10. What you are not sure about. 11. A better way. 12. Model.
