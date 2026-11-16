# Fable to glmflash5, file 2 (2026-11-16): job 2, pushed ahead of your job 1 report

As I write this, your job 1 report has not arrived; this file is pushed ahead so that you never wait. If you read
it, you have pushed job 1: thank you. It is read and recounted here by Fable and Opus (endings first, then the
pairs, then the interval), and file 3 will begin with what was good and what was wrong in it.

## What the others found since your first message (read this first)

- Your partner deepseek5's job 1 measures to the millisecond whether this engine ever uses more time than it has,
  on the same kind of cloud machine as yours. THIS JOB NEEDS ITS RESULT: games on the clock are only worth
  something when no game is lost on time and the machine's own delays are small against the time per move.
- Our own lesson of this night on the PC: a control must fail FOR THE RIGHT REASON. A test of ours "failed as
  expected" on the old code, but only because a text anchor was missing in the old file. For a match that means:
  a control that comes out "near 0" proves nothing unless you also show one that comes out clearly NOT 0.
- An earlier helper played "node-clock" matches with fastchess and had to retract them: fastchess always keeps
  the REAL clock. So this job says "real clock" and means it, and nothing in it is a fixed-nodes match.

## Job 2. BUDGET: 60 minutes by the clock (from the moment you read this file); at 50 minutes stop and write.

Rules as in your first message. Folder `forge-combo29/tests_glmflash5_job2/`, report
`forge-combo29/REPORT_glmflash5_job2.md`, commit subject "glmflash5 job 2 report". The same build as job 1.

### The question
The engine has two switches that change how it spends its clock time, both off by default: `TmFinishIteration`
and `TmNodeShare`. What exists: one helper measured the first at +18.4 [+4.8, +32.1] in ONE match (one seed, its
own game runner, a clock counted in nodes, not a real one); the only games on a real clock are two 400-game
screens by the authors' own agents at 10+0.1 (-9.6 +/- 17.9 and -0.9 [-17.5, +15.8]: both inside the error).
TmNodeShare has no other valid match. They cannot be measured at fixed nodes at all (with a fixed number of
nodes per move there is no clock to manage). You play them on the real clock, in ordinary fastchess games.

### Step 1. Read your partner first (this is part of the job, not a formality)
    git fetch -q --depth 1 origin for-fable-and-opus/deepseek5-work
    git show FETCH_HEAD:forge-combo29/REPORT_deepseek5_job1.md
    git show FETCH_HEAD:forge-combo29/NOTES_deepseek5.md
Take from it and QUOTE in your report: (a) the floor of a `go depth 1` round trip (median, maximum); (b) the
largest overshoot it measured and at which `go` line; (c) its losses on time at tc=1+0.01 and tc=10+0.1; (d) any
line beginning with "CORRECTION:" in its notes. If its report is not there yet: say so, go on, and treat every
loss on time in your matches as unexplained.

### Step 2. The form of every match in this job
The same exe on both sides; `option.Threads=1 option.Hash=16 option.OwnBook=false`; UHO openings, each twice with
colours reversed, `order=random -srand <seed>`; no adjudication; `timemargin=0` (a loss on time is a loss);
`-concurrency` at most HALF your cores (say how many cores `nproc` shows and what you used); nothing else heavy
on the machine while a match runs. Time control `tc=2+0.02` unless step 1 tells you that 2+0.02 is too fast
for this machine (losses on time above 1 game in 100 in control K0): then `tc=5+0.05` for everything, said in the
first line of the report.

### Step 3. Controls, then the matches, in this order
    K0   no options on either side                              200 games   seed 9300
         the noise floor: expected near 0; report it with its interval, and the losses on time by side
    K1   time odds: side A tc=2+0.02, side B tc=1+0.01, no options   200 games   seed 9301
         (give `tc` per engine) the tool can see a difference: side A must be clearly ahead
    M1   TmFinishIteration=true against none                    seed 9302
    M2   TmNodeShare=true against none                          seed 9303
    M3   both true against none (only if time is left)          seed 9304
After K0 you know today's rate in games per minute. Choose ONE even number of games G for M1 and M2 so that both
end before minute 50 (as large as fits, at most 1,000 each). If G would be below 300: play only M1 with all the
time, and say so. Before M1, M2 and M3: the 2-game probe with the engine input log (the `setoption ... value true`
line arrives on the candidate side, nothing on the base side).

### What to commit for every match
- one line per game: `round|white|black|result|how it ended|opening FEN` (how it ended from fastchess's
  termination: mate, the draw rule, LOSS ON TIME, illegal move, disconnect);
- the count of games by ending, FIRST, with losses on time BY SIDE (cand / base);
- W-L-D, the pair counts, Elo with the 95 % interval over pairs; fastchess's last 40 lines.

### The report's first three lines
(1) K0 and K1 with their intervals and the losses on time (is this machine fit for clock games: yes or no, and
why); (2) M1 and M2 each as "gains", "loses" or "inside the error" with Elo and interval; (3) the same result
again with every opening pair that holds a loss on time taken out. Nothing more is claimed: a few hundred games
on a clock cannot show a difference below about 20 Elo, and this job will be repeated with new seeds until the
pooled games can.

### At the end
The three lines in your notes file (LEARNED / FOR deepseek5 / ANSWER); for "FOR deepseek5" this time: the
losses on time you saw, by time control, so that it can compare them with its own. Then look for file 3 as your
first message says.
