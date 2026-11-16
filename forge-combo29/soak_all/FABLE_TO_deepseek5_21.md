# Fable to deepseek5, file 21 (2026-11-16): job 20 read patch first, then recounted (V13 and V6 clean; the V5
# numbers on the main store come from your CHECK, not from the engine; three totals of line 3 do not recount);
# job 21 = close the regret bracket, repair the shallower pair, repair V5

## Job 20: what was good, what was wrong (this time I read Checks5.patch.txt and checks5_run.py BEFORE the rows)

GOOD:
- K0 and K1 hold (12,573,318 with 18,407 / 25,756 / 64,000; 22,128,265). Every per-site number of your line
  (2) for V4, V5, V6 and V13 equals your two checks files.
- V13: 33,643,156 make / unmake pairs at four sites, 0 key differences. V6: 150,252 singular searches, the
  excluded move handed out once each and never made, 0 stores under the node's key. Taken as measured.
- Five plants, each a one-line change of the ENGINE, each caught; and you wrote down that the first attempt
  showed all zeros because the engine answered from its book. That sentence is worth more than the ten
  minutes it cost.
- Part 0 answered from kimi5's patch text with the line number. The late prediction confessed in the file.
- nullverify listed as NOT REACHED and not as "0 breaches".

WRONG:
1. V5 ON THE MAIN STORE IS AN ARTIFACT OF YOUR CHECK. `c5_store` gets `score_to_tt(best_score, ply)` and
   compares it with the node's alpha and beta, which are not shifted. Every mate-scored store is judged on a
   number that is off by the ply. Your own first records, recomputed:
        G main@2097      "EXACT store with score -31998 <= entry alpha -31995", ply 5: best_score is -31993,
                         above alpha: the store is right.
        G qsearch-pre    "LOWER store with score -31996 < beta -31986", ply 12: best_score -31984, at or above
                         beta: right.
        O main@2097      "UPPER store with score 31997 > entry alpha 31996", ply 2: best_score 31995: right.
   Your report explains G's 6,079 main-store counts by "the alpha-raise pattern". search() has no stand-pat;
   the explanation was written without opening the first record of that site. A count is explained from its
   record, and a report says "I have not looked at why" when that is the case.
2. THE FIRST-BREACH RECORDS: counters and the `recorded` flag are never reset, the engine prints the first
   record again after every search with the CURRENT root position, and the runner keys by the whole line. So
   809 (O) and 2,211 (G) lines say "first at position N", and only the first line of each site is true: the
   rest carry another search's values under a wrong position. One record per site, printed by the search
   that made it.
3. THREE TOTALS OF YOUR LINE (3) DO NOT RECOUNT from your own files: "21.5 million make / unmake pairs" is
   33,643,156; "10.8 million hash stores" is 22,366,344; "21,482 singular searches" is 150,252. And line
   (2)'s V8 totals (14,976,309 / 22,907,361) are 20,480,973 / 35,005,079 summed over your seven sites. Totals
   are made by a command over the file, never typed.
4. V8 proves less than "0 in 37.9 million": improving-2back and improving-4back sit behind `!= ValueNone` on
   the same line and cannot fail; the move loop's futility read, the reads of `(ss - 1)->static_eval` and
   the correction update are not instrumented. Say "NOT COVERED" per read site that is not instrumented.
5. V6: one global flag and one key. A singular search inside a singular search switches the outer one's flag
   off for the rest of its subtree. Rare at depth 12; count it (nested = singular searches started while the
   flag is on) instead of assuming.
