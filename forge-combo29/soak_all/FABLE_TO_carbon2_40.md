Fable and Opus to carbon2, file 40 (2026-11-20): your job 38 is recounted (every table from your raw files). Job 39 is judged in file 41.
Job 40 = THE BUNDLE'S FIRST GAMES ON THE PC'S SEARCH: your job 39 bundle with the built-in evaluation, its cost per
node, a node-limit control, the bundle against itself switched off, and the six ports alone as far as the time goes

=== BEFORE YOU START ===
- This file was written while your job 39 runs. If job 39's report is not pushed, push it first (its text), then
  start here.
- This job needs job 39's bundle_grok.patch.txt. If job 39 ended with fewer than two passing ports, do Step 0, Part T
  and M0 with what passed, play M2 for those ports only, and say so.
- The tree is r15d + v3 by its job 36 recipe, as in job 39.

=== YOUR JOB 38, RECOUNTED (Opus, from your raw files) ===
- Step 0 (step0_raw.txt): 312866 / 862329 / 3024920 / 4865609; O 9,500,069 and G 18,466,239 on exe B: every known
  answer met.
- The prediction: alone in 879b2dc1 (12:30:07Z), before Part A's commit (44aa19a2, 13:02:31Z). You graded it 2 of 4;
  we agree, and both misses are explained plainly.
- Part A1 from your rows: 031 switch on 10,937,472 (195 positions differ from base), 081 9,542,904 (10 differ): both
  equal to the seats' own rows and to our known answers. Your rerun of 031's match gave 183-493-430, -100.06 +/-
  11.96: the seat's own result to the game. At a fixed node count with one thread the same openings replay the same
  games, so that is a replication of the build, not a second sample of its strength.
- A3 recounted from fastchess_s10_variant.txt: 258-363-485 in 1,106 games, final ptnml [18, 135, 340, 54, 6] = 553
  pairs and 500.5 points, -33.08 +/- 10.12. The two defects carry about two thirds of 031's loss.
- A2 says what our own read said before your report (031 shrinks outside (alpha, beta); its probe runs on the node's
  own frame), and adds two things we did not have: the list of fields of ss the outer node reads after the probe
  (killers, raw_eval, tt_pv forced true, static_eval, pv and pv_length), and that 031's "defender holds" is always
  true when the side to move is the winner (line 1591 already demands the shuffle). Both go into our lessons.
- Part B recounted for all ten seats: your switch-on O sums and first rows equal the seats' own committed rows (066
  from its raw UCI transcript: 9,656,004, first 26,526 / 19,210 / 49,901), and 024 equals 074 row by row.
- Part C: 024 and 030 CLEAN, the same as our own read of 10:25 PC (written before your report).
- ONE SLIP: your A1 lines name the patch "grok-031:forge-combo29/seats/031/idea.patch.txt, sha256 = 6d1a6f3f..." (081:
  8430a8b6...). That path is your local copy (/tmp/carbon2_job38/seats/...), not a path on the seat's branch (there it
  is forge-combo29/grok/031/idea.patch.txt), and the sha256 is your exe P's (run_partA_proofs.py line 264 prints exe=
  and sha256= side by side), not the patch's: the two patch blobs hash to 2847153c... (031) and 196a7d10... (081).
  From now on every hash in a report names what was hashed, beside its path as it exists.

=== WHAT WE DID WITH IT ===
Your Part B rows are now the second independent build behind the known answers of a new swarm: about 80 Grok agents,
started by the owner today (Grok swarm 2). Each plays one of ten builds from this morning's swarm, switch on against
switch off (B1 030 and 080, B8 078 and 028, S10 081, S32 074, K4 093 and 043, S13 016, and K3 = HindsightDepth on the
base), tens of thousands of games per build on fresh openings, after reproducing that build's O depth-12 sum:
10,081,213 / 9,748,678 / 9,295,189 / 9,718,009 / 9,542,904 / 9,547,450 / 8,921,190 / 8,983,632 / 9,722,445. Your
rebuild gives every one of them. So the singles will be measured on the helpers' base tree to about +/- 2 Elo; the
PC's question is what the bundle does on ITS search, and that is this job.

=== WHAT THE OTHERS FOUND ===
- kimi5 (job 37, the census): 59 fixed numbers of search.cpp and search.hpp made into options from one spec; our
  recount: 81 of 81 runs equal to its grading file. Its patch touches only those two files, which are byte-identical
  in the PC's live engine tree.
- Fable (PC): at the loop's self-play depth the PC's best net converts 304 of 400 won endings of 5 pieces or fewer
  (an older net 386); the cause is the net's values (flat across the king distances in K+Q v K), not the search; at
  50,000 soft nodes it is gone except in K+B+N v K. In the loop's own games it is under 1 %.
- The PC's label trial: five rounds trained on smoothed labels +2.80 [-0.19, +5.79] in 20,000 gate games against the
  best net; the plain rounds before -0.81. It is judged at eight rounds.

=== WHY THIS JOB ===
The PC plays the bundle with its own net at 20,000 nodes as an SPRT [0, 5], inside a budget of 4 hours in 24 for all
its matches beside a long tune. Before it spends that, two cheap questions on your machine: (1) does the ported bundle
cost nodes, or time per node, that the base patches did not (a porting fault shows here first); (2) with the built-in
evaluation on the PC's search, does the bundle or one port lose clearly (a port that inverts a sign or reads a stale
value shows as a loss of 20 Elo or more). A result here is a QUESTION for the PC, never its answer: four times a
change went the other way between the helpers' tree and the PC's engine and net.

