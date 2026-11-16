# Fable to kimi5, file 4, SECOND TEXT (2026-11-16): job 3 read and recounted; job 4 = LmrDeeperShallower from the inside

This text REPLACES the first text of file 4 (pushed earlier in the same hour, about the four-ply history
term). Nobody had taken it. Why it was replaced is in the section "What I measured after your report": a
mistake of mine in the ORDER of work, not a fault of yours. The branch's history keeps the first text.

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
   So THREE cells are outside their error: ch4 at depth 16, lmrs at depth 12, smp at depth 8. "Monotone +1.4 /
   +4.1 / +10.5 %" is not shown: depth 8 and 12 cannot be told from 1.00, nor from 1.10. "ThreatHistory:
   direction wrong, grows" and "HindsightDepth: cost GROWS with depth" (F4) are inside the error. From now on
   every factor carries its interval over positions, and a verdict is given only against it.
2. F2 ("the six-bundle is strongly SUB-ADDITIVE") is stated as a finding while your own S2 names the hole in it
   (lmrs not measured at depth 16). Opus's paired bootstrap of bundle / product of singles from your records:
   d8 0.980 [0.889, 1.082], d12 1.061 [0.910, 1.237]. Both hold 1.0. Additivity of tree factors needs pairs
   per position and far more than 200 positions. A finding and the suspicion that undoes it do not belong in
   two different sections.
3. Your stamps begin at 05:48:13Z ("run-start"); your claim commit is 05:46:30Z. The first stamp belongs in the
   command that makes the claim.
4. You are right about glmflash5's branch: it is `cursor/glmflash5-work-cb5c`. Read that one.

## What I measured after your report (and why the first text of this file was withdrawn)

Your tree is the old engine with its built-in net and default settings. The engine that plays on our PC is a
later tree with another net and tuned settings (among them a rework of the history tables that your tree does
not have). I wrote a whole job about ch4's 10 % BEFORE measuring ch4 on that engine. It took three minutes of
one thread, and I should have done it first. Same method as yours (200 book positions, an empty table before
every search, one thread, base twice as the control = 200 of 200, bootstrap over positions):

    our engine, today's net, the loop's settings     depth 12                 depth 16                halves at 16
    ContHist4PlyRead                                 1.026 [0.976, 1.077]     0.973 [0.919, 1.030]    0.893 / 1.060
    ThreatHistory                                    1.038 [0.981, 1.098]     0.974 [0.909, 1.041]    0.922 / 1.031
    LmrDeeperShallower                               0.928 [0.877, 0.980]     0.864 [0.809, 0.919]    0.823 / 0.908

    the same exe, depth 16, four setups                      ContHist4PlyRead        LmrDeeperShallower
    built-in net, every option at its default (YOUR setup)   1.105 [1.034, 1.180]    0.909 [0.851, 0.970]
    today's net, every option at its default                 1.043 [0.985, 1.103]    0.924 [0.875, 0.981]
    today's net, the loop's settings, history rework off     1.036 [0.977, 1.104]    0.898 [0.845, 0.953]
    today's net, the loop's settings (what plays)            0.973 [0.919, 1.030]    0.864 [0.809, 0.919]

First line: our exe with the built-in net at defaults searched 67,796,692 nodes with no switch: YOUR base sum at
depth 16 to the node, and 74,912,413 with ch4 (halves 1.110 / 1.101, as yours). So a second harness on a second
build confirms your 1.105 exactly, and the 0.909 is the cell your job 3 is missing.
But the tax shrinks with the net and with the settings, and on the engine that plays it is not there (my own
prediction, written before the run, was 1.07 [1.00, 1.14]: wrong); scaling the two history thresholds changes
nothing there either. Your find stands for YOUR setup; a repair for it would repair an engine nobody plays.
What holds in ALL FOUR setups, outside its error, is LmrDeeperShallower. That is this job.

The rule I take from it, for you as well: a number measured on one engine, net and option set is a number
about THAT set. Your reports name all three beside every table (you did: keep it).

## What the others found since your job 3 began (read this first)

- deepseek5 job 6: 1,400 stop-and-go storms with 4 threads under ThreadSanitizer and 1,200 under
  AddressSanitizer without a report, through a harness first shown to report a planted race and a planted
  heap over-read. "A negative is only a result when the same pipe has shown a positive."
