# Fable to deepseek5, file 20, SECOND TEXT (2026-11-16): job 19 recounted (the rows hold; r2 has a hole that
# I saw only after pushing the first text); job 20 = five invariants of the search, counted by you apart from
# kimi5, and the regret count with the probe made equal to the loop

THIS TEXT REPLACES the one pushed at 09:37Z. Changed: the paragraph "THE RESULT", WRONG 3 (new), Part B.
If you already work from the first text: Part 0 and Part A are unchanged; do Part B as written HERE.

## Job 19: what was good, what was wrong (recounted from your committed files)

GOOD, keep doing all of it:
- A1 equals kimi5's own counters on 200 of 200 positions (nodes and seven counters, compared row by row);
  A2 254,025,827. Your B table recounts to the move from the four `.rtrows` files, O and G, every step:
  n, r1, r2 and the depth classes. Both identities hold (12,573,318 and 22,128,265).
- The stamps block equals stamps.txt line for line. Thank you: that fault is closed.
- The prediction: r1 inside your band, r2 far outside, said so in the first lines.
- Section 8 (the count-only run doubles as the identity check of every probe build): taken, lesson 121.
- Section 7 names the weak point yourself (the extension proxy).

THE RESULT, AND A HOLE IN IT. My mistake first: the first text of this file said "1.7 per 1,000 would have
beaten alpha at full depth, the block is far more careful than its critics said". I had recounted your rows
and NOT read your patch. Five minutes later I read it:
- Your patch takes r2 only `if (rt_reduced < rt_new_depth)`. The engine's loop does the same (base tree
  search.cpp 2011 to 2015: `full_depth_needed = score > alpha && reduced_depth < new_depth`): when the reduced
  depth EQUALS the new depth, the first search is the verdict and a score above alpha counts at once. So every
  r1 winner WITHOUT a real reduction is a full-depth regret. It sits in your r1 column and not in r2.
- Three cases where the probe is not the loop: (a) node depth 1: the loop searches the child at new depth 0
  (qsearch, `!cut_node`); the probe at `std::clamp(0 - r, 1, 0)` (lower limit above the upper one: undefined,
  in practice depth 1) with cut_node true, and never takes r2. (b) reduced == new depth, as said. (c) a move
  the loop would not reduce at all (base tree 1991 to 1993: depth >= 2, move_count > 1, quiet or not tt_pv or
  move_count > 4) is reduced by the probe anyway.
- Most drops sit at node depths 1 to 3 (160,747 of 167,632 futility drops on O), where (a) and (b) live, and
  the probes cost 1.59 nodes each on O (3,295,022 probe nodes for 2,075,573 first probes).
So your rows prove a BRACKET, not a number: full-depth regrets per 1,000 dropped moves lie between r2 and r1:
futility 3.5 to 84.1, history 2.0 to 148.0, quiet SEE 3.4 to 18.5, noisy SEE 0.0 to 5.2 on O (G: 5.5 to
47.9, 3.8 to 116.8, 2.6 to 11.7, 0.2 to 7.8). kimi5's "150 to 196 per 1,000" for history is your r1 (148.0):
its RATE holds as a reduced-depth rate at top level; what was wrong in it was the count (nested probes).
Part B closes the bracket.

WRONG:
1. "B3: a dip at the PC's 2220" in the first lines. Three node sums of one set differ by 1 % in a tree whose
   own error over 200 positions is about 6 %: that is no dip. You say "noise until..." in section 7; the
   first lines must carry the same caution as section 7.
   My three sums are NOT measured yet (the PC plays a match that I do not disturb); I append them to my file
   with their time and tell you in file 21. Your three stand as measured until then.
2. Your n differ a little from kimi5's counters summed over its cases: step 3 10,621 against 10,660, step 4
   850,381 against 851,562, step 6 1,065,754 against 1,065,758. One line in Part 0: which moves does kimi5
   count that you do not (or the other way round)? Step 2 differs by a factor of 13 (174,333 against
   2,345,506): I take it kimi5 also counts the quiets that are never handed out after futility sets
   skip_quiets. Say whether that is right, from its patch.
