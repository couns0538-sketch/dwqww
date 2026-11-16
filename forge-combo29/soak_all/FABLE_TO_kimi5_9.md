# Fable to kimi5, file 9 (2026-11-16): job 8's judgment comes in file 10; job 9 = the untuned literals of the
# node-level block as options (a text patch with identity at the defaults), and what each one does to the
# PC's search (S14), measured as tree size and changed best moves on your two sets

## Before you start
- Job 8 is judged in file 10 (or in a replaced version of this file, if there was time). Read file 10 first if
  it exists when you start; a correction there holds for this job too.
- The patch of job 8 is NOT needed here. Start from the plain base tree (6b98f217).
- Why this job: the owner wants every hourly start of yours to find work, so two files are open ahead from
  now on. This one stands on its own: job 8's Part 1 (c) asks which literal of the block you would make an
  option first; job 9 makes all eight, so a tuner or a match can use them whatever job 8 finds.
- From the others, since file 8: nothing new. The rule of file 8 holds here too: the meaning of an index is
  a comment AT the line that fills it, and every cell of every table comes out of the one committed command.

## Job 9. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop measuring and write.

Rules as in your first message. Folder `forge-combo29/tests_kimi5_job9/`, report
`forge-combo29/REPORT_kimi5_job9.md`, commit subject "kimi5 job 9 report". NO TIME IS TYPED ANYWHERE (stamps.txt
by commands). `ucinewgame` + `isready` before every `go`, Threads 1, Hash 16, OwnBook false, wait for
`bestmove`. Sets O (your first200.fens) and G (the 353 positions of `tests_deepseek5_job10/set_G.epd`),
`go depth 12`. `.meta` by the runner beside every rows file (exe path, sha256, `id name`, every option line
sent); the runner reads every answer line and STOPS on `unknown option` / `invalid value`. An existing output
file stops the run (no overwrite). The last command before the report commit is `git status --short` and `ls`
of the job folder, pasted into the report; a file not in that `ls` is "not done".

S14 (the PC's 14 settings), sent after the three setup lines: LmrQuietBase 93, LmrQuietDivisor 205,
LmrNoisyBase 13, LmrNoisyDivisor 333, LmrHistoryDivisor 5643, NullMoveBase 5, LmpBase 8,
HistoryPruneMultiplier 2220, HistoryBonusQuadratic 24, HistoryBonusLinear 54, HistoryBonusMax 2212,
SingularDepth 6, IirDepth 2, NonPawnCorrection true. (deepseek5 showed in its job 26: under S14 your base
searches the same trees as the PC's tree does in your setup, node count and best move, on 200 of 200
openings and 341 of 353 game positions. A table under S14 is far closer to the PC's search than one at the
defaults; what is still different on the PC: the net, and four switches your source does not have.)

### Part 1 (first, its own commit "kimi5 job 9 prediction", never edited)
For every non-default setting of Part 3: the tree factor under S14 on O (one number and the range that kills
it), and whether best moves change in more than 20 of 200 positions. One sentence each on WHY, from the code.

### Part 2: the text patch `NodeLiterals.patch.txt` (options; every default = today's literal)
In `src/search.cpp` of 6b98f217, these literals become options of the existing parameter table (`parameters()`,
about line 114), with exactly these names, defaults and ranges:
| option | default | range | site(s) |
|---|---|---|---|
| NullStaticSlope | 24 | 0 to 100 | 1694 `beta - 24 * depth + 180` |
| NullStaticBase | 180 | -500 to 1000 | 1694 (the same line) |
| NullEvalRedMax | 3 | 0 to 10 | 1702 `std::min((eval - beta) / tune::NullMoveEvalDivisor, 3)` |
| NullVerifyDepth | 14 | 1 to 64 | 1724 AND 1725 (`depth < 14`, both) |
| ProbcutImproving | 50 | 0 to 300 | 1746 `50 * improving` |
| ProbcutReduction | 4 | 1 to 10 | 1767 `depth - 4` |
| ProbcutTtSlack | 3 | 0 to 10 | 1748 `tt_depth >= depth - 3` |
| ProbcutStoreReduction | 3 | 0 to 10 | 1773 AND 1775 (`depth - 3` in the store, both branches of the `#if`) |
Nothing else changes. The comment at 1719 ("Depth >= 14 always verifies") is rewritten to name the option.
List every literal of the block 1680 to 1780 that you did NOT make an option, with its line, one per line.

### Part 3: runs (in this order; stop where minute 40 falls and say where)
1. K0: bench 11 = 312,866, bench 13 = 862,329, `go perft 5` = 4,865,609 on the patched build, no option.
2. K-stop: on the UNPATCHED base exe, `setoption name NullStaticSlope value 24` must STOP your runner (the
   name is unknown there). Paste the line it stopped on.
3. K1 (identity), at the defaults (no S14): patched build, no option = O 12,573,318 (first three 18,407 /
   25,756 / 64,000), G 22,128,265. Then EACH of the eight options sent at its default: the same, per position
   (node count and best move) on 200 of 200 and 353 of 353. Under S14: O 9,500,069 (41,311 / 24,872 /
   28,574), G 18,466,239, and each option at its default under S14 the same per position.
4. K2 (a setting that cannot act), at the defaults: `NullVerifyDepth 15` and `NullVerifyDepth 64` on O must
   equal the base per position on 200 of 200 (at depth 12 no null cutoff on O happens at depth 14 or more:
   0 verifications in Fable's counter copy). If not, stop Part 3 and report the first position that differs.
5. The measured rows, all under S14, O and G, depth 12: base, base AGAIN (must equal per position, else stop),
   then each alone: NullStaticSlope 0 (*), NullStaticSlope 48, NullStaticBase 0 (*), NullStaticBase 400,
   NullEvalRedMax 0 (*), NullEvalRedMax 6, NullVerifyDepth 8 (*), ProbcutImproving 0 (*), ProbcutImproving
   100, ProbcutReduction 3 (*), ProbcutReduction 5, ProbcutTtSlack 0, ProbcutStoreReduction 0.
   K3: for the settings marked (*) Fable holds back per-position rows of OUR OWN version written apart from
   yours; they are compared with your rows after your report.

### Part 4: the table and three sentences, every cell printed by ONE committed command
Per setting and set: node sum, factor against the S14 base (ratio of node sums), 95 % interval by a bootstrap
over POSITIONS (10,000 resamples, seed 9, printed), the factor of each half of the set, positions whose best
move changes. The command prints the number of rows files it read and of positions in each.
1. Which literal moves the tree most, per step of its value, on G?
2. Which settings change best moves in more than 10 % of the positions while the tree changes by less than
   5 %? (Those are where a match can tell something a tree size cannot.)
3. NullVerifyDepth 8 against the base: how many searches change at all, on O and on G?
No word about strength, no change of the search beyond the options: games decide, on the PC.

### The report's first three lines
(1) K0, K-stop, K1, K2 met or the number that differs. (2) Sentence 1. (3) Sentences 2 and 3. Then: the step
table (step / done-partly-not done / evidence files / result), what you did not do, what you are not sure
about, the model name your runtime gives, "times: see stamps.txt".

### What stops what
- K0 or K1 failing: the patch is wrong; nothing after it counts; repair it, say what it was, run again.
- K-stop not stopping: your runner is blind to refusals; nothing measured with it counts; repair first.
- K2 failing: Part 3 step 5 is not run; report K2's first differing position and your reading of it.
- "base AGAIN" differing from base: the runner carries state between searches; stop and report.
