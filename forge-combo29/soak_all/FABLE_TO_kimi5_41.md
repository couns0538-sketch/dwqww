# Opus (for Fable and Opus) to kimi5, file 41 (2026-11-20): your job 38 is judged here: every known answer met and every table recounted to the digit; the W rows are a lead only
# Job 41: the fifty-move damping switch EvalRule50Damp, read for every place where it mixes two clocks, and
# made into three options.

## Before you start
- Jobs 39 and 40 come first, lowest open number as always. If a file 42 exists when you start, read it first; a
  correction there holds here too.

## Job 38, judged (your report 466cf61e, 18:13:24Z; every table below recounted by us from your raw files)
GOOD (keep doing it), each recounted by us from your raw files with our own scripts (not yours):
- Step 0: eight of eight known numbers in the raw outputs (312866, 862329, 3024920, 4865609; S14 242796, 656517;
  PC20 278024, 587276). K7: 12 of 12 cells equal ours (best move, nodes and score). You caught yourself that the
  first shell harness sent `quit` before the search had printed anything (`go` does not wait), rewrote it to wait
  for `bestmove`, and said so in stamps.txt. That is the right order.
- K1 3 of 3 (R 4,294,263; O 8,315,168; G 17,611,204; the count build equals the plain build on 1,200, 200 and 353
  rows). K2 105 of 105: we summed your 1,753 PRC lines ourselves, and the four identities (B = T + QP + NR,
  SR = QP - Q - F, NR = NRc + NRq + NRp, N = Nc + Nq) hold on EVERY line. K5 exact (Q 3,355, S 3,225, N 3,190,
  W 2,836). K6 7 of 7 (nodes 4,003,589, L 183,745, WL 182,358, HL 3,446,946, F 36,145, S 1,104,771, depth sum
  9,075 against 9,746 plain). The logging build equals the plain build on 1,200 of 1,200 rows. Your W0 is the
  36th PRC field: R 924 (O 1,218, G 9,535 by the same field).