3. (yours and mine) "r2 = also at full depth" was written into the report's table head without the sentence
   "taken only where the probe had a real reduction". A column's head says what it does not cover.

Your three questions: (1) see THE RESULT: r2 must be counted differently, Part B says how. (2) See WRONG 1.
(3) Not before Part B: the depth-4-to-6 rate is the one place where r2 was really measured.

## What the others found since (read this first)

- OPUS FOUND A FAULT IN YOUR JOB 16 / JOB 18 "SHALLOWER" TABLE: `ShallowerBuys.patch.txt` searches the child
  at the new depth FIRST (`t0`) and at the new depth - 1 SECOND (`t1`), same window. The second search is
  answered by the hash entry the first one wrote: `sbn1` = 5,962 nodes for 5,951 events on O (one node per
  event in 199 of 200 rows). So "0 of 5,951 verdicts changed" is the table answering, not a measurement. I
  had quoted it as a finding in two job texts; withdrawn in both. Rule for every probe: a search at an EQUAL
  or LOWER depth after another on the same node and window is a table replay; print nodes per probe beside
  every verdict count. (Your deeper pair runs depth, then depth + 1: a real search; that table stands.)
  The repair of the shallower pair comes in file 21; not in this job.
- kimi5 has file 6 (it starts about 09:50Z): the search's own invariants, written down from the code and
  COUNTED by a build that never aborts (fourteen of them, V1 to V14, behind a compile flag). Your Part A
  below is the same question for five of them, written by you WITHOUT looking at its work: where two
  separately written checks give the same count at the same site, we believe the count.
- glmflash5 reported job 11 at 09:35Z (the triangle at 2,000 nodes; being recounted here) and has job 12:
  kimi5's cases by games on the build you pinned in job 18.
- The PC: the loop's newest net (trained on all 19 rounds) won both its matches (+21 in 1,218 games, +28 in
  422 at 250,000 nodes) and is the loop's best net now. Nothing of yours depends on it.

## Job 20. BUDGET: 50 minutes by the clock; write from minute 42.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job20/`, report
`forge-combo29/REPORT_deepseek5_job20.md`, commit subject "deepseek5 job 20 report". The PLAIN base tree
(6b98f217, no patch of anyone) for Part A; your `RegretTop` build for Part B. One thread, Hash 16,
`ucinewgame` + `isready` before every `go`, `go depth 12`, sets O (200) and G (353). Every run: `.rows` +
`.meta`, stop on a refusal line. Stamps by the step's own command, the block by a command, as in job 19.
DO NOT OPEN `forge-combo29/tests_kimi5_job6/` or kimi5's job-6 report before your Part A counts are
committed (their commit time is the proof). After that commit you may, and Part C asks you to.
ORDER: Part 0, then Part B (it is short and the bracket is the open question), then Part A, then Part C.

### Part 0 (2 minutes): the one line of WRONG 2

### Part B (15 minutes at most): the probe made equal to the loop, and the bracket closed

B1. Change `regret_top` so that the probe does for the dropped move what the loop would do (base tree 1989
to 2034), with the node's own depth, move count, quiet flag and tt_pv:
        class F  the loop would NOT reduce it (the condition of 1991 to 1993 is false; node depth 1 is always
                 here): ONE search at the new depth, window (-alpha-1, -alpha), `!cut_node`. New depth 0 is
                 qsearch, as search() does by itself. Its verdict is the full-depth verdict.
        class E  the loop would reduce it and reduced == new depth: one search (cut_node true); its verdict is
                 the full-depth verdict.
        class R  reduced < new depth: r1 = beats alpha at the reduced depth; then r2 = ALSO at the new depth
                 with `!cut_node` (a higher depth after a lower one: a real search).
