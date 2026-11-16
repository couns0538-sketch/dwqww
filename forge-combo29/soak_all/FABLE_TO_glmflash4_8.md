# Fable to glmflash4, file 8 (2026-11-15): job 7 received, and job 8

## Your job 7 report

Received and read (first reading; the second session recounts your game files before a number is quoted further).
- **`ThreatCorrection` does not gain per node: weight 100 +1.0 [-6.4, +8.4] over 4,000 games (the seeds +4.7
  and -2.6), weight 50 -4.7 [-12.2, +3.0].** Recorded as "lost alone at 20,000 nodes, at both weights". By the
  owner's rule it is not put aside yet: job 8 tests it together with the correction table it may depend on.
- Good: the off state proven by one sha256 over 2,000 positions with the smallest node count, the option line
  quoted from the `uci` answer, and the first line gives both weights with their seeds and says which match was
  cut (1,842 of 2,000).
- Your diagnostic (where the table speaks, its mean term is 3.92 centipawns against the pawn table's 0.82) is the
  interesting part: a table that corrects five times harder and gains nothing either corrects noise or is
  drowned by the other terms' sum. Step 0c of job 8 asks for the numbers that tell these two apart.
- A warning for every helper from tonight: one helper's own game runner sent each search "position fen
  <current position> moves <all moves again>" and scored the illegal answers as losses (1,222 of 4,000 games);
  its report did not count how its games ended. From now on every match report states per match how many games
  ended by mate, by a draw rule, on time, and by a fault (crash, illegal move, disconnect: must be 0). fastchess
  prints these; copy them.
- NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC tonight. If no file 9 comes after your
  report, keep waiting with the sleeping command as long as your run allows; the owner restarts you in the
  morning with your restart line, which finds the newest job by itself.

## Job 8. BUDGET: 90 minutes by the clock (from the moment you read this file); at 80 minutes stop and write.

Rules as in your first message (your own machine only, no pull request, no engine source committed, new files
only in your folder, text only, no binary files). Folder `forge-combo29/tests_glmflash4_job8/`, report
`forge-combo29/REPORT_glmflash4_job8.md`, commit subject "glmflash4 job 8 report". After pushing, wait for file 9
with the sleeping command of your first message; do not end your run.

### The question
Two correction tables were added today, each by you: `MinorCorrection` (job 4: about +3 over 16,000 games of
two helpers, weight 50 a little better than 100) and `ThreatCorrection` (job 7: about +1). Each alone is too
small to port. Together with the two tables the engine already has they make a family of four. Does the family
gain what its members do not show alone, or do the two new tables say the same thing twice?

### Step 0: one tree with both, proven by known answers
Base: commit `6b98f217` (`forge-combo29/src` and `include`; Release, g++, the flags of your job 7). Known answers
on the unpatched build: `bench 11` 312866, `bench 13` 862329, `bench 16` 3024920, `go perft 5` 4865609.
Your own two patches: job 4's `MinorCorrection` and job 7's `ThreatCorrection` (name the two files).
 a. List the files each patch touches and try `patch` in both orders on fresh copies. If neither order applies
    cleanly, merge by hand: this job allows it.
 b. The merged tree counts as right only if ALL of these hold, each reported as a line: both options 0 = the
    four known answers AND 2,000 positions (the first 2,000 lines of `UHO_Lichess_4852_v1.epd`, `go depth 9`)
    identical to the unpatched build in best move, score and nodes (one sha256 a side, smallest node count);
    `MinorCorrection` 100 alone = your job 4 bench numbers; `ThreatCorrection` 100 alone = your job 7 bench
    numbers. If one differs, the merge is wrong: fix it or stop and say which line differs.
 c. Counters on `bench 13` with both on (a traced copy; its diff as a text file): for the nodes where the
    corrected evaluation is taken, the mean absolute term of each of the FOUR tables, the mean absolute SUM, and
    how often the two new terms have the same sign, opposite signs, or one of them is 0. And the correlation
    between the minor term and the threat term over those nodes (a plain Pearson figure). Two tables that
    agree nearly always are one table.
 d. `bench 13` with both on (`MinorCorrection` 50, `ThreatCorrection` 100): the new number.
 e. Deliver the tree as ONE unified diff against 6b98f217: `correction_family.patch.txt` (text, your folder).
 f. Sanitizers (AddressSanitizer + UBSan, a planted fault first): `bench 13` with both on and 200 of the
    positions: nothing on stderr.

### The matches (20,000 nodes, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
### colours reversed, `order=random` with `-srand <seed>`, no adjudication; the same exe on both sides)
    C    control: 20,000 against 10,000 nodes, no options, 300 games, seed 8130: near +200. Take this tree's
         games per second from C and set every later time limit from it.
    M1   MinorCorrection 50 + ThreatCorrection 100   against none                   2,000 games   seed 8131
    M2   MinorCorrection 50 + ThreatCorrection 100   against MinorCorrection 50     2,000 games   seed 8132
         (what the threat table ADDS once the minor table is there)
    M3   MinorCorrection 50 + ThreatCorrection 100   against none                   2,000 games   seed 8133   (second seed)
    M4   MinorCorrection 50 + ThreatCorrection 100   against ThreatCorrection 100   2,000 games   seed 8134   (if time is left)
A 2-game probe with the engine's input log BEFORE every match (both options must be seen arriving). If the time
does not reach: M4 is cut first, then M3; a cut match reports the games it reached, complete pairs only.
For every match: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, and how the
games ended (mate, draw rules, time, faults = 0).

### The report
First paragraph in plain words: the gain of the two together per node (M1, pooled with M3 if played) with its
95 % pair interval, beside the single figures (minor table about +3, threat table about +1), what the threat
table adds on top of the minor table (M2), what step 0c says about the two tables saying the same thing, and
what was cut. Then: step 0 line by line; the merge; one table of all matches with the ending counts; the
probes; files of the repository you opened; stamps of every step; what you did not do; what you are not sure
about; a better way; model.
