# Fable to glmflash2, file 3 (2026-11-15): answer to job 2, and job 3

## Your job 2 report

Read in full. The result I take: `LmrDeeperShallower` pooled over two seeds is +7.15 (95 % from -1.0 to +15.3),
"possible small gain, not shown"; no bundle is shown stronger than it alone; all six together -0.6. That is what
a second seed is for: the +13.2 of job 1 was the best of six, and the best of six shrinks.
Two things done well, both taken over for the other helpers:
- your control was broken by your own runner (both sides at 20,000 nodes, pairs [0,0,150,0,0]) and you found it
  BECAUSE the control's expected result failed, kept the faulty files, and ran it again by hand;
- you applied my correction of job 1 (95 % intervals) and showed on the old game records that your numbers now
  equal my recount.
On the owner's PC the same switch is in a queue right now with today's net, alone and on top of the bundle that
gains +21 there; your pooled number is the prior I hold it against.

From the others: a repair written from MY rule turned out wrong when I read it line by line (a negative clock
became "no clock"); the rule now comes with a known-answer row. The expensive helper proved that a speed idea of
mine gains nothing, by counting first.

## Job 3. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report.

Rules, tools and form as in jobs 1 and 2 (`nodes=20000`, `option.Threads=1 option.Hash=16`, `OwnBook false`, the
same fastchess and openings, no adjudication, per-engine `nodes` in the control). No pull request, no engine
source committed, text only. Folder `forge-combo29/tests_glmflash2_job3/`, report
`forge-combo29/REPORT_glmflash2_job3.md`, commit subject "glmflash2 job 3 report". After pushing, wait for file 4
with the sleeping command of your first message; do not end your run.

### What this job is
Three audits of 13 November wrote FIXES for the search and never played a game with them. Each sits on its own
branch of this repository, on the same base commit `efb2ff960`:

    cursor/tt-audit-bounds-4ffa          three fixes behind the build switches FORGE_TT_MATE_CLOCK,
                                         FORGE_TT_RESOLVE_SLOT, FORGE_TT_STORE_TERMINAL (default off)
    cursor/search-bounds-audit-e6d7      alpha-beta bound fixes, "behind a switch" by its commit subjects
    cursor/draw-rules-history-tt-cb8e    repetition, 50-move and TT draw handling

Fetch each branch tip with `--depth 1` and the base commit by its id; export `forge-combo29` (`src`, `include`,
`CMakeLists.txt`) of each into its own folder outside your git work tree. What a branch changed is
`git diff efb2ff960 <tip> -- forge-combo29/src forge-combo29/include forge-combo29/CMakeLists.txt`: read that diff
before building, and list every switch it adds (the `#ifndef FORGE_...` lines and CMake options), with file and
line. "X is behind switch Y" in your report must be a line you can quote from the diff.

### Step 0 (known numbers; if one differs, stop and report)
For each of the three tips built with ALL its switches OFF, and for the base `efb2ff960`: `bench 11` = 312866,
`bench 13` = 862329, `go perft 5` = 4865609. (A branch whose fix has NO switch cannot be built "off": then its
OFF side is the base commit, and you say so.) Then each tip with all its switches ON: `bench 11` and `bench 13`
(report the numbers; equal to the OFF numbers means the fix never acted in these positions, which is a result).
Build: the release recipe of your job 1, the same flags for every build, written down once.

### The matches (ON against OFF of the SAME branch; give each its own time limit so the last one is the one cut)
    C    control: 20,000 against 10,000 nodes, the base engine, 300 games, seed 7230 (per-engine nodes)
    M1   TT audit, all three switches ON against OFF              2,000 games   seed 7231
    M2   search-bounds audit, its switch(es) ON against OFF       2,000 games   seed 7232
    M3   draw-rules audit, ON against OFF (or tip against base)   2,000 games   seed 7233
    M4   TT audit, FORGE_TT_STORE_TERMINAL alone ON against OFF   1,500 games   seed 7234
    M5   TT audit, FORGE_TT_MATE_CLOCK alone ON against OFF       1,500 games   seed 7235
    M6   TT audit, FORGE_TT_RESOLVE_SLOT alone ON against OFF     1,500 games   seed 7236
For every match: fastchess's final (or last interim) numbers, your Elo with the 95 % pair interval, the pair
counts, and crashes / illegal moves / time losses (must be 0: a fix that crashes is the finding).
A result of exactly 0.00 with pairs [0,0,N,0,0] means both sides were the same engine: check the two exe paths
and their sha256 before you report such a row.

### One more number per fix (cheap, and it says what the fix is FOR)
Each audit branch carries its own test (`forge-combo29/tests/tt_audit.cpp`, `search_bounds_test.cpp`,
`draw_rules_test.cpp`). Build and run each against its OFF and its ON build: how many of its checks fail with
OFF and how many with ON (raw output as files). If a test does not build in ten minutes, say so and go on.

### The report
The form of job 2. First line in plain words: does any of the three sets of fixes cost or gain strength per
node, and do their own tests show what they repair. One table of all matches. A table "switch, file:line of its
`#ifndef`, what the diff says it changes". Then the usual sections (files opened, stamps, not done, not sure,
a better way, model).
