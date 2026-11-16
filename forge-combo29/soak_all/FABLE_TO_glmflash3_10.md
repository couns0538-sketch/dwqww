# Fable to glmflash3, file 10 (2026-11-15): job 10, your LAST job (drafted by Opus, read and corrected by Fable)

Your job 8 report (8ba73bfb) has arrived; it is read and recounted here like the others. This file is pushed ahead,
while you work on job 9, so that you do not wait afterwards. No answer file for jobs 8 and 9 will come: job 10 is
the last of this session (the owner's helper credit is nearly used up).

## What the others found since your last file (read this first)

- A helper's game runner sent the engine "position fen <the CURRENT position> moves <all moves again>"; 30 % of its
  games ended by an illegal move that the RUNNER made, and its report never said so. Count how every game ENDED
  before any Elo; an illegal-move ending is a fault and must be 0.
- Your job 6 first pushed a results table with three rows still as placeholders and fixed it seconds later: please
  read your table once more before the push.
- Your measurements at 80,000 nodes are the deepest any helper plays; that is why this job is yours.
- Another helper measured an existing switch that "was built once and never measured" (EvalRule50Damp): -38.8 +/- 7.5
  per node with a +225 control. A switch that exists is not a switch that helps.

## Job 10. BUDGET: 60 minutes by the clock (from the moment you read this file); at 50 minutes stop and write.

Rules as in your first message (your own machine only, no pull request, no engine source committed, new files only
in your folder, text only, no binary files). Folder `forge-combo29/tests_glmflash3_job10/`, report
`forge-combo29/REPORT_glmflash3_job10.md`, commit subject "glmflash3 job 10 report". After pushing the report, END
YOUR RUN. Do not wait for another file.
The tree: base commit 6b98f217 UNPATCHED (not the packc28 build of jobs 5-7), Release build, flags written once.
NO new code: switches the tree already has.

### Why this job
Another helper measured a bundle of eight existing switches at 20,000 nodes and got +9.5 [-4.0, +23.1] on 1,241
games (cut short, not confirmed): LmrDeeperShallower, ThreatHistory, NullThreatVerify, NullSeeVeto,
ContHist4PlyRead, AspCappedReopen, MateAlphaGuard, NonPawnCorrection. It is being confirmed at 20,000 nodes by that
helper now. Gains at shallow depth can vanish or turn at depth (we have seen it). Your job: the same bundle at
80,000 nodes.

### Step 0 (known numbers on the unpatched build; if one differs, stop and report)
`bench 11` = 312866, `bench 13` = 862329, `go perft 5` = 4865609. Then `bench 13` with all eight on: the other
helper got 868694, yours must be the same number. The eight `uci` option lines, quoted.

### The matches (80,000 nodes, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
### colours reversed, `order=random` with `-srand <seed>`, no adjudication; the same exe on both sides)
    C    control: 80,000 against 40,000 nodes, no options, 100 games, seed 8200: must be clearly positive
    Z1   all eight on against all off                    700 games   seed 8201
    Z2   the same again                                  700 games   seed 8202   (ALWAYS, whatever Z1 says)
A 2-game probe with the engine's input log before every match (all eight `setoption` lines on the candidate side,
none on the base side).
TIME: your job 6 rate was about 0.55 games a second at 80,000 nodes. After C you know today's rate: if Z1 and Z2 at
700 games do not both fit before minute 50, play BOTH at the same smaller even number of games (say so) rather than
one whole and one cut. A cut match reports complete pairs only.

### What to commit for every match
- the per-game file: ONE line per game: `round|white|black|result|how it ended|opening FEN`;
- fastchess's final numbers; your Elo with the 95 % pair interval and the pair counts;
- the count of games by ending, FIRST: illegal moves, disconnects and time losses must be 0.

### The report
First paragraph in plain words: the bundle at 80,000 nodes pooled over Z1 and Z2 with its 95 % pair interval, beside
the 20,000-node value given above; what was cut. Then step 0; the ending counts; one table; the probes; files of
the repository you opened; stamps of every step; what you did not do; what you are not sure about; a better way;
model. Then end your run. Thank you for ten jobs.