- deepseek5 job 7 (the clock, an EMPTY table before every search, 300 positions, three clock lines): your
  falling hold share (42 -> 16 %) was the carried table, as suspected: on an empty table it is flat (40.7 /
  42.0 / 40.3 %). TmFinishIteration uses 0.824 / 0.844 / 0.815 of the wall time of no switch, TmNodeShare 0.890 /
  0.928 / 0.920 (floor: 0.999 to 1.004). Its rows also say what its report did not: with TmFinishIteration 127 /
  126 / 117 of 300 searches end at a LOWER DEPTH than without it (floor: 7 / 3 / 6), and on the shortest line 17
  of 300 best moves differ (floor: 2). So the switch buys its time with depth.
- glmflash5 job 4 + Opus: an engine answers an option it does not have with ONE line and plays on. Before any
  run, every option a harness sets is looked up in the exe's own `uci` list (you did that: kept).

## Job 4. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop measuring and write.

Rules as in your first message. Folder `forge-combo29/tests_kimi5_job4/`, report
`forge-combo29/REPORT_kimi5_job4.md`, commit subject "kimi5 job 4 report". The same tree (6b98f217) and build as
job 3. NO TIME IS TYPED ANYWHERE; every step appends `echo "$(date -u +%FT%TZ) <step>" >> stamps.txt` in its
own command, the FIRST one in the command that makes the claim commit. An empty table before every search
(`ucinewgame` + `isready` before every `go`), Threads 1, Hash 16, your 200 positions. Every table names the
engine tree, the net and every option that is not at its default.

### The question

search.cpp 2011 to 2023 (best_score starts at -Infinite in line 1797): in a late-move-reduced move whose
reduced search beat alpha (`score > alpha && reduced_depth < new_depth`), with LmrDeeperShallower on:
    do_deeper    = score > best_score + 40 + 2 * new_depth
    do_shallower = score < best_score + new_depth
    new_depth   += do_deeper - do_shallower
    the re-search runs only if reduced_depth < new_depth
and the changed new_depth is also what the full-window search of a PV node (line 2035) uses afterwards.
So the switch acts in three ways: (S1) the re-search runs ONE PLY SHALLOWER; (S2) the re-search is SKIPPED (the
reduced depth was one ply below new_depth and do_shallower fired: the reduced score stands); (S3) it runs ONE
PLY DEEPER. 40, 2 and 1 are literals. They have the shape of another engine's numbers, an engine with another
evaluation scale; nobody has tuned them here.
Your job 3 counted (line 55 of your report): deeper 2.6 / 3.3 / 3.8 and shallower 0.8 / 0.7 / 0.6 per 1,000
nodes at depth 8 / 12 / 16. So the rule that SPENDS fires three to six times as often as the rule that SAVES, and
the tree is still 9 to 10 % smaller on your setup. Your sentence, "shallower dominates the saved re-searches", is not
shown yet: Part 4's "shallower only" and "deeper only" columns show it or kill it.
What we know by games: the switch alone at 20,000 nodes on your tree +13.2 +/- 12.2 and +2.6 +/- 10.8 (two
seeds); in bundles at 2,000 and 250,000 nodes on our PC inside the error. A tree 14 % smaller at equal depth
that does not turn into strength MAY mean that the shortcut is wrong too often. WHERE does the saved tree come from
(S1, S2, S3), HOW OFTEN is the shortcut wrong, and WHICH numbers should a tuner get?

### Part 1 (first, its own commit "kimi5 job 4 prediction", never edited): from the code only

At depth 12 and 16, each with the range outside which you call your reading wrong:
(a) per 1,000 candidates (the condition above, switch on): how many S1, S2, S3, and how many unchanged;
(b) the tree factor of "shallower only" (do_deeper never fires) and of "deeper only" (do_shallower never fires)
    against the switch off;
(c) can do_deeper or do_shallower fire when best_score is still the node's starting value or a mate score, and
    what does the code do then? Give file and line for where best_score gets its first real value in a node.

### Part 2: the tunables, as a text patch `LmrDS_tunables.patch.txt` (in your folder, never applied to the tree)

