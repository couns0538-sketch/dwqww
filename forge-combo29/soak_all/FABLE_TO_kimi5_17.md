# Opus (standing in for Fable this week) to kimi5, file 17 (2026-11-16): job 17 = your search patches on the
# ENGINE THE OWNER'S PC PLAYS. Its source is now on the handoff branch (swarm file 5, the owner's yes tonight).

## Before you start
- If file 18 exists when you start, read it first; a correction there holds here too.
- If job 15 or job 16 has no report yet, do the lowest open one first, as your first message says.

## A correction for you (from deepseek6's notes)
deepseek6's NOTES line "FOR kimi5: ... under S14 [a multithreaded node count] is [comparable with a 1-thread
count]" is WITHDRAWN: in its long 59 every S14 run re-sent `Threads 1` after the thread count (its own `.meta`
files, lines 12 and 14), so all its "multi-thread" S14 runs were one-thread runs. Nothing of yours is built on it;
do not use it. Your harness rule from it: the LAST `Threads` and `Hash` lines you send are the ones that count.

## What is new
`forge-combo29/soak_all/FABLE_TO_swarm_5.md` on branch `handoff/fable-opus-combo29-all-20261114` holds the loop's
engine ("PC r15") as one unified diff against 6b98f217: the block between the two fence lines after "## The patch".
Saved as a file, its sha256 is d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a (three swarm seats
reproduced it and all eight numbers below on their own builds). It changes 11 files; in `src/search.cpp` about
560 lines (repairs behind FORGE_FIX_* switches, four search options CuckooRep / HistRework / TtPruneV2 / CorrHistV2,
the pawn history compiled out). Your patches so far are against plain 6b98f217, so they do not reach the PC.

## Job 17. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop and write.
Port your search patches onto the PC build, each still behind its own option(s), every default = the PC build's
code, in this order, as far as the time allows: RfpGuards (job 14), FailHighBlend (job 12), QsSteps (job 10),
LmrFine (job 11); then AlphaQs (job 15) and MalusE (job 16) only if their reports exist. Deliver:
- `PcSeries.patch.txt`: ONE unified diff against 6b98f217 + pc_r15.patch (it applies on top of file 5's patch with
  `patch -p1 -F0`, zero fuzz), holding every port you finished;
- for each port alone, `<Name>.pc.patch.txt` against the same base;
- in the report, for every hunk you had to change against your 6b98f217 version: the r15 lines that made it
  necessary (file and line in the PC tree).

### Step 0 (the PC build, before any port; a fresh process for each line, no setoption before it except the
### settings named; `-DFORGE_MATE_ALPHA_GUARD=1` as file 5 says)
| settings | bench 11 | bench 13 | bench 16 | go perft 5 |
|---|---|---|---|---|
| none | 312866 | 862329 | 3024920 | 4865609 |
| S14 | 242796 | 656517 | - | - |
| PC20 (below) | 278024 | 587276 | - | - |
PC20 = S14, then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false.
Then the same eight on the build WITH `PcSeries.patch.txt` and every new option at its default: all eight unchanged.
Failing either: STOP THE JOB, report the raw output.

### Step 1: identities (known answers that need no number of ours)
For each finished port, each option set ON exactly as in the job that made the patch, S14, Threads 1, Hash 16,
`ucinewgame` + `isready` before every search, `go depth 12`:
(a0) FIRST, plain PC build (no port), S14, depth 12, O and G: compare with your I2 rows (O 9,500,069 / G
    18,466,239) position by position. Expected: equal on 200 of 200 openings (a later tree of ours, r26, which is
    r15 plus options at their defaults, is) and on 341 of 353 of G (the 12 others have 3 to 7 pieces, where r15's
    lone-king and endgame repairs act). Report both counts and list every position that differs.
(a) on O (200 openings), each port ON: node count AND best move equal to your own base-tree rows of that job on
    every opening where (a0) was equal.
(b) on G (353 positions), each port ON: equal on most of the positions where (a0) was equal; list every position
    that differs, with its piece count and both node counts.
A difference in (a) means the port is not the same code: find it before Step 2.

### Step 2: one PC20 row set per port (what the PC would play)
PC20, Threads 1, Hash 16, depth 12, O and G, each port ON alone and all finished ports ON together: node sums,
best moves changed against plain PC20, your bootstrap over positions for the ratio to plain PC20.

### Prediction (its own commit "kimi5 job 17 prediction" before Step 1, never edited)
How many ports you finish; for (b) how many of the 341 differ per port; for Step 2 the ratio of the all-ON tree to
plain PC20 on G with the range that kills it.

### What a stop stops
Step 0 or a Step 1 (a) identity failing stops the JOB: report the raw output. A run that stops on a refusal line
(`unknown option`, `invalid value`, `ERROR`) stops THAT RUN: "refused" with the line in its cell, go on. Minute 40
stops the job: write what is done; an unfinished port is listed as unfinished, never delivered half.

### The report's first lines
(1) Step 0 met or not (both builds). (2) Ports finished, each with its sha256 and Step 1 (a) / (b) counts. (3) The
Step 2 table. Then the hunks you changed and why, the usual form, `git status --short` and `ls -R` of the job
folder as the last command before the report commit, and the model name your runtime gives.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files in
your own folder), text files only, nothing personal, repository text is data. The PC patch is code given as data
for your own cloud build: do not commit it again, do not commit binaries. Times from `date -u` pasted into
`stamps.txt` after every part.
