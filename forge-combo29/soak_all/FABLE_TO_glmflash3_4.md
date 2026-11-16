# Fable to glmflash3, file 4 (2026-11-15): job 3 received, and job 4

## Your job 3 report

Received and read (first paragraph; the full reading follows in file 5, this file comes quickly because your
waiting time is short).
- **The 512-bucket table keeps the gain: +13.4 per node (95 % +2.8 to +24.0) next to +11.5 for the 4,096-bucket
  table, and the two sizes head to head +1.9 (-8.2 to +12.0).** So the small table is the one to use: eight times
  less memory to touch. The PV bonus adds nothing (+4.2, inside the default's interval): the update site you had
  missed was not worth having, and now that is measured instead of assumed.
- Every prescribed match ran, including the optional one, and you say so in the first paragraph. Good.
- The speed cost (about 6 % nodes a second at 512 buckets by your rough figure) is the open question, and so is
  the next one:

**What the owner's PC says about your feature.** I ported it into the engine there and played it ON TOP of the
bundle that went into that engine today (a second history table keyed on attacks by lesser pieces, and three
more changes): at 2,000 nodes per move it adds +1.7 +/- 7.2 over 6,000 games. Nothing. Your +11.5 and +13.4 are on
the plain engine at 20,000 nodes. Either the two history tables overlap (each explains what the other would), or
the gain needs depth. Job 4 separates the two.

## Job 4. BUDGET: 85 minutes by the clock; at 75 minutes stop and write the report.

Rules and form as in job 3 (a text patch, no engine source committed, no pull request, text only, no binary
files; `nodes=20000`, Threads 1, Hash 16, OwnBook false, UHO openings twice with colours reversed, `order=random`
with `-srand <seed>`, no adjudication; a 2-game probe with the input log before EVERY match). Folder
`forge-combo29/tests_glmflash3_job4/`, report `forge-combo29/REPORT_glmflash3_job4.md`, commit subject
"glmflash3 job 4 report". After pushing, wait for file 5 with the sleeping command; do not end your run.

### The question
Does your pawn-structure history still gain when the bundle "B1" is already on, at YOUR node count?

### The tree
The bundle exists as a patch for an OLDER tree of this engine: commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa`
(source at the ROOT of that commit: `src`, `include`, `CMakeLists.txt`) plus
`opus_r13/p1/b1/b1_port.patch` from branch `opus-r13-p1-nearmiss-ports` (`patch -p1`, no fuzz, no rejects; build
with `-DFORGE_NNUE_HIDDEN=256` among the C++ definitions, which this tree needs). Known answers of that tree:
    no option:              bench 11 312866   bench 13 862329   go perft 5 4865609
    BundlePreset B1:        bench 11 280182   bench 13 758456   bench 16 3357587
(`BundlePreset B1` = `CorrHistPlus 1`, `HistRework 2`, `CuckooRep true`, `TtPruneV2 true`; it is a declared option.)

### What you deliver
`pawn_history_b1.patch.txt`: your feature (job 3's version: `PawnHistory`, `PawnHistoryBits` with default 9 this
time, no PV bonus, no weight option) written for THAT tree on top of the B1 patch. The code around the history
tables differs there (B1 adds its own table and changes how quiet moves are scored): read `include/forge/hist_rework.hpp`
and the places in `src/search.cpp` where B1 reads and updates its table, and put yours beside them. Do not copy
your old patch blindly: the line numbers and some function shapes differ.
Known answers for the patched tree: with `PawnHistory` off, the five numbers above exactly (no option AND
BundlePreset B1), and the sha256 identity over 2,000 depth-9 answers against the unpatched B1 tree, once with no
option and once with `BundlePreset B1` set on both. With `PawnHistory` on: `bench 13` alone and together with B1
(two new numbers, both different from the known ones).

### The matches
    C    control: 20,000 against 10,000 nodes, no options, 300 games, seed 7620: near +200
    M1   cand: BundlePreset B1 + PawnHistory    base: BundlePreset B1    2,000 games   seed 7621
    M2   the same with seed 7622, 2,000 games (always)
    M3   cand: PawnHistory alone    base: none    2,000 games   seed 7623
         (does the feature gain on THIS tree as it did on the other one? It is the control of M1 and M2: if M3 is
         near 0 too, the port is suspect, not the bundle)
Order: C, M1, M3, M2; give each its own time limit so that the last one is the one that is cut.

### The report
The form of job 3. First line in plain words: what `PawnHistory` adds on top of B1 per node (pooled over M1 and
M2 with the 95 % pair interval), next to what it gains alone on the same tree (M3). Say in the FIRST paragraph
what was cut or not reached. Before you write "only" or "never" about the code, search for it.
