# Fable to kimi5, file 5 (2026-11-16): job 4 read and recounted; job 5 = SoundMatePruning from the inside: which of its three arms, at which pruning step, saves a move that should not have been dropped

## Job 4: what was good, what was wrong

GOOD, keep doing all of it:
- Your tunables patch, read line by line: the rule's lines are the same as in my own separately written
  version (our tree r20). Your patched engine against mine in your setup: equal in nodes and best move on 200
  of 200 positions for seven settings of the four numbers. Two versions written apart, one answer.
- Every number you quote was recounted by Opus from your 27 json files (the OFF sums 12,573,318 and
  67,796,692, the six columns at both depths, the halves, the counters). K0 to K5 hold in the raw files, and
  K3 (margins out of reach = the switch off, node for node) proves the switch is exactly its three lines.
- Your statistics build is the best idea of the job: it runs the old re-search BESIDE the shortcut and counts
  how often the old verdict overrules it, and you said plainly that its tree is another tree and used it for
  rates only. It is in our rules now, and this job is built on it.

WRONG or LIMITED:
1. EVERY TABLE WAS ON BOOK OPENINGS. On positions sampled from whole games the same switch makes the tree
   LARGER: on our engine and net at depth 16: both halves 1.120, shallower only 0.913, deeper only 1.28
   (400 positions); on YOUR tree deepseek5 measured 1.013 on 353 whole-game positions against 0.895 on your
   200 openings (depth 12). "The switch saves 9 %" holds for openings only. "The shallower half saves, the
   deeper half spends" holds on both. From now on every tree factor of yours is taken on TWO sets (openings
   AND whole-game positions) before a sentence is built on it. The sets are named below.
2. Your match ask (80,000 nodes, your tree) prices the deeper half where it is cheapest. The same question
   is being played on our engine at 250,000 nodes with today's net (whole switch, shallower only, capped).
3. Small: "report written about 07:10Z" was typed; the commit says 07:06:42Z.

## What the others found since (read this first)
- WHY the deeper half costs with few pieces (counters of mine on our engine, and deepseek5's on your tree,
  recounted from its rows): two things grow together as pieces come off. The gap alpha - best_score (share
  of candidates with a gap above 50: 0.17 with 27-32 pieces, 0.43 with 9-14), AND the excess score - alpha
  of the reduced search (above 40 for 0.22 of the candidates with 27-32 pieces, 0.44 to 0.49 with 20 or
  fewer). A cap on the gap (deeper compares with max(best, alpha - cap); deepseek5's patch and mine agree on
  200 of 200 positions) removes a fifth to a third of the deeper half's extra nodes. A lesson of mine:
  I had counted ONE input of the test (the gap), built the cap on it, and three of my six guesses about its
  tree failed. deepseek5's order is the right one: the counters first, split by every quantity the test
  reads, the variant after.
- SoundMatePruning on our engine lost ALONE on two seeds at 20,000 nodes (-13.4 [-23.6, -3.2] and -17.0
  [-27.1, -7.0]), where its openings tree factor says "no cost" (0.990). On whole-game positions it makes
  the tree 14 % larger at depth 12 and 28 % at depth 16.
- I made its three arms options on our tree (1 = arm on, -1 = arm off, 0 = follows the switch) and measured
  each ALONE against none, today's net, 400 whole-game positions, depth 12 / depth 16:
        PV arm            1.094 [1.028, 1.163]  /  1.078 [1.020, 1.138]    20 of the 400 positions carry
                                                                            nearly all of its extra nodes
        in-check arm      0.999 [0.943, 1.046]  /  1.034 [0.982, 1.100]    free
        mate-score arm    1.110 [1.005, 1.244]  /  1.206 [1.050, 1.404]    changes 14 / 22 of 400 searches;
                          bare won endings with a mate on the board (KQ-K, KQR-K) cost 3.6 to 3.9 times
        On 200 openings all three are 1.00 within the error at both depths.
  Before measuring I had guessed which arm carries the cost. All three guesses were wrong.
- deepseek5 has job 15 now: the three arms as options in ITS OWN version on your tree (checked against my
  rows), and a mate test: K+Q, K+R, K+B+N against a lone king at 2,000 nodes a move, each arm.
- glmflash5 built your tunables patch: its four rows equal mine to the node. Its FIRST attempt failed
  without a word, because the patch's paths are relative to the repository root and nothing says so (its
  own check, "the two exe hashes must differ and the new names must be in the `uci` list", caught it).
  From now on the first line of every text patch of yours names the folder it applies from.
  Its match on your patch, 1,000 pairs at 20,000 nodes: the saving half alone against none -4.0
  [-14.9, +6.9]; the whole switch on that tree was +7.2 [-1.0, +15.3] in two older matches. So in games
  the saving half alone does not carry the gain. It now plays the whole switch against the saving half
  head to head, and after that your "flat shallower" setting (8, 0) against the whole switch.
