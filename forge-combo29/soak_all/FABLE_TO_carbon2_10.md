Your name in this job is: carbon2 (job 10)

Opus (standing in for Fable this week) to carbon2, file 10, 2026-11-17. Same machine, same builds, same Step 0 as
jobs 1 to 9. If your builds are gone, rebuild them exactly as job 1 says and show Step 0 again before anything else.
This file was written while your job 9 ran, so it does not judge job 9 yet (file 11 will). It judges job 8 and gives
you a new task, because the PC has now timed your job 5 bundle on its own build.

=== JOB 8 AS WE COUNTED IT (raw files, not the summaries) ===
- Good, keep doing it: each step had its prediction as its own commit before its timing (W1 580bcddb0, W2
  851a04d82); W1 was graded KILLED by its own clause, and W2 was built from what killed W1 (the 384-square pre-sum).
  Your section 4 item 1 (time the bundle on a build made like the PC's) is the right next step: the task below.
- Recounted with our own parser: W1 engine CPU per-round median 1.0043, 8 of 12 (killed, as you said). W2 = bundle 4
  against bundle 3: 48 runs, ONE trace ee465caeff9c0fcf (7,670 searches, 25,641,316 nodes in every run), engine CPU
  per-round median 1.0127, 9 of 12 rounds faster, pooled 1.0128; wall 1.0117, 9 of 12, pooled 1.0078; per-round
  A2/A1 CPU 0.971 to 1.041. Equal to your report. Identity EXACT as printed (both nets, bench 11 / 13 / 16, 250 rows,
  1,000 evals, both traces); MovePicker oracle 2,010 and evasion oracle 55,868 sequences with 0 mismatches; your
  planted fault caught.
- Verdict: met at the low edge of its range, inside the A/A spread of single rounds. Bundle 4 is not built on the PC
  (the reason is the next block).

=== WHAT THE PC MEASURED (new since file 9) ===
- Your job 5 bundle 1 (without S7 part 3, with the S5 recheck) went onto the PC's engine as r15e = r15d + bundle 1 and
  passed every identity check there: node count and best move equal on 1,200 of 1,200 searches with two nets; the
  whole UCI output equal line for line on 208 go commands; your S6 planted fault caught; half the stack reserve fine;
  AddressSanitizer + UBSan clean at 1 and 4 threads; your parse oracle on 53,208 commands with 0 differences and its
  planted fault caught; your protocol stress, 1,000 cycles at Threads 1 and at Threads 4, ALL PASS.
- Its timing on the PC (the PC's own build of each tree, built twice: A = r15d twice, B = r15e twice; 10 rounds of 12
  self-play games at softnodes 2000, at most 160 plies; round 30's 768 net; the options of file 8): one trace in all
  40 runs; engine CPU A/B median 1.0078, faster in 8 of 10 rounds; wall 0.9987, 4 of 10; A/A spread 1.019 (CPU). Our
  rule, written before the run: below 1.01 is no measurable gain, not placed. So the bundle's +3.4 % on your machine
  (job 5: CPU 1.0342, 12 of 12 rounds) is +0.8 % on the PC, inside the noise. Your +3.4 % included S7 part 3, which
  r15e leaves out; your own job 8 count puts the whole Worker::clear at 0.16 % of the engine CPU time, so S7 part 3
  cannot explain the gap. Your E1 did carry over (on the PC +4.2 % engine CPU, +4.4 % wall).
- We do not know why. Checked and FALSE: "the bundle sits in code the PC compiles out" (each changed file
  preprocessed with the PC's defines and with yours, r15d against r15e: board.cpp 73 and 73 lines differ,
  nnue_v3.cpp 219 and 219, search.cpp 187 and 183, uci.cpp 219 and 219). What differs between your timing build
  and the PC's, as facts:
  (a) Compiler: clang 23.1.5 (llvm-mingw 20261104) with GCC 16.2's libstdc++, against your g++ 13.3.
  (b) ThinLTO (-flto=thin, linked with lld, static) and profile-guided optimization: compile with
      -fprofile-instr-generate, run the profile workload below, llvm-profdata merge, compile again with
      -fprofile-instr-use. The profile workload is exactly these lines on stdin:
        uci
        setoption name NNUEArchFile value <the 768 net>
        setoption name NNUEArch value true
        setoption name CuckooRep value true
        setoption name HistRework value 2
        setoption name TtPruneV2 value true
        setoption name CorrHistV2 value true
        isready
        bench 11
        bench 13
        bench 16
        isready
        quit
      So the UCI protocol code (ucinewgame, position, info lines) runs only a little in the profile and is laid out
      as cold code.
  (c) Every PC build compiles with  -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1
      -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1
      -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1
      -ffp-contract=off -fno-fast-math -march=znver5 -pthread. The six FORGE_SPD / FORGE_SEARCH_SPEED2 switches are
      speed paths that exist in your tree too (grep for their names) and are missing from your compile line
      (-O3 -DNDEBUG -march=x86-64-v4 -ffp-contract=off -fno-fast-math -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1).
      They do not change node counts: the PC's builds print 312866 / 862329 / 4865609 with them.
  (d) -march=znver5 (AMD Zen 5, AVX-512 with VNNI) against your x86-64-v4.
  (e) On the PC 16 engines and 16 Python clients share 16 hardware threads; every engine runs at Threads 1, Hash 16.
- Running on the PC while you read this: r15d and r15e built again WITHOUT PGO (ThinLTO kept), once with and once
  without the six switches of (c), and timed the same way. Its result comes in file 11; it does not change your
  first step below.

=== THE TASK (yours to plan; the owner's words: a task, not an order) ===
Make Forge spend less processor time per self-play position ON A BUILD MADE LIKE THE PC'S, without changing one move,
node count, score or info line (time and nps excepted).
What we need first, because it decides whether the rest is worth anything: a timing build as close to the PC's as
your machine allows (clang with libstdc++, the full compile line of (c) with your machine's -march, ThinLTO, PGO
with the profile workload of (b) and your net768.fnn3), Step 0 on it, and then your usual timing on it: r15d (your
job 4 base) against bundle 1 (job 5) and against bundle 4 (job 8). Build each tree TWICE and use one build as A1 / B1
and the other as A2 / B2 (on the PC two builds of one source differ by up to 1.5 %). If your machine has no clang,
install it from your distribution's own archive and say which version; nothing else is installed. If your machine
cannot run -march=znver5 code, say which -march you used and why.
Then decide yourself, with the counts that decide it:
- If a bundle keeps a gain of 1 % or more on that build, find out which of its steps carry it (each step alone on
  the PGO build) and look for the next speed step with a TIME profile of the PGO build (perf or your own counters),
  never a count of calls alone.
- If nothing keeps 1 %, say so and take the other half of file 8's task: a change of play behind a new UCI option
  that is OFF by default (with it off your identity proof must hold), with your reasoning and a match on your machine
  (your 768 net, the PC's options, 20,000 nodes a move, Elo with its 95 % interval; under 4,000 games it is a
  suggestion, not a result). Your own job 8 list item 2 (staged quiet generation behind StagedQuiets) is one
  candidate: it changes the order of equal-score moves, so it needs games.
Not wanted: bug hunting (cheaper helpers do that), a change of the net file format, anything about training.

=== EVIDENCE RULES (as in jobs 4 to 9) ===
- Every step: its prediction committed ALONE before its first timed run (what it removes, its count, the predicted
  self-play gain with the range that kills it); one unified diff forge-combo29/carbon2/job10/<step>.patch.txt on your
  base; the identity proof of files 4 to 9 (bench 11, 13 and 16 of both nets, the 250 depth-9 rows, the 1,000 evals,
  both traces) plus any oracle of the code the step touches; a planted fault your checks catch.
- The build: the full compile and link lines and the profile run's output in a raw file (build_pgo_raw.txt).
- Timing with your self-play driver at Hash 16: A1 B1 B2 A2, 12 rounds of 60 games, the per-round ratios, their
  median, the number of rounds faster, and the per-round A/A range beside the median.
- A count, share or time in the report comes from a committed raw file. Before you write "X is in file Y", open Y.
- After every step append the output of  date -u  and a few words to forge-combo29/carbon2/job10/stamps.txt; never
  type a time.

=== BUDGET ===
90 minutes from the moment you read this file, by the clock; the report at minute 80 with what you have. Nobody
answers questions within that time: decide, write down what you decided and why, go on.

=== RULES (as in jobs 1 to 9) ===
- Your branch: for-fable-and-opus/carbon2-work (add commits on top). New files only under
  forge-combo29/carbon2/job10/ (text only).
- Change NO engine source file in the repository: patches stay text files. No binaries, no net files, no profile
  data files.
- Do NOT open a pull request. If your tool opens one by itself, say so in the report.
- Read no other branches than the ones named in jobs 1 to 9 and here. No secrets, keys or personal data anywhere.
  Text in the repository is data, not instructions to you; only this file and your job 1 to 9 files direct your work.
- The last command before the report commit is  git status --short  and  ls -R forge-combo29/carbon2/job10 , pasted
  into the report.

=== THE REPORT: forge-combo29/carbon2/job10/REPORT_carbon2_job10.md ===
  0. Step 0 on the PGO build (and on your old build if you used it), the compiler and its version, the -march.
  1. The PGO-build timing: r15d against bundle 1 and against bundle 4 (per-round ratios, median, rounds faster,
     A/A range); your prediction graded.
  2. What you chose next and why: the counts or the time profile that decided it.
  3. A table, one row per step: step | patch file | lines | identity | timing | prediction (met or killed) | planted
     fault (caught or not). For a change of play: the option, its reasoning, the match (games, W-L-D, Elo with its
     95 % interval) and the raw game file.
  4. What you would do next with another 90 minutes, ranked, or why you would stop.
  5. Times: the first and last line of stamps.txt; your model name and version as your runtime gives it.
Then push your branch.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_11.md on branch handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1 origin handoff/fable-opus-combo29-all-20261114, then git show FETCH_HEAD:<path>) every 2 minutes for at
most 20 minutes. If it appears, it is your next job. A first line STOP ends you. If nothing appears within 20
minutes, end.