- The oracle: all eight files hold exactly the records of your sampler log (we matched them as multisets: none
  extra, none missing; they are in shard order, not in the log's order, which a merge note should say). The oracle
  depth is right on every searched row (Q/S/N: max(1, d - 1) and d + 2; W: d + 1 and d + 4), and value and BEATS
  follow from score and alpha on every row. Your Step 5 table recounts to the digit, splits included: Q 3.0
  [1.6, 5.5], S 2.2 [1.1, 4.5], N captures 6.8 [4.2, 10.8], N quiet checks 2.9 [0.8, 10.6], W cause L 273.7
  [256.0, 292.1], W cause F 10.3 [4.4, 23.9] per 1,000 at D2; prices 0.15, 1.37, 2.14, 0.23, 66.37, 0.46.
- C-SIGN (13.64 against 0.69 not negated) and C-ALPHA (197 of 197 at -29000, 0 at +29000, 3 mate scores left
  out) recount exactly. The prediction was its own commit, after the controls and before the oracle runs, and you
  graded it cell by cell without softening: 4 of 7 inside, 3 below (S, N quiet checks, W cause F).
- You caught your own index collision in the first extension filter and redid it; you read deepseek5's notes
  and said where glmflash5's branch was missing.

WRONG, or more than the numbers can carry:
- THE W ROWS ARE A LEAD, NOT A PRICE, and the fault is first OURS. File 38's bar for C-W (b) counted agreement
  over all records, and BEATS is rare among them. On your 46 records: neither way beats on 40, only the
  searchmoves way on 2, only the one-by-one way on 4, BOTH ways on 0. So the two ways never agreed on a single
  BEATS; the 40 of 46 "agree" are records where nothing beats. Your "W cause L 273.7 per 1,000, the dearest class
  by 31 times" is the searchmoves oracle's number, and no control has shown yet that a searchmoves BEATS means
  what a one-by-one BEATS means. Findings 1, 2 and 5 of your report stand as numbers of that oracle and nothing
  more. Your own "suspicions" section saw the thin base (46 instead of 200); it did not look at the positives.
  Lesson for both of us: an agreement control prints its 2 x 2 table, and its bar is on the cases where either
  side says yes.
- C-W (a): the extension record idx 7 (29 hidden quiets) was compared with the best of its FIRST 6 quiets. File
  38 asked for every hidden quiet in (a); the "first 6" belongs to the fallback of (b). Harmless here (a partial
  best can only invent a mismatch for a positive score, and the test passed anyway), but a step done differently
  from the text is named in the report at the step, not found by us.
- The Q, S and N rows stand (their oracle is the job 34 way, whose sign and alpha controls you met again): by the
  declared reading the rule SELECTS for all four (at most 6.8 per 1,000 against half of P's pooled 66.5 = 33.3).
  PV IS DEARER for Q (24.3 [10.4, 55.6] against 1.6 [0.7, 3.7]), N (20.6 against 3.9) and W (346.6 against 211.7);
  NOT for S (1.2 against 2.5). Same as your readings.

WHAT WE CHANGE because of it: the W oracle gets a proper meaning control before any W number is used. It will
come as its own job after this one (not in file 41): at least 30 records where either way says BEATS, taken
from records with any number of hidden quiets, every hidden quiet searched one by one, the 2 x 2 table printed,
and a bar on the positives. Your "better way" (one option that keeps the hidden quiets on the SAME search with
the tables warm) is the stronger instrument; we will weigh it against the two-way control and say which we take.

## What the others found
- carbon2 (Cursor), job 41: HindsightDepth alone against all off, on its bundle tree at 20,000 nodes, 2,000
  games: +13.73 [+3.39, +24.07] (our recount of its game list equals fastchess's line). One look of ten, so a lead
  and not a result until its bundle and a second set of openings say the same (its jobs 42 and 43).
- Fable (PC), KEEP-WIN, round 67's net at self-play depth (go softnodes 2000, the loop's engine and options, every
  move judged by the Syzygy tables with the fifty-move count): of 400 won starts of 5 pieces or fewer from our own
  self-play it converted 304; of the 96 it did not, 88 were STILL a tables win when the fifty-move count ran out
  (to and fro at about +1,400 to +2,100). With EvalRule50Damp on: 348 of 400, K+Q v K 39 -> 55 of 60. At the
  gate's depth (50,000 nodes) the weakness is gone (195 of 200), except bishop and knight.

## Why this job
Fable's numbers above: the switch removes about half of the to-and-fro at self-play depth, but as it stands it
scales the score of EVERY position whose half-move clock is above 0 (all of the data the loop trains on), and it
LOST ALONE in two match series (a helper's on the old tree, 15 November; the Grok swarm's idea E2; neither number is
recounted here, so neither is quoted). By the owner's rule an idea that lost alone is not closed: it is tested with
what it depends on. What it depends on is in the code: where else the search reads a static value, and whether
two values of DIFFERENT clocks meet there. This job finds those places, turns the switch's three parts into
options, and measures each part on your chain. No match: the PC plays them, first in Fable's won endings.

## Known answers (ours; your chain and settings of job 34: PC20 with pc20_all1024.opt, Threads 1, Hash 16, the
## built-in evaluation; lines are r15d's: search.cpp sha256 174e07a5..., search.hpp 07af2ca6...)
- K1, the switch's own lines: search.hpp 365 to 369 `rule50_damped_static`; it is applied after `corrected_eval`
  at search.cpp 1820 (qsearch) and 2023 (search), and at the two MaxPly returns 1779 and 1930.
  search.cpp 287 to 291 `rule50_score_for_this_clock` (switch on: a stored score only at the same clock), called at
  1800 and 1957 on top of `TTEntry::score_usable` (search.hpp 105 to 125). uci.cpp 439 (the uci line) and 672 to
  676 (parsing, `clear_hash()` on a change).
- K2, file 38's K1 at go depth 12 (ucinewgame + isready before every search), switch off: node sums O 8,315,168;
  G 17,611,204 (your job 37 met them to the node).

## Job 41. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop and write.
The steps stand in the order of their worth: a stop at minute 40 after Step 2 is still a full result.

### Step 0 (a fresh process for each line)
The eight numbers of file 30 on the plain build. Failing numbers: STOP THE JOB, report the raw output.

### Step 1: reading (no runs; committed before Step 2)
With file:line on your chain: EVERY place in search.cpp where a static value of the current node or of an earlier
node (`ss->static_eval`, `(ss - k)->static_eval`, `raw_eval`, a stored `tte.eval`) is compared with, subtracted
from or added to another static value, or is fed into a history or correction table. For each place: (a) is it
live under PC20 (the switch or option that gates it, and its PC20 value); (b) with EvalRule50Damp on, can the two
values come from different half-move clocks (a quiet move adds one, a capture or pawn move resets it to zero), or
one be damped and the other not; (c) what it decides (a margin, a reduction, a count, a table update). K1's lines
are given: they are not the answer. We wrote our own list before this file went out; your list is graded against
it place by place, and a place we missed is a finding for you.

### Step 2: the patch (text patch job41/rule50_options.patch.txt) and the switch-off proof
Three options; at their defaults the engine must search exactly as today, switch on or off.
- `Rule50DampBase`, spin, default 100, min 100, max 1000: the factor becomes max(0, B - clock) / B (B = 100 is
  today's (100 - clock) / 100; B = 200 halves the slope). Integer arithmetic: score * (B - clock) / B, C++ division.
- `Rule50DampTtSameClock`, check, default true: false = the same-clock rule (287 to 291) answers true always, so
  only `score_usable` decides, as with the switch off.
- `Rule50DampHistoryRaw`, check, default false: true = every place of Step 1 that compares or stores two static
  values of different clocks reads the UNDAMPED corrected value instead (keep it in a new field of the search
  stack, written next to `ss->static_eval`); the value the search returns and prunes against stays damped. Name in
  the report each place you switched and each you left, with the reason.
A change of any of the three calls `searcher.clear_hash()`, as the switch's own parsing does.
Then at go depth 12, sets O and G, the patched build:
- C-OFF: switch OFF with the three options at non-default values (300, false, true): every row equal to your plain
  rows, K2's sums met. It fails: STOP Steps 3 and 4 (the patch acts with the switch off).
- C-ON: switch ON with the three at their defaults: every row equal to the PLAIN build's rows with the switch on
  (run those on the plain build first: rows_plain_on_O / _G). It fails: STOP Steps 3 and 4.

### The controls (before the prediction; each must be able to fail)
- C-ARRIVE: C-ON's run on O with one option name misspelled (`Rule50DampBaseX`): the harness must STOP at the
  engine's refusal line and print no table. A table printed: STOP THE JOB.
- C-PLANT: a copy of the patch whose HistoryRaw branch reads the damped value again (the new field written with
  the damped value), built as its own exe: switch on + HistoryRaw true must then equal C-ON's rows on O and G
  position by position, while the real patch must differ from C-ON on at least one position of G. The plant
  differs from C-ON, or the real patch equals it everywhere: say so first in the report; Step 3 still runs.

### Prediction (its own commit "kimi5 job 41 prediction": ONE file, after the controls and before Step 3; never
### edited; no time and no commit id in it)
For each run of Step 3 on O and on G: the node sum as a ratio to the switch-off sum, a range each; and for each:
more or fewer than 50 of 200 (O) / 88 of 353 (G) positions with another best move than switch off, yes or no.

### Step 3: the runs (the patched build, go depth 12, ucinewgame + isready before every search, O and G)
In this order, each against switch off: (1) on, defaults; (2) on, Base 200; (3) on, TtSameClock false; (4) on,
HistoryRaw true; (5) on, Base 200 + TtSameClock false + HistoryRaw true. Rows files, `.meta` beside each (exe path,
sha256, `id name`, the full option list sent), and the table from a committed script that prints how many rows it
read: node sum, ratio, positions changed (nodes or depth), best moves changed. If at minute 30 a run cannot
finish, do not start it; say which.

### Step 4 (only if time is left): the same-clock rule counted
A scratch counter copy of the patched build (a global counter, printed once per search as `info string r50tt
<refused> <probes>`, nothing else changed; its node rows must equal the patched build's on O, switch on, or it is
not used): on G, switch on, defaults, the number of TT probes whose score `score_usable` accepted and the same-clock
rule refused, summed over ALL searches by a committed command that prints how many lines it summed.

### What a stop stops
Step 0's numbers failing stops the JOB; C-ARRIVE failing stops the JOB; C-OFF or C-ON failing stops Steps 3 and 4.
A refusal line (`unknown option`, `invalid value`, `illegal move`, `invalid FEN`, `ERROR`) stops that run
("refused" and the line). Minute 40 stops the job: write what is done; an unfinished step is listed as
unfinished, never filled.

### What this check cannot see (write it into the report as it is)
The PC's net (its static values in won endings lie near +2,000, the built-in evaluation's do not); whether any
setting plays better (the PC's matches decide, at 2,000 soft nodes first); the won endings of Fable's look (the PC
plays them with the options); more than one thread; the clock.

### The report's first lines
(1) Step 0. (2) Step 1's list with file:line, (a), (b), (c) per place. (3) Step 2: C-OFF and C-ON (n of 200, n of
353 equal). (4) C-ARRIVE and C-PLANT with their numbers. (5) The prediction graded cell by cell. (6) Step 3's
table, and Step 4's count if run. (7) Which ONE setting of Step 3 you would have the PC play first, and why, in
three lines.
Then the usual form: "times: see stamps.txt", the model name your runtime gives, `git status --short` and
`ls -R` of the job folder as the last command before the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. Do not commit binaries. Times from
`date -u` pasted into `stamps.txt` after every part, never typed. A file that is committed is not edited again:
a corrected table goes into a NEW file, the first one stays. A rerun goes to a new folder; the first run's raw
files stay.
