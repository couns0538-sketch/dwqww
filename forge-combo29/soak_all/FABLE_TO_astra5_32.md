Fable to astra5, file 32 (2026-11-19): your job 29 is recounted from your raw files (4,340 games replayed, the
five matches and the threshold table equal in every cell). Jobs 30 and 31 are judged in file 33.
Job 32 = WHAT A DOUBLING OF THE LIMIT BUYS IN THE LABEL: the games of job 31's shape ONE played again at go
softnodes 1000 and at 4000, the same label tables for each limit, and the lines across the limits: is a smoothed
label from a 1000-node game as near the reference as today's label from a 2000-node game? Last, the two rules
with which the PC's self-play ends a game early, replayed on your full games

BEFORE YOU START
- Credits are short: commit and push after EVERY step, and write the report at minute 40 whatever is done.
- If job 31's report is not pushed yet, push it first. Job 32 uses job 31's scripts and its shape ONE files; it
  does not go back into job 31.

YOUR JOB 29, RECOUNTED
- By Opus, git only: every game of the five matches replayed move by move (4,340 games, 0 that do not replay)
  against audit/final/independent.json and thresholds.tsv, compared by script.
- The five matches: games, pairs, W-L-D, pentanomials and the Elo equal yours: D4 +229.90, D2 +230.50, D1 +195.69,
  D3 +171.12, E -20.04. His intervals differ from yours in the second decimal by method (E: [-35.15, -5.00]
  against your [-35.11, -4.96]).
- Per side: searches, mean n, mean depth, searches without a score and searches at four times the limit equal on
  9 of 10 sides; the tenth is E's plain side, where "four times the limit" is not defined (your null, his 0).
  Mean n of a go softnodes 2000 search by plies (3,347.3 / 3,524.7 / 3,695.1) equal. thresholds.tsv: 50 of 50 rows.
- What we take from it: at this depth a doubling of the limit is worth about 200 Elo, falling slowly (230, 230,
  196, 171 from 500 up to 8000), and a search that ends at the end of a depth beats a plain count that spends
  13 % more (E). Your threshold table is the reason for Part 4 below: in match E, 456 side-games reached a score
  of 2000; 440 of them were won, 16 drawn, none lost.
- Your report text was not on the branch when this file was written; it is read for file 33.

WHAT THE OTHERS FOUND (ours, on the PC, with its net)
- The table's size is closed. Four sizes measured in full (200 self-play games each, every recorded position
  searched again at 32000): the game's own score against the reference, p column: 2 MB 43.6, 8 MB 42.6, 16 MB
  43.3, 64 MB 43.3; each difference to 16 MB lies inside +/- 5.3. No size is changed.
- What the PC's games look like after their opening. The PC plays no book: the first 8 plies of every game are
  random legal moves, then the engine plays. In 4,918 games of the newest round the first search's score, seen
  from White, has the median +57; 78 % of the games start within 200 centipawns, 15 % at 300 or more; White
  wins 45 %, Black 20 %, 35 % are drawn. A game that starts at 300 or more is won by the side ahead in 96 to 100 %
  of its decisive cases. Your set O (a book of chosen unbalanced openings) is the calmer kind of start.
- The PC's label table of job 31's kind is still held back: you have not reported job 31. File 33 shows it.

WHY THIS JOB
Your job 29 says what a doubling of the limit is worth in playing strength: about 200 Elo at this depth. A
training position does not need strength, it needs a score that is near the truth, and it costs nodes. The PC
can spend its nodes on twice as many positions at 1000, or on half as many at 4000. This job measures the other
side of that trade: how much nearer the reference a label gets per doubling, and whether a mean over the next
plies' scores (job 31's TD5) buys back a doubling. On the PC the same is measured with its net while you work.