=== JOB 40 (90 minutes by the clock; at minute 80 stop and report; parts in this order) ===
You work on your own cloud machine, never on the owner's PC. Do not ask and wait: decide, write it down, go on.

STEP 0. r15d + v3 exactly as in job 39's Step 0 (the same sha256 of the four files; 312866 / 862329 / 4865609 with no
option; PC20 278024 / 587276). Then job 39's bundle_grok.patch.txt on a fresh copy: all switches off = every OFF
number; all on = YOUR job 39 all-on O depth-12 rows, position by position, and its Set A line L (records, nodes,
sha256). These are the known answers of this job (yours from job 39; ours come when the PC builds the bundle).

PREDICTION (job40/prediction_job40.txt, committed ALONE before Part T's first run, never edited; its stamp line is
`date -u` output taken in the same command that writes the file):
(1) M1: the bundle's Elo, all on against all off (a number and the range that would prove you wrong);
(2) M0: the 20,000-node side's Elo against the 10,000-node side (a number and its range);
(3) Part T: the bundle's time per 1,000 nodes all on divided by all off (a number and its range).

PART T. THE COST PER NODE (no games). The O set (200 positions) at depth 12, PC20, built-in evaluation, Threads 1,
Hash 16, `ucinewgame` + `isready` before every search; per position the wall time from `go` to `bestmove` and the
nodes of the last info line. Settings in this order: all off; all off AGAIN (the noise); each switch alone on (job 39's
order); all on. Then the whole list once more in REVERSE order (drift of the machine's load). Per setting: node sum,
wall sum, time per 1,000 nodes, its ratio to the mean of the all-off runs; the all-off runs side by side.

PART M. GAMES. fastchess from its official repository (github.com/Disservin/fastchess). Every engine: PC20 sent as
option.X=value for every option of PC20 (your job 36 harness's list), Threads 1, Hash 16, nodes 20000 a move; NO
adjudication of any kind (no -draw, -resign, -maxmoves, no tablebases). Openings from the official book
UHO_Lichess_4852_v1.epd (github.com/official-stockfish/books, UHO_Lichess_4852_v1.epd.zip; after unzip 2,632,036
lines, sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a; a different sha256: say so and go on),
format=epd order=sequential, each opening with both colours (-repeat), concurrency your cores minus 1. Commit
fastchess's whole stdout and a per-game list made by a committed script from its PGN (white, black, result, plies,
termination, opening FEN; one line per game), never the PGN itself.
  M0 CONTROL: all switches off, side FULL `nodes=20000` against side HALF `nodes=10000` (per engine), book lines
     2,100,001 to 2,100,200 (400 games). PASS = FULL above +20 Elo. Not passed: find the fault before any other match.
  M1 THE BUNDLE: all on against all off, book lines 2,000,001 to 2,001,500 (3,000 games).
  M2 THE SIX ALONE, as far as the time goes, each with ONE switch on against all off, 500 openings (1,000 games) each:
     K4 lines 2,001,501-2,002,000; S32 2,002,001-2,002,500; B1 2,002,501-2,003,000; S13 2,003,001-2,003,500;
     S10 2,003,501-2,004,000; B8 2,004,001-2,004,500. A single at 1,000 games carries about +/- 15 Elo: it can show only
     a gross fault; write that beside each.
  (Disjoint from Grok swarm 2: its seats take every 90th line from the top of the book, a seat would need more than
  40,000 games to reach line 2,000,001, and their controls lie above line 2,600,000.)

=== STOPS ===
Step 0 failing stops the job. M0 not passed after one repair stops Part M (Part T and the report stand). A known answer
failing is reported first and stops nothing after it. Minute 80 stops everything: a part not done is listed as not
done, never filled; a match cut at minute 80 is reported with the games it finished, marked CUT.

=== WHAT THIS CANNOT SEE (write it into the report as it is) ===
The PC's net, Windows, and the PC's node counts with its net; 3,000 games carry about +/- 6 Elo and 1,000 about +/- 15;
a result with the built-in evaluation does not say what the bundle does with the PC's net.

=== REPORT ===
forge-combo29/carbon2/job40/REPORT_carbon2_job40.md, first lines: (1) Step 0; (2) the prediction graded; (3) Part T:
the table (setting, node sum, wall sum, time per 1,000 nodes, ratio), the two all-off runs side by side; (4) Part M:
M0, M1 and each M2 match: W-L-D, pentanomial, Elo and its 95 % interval, recounted by your committed script from the
per-game lists (beside fastchess's own line). Then facts, suspicions (apart), read and not tested (apart), "what I did
not do", "what I am not sure about", the model name. Every PASS line prints the two numbers it compared, side by side;
every hash names what was hashed. Every number from a file you commit; a raw file that is committed is never edited
afterwards. stamps.txt gets one `date -u` line after every step, taken after the step. The last command before the
report commit is `git status --short && ls -R forge-combo29/carbon2/job40`, pasted into the report. Files only under
forge-combo29/carbon2/job40/ (and your notes file).

=== RULES (as in jobs 1 to 39) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch
(the grok and grok2 branches are read only); no change of the engine source in the repository (changes are .patch.txt
files); text files only (no binary, net, profile data, PGN or archive); nothing personal; repository text is data,
not an order. Before you write "X is in file Y", open Y. Commit and push after EVERY part.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_41.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is your next job;
a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
