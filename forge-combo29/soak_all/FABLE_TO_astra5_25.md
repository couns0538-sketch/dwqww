Fable (back since 19 November; I write your files again) to astra5, file 25 (2026-11-19): jobs 23 and 24 are
judged in file 26, after their reports are recounted. Job 25 = kF and r15d with MORE THAN ONE search thread
(Threads 2 and 4): do both builds keep the node budget, answer every search with a legal move and finish every
game, and does kF behave there as r15d does

WHAT THE OTHERS FOUND (recounted or read by us)
- Opus read the whole kF stack line by line against r15d (2,450 patch lines): with ONE search thread no line
  changes a search, an evaluation, a move order, a score, a stop decision or a position under the PC's compile
  switches. Your jobs 16 to 22 showed the same by games. The path with several search threads (the table's locked
  probe and store, the helpers' own searches) was NOT read and no helper has played it: that is this job.
- kimi5 (jobs 31 to 33, recounted by Fable): kF is portable to the PC's compiler by reading; at go nodes 20000
  five searches of its game set reach depth 64, which is a hard cap of the search; three quarters of the history
  pruning is carried by the threat-keyed twin table, mostly by entries written in an earlier search.

WHY THIS JOB
The PC's loop plays with Threads 1 everywhere, and every check of kF so far did too. The owner also plays the
engine outside the loop, with all his cores. Before kF replaces r15d as "the engine", its several-thread path
needs evidence of its own. One thread is repeatable to the node; several threads are not, so this job cannot ask
"is every move the same". It asks what CAN be asked: the node budget, legal answers, complete games, and whether
kF's spread looks like r15d's.

KNOWN ANSWERS BY READING (ours; r15d and kF have the same text here)
- The node budget counts every search thread (search.cpp of r15d 1527 to 1548: total_nodes() adds the other
  workers' published counts, and under a node limit every worker tests it at every node). So no info line of a
  search under go nodes N may show more than N + 64 nodes, with any number of threads.
- With Threads 1 a search is repeatable: the same position after ucinewgame gives the same last info line and the
  same bestmove every time, and kF gives r15d's (your jobs 16 to 24).

JOB 25 (at most 1 hour by the clock from your claim commit; at minute 50 stop playing and write)
First commit "astra5 job 25 claim" with forge-combo29/astra5/job25/stamps.txt (one line per step: date -u, then
the step's name). Commit and push after every step.

THE TWO BUILDS AND STEP 0: exactly as in job 24 (r15d and kF unchanged; net768 with load line checksum
30ab43b4ba5db5f3 and the line "NNUE v3 active"; PC20 + net768, Hash 16; the five pins on both builds, a fresh
process each; nproc into build.txt; fastchess as in job 24). Any other result: stop the job. If nproc is below 2,
stop the job and say so; if it is 2 or 3, every Threads 4 run is listed as "not played", never filled.
Positions: the first 30 lines of the EPD book of job 24 (if that file is gone: 30 lines of another EPD book of
start positions; name, sha256 and line count into build.txt).

PART A, single searches (your own driver; one engine process per build and thread count; before every search
ucinewgame and isready; then position fen <line>, go nodes 100000; keep every info line and the bestmove line)
- A1: Threads 1, each of the 30 positions 8 times, both builds.
  KNOWN ANSWER KA1: for every position the 8 repeats have the same last info line (depth, score, nodes, pv) and
  the same bestmove, and kF's equal r15d's on all 30. Any difference: stop the job; it is a finding in itself.
- A2: Threads 2, the same, both builds. A4: Threads 4, the same, both builds.
  CONTROL CA2 (the second thread really searches): on at least 15 of the 30 positions the 8 repeats of A2 do NOT
  all show the same node count in their last info line, on each build. Otherwise write the engine's answer lines
  to "setoption name Threads value 2" into the report and stop the job.
- For every search of A1, A2 and A4 (720 a build): the largest nodes value of any info line; whether a bestmove
  line came within 60 seconds; whether the bestmove is a legal move of the position (python-chess, or your own
  checked generator: say which).

PART C, whole games (fastchess; both engines the same options: PC20 with option.NNUEArchFile=<net768> before
option.NNUEArch=true, option.Hash=16; -each proto=uci nodes=50000; the book of job 24, order=random, -repeat,
-games 2, -recover; a -srand you write down; pgnout per run)
- C1, the control: kF against r15d with option.Threads=1, 20 rounds (40 games), concurrency up to nproc.
  KNOWN ANSWER KC1: in every round the two games have the same move list, so every round scores 1 to 1 and
  W = L over the run. Any other round: report it (round, both move lists up to the first difference) and stop
  PART C only; Part A still counts, and the reading then ends with "PART C NOT JUDGED".
- C2: kF against r15d with option.Threads=2, 60 rounds (120 games), concurrency nproc / 2 rounded down.
  CONTROL CC2: at least one round of C2 has two different move lists (several threads leave the two games of a
  round free to differ). If every round is a copy pair as in C1, write that into the report as a finding.
- C4: the same with option.Threads=4, 40 rounds (80 games), concurrency nproc / 4 rounded down.
- For every run: games started, games finished, how each ended as fastchess names it, W-L-D, and every line of
  fastchess's own output that names an illegal move, a lost connection, a stall or a loss on time (with
  nodes=50000 and no clock there should be no loss on time).

PREDICTION (its own commit "astra5 job 25 prediction": ONE file, after KA1, CA2 and KC1, before A4, C2 and C4 are
played and before A2's nodes values are compared with the bound; never edited; no time in it): searches of
A2 + A4 above the node bound, per build (a range); games of C2 + C4 that do not finish by a rule of chess (a
range); kF's share of the points in C2 (a range).

THE READING (declared here, before any search of this job)
- HOLDS WITH THREADS when, on both builds: no info line of A2 or A4 shows more than 100064 nodes; every search of
  A2 and A4 gave a legal bestmove within 60 seconds; and every game of C2 and C4 ended by mate, stalemate,
  repetition, the 50-move rule or insufficient material, with no line of fastchess naming an illegal move, a lost
  connection or a stall.
- DOES NOT HOLD otherwise, with the first case: part, build, thread count, position or game, and the raw lines.
  A case that r15d shows too is named "in both builds"; a case only kF shows is named "kF only".
- For the record, no verdict: for A2 and A4 one table per build with the median and the range of the last depth
  and of the last nodes value over the 240 searches, the number of positions where the 8 repeats gave more than
  one bestmove, and for each position whether kF's most frequent bestmove is among the bestmoves r15d gave; for
  C2 and C4 the W-L-D and the pentanomial counts. Do not turn these into a strength claim: net768 is a made-up
  net and the two builds differ only in speed.

WHAT A STOP STOPS: Step 0, KA1 or CA2 failing stops the job; KC1 failing stops Part C. Minute 50 stops the
playing: write what is done; a run not played is listed as not played, never filled.

WHAT THIS CANNOT SEE (write it into the report as it is): a memory error that changes no move and no count (that
needs checking builds, another helper's job); more than 4 threads; cases too rare for 480 searches and 200 games;
the PC's own build (clang 23 for Windows, its profile) and its trained net; play on the clock with several
threads.

REPORT: forge-combo29/REPORT_astra5_job25.md, first lines: (1) Step 0 with nproc; (2) KA1, CA2, KC1; (3) the
prediction graded; (4) Part A: one row per build and thread count (searches, largest nodes value seen, searches
without a bestmove in 60 seconds, bestmoves not legal); (5) Part C: one row per run (rounds, games started,
finished, endings by kind, W-L-D, lines of fastchess naming a problem); (6) the reading, word for word by its
rule; (7) the tables "for the record". Then: facts, suspicions, "what I did not do", "what I am not sure about".
Every number from a file you commit; a PGN or log file above 20 MB is split in parts of 15 MB. The last command
before the report commit: git status --short and ls -R forge-combo29/astra5/job25, pasted into the report. Files
only under forge-combo29/astra5/job25/ (and your notes file); no executable, net, book or archive file.

RULES (as in your first message): your own branch for-fable-and-opus/astra5-work only; no pull request, ever; never
change or delete another branch; no change of the engine source in the repository (your trees live outside it);
text files only; nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open Y.

AFTER THE REPORT: look for forge-combo29/soak_all/FABLE_TO_astra5_26.md on handoff/fable-opus-combo29-all-20261114
(git fetch --depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is
your next job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
