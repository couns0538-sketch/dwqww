# glmflash2 job 3 report (2026-11-15)

## 1. Result in plain words

**The draw-rules branch loses strength per node: -12.65 +/- 9.05 my count, -13.13 +/- 9.29 fastchess
(1,869/2,000 games, tip against base) - its interval excludes 0.** The other two branches cost nothing
measurable at 20,000 nodes: the TT branch with all three switches ON played the OFF engine to a
standstill (-0.56 +/- 1.76 over 1,901 games; 911 of 928 pairs were two draws), and the search-bounds
switches (PvBoundFix + AspirationKeepExact) gave -1.05 +/- 10.20 over 1,978 games. Each TT switch
alone also changed play not at all or almost not at all (section 5). Their own tests do
NOT show what they repair: tt_audit passes 69/69 checks with the switches OFF and ON and its output
is byte-identical between the two builds; draw_rules_test does not even compile against the base
(the branch's test calls the patched 2-argument `score_usable`, the base has 1 argument);
search_bounds_test passes ("all passed") in the one form I could run it.

## 2. Step 0, expected against printed (fresh process each)

Build recipe (same for every build, written once): CMake Release, g++ 13.3.0, default
FORGE_MARCH=x86-64-v4 (VM has AVX-512+BMI2), no other flags; ON builds of the TT branch add
-DCMAKE_CXX_FLAGS="-DFORGE_TT_...=1" (the switches are `#ifndef`-guarded compile defines; the branch
adds no CMake option()). Base commit efb2ff960 and all three tips fetched --depth 2; the raw-SHA
fetch of efb2ff960 was refused by the remote ("couldn't find remote ref"), the commit was already in
local history.

| build                | bench 11 | bench 13 | perft 5 | files                                  |
|----------------------|----------|----------|---------|----------------------------------------|
| base efb2ff960       | 312866   | 862329   | 4865609 | step0/bench11_base.txt, bench13_base.txt, perft5_base.txt |
| tt tip, switches OFF | 312866   | 862329   | 4865609 | step0/bench11_tt_off.txt, bench13_tt_off.txt, perft5_tt_off.txt |
| bounds tip (its compile defaults) | 312866 | 862329 | 4865609 | step0/bench11_bounds.txt, bench13_bounds.txt, perft5_bounds.txt |
| draw tip             | 312866   | 862329   | 4865609 | step0/bench11_draw.txt, bench13_draw.txt, perft5_draw.txt |
| tt tip, all 3 ON     | 312866   | 862329   | (not run) | step0/bench11_tt_on.txt, bench13_tt_on.txt |
| bounds tip, PvBoundFix=1 + AspirationKeepExact=1 (UCI spin, runtime) | 409709 | 890480 | (not run) | step0/bench11_bounds_on.txt, bench13_bounds_on.txt |
| tt_st (STORE_TERMINAL only) | -  | 862329  | -       | step0/bench13_tt_st.txt                 |
| tt_mc (MATE_CLOCK only)     | -  | 862329  | -       | step0/bench13_tt_mc.txt                 |
| tt_rs (RESOLVE_SLOT only)   | -  | 862329  | -       | step0/bench13_tt_rs.txt                 |

Findings inside Step 0: all OFF numbers equal the known numbers. The three TT switches, together AND
each alone, leave the two bench positions bit-identical (862329) - they never acted there; that is a
result, per the job text. The bounds switches act (409709 / 890480). The draw branch has NO switch:
per the job rule its OFF side is the base commit, and its ON side is the tip.

## 3. Control (power line), seed 7230, 300 games, per-engine nodes

fastchess header line says "20000 nodes - 10000 nodes" (per-engine nodes took effect). 20k side
W 193 L 23 D 84 (78.33%), fastchess Elo +223.26 +/- 32.84, Ptnml [0,3,30,61,56]; my parser: identical
counts and point estimate, 95% pair interval +/- 34.72. The tool can see a difference; power line
stands. Files: matches/control_7230_fastchess_tail40.txt, matches/control_7230_lines.txt.
Crashes/disconnects: 0. Ended 16:38:49Z.

## 4. Switch table ("X is behind switch Y" = a line I can quote)

| switch (branch)          | where (file:line in the tip)                       | what the diff says it changes |
|--------------------------|----------------------------------------------------|-------------------------------|
| FORGE_TT_MATE_CLOCK (tt) | include/forge/search.hpp:31-32 (`#ifndef`/`#define ... 0`), used at search.hpp:106 | "a stored mate that needs more plies than the halfmoves left before the 50-move draw is not reused" (comment, search.hpp:29-30) |
| FORGE_TT_STORE_TERMINAL (tt) | include/forge/search.hpp:37-38, used at src/search.cpp:1356 and :1729 | "store checkmate, and a no-move node that finishes the move loop, as an exact table score" (comment, search.hpp:36-37) |
| FORGE_TT_RESOLVE_SLOT (tt) | include/forge/search.hpp:43-44, used at src/search.cpp:340 and :400 | "a store updates an existing tag or re-runs replacement instead of always writing the probe-time slot" (comment, search.hpp:42-43) |
| PvBoundFix (bounds)      | UCI spin option, default 0 (verified in `uci` output); declared include/forge/search.hpp:275 | "skip move pruning on PV nodes in the main search and in quiescence" so a bound is not built from a line that skipped legal moves (diff, include/forge/search.hpp hunk; also branch README: changes root score/best move in sampled positions) |
| AspirationKeepExact (bounds) | UCI spin option, default 0 (verified in `uci` output); declared include/forge/search.hpp:279 | "a fail-low aspiration re-search does not pull beta below the last exact score" (diff, same hunk) |
| (draw branch)            | no switch anywhere in its diff (checked: no added `#ifndef FORGE_`, no CMake option) | commits: "Search the 50-move draw when it is inside the horizon"; repetition/50-move/TT-draw handling edits in src/board.cpp and src/search.cpp |

The bounds branch also carries two fixes with NO switch (its README table marks them "always"):
the aborted-root-attempt best-move/PV handling and a `score_from_tt` mate/fifty-move filter. In M2
those ride along on BOTH sides (same exe); a tip-vs-base match would have isolated them, and I did
not have time for it (section 8).

## 5. All matches (ON against OFF of the same branch; 20000 nodes, 1 thread, 16 MB, OwnBook false)

Machine: 4 cores, concurrency 4. fastchess v1.8.3-alpha, same book, no adjudication. All matches:
crashes / illegal moves / disconnects / time losses = 0 (grep over each full output; the count lines
are quoted per match below). "fc Elo" = fastchess's own final or last-interim block; "my Elo" with
95% pair interval from pgn_stats.py (identical point estimates everywhere, as in jobs 1-2).

| #  | match                                          | seed | games     | W-L-D       | Ptnml(0-2)              | fc Elo +/- err   | my Elo +/- 95%  | crashes |
|----|------------------------------------------------|------|-----------|-------------|-------------------------|------------------|-----------------|---------|
| C  | base 20k nodes vs base 10k nodes               | 7230 | 300       | 193-23-84   | [0,3,30,61,56]          | +223.26 +/- 32.84 | +223.26 +/- 34.72 | 0 |
| M1 | tt all 3 ON vs OFF                             | 7231 | 1901/2000 | 540-543-818 | [2,7,911,8,0]           | -0.39 +/- 1.77 (last interim) | -0.56 +/- 1.76 | 0 |
| M2 | bounds PvBoundFix=1+AspirationKeepExact=1 vs defaults (same exe) | 7232 | 1978/2000 | 540-548-890 | [48,243,417,227,53] | -0.39 +/- 10.71 (last interim) | -1.05 +/- 10.20 | 0 |
| M3 | draw tip vs base                               | 7233 | 1869/2000 | 510-579-780 | [37,204,511,154,28]     | -13.13 +/- 9.29 (SIGINT summary) | -12.65 +/- 9.05 | 0 |
| M4 | tt STORE_TERMINAL alone ON vs OFF              | 7234 | 1453/1500 | 416-416-621 | [0,0,726,0,0]           | -0.00 +/- 0.00   | -0.00 +/- 0.00  | 0 |
| M5 | tt MATE_CLOCK alone ON vs OFF                  | 7235 | 1432/1500 | 408-407-617 | [0,0,715,1,0]           | +0.25 +/- 0.49   | +0.24 +/- 0.48  | 0 |
| M6 | tt RESOLVE_SLOT alone ON vs OFF                | 7236 | 1500      | 406-405-689 | [0,4,741,5,0]           | +0.23 +/- 1.36   | +0.23 +/- 1.36  | 0 |

M1 needs its own line said plainly: with 911 of 928 pairs double-draws and only 17 deciding pairs,
the pair-level interval (+/- 1.76) is narrow but rests on few decisive pairs; read it as "the three
fixes together change play in only ~2% of opening pairs and lose nothing where they do". The three
single-switch matches agree: STORE_TERMINAL changed not one move in 1,453 games (every pair a
double draw), MATE_CLOCK left 715 of 716 pairs double-draws, RESOLVE_SLOT 741 of 750. For the
all-draws rows I checked the job's rule: the two exe paths differ and their sha256 differ
(tt_off 7dcfbe8a7019f169... vs tt_st 983b4f44b6ddc211...), and the CMake caches prove the
-DFORGE_TT_...=1 flags reached the compiler (step0/cmake_flags_evidence.txt, one line per ON build).
So the 0.00 rows are "the fix never acted in play", not "both sides the same engine".

Per-game line files committed: matches/<name>_lines.txt for every row (control and M1-M6).

## 6. Part B

Not done: this job file has no part B.

## 7. Files of the repository I opened

- The job file (git show on the handoff branch, read-only).
- The three branch diffs (saved as diffs/diff_tt.txt, diff_bounds.txt, diff_draw.txt; quoted above).
- Exported tip sources read by grep/sed only: include/forge/search.hpp (tt and bounds), src/search.cpp
  line probes, src/uci.cpp (bounds), CMakeLists.txt (all three tips), tests/*.cpp presence.
- No file of my working branch's HEAD tree was opened beyond these (builds ran on exports in
  /home/ubuntu/j3work, outside the git work tree).

## 8. Start and end of each step (recorded stamps, UTC)

- 16:33:2xZ  job 3 file read (fetched with job-2 wait loop at 16:32:46Z).
- 16:33-16:34Z  fetches (3 branch tips depth 2; SHA fetch of base refused; base present locally),
  exports to /home/ubuntu/j3work/j3/{base,tt,bounds,draw}, diffs saved (778/936/589 lines).
- 16:34:23Z  all 8 binaries built (51 s): base, tt_off, tt_on, tt_st, tt_mc, tt_rs, bounds,
  draw (forge + tt_audit x2 + forge_search_tests + draw_rules_test).
- 16:34:4xZ  Step 0 benches (files stamped 16:34:49Z).
- 16:34:5xZ  audit tests run: tt_audit OFF/ON, search_bounds_test, draw_rules_test (ON only;
  the OFF build of that test does not compile - section 1).
- 16:35:04Z  first runner launch - its control match died at once ("Engine binary does not exist"):
  /tmp/j3build/base had been deleted from under it by something outside my commands (second such
  /tmp deletion this session; I then moved all working files to /home/ubuntu/j3work). That first
  runner also survived its kill and spawned a second copy of itself racing the real one; its
  instant-fail match attempts wrote junk *_tail40/_lines files (same filenames, overwritten later by
  the real runs) and its `pkill -f j3build` killed the real M1's engines at 26 games
  ("Tournament was interrupted"). Cleaned up at 16:38-16:39; see section 10.
- 16:35:30Z  base rebuilt under /home/ubuntu/j3work (bench 11 = 312866 verified).
- 16:35:35Z -> 16:38:49Z  control 7230 (clean, 300 games).
- 16:39:13Z  second runner launch - my own bug this time: I changed run_match's signature to 8
  arguments but left 10-argument call sites; fastchess rejected the shifted line at once. Fixed the
  call sites; no match data from either false start.
- 16:39:44Z -> 16:51:29Z  M1 (cut at 700 s cap by SIGINT, 1901 games).
- 16:51:29Z -> 17:03:32Z  M2 (cut at cap, 1978 games).
- 17:03:32Z -> 17:15:00Z  M3 (cut at cap, 1869 games).
- 17:15:00Z -> 17:23:4xZ  M4 (cap 520 s; cut by SIGINT at 1453 games).
- 17:23:4xZ -> 17:32:3xZ  M5 (cap 520 s; cut by SIGINT at 1432 games).
- 17:32:3xZ -> 17:41:41Z  M6 (finished its full 1500 games before the 17:43 deadline; no cut).
- Report written from 17:17Z (overlapped with M4-M6), final numbers filled 17:41-17:45Z,
  committed and pushed ~17:46Z.

## 9. What I did NOT do

- M4 and M5 were cut by their 520 s caps (1453 and 1432 of 1500 games); M6 finished all 1500 inside
  the deadline, so no match ended UNCOUNTED - every match has fastchess's own summary block.
- I did not run a tip-vs-base match for the bounds branch (would have isolated its two "always"
  fixes); no time in the budget.
- I did not run the draw branch's test against OFF (cannot compile - section 1), and I did not try
  to patch the test to make it compile: that would be changing a branch's own evidence.
- No SPRT, no other TC, no engine source committed, no PR opened, no review bot appeared.

## 10. What I am NOT sure about

- The M3 loss (-12.65/-13.13) is one match against one seed. The interval excludes 0 with BOTH
  counters, and the branch's own commits say what changed (searching the 50-move draw inside the
  horizon changes the tree), so I believe the direction; the SIZE needs the PC retest.
- M1's pair structure (97% double draws) makes its tiny interval partly an artifact of how few pairs
  decide; I would not quote +/1.76 as a general precision claim for these fixes.
- tt_audit passing 69/69 in BOTH builds could mean (a) the suite has no power against these three
  faults, or (b) I ran it in a mode/way it was not meant for (it takes no arguments; I ran the bare
  binary in both compile configurations). I could not distinguish (a) from (b) in the time I had.
- search_bounds_test "all passed" was one run of one binary; I did not establish from its output how
  many checks it contains or whether it flips PvBoundFix internally (its README says the suite
  covers "the score changes with PvBoundFix", which suggests it does).
- The /tmp deletions: two directory trees vanished without any command of mine deleting them
  (/tmp/j3/base/forge-combo29 and /tmp/j3build/base). I rebuilt what I needed and moved everything
  to /home/ubuntu/j3work; I cannot say what deleted them.
- Timeline pollution: the false-start runners wrote junk lines into matches/timeline.txt and junk
  *_tail40/_lines files that the real runs then overwrote. The committed timeline.txt therefore
  contains both real and false-start lines; the report's stamps section is the cleaned-up story.

## 11. A better way

- `pkill -f <short substring>` is a footgun in a runner that also matches OTHER processes' command
  lines (here: every binary path containing "j3build"). My first runner killed the second runner's
  engines with it. Fix: kill by recorded PID list written by the runner itself, never by a path
  substring.
- One runner per session, named uniquely, and a startup check that kills any previous instance by
  exact script path before starting - the double-runner race cost ~4 minutes and one match.
- The audits' own tests should be written so they FAIL on the OFF build: tt_audit today cannot
  distinguish its own fix from the lock (byte-identical output). deepseek2's rule (a test must show
  power against a planted fault) applies to the audits' own tests, not only to Fable's prescribed
  controls.
- /tmp on this VM is not safe for state that must outlive a few minutes; /home/ubuntu is. All future
  runners of mine will write under /home/ubuntu from the start.

## 12. Model name and version

I am glmflash2, running on GLM, model glm-5p3-flash (GLM 5.3 Flash) as far as I know it.
