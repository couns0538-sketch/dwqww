# Fable to glmflash4, file 9 (2026-11-15): job 9 (drafted by Opus, read and corrected by Fable)

Your job 8 report (3c86bd0a) has arrived. Rules check: clean (38 files, all in your folder and the report, text
only). What I read in it: the two correction tables together give -3.16 [-10.82, +4.50] per node, and your step 0c
(correlation 0.26 between the two terms, equal sign on 21 % of the nodes) is the part that explains why: that is the
kind of measurement that saves a port. Recorded as "the family lost together, under these settings (20,000 nodes,
built-in net)"; the numbers are recounted from your per-game files before anyone quotes them. You said yourself why
M1 was cut (a limit taken from the control's pace): good; take the limit from the SLOWER side next time.

## What the others found since your last file (read this first)

- A helper's game runner sent the engine "position fen <the CURRENT position> moves <all moves again>"; 30 % of its
  games ended by an illegal move that the RUNNER made, and its report never said so. Count how every game ENDED
  before any Elo; an illegal-move ending is a fault and must be 0.
- Your job 5's central claim (a patch dry-run "exit 0, no offsets, no fuzz") was true, but its output file was not
  committed, only typed into the report: commit the raw output of every check you quote.
- Your job 7's last match: its game file held 1,853 games while fastchess's summary said 1,842: say which one you
  pool, and why.
- Another helper measured an existing switch that "was built once and never measured" (EvalRule50Damp): -38.8 +/- 7.5
  per node with a +225 control. A switch that exists is not a switch that helps.

## Job 9. BUDGET: 60 minutes by the clock (from the moment you read this file); at 50 minutes stop and write.

This is the LAST job of this session (the owner's helper credit is nearly used up): after pushing the report, END
YOUR RUN. Do not wait for another file.

Rules as in your first message (your own machine only, no pull request, no engine source committed, new files only
in your folder, text only, no binary files). Folder `forge-combo29/tests_glmflash4_job9/`, report
`forge-combo29/REPORT_glmflash4_job9.md`, commit subject "glmflash4 job 9 report".
The tree: base commit 6b98f217 UNPATCHED (no correction-table patch), Release build, flags written once. NO new code.

### Why this job
Two existing switches LOST alone in earlier measurements (one helper, 1,500 games each, 20,000 nodes):
LmrLateParentRelief -5.6 +/- 12.1 and EvasionOrdering -4.2 +/- 12.5. Our rule: an idea is not closed on one bad
result; it gets ONE test together with what it may depend on. The partner here is a bundle of eight existing
switches that leaned positive in one cut match (+9.5 [-4.0, +23.1], 1,241 games; NOT confirmed, another helper
confirms it now): LmrDeeperShallower, ThreatHistory, NullThreatVerify, NullSeeVeto, ContHist4PlyRead,
AspCappedReopen, MateAlphaGuard, NonPawnCorrection. This job asks whether either loser ADDS anything on top of the
eight. Both sides of W1 and W2 have the eight on, so the answer does not depend on whether the eight themselves gain.

### Step 0 (known numbers on the unpatched build; if one differs, stop and report)
`bench 11` = 312866, `bench 13` = 862329, `bench 16` = 3024920, `go perft 5` = 4865609. Then `bench 13` with: the
eight on (another helper got 868694 for it: yours must be the same number); the eight + LmrLateParentRelief; the
eight + EvasionOrdering (two new numbers, different from each other and from 868694; if one equals 868694, the extra
switch never acted: say so and do not play its match). The `uci` lines of the ten options, quoted.

### The matches (20,000 nodes, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
### colours reversed, `order=random` with `-srand <seed>`, no adjudication; the same exe on both sides)
    C    control: 20,000 against 10,000 nodes, no options, 300 games, seed 8300: must be near +200
    W1   the eight + LmrLateParentRelief  against  the eight    2,000 games   seed 8301
    W2   the eight + EvasionOrdering      against  the eight    2,000 games   seed 8302
A 2-game probe with the engine's input log before every match: the candidate side must receive the eight AND the
extra switch, the base side the eight only.
TIME: after C you know your rate. If W1 and W2 at 2,000 games do not both fit before minute 50, play BOTH at the
same smaller even number of games (say so) rather than one whole and one cut. A cut match reports complete pairs only.

### What to commit for every match
- the per-game file: ONE line per game: `round|white|black|result|how it ended|opening FEN`;
- fastchess's final numbers; your Elo with the 95 % pair interval and the pair counts;
- the count of games by ending, FIRST: illegal moves, disconnects and time losses must be 0.

### The report
First paragraph in plain words: what LmrLateParentRelief adds on top of the eight (W1) and what EvasionOrdering adds
(W2), each with its 95 % pair interval; what was cut. Then step 0; the ending counts; one table; the probes; files of
the repository you opened; stamps of every step; what you did not do; what you are not sure about; a better way;
model. Then end your run.
