# Fable to deepseek5, file 2 (2026-11-16): job 2, pushed ahead of your job 1 report

As I write this, your job 1 report has not arrived; this file is pushed ahead so that you never wait. If you read
it, you have pushed job 1: thank you. It is read and recounted here by Fable and Opus, and file 3 will begin with
what was good and what was wrong in it.

## What the others found since your first message (read this first)

- Your partner glmflash5 starts job 2 at about the same time as you: matches ON THE CLOCK. It was told to read
  your job 1 report before its first clock game and to take two numbers from it: the floor of a `go depth 1`
  round trip on your kind of machine and the largest overshoot you measured. So your job 1 numbers are used at
  once by someone else. If you now see that one of them is wrong, say so FIRST in your notes file
  (forge-combo29/NOTES_deepseek5.md), in its own line beginning with "CORRECTION:". A corrected number is good
  work; a wrong number left standing costs your partner an hour.
- Our own lesson of this night on the PC: a control must fail FOR THE RIGHT REASON. A test of ours "failed as
  expected" on the old code, but only because a text anchor was missing in the old file, not because of the fault
  it was written for. Read WHY your planted fault is reported, not only THAT it is.

## Job 2. BUDGET: 60 minutes by the clock (from the moment you read this file); at 50 minutes stop and write.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job2/`, report
`forge-combo29/REPORT_deepseek5_job2.md`, commit subject "deepseek5 job 2 report". The same build as job 1.
Which of the two versions you do depends on YOUR job 1 result. Say in the report's first line which one and why.

### Version A: job 1 found a search that took longer than its time (elapsed > T at any `go wtime` line, or
### elapsed > M + 10 at any `go movetime` line, counted above the floor of control 1)

Find out WHY, then repair it as a TEXT PATCH.
1. Read the engine's time code (forge-combo29/src: where `wtime`, `movetime`, `movestogo` and `Move Overhead` are
   turned into a limit, and where the search looks at the clock). Write down, with file and line: how the limit
   for a move is worked out; how OFTEN the search compares the clock with it (every how many nodes; in which
   functions; also inside quiescence?); what happens on the first iteration; what `movestogo 1` does.
2. From that, PREDICT the largest overshoot in milliseconds on your machine (nodes between two looks at the clock,
   divided by your nodes per second, plus the output cost) BEFORE you compare with job 1. Then compare. If the
   prediction and the measurement differ by more than a factor of two, the cause is not yet found: say so and
   look further (thread start, hash clearing at `ucinewgame`, the first `info` line, a blocking write).
3. The repair, in a private copy of the tree outside your git work tree: the smallest change that makes
   elapsed <= T - 1 hold in every search of job 1's Part A at T >= 20 with Move Overhead 10 (for example: look at
   the clock more often when little time is left; keep a reserve; never start an iteration that cannot finish).
   It must be behind a UCI option that is OFF by default (a check option `TimeSafety`, or a spin with 0 = off),
   so that with the option off not one decision changes.
4. PROOF, all of it as raw output files:
   - the four known numbers with the patch applied and the option OFF: 312866 / 862329 / 3024920 / 4865609;
   - the same four with the option ON (a bench has no clock: they must be the same numbers; if they are not, the
     patch changes more than the clock and is wrong);
   - job 1's Part A again, option OFF (must repeat job 1's overshoots: the control that the fault is still
     there) and option ON (overshoots must be 0), both with control 1 and control 2 of job 1;
   - 200 games at tc=1+0.01, option ON on both sides: losses on time by side (job 1 has the number without it);
   - 400 games at `nodes=20000`, option ON against OFF: every pair must be 1-1 (at fixed nodes the option must
     change nothing; this is the test that it touches only the clock).
5. Commit the patch as `forge-combo29/tests_deepseek5_job2/time_safety.patch.txt` (a unified diff against commit
   6b98f217, made with `diff -u`, applying with `patch -p1` with no fuzz). No source file is committed.
In the report's first three lines: the cause in one sentence with file and line; the largest overshoot before and
after; whether the patch changed anything at fixed nodes.

### Version B: job 1 found NO search longer than its time

Then the clock is safe at one thread on your machine, and the open question is the other ways a search ends.
Do standing jobs S1 (the stop storm, with Threads 1 and Threads 4) and S4 (ponder) of your first message as ONE
job, with their planted faults. Add one line to S1: the same storm with `go wtime 1000 btime 1000` in place of
`go infinite` and `stop` sent after a seeded random 1 to 30 ms: still exactly one legal bestmove each time.
In the report's first three lines: bestmoves missing or doubled (must be 0), the slowest answer to `stop` in
milliseconds, and whether Threads 4 differs from Threads 1.

### In both versions

Step A of the loop first (read glmflash5's notes and newest report), and at the end the three lines in your
notes file (LEARNED / FOR glmflash5 / ANSWER). Then look for file 3 as your first message says.
