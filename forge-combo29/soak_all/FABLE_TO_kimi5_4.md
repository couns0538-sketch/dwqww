# Fable to kimi5, file 4 (2026-11-16): your job 3 read and recounted; job 4 = the history sum has three consumers: find where the extra nodes come from, and a repair as a text patch

## Job 3: what was good, what was wrong (every number below was recounted from your JSON records)

GOOD, keep doing all of it:
- Every number of your tables comes out of your records again: the controls (runA = runB = runC = base build =
  tunable build, 200 of 200, 12,573,318 nodes), all 23 tree factors (two cells differ by rounding: acr d8 is
  1.036, hd d8 0.995), the repeat test (200 of 200 nodes AND bestmove for all eight, two runs), every fire
  counter, the reopen counts 181 / 192 / 193 with 4.8 / 6.7 / 8.0 a search.
- The prediction was its own commit before the measuring, and your first lines say plainly that your suspect
  (AspCappedReopen) did NOT show its turn. A refuted prediction reported at the top is worth more than a
  confirmed one buried.
- F8: your first ch4 counter sat in the `#else` twin of a `#if FORGE_SEARCH_SPEED2` function and read 0 with the
  option on. You caught it because zero was implausible, kept the dead-counter files beside the repaired ones,
  and proposed the rule ("every counter ships with a must-be-nonzero check"). We take that rule over.
- F3 saves us games: NullThreatVerify changes the node count of 30 of 200 positions at depth 8 and its gate
  fires on 0.004 to 0.019 % of nodes. A match of that switch alone measures noise. Noted in our match ledger.
- The honest postscript on your own tunable patch (Part 2 refuted the mechanism that nominated it).

WRONG or missing, in order of weight:
1. NO ERROR OVER POSITIONS. "200 of 200 identical on a rerun" shows the run is deterministic. It does not say
   how far a factor would move with 200 OTHER positions, and that is the error your verdicts need. The
   per-position ratio spreads from 0.3 to 4.5 (sd of the log ratio 0.27 to 0.47). From your own records, ratio
   of sums with a bootstrap 95 % interval over positions (4,000 resamples) and the two halves of your list:
       ch4  d8  1.014 [0.972, 1.058]    d12 1.041 [0.981, 1.107]    d16 1.105 [1.038, 1.181]  halves 1.110 / 1.101
       lmrs d8  0.964 [0.922, 1.011]    d12 0.895 [0.851, 0.944]
       smp  d8  1.097 [1.040, 1.159]    d12 0.999 [0.941, 1.059]    d16 1.037 [0.960, 1.125]
       hd   d8  0.995 [0.966, 1.026]    d12 1.039 [0.979, 1.106]    d16 1.056 [0.996, 1.121]
       acr  d8  1.036 [0.997, 1.077]    d12 0.979 [0.928, 1.033]    d16 1.031 [0.969, 1.095]
       thr  d8  1.027 [0.986, 1.073]    d12 1.034 [0.976, 1.095]
       six  d8  1.023 [0.973, 1.075]    d12 0.986 [0.936, 1.041]    d16 0.994 [0.936, 1.058]
   So THREE cells are outside their error: ch4 at depth 16, lmrs at depth 12, smp at depth 8. Your main find
   stands at depth 16. "Monotone +1.4 / +4.1 / +10.5 %" does not: depth 8 and 12 cannot be told from 1.00, nor
   from 1.10 (the medians are 1.000 / 0.991 / 1.099). "ThreatHistory: direction wrong, grows" and "HindsightDepth:
   cost GROWS with depth" (F4) are inside the error. From now on every factor carries its interval over
   positions, and a verdict is given only against it.
2. F2 ("the six-bundle is strongly SUB-ADDITIVE") is stated as a finding while your own S2 names the hole in it:
   lmrs was not measured at depth 16, and at depth 12 it saves 10.5 %. With the intervals above, 0.994 [0.936,
   1.058] against a product of singles that misses its largest saver is not a finding yet. A finding and the
   suspicion that undoes it do not belong in two different sections.
3. Your stamps begin at 05:48:13Z ("run-start"); your claim commit is 05:46:30Z, and the prediction (eight
   switches with file and line) is stamped 21 seconds after "run-start". So the reading happened in an unstamped
   1 min 43 s. Nothing wrong was done, but the first stamp belongs in the command that makes the claim.
4. You are right about glmflash5's branch: it is `cursor/glmflash5-work-cb5c` (Cursor named it); the first
   message's name does not exist. Read that one.

## What the others found since your job 3 began (read this first)

- deepseek5 job 6: 1,400 stop-and-go storms with 4 threads under ThreadSanitizer and 1,200 under
  AddressSanitizer without a report, through a harness that was first shown to report a planted race and a
  planted heap over-read. Its sentence: "a negative is only a result when the same pipe has shown a positive".
  What its files did not carry: exit codes (null in all five controls), and two counts that added two runs
  because a rerun wrote its logs beside the first run's. So: one run = one set of file names.
- glmflash5 job 4 + Opus: an engine answers an option it does not have with ONE line and plays on; ten old
  builds of ours answer with nothing. Before any run, every option a harness sets is looked up in the exe's own
  `uci` list (you did that: kept).
- Here on the PC: our own sanitizer harness was proven the same way an hour ago (a heap over-read and a signed
  overflow planted at the top of the root search: both reported). And the loop now refuses a match whose
  engine does not take one of its options.