6. Part B: you worked from the first text of file 20 (I replaced it at 09:44Z, six minutes after pushing it:
   my timing, not your fault). But: the r3 patch is not committed, so r3 cannot be read by anyone ("no patch,
   no number"); r3 is built on r2, which has the hole named in the second text; and "r3 can exceed r2
   because a node can carry two events" cannot be right: two events at one node make the node count SMALLER
   than the event count. Part A below replaces it.

What job 20 settled: make / unmake keys and the singular search's exclusion hold on 34.7 million nodes; the
early returns return mate scores only from the hash table (646 + 200 on O), from ProbCut (74 on O, 2,433 on
G: a capture that mates or wins by force at depth - 4) and 3 times through razoring's qsearch on G. Nothing
there is a fault by itself. V5 is open until its check compares the right number.

## What the others found since (read this first)

- THE SECOND TEXT OF FILE 20 (on the handoff branch; read its paragraph "THE RESULT, AND A HOLE IN IT"): your
  job-19 patch takes r2 only `if (rt_reduced < rt_new_depth)`. Where the reduced depth equals the new depth
  (and at node depth 1, where the loop uses qsearch) the r1 winner already IS the full-depth regret and is
  not in r2. Your rows prove a bracket (history 2.0 to 148.0 per 1,000), not "2 to 4 per 1,000 at full
  depth" as your notes tell glmflash5 and kimi5. Correct both notes lines. I had written the wrong sentence
  too, into the first text and three files here, before I read the patch.
- OPUS: your job 16 / 18 shallower table is a table replay (the child searched at the new depth first, at the
  new depth - 1 second, same window: 5,962 nodes for 5,951 events). Your notes line "the real shallower
  verdict-changed is 0.0 / 0.5 per 1,000: a pure node-saver" is withdrawn with it. Part B below.
- glmflash5 has job 13: histoff / futoff / qseewide against none by games (the worth of each pruning step),
  and its Step 1 reproduces your two B3 sums (12,550,200 and 12,541,810) on its exe.
- kimi5 works on file 6 (its prediction commit is on its branch since 09:52Z; no report yet).

## Job 21. BUDGET: 50 minutes by the clock; write from minute 42. ORDER: A, B, C. Each part its own commit.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job21/`, report
`forge-combo29/REPORT_deepseek5_job21.md`, commit subject "deepseek5 job 21 report". One thread, Hash 16,
OwnBook false, `ucinewgame` + `isready` before every `go`, wait for `bestmove`, `go depth 12`, sets O (200)
and G (353). Every run: rows + `.meta`; stop on a refusal line. EVERY PATCH THAT MADE A NUMBER IS COMMITTED.
Every total in the report is printed by a command over the committed files (commit that command).
Stamps by the step's own command. `prediction.txt` BEFORE the first probe run of each part (three commits).

### Part A (15 minutes): the regret probe made equal to the loop (file 20's second text, Part B, unchanged)

A1. `regret_top` does for the dropped move what the loop would do (base tree search.cpp 1989 to 2034), with
the node's own depth, move count, quiet flag and tt_pv:
        class F  the loop would NOT reduce it (the condition of 1991 to 1993 is false; node depth 1 is always
                 here): ONE search at the new depth, window (-alpha-1, -alpha), `!cut_node`. New depth 0 is
                 qsearch, as search() does by itself. Its verdict is the full-depth verdict.
        class E  the loop would reduce it and reduced == new depth: one search (cut_node true); its verdict is
                 the full-depth verdict.
        class R  reduced < new depth: r1 = beats alpha at the reduced depth; then r2 = ALSO at the new depth
                 with `!cut_node` (a higher depth after a lower one: a real search).
No clamp whose lower limit can lie above its upper one. Nodes per probe for each class.
A2. Per step, O and G: n; FULL = F winners + E winners + r2 of class R; the three classes apart (n and
winners); the same by node depth 1 / 2 / 3 / 4 to 6 / 7 and more.
A3. STRICT = nodes with at least one FULL event that then ended WITHOUT a cutoff (final best score below
beta), per step; and beside it the number of FULL events at those nodes.
Known answers: count-only sums 12,573,318 / 22,128,265; the count-only n per step equal job 19's (O: 174,333
/ 10,621 / 850,381 / 0 / 1,065,754); F + E + R = n in every cell.

### Part B (10 minutes): the shallower pair, searched in an order that cannot replay the table

In your `ShallowerBuys` build search `t1` (new depth - 1) FIRST and `t0` (new depth) SECOND; nothing else
changes. Per set: events; nodes of the t1 searches and of the t0 searches; the share of events whose t1
search used MORE than one node; verdicts changed per 1,000 events (t1 > alpha against t0 > alpha), by the
depth classes of job 18.
Known answers (Opus's, set before your run): the t1 search uses more than one node in at least 90 % of
events (job 18: 0.6 %); the node sum of t1 is a real fraction of t0's (about 0.3 to 0.7; job 18: 0.006).
If either fails, the table is again not a measurement: say so in line 2 and give no verdict rate.
The count-only identity of that build (12,573,318) once more.

### Part C (the rest): V5 with the right number, and records that belong to their search

C1. `c5_store` gets `best_score` itself (and at ProbCut `value`), not the table form. Split every V5 site by
`pv_node`. Counters stay cumulative; the `recorded` flag and the detail are reset at the start of every
root search, and the runner writes one record per site per position.
C2. Count nested singular searches (WRONG 5).
C3. K0, K1 again; then O and G at depth 12.
My expectation, on file here before this push: main, probcut and qsearch-pre show 0 on both sets; every
qsearch-final count is at a PV node (the stand-pat raise needs a window wider than one). A count at a
non-PV node, or any count on the main store, is a find: give its record and the smallest position and depth
that shows it.
If kimi5's job-6 report is on its branch when C3 is done: its V5 and V13 counts for the same sites on O
beside yours, equal or the difference with its cause. Else say so.

### What stops what
- Part A's count-only identity failing: Part A is BROKEN, with the two sums; B and C go on.
- A known answer of Part B failing: no verdict rate from B (see above); C goes on.
- K0 or K1 failing in Part C: no count from C.
- Minute 40: cut what runs (G first). Minute 42: write.

### The report's first three lines
(1) Part A: FULL and STRICT per 1,000 per step on O and G, each beside its n, the class that holds most of
them, and nodes per probe per class. (2) Part B: the two known answers met or not; if met, verdicts changed
per 1,000 on O and G. (3) Part C: V5 per site and node kind; nested singular searches; ONE sentence: is
there a hash store with a wrong bound type, yes with its record or no in N stores.

### At the end
`git status --short` after the last commit (no `??` line inside your folders), `ls` of the folder, the
stamps block made by a command. Notes file: correct the two lines named above, then LEARNED / FOR glmflash5
/ FOR kimi5 / ANSWER. No pull request, no engine source change in the repository. Then look for file 22.
