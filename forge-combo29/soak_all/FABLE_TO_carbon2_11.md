Your name in this job is: carbon2 (job 11)

Opus (standing in for Fable this week) to carbon2, file 11, 2026-11-17. Same machine, same builds, same Step 0 as
jobs 1 to 10. If your builds are gone, rebuild them exactly as job 1 says and show Step 0 again before anything else.
This file was written while your job 10 ran, so it does not judge job 10 yet (file 12 will). It judges job 9 and
gives you the next task, because your job 9 report named a fault in the PC's own build.

=== JOB 9 AS WE COUNTED IT (raw files, not the summaries) ===
- Good, keep doing it: both predictions as their own commits before their timings (prediction_p1 8f0a17e52,
  prediction_bundle5 d1e028b59); bundle 5 graded KILLED by its own bound although 12 of 12 rounds were faster; the
  bench 13 timing that pointed the other way kept in the report; the planted fault in the TT victim scan.
- Recounted with our own parser: P1 against bundle 4: 48 runs, ONE trace ee465caeff9c0fcf (7,670 searches,
  25,641,316 nodes in every run), engine CPU per-round median 1.0095, 11 of 12 rounds faster, wall 1.0092, 8 of 12.
  Bundle 5 against r15e: ONE trace, engine CPU median 1.0362, 12 of 12 (per round 1.0097 to 1.0874), wall 1.0415,
  12 of 12. Equal to your report. Identity EXACT as printed (both nets, bench 11 / 13 / 16, 250 rows, 1,000 evals,
  both traces); TT + stop-cap oracle 500,000 operations, MovePicker 2,010 and evasion 55,868 sequences, 0
  mismatches.
- Wrong, small: the predicted step product used W1 = 1.0423 and the report's "true" product uses W1 = 1.0149. Your
  job 8 W1 raw rows give 1.0043 (median of rounds), 1.0062 (pooled medians), 1.0052 (all time A / all time B):
  neither figure is W1's. With the medians the product is 1.0043 x 1.0127 x 1.0095 = 1.0267, BELOW the 1.0362 you
  measured, so steps timed one at a time do not predict a bundle in either direction. A number you multiply is
  copied from its raw file, with the file named beside it.
- Verdict: honest work, real gains on your machine. For the PC they stay questions until a build made like the PC's
  shows them (your bundle 1 gave +3.4 % on your machine and +0.8 % on the PC).

=== WHAT THE PC FOUND FROM YOUR REPORT (new since file 10) ===
- Your section 3.3 is right about the PC's build, and we had missed it. The PC profiles with "bench 11 / 13 / 16"
  only (file 10, fact (b)). bench (uci.cpp, the "bench" branch) searches to a fixed DEPTH with its own Searcher: no
  UCI worker thread, no node limit, no position parsing, no info lines. Self-play ("go softnodes 2000") and the PC's
  gate ("go nodes 50000") set node_limit_specified_, and the two lines in search() and qsearch() that read
  ((local_nodes_ & 1023U) == 0 || node_limit_specified_) && should_stop()
  then call should_stop() at every node instead of every 1,024th. So every PC exe since 14 November was profiled
  without the work it does most.
- The PC tests it tonight, declared before any exe exists: r15d built twice with the profile "bench 11 / 13 / 16,
  then 60 self-play games (go softnodes 2000, the PC's options, round 30's 768 net, openings not used by the timing),
  all profile files merged", timed against the loop's exe and its twin (both bench-profiled), 40 games a run, 10
  rounds; it pays at an engine CPU speedup of 1.02 or more in 8 of 10 rounds. Its result comes in file 12.
- The no-PGO builds of file 10 are timed (clang 23.1.5, ThinLTO, -march=znver5, libstdc++, NO profile; r15d against
  r15e = your bundle 1; 12 self-play games x 10 rounds, round 30's 768 net, the PC's options; one trace in all 80
  runs). WITH the PC's six speed switches of file 10 fact (c): engine CPU 0.977 (r15e faster in 1 of 10 rounds),
  wall 0.983 (4 of 10). WITHOUT them: engine CPU 1.039 (9 of 10), wall 1.032 (10 of 10). So your bundle buys, on a
  base without those six switches, what the switches already buy on the PC. Every timing of yours must be on a build
  WITH them (the job 10 build), or it measures a gain the PC already has.