- Your F6 (a capped reopen in 90 to 96 % of searches) and F4's counts (a quarter of all nodes are children of
  reduced moves) go to Opus, who runs the HindsightDepth looks at 250,000 nodes.

## Job 4. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop and write with what you have.

Rules as in your first message. Folder `forge-combo29/tests_kimi5_job4/`, report
`forge-combo29/REPORT_kimi5_job4.md`, commit subject "kimi5 job 4 report". The same tree (6b98f217) and build as
job 3. NO TIME IS TYPED ANYWHERE; every step appends `echo "$(date -u +%FT%TZ) <step>" >> stamps.txt` in its
own command, the FIRST one in the command that makes the claim commit. An empty table before every search
(`ucinewgame` + `isready` before every `go`), Threads 1, Hash 16, your 200 positions.

### The question

`Worker::quiet_history()` (search.cpp 1322 to 1345) returns ONE sum: main history + two continuation tables,
plus half of the four-ply table when ContHist4PlyRead is on, plus the threat bonus when ThreatHistory is on.
That one number has THREE consumers:
  (O) move ORDERING (the picker, 798 / 931 / 953 / 990),
  (P) HISTORY PRUNING at 1880: `history < -tune::HistoryPruneMultiplier * depth`,
  (R) the REDUCTION at 2002: `r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2)`,
(P) and (R) both through `const int history = ...` at 1829. The two thresholds were set for a sum of three
terms. A fourth term widens the sum, so more quiet moves may sit at the clamp's ends and on either side of the
pruning line. Your S1 says this is where ch4's 10 % at depth 16 comes from. Prove it or kill it, and if it
holds, repair it.

### Part 1 (first, its own commit "kimi5 job 4 prediction", never edited): from the code only

For ContHist4PlyRead ON against OFF at depth 16, your numbers with the range outside which you call your
reading wrong: (a) the share of quiet moves reaching line 2002 whose clamp term is -2 or +2, OFF and ON;
(b) history-pruning fires per 1,000 nodes, OFF and ON; (c) which consumer carries the extra nodes: P, R, or O
(the order itself), in per cent of the extra 10.5 %; (d) the tree factor at depth 16 of "ch4 ON, but (P) and
(R) read the three-term sum" against all OFF.

### Part 2: counters (a patch as in job 3, text, with its proof)

A histogram of the clamp term at 2002 (five bins, quiet moves only), the count of history-pruning fires at
1880, the count of quiet moves that reach 1829. Each counter with the must-be-nonzero check of your own F8
on ONE position before the matrix runs. Proof that the counter build is the base build: the four known numbers
(bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, `go perft 5` = 4865609) and 200 of 200 at depth 12.
Runs: OFF and ch4, depth 12 and 16.

### Part 3: the repair, as a text patch `HistoryBaseForPruning.patch.txt` (in your folder, never applied to the tree)

ONE new UCI check option, default false: `HistoryBaseForPruning`. When it is on, the `history` of line 1829
(what pruning and the reduction read) is the THREE-term sum (main + the two continuation tables, no four-ply
term, no threat bonus); the ordering sites are not touched. Off = today's code, line for line.
Known answers, each in a raw file:
    K0  the four known numbers with the option off
    K1  option OFF: 200 of 200 nodes equal to the base build at depth 12
    K2  option ON, ContHist4PlyRead off, ThreatHistory off: 200 of 200 EQUAL to the base build (with both
        switches off the three-term sum IS the sum; if this is not 200 of 200 your patch changes something else)
    K3  option ON with ContHist4PlyRead on: differs from ContHist4PlyRead alone in MORE than 0 positions
        (the control that the option arrives and acts)
    K4  the option is in the exe's `uci` list; an input log shows its setoption line
If K2 fails, that ends Part 3 (the patch is wrong; say what came out) and you go on with Part 4 without it.

### Part 4: the factors, each WITH its interval

Depth 12 and 16 (depth 8 only if time is left), ratio of sums against all OFF, with the bootstrap 95 % interval
over positions (say how many resamples and the seed) and the two halves of the list:
    ch4 | ch4 + HistoryBaseForPruning | thr | thr + HistoryBaseForPruning | lmrs (depth 16 is the cell your
    job 3 is missing) | six | six + HistoryBaseForPruning | the five = six without ch4
One table. Beside each factor of a "+ HistoryBaseForPruning" row, the same row without it.
If the minute-40 mark comes first: the ch4 rows and lmrs at depth 16 come before everything else.

### The report's first three lines
(1) K0 to K4, each met or not, in numbers. (2) Prediction against measurement for (a) to (d), and in one
sentence: does the extra tree of ch4 come from the pruning and reduction lines (factor of "ch4 +
HistoryBaseForPruning" at depth 16 with its interval, beside ch4's)? (3) The ONE match you ask of glmflash5
(80,000 nodes, built-in net: which options on each side, how many games for a 95 % error of +/- 10 Elo or
better) and the ONE for our PC at 250,000 nodes.

### What stops what
K0 or K1 failing ends the JOB (the build is not the base build: report what came out). K2 failing ends Part 3
only. The minute-40 mark ends the measuring, not the report. Nothing else stops anything: decide, write it
down, go on.

### At the end
`NOTES_kimi5.md`: LEARNED / FOR deepseek5 (what it should test in your patch: name the sanitizer run and the
positions) / FOR glmflash5 (the match, ready to copy, with every option name as the exe's `uci` list spells it)
/ ANSWER. Then end the run.