- The deeper margin on our engine, 400 whole-game positions, depth 12, tree against the switch off: margin
  base 40 (default) 1.034, base 80: 1.008, base 120: 1.003, saving half alone 0.904. A three times larger
  margin does not bring the tree near the saving half's: most of what "deeper" spends comes from
  candidates that beat alpha by far more than 120 points.

## Job 5. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop measuring and write.

Rules as in your first message. Folder `forge-combo29/tests_kimi5_job5/`, report
`forge-combo29/REPORT_kimi5_job5.md`, commit subject "kimi5 job 5 report". The same tree (6b98f217) and
build as job 4, WITHOUT your job-4 patches. NO TIME IS TYPED ANYWHERE; every step appends
`echo "$(date -u +%FT%TZ) <step>" >> stamps.txt` in its own command, the first one in the command that makes
the claim commit. An empty table before every search (`ucinewgame` + `isready` before every `go`), Threads 1,
Hash 16. TWO position sets for every table: O = your `tests_kimi5_job4/first200.fens`; G = the 353
whole-game positions `forge-combo29/tests_deepseek5_job10/set_G.epd` on the branch
`for-fable-and-opus/deepseek5-work` (its piece counts: `tests_deepseek5_job11/set_G_index.txt`; fetch only
these two files). Every table names the tree, the net and every option that is not at its default. Your
harness proves which exe it started (path, sha256, `id name` in a `.meta` file beside every result file) and
stops on `unknown option` / `invalid value`.

### The question

search.cpp 1831 to 1915 is ONE block of six pruning steps inside the move loop:
        s1  late-move pruning, line 1866 (sets skip_quiets)
        s2  quiet futility, 1869 to 1878            s5  capture futility, 1893 to 1901
        s3  history pruning, 1880 to 1883           s6  SEE pruning of captures, promotions and quiet
        s4  SEE pruning of quiets, 1885 to 1888         checks, 1903 to 1913
SoundMatePruning skips the WHOLE block in three cases (1837 to 1840): at a PV node, in check, when alpha is a
mate score. The comment gives the reason: a dropped move can hide a faster mate while the node still stores an
exact bound. The cost is measured (above). What the arms BUY is not measured by anyone: nobody has counted
how often a move that the block drops in one of the three cases would have beaten alpha, and whether that
happens more often there than at an ordinary node. If a case is no worse than the ordinary node, its arm
buys nothing and costs nodes. If one STEP in one CASE is much worse, the right repair is that step in that
case and not the whole block. That table (case by step) is the job.
One difference between your build and the PC's: the PC's build sets FORGE_MATE_ALPHA_GUARD and plays with
the option MateAlphaGuard on, so s2 and s5 (lines 1871 and 1896) are already skipped there when alpha is a
mate score (measured: that guard costs 3 % of the tree on whole-game positions, all of it in 14 of 400
searches). Your plain build has neither. So for the mate-score case say which regrets lie in s2 and s5
(repaired on the PC already) and which in the other four steps (what the mate-score arm would add).

### Part 1 (first, its own commit "kimi5 job 5 prediction", never edited): from the code only

Each with the range outside which you call your reading wrong:
(a) the tree factor of each arm ALONE against none at depth 12, on O and on G, on your tree;
(b) for the PV arm and for the mate-score arm: WHICH step (s1 to s6) carries most of its extra nodes on G;
(c) the "regret rate" (Part 3) of the ordinary case and of each of the three cases, all steps together, and
    the one (case, step) cell you expect to be worst;
(d) why does the mate-score arm change so few searches and then multiply a bare won ending? File and line
    for every condition that matters (1841 and 1842 hold several: has_material, bare_king_mode, mate_moves_).

### Part 2: the three arms as options (a text patch, `SoundArms.patch.txt`)

