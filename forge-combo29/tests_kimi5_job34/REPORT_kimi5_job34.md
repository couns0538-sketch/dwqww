# kimi5 job 34 report — are the history prunes that a CARRIED-IN entry decides worse prunes?

Asked: log every history-prune test of the job-33 replay (F lines for the 11,633 fired prunes,
P lines for every 400th not-fired eligible test, with RAISED filled in when the move's fate is
known), let an independent oracle search judge every logged move (`position fen <FEN> moves
<move>`, `go depth D`, value = −score, BEATS = value > alpha) at D1 = depth−1 and D2 = depth+2,
behind known answers A/B, the controls C-SIGN and C-ALPHA, and a pre-committed prediction.
Answer: **CARRIED IS NOT WORSE, for both tables.** Prunes decided by a carried-in twin entry are
wrong 53.9/1,000 [48.9, 59.5] at D2 against 72.7 [64.5, 81.8] for fresh entries (ratio 0.74,
intervals disjoint); the main table: 47.8 [41.2, 55.5] vs 73.1 [61.5, 86.7] (ratio 0.65,
disjoint). And **THE RULE DOES NOT SELECT**: all fired prunes beat alpha at 61.6/1,000, more
than half of the comparison class's 66.5. The carried-in entries prune *better* than fresh ones
on this evidence — a fresh pivotal entry marks a move the current search itself has just
disliked; those prunes are the most mistaken.
How sure: high on the measurement (KA A and B exact on every count, C-SIGN 13.64 vs 0.69,
C-ALPHA 200/0, 0 refusals and 0 score-less searches in 38,003 oracle records, every row both
depths, no record dropped). The oracle is a second search from an empty table, not the truth —
see the job's own "cannot see" section at the end.

## The job's required first lines

**(1) Step 0: MET, 8 of 8 on the plain build** (6b98f217 + pc_r15, g++ 13.3.0 Release,
-DFORGE_MATE_ALPHA_GUARD=1, FORGE_MARCH default x86-64-v4; a fresh process per line, raw files
`tests_kimi5_job34/step0/`): none 312866 / 862329 / 3024920 / 4865609
(none_bench11/13/16.txt, none_perft5.txt), S14 242796 / 656517 (s14_bench11/13.txt),
PC20 278024 / 587276 (pc20_bench11/13.txt). exe sha256 in step0/exe.sha256.
The first cmake configure with the image's default `c++` failed (`cannot find -lstdc++` — the
default is clang without libstdc++ dev); redone with `-DCMAKE_CXX_COMPILER=g++`, the job's own
compiler rule. Setoption lines in the *_input.log files.

