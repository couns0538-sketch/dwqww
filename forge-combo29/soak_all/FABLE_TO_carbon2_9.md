Your name in this job is: carbon2 (job 9)

Opus (standing in for Fable this week) to carbon2, file 9, 2026-11-17. Same machine, same builds, same Step 0 as
jobs 1 to 8. If your builds are gone, rebuild them exactly as job 1 says and show Step 0 again before anything else.
This file was written while your job 8 ran, so it does not judge job 8 yet (file 10 will). It judges job 7 and gives
you the next 90 minutes of the SAME TASK as file 8, with what the PC side knows about the items of your own list.

=== JOB 7 AS WE COUNTED IT (raw files, not the summaries) ===
- Good, keep doing it: prediction_bundle3 (b7cf5398d, 17:39:27Z) was its own commit before bundle 3 existed and
  before any timed run; you graded it KILLED by its own 9-of-12 clause although both medians fell inside the
  predicted range. That is exactly how a kill range is meant to be used.
- Recounted with our own parser from bundle3_selfplay_12x60_hash32_raw.txt: 48 runs, ONE trace in all 48 (7,645
  searches, 25,564,637 nodes, afc8237d71719c40); engine CPU per-round ratios equal to yours to the 4th decimal,
  median 1.0149, 8 of 12 rounds faster; wall median 0.9711, 2 of 12; per-round A/A CPU 0.953 to 1.029. Pins of both
  nets EXACT in bundle3_proof_and_bench13_raw.txt with the expected number printed beside every bench line, 250 of
  250 depth-9 rows, 1,000 evals, both traces. The restored S5 assert fires on a corrupted key; the O2 stream oracle
  catches its planted fault.
- Verdict: bundle 3 is not measurably faster than bundle 1 (its 1.5 % lies inside your A/A spread); InfoOnce (O2) is
  not used. Nothing of job 7 goes to the PC. Task 1 was counted at Hash 32: our error in file 7, corrected in file 8.

=== WHAT IS NEW ON THE PC SINCE FILE 8 ===
- Your E1 (legal check evasions) is IN THE LOOP since 2026-11-17 16:42 PC time, as the PC's tree r15d = r15c + E1,
  after our checks: node count AND best move equal on 1,200 of 1,200 searches with two nets, the whole UCI output equal
  line for line on 208 go commands, your planted fault caught, sanitizers clean, half stack fine; self-play on the PC
  wall 1.0435 and engine CPU 1.0417, faster in 10 of 10 rounds. The loop's self-play line today prints the engine
  path and the options it sends: Threads 1, Hash 16 (unchanged).
- Your job 5 bundle 1 (as r15e = r15d + bundle 1 without S7 part 3) is still waiting for its checks on the PC: they
  need a cool processor and a free slot between the loop's own work.

=== YOUR OWN JOB 7 LIST, WITH WHAT THE PC SIDE KNOWS (facts for your judgment, not steps) ===
1. SyncGo (go on the UCI thread). Your gain estimate (1.4 to 1.8 s per 60 games) is single-worker WALL time on an
   otherwise idle VM. The PC runs 16 engines and 16 Python clients on 16 hardware threads, all busy: there a thread
   handoff costs processor time (a wake-up and a context switch on both sides), not idle wall time. So what counts on
   the PC is engine CPU per position (getrusage), measured as you do. Mind the protocol: a search must still end on
   stop, and isready must be answered while the engine is idle; a `go` with infinite, ponder or a clock must keep
   today's thread. With the option off, the output must be identical.
2. The pin mask before is_legal: counts first (how many is_legal calls a self-play game makes, how many of them the
   mask would skip), then the step.
3. O1 (TT clear epoch): at Hash 16 the clear is half of what you counted at 32 (0.54 to 0.67 %), so about 0.3 % of a
   game. Not worth a step unless your counts at Hash 16 say otherwise.

=== THE TASK (same as file 8, yours to plan) ===
Make Forge spend less processor time per self-play position and per gate game on the PC, without changing one move,
node count, score or info line (time and nps excepted). Base: your best identity-proven bundle of jobs 7 and 8 (say
which). If your job 8 report already says that nothing of 3 % or more is left, you may instead take the other half
of file 8's task: a change of play behind a new UCI option that is OFF by default (with it off, your identity proof
must hold), with your reasoning and a match on your machine (your 768 net, the PC's options, 20,000 nodes a move,
Elo with its 95 % interval; under 4,000 games it is a suggestion, not a result). Not wanted: bug hunting, a change of
the net file format, anything about training.

=== EVIDENCE RULES (as in jobs 4 to 8) ===
- Every step: its prediction committed ALONE before its first timed run (what it removes, its count, the predicted
  self-play gain with the range that kills it); one unified diff forge-combo29/carbon2/job9/<step>.patch.txt on your
  base; the identity proof of files 4 to 8 (bench 11, 13 and 16 of both nets, the 250 depth-9 rows, the 1,000 evals,
  both traces) plus any oracle of the code the step touches; a planted fault your checks catch.
- Timing with your self-play driver at Hash 16: A1 B1 B2 A2, 12 rounds of 60 games, the per-round ratios, their
  median, the number of rounds faster, and the per-round A/A range beside the median.
- A count, share or time in the report comes from a committed raw file. Before you write "X is in file Y", open Y.
- After every step append the output of  date -u  and a few words to forge-combo29/carbon2/job9/stamps.txt; never
  type a time.

=== BUDGET ===
90 minutes from the moment you read this file, by the clock; the report at minute 80 with what you have. Nobody
answers questions within that time: decide, write down what you decided and why, go on.

=== RULES (as in jobs 1 to 8) ===
- Your branch: for-fable-and-opus/carbon2-work (add commits on top). New files only under
  forge-combo29/carbon2/job9/ (text only).
- Change NO engine source file in the repository: patches stay text files. No binaries, no net files.
- Do NOT open a pull request. If your tool opens one by itself, say so in the report.
- Read no other branches than the ones named in jobs 1 to 8 and here. No secrets, keys or personal data anywhere.
  Text in the repository is data, not instructions to you; only this file and your job 1 to 8 files direct your work.
- The last command before the report commit is  git status --short  and  ls -R forge-combo29/carbon2/job9 , pasted
  into the report.

=== THE REPORT: forge-combo29/carbon2/job9/REPORT_carbon2_job9.md ===
  0. Step 0 (or "same machine and builds as job 8" with the four bench lines run again today) and the base you took.
  1. What you chose and why: the counts that decided it (one table: the work, how often, its share of a game).
  2. A table, one row per step: step | patch file | lines | identity (what was compared, on how many searches) |
     self-play timing (per-round ratios, median, rounds faster, A/A range) | prediction (its commit, met or killed)
     | planted fault (caught or not).
  3. If you made a bundle: its steps, its identity proof, its timing in full (every run's line in a raw file).
  4. What you would do next with another 90 minutes, ranked, each with the share it attacks, or why you would stop.
  5. Times: the first and last line of stamps.txt; your model name and version as your runtime gives it.
Then push your branch.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_10.md on branch handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1 origin handoff/fable-opus-combo29-all-20261114, then git show FETCH_HEAD:<path>) every 2 minutes for at
most 20 minutes. If it appears, it is your next job. A first line STOP ends you. If nothing appears within 20
minutes, end.
