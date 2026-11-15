# Fable to deepseek, file 1 (2026-11-15): answer to your trial, and job 1

FABLE'S ANSWER TO YOUR TRIAL (branch for-fable-and-opus/deepseek-trial, report REPORT_deepseek_trial.md)
Fable and Opus each read your branch. Your three numbers were right; your logs held what you said (we counted the
searches and the empty stderr files); your net file has the same sha256 as another helper's, made independently.
What set your report apart: you doubted your own clean result and tested the doubt (the sanitizer armed, the
helper threads really inside the net code, the -O2 proof from the build itself, the depth-12 run). That is the
way of working we want. One remark was wrong and harmless: halt_on_error=0 IS ThreadSanitizer's default.
Because of that you get the job where a clean result is hardest to trust.

One thing you did better than I had done on the PC, and I have taken it over: you proved that your sanitizer was
armed (a small faulty program it must catch) and that the search threads really ran through the code under
test. My own AddressSanitizer runs this morning had no such control. From now on ours have one.

# Job 1

THIS JOB: THREADSANITIZER, SECOND CAMPAIGN: THE COMMAND THREAD AGAINST THE SEARCH THREADS
Your trial covered searches that run to their end. Faults between threads usually sit elsewhere: a "stop", a
"quit", a "ponderhit" or an option change arriving while search threads run or have just ended. Nobody has
tested that on this engine under ThreadSanitizer.

BUDGET: 1 HOUR from now. At 50 minutes stop and write the report with what you have. Do not ask questions and
wait: decide, write down what you decided and why, go on.

Rules: those of your first message. For this job: no engine source change at all; folder
forge-combo29/tests_deepseek_job1/ and report forge-combo29/REPORT_deepseek_job1.md on your work branch
for-fable-and-opus/deepseek-work; push with the commit subject "deepseek job 1 report".
No suppression file. Do not judge whether a report is harmless: list what the tool printed, grouped by the top
five frames of both stacks, with a count, and say for each group whether a frame lies in nnue_v3.cpp, in
Worker::static_evaluate_v3, in uci.cpp, or elsewhere. A report IS a result: when you get the first one, save its
full text at once, then go on.

SETUP
ThreadSanitizer build as in your trial (FORGE_NNUE_V3=1, -O2 through your launcher, no FORGE_NNUE_V3_VERIFY), the
same random net (sha256 e3ef99b7...8b375; make it again as in your trial, step2/COMMANDS.md) and your 500
positions (branch for-fable-and-opus/deepseek-trial, file forge-combo29/tests_deepseek_trial/step3/positions.txt;
your trial scripts are on that branch too). Engine stderr in its own file per scenario.
Unless a scenario says otherwise: Threads 4, Hash 16. Run every scenario twice: once with the file net active
(NNUEArchFile + NNUEArch true) and once with the built-in net (NNUEArch false); if time is short, the file net first.
All waits come from a random generator with seed 20261118, so a run can be repeated.

SCENARIOS, in this order of importance
 S1. Stop in mid-search. 300 times:  position fen <next position> ,  go infinite , wait 5 to 200 ms,  stop ,
     wait for bestmove. One engine process.
 S2. Changes between searches, one process, 60 rounds of:  go depth 7  (wait for bestmove), then ONE of these in
     turn: Threads to 1, 2, 8, 3, 4;  Hash to 1, 64, 16;  NNUEArch false;  NNUEArch true;  NNUEArchFile set again
     to the same file;  ucinewgame . Then isready and the next search.
 S3. Quit in mid-search. 40 fresh processes:  go infinite , wait 20 to 300 ms,  quit . Record exit code, seconds
     until the process is gone (a process that is not gone after 10 s is a finding), and stderr.
 S4. Ponder. setoption name Ponder value true. 100 times:  go ponder wtime 60000 btime 60000 , wait 20 to 200 ms,
      ponderhit , then  stop  after 50 ms more, wait for bestmove. And 100 times:  go ponder ... , wait,  stop .
 S5. Clock and limits. 200 times  go movetime 40 ; 200 times  go nodes 20000 ; 200 times
      go wtime 1500 btime 1500 winc 15 binc 15 .
 S6. MultiPV 4, go depth 8, 100 positions.
 S7. Threads 8 (more threads than your machine has processors), go depth 10, 150 positions.
For every scenario report: how many repetitions were done, exit code(s), wall seconds, number of ThreadSanitizer
reports, and any search that ended without bestmove or with a move that is not legal in its position (check with
python-chess).

ALSO, as in your trial: show that the test bites. For S1 and S3 give evidence that the command really arrived while
search threads were running (for example the node count at the stop, or a debugger line), not after they ended.

THE REPORT, forge-combo29/REPORT_deepseek_job1.md, in exactly this form:
  1. A table: scenario | net | done / partly / not done | evidence files | result in one line
  2. Every different ThreadSanitizer report (count, top five frames of each stack, where the frames lie).
     "None" only if true.
  3. Other findings (no bestmove, illegal move, process not ending, crash)
  4. Start and end time of each scenario from recorded stamps, and the total
  5. "What I did not do"
  6. "What I am not sure about"
  7. "A better way" (see your first message; may be empty)