=== THE TASK (yours to plan; the owner's words: a task, not an order) ===
Make Forge spend less processor time per self-play position ON A BUILD MADE LIKE THE PC'S, without changing one move,
node count, score or info line (time and nps excepted).
First, because it decides whether your bundles matter for the PC at all: on the PC-like PGO build of job 10 (WITH
the six switches of file 10 fact (c) in every tree you time), make a
second profile, the SP profile: bench 11 / 13 / 16 exactly as today, THEN 60 self-play games through your own
self-play driver (go softnodes 2000, PC20 and your net768.fnn3, Hash 16, Threads 1, openings that your timing does
not use), every engine process writing its own profile file, all files merged into one profile. Then, two builds of
each tree and your usual A1 B1 B2 A2 timing (12 rounds of 60 games, Hash 16), each with its prediction committed
alone first:
  (1) r15d with today's profile against r15d with the SP profile: does the profile alone pay on your machine?
  (2) r15d against bundle 5, BOTH with the SP profile: does bundle 5 keep anything once the profile holds self-play?
If job 10 already did one of these, say so, point to its raw file and go on. If your machine cannot make a PC-like
PGO build at all (job 10 says why), skip to the change of play below.
Then decide yourself, with the counts that decide it:
- If bundle 5 keeps 1 % or more in (2), find out which of its steps carry it (each step alone on the SP-profile
  build) and give the PC ONE unified diff against r15d that holds only the steps that carry it.
- If it keeps less than 1 %, say so and take the other half of file 8's task: a change of play behind a new UCI
  option that is OFF by default (with it off your identity proof must hold), with your reasoning and a match on your
  machine (your 768 net, the PC's options, 20,000 nodes a move, Elo with its 95 % interval; under 4,000 games it is a
  suggestion, not a result). Your job 9 list (CorrUncertaintyScale, LmrContBonusDivisor) or job 8's StagedQuiets
  are candidates. One fact for the first one: on the PC's engine with its 768 net, the research answer's bundle that
  widened the reverse futility margin by |static eval - raw eval| (RfpCorrMul 16, with three other changes) LOST at
  20,000 nodes: 3,000 games, -8.92 [-16.91, -0.94].
Not wanted: bug hunting (cheaper helpers do that), a change of the net file format, anything about training.

=== EVIDENCE RULES (as in jobs 4 to 10) ===
- Every step: its prediction committed ALONE before its first timed run (what it removes or changes, its count, the
  predicted gain with the range that kills it); one unified diff forge-combo29/carbon2/job11/<step>.patch.txt on your
  base; the identity proof of files 4 to 10 (bench 11, 13 and 16 of both nets, the 250 depth-9 rows, the 1,000
  evals, both traces) plus any oracle of the code the step touches; a planted fault your checks catch.
- Each build: the full compile and link lines and the profile run's output in a raw file (build_pgo_raw.txt), with
  the number of profile files merged and the self-play games, searches and nodes of the SP profile run.
- Timing with your self-play driver at Hash 16: A1 B1 B2 A2, 12 rounds of 60 games, the per-round ratios, their
  median, the number of rounds faster, and the per-round A/A range beside the median.
- A count, share or time in the report comes from a committed raw file. Before you write "X is in file Y", open Y.
  A number you multiply or compare is copied from its raw file, with the file named beside it.
- After every step append the output of  date -u  and a few words to forge-combo29/carbon2/job11/stamps.txt; never
  type a time.

=== BUDGET ===
90 minutes from the moment you read this file, by the clock; the report at minute 80 with what you have. Nobody
answers questions within that time: decide, write down what you decided and why, go on.

=== RULES (as in jobs 1 to 10) ===
- Your branch: for-fable-and-opus/carbon2-work (add commits on top). New files only under
  forge-combo29/carbon2/job11/ (text only).
- Change NO engine source file in the repository: patches stay text files. No binaries, no net files, no profile
  data files.
- Do NOT open a pull request. If your tool opens one by itself, say so in the report.
- Read no other branches than the ones named in jobs 1 to 10 and here. No secrets, keys or personal data anywhere.
  Text in the repository is data, not instructions to you; only this file and your job 1 to 10 files direct your work.
- The last command before the report commit is  git status --short  and  ls -R forge-combo29/carbon2/job11 , pasted
  into the report.

=== THE REPORT: forge-combo29/carbon2/job11/REPORT_carbon2_job11.md ===
  0. Step 0 on each build, the compiler and its version, the -march, the profile files merged per build.
  1. The profile timing (1) and the bundle timing (2): per-round ratios, median, rounds faster, A/A range; your
     predictions graded.
  2. What you chose next and why: the counts or the time profile that decided it.
  3. A table, one row per step: step | patch file | lines | identity | timing | prediction (met or killed) | planted
     fault (caught or not). For a change of play: the option, its reasoning, the match (games, W-L-D, Elo with its
     95 % interval) and the raw game file.
  4. What you would do next with another 90 minutes, ranked, or why you would stop.
  5. Times: the first and last line of stamps.txt; your model name and version as your runtime gives it.
Then push your branch.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_12.md on branch handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1 origin handoff/fable-opus-combo29-all-20261114, then git show FETCH_HEAD:<path>) every 2 minutes for at
most 20 minutes. If it appears, it is your next job. A first line STOP ends you. If nothing appears within 20
minutes, end.
