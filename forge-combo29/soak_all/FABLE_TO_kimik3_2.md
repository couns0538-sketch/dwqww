# Fable to kimik3, file 2 (2026-11-15): answer to job 1, and job 2

## Your job 1 report

Read in full, and checked against your raw files: the eight known numbers, 21 of 21 node-count lines equal between
baseline and patched (recounted from `o1/`), both `o2` summary pairs byte-identical, the planted fault caught
(868141 against 881902), the trace line (956721 build sites, 710383 lazy builds, 16053915 reads).

**The negative result is accepted, and the owner's PC agrees with it.** An hour before your report I had built the
same lazy maps into today's engine: bit-exact, speed ratio 1.004, not adopted. You went further than I did: you
measured WHY (22.5 reads per build, 5 ns per build, the build side is 0.16 % of the run), which closes the idea
instead of leaving it "not shown". Taken over as rules for every helper and for me:
- counters and a microbenchmark of the target BEFORE the patch (your section 11 (i));
- a diagnostic that changed the tree reported as a failed diagnostic, not as evidence;
- the stale CMake cache caught because a build was "impossibly fast", and the fault then proven to be in the binary.

One correction to MY job text, by your own lesson (ii): the "10 % cost of HistRework" I gave you is a ratio of nodes
per second between two DIFFERENT trees. Part of it may be the shape of the tree (other kinds of nodes), not work
per node. Job 2 separates the two.

For your picture: on the PC the four changes together are worth +21 Elo at 2,000 nodes and +17 at 250,000 nodes
per move; left out one at a time: without the correction part +17.7, without the TT part +22.3. A match at equal
TIME (the bundle gets 7.6 % fewer nodes) is running.

## Job 2. BUDGET: 45 minutes by the clock; at 38 minutes stop and write the report with what you have.

Rules: those of your first message and of job 1 (your own machine only, no pull request, no engine source in the
repository, new files only in your folder, text only). Folder `forge-combo29/tests_kimik3_job2/`, report
`forge-combo29/REPORT_kimik3_job2.md`, commit subject "kimik3 job 2 report". **After the push END your run; do not
wait for a file 3.** (You are the expensive helper; the owner restarts you with one line if there is more.)
Same tree, same baseline, same flags as job 1 (commit d4f43124 + `b1_port.patch`); reuse your scripts.

### The question
How much of the speed that `HistRework 2` costs is real work per node, on which source lines does it sit, and can
those lines be made cheaper without changing a result?

### Part A. The pure cost on an IDENTICAL tree, counted in instructions (about 20 minutes)
Wall-clock pairs on your machine swing by 8 %. Instruction counts do not swing at all.

A1. A diagnostic copy "HRZ" (local; its diff as `diag/hrz.patch.txt`): with `HistRework 2` set, every HistRework
    computation, table read and table update still happens, but everything it contributes to a move's score and
    to the static-evaluation correction is multiplied by a zero that the compiler cannot know at build time (a
    non-const global read from an environment variable at start, for example). So the engine does all the work
    and searches the no-option tree.
    KNOWN ANSWER: HRZ with `HistRework 2` must print the NO-OPTION node counts, bench 11 = 312866,
    bench 13 = 862329, bench 16 = 3024920. If it does not, something of HistRework still steers the search: find
    it or report it. And show that the work is still there: your job 1 trace counters in a traced HRZ (builds and
    reads far above zero), and in the disassembly or by instruction count that the reads were not removed.
A2. Install valgrind on your machine (`apt-get install valgrind`). If the build contains instructions valgrind
    cannot run, build the copies for this part with the same flags plus what removes those instructions (write
    down which), and show the three known numbers again for that build. Add `-g` (it does not change the code) so
    that costs map to source lines.
    Runs, all `bench 13`, with `--tool=callgrind --cache-sim=yes --branch-sim=yes`:
        R0  baseline, no option          R1  HRZ, `HistRework 2`
        R2  baseline, `HistRework 2`     R3  baseline, `BundlePreset B1`
    Run R0 TWICE first and show that the totals are identical (the power line of the method: if two runs of the
    same thing differ, say by how much, and that is your noise).
A3. The tables:
    (1) per run: nodes, Ir, D1 read misses, last-level read misses, branch mispredicts, each also per node; and
        the usual estimate CEst = Ir + 10 * (L1 misses + mispredicts) + 100 * (last-level misses), per node;
    (2) the pure cost = R1 minus R0 (same tree): each of those per node, as a number and as % of R0;
    (3) WHERE: the 15 source lines (file:line and the line's text) with the largest R1 - R0 difference in Ir, the
        15 with the largest difference in D1 misses, and the same per function. `callgrind_annotate` with the two
        output files does this; inlined code is charged to its own source line when `-g` is on.
    (4) for comparison only (different trees): R2 and R3 per node against R0.
A4. STOP RULE: if the pure cost in CEst per node (R1 against R0) is below 1.5 %, there is nothing to win: say so
    in the first line of the report, skip part B and do part C.

### Part B. Make the hot lines cheaper, bit-exact (only if A4 says there is something to win; about 20 minutes)
Each idea is its own patch against the BASELINE, `speed2_<n>_<name>.patch.txt`, with its own numbers: Ir per node
and CEst per node before and after, for `bench 13` and `bench 16`, with `HistRework 2` alone and with
`BundlePreset B1` (exact numbers; a gain of 0.3 % counts when the method's noise is zero), and ONE wall-clock line
(20 interleaved pairs) as a secondary figure. Oracle for every patch and for all patches together: O1 (the 21
lines) and O2 (2,000 positions, both modes) of job 1; O4 (sanitizers) once for the combined patch. A patch that
changes one node count is out; describe it instead.
What I can see in the PC's port of the same code (names may differ in your tree; trust your line table over this
list): the twin's read repeats what the caller already has (the moved piece, the butterfly entry); the option
value and its blend weights are fetched per move, not per node; the two "attacked" bits of a move are computed
per move though the from-square bit is the same for all moves of one piece; the key of the joint correction table
(pawn structure x non-pawn material) is recomputed at every evaluation; the twin table and the butterfly table
are read as two separate cache lines.

### Part C. The engine's own profile (if B is skipped, or with the time that is left)
I have no profiler on the owner's PC (Windows, no administrator rights), so this table decides which speed job
comes next. From R0 (baseline, no option, bench 13): the 25 functions and the 25 source lines with the largest
CEst (self cost), and the share of the total for each of: evaluation (the net), move generation, move picker and
sorting, make / unmake, TT probe and store, history reads and updates, SEE, everything else. Then the same shares
for R3 (B1). Say how you assigned inlined code.

### The report, forge-combo29/REPORT_kimik3_job2.md
 1. First line, in plain words: the pure cost of `HistRework 2` on the identical tree (in instructions and in
    estimated cycles, per node, as %), how much of it your patches removed, and whether every result stayed
    identical.
 2. A1: the HRZ node counts against the known answer; how you know the work was not optimised away.
 3. A2/A3: the tables, with the repeated-run line first.
 4. Part B: one paragraph and one number line per patch; the oracle results.
 5. Part C: the two tables and the shares.
 6. Ideas that were not bit-exact; ideas you had no time for.
 7. Files of the repository you opened. 8. Start and end of each step from recorded stamps.
 9. What you did not do. 10. What you are not sure about. 11. A better way (may be empty).
12. Your model name and version as you know it.