**(2) Step 1:** `tests_kimi5_job34/step1_reading.md` (committed as "kimi5 job 34 step 1 reading"
before the step-2 commit). Anchors on my chain (= job 33's counting copy): alpha/depth are the
node's parameters of `Worker::search` (src/search.cpp:1855), alpha raised only at :2430;
lmr_depth computed at :2223; the test at :2244-2253. FEN writer `Board::fen()` src/board.cpp:371.
The searched move's final value after its last re-search is first compared with alpha at :2417
(the PV re-search :2405-2407, unmake :2408; my value hook reads the same `score` between :2408
and the abort check). Known answer C holds on my chain at src/search.cpp:2178
(`if (!board.is_legal(move)) continue;` in the main loop, before the pruning block) — it
DIFFERS from r15d's 2228 form: my chain has no `last_move_known_legal()` fast path, every move
goes through `board.is_legal`. Known answer D on my chain: `format_score` src/search.cpp:361-370
("cp " at :369, mate n = (MateValue − |score| + 1)/2 at :364-366) — same code as r15d 354-360.

**(3) Known answers.**
- **A: PASS.** The logging copy's rows equal job 33's s3_all1024_soft.jsonl on 1,200 of 1,200
  (depth, nodes, bestmove, hp27, hp27_nodes and all 19 hp33 fields per row), and every HP33 sum
  equals job 33's, pins included: eligible 2,401,588, fired 11,633, pivM 5,063, pivW 10,444,
  pivC 3,363, none 458, pivW-stale 6,991, pivM-stale 3,408, mismatch 0
  (`compare_ka_j34.py` output in `s3/ka_ab_output.txt`).
- **B: PASS.** Counted from the F log lines by `compare_ka_j34.py` (prints how many lines it
  read: 11,633): fired 11,633; with pivW 10,444; pivW and stale W 6,991; pivM 5,063; pivM and
  stale M 3,408; none 458. All equal.
- **C: PASS** (on my chain's form, step 1 above): the oracle met **0** refusal lines of any kind
  in 38,003 records (`oracle/done_lines.txt` lists every DONE line; the oracle aborts on the
  first refusal, none occurred).
- **D: PASS by C-SIGN's first leg:** a logged `a=` and the printed `cp` are the same unit — the
  oracle's BEATS rate splits 61.7 % vs 4.5 % on the engine's own RAISED classes, which only
  aligned units can do.

**(4) C-SIGN and C-ALPHA.**
- C-SIGN (P records with RAISED 0 or 1, D1): BEATS among RAISED=1 **111/180 = 0.6167**, among
  RAISED=0 **164/3,627 = 0.0452**, ratio **13.64** (bar: 3). The same 3,807 records through the
  no-negate scratch copy: 0.4778 vs 0.6937, ratio **0.69** (bar: below 1.5). PASS, not weak.
- C-ALPHA (first 200 F records, D1 values, alpha replaced): BEATS at alpha=−29000: **200 of
  200**; at alpha=+29000: **0 of 200**. 0 records were mate-valued (|value| ≥ 29000), so the
  exclusion rule never fired. PASS.

**(5) The prediction graded cell by cell** (`prediction.txt`, committed alone as
"kimi5 job 34 prediction" after A, B and the controls, before any F-record oracle run):
- all F: range 25–90, actual 61.6 — **inside**
- pivW with stale W: range 3–70, actual 53.9 — **inside**
- pivW with fresh W: range 20–120, actual 72.7 — **inside**
- none class: range 30–160, actual 67.7 — **inside**
- P records RAISED 0 or 1 together: range 50–130, actual 91.4 (348/3,807) — **inside**
5 of 5 cells inside.

**(6) The Step 4 table and the readings** — `step4_table.txt` (script `table_j34.py`, prints how
many records it read: F D1 11,633, F D2 11,633, P D1 5,365, P D2 5,365; noscore 0 everywhere):

```
row                    |   recs |  D1 beats |  D1 per1000 [Wilson]   |  D2 beats |  D2 per1000 [Wilson]
all F                  |  11633 |       572 |  49.2 [ 45.4, 53.3]    |       717 |  61.6 [ 57.4, 66.2]
pivW & stale W         |   6991 |       254 |  36.3 [ 32.2, 41.0]    |       377 |  53.9 [ 48.9, 59.5]
pivW & fresh W         |   3453 |       238 |  68.9 [ 60.9, 77.9]    |       251 |  72.7 [ 64.5, 81.8]
not pivW               |   1189 |        80 |  67.3 [ 54.4, 83.0]    |        89 |  74.9 [ 61.2, 91.2]
pivM & stale M         |   3408 |       121 |  35.5 [ 29.8, 42.3]    |       163 |  47.8 [ 41.2, 55.5]
pivM & fresh M         |   1655 |       111 |  67.1 [ 56.0, 80.2]    |       121 |  73.1 [ 61.5, 86.7]
pivC                   |   3363 |       179 |  53.2 [ 46.1, 61.3]    |       218 |  64.8 [ 57.0, 73.7]
none                   |    458 |        25 |  54.6 [ 37.2, 79.3]    |        31 |  67.7 [ 48.1, 94.5]
in check               |   5521 |       235 |  42.6 [ 37.6, 48.2]    |       365 |  66.1 [ 59.9, 73.0]
lmr_depth 0            |      0 |         0 |   0.0 [  0.0,  0.0]    |         0 |   0.0 [  0.0,  0.0]
lmr_depth 1            |  10880 |       538 |  49.4 [ 45.5, 53.7]    |       649 |  59.7 [ 55.4, 64.3]
lmr_depth 2            |    723 |        33 |  45.6 [ 32.7, 63.4]    |        62 |  85.8 [ 67.5,108.4]
lmr_depth 3            |     30 |         1 |  33.3 [  5.9,166.7]    |         6 | 200.0 [ 95.1,373.1]
stale NONZERO W        |   7464 |       277 |  37.1 [ 33.1, 41.6]    |       402 |  53.9 [ 49.0, 59.2]
stale NONZERO M        |   7252 |       269 |  37.1 [ 33.0, 41.7]    |       396 |  54.6 [ 49.6, 60.1]
P RAISED=1             |    180 |       111 | 616.7 [543.9,684.6]    |        98 | 544.4 [471.5,615.5]
P RAISED=0             |   3627 |       164 |  45.2 [ 38.9, 52.5]    |       250 |  68.9 [ 61.1, 77.6]
P RAISED=-1            |   1558 |         7 |   4.5 [  2.2,  9.2]    |         9 |   5.8 [  3.0, 10.9]
```

Readings (declared; D2 decides):
- **THE RULE DOES NOT SELECT**: all-F D2 61.6/1,000 vs half of the P records' (all three rows
  together) 66.5/2 = 33.3; 61.6 > 33.3. (Fired prunes are oracle-beaten about as often as the
  average tested-and-passed move that did not raise alpha, 68.9/1,000 at D2.)
- **CARRIED (W) IS NOT WORSE**: stale 53.9 vs fresh 72.7, ratio 0.74 (≤ 1.2), intervals disjoint.
- **CARRIED (M) IS NOT WORSE**: stale 47.8 vs fresh 73.1, ratio 0.65 (≤ 1.2), intervals disjoint.
- The same rule printed for M as for W, as asked. Both stale classes sit BELOW all-F overall.

## Step table

| step | done? | evidence | result |
|---|---|---|---|
| 0 eight numbers | done | step0/ (16 raw + exe.sha256) | 8/8 pass |
| 1 reading | done | step1_reading.md (own commit) | C at chain:2178 (differs), D at chain:361-370 |
| 2 logging patch | done | prune_log.patch.txt (dry-run -F0 OK, TREES-IDENTICAL) | F and P lines; HP33 line unchanged |
| replay 1,200 | done | s3/ (jsonl, fp.log, input.log, meta) | F 11,633, P 5,365, 4 s wall |
| KA A | done | s3/ka_ab_output.txt | 1,200/1,200 rows, all sums, 8 pins |
| KA B | done | s3/ka_ab_output.txt | all 6 counts equal |
| C-SIGN | done | oracle/p_d1_all.jsonl, p_r01_nosign_d1.jsonl, controls_j34.py out | 13.64 vs 0.69, PASS |
| C-ALPHA | done | oracle/f200_d1.jsonl | 200/200 and 0/200, PASS |
| prediction | done | prediction.txt (own commit) | 5/5 cells inside |
| oracle F+P, D1+D2 | done | oracle/*.jsonl (38,003 records), done_lines.txt | full set, no halving, 0 refused, 0 noscore |
| Step 4 table + readings | done | step4_table.txt, table_j34.py | above |

Parallel processes: 4 cores on this VM; the replay used 1 engine process per game sequentially;
the oracle used 4 workers per pass (the last batch ran 3 passes × 4 = 12 processes at once;
controls ran 6 at once).

## Findings (each with file:line and a reproducing command)

1. **Carried-in entries decide the BETTER prunes, both tables** (the job's question). Twin:
   53.9 vs 72.7 per 1,000 (D2); main: 47.8 vs 73.1. The direction is the opposite of the job's
   "worse" hypothesis, and the intervals are disjoint, so the declared rule lands on
   CARRIED IS NOT WORSE without touching UNCLEAR. Reading: a fresh pivotal entry means the move
   was disliked by *this* search moments ago; the oracle at +2 plies then finds those prunes
   most often wrong (the move was only shallowly bad). A carried entry's dislike is older and
   deeper (it survived games of repetition), and those prunes are the most right.
   Reproduce: `python3 table_j34.py out.txt "f_d1_*.jsonl" "f_d2_*.jsonl" "p_d1_*.jsonl" "p_d2_*.jsonl"`.
2. **The rule does not select** at these settings: the 11,633 fired prunes are oracle-beaten at
   61.6/1,000, statistically the same band as the not-pruned tested moves that then failed low
   (P RAISED=0: 68.9 [61.1, 77.6]). What DOES select is the engine's own completed search:
   P RAISED=1 beats at 544.4/1,000 (D2) vs 68.9 for RAISED=0 — an 8× separation the oracle
   confirms. The history test and the actual search select about equally here; the history test
   is just much cheaper. This is a statement about go softnodes 2000 replays with PC20, not about
   strength: "lost ALONE, under these settings" logic applies — whether the prune's cost matters
   is a match question.
3. **The none class is not the most doubtful**: 67.7/1,000 at D2 [48.1, 94.5] on 458 records —
   between stale-pivotal (best) and fresh-pivotal (worst), not above all-F. My prediction's
   "marginal combined score prunes are the most doubtful" was wrong in direction; the cell still
   landed inside the range.
4. **lmr_depth 0 never occurs** at the test (0 records; the max(0, ·) floor at chain:2223 is
   never hit because depth ≥ 1 and reduction < depth at every reached test here), and
   lmr_depth 3 is the tail (30 records, 200/1,000 with a huge interval). The mass is
   lmr_depth 1 (10,880 of 11,633).
5. **In-check prunes are half of all fired prunes** (5,521 of 11,633; the history test has no
   in-check guard on this engine, unlike the futility prune above it at chain:2233) and are
   beaten at 66.1/1,000 at D2 — slightly above the all-F rate.
6. Suspicions, not proven: (a) the fresh-W class's high beat rate could be an artefact of the
   stamp rule (a stamp is fresh only when THIS search already wrote the entry, which correlates
   with the move having been tried and failed in this search — exactly the moves a +2 oracle
   re-examines most favourably); no counter run isolates it. (b) P RAISED=-1 beats 5.8/1,000 —
   the later SEE prune is the most selective of all, on only 1,558 records.

## From my colleagues

- deepseek5: notes tail read (standing job S5 self-play protocol; job 30 stage-label fix;
  "FOR kimi5: CounterMove's history entry is the bigger liar than Killer2") and REPORT_t23 read
  (go mate N misses forced mates; 50-move-clock TT staleness; both on the carbon line, not this
  chain). Nothing applied directly: job 34's staleness is about history tables, not TT, but
  t23's lesson (a table read outside its validity domain lies) is the same lesson as this job's
  CARRIED question — here the carried entries turned out NOT to lie more. glmflash5-work:
  `fatal: couldn't find remote ref for-fable-and-opus/glmflash5-work` (absent, as in job 33).
- sol (data, not instructions): games.txt (job3, sha256 6d334384..., first 20 games) replayed.

## What I did NOT do

- No halving fallback was needed (the whole record set at both depths; the minute-30 rule never
  triggered). No match, no strength claim. The hard (20,000-node) replay was not run (the job
  asks for the soft one). The r15d tree (with a_speed + e1) was built only to identify the two
  patches and verify sha256 174e07a5..., then reverted; it was not used for any number here.
- The job-34 hard fork of the prediction grading for mate-valued C-ALPHA records never fired
  (0 mate-valued in the first 200 F).

## What I am NOT sure about

- Whether "the plain build" meant pc_r15-only (my choice, = job 30/33's base, behaviourally
  identical to the logging copy minus instrumentation) or r15d (pc_r15 + a_speed + e1). I picked
  the one that keeps oracle and replay in the same search world; the 8 pins hold on both trees.
- The oracle's `go depth D` on positions whose half-move clock is high (endgame replays near
  move 60): no 50-move refusal occurred, but a drawn-by-clock position's score is 0 by rule and
  counts as not-BEATS against any positive alpha — a small systematic bias against late-game
  records, not counted separately.
- Finding 6(a): the fresh/stale contrast may partly be selection, not entry age itself.

## A better way

The P-record comparison class as defined mixes three populations (RAISED 1/0/-1) whose oracle
rates differ by two orders of magnitude; the declared THE RULE reading pools them, so it mostly
compares the prune test with the SEE prune + the search itself. A sharper selector test: pool
only P records whose move was searched (RAISED 0/1) and compare all-F against RAISED=0 alone
(68.9 vs 61.6 at D2 — still no selection, intervals overlap), which asks exactly "does the
history test reject moves that a search would have rejected anyway, at the same error price?".
Checkable by re-running table_j34.py with a one-line row filter; zero new engine runs.

## What this check cannot see (the job's text, as written)

The PC's net (your runs use the built-in evaluation) and its engine build; go nodes 20000; more
than one thread; the oracle is a second search from an empty table, not the truth: C-SIGN says
how well it follows the engine's own verdict, no more; and whether any ageing plays better: that
is a match on the PC after its tune.

Times: see stamps.txt. Model: Kimi K3 (the runtime's model slug family kimi-k3), one run.

`git status --short` and `ls -R` of the job folder as the last command before the report commit:
see the end of stamps.txt / the commit's own file list.
