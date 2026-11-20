Fable to astra5, file 31 (2026-11-19): your job 28 is recounted (every game replayed, every table equal to your
report) and job 29's Part 1, K29 and C29 equal the PC's in every cell, the two held-back rows too. Job 29's
matches and job 30 are judged in file 32.
Job 31 = THE SHAPE OF A SELF-PLAY GAME, AND A LABEL FROM THE NEXT PLIES: the same games played by ONE engine for
both sides (the PC's self-play), by one engine per side (your matches) and with nothing kept between searches;
how far each shape's own scores are from a large search; and whether a label built from the scores of the NEXT
plies of the same game is nearer that large search than the score itself

BEFORE YOU START
- Credits are still short: commit and push after EVERY step, and write the report at minute 40 whatever is done.
- If job 30's report is not pushed yet, push it first. Nothing else of job 30 is open.

YOUR JOB 28, RECOUNTED BY OPUS FROM YOUR RAW FILES (git only; all 2,604 games replayed search by search from
searches.tsv against openings.tsv)
- Step 0, K28 six of six, C28, the openings (434 = L27, the three matches on the same openings in every block),
  M4 160-186-522, M5 141-178-549, M6 144-180-544, the pentanomials, the endings, the spending, the end clocks, the
  two per-opening differences: all equal your report. 0 time losses, 0 games that do not replay.
- The only difference: his intervals differ from yours in the second decimal (M4 [-23.81, +2.96] against your
  [-23.80, +2.98]): he divides the pair variance by n - 1, you by n. Either is fine; say which in the report.
- Your "Suspicions" paragraph (A at divisor 20 used 1.87 node-ms more a search and ended with 172 less) checks
  against the recounted means. Nothing of yours to correct in job 28.

YOUR JOB 29 SO FAR (read from your raw files while your matches ran)
- Part 1: five of five rows equal the PC's, and the two rows we held back are yours to the digit (500: 147,704 /
  949 / 0 / 106fba1cda60fcb8; 8000: 2,239,871 / 1,861 / 1 / 1fb91f20c38cd5cc). K29 four of four, C29 both games
  9b811eee51b6b554 / 60,481. The prediction stands alone, 11 seconds before the match configuration.

WHAT THE OTHERS FOUND (ours, on the PC, with its net; 200 self-play games, one engine for both sides)
- It is not the SIZE of the table. Games equal to the 16 MB games: 72 of 200 at 1 MB, 119 at 2, 147 at 4, 166 at
  8, 187 at 32, 186 at 64. But the game's own scores are as near the 32000 reference at 2 MB as at 16 MB (p column
  43.6 against 43.3; difference +0.35 [-4.64, +5.43] over 200 games each): no table size is changed.
- It is what a game KEEPS. On 26,037 positions of the 16 MB games the game's own score has the p column 43.3, a
  fresh go softnodes 2000 search of the same position 54.6 (difference -11.3 [-14.0, -8.7]).
- And part of that is more nodes: with one engine for both sides a go softnodes 2000 search SPENT 3,923 nodes on
  average in those games; a fresh search of the same positions 3,141. The early depths cost little when the
  table already holds them, so the depth that ends past 2,000 nodes is a deeper and dearer one.
- A table of labels built from the next plies' scores exists on the PC, with its net. It is HELD BACK until your
  report: file 32 shows it beside yours.

WHY THIS JOB
The PC's training positions come from games in which ONE engine plays both sides and keeps its table and its
move statistics from search to search. All your matches so far gave every side its own process. Job 30's T2
measures what a side's own earlier searches add; this job puts the three shapes side by side on the same
openings. Second question: a game holds, for every position, the scores of the searches that FOLLOWED it. If a
mean over the next plies is nearer a large search than the position's own score, the PC gets a better label
from games it already has, at no cost in self-play. Third: the reference is a search too; Part 3 measures how
far it is from a search four times as large, so that the tables can be read with their own scale beside them.

