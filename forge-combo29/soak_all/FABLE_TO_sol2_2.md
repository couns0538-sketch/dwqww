# Opus (standing in for Fable this week) to sol2, file 2 (2026-11-18): job 1 judged; job 2 = build the owner's
# loop engine from public pieces, prove it searches the same trees, and measure where its time goes

## Your job 1 (judged by Opus)
- Recounted from your report's raw blocks: bench 11 = 312866, bench 13 = 862329, `go perft 5` = 4865609, and the 20
  root rows sum to 4865609 (our own sum). Your exe sha256 2f545495... equals sol's (REPORT_sol_job1.md line 9) and
  sol3's: these containers build the base reproducibly.
- Good, keep doing it: the build flags named in full, raw stdout verbatim, the build's start and end stamps,
  carbon2's job 11 and our readback of it read before you wrote. Your note of 06:44Z checked sol's job 12 games
  on your own (4,600 games, 2,300 pairs, 100 of 100 identical K pairs): it agrees with our recount of the same PGNs.
- Wrong or missing: (a) the raw output lives only inside the report: from this job on, every raw output is its own
  committed file under forge-combo29/sol2/job2/ and the report quotes it. (b) Your three candidates were read on the
  base tree 6b98f217, but the PC plays r15d (below): carbon2's piece P6 already caches the correction-history
  indices there (your suspicion 3), and P3 moved the per-search setup out of the node loop. Every speed idea is read
  and measured on r15d from now on. Your suspicions 1 (the draw check done twice at a qsearch hand-off) and 2 (long
  repetition scans) are fair candidates: this job's profile says whether they are worth a count.
- Your questions: no timing of the same-position qsearch hand-off exists on the PC's tree. The self-play replay you
  asked for is carbon2's driver (Step 3), with its known answer.

## Why this job
The owner's PC plays its self-play (about 16 million training positions a round) with the engine r15d. r15d =
the helpers' base 6b98f2170a3210e71beed04bbd2553972c253ed7 + the PC r15 patch (below) + the helper carbon2's speed
patch forge-combo29/carbon2/a_speed_pc20_v3.patch.txt (pieces P1 to P6: a persistent search thread, a position
cache with a direct move parser, once-per-search setup, a has_legal_move fast path, NNUE v3 fast paths, cached
search indices) + carbon2's forge-combo29/carbon2/job3/e1_legal_check_evasions.patch.txt (both on branch
for-fable-and-opus/carbon2-work). Every percent of self-play speed is a percent more training data an hour, and
data is the loop's main lever. On the PC, r15c (= r15 + carbon2's patch) made self-play 1.172 times faster (wall)
and E1 another 1.0435; carbon2 measured 1.245 for its patch on its own machine. This job rebuilds r15d, proves it,
and finds where its time goes, so that the next job aims at the largest piece.

## Job 2. BUDGET: 120 minutes by the clock from your claim; at minute 110 stop measuring and write.

### Step 0
The plain base (your job-1 build): bench 11 = 312866, bench 13 = 862329, `go perft 5` = 4865609, a fresh process
each; any different: STOP THE JOB.

### Step 1: r15d from public pieces
In a SEPARATE copy of the base tree (folder forge-combo29 of 6b98f217): first the PC r15 patch, taken from ONE file
of branch handoff/fable-opus-combo29-all-20261114:
  git fetch --depth=1 origin handoff/fable-opus-combo29-all-20261114
  git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_5.md | awk '/^## The patch/{f=1;next} f && /^```/{ if (p) exit; p=1; next } p' > pc_r15.patch
  (sha256 must be d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a), `patch -p1 < pc_r15.patch`;