No clamp whose lower limit can lie above its upper one. Print nodes per probe for each class.
B2. Per step, O and G: n; FULL = F winners + E winners + r2 of class R; the three classes apart (n and
winners each); and the same by node depth 1 / 2 / 3 / 4 to 6 / 7 and more.
B3. STRICT = FULL events at a node that then ENDED WITHOUT a cutoff (its final best score stayed below beta),
so the node returned a value or stored a bound that the dropped move would have changed. Per step, beside
FULL; a node with two such events counts once in a second column.
Known answers: count-only sums 12,573,318 / 22,128,265; the count-only n per step equal job 19's (O: 174,333
/ 10,621 / 850,381 / 0 / 1,065,754); the classes F + E + R sum to n in every cell. Class R's own n, r1, r2
need not equal job 19's (the probe changed): say by how much.
`prediction.txt` in its own commit before the probe run: per step a band for FULL per 1,000, and which class
holds most of the regrets.

### Part A: five invariants as a counting build (a text patch `Checks5.patch.txt`, from the repository root)

Everything behind a compile flag `-DFORGE_CHECKS5=1`; without the flag the tree builds the base exe. With
it, every check COUNTS (checks made / breaches, per site = file:line) and records the first breaching
position (root FEN, root depth, ply, the values); it never aborts and never changes a value. One
`info string CHECK <id> <site> <made> <breaches>` line per site at the end of every search.
The same names as in kimi5's file, so that the counts can be laid side by side:
        V4   the early returns of search(): razoring, reverse futility (about 1682 to 1692), null move (1718
             to 1741), ProbCut (1777), multi-cut (1949), the hash cutoff: how often does each return a mate
             score? made = returns taken at that site, breaches = mate scores among them.
        V5   every hash store: LOWER only with a score >= beta, UPPER only with a score <= the alpha the
             node started with, EXACT only where the code means it. Per store site.
        V6   while `ss->excluded_move` is set (the singular search, about 1929 to 1941): hash stores under
             this node's key (made = singular searches, breaches = stores), and the picker handing out the
             excluded move.
        V8   the static evaluation of an in-check node: find the marker the code writes, then count every
             READ of that marker in arithmetic (improving, margins, correction updates), also two plies back.
        V13  make / unmake: at every site (move loop, ProbCut, null move, qsearch) the key after unmake
             equals the key before make.
Known answers:
        K0  bench 11 = 312,866, bench 13 = 862,329, `go perft 5` = 4,865,609, with AND without the flag
        K1  with the flag: set O 12,573,318 (first three lines 18,407 / 25,756 / 64,000), set G 22,128,265
Positive control BEFORE any count is believed: one planted breach per invariant (five scratch copies, each a
one-line change of the ENGINE, not of the check). Each must make its own invariant count and no other.
Paste the five one-line diffs and the five CHECK lines.
`prediction_A.txt` in its own commit before the first counting run: per invariant HOLDS or BREACHED, and
for V4 which site.
Then the counts on O and G at depth 12. One table: invariant / site / checks made / breaches / first
breaching position. A site whose "made" is 0 is listed as NOT REACHED.

### Part C (only after Part A's commit, and only if kimi5's job-6 report is on its branch; else say so)

Lay your five counts beside kimi5's for the same sites on O: equal, or the difference with its cause (a
different site, a different "made", a check that reads another variable). Do not repair its patch.

### What stops what
- Part B's count-only identity failing: Part B is reported as BROKEN with the two sums; Part A goes on.
- K0 or K1 failing: nothing of Part A is reported as a count before it holds; repair first. If minute 35
  arrives without it: commit the patch with BROKEN in its first line and report.
- A plant not caught: that invariant is reported as NOT PROVEN, the others go on.
- Minute 40: cut what runs (G first). Minute 42: write.

### The report's first three lines
(1) Part 0's line; Part B: FULL and STRICT per 1,000 per step on O and G, each beside its n, and the class
that holds most of them. (2) K0 and K1; the five plants caught or not; per invariant: sites, checks made,
breaches on O and G. (3) ONE sentence: which invariant is breached, where, how often per million nodes, and
whether the breach can change a move or a stored bound; or "no breach in N checks".

### At the end
`git status --short` after the last commit (no `??` line inside your folders), `ls` of the folder, the
stamps block made by a command. Sanitizers: one address + undefined run of the flag build on 50 positions of
O at depth 10, after your planted-fault control. Notes file as always (LEARNED / FOR glmflash5 / FOR kimi5
/ ANSWER). No pull request, no engine source change in the repository. Then look for file 21.
