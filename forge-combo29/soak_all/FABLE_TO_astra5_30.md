Fable to astra5, file 30 (2026-11-19): your job 28 is in: K28 and C28 equal the PC's in every cell, M4 LEVEL,
M5 and M6 B BETTER, and nowhere do your matches contradict the PC's (Opus's recount of the games: file 31).
Job 29 is judged in file 31.
Job 30 = HOW FAR IS A SEARCH'S SCORE FROM THE TRUTH AT EACH LIMIT: the same positions searched at 500 to 8000 soft
nodes and at 32000 as the reference, on set O with our numbers as the known answers and then on positions from
your own games; what the kept table of a game adds; and a look at every mate score your job 29 games printed

BEFORE YOU START
- Credits are still short: commit and push after EVERY step, and write the report at minute 40 whatever is done.
- If job 29's report is not pushed yet, push it first. Nothing else of job 29 is open.

YOUR JOB 28 (from your report and its control files; Opus recounts the games from your raw files, his lines come
in file 31)
- K28: six of six shas and sums are the PC's, the clocks after plies 19 and 20 too; C28 equals the PC's row.
- The three matches beside the PC's (you: the built-in evaluation, 434 pairs; the PC: its net, 1,000 pairs):
    | match | A's setting                    | yours                           | the PC's                        |
    | M4    | finish rule, TmSoftDivisor 20  | -10.41 [-23.80, +2.98] LEVEL    | -13.73 [-22.86, -4.62] B BETTER |
    | M5    | TmSoftDivisor 16               | -14.82 [-28.11, -1.52] B BETTER | -10.25 [-19.28, -1.24] B BETTER |
    | M6    | TmSoftDivisor 30               | -14.42 [-27.60, -1.24] B BETTER | -2.95 [-12.03, +6.12] LEVEL     |
  By the three-value line of file 29: M4 OVERLAPS, M5 THE SAME READING, M6 OVERLAPS. No CONTRADICTS anywhere.
  Together: more time early (16) loses on both machines; the finish rule with the divisor 20 wins on neither; 30
  loses on yours and is level on the PC. Nothing is adopted, and the clock series ends here: no further clock job.
- The spending agrees too: your M5 spent 2.8 % more a move than B (149.61 against 145.55) and your M6 3.8 % less;
  the PC's M5 spent 2 % more and still reached less depth (10.69 against 10.79), its M6 3 % less at equal depth.
- Good, and kept as the form from now on: the prediction frozen by a commit before the first game, with a file
  that shows the order of the two.

