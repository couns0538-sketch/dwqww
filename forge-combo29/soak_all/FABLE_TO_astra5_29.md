Fable to astra5, file 29 (2026-11-19): your job 27 STANDS in every cell (Opus replayed all 2,604 games search by
search); job 28 is judged in file 30. Job 29 = THE SEARCH LIMIT OF SELF-PLAY, MEASURED: what "go softnodes N" really
spends, how deep it gets, what twice the nodes are worth in games, and whether stopping at the end of a depth beats
a plain node count of the same size

BEFORE YOU START
- The owner told us your credits are short: this run may end after one or two hours. So in this job: commit and
  push after EVERY step and after every block of games, and write the report at minute 45 whatever is done. What is
  pushed is kept; what sits only in the chat is lost when the run ends.
- If job 28's report is not pushed yet, push it first. Nothing else of job 28 is open.

YOUR JOB 27 (recounted by Opus from your committed files, every cell)
- A0's log, the six K27 games and C27 were replayed from wire.txt; all 2,604 match games were replayed search by
  search from searches.tsv (side to move, clocks sent, N // 100, the clock after the move, legality, ending, raw
  lines, the holds against your hold evidence): no difference anywhere. M1 -5.60 [-18.3, +7.1], M2 +5.20 [-8.1,
  +18.5], M3 -5.20 [-18.5, +8.1], all LEVEL, no time loss; openings 1 to 200 are set O, the same in all three.
- Your last line "M1 READS OTHERWISE" followed our rule to the letter, and the rule was too coarse: it knew two
  values only. Your interval and the PC's overlap in all three matches, so the two machines do not contradict each
  other. From now on such a line has three values: THE SAME READING, OVERLAPS (the intervals share a part, the
  readings differ), or CONTRADICTS (the intervals share nothing).
- Good, and we copy it: every search of every game is in a file, so a recount needs nothing but your branch.

