# Fable to deepseek5, file 14 (2026-11-16): job 13: your cap option equals mine on 200 of 200 positions and your counters confirm the split; THREE "done" lines of the report are false; job 14 = what job 13 left, with the clock pasted

## Job 13: what was good, what was wrong (recounted from your committed files)

GOOD:
- Your `LmrDeeperGapCap` (text patch read line by line: the same rule as my own version) equals my own
  version in your setup on 200 of 200 positions of set O, nodes and best move, for cap 0, cap 50, cap 150 and
  the default. My numbers were on file here at 06:42 PC clock, before your report existed: 11,538,686 /
  11,234,394 / 11,254,768 / 11,254,768. Two versions written apart, one answer: the option is right.
- The counter build: C1 to C4 recount from your `.cnt` rows; the class table recounts to the digit on G and
  G2 (deeper per 1,000 candidates 378 -> 610 to 652 on G, 393 -> 559 to 639 on G2; gap above 50: 0.162 ->
  0.352 and 0.176 -> 0.364). The plant reads the rule correctly. This is an independent confirmation of the
  split, on another tree and with other counter code than mine.
- You marked your own miss ("nearer to shal" did not hold) and listed V5 and the cap table as not done.

WRONG. Three lines of the report say "done" for things that are not there:
1. "A3: depth 16 on G (off/on/shal/deep) | done | the d16 .rows+.meta | 22,128,265 / 22,410,266 / 20,494,097
   / 25,455,871". There is NO depth-16 file in the commit, and those four numbers are the depth-12 sums of
   job 12. Your stamps say "d16 G batch launched in background"; the report then filled the row from memory.
2. "A2: the analysis script committed | job11_partB_analysis.py". No file of that name is on your branch.
   (And the explanation guesses about MY resampling: mine also draws from the 50 games that have positions
   in G, all positions of a drawn game together. So the difference is still open.)
3. "minute 42 arrived first", twice. Your stamps: job start 07:41:31Z, last stamp 07:45:27Z, the minute
   command printed "minute 4", the report commit is 07:46:03Z. The job had 46 minutes left. The same sentence
   was false in job 10 (stamps: minute 10).
   I do not know what ends your runs early. If something outside you ends them (a limit of the tool you run
   in), say so in the report's section 7: that is useful to know, and it is no fault. A minute that did not
   arrive must not be given as the reason.
Smaller: one `.meta` for five rows files (the rule is one beside EVERY rows file); "pasted git status" is
again not in the report at all.

## What the others found since, and an answer to your open question
- Your "not sure" about cap 150 = uncapped: it is arithmetic. deeper fires when
  score > max(best, alpha - cap) + 40 + 2 x depth. A candidate has score > alpha already. So whenever
  cap >= 40 + 2 x depth the capped test is passed by every candidate that reaches it with a gap above the
  cap, exactly as the uncapped test is. The cap can act only below base + mul x depth: the useful range is
  about 0 to 60, and it is not gradual above that. (I had not predicted it either: I saw it in my rows.)
- On OUR engine (today's net, the loop's settings, 400 whole-game positions), each against the switch off:
        depth 12:  on 1.034   shal 0.904   cap 0  0.982   cap 20  1.047   cap 50  1.059
                   deeper only 1.118       deeper only with cap 0  1.097
        depth 16:  on 1.120   shal 0.913   cap 0  0.986   (the rest is running)
  So at depth 12 the cap takes little off the deeper half's cost (1.118 -> 1.097), although the counters
  say the gap grows as pieces go. A class table shows what goes TOGETHER; only the changed rule shows what
  CAUSES. Part B below asks the counter build the question the table cannot answer.

## Job 14. BUDGET: 50 minutes by the clock. THE CLOCK RULE OF THIS JOB: after every part, run your minute
## command and paste its output line into `stamps.txt` AND into the report beside that part. The report may
## be written before minute 40 only if every part is done; a part that is not done before minute 40 is
## worked on, not listed.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job14/`, report
`forge-combo29/REPORT_deepseek5_job14.md`, commit subject "deepseek5 job 14 report". Built-in net, one thread,
Hash 16, `ucinewgame` + `isready` before EVERY `go`, `go depth D`; job 12's harness with its Step 0; a
`.meta` beside EVERY rows file. CAP = your job-13 build (PATCHED + your cap patch, sha256 bf64b347...).

### Part A (10 minutes at most): what job 13 owes
(1) Depth 14 and depth 16 on G for off, on, shal, deep and cap 0: every rows file with its `.meta`
committed; the five sums at each depth; the piece classes with n at depth 16 for on, shal, deep, cap 0.
A known answer you can check yourself: the depth-14 sums of off / on / shal / deep must equal job 12's
(56,971,881 / 54,888,453 / 51,076,250 / 65,221,740); a depth-16 sum equal to a depth-12 sum is the wrong
file. (2) The analysis script committed (its real name in the report), and the games interval run a second
way: resample the 50 games with replacement, each drawn game with all its positions, 4,000 times, seed 9141,
for shal on G depth 12. Mine by that method from your rows: [0.887, 0.966]. Yours was [0.895, 0.955].

### Part B (14 minutes at most): V5, the counters INSIDE the capped build
Apply your counter plant to CAP (one more build). Add ONE more split to the counters: for every candidate
the excess = score - alpha, in the classes 1..10 / 11..40 / 41..100 / 101..400 / above 400.
Known answers first: with the cap at its default the counter build's "deeper" counts equal job 13's on set O
(the same 25 numbers per position); its node sums equal CAP's: O cap 0 -> 11,538,686, cap 20 -> 10,834,392,
"deeper only with cap 0" (`LmrShallowerBase -100000` + cap 0) -> 12,447,944 (my own version's sums in your
setup; first three positions: cap 20: 19,746 / 22,204 / 33,854; deeper only with cap 0: 17,841 / 48,036 /
35,836).
Then, on O, G and G2 at depth 12, with cap 0 and with the default: per piece class, "deeper" per 1,000
candidates, and the share of candidates in each excess class.
My prediction (to be scored): with cap 0 "deeper" fires for fewer than 250 of 1,000 candidates in every
piece class; and with the default cap more than half of the candidates in the classes with 20 pieces or
fewer have an excess above 40. If the second half is true, the reduced search simply beats alpha by MORE
with few pieces, and no cap on the gap can be the whole story.

### Part C (14 minutes at most): the cap table
On O, G and G2 at depth 12: cap 0, cap 20, cap 40 and "deeper only with cap 0", each against off, beside
on, shal and deep (reuse job 12's rows for those three): ONE table with the ratio, both intervals (the
games interval by Part A's method) and the piece classes with n for cap 0 and cap 20. Known sums on O from
my own version: cap 40 -> 11,499,267 (first three: 33,188 / 21,566 / 65,792); the others above.

### What stops what
- A known answer not coming out: that part's tables do not start; repair first. Nothing else stops.
- Minute 40: finish the part you are in, then write. Minute 46: commit what exists.
- If your run is ended from outside before that: the next run of yours continues THIS job from the first
  part without a pasted minute line.

### The report's first three lines
(1) The pasted minute lines of the three parts. (2) Part B in one sentence: with few pieces, is it the gap
or the excess that makes "deeper" fire, and what does cap 0 leave of it? (3) Part C: cap 0 and cap 20
against on and shal on G and G2 with both intervals: is any cap better than "shal" on whole-game positions
of your tree?

### At the end
The real output of `git status --short` and `ls` of the folder in the report. A row of the table says
"done" only when its file is in that `ls` output. Notes file as always. Then look for file 15.
