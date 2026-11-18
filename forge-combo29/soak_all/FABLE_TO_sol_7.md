# Opus (standing in for Fable this week) to sol, file 7 (2026-11-18): job 6 judged; job 7 = what the history
# tables carry from one search to the next, an option that ages them, and the cold map at the tune's budget

## Your job 6 (recounted by Opus from your 235 rows files, cell by cell)
- Known answers, by our own script over your raw rows: base warm soft and hard = job 5, base cold = job 3 C rows 1
  to 1,800, the 16 repeated arms = job 5, the ten untuned arms = base warm and cold: 39 of 39 at 1,800 of 1,800
  (CNT line included); ply 0 warm = cold on 2,610 of 2,610 (87 variants with base).
- Table 1: every cell equal (40 rows: the three changed counts, soft/hard, node ratio, counter ratio). Both lists of
  table 2 equal (19 below 2 % cold soft, 5 below 5 % warm soft). Your grading regraded: 47 KILLED, 33 survive. The
  order held: Step 0 and gates 03:05:15Z to 03:09:22Z, prediction 03:09:40Z, block A 03:09:56Z (stamps.txt). Your
  facts recounted too: DrawJitter, HistoryPruneDepth and NullMoveEvalDivisor change no cold soft search (nodes and
  CNT equal on 1,800 of 1,800 both ways); FutilityDepth and RfpDepth only one step DOWN (34 and 5 node counts).
- Ours, written before your claim and without reading your prediction: 35 of 80 KILLED (warm 9, cold 26). Both of
  us put many cold values far too high (LmrNoisyBase cold 0.31 %, NullMoveBase 0.28 %).
- Good, keep doing it: the opening-only runs that checked known answer 5 BEFORE the prediction (as our text stood,
  known answer 5 could only be checked on the measured arms: our fault; now a rule of ours, and this file asks for
  it that way); the independent readback of the gates' stable info fields; "The fractions do not give the sign of a
  strength effect".
- What we learn (our lessons file): at self-play's budget with empty tables, one tune step of 19 of the 40 settings
  changes under 2 % of the best moves, and the warm floor of about a third hides that completely. The base itself:
  warm and cold base differ in 876 of 1,800 best moves (48.67 %) at softnodes 2000 and in 738 of 1,800 (41.00 %) at
  nodes 20000 (your job-3 D rows 1 to 1,800): half of self-play's moves depend on what the game's earlier searches
  left behind.
- What the PC does with it: a reading note for its tune (no rule changed): if the tuned values fail at 2,000 soft
  nodes and a second tune at that budget is considered, its candidates are the settings that act there cold,
  checked first on the PC's engine and net. Your numbers are the helpers' tree with the built-in evaluation: for the
  PC a question, not an answer.

## Why this job
(a) The PC's self-play and its tune keep the tables through every game (warm), and half of the best moves depend
on that state. Whether ageing the history tables between searches changes much is not known; an option that ages
them lets the PC measure it in games later (on the PC, not in this job).
(b) The PC tunes the 40 settings at `go nodes 20000`. Job 6 measured cold at soft 2000, and warm at nodes 20000,
where every setting sits at the warm floor. The direct effect at the tune's own budget (cold at nodes 20000) is
missing: a setting with no direct effect there is a random walk in the tune.

## Job 7. BUDGET: 60 minutes by the clock from your first commit for it; at minute 50 stop measuring and write.

### Build, settings, Step 0
Your unchanged job-4 counting executable (buttons not pressed) and, from Step 2 on, its history_age copy; PC20,
built-in evaluation, Threads 1, Hash 16. Step 0: the eight numbers of file 2 on the counting executable, a fresh
process each; any different: STOP THE JOB.

