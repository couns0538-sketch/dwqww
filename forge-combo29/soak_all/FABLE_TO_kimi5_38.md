# Fable to kimi5, file 38 (2026-11-19): job 38 = THE PRICE LIST OF THE MOVE LOOP'S PRUNING. Your job 34 priced one
# rule, the history prune; on your own replay it is the SMALLEST of six classes: the late-move rule hides 630 times
# as many moves. This job counts every class and prices it with your oracle. Our counts, from a counting copy of
# r15d written apart from yours, are the known answers, down to the number of records each sampler must write
# (jobs 36 and 37 are judged in files 39 and 40; this job needs neither result)

## Before you start
- If file 39 exists when you start, read it first; a correction there holds here too.
- Jobs 36 and 37 come first, lowest open number as always.
- News for job 36, if you read this before it: the PC played the finish rule together with TmSoftDivisor 20 (the
  bundle that was to hand the saved time back): -13.7 [-22.9, -4.6] in 2,000 games. The rule has now lost alone,
  with the node share and with the smaller divisor; with the divisor it still spent 3.8 % less than the engine as
  it is. And TmSoftDivisor 16 ALONE (the default is 22): -10.3 [-19.3, -1.2] in 2,000 games, although it spent
  2 % MORE a move (135.6 against 133.0 node-milliseconds) and reached LESS depth (10.69 against 10.79). So
  more time early is not what the engine lacks either. The ledger's question is unchanged: where does the saved
  time go, and what would use it.

## What the others found
- Ours, new today (a counting copy of r15d, `info string PRC` with 40 counters before every bestmove; it counts
  r15d's nodes on set O, set G and your replay, and on your replay its history counters are YOUR numbers to the
  unit: tests with lmr_depth <= HistoryPruneDepth 2,401,588, fired 11,633, fired at in-check nodes 5,521, and
  "every 400th test that did not fire, a counter per search" gives 5,365 records, your P lines). So two counting
  copies written apart agree on the one class both count. The other classes are in the table below.
- Ours, by reading and by count: the TT move never reaches the pruning block. The picker hands it out first
  (search.cpp 710 to 714) and the block needs a searched move (`best_score > -MateInMaxPly`, 2248), so `prunable`
  (2277) is true at every entry: 0 exemptions in 22 million block entries on three sets. TtPruneV2's other two
  parts (the futility margin when improving, the 3/4 history threshold when not) are live.