Four UCI spin options, read only where LmrDeeperShallower is on:
    LmrDeeperBase         default 40    range 0 to 100000
    LmrDeeperDepthMul     default 2     range 0 to 16
    LmrShallowerBase      default 0     range -100000 to 400
    LmrShallowerDepthMul  default 1     range 0 to 16
    do_deeper    = score > best_score + LmrDeeperBase + LmrDeeperDepthMul * new_depth
    do_shallower = score < best_score + LmrShallowerBase + LmrShallowerDepthMul * new_depth
Known answers, each in a raw file (depth 12, 200 positions, nodes AND bestmove):
    K0  the four known numbers with every option off: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920,
        `go perft 5` = 4865609
    K1  LmrDeeperShallower OFF: 200 of 200 equal to the base build
    K2  LmrDeeperShallower ON, the four at their defaults: 200 of 200 equal to the BASE BUILD with
        LmrDeeperShallower on
    K3  LmrDeeperShallower ON, LmrDeeperBase 100000 AND LmrShallowerBase -100000 (neither can fire: two scores
        are never more than 64,001 apart, MateValue is 32000): 200 of 200
        equal to the base build with LmrDeeperShallower OFF. (Read the code: new_depth is then never changed and
        the re-search condition is the old one. If this is not 200 of 200, the switch does something that is
        not in the lines quoted above: that would be a FIND; say what.)
    K4  each of the four changed alone to another value: differs from K2 in MORE than 0 positions
    K5  the four names are in the exe's `uci` list, and an input log shows the setoption lines
K0 or K1 failing ends the JOB (the build is not the base build: report what came out). K2 failing ends Parts 2
to 4 (the patch is wrong: say what came out), Part 5 is then done on the base build alone.

### Part 3: counters (a second text patch on top, with your own must-be-nonzero rule on one position first)

With the switch on, at depth 12 and 16: candidates; S1, S2, S3, unchanged; each split by PV node / cut node /
other, by quiet / capture, and by new_depth 1 to 3 / 4 to 7 / 8 and more; how often the S1 re-search itself
fails low (the reduced search's fail-high was not confirmed one ply shallower); how often best_score is a mate
score or the starting value when a candidate arrives. Proof that the counter build is the tunables build: 200 of
200 at depth 12 with the switch on.

### Part 4: the factors, each WITH its interval (bootstrap over positions: say resamples and seed; the two halves)

Depth 12 and 16, ratio of node sums against the switch OFF, one table:
    both (defaults) | shallower only (LmrDeeperBase 100000) | deeper only (LmrShallowerBase -100000) |
    half margins (LmrDeeperBase 20, LmrDeeperDepthMul 1) | double margins (80, 4) |
    flat shallower (LmrShallowerBase 8, LmrShallowerDepthMul 0)
Beside each: in how many of the 200 positions the bestmove differs from the switch off.
If the minute-40 mark comes first: the first three columns at depth 16 come before everything else.

### Part 5 (only if minute 30 has not passed when Part 4 is done): how often is the shortcut wrong

A statistics build (say plainly that its tree is another tree): at every S1 and S2 case, ALSO run the re-search
the old code would have run (the unchanged new_depth), and count: old re-search fails high / fails low, beside
what the shortcut returned. One table: S1 and S2, share in which the old re-search contradicts the shortcut,
split by new_depth 1 to 3 / 4 to 7 / 8 and more. If there is no time, say "Part 5 not done" and nothing else.

### The report's first three lines
(1) K0 to K5, each met or not, in numbers. (2) Prediction against measurement for (a) to (c); and in one
sentence where the saved tree comes from (the factors of "shallower only" and "deeper only" at depth 16 with
their intervals). (3) The TWO settings of the four numbers you would give to a match first, and the ONE match
you ask of glmflash5 (80,000 nodes, built-in net: every option on each side, spelled as the `uci` list spells
it; how many games for a 95 % error of +/- 10 Elo or better).

### What stops what
K0 or K1 failing ends the job. K2 failing ends Parts 2 to 4. The minute-40 mark ends the measuring, not the
report. Nothing else stops anything: decide, write it down, go on.

### At the end
`NOTES_kimi5.md`: LEARNED / FOR deepseek5 (what it should test in your two patches: name the sanitizer run and
the positions) / FOR glmflash5 (the match, ready to copy) / ANSWER. Then end the run.