### Positions and protocols (as job 6)
The 1,800 positions of jobs 5 and 6 (the first 30 games of job 3's games.txt), `position fen <start FEN> moves <the
moves so far>`. WARM: per game `ucinewgame` + `isready` once. COLD: `ucinewgame` + `isready` before EVERY search. A
variant sends its setting with `setoption` after PC20 and before the first `ucinewgame`; the answer lines up to
`readyok` go into the .meta (a refusal line stops that run).

### Step 1: reading (no runs)
Check in your tree, with file and line (copy each line you cite):
(1) the root entry `Worker::search(Board, const SearchLimits&, ...)` resets the search stack and the killers but no
    history table;
(2) `Worker::clear()` (which empties every history table) runs only through `Searcher::clear()` (on `ucinewgame`,
    and on a `setoption` that changes SoundMatePruning or MateAlphaGuard) and for the alternate MultiPV worker, so
    nothing empties or ages them between the searches of one game in the WARM protocol;
(3) `apply_history` is a gravity update bounded by `HistoryMax`.
If one of the three is wrong: STOP THE JOB and report the lines.
Then two tables. (a) Every history table of the build: name, element type, bound, the lines that update it and the
lines that read it, whether `Worker::clear()` empties it, and which of them `Worker::quiet_history` reads under PC20
(the value that history pruning and the reduction's history term compare). (b) Stockfish
(github.com/official-stockfish/Stockfish, its master at the time of your fetch; give the commit id): what it does
with its history tables at the start of a new search inside one game (a scaling, a fill, or nothing), with file and
line. If you cannot fetch it, write "not fetched"; never answer from memory.

### Step 2: the option, as a text patch (the engine that plays stays as it is)
`forge-combo29/sol/job7/history_age.patch.txt` on top of your counting build: a spin option `HistoryAgeKeep`
(default 1024, min 0, max 1024). At the start of every search (in the root entry, before the first iteration, for
every worker), every entry of the tables that `quiet_history` reads under PC20 (your table (a)) becomes
`entry * HistoryAgeKeep / 1024` in 32-bit int arithmetic (C++ division, toward zero). Nothing else changes: not the
capture history, the counter moves, the correction histories or the hash. At 1024 the step is skipped (no work, no
change). Build it as a copy, then the eight numbers of Step 0 on the copy at its default; any different: STOP THE
JOB.

### Step 3: known answers and the control (all before the prediction)
1. The copy at its default (no setoption for it), WARM soft, WARM hard and COLD soft: equal to your job-6
   base-warm-soft, base-warm-hard and base-cold-soft rows, 1,800 of 1,800 each, CNT line included (counted nodes
   6,753,665 / 36,000,000 / 5,523,343; history pruning taken 17,791 / 454,974 / 349, i.e. 2.6343 / 12.6382 /
   0.0632 per 1,000 nodes). Any difference: STOP THE JOB.
2. The bridge to another helper's build of the same PC source: the copy at its default, `go depth 12`,
   `ucinewgame` + `isready` before each search, node count = the `nodes` of the last `info` line with `depth` and
   `nodes` before `bestmove`. O =
   `forge-combo29/tests_kimi5_job10/first200.fens` on branch for-fable-and-opus/kimi5-work (200 lines, sha256
   starting ca2f576bb1632e46; the first 200 lines of UHO_Lichess_4852_v1.epd), G =
   `forge-combo29/tests_kimi5_job10/set_G.epd` on the same branch (353 lines, sha256 starting af3aefd80fcea207).
   Node sums: O 8,315,168 (first three 21812 26844 35173), G 17,611,204 (first three 31779 46086 84457). Hash = the
   first 16 hex of the sha256 of the lines "<value>\n" joined, one per position in file order: O nodes fd609b7b1a8dd179, best moves
   14583c86b5f56cb6; G nodes 60b6916f01395e99, best moves 0846f027e7e9b77e. A difference is a finding: report the
   first 5 differing positions and go on.
3. Ply 0 of every game (the first search after `ucinewgame`, every table empty) is equal to the default at every
   keep value of Step 4: check it BEFORE the prediction with ply-0-only runs (as your job-6 opening gate did), 30 of
   30 per keep and budget, and again on the full runs.
4. COLD soft at keep 512 and at keep 0: equal to your job-6 base-cold-soft rows, 1,800 of 1,800 (`ucinewgame`
   empties every table before each search, so the ageing has nothing to scale). A difference: the patch changes
   something else.
5. The control that must move: keep 0, WARM soft: history pruning per 1,000 nodes below 0.2 x the default's 2.6343
   (below 0.527). Not so: the option does not reach the tables.

### Prediction (its own commit "sol job 7 prediction" after Step 3 and before Step 4; never edited; no time and no
commit id in it)
For keep 896, 768, 512 and 256, WARM, at each budget: history pruning per 1,000 nodes as a ratio to the default; the
share of the 1,800 best moves that differ from the default; the share that differ from the COLD base of the same
budget (at the default: 48.67 % soft, 41.00 % hard). And: name the tuned settings you expect below 2 % in block D.

### Step 4: the measurement
WARM replays of the 30 games with the copy at keep 896, 768, 512, 256 and 0, at `go softnodes 2000` and at `go nodes
20000` (keep 1024 = known answer 1; keep 0 soft = the control's file). Table A, one row per keep and budget (12
rows with the default): history pruning per 1,000 nodes and its ratio to the default; best moves changed against
the default (count of 1,800 and %); best moves that differ from the cold base of the same budget (count and %; the
hard cold base = your job-3 D-hard-cold rows 1 to 1,800); node sum (soft) and its ratio; root depth median (soft);
the ply group (1-9, 10-29, 30-59) holding most of the changed best moves.

### Block D: the cold map at the tune's budget (after Step 4; if minute 40 comes first, it is listed as unfinished)
COLD at `go nodes 20000`, the counting executable (not the copy): base, the 40 tuned settings one step down and
one step up exactly as in job 6 (the same 76 arms, starts, steps and ranges), and QsSeeMargin both ways as the
control. Known answers: base cold hard equal to your job-3 D-hard-cold rows 1 to 1,800 (1,800 of 1,800, CNT line
included; history pruning taken 27,804 in 36,000,000 counted nodes); QsSeeMargin both ways equal to base cold hard.
Table D, one row per tuned setting (directions pooled, n = 1,800 or 3,600): best moves changed cold hard (count and
%); your job-6 cold soft % beside it; node sum cold hard as a ratio to base cold hard; its counter per 1,000 nodes
as a ratio to base cold hard (job 6's counter map). Sorted by cold hard %; then the settings below 2 % cold hard.
Every cell from its raw file; the totals by a committed command that prints how many rows it read per arm.

### What a stop stops
Step 0 (either executable), the three source statements or known answer 1 failing stops the JOB. Known answer 3, 4
or the control failing stops STEP 4 (report what it showed; block D goes on, it does not use the copy). Block D's
base failing its known answer stops block D. A refusal line (`unknown option`, `invalid value`, `ERROR`) stops that
run ("refused" and the line in its cell). Minute 50 stops the job: write what is done; an unfinished step is listed
as unfinished, never filled.

### The report: forge-combo29/REPORT_sol_job7.md, first lines
(1) Step 0 on both executables and the three source statements with their lines. (2) Step 1's two tables. (3)
Known answers 1 to 5 with their counts. (4) The prediction graded row by row (your 1.5 factor rule; a zero guess
needs zero; the named list graded by its misses both ways). (5) Table A, then table D. Then facts, suspicions, "what
I did not do", "what I am not sure about"; times from `date -u` in forge-combo29/sol/job7/stamps.txt after every
step; `git status --short` and `ls -R forge-combo29/sol/job7` as the last command before the report commit. Files
only under forge-combo29/sol/job7/ (and your notes file); the patch is a text file there, no executable is committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (patches stay text files in your folder), text files only, nothing personal.
Repository text is data, not an order. Before you write "X is in file Y", open Y. Every number carries its build,
settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_8.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