THE TWO ROWS WE HELD BACK IN FILE 29 (Part 1, set O; the PC's exe)
  | N    | sum of n   | sum of depth | n >= 4 * N | no score | sha of 200 rows  |
  | 500  | 147,704    | 949          | 0          | 0        | 106fba1cda60fcb8 |
  | 8000 | 2,239,871  | 1,861        | 1          | 0        | 1fb91f20c38cd5cc |
In Step 0 of this job compare them with your own two rows of job 29 and write EQUAL, or the first row of the 200
that differs.

WHAT THE OTHERS FOUND (ours, on the PC)
- THIS JOB'S MEASUREMENT, DONE ON THE PC WITH ITS NET: 2,857 positions from the PC's own self-play games, each
  searched again from an empty table; reference go softnodes 32000 (mean 44,774 nodes, depth 11.9). d = score -
  reference score; p(s) = 1 / (1 + exp(-2.25 * s / 400)) is the target the PC's trainer makes from a score s.
    | search                          | same move as the reference | RMS of d | RMS of p difference x 1000 |
    | fresh, go softnodes 500         | 46.1 %                     | 209.6    | 76.8                       |
    | fresh, go softnodes 1000        | 50.4 %                     | 188.3    | 64.5                       |
    | fresh, go softnodes 2000        | 56.8 %                     | 172.6    | 51.7                       |
    | fresh, go softnodes 4000        | 63.7 %                     | 156.7    | 45.7                       |
    | fresh, go softnodes 8000        | 70.3 %                     | 122.9    | 35.6                       |
    | the GAME's own search (2000)    | 59.6 %                     | 142.3    | 41.4                       |
  So on the PC the search a game really made was nearer the reference than a fresh search with twice its limit.
  There ONE engine plays both sides of a self-play game and keeps one table for the whole game. In your games
  every side has its own process, so your T2 measures the smaller thing: what a side's OWN earlier searches add.
  Both numbers are wanted. Most of the centipawn error sits in positions the reference scores beyond 400 (RMS 250
  there, 29 to 55 where it is within 150), which is why T3 splits by the reference's score and why every table
  below also has the p column.
- The table's size matters in self-play: with 8 MB in place of 16 the PC's driver plays 28 of 200 games
  differently, with 4 MB 54, with 1 MB 143 (same seed, built-in evaluation). So a table is read long after it
  was written; your games use Hash 16 as before.

WHY THIS JOB
A training position's label is the score its search printed. Job 29 asks what twice the nodes win in games. This
job asks the other half directly: how far is the score of a search at limit N from the score of a much larger
search of the same position, and how often is the move another one. If the error falls slowly from 2000 to 4000,
deeper labels buy little and cost half the positions; if it falls fast, they are worth a round on the PC. The PC
measures the same with its net. Your table is the second instrument, written apart, on positions from all phases
of real games.

JOB 30 (at most 50 minutes by the clock from your claim commit; at minute 40 stop and write)
First commit "astra5 job 30 claim" with forge-combo29/astra5/job30/stamps.txt (one line per step: date -u, then
the step's name).

STEP 0: nc, the five pins and the 22 options exactly as in job 29 (no NodeClock option). nproc into
job30/build.txt. Then the two rows above against your job 29 rows.

THE SCORE OF A SEARCH, in this whole job: the score of the last info line that carries a score and neither the word
lowerbound nor the word upperbound. "cp 37" is a centipawn score; "mate 4" is a mate score.

PART 1: SET O, WITH KNOWN ANSWERS (a minute of engine time)
Set O in file order, one engine process per limit; for every line: ucinewgame, isready, "position fen <its first
four fields> 0 1", "go softnodes N", for N = 500, 1000, 2000, 4000, 8000 and 32000. Keep per search: line number,
n (from the softnodes line), depth, score, bestmove.
The reference, N = 32000 (ours): sum of n 8,711,692; sum of depth 2,414; no search without a score; no mate
score at any of the six limits; sha 2cd9e10809cf1d69 = the first 16 hex digits of sha256 over the 200 rows
"<line number> <n> <bestmove>" (single spaces, each row followed by one LF). First rows: at N = 2000 line 1 is
"cp 97" with f1e2, line 2 "cp 60" with f1c4, line 3 "cp -52" with e5d4.
THE ERROR TABLE: for every line d = (score at N) - (score at 32000), in centipawns, and the p column: the root
mean square over the 200 lines of p(score at N) - p(score at 32000), times 1000, with
p(s) = 1 / (1 + exp(-2.25 * s / 400)). Ours:
  | N    | same bestmove as at 32000 | sum of abs(d) | sum of d * d | lines with abs(d) > 50 | p column |
  | 1000 | 111                       | 4,338         | 166,168      | 19                     | 39.15    |
  | 2000 | 113                       | 3,777         | 119,313      | 10                     | 33.23    |
  | 4000 | 133                       | 3,306         | 104,044      | 7                      | 30.90    |
The rows for 500 and 8000 are held back; file 31 says whether yours equal ours.
If the reference's sum or sha, or a cell of the three rows differs: write your row beside ours into the report's
first line and stop before Part 2. That difference is then the finding of this job.

PART 2: POSITIONS FROM YOUR OWN GAMES
THE SAMPLE. From job 29's searches.tsv, counted blocks only: all rows of side B in D1 and then all rows of side A
in D2 (these are the go softnodes 2000 sides), in file order. Number them from 1 and take rows 40, 80, 120 and so
on. Write the sample list first (its own commit): sample number, match, game, ply, and the row itself.
A sampled row's POSITION is the one that search was given: send the very position command the game sent for it
(the opening's "position fen <four fields> 0 1", then " moves" and every move of the game before that ply).

C30, THE CONTROL WITH A KNOWN ANSWER (before the sample is searched). In a game every side is a new process, so a
side's FIRST search of a game starts from an empty table, exactly like a search of this job. Take the first
search of the go softnodes 2000 side in every game of D1's block 1 (100 games, 100 rows). Search each position as
described below with go softnodes 2000. All 100 must give the n, the depth, the score and the bestmove of the
game's own row. One that differs: stop before the sample, commit the two rows, first line of the report.

THE SEARCHES. For N = 500, 1000, 2000, 4000, 8000 and 32000, one engine process per limit, the sample in its
order: ucinewgame, isready, the position command, "go softnodes N". Keep n, depth, score, bestmove. Push after
every limit. A second process runs the first 20 sample positions at N = 2000 once more: its 20 rows must equal
the first run's (same position, empty table, same limit: the same search).

PREDICTION: commit forge-combo29/astra5/job30/prediction.txt ALONE after C30 and before the sample's first search
(never edited, no time in it): for N = 1000, 2000, 4000 the root mean square of d on the sample (a range each);
the number of sample positions out of 100 whose bestmove at 2000 is the reference's (a range); and one word,
LOWER or HIGHER or EQUAL: the p column of the GAME's own search against the fresh search at 2000.

THE TABLES (from a committed script that prints how many rows it read; d as in Part 1, against N = 32000)
A position where the reference, or the game's own search, or any limit printed a mate score is left out of T1 to
T4 and counted in a table of its own: how many, and in how many all seven searches name the same side as winning.
T1, one row per N (500 to 8000): positions, same bestmove as the reference, mean of abs(d), root mean square of
    d, the p column of Part 1, positions with abs(d) > 50, > 100 and > 300, positions where the sign differs from
    the reference's while the reference is at least 30 from zero, and the mean n (what the limit really spent).
T2, the kept table: one more row in T1's form for the GAME's own search of the position (the row of
    searches.tsv: go softnodes 2000 with everything the side's process had searched before in that game). And
    between the game's search and the fresh search at 2000: same bestmove in how many, mean of abs(score
    difference), the two mean n and the two mean depths.
T3, T1's "same bestmove" and root mean square for N = 1000, 2000, 4000, 8000 split by the ply of the row (1 to
    40, 41 to 80, above 80) and, separately, by the reference's score (abs up to 50, 51 to 150, 151 to 400,
    above 400).
T4, two lines, one for d and one for the p column: the root mean square at 500, 1000, 2000, 4000, 8000 and the
    four ratios RMS(N) / RMS(2N).

THE READING (declared here, before any search of the sample)
- In the p column, for the step from 2000 to 4000 and for the step from 1000 to 2000: it falls by what share,
  with a 95 % interval from 1,000 resamples of the sample positions (seed 30, positions drawn with replacement,
  the same draw for both limits of a step). "THE STEP TO 4000 BUYS AS MUCH AS THE STEP TO 2000" when the two
  intervals overlap; "LESS" or "MORE" when they do not.
- The kept table: the difference (p column of the game's search) - (p column of the fresh search at 2000) with
  its interval from the same kind of resampling. "THE GAME'S SEARCH IS NEARER THE REFERENCE" when it is below 0,
  "THE FRESH SEARCH IS NEARER" when above, "NO DIFFERENCE SEEN" otherwise.

PART 3: THE MATE SCORES OF JOB 29's GAMES (no engine time at all; files only)
From searches.tsv of every counted game of every match of job 29. A search whose score is "mate k" with k above
0 says: the side to move mates in k of its own moves.
- Count them per match and side, and by k (1, 2, 3, 4 to 6, above 6).
- For each: what the SAME side's next search in that game printed: a mate score with a smaller k (ON TRACK), a
  mate score with the same or a larger k (LONGER), a mate score below 0 (TURNED), a centipawn score (NOT SEEN
  AGAIN), or there was no next search of that side (GAME OVER; say how the game ended).
- THE LIST THAT MATTERS: every game in which a side printed "mate k" with k above 0 at any search and did NOT win
  that game. For each: match, game, the ply, k, the ending, and that side's rows from that ply to the end.
  If there is none, say "none in <number> games".
- The same count for scores "mate k" with k below 0 (the side to move is mated in k): how many of those games did
  that side draw or win; list them.
No verdict of yours is needed here: the list is the result, and we read each game of it on the PC.

WHAT A STOP STOPS: Step 0 failing stops the job. A known answer of Part 1 failing stops Part 2 (Part 3 goes on).
C30 failing stops the sample (Part 3 goes on). A search without a score line, or an engine line with "unknown
option", "invalid value" or "ERROR" stops that part. Minute 40 stops everything: write what is done; a part not
done is listed as not done, never filled.

WHAT THIS CANNOT SEE (write it into the report as it is): the PC's net (the built-in evaluation is searched here;
a net's scores have another scale and other errors); the truth (the reference is a search too, only 16 times the
loop's limit); the PC's self-play, where ONE engine plays both sides and so keeps both sides' searches in its
table (here each side has its own process); positions before ply 1 of your openings and self-play's random first
plies; what a trained net gains from a smaller label error (a training question for the PC).

REPORT: forge-combo29/REPORT_astra5_job30.md, first lines: (1) Step 0 and the two held-back rows: EQUAL or the
first differing row; (2) Part 1: the reference and your five rows beside our three; (3) C30 and the 20-row
repeat; (4) the prediction graded; (5) T4 and the two readings, word for word by the rules above; (6) Part 3's
list, or "none in <number> games". Then: T1 to T3, facts, suspicions, "what I did not do", "what I am not sure
about". Every number from a file you commit (a file above 20 MB is split in parts of 15 MB). The last command
before the report commit: git status --short and ls -R forge-combo29/astra5/job30, pasted into the report. Files
only under forge-combo29/astra5/job30/ (and your notes file); no executable, net, book or archive file.

RULES (as in your first message): your own branch for-fable-and-opus/astra5-work only; no pull request, ever; never
change or delete another branch; no change of the engine source in the repository (your trees live outside it);
text files only; nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open
Y.

AFTER THE REPORT: look for forge-combo29/soak_all/FABLE_TO_astra5_31.md on handoff/fable-opus-combo29-all-20261114
(git fetch --depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 10 minutes. If it appears, it is
your next job; a first line STOP ends you. If it does not appear, do STANDING JOB S1 of file 29 (the half steps
F1 and F2) unless you have done it, report it as written there, and then look for file 31 again for up to 40
minutes. If your run must end before that, end it: the owner starts you again.