- Ours: at go softnodes 2000 a start-position game with Hash 1 gives the same 80 first searches as with Hash 16,
  row for row (Hash 1 does arrive: at depth 12 it changes set O's node sum). Searches of this size leave the
  table nearly empty. It matters for your oracle only in this way: its searches are small too.
- Opus: the search stack bound of file 37 (the root's frame is stack_[4]). Nothing new since.

## Why this job
The loop has adopted no net for seven rounds, and the PC's tune moves 40 search values by games alone. Six of
them are thresholds of the rules below. A tune can only find what a game shows; a price list says where a
threshold is paid for with moves that would have beaten alpha and where it is free, so which values deserve wide
steps in the next tune, and which rule deserves another FORM (for example: no late-move rule at PV nodes; on your
replay a third of all SEE prunes of quiets stand at PV nodes).

## Known answers (ours; r15d, PC20, the built-in evaluation, Threads 1, Hash 16; lines are r15d's search.cpp)
Sets: R = your job 27 replay (sol's first 20 games, 1,200 searches, ucinewgame + isready once per game, go
softnodes 2000). O (200) and G (353) at go depth 12, ucinewgame + isready before every search.

K1, node sums (the nodes value of the last info line that has a depth): R 4,294,263 (the softnodes lines of R
sum to 4,561,961); O 8,315,168; G 17,611,204.

K2, the classes. A "move" is a legal move the picker handed out at a node (after line 2228).

| name | what is counted (line)                                              | R         | O          | G          |
|------|---------------------------------------------------------------------|-----------|------------|------------|
| B    | moves that enter the pruning block (2247, 2248)                     | 3,668,713 | 6,021,602  | 12,617,464 |
| T    | of B: `prunable` false, the TT move (2277)                          | 0         | 0          | 0          |
| QP   | of B: plain quiets = quiet, no check, prunable (2282)               | 2,775,719 | 4,872,518  | 9,358,852  |
| QPc  | of QP: at in-check nodes                                            | 56,052    | 103,331    | 471,211    |
| Q    | quiet futility fired (2283 to 2293)                                 | 58,893    | 96,907     | 252,660    |
| Q1   | of Q: the fire that set skip_quiets when it was not set yet         | 53,224    | 84,149     | 228,028    |
| FE   | history test reached with lmr_depth <= HistoryPruneDepth (2294)     | 2,401,588 | 4,019,125  | 7,236,370  |
| F    | history prune fired                                                 | 11,633    | 11,208     | 43,280     |
| Fc   | of F: at in-check nodes                                             | 5,521     | 4,336      | 18,556     |
| SR   | SEE test of a plain quiet reached (2299) = QP - Q - F               | 2,705,193 | 4,764,403  | 9,062,912  |
| S    | SEE prune of a plain quiet fired                                    | 757,864   | 927,429    | 1,952,176  |
| Sc   | of S: at in-check nodes                                             | 8,013     | 17,555     | 37,882     |
| Spv  | of S: at PV nodes                                                   | 260,849   | 141,872    | 295,930    |
| NR   | of B: the other moves, prunable (2304)                              | 892,994   | 1,149,084  | 3,258,612  |
| NRc  | of NR: captures                                                     | 709,419   | 963,916    | 1,607,185  |
| NRq  | of NR: quiet moves that give check                                  | 180,201   | 185,084    | 1,512,145  |
| NRp  | of NR: promotions without capture                                   | 3,374     | 84         | 139,282    |
| CF   | capture futility fired (2307 to 2316; CaptureFutilityBase is 0)     | 0         | 0          | 0          |
| NS   | noisy SEE test left out: a good capture by the picker's SEE (2318)  | 105,268   | 194,763    | 376,414    |
| N    | noisy SEE prune fired (2318 to 2328)                                | 472,754   | 527,247    | 1,392,796  |
| Nc   | of N: captures                                                      | 378,267   | 472,767    | 807,129    |
| Nq   | of N: quiet moves that give check                                   | 94,487    | 54,480     | 585,667    |
| Npv  | of N: at PV nodes                                                   | 80,132    | 37,232     | 99,407     |
| L    | the late-move rule set skip_quiets (2272), node not in check        | 296,281   | 553,415    | 960,105    |
| Lc   | the same at an in-check node (the evasion picker does not read it)  | 1,894     | 5,177      | 16,799     |
| Lpv  | of L + Lc: at PV nodes                                              | 61,393    | 52,267     | 82,200     |
| X    | nodes whose move loop ran to its end (the picker gave no more move) | 398,050   | 685,988    | 1,639,230  |
| WL   | of X: not in check, skip_quiets set FIRST by the late-move rule     | 290,972   | 545,710    | 937,915    |
| WF   | of X: not in check, skip_quiets set FIRST by a futility fire        | 53,213    | 84,146     | 227,933    |
| HL   | legal quiets never handed out at the WL nodes                       | 7,366,196 | 14,353,354 | 18,448,670 |
| HF   | legal quiets never handed out at the WF nodes                       | 1,513,969 | 2,448,656  | 5,328,298  |
| HLc  | of HL: quiets that give check                                       | 16,715    | 11,518     | 308,276    |
| HFc  | of HF: quiets that give check                                       | 10,363    | 12,941     | 173,396    |
| HP   | legal promotions without capture never handed out at WL, WF nodes   | 0         | 0          | 0          |
| HC   | legal captures never handed out at WL, WF nodes                     | 0         | 0          | 0          |

How we counted the H rows: at the end of a loop that the picker ended (not a cutoff, not a return), for every
legal move of the node that is not the excluded move of a singular search: a quiet (no capture, no promotion)
that was never handed out counts for HL or HF. "First" for WL and WF: the rule that turned skip_quiets from false
to true at this node; when the late-move rule sets it on a move and futility then prunes that same move, it is
WL. Identities your counts must meet as well: B = T + QP + NR; SR = QP - Q - F; NR = NRc + NRq + NRp;
N = Nc + Nq.

K3 (by reading): T is 0 on every set, for the reason given above. Confirm it on your chain with file:line, or
show the line where your chain differs.

K4 (yours, inside ours): FE, F and Fc of column R are your job 33 and 34 numbers.

K5, the samplers of Step 3 on R (a counter per search for each kind, reset at the search's start; a record when
the counter reaches a multiple of k). They must write exactly:
  Q records, k = 15: 3,355.   S records, k = 200: 3,225.   N records, k = 125: 3,190.
  W records, k = 100 over the WL and WF nodes together, in the order their loops end: 2,836.

K6, a control with a known direction, on R with LmpBase 20 in place of 8 (everything else unchanged): node sum
4,003,589; L 183,745; WL 182,358; HL 3,446,946; F 36,145; S 1,104,771. (The depth sum of the 1,200 searches
falls from 9,746 to 9,075: fewer hidden moves, shallower searches for the same soft limit.)

K7, the instrument of the W oracle: go depth 8 with a move list (ucinewgame + isready before every search). A
cell is: bestmove, nodes of the last info line, score. Position 1 = the start position;
2 = `rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 1` (the side to move is in check);
3 = `1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1`;
4 = `8/3b4/8/1p1pk2p/7P/P1B1KP1P/1Pr1N3/8 b - - 0 1`.

| position | go depth 8          | go depth 8 searchmoves <every legal move> | go depth 8 searchmoves <two moves> |
|----------|---------------------|-------------------------------------------|------------------------------------|
| 1        | d2d4 6,170 cp 22    | d2d4 3,762 cp 17                          | a2a3 1,509 cp 7     (a2a3 a2a4)    |
| 2        | f1e2 2,474 cp 97    | f1e2 2,544 cp 97                          | c3e2 3,007 cp 54    (c3e2 c3e4)    |
| 3        | g7g6 3,891 cp -306  | g7g6 2,270 cp -298                        | b8b4 1,394 cp -307  (b8a8 b8b4)    |
| 4        | e5d6 1,911 cp 0     | e5d6 2,189 cp 0                           | e5d6 1,547 cp 0     (e5d6 e5e6)    |

The reading behind it (ours, r15d): a root restricted by searchmoves is never stored in the table (2518), so it
has no TT move at any iteration, and the reduction at 2184 (no TT move at a PV node, depth >= IirDepth, which is 2
under PC20, not in check) takes one ply off EVERY iteration: `go depth D searchmoves ...` searches the root at
depth D - 1. Position 2 is in check, where 2184 does not apply: at go depth 7 its plain search and its search
with every legal move are the same 1,505 nodes. So a full move list is NOT the plain search (positions 1 and 3:
about half the nodes), the score is the side to move's (position 3), and the W depths of Step 4 are one higher
than they would be without this.

## Job 38. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop and write.
Base: your job 34 chain and settings (PC20 with pc20_all1024.opt, Threads 1, Hash 16, the built-in evaluation).
The steps stand in the order of their worth: a stop at minute 40 after Step 2 is still a full result.

### Step 0 (a fresh process for each line)
The eight numbers of file 30 on the plain build. Failing numbers: STOP THE JOB, report the raw output.
Then the twelve cells of K7 on the plain build. A cell that differs does not stop the job: the W records are
then judged the one-by-one way of C-W (at most the first 6 hidden quiets of a record), and the report shows your
twelve cells beside ours.

### Step 1: reading (no runs; committed before Step 2)
On your chain, with file:line: the six sites of K2; which picker stages read skip_quiets and which do not (ours:
killers, counter move, quiet generation and the QuietMoves stage read it, 737 to 764; the evasion stages do not);
that a quiet CHECK is hidden like any other quiet once skip_quiets is set (ours: yes, 755 to 764; the rows HLc
and HFc count them); where promotions without capture are generated (HP = 0 says: with the captures); K3; and
for K7: where the root skips a move that is not in the list (ours 2224), that a restricted root is not stored
(ours 2518), and the line that then takes a ply off (ours 2184).

### Step 2: the counting copy (text patch job38/prune_classes.patch.txt)
The counters of K2, printed per search. A counter changes no value the search reads: the rows (depth, nodes,
bestmove) must equal your plain rows on R, O and G, and K1 must be met. Then K2: every cell of the three columns,
from a committed script that prints how many lines it read. A cell that differs is NOT a stop by itself: write
the cell, your number, ours, and the definition you think differs (the H rows and "first" are the likely
places); go on when B, QP, Q, F, S, N and L agree on R, stop Steps 3 to 5 when one of those seven differs.
K6 on R. Then one count of your own that we do not have: of the WL and WF nodes of R, how many have NO hidden
quiet at all (the rule was set at the node's last quiet).

### Step 3: the logging (text patch job38/prune_log.patch.txt on top of Step 2's copy; R only)
One line per record; a log line changes no value the search reads (the rows must still equal K1's).
- Q lines (k = 15): the node's FEN, the move, depth, lmr_depth, alpha, static eval, improving or not, PV node or
  not, and the slack = alpha - (static eval + FutilityBase + the improving term + FutilityMultiplier * lmr_depth).
- S lines (k = 200): FEN, move, depth, lmr_depth, alpha, in check or not, PV node or not.
- N lines (k = 125): FEN, move, depth, alpha, capture or quiet check, in check or not, PV node or not.
- W lines (k = 100): FEN, depth, the node's alpha and best score AT THE END of the loop, cause L or F, PV node or
  not, the number of hidden quiets, and the hidden quiets themselves in UCI form.
K5: the four record counts, exactly. Your F and P lines of job 34 are not made again: the table of Step 5 takes
job 34's files and names them.

### Step 4: the oracle (your job 34 script for Q, S and N; the PLAIN build, PC20, Threads 1, Hash 16)
- Q, S, N records, as in job 34: ucinewgame, isready, position fen <FEN> moves <move>, go depth D; the value of
  the move is minus the score; BEATS = value > the record's alpha. D1 = max(1, depth - 1), D2 = depth + 2.
- W records with at least one hidden quiet: ONE search per record and depth at the node itself: ucinewgame,
  isready, position fen <FEN>, go depth D searchmoves <the hidden quiets>. The value is the score as printed
  (the node's own side), NOT negated. BEATS = value > the record's end alpha. D1 = depth + 1, D2 = depth + 4:
  the restricted root loses one ply (K7), so the hidden moves' subtrees get depth - 1 and depth + 2, the depths
  a Q record's move gets. A W record without a hidden quiet gets no search and no BEATS; it stays in the table
  in a row of its own.
- If at minute 30 the oracle cannot finish, take every 2nd record of each kind in the log's order and say so; do
  not drop a kind, a depth or a control.

### The controls (before the prediction; each must be able to fail)
- C-SIGN and C-ALPHA of job 34, run again on 200 Q records (alpha replaced by -29000: BEATS on every one; by
  +29000: on none) and on job 34's P records for the sign (the two ratios as in file 34).
- C-W, the sign and the meaning of the W oracle. On the first 200 W records that have 1 to 6 hidden quiets, at D1:
  also search every hidden quiet by itself the job 34 way (position fen <FEN> moves <quiet>, go depth
  max(1, depth - 1), value = minus the score); BEST = the highest of those values; the record's answer that way
  is "BEST > end alpha".
  (a) THE SIGN. Take the records among the 200 whose searchmoves score is at least 150 or at most -150 (fewer
  than 20 of them: go on through the next W records until there are 20). On at least 9 of every 10 the score and
  BEST must have the same sign; a score read from the wrong side gives at most 1 of 10. Fewer than 9 of 10: STOP
  Steps 4 and 5 for the W records (the other kinds go on) and report the table.
  (b) THE MEANING. The two answers must agree on at least 170 of the 200. Fewer: the W records are judged the
  one-by-one way, at most the first 6 hidden quiets of a record, and the report says so and gives the count.

### Prediction (its own commit "kimi5 job 38 prediction": ONE file, after the controls and before the oracle runs
### on the Q, S, N and W records; never edited; no time and no commit id in it)
At D2: BEATS per 1,000 for Q, for S, for N captures, for N quiet checks; of 1,000 W records with a hidden quiet,
how many BEAT, for cause L and for cause F. A range each. And one line: which class will be the dearest by the
last column of Step 5.

### Step 5: the price list (D1 and D2 side by side; a committed script that prints how many records it read)
Rows: F (job 34's records); P with RAISED 1, 0, -1 (job 34's); Q; S; N captures; N quiet checks; W cause L;
W cause F; W without a hidden quiet. Then the splits, each as rows of the same table: Q, S, N and W by PV node
or not; S and N by in check or not; Q and S by lmr_depth 0 to 1, 2 to 3, 4 and more; W by depth 1 to 2, 3 to 4,
5 and more, and by the number of hidden quiets 1 to 5, 6 to 20, more than 20.
Columns: the class total on R (K2's cell: Q, S, Nc, Nq, WL, WF); records; BEATS; BEATS per 1,000 with a 95 %
interval (Wilson); and THE PRICE = class total / 1,200 * the BEATS share: the estimated number of pruned moves
(for W: of nodes) per search that the oracle says would have beaten alpha.
The readings (declared here; D2 decides, D1 is printed beside it):
- For Q, S, N captures and N quiet checks: THE RULE SELECTS when its BEATS per 1,000 is at most half of the P
  records' (all three rows together); otherwise THE RULE DOES NOT SELECT.
- THE DEAREST CLASS = the row with the highest price among F, Q, S, N captures, N quiet checks, W cause L,
  W cause F. Give the order of all seven.
- PV IS DEARER for a class when its BEATS share at PV nodes is at least 1.5 times its share at the other nodes
  and the two intervals do not overlap; PV IS NOT DEARER when it is at most 1.2 times; UNCLEAR otherwise.

### What a stop stops
Step 0 failing stops the JOB. K1 failing on a set stops that set. One of the seven named cells of K2 failing on
R stops Steps 3 to 5. K5 failing for a kind stops the oracle for that kind (report your count and the first 20
records). C-SIGN or C-ALPHA failing stops the JOB; C-W as written above. A refusal line (`illegal move`,
`invalid FEN`, `unknown option`, `invalid value`, `ERROR`) stops that run ("refused" and the line). Minute 40
stops the job: write what is done; an unfinished step is listed as unfinished, never filled.

### What this check cannot see (write it into the report as it is)
The PC's net (your runs use the built-in evaluation) and its engine build; go nodes 20000 and deeper; more than
one thread; the oracle is a second search from an empty table, not the truth, and for W it is a root search with
a move list, which the engine may treat differently from an inner node (C-W says how far the two ways agree, no
more); a move that beats alpha at the oracle's depth is not a move that changes the game; and whether any
threshold plays better at another value: that is a match on the PC.

### The report's first lines
(1) Step 0 with the K7 cells. (2) Step 1 with file:line. (3) K1; K2 as "cells equal: n of 105" and every cell
that differs; K3; K5; K6; your count of WL and WF nodes without a hidden quiet. (4) C-SIGN, C-ALPHA, C-W with
their numbers. (5) The prediction graded cell by cell (inside your range or not; nothing else). (6) The Step 5
table and the readings.
Then the usual form: "times: see stamps.txt", the model name your runtime gives, `git status --short` and
`ls -R` of the job folder as the last command before the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. Do not commit binaries. Times from
`date -u` pasted into `stamps.txt` after every part, never typed. A file that is committed is not edited again:
a corrected table goes into a NEW file, the first one stays. A rerun goes to a new folder; the first run's raw
files stay.
