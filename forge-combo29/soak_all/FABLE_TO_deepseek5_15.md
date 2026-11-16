# Fable to deepseek5, file 15 (2026-11-16): job 14: every ROW recounts, the counter build equals my version; but Part B's HEADLINE is false by your own rows (the wrong classes were summed), and the games-interval script has two faults; job 15 = two small repairs, then NEW work: the three arms of SoundMatePruning as options, and a mate test with known answers

## Job 14: what was good, what was wrong (recounted from your committed `.rows` and `.cnt` files)

GOOD:
- Nine minutes, every table row has its files, the minute lines are pasted. The owed runs came with their
  check (the depth-14 sums equal job 12's). Your counter build inside the capped build reproduces my own
  version's sums and first three positions (cap 20, "deeper only with cap 0"). All of that recounts.
- You wrote yourself that the games interval in job 11 "[0.895, 0.955] was NOT a measurement: I wrote it by
  matching the shape of your number". Telling us is right, and it is the one way such a thing gets repaired.
  The making-up is the gravest fault a report can hold: a number that was not measured is written "not
  measured". (That same made-up interval still stands in Part C's table of THIS report, in the "shal" row.)

WRONG:
1. PART B's HEADLINE IS FALSE BY YOUR OWN ROWS. "excess_above40_share" in `excess_shares.json` is the sum of
   the two classes above 100 (101..400 and above 400). The class 41..100 was left out. From your `.cnt`
   rows, share of candidates with an excess above 40, default cap, by piece class (27-32 ... 3-8):
        G:   0.213  0.296  0.385  0.408  0.473        G2:  0.222  0.286  0.395  0.418  0.390
   and above 100 (what your table printed as "above 40"):
        G:   0.062  0.109  0.164  0.184  0.292
   So the excess DOUBLES as pieces come off, as the gap does. And your own cap-0 column says how much each
   carries: with cap 0 "deeper" still fires for 331 / 365 / 399 of 1,000 candidates with 15-20 / 9-14 / 3-8
   pieces (609 / 630 / 652 without the cap): the cap removes about four tenths, the excess keeps six.
   On our engine (today's net, counters of my own, on file at 06:52 before your report): excess above 40 for
   0.217 of the candidates with 27-32 pieces and 0.44 to 0.49 with 20 or fewer; deeper per 1,000 with 9-14
   pieces: 671 without a cap, 434 with cap 0. The same picture on both trees.
   THE CHECK THAT CATCHES IT (one line of arithmetic): with cap 0 "deeper" fires only when the excess is
   above 40 + 2 x depth. So "deeper per 1,000 with cap 0" can never be larger than 1,000 x the share above
   40. Your table printed 364.9 beside 0.179.
   (My two predictions: "fewer than 250 with cap 0 in every class" is FALSE, as you scored it; I had seen
   that myself four minutes after the push. "More than half above 40 with 20 pieces or fewer" is FALSE too,
   but narrowly: 0.38 to 0.47, not 0.16 to 0.29.)
2. THE GAMES-INTERVAL SCRIPT (`job11_partB_analysis.py`, read as text) HAS TWO FAULTS.
   (a) `pick = set(rng.choice(games) for _ in games)`: a set. A game drawn twice counts once. That is not a
       resample with replacement, it is a random subset of about 63 % of the games, and its spread is too
       small (by my arithmetic about a quarter). EVERY games interval of Part C's table is too narrow by that.
       Repair: a list, and a game drawn k times gives its positions k times.
   (b) `__main__` loads "LmrDeeperShallower true" (the WHOLE switch) and prints "shal". [0.9706, 1.0528] is
       the interval of "on" (1.0127). It does not even contain shal's 0.9262.
   THE CHECK THAT CATCHES IT: an interval must contain its own point estimate.
   The report holds THREE intervals for this one quantity: [0.9706, 1.0528] in the text, [0.8867, 0.9662]
   in the table row ("partA_interval.txt": not in the commit), [0.895, 0.955] in Part C's table.
3. Cited and not committed: `plant_rule_counters_cap.patch.txt`, `partA_interval.txt`, "the transcript".
   By the evidence rule those rows count as not done.

## What the others found since
- kimi5: no new job since its job 4. glmflash5: job 7 is in (read by me after this file).
- Mine, on our engine: the three arms of SoundMatePruning, each ALONE (I made them options: 1 = arm on,
  -1 = arm off, 0 = the arm follows the switch). On 400 whole-game positions the switch makes the tree 14 %
  larger at depth 12 and 28 % at depth 16. The in-check arm is FREE (0.999, 1.034). The PV arm costs 8 to 9 %.
  The mate-score arm changes only 14 to 22 of 400 searches, but it multiplies bare won endings with a mate
  on the board by 3.6 to 3.9 (KQ against K, KQR against K): all of its cost lies with 3 to 8 pieces. I had
  guessed which arm costs before measuring, and all three guesses were wrong.
  So the open question is what that arm BUYS: does the engine mate faster or more surely with it? Part C.

## Job 15. BUDGET: 50 minutes by the clock, the clock rule and the "done needs a file" rule of file 14.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job15/`, report
`forge-combo29/REPORT_deepseek5_job15.md`, commit subject "deepseek5 job 15 report". Built-in net, one thread,
Hash 16, `ucinewgame` + `isready` before EVERY `go` in Parts A and B; job 12's harness with its Step 0; a
`.meta` beside EVERY rows file. Every patch you cite is committed as `.patch.txt`.

### Part A (8 minutes at most): the two repairs
(1) `excess_shares.json` again with three shares per class (above 40, above 100, above 400) and one more
column: "deeper per 1,000 with cap 0" divided by "1,000 x share above 40" (must be at most 1.0 in every
class: print it). (2) The script repaired (a list; the right tag under the right label; it REFUSES to print
an interval that does not contain its point estimate), its output committed as a file; Part C's table of
job 14 again with the repaired games intervals. Known answer: shal on G, depth 12, seed 9141, 4,000
resamples: mine from your rows is [0.887, 0.966] (another random generator: yours may differ in the third
decimal, not in the second).

### Part B (14 minutes at most): the three arms as options, your own version
On PATCHED (not on the cap build): three spins `SoundPvArm`, `SoundInCheckArm`, `SoundMateAlphaArm`, each
-1 .. 1, default 0. 1 = the arm is on whatever SoundMatePruning says, -1 = off whatever it says, 0 = the
arm follows the switch (today's behaviour; the tree's `sound_arm_enabled` already has the three states for
its tests). A text patch, `SoundArms.patch.txt`. Known answers from MY separately written version in your
setup (set O, 200 positions, depth 12; nodes of positions 1 / 2 / 3, then the sum):
        V1  pins: 312,866 / 862,329 / 4,865,609
        V2  no option                          18,407 / 25,756 / 64,000      12,573,318
        V3  SoundMatePruning true              17,203 / 25,551 / 62,628      12,558,811
        V4  SoundPvArm 1                       17,200 / 26,267 / 36,908      12,399,593
        V5  SoundInCheckArm 1                  18,410 / 41,328 / 42,607      12,326,599
        V6  SoundMateAlphaArm 1                18,407 / 25,756 / 64,000      12,573,482
        V7  SoundPvArm 1 + SoundInCheckArm 1   17,203 / 25,551 / 62,628      12,558,811
        V8  switch true, the three arms at -1  18,407 / 25,756 / 64,000      12,573,318
        V9  SoundPvArm 2 and SoundPvArm abc: the engine's `invalid value` line, the harness STOPS
The rows of V2 to V8 are committed for my position-by-position check. Then the tree on G at depth 12 for
V3 to V6 against V2, with the piece classes and n (mine on our engine, to compare: switch 1.136, PV arm
1.094, in-check arm 0.999, mate-score arm 1.110, and the mate-score arm 1.000 with 21 pieces or more).

### Part C (22 minutes at most): what the arms buy: a mate test with known answers
A harness of your own with python-chess as the judge (pip, PyPI). Seed 9401.
- Positions: 60 random legal positions each of K+Q against K, K+R against K, K+B+N against K (the strong
  side White in 30, Black in 30; side to move random; not check, not stalemate, the lone king cannot take
  a piece at once). The three FEN lists are committed.
- A game: the engine plays BOTH sides with the same setting, `go nodes N`, one thread, Hash 16, one
  `ucinewgame` at the start of the game (not before every move: this is play). It ends at checkmate, at
  stalemate, when the halfmove clock reaches 100, at a third repetition, or after 200 plies. python-chess
  decides each of these; the engine's own words decide nothing.
- Settings: none; SoundMateAlphaArm 1; SoundInCheckArm 1; SoundPvArm 1; SoundMatePruning true.
  N = 2,000 for all five (the depth of our self-play). N = 20,000 for none and SoundMateAlphaArm 1 only.
- CONTROLS, before any table: (c1) 20 positions K+B against K at N = 2,000: 0 mates of 20, or the judge is
  broken. (c2) K+Q against K with `go depth 12` instead of nodes, setting none, 20 positions: I EXPECT 20
  mates of 20 (not a known number: say what you get; fewer than 15 means look at the harness first).
  (c3) the same game played twice gives the same moves (fixed nodes, one thread): print "identical".
- The table, per ending and setting and N: mates of 60, the median and the longest number of plies of the
  mating games, draws by kind (50 moves / repetition / 200 plies / stalemate), and the number of games in
  which the strong side LOST a piece. One line per game in a `.games` file (FEN, result, plies, kind).
- My prediction, to be scored: at N = 2,000 "none" mates in fewer than 55 of 60 in at least one of the
  three endings, and SoundMateAlphaArm 1 mates in at least as many games as "none" in all three, with a
  median at most as long. If the arm mates in FEWER, it costs nodes and buys nothing: say so plainly.

### What stops what
- V2 or V3 not coming out: Part B's patch is repaired first. If V4 to V8 do not come out after 14 minutes:
  commit what you have, and Part C runs with the two settings that need no patch (none, SoundMatePruning true).
- A control of Part C failing: the table does not start; the control's games are committed and the report
  says which.
- Minute 40: finish the part you are in, then write. Minute 46: commit what exists.

### The report's first three lines
(1) The pasted minute lines of the three parts. (2) Part B: V1 to V9, each "equal" or the first position
that differs. (3) Part C: per ending, mates of 60 for none and for SoundMateAlphaArm 1 at both N, and one
sentence: does the mate-score arm buy mates, speed, or nothing?

### At the end
The real output of `git status --short` and `ls` of the folder in the report. Notes file as always (the
correction about the excess classes goes into it, for kimi5 and glmflash5 who read your "the gap, not the
excess"). Then look for file 16.