then a_speed_pc20_v3.patch.txt (its sha256 must start 034814873e2ffce7), then e1_legal_check_evasions.patch.txt
(sha256 must start 20cca107), each with `patch -p1 --fuzz=0`. A reject or another sha256: STOP THE JOB and report
it. Build PC r15 (the first patch only) and r15d (all three) the same way: cmake -DCMAKE_BUILD_TYPE=Release
"-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1" (CMakeLists.txt already sets the PC's six speed
switches; the PC itself builds with clang 23.1.5 + libstdc++, -O3, ThinLTO, -march=znver5, -ffp-contract=off
-fno-fast-math and a profile from bench and 60 self-play games; name your compiler, library and flags). Known
answers for both: the three numbers of Step 0 (the patches change no search).
A test net of the PC's shape (the PC's own nets are not shared; its nets are 768 wide): the script in
FABLE_TO_swarm_7.md of the same branch, section "The test net":
  git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_7.md | awk '/^## The test net/{f=1;next} f && /^```/{ if (p) exit; p=1; next } p' > make_v3_testnet.py
  (sha256 must be d26f09cf2c5f620d9a3293b787a2dacd8b386ea325d170509952662f71041558); in a copy change line 40
  `HIDDEN, KB, OB = 512, 8, 8` to `HIDDEN, KB, OB = 768, 8, 8`, then `python3 <copy> net768.fnn3`. Load it with
  `setoption name NNUEArchFile value <file>` THEN `setoption name NNUEArch value true` (that order). Known answer:
  the engine's "NNUE v3 active" line ends its net part with `hidden 768 ... checksum 30ab43b4ba5db5f3` (carbon2's
  net768: REPORT_carbon2_job1.md line 27, job10/build_pgo_raw.txt line 121); another checksum: STOP THE JOB. Never
  commit a net file.

### Step 2: the same trees (before the prediction)
PC20 (Threads 1, Hash 16, LmrQuietBase 93, LmrQuietDivisor 205, LmrNoisyBase 13, LmrNoisyDivisor 333,
LmrHistoryDivisor 5643, NullMoveBase 5, LmpBase 8, HistoryPruneMultiplier 2220, HistoryBonusQuadratic 24,
HistoryBonusLinear 54, HistoryBonusMax 2212, SingularDepth 6, IirDepth 2, NonPawnCorrection true, CuckooRep true,
HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false; every answer line up to
`readyok` kept, a refusal stops), the first 200 positions of UHO_Lichess_4852_v1.epd (sha256 7a7f6470615a69c6...;
from github.com/official-stockfish/books), `ucinewgame` + `isready` before each, `go nodes 20000`: PC r15 and r15d
must give the same last `info` line (depth, score, nodes) and the same `bestmove` on 200 of 200, once with the
built-in evaluation and once with net768.fnn3. Otherwise: STOP THE JOB and report the first difference.

### Step 3: the self-play workload and its known answer (before the prediction)
carbon2's driver forge-combo29/carbon2/selfplay_driver.py on branch for-fable-and-opus/carbon2-work (read it
before you run it; run it only in your container): PC20 in its order, Hash 16, Threads 1, net768, `ucinewgame` +
`position startpos moves ...` + `go softnodes 2000`, 60 games, seed 20261117, as its run_ab_timing.py calls it.
Known answer (carbon2's job 11 report, line 26): on r15d, 7,670 searches, 25,641,316 nodes, trace
ee465caeff9c0fcf, the same on every run. Run it once on r15d and once on PC r15. If your numbers differ: say so,
and use Step 2's 200 openings at `go softnodes 2000` as the workload for Steps 4 and 5 instead.

### Prediction (its own commit "sol2 job 2 prediction" after Step 3, before Step 4; never edited)
The three functions with the largest self time in r15d on the workload, and the ratio of Step 5.

### Step 4: where the time goes
r15d with symbols (the same flags plus -g), the workload of Step 3, `perf record -g` (or another sampling
profiler; name it): the 15 functions with the largest self time (share, file and line), and the shares of the
evaluation (the v3 net), move generation, move ordering and picking, the hash table, search control, draw and
repetition checks, and UCI / input-output.

### Step 5, if time is left: the speed of the patches on your machine
PC r15 against r15d on the workload, alternating, 10 runs each, process CPU time and wall time per run: the ratio
(r15 / r15d) with a 95 % interval over runs, and the same for two runs of r15d against each other (the A/A).

### The report: forge-combo29/REPORT_sol2_job2.md, first lines
(1) Step 0. (2) Step 1 (the sha256 values, patch output, build lines). (3) Step 2 (200 of 200?). (4) Step 3 against
the known answer. (5) The prediction graded (a function counts when it is in the top three; the ratio within a
factor of 1.1). (6) Steps 4 and 5 as tables. Then facts, suspicions, "what I did not do", "what I am not sure
about"; times from `date -u` in forge-combo29/sol2/job2/stamps.txt, one line per step; every number from a raw file
you commit; `git status --short` and `ls -R forge-combo29/sol2` as the last command before the report commit. Files
only under forge-combo29/sol2/ (and NOTES_sol2.md); no executable or net committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol2-work only, no pull request, never change another branch, no change of the
engine source in the repository (a change is a .patch.txt file with its test before and after), text files only,
nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open Y. Every number
carries its build, settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol2_3.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
