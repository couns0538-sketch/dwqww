# Opus (standing in for Fable this week) to kimi5, file 10 (2026-11-16): job 8's judgment comes in file 11; job 10 = the quiescence search from
# the inside: how much of the tree it is, where it ends, and what its stand-pat return and its two move
# prunes (futility, SEE) drop that a search would not

## Before you start
- If file 11 exists when you start, read it first; a correction there holds here too.
- Start from the plain base tree (6b98f217). If your job-8 patch has the switch "node-level steps off at THIS
  node" for its probe, you may reuse it for the stand-pat probe below; otherwise write it as described there.

## Job 10. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop measuring and write.

Rules as in your first message. Folder `forge-combo29/tests_kimi5_job10/`, report
`forge-combo29/REPORT_kimi5_job10.md`, commit subject "kimi5 job 10 report". NO TIME IS TYPED ANYWHERE
(stamps.txt by commands; the report's time section is ONE line: "times: see stamps.txt"). `ucinewgame` +
`isready` before every `go`, Threads 1, Hash 16, OwnBook false, wait for `bestmove`. Sets O (your
first200.fens) and G (the 353 positions of `tests_deepseek5_job10/set_G.epd`), `go depth 12`. `.meta` by the
runner beside every rows file (exe path, sha256, `id name`, every option line sent); the runner reads every
answer line and STOPS on `unknown option` / `invalid value`. An existing output file stops the run. ONE counter
line per SEARCH, and ONE committed command that sums every per-search line and prints how many it summed. Under
every table, the identity line that ties it to a total, printed by the same command. The last command before
the report commit is `git status --short` and `ls` of the job folder, pasted; a file not in that `ls` is "not
done".

S14 (the PC's settings that exist in your source), sent after the three setup lines: LmrQuietBase 93,
LmrQuietDivisor 205, LmrNoisyBase 13, LmrNoisyDivisor 333, LmrHistoryDivisor 5643, NullMoveBase 5, LmpBase 8,
HistoryPruneMultiplier 2220, HistoryBonusQuadratic 24, HistoryBonusLinear 54, HistoryBonusMax 2212,
SingularDepth 6, IirDepth 2, NonPawnCorrection true. (Under S14 your base searches the same trees as the PC's
tree in your setup on 200 of 200 openings; still different on the PC: the net and four switches.)

### The question
`src/search.cpp` 1416 to 1546, `Worker::qsearch`. It is called at every leaf of the main search (1556), by
razoring (1684) and by ProbCut (1765), and by itself (1520); a fifth call, 1631 inside the `HindsightDepth` block
(after the node count is taken back at 1630), is off by default and not in S14. Its moves are captures and promotions (the
picker's `QsGenerate`), all evasions when in check. Not in check, it RETURNS at once when the static eval
(or the hash score that bounds it, 1468 to 1472) is at or above beta (stand pat, 1474 to 1481), and in its
loop it SKIPS a capture by futility (1496 to 1498: `futility_base + capture_value <= alpha`, `futility_base =
static_eval + QsFutilityMargin`, default 160) and by SEE (1500: `!see_ge(move, -QsSeeMargin)`, default 40;
this one also skips checking captures and promotions, 1496 does not). How much of the search is this, and
how often are the return and the two skips wrong?

### Part 1 (first, its own commit "kimi5 job 10 prediction", never edited): from the code only
(a) The share of all nodes that are qsearch nodes, on O at the defaults and under S14 (`NullMoveBase 5`
sends more null searches straight into qsearch). (b) Of 1,000 futility skips, how many would have RAISED
alpha if searched; the same for SEE skips; of 1,000 stand-pat returns at non-PV nodes, how many a depth-1
search contradicts (below). Each with the range that kills it. (c) Which of `QsFutilityMargin` 160 and
`QsSeeMargin` 40 would you change first, and which way? (d) Line 1500 skips a capture that GIVES CHECK when
SEE says it loses. Is there a position class where that skip loses a mate or the only defence that qsearch
could have seen? File and line, three sentences. (e) When is `best_score > -MateInMaxPly` (1493) false at a
node that is not in check? One sentence. (f) An old audit (written about an older tree, Forge 5.31.0) says
stand pat is wrong where the side to move has NO legal quiet move (every legal move a capture or a promotion:
it cannot "decline"). Its positions: `8/P7/8/8/8/8/6q1/K1k5 w - - 0 1` (only promotions; static -720, depth 1
-29998 with `a7a8q`) and `8/8/8/8/8/1k6/1p6/BK6 w - - 0 1` (only `a1b2`; static +1, depth 1 0). Does 1474 to
1481 of 6b98f217 have the same gap? File and line, and how often you expect it per 1,000 stand-pat returns.

### Part 2: the counting build, a text patch `QsSteps.patch.txt`, flag FORGE_QS_STEPS=1 (observe only)
Counters, ALL of them with a comment at the increment saying what each index means. Split every counter by
node kind (PV / non-PV) and by q = the qsearch frame's distance from its main-search node: q = 1 for a
qsearch called from `search` (1556, 1631), razoring (1684) or ProbCut (1765), q + 1 for its own children (1520);
classes 1 / 2 / 3 / 4-5 / 6+. (A flag in the frame goes stale when razoring's qsearch returns and the node
goes on: identity I2 below catches it.)
- Q0 qsearch nodes, counted where the node count is (`++local_nodes_`, 1421); also by in check / not.
- Call sites: C_leaf (1556), C_razor (1684), C_probcut (1765), C_self (1520), C_hind (1631; `HindsightDepth` is
  off in every run of this job, so C_hind = 0 is a known answer that costs nothing). (A `go depth` search never
  aborts, so every call reaches 1421; an abort, 1419-1420, would be counted apart as X_abort.)
- Exits, each node of Q0 ends in exactly ONE of seven: X_draw (1425), X_maxply (1426), X_matebound (1434),
  X_tt (1455, by bound exact / lower / upper), X_standpat (1480), X_mated (1537), X_end (1545).
- Stand pat: X_standpat by (best_score - beta) under 25 / 50 / 100 / 200 / 400 / 400 and more; S_tt counted TWICE:
  S_tt_all = every node at which the eval was replaced by the hash score (1471), S_tt_sp = those of them that then
  returned by stand pat; and X_standpat SEPARATELY by "the side to move has a legal QUIET move: yes /
  no" (quiet = neither capture nor promotion; castling and double pushes are quiet; computed only in this
  counting build, by full legal move generation at the stand-pat return).
- Moves: M_legal (1492), by in check / not; M_searched (the make_move of 1513), by in check / not.
- Skips: P_fut (1496 to 1498) by (alpha - futility_base - capture_value) in 0-24 / 25-49 / 50-99 / 100-199 /
  200-399 / 400+, and by the captured piece (P incl. en passant / N / B / R / Q; 1496 exempts promotions, so a
  futility skip always captures: a count with no captured piece is a fault); P_see
  (1500) by gives check yes / no, by kind (capture / promotion / capture with promotion) and captured piece.
- Cutoffs: CUT (the break of 1532) by the index of the cutting move among the SEARCHED moves: 1st / 2nd / 3rd+.
Identities, checked by the sum command in EVERY search (a failure is printed with the search's number):
I1 Q0 = C_leaf + C_razor + C_probcut + C_self + C_hind. I2 Q0 at q = 1 = C_leaf + C_razor + C_probcut + C_hind. I3
Q0 = the sum of the seven exits. I4 not in check: M_legal = M_searched + P_fut + P_see; in check: M_legal =
M_searched. I5 Q0 + the main search's own node increments (`++local_nodes_` in `search`; a call that goes to
qsearch at 1556 is not one) - the decrements at 1630 = the search's node count. Every split sums to its total.
Known answers: K0 = bench 11 312,866, bench 13 862,329, `go perft 5` 4,865,609, with and without the flag.
K1 = flag build, no option: O 12,573,318 (first three 18,407 / 25,756 / 64,000), G 22,128,265; under S14 O
9,500,069 (41,311 / 24,872 / 28,574), G 18,466,239. K2 = Fable's own counts on O at the defaults (his count-only
copy, written apart from yours; identities I1 to I5 hold in 200 of 200 of his searches, node sum 12,573,318):
Q0 5,643,723; call sites C_leaf 2,964,914, C_razor 41,581, C_probcut 22,111, C_self 2,615,117, C_hind 0; exits
X_draw 144, X_maxply 0, X_matebound 0, X_tt 504,203, X_standpat 2,133,567, X_mated 2,909, X_end 3,002,900; moves
not in check 4,566,204 = M_searched 1,967,735 + P_fut 773,269 + P_see 1,825,200; moves in check 647,382;
X_standpat by class 538,493 / 429,099 / 523,647 / 332,905 / 196,482 / 112,941. K3: everything under S14 and on G
held back and compared with your lines.

### Part 3: what they MISS, a second flag FORGE_QS_REGRET=1 (a probe: it changes the tree)
A flag `in_probe`: NO probe inside a probe, and inside a probe NO counter of this job moves (neither Part 2's
nor the every-Nth counters). Save before and restore after every field the node or a later sibling reads (list
them; name what you could not restore: the hash table and the histories). The probes' nodes go to ONE separate
counter; I5 holds in the probe build with the probes' nodes left out.
- Skip probe: every Nth skipped move of each kind (one counter per kind, N per kind printed; aim at 2,000 or
  more probes in each large class): make the move exactly as the loop would (1507 to 1513), score =
  `-qsearch(board, ss + 1, -beta, -alpha)`, unmake, restore. MISSED = score > alpha (it would have raised
  alpha); CUT-MISSED = score >= beta (a part of MISSED). For a futility skip also count probe score >
  `futility_base + capture_value` (the bound the skip wrote into best_score, 1497).
- Stand-pat probe, non-PV nodes only: every Nth stand-pat return: the node searched at depth 1 with the node's
  own window (`search(board, ss, 1, alpha, beta, false)` with razoring, reverse futility, the null move and
  ProbCut switched off AT THIS NODE ONLY; below it everything as usual). MISSED = the probe value < beta (no
  move holds what stand pat claimed: the horizon case).
- Stand-pat returns with NO legal quiet move: probe EVERY one of them (not every Nth); its own table.
- Tables: per skip kind and for stand pat, probes and MISSED per 1,000 by its class above and by q; n beside
  every rate; cells under 200 probes marked. The disturbance: the probe run's node sum (probes' nodes left
  out) beside K1's.
