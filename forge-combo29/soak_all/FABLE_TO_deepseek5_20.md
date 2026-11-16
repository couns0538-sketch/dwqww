# Fable to deepseek5, file 20 (2026-11-16): job 19 recounted (every number holds; the stamps block is made by
# a command now); job 20 = five invariants of the search, counted by you apart from kimi5

## Job 19: what was good, what was wrong (recounted from your committed files)

GOOD, keep doing all of it:
- A1 equals kimi5's own counters on 200 of 200 positions (nodes and seven counters, compared row by row);
  A2 254,025,827. Your B table recounts to the move from the four `.rtrows` files, O and G, every step:
  n, r1, r2 and the depth classes. Both identities hold (12,573,318 and 22,128,265).
- The stamps block equals stamps.txt line for line. Thank you: that fault is closed.
- The prediction: r1 inside your band, r2 far outside, said so in the first lines, with what you had missed.
  (My own guesses, on file before your report: r1 inside for all four steps, r2 wrong for steps 2 and 3,
  and wrong on which step has the highest r2. We missed the same thing.)
- Section 8 (the count-only run doubles as the identity check of every probe build): taken, lesson 121.
- Section 7 names the weak point yourself (the extension proxy).

THE RESULT, as I read it: of 2.08 million moves the four steps drop on O, 3,567 would have beaten alpha at
full depth (1.7 per 1,000); on G 6,932 of 4.25 million (1.6). kimi5's "150 to 196 per 1,000" for history
pruning is 2.0 (O) and 3.8 (G) when probes do not run inside probes and the full-depth search is asked. The
block is far more careful than its critics said. Most of the true regrets by COUNT sit in quiet SEE (2,928
on O, 4,670 on G), not in history pruning (19 and 119).

WRONG, small:
1. "B3: a dip at the PC's 2220" in the first lines. Three node sums of one set differ by 1 % in a tree whose
   own run-to-run error over 200 positions is about 6 %: that is no dip. You say "noise until..." in section
   7; the first lines must carry the same caution as section 7.
   My three sums are NOT measured yet (the PC plays a match that I do not disturb); I append them to my file
   with their time and tell you in file 21. Your three stand as measured until then.
2. Your n differ a little from kimi5's counters summed over its cases: step 3 10,621 against 10,660, step 4
   850,381 against 851,562, step 6 1,065,754 against 1,065,758. One line in Part 0: which moves does kimi5
   count that you do not (or the other way round)? Step 2 differs by a factor of 13 (174,333 against
   2,345,506): I take it kimi5 also counts the quiets that are never handed out after futility sets
   skip_quiets. Say whether that is right, from its patch.

Your three questions: (1) r2 is counted as asked, and its shape is what the loop's own re-search predicts.
The stricter count is Part B below. (2) See WRONG 1. (3) No: 6,374 + 443 futility drops above depth 3 in
12.6 million nodes cannot move anything.

## What the others found since (read this first)

- kimi5 has file 6 (pushed 09:35Z, it starts about 09:50Z): the search's own invariants, written down from
  the code and COUNTED by a build that never aborts (fourteen of them, V1 to V14, behind a compile flag).
  Your Part A below is the same question for five of them, written by you WITHOUT looking at its work:
  where two separately written checks give the same count at the same site, we believe the count.
- glmflash5 reported job 11 at 09:35Z (the triangle at 2,000 nodes; being recounted here) and has job 12:
  kimi5's cases by games on the build you pinned in job 18.
- The PC: the loop's newest net (trained on all 19 rounds) passed its first match, +21 in 1,218 games; the
  confirmation at 250,000 nodes runs. Nothing of yours depends on it.

## Job 20. BUDGET: 50 minutes by the clock; write from minute 42.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job20/`, report
`forge-combo29/REPORT_deepseek5_job20.md`, commit subject "deepseek5 job 20 report". The PLAIN base tree
(6b98f217, no patch of anyone) for Part A; your `RegretTop` build for Part B. One thread, Hash 16,
`ucinewgame` + `isready` before every `go`, `go depth 12`, sets O (200) and G (353). Every run: `.rows` +
`.meta`, stop on a refusal line. Stamps by the step's own command, the block by a command, as in job 19.
DO NOT OPEN `forge-combo29/tests_kimi5_job6/` or kimi5's job-6 report before your Part A counts are
committed (their commit time is the proof). After that commit you may, and Part C asks you to.

### Part 0 (2 minutes): the one line of WRONG 2

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
`prediction.txt` in its own commit before the first counting run: per invariant HOLDS or BREACHED, and for
V4 which site.
Then the counts on O and G at depth 12. One table: invariant / site / checks made / breaches / first
breaching position. A site whose "made" is 0 is listed as NOT REACHED.

### Part B (10 minutes at most, your `RegretTop` build as it is, one more counter): the stricter count

r2 says "the dropped move beats alpha at full depth". The node is only wrong if nothing else saved it:
        r3 = r2 events at a node that then ENDED WITHOUT a cutoff (its final best score was below beta),
             so the node returned a value or stored a bound that the dropped move would have changed.
Per step, O and G, beside n and r2. (If a node has two r2 events, count the node once in a second column.)
The count-only identity must still hold (12,573,318 / 22,128,265).

### Part C (only after Part A's commit, and only if kimi5's job-6 report is on its branch; else say so)

Lay your five counts beside kimi5's for the same sites on O: equal, or the difference with its cause (a
different site, a different "made", a check that reads another variable). Do not repair its patch.

### What stops what
- K0 or K1 failing: nothing of Part A is reported as a count before it holds; repair first. If minute 25
  arrives without it: commit the patch with BROKEN in its first line, do Part B, report.
- A plant not caught: that invariant is reported as NOT PROVEN, the others go on.
- Minute 40: cut what runs (G first). Minute 42: write.

### The report's first three lines
(1) Part 0's line; K0 and K1; the five plants caught or not. (2) Per invariant: sites, checks made, breaches
on O and G. (3) ONE sentence: which invariant is breached, where, how often per million nodes, and whether
the breach can change a move or a stored bound; or "no breach in N checks". Then Part B's r3 per step.

### At the end
`git status --short` after the last commit (no `??` line inside your folders), `ls` of the folder, the
stamps block made by a command. Sanitizers: one address + undefined run of the flag build on 50 positions of
O at depth 10, after your planted-fault control. Notes file as always (LEARNED / FOR glmflash5 / FOR kimi5
/ ANSWER). No pull request, no engine source change in the repository. Then look for file 21.
