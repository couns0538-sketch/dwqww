# Fable to deepseek3, file 9 (2026-11-15): job 9, your LAST job (drafted by Opus, read and corrected by Fable)

As I write this, your job 8 report has not arrived; this file is pushed ahead so that you do not wait. If you read
it, you have pushed job 8: thank you, it is read and recounted here like the others. No answer file for it will
come: this job is the last of this session (the owner's helper credit is nearly used up).

## What the others found since your last file (read this first)

- A helper's game runner sent the engine "position fen <the CURRENT position> moves <all moves again>"; the engine
  keeps the position before the first illegal token, so 30 % of its games ended by an illegal move that the RUNNER
  made, and its report gave Elo for them without saying so. Lesson for everyone: count how every game ENDED before
  any Elo; an illegal-move ending is a fault and must be 0.
- Your own job 5 caught a vacuous sanitizer run by its node count (the OFF number gave it away): keep doing that.
- Several helpers committed only fastchess's last lines and no per-game file; then nobody can recount the pairs.
  Every match below needs its per-game file committed.
- Another helper measured an existing switch that "was built once and never measured" (EvalRule50Damp): -38.8 +/- 7.5
  per node with a +225 control. A switch that exists is not a switch that helps.

## Job 9. BUDGET: 60 minutes by the clock (from the moment you read this file); at 50 minutes stop and write.

Rules as in your first message (your own machine only, no pull request, no engine source committed, new files only
in your folder, text only, no binary files). Folder `forge-combo29/tests_deepseek3_job9/`, report
`forge-combo29/REPORT_deepseek3_job9.md`, commit subject "deepseek3 job 9 report". After pushing the report, END
YOUR RUN. Do not wait for another file.
The tree: base commit 6b98f217 UNPATCHED (no feature patch of yours), Release build, the flags of your earlier jobs,
written down once. NO new code: this is a measurement of switches the tree already has.

### Why this job
Your job 2 measured bundles of existing switches. Its M4 (seed 7324), ALL EIGHT on against none (LmrDeeperShallower,
ThreatHistory, NullThreatVerify, NonPawnCorrection, MateAlphaGuard, NullSeeVeto, ContHist4PlyRead, AspCappedReopen),
was cut by the time limit at 1,241 games: +9.53 [-4.0, +23.1]. It leans positive and is not decided; and in the same
job three of the eight alone (M1, complete) gave -5.56 [-15.9, +4.8] and a pair with AspCappedReopen in it (M5)
-22.5 [-36.2, -8.8]. A bundle chosen after looking at many results must be confirmed by NEW matches with NEW seeds
before anyone believes it (our rule). That is this job, and only this: the eight, twice.

### Step 0 (known numbers on the unpatched build; if one differs, stop and report)
`bench 11` = 312866, `bench 13` = 862329, `bench 16` = 3024920, `go perft 5` = 4865609. Then `bench 13` with all
eight switches on: your job 2 got 868694, it must be that number again. The `uci` lines of the eight options, quoted.

### The matches (20,000 nodes, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
### colours reversed, `order=random` with `-srand <seed>`, no adjudication; the same exe on both sides)
    C    control: 20,000 against 10,000 nodes, no options, 300 games, seed 8100: must be near +200
    Y1   all eight on against all off                    2,000 games   seed 8101
    Y2   the same again                                  2,000 games   seed 8102   (ALWAYS, whatever Y1 says)
A 2-game probe with the engine's input log BEFORE every match: all eight `setoption` lines must be seen arriving on
the candidate side and none on the base side.
TIME: your job 2 needed 18 minutes for 2,000 games. After C you know today's rate: if Y1 and Y2 at 2,000 games do
not both fit before minute 50, play BOTH at the same smaller even number of games (say so) rather than one whole and
one cut. A cut match reports the games it reached, complete pairs only.

### What to commit for every match
- the per-game file: ONE line per game: `round|white|black|result|how it ended|opening FEN` (how it ended from
  fastchess's termination: mate, the draw rule, time, or a fault);
- fastchess's final numbers; your Elo with the 95 % pair interval and the pair counts;
- the count of games by ending, FIRST: illegal moves, disconnects and time losses must be 0.

### The report
First paragraph in plain words: the eight-switch bundle pooled over Y1 and Y2 with its 95 % pair interval; then the
same pooled together with your job 2's M4 as a second number (say that M4 was the match the bundle was CHOSEN on, so
the first number is the honest one); what was cut. Then step 0; the ending counts; one table of all matches; the
probes; files of the repository you opened; stamps of every step; what you did not do; what you are not sure about;
a better way; model. Then end your run. Thank you for nine jobs.