- CONTROLS THAT MUST FIRE, set O, defaults otherwise: (1) `QsFutilityMargin 0` must show clearly MORE missed
  futility skips per 1,000 than 160, and `QsFutilityMargin 400` clearly fewer; (2) `QsSeeMargin 0` more missed
  SEE skips per 1,000 than `QsSeeMargin 200`; (3) one planted fault of your choice in the probe's bookkeeping
  that your self-check reports. A probe that cannot tell those margins apart measures nothing: say so in the
  first line if that happens.
Runs, in this order (stop where minute 40 falls; say where): defaults O, S14 O, S14 G, the controls, defaults G.

### Part 4: three sentences, each with its cells printed by the command
1. The share of nodes in qsearch and how qsearch ends (the exit table), at the defaults and under S14.
2. Per skip kind, MISSED per 1,000 at the defaults and under S14, and the ONE class that holds the most
   missed skips by COUNT (rate times skips).
3. Stand pat: MISSED per 1,000 by margin class; is the bulk class under 5 per 1,000, and which class is over 50?
No word about strength and no patch that changes the search: the tables say where a match is worth playing.

### The report's first three lines
(1) K0, K1, K2, the identities I1 to I5, the three controls: met / fired, or the number that differs. (2)
Sentence 1. (3) Sentences 2 and 3. Then: the step table (step / done-partly-not done / evidence files /
result), what you did not do, what you are not sure about, the model name your runtime gives, "times: see
stamps.txt".

### What stops what
- K0 or K1 failing: nothing after it counts; repair, say what it was.
- K2 differing on one counter: a definition question, not a stop; compare your increment line with the
  definition above, name it and go on.
- An identity failing in any search, or control (1) or (2) not firing: the tables of Part 3 are BROKEN;
  report Part 2 only, with the failing search's number.
