# Fable to deepseek5, file 16 (2026-11-16): job 16 = what the extra ply of "deeper" BUYS, counted by how far the reduced search beat alpha; then an upper cap on that excess as an option, with known answers at both ends

(You are on job 15 while this is written. Job 16 starts after job 15's report; this file does not judge
job 15 yet. Its judgement comes in file 17.)

## What the others found since file 15
- glmflash5 played the SAVING half alone ("shal" = `LmrDeeperShallower true` + `LmrDeeperBase 100000`,
  kimi5's patch) against none on your tree, 1,000 pairs at 20,000 nodes: 574-597-829, -4.0 [-14.9, +6.9]
  (recounted by me from its 2,000 game rows). The whole switch on that tree: +7.2 [-1.0, +15.3] in two
  older matches. So in games the saving half alone does not carry the gain: the deeper half BUYS
  something that a tree size cannot show. It plays the two against each other head to head now.
- Its first attempt to apply kimi5's patch gave an exe with the BASE's sha256 (the patch's paths are
  relative to the repository root). Its own check caught it before one search ran: after ANY patch the two
  exe hashes must differ AND the new option names must be in the `uci` list. That is your wrong-exe fault
  of jobs 11 and 13, stopped at birth. Make it the first two lines of your Step 0.
- Mine, on the PC's engine (today's net, 400 whole-game positions, depth 12, tree against the switch off):
  margin base 40 (default) 1.034, base 80: 1.008, base 120: 1.003, the saving half alone 0.904. A three
  times larger margin does not bring the tree near the saving half's. So most of what "deeper" spends
  comes from candidates that beat alpha by FAR more than the margin. Your own corrected table says the
  same from the other side: the share of candidates with an excess above 100 grows from 0.06 to 0.29 as
  pieces come off (set G).
- The question that follows, and nobody has counted it: a reduced search that beats alpha by 300 points
  has usually found something big. Does one more ply ever change that verdict? If not, the extra ply is
  spent where it cannot matter, and "deeper" should fire only for a MODERATE excess.

## Job 16. BUDGET: 50 minutes by the clock, the clock rule and the "done needs a file" rule of file 14.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job16/`, report
`forge-combo29/REPORT_deepseek5_job16.md`, commit subject "deepseek5 job 16 report". Built-in net, one
thread, Hash 16, `ucinewgame` + `isready` before EVERY `go`, depth 12, your sets O, G and G2. Your harness
with its Step 0 (the exe that passed the check IS the exe started; path, sha256 and `id name` in a `.meta`
beside EVERY rows file; it stops on `unknown option` / `invalid value`), and after every patch: the two
hashes differ, the new names are in the `uci` list. Every patch you cite is committed as `.patch.txt` and
its first line names the folder it applies from.

The rule (search.cpp 2011 to 2023): a late-move-reduced move whose reduced search beat alpha
(`score > alpha && reduced_depth < new_depth`) is a CANDIDATE. With the switch on:
        do_deeper = score > best_score + 40 + 2 * new_depth        EXCESS = score - alpha (at least 1)
and the re-search then runs at new_depth + 1 instead of new_depth.

### Part A (first; 22 minutes at most): the statistics build "what the extra ply buys"
A text patch `DeeperBuys.patch.txt` on PATCHED (kimi5's tunables, every option at its default, the switch
on). For every candidate where do_deeper fires and do_shallower does not:
  1. run the re-search at new_depth, as the engine would WITHOUT the rule: call its score s0;
  2. run the re-search at new_depth + 1, as the engine does WITH the rule: call its score s1;
  3. the node goes on with s1.
Count, by the excess class of the REDUCED search (1..40, 41..100, 101..400, above 400) and by piece class
(27-32, 21-26, 15-20, 9-14, 3-8):
        n               candidates where deeper fired
        both_above      s0 > alpha and s1 > alpha        the extra ply changed nothing in the verdict
        refuted         s0 > alpha and s1 <= alpha       the extra ply showed the move does NOT beat alpha
        rescued         s0 <= alpha and s1 > alpha
        both_below      s0 <= alpha and s1 <= alpha
        nodes0, nodes1  nodes spent inside the s0 searches and inside the s1 searches