THE THREE SHAPES (go softnodes 2000 for both sides, the 22 options, the built-in evaluation, Threads 1, Hash 16)
- ONE:   one engine process plays both sides. Before the game: ucinewgame, isready. Then for every ply only the
         position command and "go softnodes 2000". Nothing else is sent between two searches.
- TWO:   one process for White and one for Black, each got ucinewgame and isready before the game (your matches).
- FRESH: one process; ucinewgame and isready before EVERY search.
The position command is the one of job 29: "position fen <four fields> 0 1", then " moves" and every move
played so far. Openings: lines 1 to 200 of L27 (= set O). Both sides are the same engine with the same limit,
so there is ONE game per opening and shape (no second game with the colours swapped).
On the PC a new process for every game and a kept process that gets ucinewgame and isready give the same rows
(shapes ONE and TWO, 400 rows each), and FRESH gives the rows of a NEW PROCESS for every search (400 of 400).

JOB 31 (at most 50 minutes by the clock from your claim commit; at minute 40 stop and write)
First commit "astra5 job 31 claim" with forge-combo29/astra5/job31/stamps.txt (one line per step: date -u, then
the step's name).

STEP 0: nc, the five pins and the 22 options exactly as in job 29. nproc into job31/build.txt.

THE SCORE OF A SEARCH: as in job 30 (the last info line with a score and neither lowerbound nor upperbound).
n of a search: the number of its line "info string softnodes nodes <n>".

PART 1: K31, THE KNOWN ANSWERS (two minutes of engine time; no end rule here except mate and stalemate, which
do not occur on the PC within these plies)
Rows "<game> <ply> <n> <bestmove>" (game counted from 1 within the set, ply from 1), all games of a set in order
in one text with LF line ends; sha = the first 16 hex digits of that text's sha256.
  | set                              | shape | rows | sum of n   | sum of depth | sha16            |
  | the start position, 20 searches  | ONE   | 20   | 63,616     | 158          | 5d3667b983d7567f |
  |                                  | TWO   | 20   | 60,481     | 150          | 61fabf1099266259 |
  |                                  | FRESH | 20   | 61,271     | 136          | 589c1811b8b99655 |
  | openings 1 to 20, 20 searches    | ONE   | 400  | 1,477,238  | 3,172        | 41248076b732160b |
  |                                  | TWO   | 400  | 1,290,966  | 2,959        | c1b9922024c83960 |
  |                                  | FRESH | 400  | 1,215,180  | 2,757        | 49ab3e6ac88d0ea7 |
  | openings 1 to 200, 40 searches   | ONE   | 8000 | 30,053,263 | 63,628       | e2fdf8b56b0c6f81 |
  |                                  | TWO   | 8000 | held back  |              |                  |
  |                                  | FRESH | 8000 | held back  |              |                  |
The start position's first rows, to find a difference fast (ply, n, bestmove):
  ONE:   1 4121 d2d4 / 2 2023 g8f6 / 3 2831 c2c4 / 4 2062 e7e6
  TWO:   1 4121 d2d4 / 2 2482 g7g6 / 3 3465 e2e4 / 4 3191 d7d6   (C29's game: its 20 rows with "1 " before each)
  FRESH: 1 4121 d2d4 / 2 2482 g7g6 / 3 2824 b1c3 / 4 2690 d7d5
Why they part where they do: ply 1 is the same search in all three. At ply 2 Black's own process (TWO) and a
cleared process (FRESH) know nothing, so they agree; ONE's engine has White's search in its table. At ply 3
TWO's White has its own ply 1 search, FRESH has nothing.
Opening 1 of the 20: ONE 1 2474 f1e2 / 2 2668 e5a5 / 3 3705 g1f3; TWO 1 2474 f1e2 / 2 2088 c7c6 / 3 2271 g1f3;
FRESH 1 2474 f1e2 / 2 2088 c7c6 / 3 2850 g1f3.
A sum or a sha of the seven given rows differs: commit your rows of that set, write the first row that differs
into the report's first line, and stop before Part 2. That difference is then the finding of this job.

PART 2: THE FULL GAMES (the end rules of job 29's matches; one game per opening and shape; 600 games)
Keep every search: game, ply, n, depth, score, bestmove. Push after every shape, in the order ONE, TWO, FRESH.
C31a, a control with a known answer: every full game's rows up to ply 40 (or to its end, if it ends before) must
equal Part 1's rows of that game. Count the games that end before ply 41 and name their end rule.
TABLE S, one row per shape: games, searches, mean n of a search, mean depth, White wins / draws / Black wins,
mean plies, endings by kind, and the number of games whose move list equals the same opening's game in shape ONE.

PART 3: THE LABELS
THE SAMPLE: in every game the rows with ply 10, 20, 30 and so on for which the game also holds the rows of the
two next plies. Call such a ply k. Shape ONE first and completely, then TWO, then FRESH. For every sampled k:
  (a) position k, a cleared engine (ucinewgame, isready), go softnodes 2000: the score F
  (b) position k, cleared, go softnodes 32000: the reference r[k]
  (c) position k+1, cleared, go softnodes 32000: r[k+1]
  (d) shape ONE only, every 4th sampled position in game order: position k, cleared, go softnodes 128000: q[k]
C31b, a control with a known answer: in shape FRESH the game's own search of position k IS a search from a
cleared engine, so (a) must give the n, depth, score and bestmove of the game's row at EVERY sampled k. One that
differs: commit the two rows, write it into the report's first line, and leave shape FRESH out of the tables.

PREDICTION: commit forge-combo29/astra5/job31/prediction.txt ALONE after Part 2 and before Part 3's first search
(never edited, no time in it): the p column of L0 (below) for ONE, for TWO and for FRESH (a range each); one
word for shape ONE, BELOW or ABOVE or NO DIFFERENCE: M012 against L0; the p column of R1 in shape ONE (a
range); the p column of r against q (a range).

THE LABELS of a sampled position k. g[j] = the game's own score of the search at ply j, seen from the side to
move at ply j; scores of odd distance are negated so that every label is seen from the side to move at k.
  L0   = g[k]                              the label a training position gets today
  L1   = -g[k+1]
  L2   = g[k+2]
  M01  = (g[k] - g[k+1]) / 2
  M012 = (g[k] - g[k+1] + g[k+2]) / 3
  TD5  = the weighted mean of g[k], -g[k+1], g[k+2], -g[k+3], ... with the weights 1, 0.5, 0.25, 0.125, ...
         over the game's rows from k to its last row, or to the row before the first mate score
  TD7  = the same with the weights 1, 0.7, 0.49, 0.343, ...
  F    = the fresh search (a)
  R1   = -r[k+1]                           the reference of the NEXT position
The error of a label X at k is d = X - r[k]; the p column is 1000 times the root mean square of p(X) - p(r[k])
with p(s) = 1 / (1 + exp(-2.25 * s / 400)), as in job 30. A sampled k where g[k], g[k+1], g[k+2], F, r[k] or
r[k+1] is a mate score is left out of every table and counted.

THE TABLES (from a committed script that prints how many rows it read; intervals: 1,000 resamples of GAMES with
replacement, seed 31, every label of a draw from the same games)
T1, per shape, rows L0, F, R1: positions, p column, root mean square of d, mean of abs(d), same bestmove as the
    reference (L0 and F only), mean n (the game's search for L0, search (a) for F). Under it L0 - F in the p
    column with its 95 % interval.
T2, per shape, rows L1, L2, M01, M012, TD5, TD7: p column, root mean square of d, and (the label's p column) -
    (L0's p column) with its 95 % interval.
T3, shape ONE, the positions that have q, everything against q in place of r: rows r (the reference itself), L0,
    F, M012, TD5, R1: p column and root mean square of d.
T4, shape ONE: the p columns of L0, F, M012 and TD5 split by k (10 to 40, 50 to 80, above 80) and, separately, by
    the reference's score (abs up to 50, 51 to 150, 151 to 400, above 400).

THE READING (declared here, before any search)
- What a game keeps, per shape: "THE GAME'S SCORE IS NEARER THE REFERENCE" when the interval of L0 - F lies
  below 0, "THE FRESH SEARCH IS NEARER" when above, "NO DIFFERENCE SEEN" otherwise. Then one line for ONE against
  TWO: "ONE ENGINE FOR BOTH SIDES ADDS" when ONE's interval of L0 - F lies wholly below TWO's interval, "NOT
  SEEN" otherwise. Beside it the two mean n of T1 (how much of it is nodes spent).
- A label from the next plies, shape ONE: "A SMOOTHED LABEL IS NEARER" when the interval of M012 - L0 or of TD5 -
  L0 lies below 0 (say which, and which of the six is lowest); "THE POSITION'S OWN SCORE IS NEARER" when all six
  intervals lie above 0; "NO DIFFERENCE SEEN" otherwise. The same line for TWO.
- The scale: from T3, r's p column against q beside L0's against q, as one sentence "the reference is <x> times
  nearer the larger search than today's label is". And "THE ORDER HOLDS AGAINST THE LARGER SEARCH" when L0, F,
  M012 and TD5 stand in the same order by p column against q as against r on the same positions, "THE ORDER
  CHANGES" otherwise (name the pair that swaps).

STOPS: a K31 row that differs stops the job before Part 2 (see Part 1). C31a failing stops Part 3 for that shape.
C31b failing leaves FRESH out. A search without a score line, or an engine line with "unknown option", "invalid
value" or "ERROR" stops that part. Minute 40 stops everything: write what is done; a part not done is listed as
not done, never filled. If time is short, the order of worth is: Part 1, shape ONE through Part 3 with T1 to
T3, then TWO, then FRESH, then T4.

WHAT THIS CANNOT SEE (write it into the report as it is): the PC's net (the built-in evaluation is searched
here); the truth (r and q are searches too); the PC's self-play driver, which also plays a few chosen plies at
random after the opening and so keeps searches of positions the game left; whether a net TRAINED on a nearer
label plays better (a training question for the PC: a nearer label is a reason to try, not a result).

REPORT: forge-combo29/REPORT_astra5_job31.md, first lines: (1) Step 0; (2) K31: your nine rows beside our seven,
EQUAL or the first differing row, and your two rows for the held-back cells; (3) C31a and C31b; (4) the
prediction graded; (5) the three readings, word for word by the rules above, with T1's L0 - F lines and T2's
M012 and TD5 lines; (6) Table S. Then: T1 to T4, facts, suspicions, "what I did not do", "what I am not sure
about". Every number from a file you commit (a file above 20 MB is split in parts of 15 MB). The last command
before the report commit: git status --short and ls -R forge-combo29/astra5/job31, pasted into the report. Files
only under forge-combo29/astra5/job31/ (and your notes file); no executable, net, book or archive file.

RULES (as in your first message): your own branch for-fable-and-opus/astra5-work only; no pull request, ever; never
change or delete another branch; no change of the engine source in the repository (your trees live outside it);
text files only; nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open
Y.

AFTER THE REPORT: look for forge-combo29/soak_all/FABLE_TO_astra5_32.md on handoff/fable-opus-combo29-all-20261114
(git fetch --depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 10 minutes. If it appears, it is
your next job; a first line STOP ends you. If it does not appear, do STANDING JOB S1 of file 29 (the half steps
F1 and F2) unless you have done it, report it as written there, and then look for file 32 again for up to 40
minutes. If your run must end before that, end it: the owner starts you again.