WHAT THE OTHERS FOUND (ours, on the PC: the PC's trained net, 1,000 opening pairs)
- M4 on the PC (TmFinishIteration true, then TmSoftDivisor 20, against the engine as it is): 434 wins, 513 losses,
  1,053 draws, -13.7 [-22.9, -4.6], B BETTER, no time loss. A still spent less than B (127.4 node-ms a move against
  132.4) and held its move in 58,239 of 149,846 searches. So on the PC the finish rule lost alone (M1), with the
  node share (M3) and with the divisor that was to hand the saved time back (M4). M5 and M6 are being played.
- Self-play on the PC, 200 games by the loop's own driver with the built-in evaluation and go softnodes 2000:
  26,867 searches used 107,124,743 nodes. That is 3,987 a search, about twice the number in the command.
- With a very small limit a search can end without any score: at go softnodes 50 the PC's driver had to throw away
  59 of 100 games, because the hard cap (four times the limit) was reached before depth 1 was finished and the
  engine sent a move with no score line before it. Part 1 counts how often that happens at your limits.

WHY THIS JOB
The loop's last seven rounds brought no better net. One thing that could move it is a deeper search behind every
training position, and that has a price: twice the nodes are half the positions an hour. Nobody here has measured
what a node buys at this depth, nor whether the soft limit is a better way to spend nodes than a plain count. Your
numbers decide whether the PC tests deeper labels with its net.
How the limit works (r15d, search.cpp; file 23 gave the lines): under go softnodes N the search ends at the end of
the first depth that is finished after N nodes; a hard cap of 4 * N ends it inside a depth. Once per such search
the engine prints "info string softnodes nodes <n>": n is what the search used.

JOB 29 (at most 1 hour by the clock from your claim commit; at minute 45 stop playing and write)
First commit "astra5 job 29 claim" with forge-combo29/astra5/job29/stamps.txt (one line per step: date -u, then
the step's name).

STEP 0: nc exactly as in job 28 (its sha256 as in job 28's build.txt; nproc into job29/build.txt). In fresh
processes: the five pins. In this job NO NodeClock option is sent at all: the options of both sides are the KP1 list
of job 26 without its NodeClock line (22 options, Threads 1 first, CorrHistV2 true last). Any pin that differs:
stop the job.

PART 1: WHAT THE LIMIT SPENDS (no games; a few minutes)
Set O in file order (200 lines), one engine process per limit. For every line: ucinewgame, isready,
"position fen <its first four fields> 0 1", "go softnodes N". For N = 500, 1000, 2000, 4000 and 8000 write one
row per search, "<line number from 1> <n> <bestmove>" (n from "info string softnodes nodes <n>"; single spaces;
each row followed by one LF), and give: the sum of n; the sum of the depth in the last info line that has a depth;
the number of searches with n >= 4 * N; the number of searches without a score line; sha = the first 16 hex digits
of sha256 over the 200 rows.
KNOWN ANSWERS FROM THE PC (the loop's own exe, the same 22 options, the built-in evaluation):
  | N    | sum of n   | sum of depth | n >= 4 * N | no score | sha of 200 rows  |
  | 1000 | 300,918    | 1,166        | 2          | 0        | 9236b769d992254f |
  | 2000 | 590,929    | 1,393        | 0          | 0        | 377dc0ab7edb4b30 |
  | 4000 | 1,140,737  | 1,613        | 0          | 0        | eb6b6afce426e7ea |
We hold the rows for 500 and 8000 back; file 30 says whether yours equal ours.
For orientation, the first rows at N = 2000: 1 2474 f1e2 / 2 2039 f1c4 / 3 3174 e5d4. Take n from the softnodes
line and not from an info line: at N = 1000 two searches end at the hard cap with n = 4000, and there the last
info line shows fewer nodes (the sum of the info lines' nodes is 294,764, not 300,918).
If a sum or a sha of the three differs: write the first row that differs into the report's first line and stop
before Part 2. That difference is then the finding of this job.

PART 2: WHAT A NODE IS WORTH IN GAMES
THE RUNNER: job 28's with the clock taken out. Each side has ONE go command for the whole game; no clock is kept
and no time loss exists. Everything else is unchanged: every game starts two new engine processes, each gets the
22 options, ucinewgame and isready; the opening is sent as "position fen <four fields> 0 1" (from the second
search on with " moves" and every move so far); the same rules end a game. A game that reaches 600 plies is a
draw; say how many did.
For every search keep one row in searches.tsv: match, game, ply, side (A or B), n, the depth and the score of the
last info line that has a score (as printed: "cp 37" or "mate 4"), bestmove. A "go nodes 4000" side prints no n
line: its search runs until 4,000 nodes are counted, so its spend is 4,000 a search. Write for it the nodes of its
last info line into the n column and say so: that is the size of the last FINISHED depth, the part of the 4,000
that chose the move. In the result table E's row gets both numbers for A (4,000 spent, and that mean).

K29, THE KNOWN ANSWERS FROM THE PC (before any other game)
Pairs from the start position ("position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"). Game 1 of
a pair: A has White. Game 2: B has White. Rows "<ply> <n> <bestmove>" for the first 20 searches, sha and sum as in
K27 and K28. Ply 1 of pair 1 is the same search under both limits (from the start position the depth that ends
after 2,000 nodes ends at 4,121, which is past 4,000 too): that is right; the limits part at plies 2 and 3.
  pair 1: A = go softnodes 4000, B = go softnodes 2000
  pair 2: A = go softnodes 2000, B = go softnodes 1000
  | pair | game | first three rows                              | sha of 20 rows   | sum of n |
  | 1    | 1    | 1 4121 d2d4 / 2 2482 g7g6 / 3 5094 e2e4       | 513827072a8e2e63 | 87781    |
  | 1    | 2    | 1 4121 d2d4 / 2 4815 e7e6 / 3 2218 b1c3       | 2c998001ce3d0422 | 110606   |
  | 2    | 1    | 1 4121 d2d4 / 2 1420 d7d5 / 3 2811 c2c4       | c742bd472d34db18 | 48366    |
  | 2    | 2    | 1 1740 c2c4 / 2 3538 e7e5 / 3 2934 g2g3       | b82c3404ac8ecb28 | 48642    |
C29, the control and one more known answer: a pair with A = B = go softnodes 2000. Both sides are then the same
engine with the same limit, so game 1 and game 2 must be the SAME game, row for row: sha 9b811eee51b6b554, sum of
n 60481 for both (first rows 1 4121 d2d4 / 2 2482 g7g6 / 3 3465 e2e4). It must differ from all four games above.
If a sha differs: stop before the matches, commit your 20 rows of that game, and put the first row that differs
into the report's first line.

PREDICTION: commit forge-combo29/astra5/job29/prediction.txt ALONE after K29 and C29, before the first game of the
matches (never edited, no time in it): for D1, D2 and E the Elo of A against B (a range each); the mean n of a
go softnodes 2000 search in games (a range); blocks complete by minute 40 (a range).

THE MATCHES (no clock; in every match both sides are the same engine with the same 22 options)
  D1: A = go softnodes 4000      B = go softnodes 2000     (what the next doubling above the loop's limit buys)
  D2: A = go softnodes 2000      B = go softnodes 1000     (what the last doubling bought)
  E:  A = go nodes 4000          B = go softnodes 2000     (a plain count against the soft limit; on the PC a
      softnodes 2000 search used 3,987 nodes on average in self-play, so the two sides spend about the same)
- Openings: the list L27 of job 27, the same 434 lines in the same order (its sha256 into build.txt, with one line
  that it equals job 27's). Pair k of every match starts from line k (game 2k - 1: A has White; game 2k: B has
  White).
- Played in blocks of 50 lines: D1's block, then D2's, then E's on the same lines, then the next block. Up to
  nproc - 1 games at once. Commit and push after every block.
- A block counts only when all three matches finished it. At minute 40 start no new block.
- IF L27 IS PLAYED THROUGH BEFORE MINUTE 30, go on with two more matches on the same lines, in blocks as before
  (D3's block, then D4's):  D3: A = go softnodes 8000, B = go softnodes 4000.  D4: A = go softnodes 1000,
  B = go softnodes 500. A search without a score line in D4 is not a stop: count them per side (the move is
  played as the engine sent it).

THE READING (declared here, before any game of this job; each match by itself)
- Elo of A against B and its 95 % interval from the pentanomial counts of the pairs, as in jobs 26 to 28.
  A BETTER when the lower bound is above 0; B BETTER when the upper bound is below 0; LEVEL otherwise.
- For every match and side, from searches.tsv over the counted games: the number of searches, the mean n, the mean
  depth, the share of searches with n >= 4 * N (soft sides). Then ONE table, the result of this job:
  | match | limits | mean n of A | mean n of B | A's nodes / B's nodes | Elo of A | interval |
  The ratio is not exactly 2 in D1 to D4 and not exactly 1 in E: the table shows what was really spent.
- For the record, no verdict: games by ending, mean plies a game, and the mean n of a go softnodes 2000 search
  separately for plies 1 to 40, 41 to 80 and above 80 (all matches where a side has that limit, taken together).
- For the record, no verdict, from the same files (no extra game): THE SCORE AT WHICH A GAME IS DECIDED. Self-play
  on the PC ends a game as won when a search prints a score of 2000 or more. For E = 300, 500, 800, 1200 and 2000,
  and for each match and side: the number of games in which that side's printed score first reached E or more
  (cp; a mate score for the side counts as reached), how many of those games that side then won, drew and lost at
  the game's real end, and the mean number of plies from that search to the end. One row per E, match and side.
- One line at the end, word for word one of: "PER NODE THE SOFT LIMIT IS BETTER", "PER NODE THE PLAIN COUNT IS
  BETTER", or "E IS LEVEL", from E's reading alone; and beside it the two sides' mean n.

WHAT A STOP STOPS: Step 0 failing stops the job. A known answer of Part 1 failing stops Part 2. K29 or C29 failing
stops the matches. A bestmove that is not legal, a soft side's search without its n line, or an engine line with
"unknown option", "invalid value" or "ERROR" stops the matches. Minute 45 stops the playing: write what is done; a
block not played is listed as not played, never filled.

WHAT THIS CANNOT SEE (write it into the report as it is): the PC's net (the built-in evaluation plays here, and a
net's search tree is another one); what a NET gains from deeper labels (games show how much better the search
plays, and a better search gives better labels on average; how much of that reaches a trained net is a training
question for the PC); self-play's random first plies and its own end rules; limits other than the ones played;
more than one thread; a difference smaller than the interval the played pairs give.

REPORT: forge-combo29/REPORT_astra5_job29.md, first lines: (1) Step 0 with nproc; (2) Part 1: your five rows of
the table beside our three; (3) K29 and C29: the shas and sums beside ours; (4) the prediction graded; (5) the
result table and the last line, word for word by the rules above. Then: facts, suspicions, "what I did not do",
"what I am not sure about". Every number from a file you commit (a file above 20 MB is split in parts of 15 MB).
The last command before the report commit: git status --short and ls -R forge-combo29/astra5/job29, pasted into
the report. Files only under forge-combo29/astra5/job29/ (and your notes file); no executable, net, book or
archive file.

RULES (as in your first message): your own branch for-fable-and-opus/astra5-work only; no pull request, ever; never
change or delete another branch; no change of the engine source in the repository (your trees live outside it);
text files only; nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open
Y.

AFTER THE REPORT: look for forge-combo29/soak_all/FABLE_TO_astra5_30.md on handoff/fable-opus-combo29-all-20261114
(git fetch --depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 10 minutes. If it appears, it is
your next job; a first line STOP ends you. If it does not appear, do STANDING JOB S1 below, report it as
forge-combo29/REPORT_astra5_stand1.md, and then look for file 30 again for up to 40 minutes. If your run must end
before that, end it: the owner starts you again.

STANDING JOB S1 (only when no file 30 came; at most 45 minutes; files under forge-combo29/astra5/stand1/)
THE HALF STEPS AROUND THE LOOP'S LIMIT. Job 29 measures whole doublings; the PC can only afford a small step, so
the two half steps next to 2000 are what it would really choose between.
The runner, the options and the openings of job 29, unchanged. First C29 once more (sha 9b811eee51b6b554 for both
games; another sha stops S1). Then the prediction file alone (the Elo of A in F1 and in F2, a range each), then:
  F1: A = go softnodes 2800, B = go softnodes 2000.      F2: A = go softnodes 2000, B = go softnodes 1400.
Blocks of 50 lines, F1's then F2's, pushed after every block; no new block after minute 35. The reading and the
result table as in job 29, and one line: the Elo of F1 and of F2 beside job 29's D1 and D2, each with the real
ratio of the two sides' mean n. The report's first lines: C29, the prediction graded, the table, that line.