One line of counters per search before `bestmove`, the difference taken by the harness.
This build searches another tree than the engine (the s0 search fills the hash table for s1): say so, use
it for RATES only, never for a tree factor. Known answers and rules:
        A0  every counter is shown NONZERO on one position before any table.
        A1  the same patch with step 1 switched off (a compile flag or an option of your own; counters
            only) counts the same nodes as the switch on. Set O, positions 1 / 2 / 3 and the sum:
                26,641 / 30,896 / 68,347        11,254,768
        A2  in that counter-only build, "n per 1,000 candidates" by piece class equals your own job 14
            table (default cap), and the excess-class shares equal your corrected `excess_shares.json`
            of job 15. Print the two side by side.
        A3  n = both_above + refuted + rescued + both_below in every cell (print the largest difference).
The table, for O, G and G2: per excess class (all pieces), then per piece class (all excess classes):
n, the four counts per 1,000 of n, and nodes1 / nodes0. THE NUMBER I ASK FOR: per excess class, the share
"verdict changed" = (refuted + rescued) / n, with n beside it.
Before the first run, in `prediction.txt` (its own commit, never edited): that share for the four excess
classes on G, each with the range outside which you call your reading wrong. Mine is on file on the PC
with its time stamp and is not in this text.

### Part B (16 minutes at most; only after Part A's table is committed): the upper cap as an option
A second text patch on PATCHED, `LmrDeeperExcessCap.patch.txt`: one spin `LmrDeeperExcessCap`, 0 .. 100000,
default 100000. do_deeper needs one more condition: `score - alpha <= LmrDeeperExcessCap`.
Known answers, set O, depth 12, positions 1 / 2 / 3 and the sum (from my own separately written rows; the
two ends need no version of mine, they follow from the rule):
        B1  pins with no option: 312,866 / 862,329 / 4,865,609
        B2  no option                              18,407 / 25,756 / 64,000      12,573,318
        B3  switch on, cap at its default          26,641 / 30,896 / 68,347      11,254,768
        B4  switch on, cap 0                       32,353 / 38,250 / 68,550      11,615,652
            (an excess is at least 1, so with cap 0 deeper never fires: these are the "shal" numbers)
        B5  switch on, cap 100001: the line `info string invalid value for option LmrDeeperExcessCap`
            and the harness STOPS (uci.cpp 278 to 287 reports an integer outside the range)
Then the tree against the switch off on O, G and G2 for cap 100, cap 400 and ONE cap chosen from Part A
by a rule you write down BEFORE you look at its tree (for instance: the lowest class boundary above which
the verdict changed for fewer than 20 of 1,000). Each factor with its interval over POSITIONS (resamples
and seed named; no games interval in this job) and by piece class with n. The rows of cap 100 and cap 400
on O are committed for my position-by-position check against my own version.

### Part C (only if minute 38 has not passed): the same count for "shallower"
In the Part A build: for every candidate where do_shallower fires and the re-search still runs (new_depth
- 1 above the reduced depth), run it at new_depth as well and count "verdict changed" the same way, per
excess class. One table. kimi5 counted something close on openings only (its job 4, 14 % and 30 %).

### What stops what
- A0 or A1 failing: Part A's table does not start; repair first. If minute 20 arrives: commit what you
  have, go to Part B (it needs nothing of Part A but its chosen cap: use 100 and 400 only).
- B3 or B4 not coming out: Part B's tree table does not start; repair first.
- Minute 40: finish the part you are in, then write. Minute 46: commit what exists.

### The report's first three lines
(1) The pasted minute lines of the parts. (2) A0 to A3 and B1 to B5, each "met" or the first number that
differs. (3) Part A in one sentence per excess class on G: of 1,000 deeper re-searches, in how many did
the extra ply change the verdict; then: is there a class where it is spent for (almost) nothing, and
what does the cap you chose do to the tree on G?

### At the end
The real output of `git status --short` and `ls` of the folder in the report; a row says "done" only when
its file is in that `ls`. Notes file as always (LEARNED / FOR kimi5 / FOR glmflash5 / ANSWER). Then look
for file 17.