If `forge-combo29/tests_deepseek5_job15/SoundArms.patch.txt` is on deepseek5's branch when you start, read
it, apply it, and CHECK it with the known answers below: a colleague's patch that passes is a better use of
your minutes than a second one. If it is not there, or a known answer fails: write your own (three spins
`SoundPvArm`, `SoundInCheckArm`, `SoundMateAlphaArm`, -1 .. 1, default 0 = the arm follows the switch) and
say which line of the other one was wrong. Known answers from MY separately written version in your setup
(built-in net, every option at its default, set O, depth 12; nodes of positions 1 / 2 / 3, then the sum):
        K0  pins with no option: 312,866 / 862,329 / 4,865,609
        K1  no option                          18,407 / 25,756 / 64,000      12,573,318
        K2  SoundMatePruning true              17,203 / 25,551 / 62,628      12,558,811
        K3  SoundPvArm 1                       17,200 / 26,267 / 36,908      12,399,593
        K4  SoundInCheckArm 1                  18,410 / 41,328 / 42,607      12,326,599
        K5  SoundMateAlphaArm 1                18,407 / 25,756 / 64,000      12,573,482
        K6  SoundPvArm 1 + SoundInCheckArm 1   17,203 / 25,551 / 62,628      12,558,811
        K7  switch true, the three arms at -1  18,407 / 25,756 / 64,000      12,573,318
Then the tree factor of K2 to K5 against K1 on G at depth 12, each with its interval over positions
(resamples and seed named) and by piece class (27-32, 21-26, 15-20, 9-14, 3-8) with n.

### Part 3: the regret build (a SECOND text patch on top, `SoundRegret.patch.txt`; a statistics build)

With every arm OFF (the block prunes as the engine does today), count for each move the block drops:
  the CASE it was dropped in: ordinary (none of the three) / PV node / in check / alpha a mate score
        (a move can lie in more than one case: count it in each);
  the STEP that dropped it (s1 to s6; for s1 count the quiets that skip_quiets later removes, and say in the
        report exactly where you count them);
  REGRET: search the dropped move anyway, with the window (alpha, alpha + 1), at the depth the move loop
        would have given it after its reduction, and count it when the score is above alpha; count apart
        the regrets whose score is a mate score. The node then goes on as if the move had been dropped.
One line of counters per search before `bestmove`, the difference taken by the harness.
Known answers and rules of this build:
        R0  your own rule: every counter is shown NONZERO on one position before any table.
        R1  a build with the counters but WITHOUT the extra searches counts the same nodes as K1 on O,
            200 of 200. (The regret build itself is another tree, as in job 4: say so, use it for rates.)
        R2  in the counter-only build the drops per case add up: every drop is in "ordinary" or in at least
            one of the three cases, never in none.
        R3  with SoundMatePruning true the counter-only build shows 0 drops in the three cases.
The table, on O and on G at depth 12: 4 cases x 6 steps, each cell: drops, regrets per 1,000 drops, mate
regrets per 1,000 drops; and the same by piece class for the four cases (all steps together). The
"ordinary" row is worth having by itself: it says which of the six steps is most often wrong at a normal
node, on openings and on whole-game positions. Nobody has that number for this engine.

### Part 4: the narrow version (a THIRD text patch, `SoundSteps.patch.txt`), only what Part 3 supports

One spin `SoundStepMask`, 0 .. 63, default 63, bit 0 = s1 ... bit 5 = s6: in an arm's case only the steps
whose bit is set are skipped. Known answers: with the mask at 63, K2 to K6 again, node for node; with the
mask at 0 and the switch true: K1. Then ONE mask chosen from Part 3 by a rule you state before you look at
its tree (for instance: the steps whose regret rate in an arm's case is at least twice the ordinary
case's), and its tree factor against none on O and on G with the intervals, for the whole switch and for
the PV arm alone. If Part 3 shows no cell that is worse than the ordinary case, say so and write no mask:
"the arms buy nothing that this count can see" is a full answer.

### Part 5 (only if minute 32 has not passed when Part 4 is done)

Your job-4 find, as a fourth small text patch: the mate guard in the LmrDeeperShallower block (the rule
does not fire when best_score is a mate score), behind an option that is off by default, with the no-op
proof and the count of candidates it removes on O and G.

### The report's first three lines
(1) K0 to K7 and R0 to R3, each met or not, in numbers; whose arms patch you used. (2) Prediction against
measurement for (a) to (d). (3) The regret table in one sentence per case: is a dropped move there more
often a mistake than at an ordinary node, by what factor, and at which step; then the ONE setting (arms and
mask, spelled as the `uci` list spells them) that you would give to a match first, and why.

### What stops what
K0 or K1 failing ends the job. K2 to K7 failing ends Parts 2 and 4, not Part 3 (it needs no option). R0 or
R1 failing ends Part 3's table: repair first. The minute-40 mark ends the measuring, not the report.
Nothing else stops anything: decide, write it down, go on.

### At the end
The real output of `git status --short` and `ls` of your folder in the report; a table row says "done"
only when its file is in that `ls`. `NOTES_kimi5.md`: LEARNED / FOR deepseek5 (what it should test in your
patches: the positions and the known answers) / FOR glmflash5 (the match, ready to copy) / ANSWER. Then end
the run.
