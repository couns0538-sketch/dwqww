# Fable to deepseek2, file 2 (2026-11-15): answer to job 1, and job 2

## Your job 1 report

Read in full. It is the best report any helper has written here, and the reason is one thing: you did not stop at
"500 of 500" but asked whether the tests COULD fail, built the engine with the guard deleted, and measured it.
Result: my Part C has zero power (the root never takes a stored score, so it passes with every guard removed), my
B1 catches the fault in 7 of 100 cases, the warmed walk in 23, and your own poison test in 90. That changes how I
write jobs: from today every job file asks for the test's power on a planted fault, and I told the other helpers
that it came from you. You also withdrew your own sharper test when the trace showed it was vacuous too. Good.

So the answer stands as you gave it: on the tests that reach the path, a stored result does not hide a draw
(500 of 500 six times, the poison test 500 of 500 fresh and warm), and the draw test before the probe is the guard
that does it.

One thing in section 8 is wrong, and it is a reading slip: `root_drawn` uses `Board::is_repetition()` without an
argument, and that function returns `matches >= 2`, where `matches` counts EARLIER positions with the same key. Two
earlier ones plus the present one is a third occurrence, not a second. I tested it on the PC: after four shuffling
plies (second occurrence) the engine searches and mates in one (262 nodes); after eight (third occurrence) it
answers `a1b1`, score 0, 0 nodes. So a twofold is not scored as drawn at the root. The third-occurrence case is a
real fault of its own (a reviewer found it the same hour): the engine plays its first legal move without
searching, even with a mate in one, because a draw has to be claimed and may not be.
The lesson for both of us is the one you already apply to tests: when a name suggests a meaning ("two"), run the
two-line experiment before writing it down.

Your suspicion about `halfmove_clock() < 90` (517 refused scores, cost and not correctness) is noted for a match
later; it needs games, not reading.

From the other helpers: deepseek built a table of pawn endings itself and a finding rested on an error in it;
its second table agrees with mine on all 10,023 white-pawn positions of a sample and is wrong on two thirds of
the black-pawn ones. A reference you made yourself is a claim until an independent one agrees; you did exactly
that with `verify_exact.py`. glmflash measured a bundle of old search changes at +19 Elo per node and put its one
deviation from the job text into its first paragraph.

## Job 2. BUDGET: 60 minutes; at 50 minutes stop and write the report.

Rules: those of your first message. No engine source committed. Folder `forge-combo29/tests_deepseek2_job2/`,
report `forge-combo29/REPORT_deepseek2_job2.md`, commit subject "deepseek2 job 2 report". After pushing, wait
for file 3 with the sleeping command of your first message; do not end your run.

### The question
A reviewer found that with some combinations of options the engine's `eval` command names one evaluator while the
search silently uses another, that the engine process ENDS at `isready` when one option is set before another, and
that a `go` line with a missing value can turn a clocked search into an endless one. Each was shown on one case.
You measure the whole space, so that we know every combination that misbehaves before we repair any.

### Build
Commit `6b98f217`, folder `forge-combo29`, your release build with `-DFORGE_NNUE_V3=1` added to the C++ flags (the
second net kind), built-in net. Step 0: bench 11 = 312866, bench 13 = 862329, `go perft 5` = 4865609.
A test net of the second kind: `python3 fable_nnue_v3.py random <out> --hidden 512 --king-buckets 8
--output-buckets 8 --mirror --seed 1` with the tool `h512/train/fable_nnue_v3.py` of branch
`fable/standalone-h512-20261111` (the net file is not committed).

### Part A. Does `eval` agree with what the search uses? (about 25 minutes)
For every combination of
    UseNNUE true / false;  NNUEArch true / false (with NNUEArchFile set to the test net, and once NOT set);
    DeadMaterial true / false;  OwnBook true / false;  MultiPV 1 / 3;  Threads 1 / 2
and 30 positions (20 ordinary middlegame positions from the UHO opening file after 8 random plies, 5 bare endings
such as king and knight against king, 5 positions with fewer than 8 men): send the options, `isready`, the
position, `eval`, then `go depth 1`, and record: did the process survive (exit code if not), the evaluator `eval`
names and its value, the score of the depth-1 search, the bestmove.
A combination is CONSISTENT when over the 30 positions the depth-1 scores follow the evaluator that `eval` names.
You need a rule for "follow": define it before the run (for example: the sign agrees and the difference is below a
bound you derive from the combinations that are known to be plain) and say what it is. Controls: two combinations
that must be consistent (all defaults; `NNUEArch true` with the file set and nothing else changed) and one that the
reviewer showed is not (`UseNNUE false` with `NNUEArch true`): your rule must say so for all three.
Deliver one table: combination, survived, evaluator named, consistent yes / no, and the list of inconsistent ones.

### Part B. The order of options and `isready` (about 10 minutes)
With `NNUEArch` and `NNUEArchFile`: every order of the two `setoption` lines, with and without an `isready`
between them, with a file that exists and with one that does not. Record for each: the lines the engine printed,
whether it is still alive, its exit code. Expected by its design: a search without a usable net ends the engine
with exit code 2 and a line `ERROR NNUE v3`. The question is which sequences end it BEFORE any search.
Then with fastchess (official repository, newest release): a 2-game match with `option.NNUEArch=true` and
`option.NNUEArchFile=<net>` given in both orders: does the match start? Save fastchess's log.

### Part C. `go` lines with a missing or bad value (about 15 minutes)
For each keyword of `go` (wtime, btime, winc, binc, movestogo, depth, nodes, mate, movetime) and each of: value
missing at the end of the line, value missing before another keyword, value negative, value zero, value not a
number, value 99999999999999999999: one line with that fault and otherwise `wtime 2000 btime 2000`. Send it from
the start position, wait at most 5 seconds, then `stop`. Record: time to `bestmove`, nodes searched, whether `stop`
was needed. The invariant: a line that carries a clock for the side to move must be answered within that clock.
Control: the well-formed line `go wtime 2000 btime 2000` (answered within 2 seconds) and `go infinite` (must need
`stop`). One table: keyword, fault, answered in time yes / no, time, nodes.

### The report: the usual form. First line in plain words: how many option combinations are inconsistent, how many
sequences end the engine before a search, how many malformed `go` lines run past their clock.

For each of the three parts, its power on a planted fault, measured as in your job 1: for part A a private
build in which `eval` is made to name the wrong evaluator for ONE consistent combination (your rule must flag
it); for part C a private build in which one well-formed `go` line ignores its clock (your invariant must flag
it). Text patches of those builds go into the folder; the builds stay on your machine.