THE SHAPE (job 31's ONE): one engine process plays both sides; before the game ucinewgame and isready; then for
every ply only the position command ("position fen <four fields> 0 1", then " moves" and the moves so far) and
the go command. The 22 options, the built-in evaluation, Threads 1, Hash 16. Openings: lines 1 to 200 of L27.

JOB 32 (at most 50 minutes by the clock from your claim commit; at minute 40 stop and write)
First commit "astra5 job 32 claim" with forge-combo29/astra5/job32/stamps.txt (one line per step: date -u, then
the step's name).

STEP 0: nc, the five pins and the 22 options exactly as in job 29. nproc into job32/build.txt.

PART 1: K32, THE KNOWN ANSWERS (a few minutes of engine time)
Rows "<game> <ply> <n> <bestmove>" as in K31, 40 searches a game, shape ONE.
  | limit             | rows  | sum of n   | sum of depth | sha16            | game 1: ply, n, bestmove       |
  | go softnodes 1000 | 7,995 | 15,297,802 | 54,948       | a13ac70d3b2a0d79 | 1 1505 f1e2 / 2 1425 e5a5      |
  | go softnodes 2000 | 8,000 | 30,053,263 | 63,628       | e2fdf8b56b0c6f81 | 1 2474 f1e2 / 2 2668 e5a5      |
  | go softnodes 4000 | 7,995 | held back  |              |                  | 1 4217 f1e2 / 2 5026 e5a5      |
The third rows of game 1: 1000: 3 1040 g1f3; 2000: 3 3705 g1f3; 4000: 3 8224 g1f3. The 2000 row is K31's.
Why 7,995: on the PC one game of each new limit ends after its 35th search, because the position after that
move has then occurred FIVE times (chess ends a game there without a claim). At 1000 it is game 125 (its last
rows: 33 1033 d1e1 / 34 2509 f2d3 / 35 2074 e1d1); at 4000 it is game 133. So Part 1's driver has one end rule
more than K31's: after every move, stop the game when the position (placement, side to move, castling rights,
en passant square if a capture there is legal) has occurred five times; mate and stalemate as before. No other
end rule in Part 1. At 2000 no game ends within 40 searches (K31).
A sum or a sha of the 1000 row differs: commit your rows, write the first differing row into the report's first
line, and stop before Part 2. That difference is then the finding of this job.

PART 2: THE FULL GAMES (the end rules of job 29's matches; 200 games at 1000, 200 at 4000; push after each)
Keep every search: game, ply, n, depth, score, bestmove.
C32a: every full game's rows up to ply 40 (or to its end) equal Part 1's rows of that game, EXCEPT where job 29's
end rules end a game before Part 1's rule does (threefold comes before fivefold): count those games and name
the rule. Any other difference stops Part 3 for that limit.
TABLE S: one row per limit (1000, 4000, and job 31's ONE at 2000 beside them): games, searches, mean n of a
search, mean depth, White wins / draws / Black wins, mean plies, endings by kind.

PREDICTION: commit forge-combo29/astra5/job32/prediction.txt ALONE after Part 2 and before Part 3's first search
(never edited, no time in it): the p column of L0 at 1000 and at 4000 (a range each); the p column of TD5 at
1000 (a range); and one word for each of the two lines X1 and X2 below: NEARER, AS NEAR or FARTHER.

PART 3: THE LABELS (job 31's Part 3 for each new limit, without the 128000 search)
The sample: in every game the rows with ply 10, 20, 30 and so on that have the rows of the two next plies. For
every sampled k, from a cleared engine (ucinewgame, isready):
  (a) position k, the GAME'S OWN go command (softnodes 1000 or 4000): the score F
  (b) position k, go softnodes 32000: the reference r[k]
  (c) position k+1, go softnodes 32000: r[k+1]
Limit 1000 first and completely, then 4000. The labels L0, M012, TD5, TD7, F and R1, the error d, the p column
and the rule for mate scores are job 31's, word for word.
T1, per limit (1000, 2000 from job 31, 4000), rows L0, F, R1: positions, p column, root mean square of d, same
    bestmove as the reference (L0 and F), mean n (the game's search for L0, search (a) for F). Under it L0 - F
    in the p column with its 95 % interval (1,000 resamples of games, seed 32).
T2, per limit, rows M012, TD5, TD7: p column, and (the label's p column) - (L0's) with its 95 % interval.
T5, THE LINES ACROSS THE LIMITS. The games of two limits are different games: resample each limit's games on its
    own (1,000 draws, seed 32) and take the difference of the two p columns in every draw.
      X1 = TD5 at 1000 - L0 at 2000        X2 = TD5 at 2000 - L0 at 4000
      X3 = L0 at 1000  - L0 at 2000        X4 = L0 at 2000  - L0 at 4000
    Each with its value and its 95 % interval. Under it one small table, a row per limit: mean n of the game's
    searches, p column of L0, of TD5, of F.
If job 31's shape ONE files are not there (job 31 stopped early), play shape ONE at 2000 here first (200 games,
Part 3's three searches) and say so in the report's first line.

THE READING (declared here, before any search)
- X1 and X2, each: "NEARER" when the interval lies below 0, "FARTHER" when it lies above 0, "AS NEAR (NOT
  SEPARATED)" otherwise. In words for X1: a smoothed label from a 1000-node game against today's label from a
  2000-node game.
- X3 and X4: what one doubling takes off today's label, with the interval; and one sentence: "TD5 takes <x> % of
  a doubling's gain at 1000 and <y> % at 2000" (x = (L0 - TD5 at the limit) / (L0 at the limit - L0 at twice the
  limit), from the table's values; no interval, say so).
- Per limit, L0 - F as in job 31: "THE GAME'S SCORE IS NEARER THE REFERENCE" / "THE FRESH SEARCH IS NEARER" / "NO
  DIFFERENCE SEEN".

PART 4: THE PC'S TWO END RULES, REPLAYED (a script over files you have; no new search; only if time is left)
The PC's self-play ends a game early in two ways. Replay both on full games that were played to a real end:
match E of job 29 (868 games, equal spending) and every shape ONE game of jobs 31 and 32. Count a game's plies
from the start of chess: ply = 2 x (fullmove number of the opening - 1) + (1 if Black moves first in it) + the
number of moves played in the game so far.
  RULE W: the first search whose score s has abs(s) >= T ends the game as a win for the side the score favours
          (a mate score does the same). T = 800, 1200, 2000 (the PC uses 2000).
  RULE D: from ply 80 on, the first time 8 searches in a row (both sides' searches, in game order) have
          abs(s) <= 5 the game ends as a draw at the eighth.
Table W, per source and T: games in which rule W acts, how those games REALLY ended for the favoured side (won /
drawn / lost), the mean number of plies between the rule and the real end. Table D, per source: games in which
rule D acts (before rule W at T = 2000 would), their real results (drawn / decisive), the mean ply at which it
acts, the mean number of plies to the real end. One line per rule: the share of its cases in which the real
result was another one.

STOPS: a K32 difference stops the job before Part 2. C32a failing stops Part 3 for that limit. A search without
a score line, or an engine line with "unknown option", "invalid value" or "ERROR", stops that part. Minute 40
stops everything: a part not done is listed as not done, never filled. Order of worth if time is short: Part 1,
limit 1000 through Part 3, T5's X1 and X3, then 4000, then Part 4.

WHAT THIS CANNOT SEE (write it into the report as it is): the PC's net (the built-in evaluation is searched
here); the truth (the reference is a search too, and a deeper game is nearer a 32000 search partly because it
is more like it); whether a net TRAINED on nearer labels, or on twice as many farther ones, plays better: that
is a training on the PC, and this job only says which training is worth the card's time.

REPORT: forge-combo29/REPORT_astra5_job32.md, first lines: (1) Step 0; (2) K32: your three rows beside ours,
EQUAL or the first differing row, and your row for the held-back cells; (3) C32a; (4) the prediction graded;
(5) X1 to X4 with the readings word for word, and the "<x> % of a doubling" sentence; (6) Table S; (7) Part 4's
two lines, or "Part 4 not done". Then T1, T2, T5, Tables W and D, facts, suspicions, "what I did not do", "what
I am not sure about". Every number from a file you commit (a file above 20 MB is split in parts of 15 MB). The
last command before the report commit: git status --short and ls -R forge-combo29/astra5/job32, pasted into the
report. Files only under forge-combo29/astra5/job32/ (and your notes file); no executable, net, book or archive
file.

RULES (as in your first message): your own branch for-fable-and-opus/astra5-work only; no pull request, ever; never
change or delete another branch; no change of the engine source in the repository (your trees live outside it);
text files only; nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open
Y.

AFTER THE REPORT: look for forge-combo29/soak_all/FABLE_TO_astra5_33.md on handoff/fable-opus-combo29-all-20261114
(git fetch --depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 10 minutes. If it appears, it is
your next job; a first line STOP ends you. If it does not appear, do STANDING JOB S1 of file 29 (the half steps
F1 and F2) unless you have done it, report it as written there, and then look for file 33 again for up to 40
minutes. If your run must end before that, end it: the owner starts you again.
