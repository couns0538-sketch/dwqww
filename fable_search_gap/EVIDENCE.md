# EVIDENCE: what was observed, and what it does and does not support

Terms are explained in `NO_QUALIFIED_GAP.md` section 9. This file was corrected after the review; `REVIEW_LOG.md` lists what changed.

## Key points

- **The gate record shows no failure that points to an unowned search mechanism.** Of 126 gate rows, 80 were capped without a decision. The decided rows are about owned candidates, weak nets, time losses, a changed book and thread count, and old baselines.
- **Six in ten gate games end by threefold repetition** (54,667 logged games). The mechanisms that target repetition are all owned already.
- **Time losses are new and concentrated.** All 70 sit in 8 rows, 67 of them in seven rows recorded on 2026-11-07 to 2026-11-09. Their logs are missing, so the cause is UNVERIFIED.
- **The one unowned mechanism was measured in a replica search on the lock's own board and evaluation code.** A cutoff is already available from a child entry at about 4 % of eligible middlegame nodes and at 8 to 17 % of eligible endgame nodes, depending on the position set.
- **Taking that cutoff gave no node saving that can be told from zero, or from a placebo.** On 91 distinct positions the node ratio is 0.92 to 0.95 with a range that includes 1.00. A change that is no mechanism at all (one history constant moved by 1) gives 0.98 with the same kind of range, changes as many best moves, and swings single positions as far.
- **A second, larger set gave the same answer.** On 336 positions from 48 independent openings, read by a rule committed before the run, the result is "not shown either way": node ratio 0.987, range by opening [0.954, 1.022]. In this replica a saving above about 5 % is ruled out on such positions.
- **The lookups cost a few percent of time, the same order as the possible saving.** This machine is loaded. The comparison could not be settled here, in either direction.
- **On the classic pawn-ending test position, three of eight settings of the mechanism play the drawing move at some depth.** The plain replica never does, also not under ten placebo-size changes. Under those changes the mechanism's settings miss the winning move at some depth in 31 of 80 runs; rule cut6 never does, and by depth 40 all but 3 runs have found it again. This is one position. Why it happens is not established.
- **The rule fixed before the deciding run was read gives NO QUALIFIED GAP.** The honest reading is "not shown", not "refuted".

Nothing in this file is an Elo claim. "Observed" means I ran it or read it in a file I name. "Hypothesis" means I did not.

## 1. Observed and hypothesis, side by side

| Statement | Status | Where |
|---|---|---|
| The lock exe reproduces its twelve pins on CPU 3-6 | observed | `data/pins_combo29.json` |
| 80 of 126 gate rows are capped with no decision | observed | `data/gate_table_summary.md` |
| 59.9 % of 54,667 logged gate games end by threefold repetition | observed | `data/gate_log_terminations.tsv` |
| All 70 recorded time losses are in 8 rows | observed | `data/gate_table_summary.md` |
| The time losses come from host load, not from the engine | hypothesis | logs missing |
| The lock never reads a child's table entry | observed | lock `src/search.cpp` 1165-1170, 1379-1383, 1066-1070 |
| In the replica, a child entry already proves the cutoff at 3.9 to 4.7 % of eligible middlegame nodes and 17.1 to 19.5 % of eligible endgame nodes | observed | `data/etc_probe_wide_summary.md` |
| In the replica, taking that cutoff changes the node count by a factor of 0.92 to 0.95, with a 95 % range that includes 1.00 | observed | same |
| In the replica, a placebo change moves node counts and best moves about as much | observed | `data/etc_probe_wide_variants_summary.md`, `data/etc_probe_supp_summary.md` |
| On 336 positions from 48 independent openings the node ratio is 0.987 with range [0.954, 1.022] | observed | `data/etc_probe_supp_summary.md` |
| The lookups cost more time than the cutoffs save, or less | not resolved | section 5.6 |
| The same numbers hold inside the real lock search | hypothesis | needs an instrumented build |
| The mechanism is worth any Elo | not claimed | - |

## 2. Failure analysis of the gate table

Source: `C:\Users\Administrator\grok-pc\forge_push\FORGE_RESULTS.csv` (126 rows, sha256 `17c8bde8fbb40680...`), summarised by `tools/gate_table_summary.py`.

| Verdict class | Rows |
|---|---|
| Capped, no decision | 80 |
| H0 accepted | 18 |
| H1 accepted | 14 |
| NOT CLEAN (time losses) | 8 |
| H0 early stop (nets) | 4 |
| H1 non-regression | 1 |
| Trial only | 1 |

Each cause below is separated from "real search defect".

**Noise and low power: the main cause.** 56 of the 77 option-line rows are capped. The crew's own arithmetic says a 3,000-game run resolves about ±5.9 Elo and that singles worth +1 to +4 end "UNPROVEN at the cap by construction" (`opus-deepres-20261104@2231439c:opus_deepres/notes/RANKING_FINAL.md:32-35`). Repeats show the spread directly:

| Candidate | First run | Repeat | Note |
|---|---|---|---|
| net `f006` | +29.44 Elo, 698 games, H1 | +7.18, 1,500 games, capped | same exe |
| `EvalOptimism=40` | +6.95, 3,000 games, capped | -5.30, 2,360 games, H0 | same exe and option |
| `BundlePreset=B1` | +11.25, 2,100 games, H1 | +8.34, 3,000 games, capped | same exe and option |
| net file `o30...soupU8` | +16.50, 2,528 games, H1 | +3.04, 4,000 games, capped | **not a pure repeat**: the two runs had different bases |

A single capped result, and even a single H1, says little about the size of a mechanism.

**Option lines that were measured and lost.** Ten option-line rows are H0. Those candidates were tested and were not better. Every one of them is an owned candidate, so these rows say nothing about an unowned mechanism.

**Net strength, not search.** Six net-file rows are H0 at -86 to -116 Elo and three more are NOT CLEAN at -96 to -124. The four early stops are net builds too. These are about the net.

**Time control, threads and book.** Fifteen rows name the UHO book, most with the note that it is "NOT poolable" with the older book. The manifest entry of the newest such gate (`uhoB70_packanpc_w50_vs_AL1lp` in `...\forge_push\autorestart\forge_gates.json`) says `threads = 2`, `concurrency = 4`. Of the 51 surviving logs, 50 carry the setup line "10+0.1, 1t, 16MB, 8moves_v3"; the log of `gate1` (18 games) has an empty setup field. Rows from the two regimes cannot be compared.

**Crashes and time losses.** Zero crashes. 70 time losses in 8 rows:

| Gate | Candidate exe | Games | Time losses | Recorded |
|---|---|---|---|---|
| R5A-2 | `forge_r5a_singles_ee83d6d.exe` | 3,000 | 3 | 2026-10-30 23:28 |
| CAN1 | `..._caN_nmpcutoff_al1_2b8dcb5c.exe` | 1,316 | 6 | 2026-11-07 16:33 |
| UT1 | same exe as CAN1 | 498 | 6 | 2026-11-08 21:35 |
| NPTW4S5-B07 | `..._r10fix1_halfka_9e5cb644.exe` | 256 | 1 | 2026-11-08 22:10 |
| NPTW4S5-FIN | same exe | 286 | 15 | 2026-11-08 22:50 |
| NPTW4S6-FIN | same exe | 242 | 5 | 2026-11-08 23:23 |
| UB69 | `..._b69bundleB1_al1_a0d0eca9.exe` | 748 | 12 | 2026-11-09 01:08 |
| UB70W50 | `..._b70packanpc_al1_e7cea33f.exe` | 746 | 22 | 2026-11-09 16:55 |

- The 51 older logs (54,667 games) contain no time loss at all.
- UB70W50 lost 22 of 746 games on time and was read as H0 at -24 Elo. If the candidate was the side that forfeited, the forfeits alone account for about 10 to 20 of those 24 Elo (10 if the lost games would otherwise have been drawn on average, 20 if they would have been won). I could not check which side forfeited, because those logs are missing.
- These verdicts should not be read as evidence about the search.
- Whether an engine overruns its clock under load is open. The lock source checks the clock every 1,024 nodes (`search.cpp:992`, `:1125`, `:891-902`). That is a statement about the lock's code only. The forfeits happened in games of candidate exes that I did not read, and three of the rows (21 time losses) ran an exe with a different net type.
- I found no PGN in the mirrored gate folders. The crew's throughput notes mention gates timed from PGNs, so PGNs may exist somewhere I did not look.

**Paired-game imbalance.** The pentanomial counts are recorded for every row. I found no row whose verdict depends on an imbalance, and did not analyse this further.

**Obsolete baselines.** By the base column the base changed six times: 7 rows against `ep10`, 62 against `h256_e12`, 16 against the AL1 net lock, 23 against its LTO build, 8 against trial_w6, 6 labelled combo29, 4 against job-local bases. Half the table is measured against a base two net generations old. **The base column is not reliable.** It disagrees with the gate tag in 17 rows. Twelve rows tagged `vs_h256e12` have base column AUTOLOCK_1 (gates 55, 56, 98, 103, 105, 106, 107, 109, 111, 112, 122, 123). Five rows tagged `vs_AL1` or `vs_AL1lp` have base column combo29 (the three NPTW rows, UB69, UB70W50). The counts above are therefore approximate.

Two things follow that are not new mechanisms but matter for reading the record:

- The search bundle `BundlePreset=B4` is H1 twice against `h256_e12` (+14.08 and +11.05 Elo). I found no result for it against any later base. (UB69 is a port of bundle B1, and UB70W50 is a different pack; both are NOT CLEAN.)
- For UB70W50 the manifest entry names the older LTO lock exe as `base_override`, while the table says combo29. Which exe played is UNVERIFIED.

**Real search defects in the record.** The only ones I found are already owned: the two lock bugs fixed by today's live candidate `t12b`.

## 3. What the game endings say

`tools/gate_log_miner.py` over the 51 surviving logs in `D:\grok-pc-data\forge_push` (no adjudication):

| Ending | Games | Share |
|---|---|---|
| Threefold repetition | 32,723 | 59.9 % |
| Checkmate | 14,351 | 26.3 % |
| Fifty-move rule | 3,780 | 6.9 % |
| Insufficient material | 3,716 | 6.8 % |
| Stalemate | 97 | 0.2 % |
| Time loss, illegal move, disconnect | 0 | 0 % |

Draws are 73.7 % of games and 81.2 % of draws are repetitions. Without PGNs I cannot tell how many repetitions came from better positions, or how the clock is spent between middlegame and endgame. The mechanisms aimed at repetition are owned: the upcoming-repetition test, the twofold rule by node type and the draw-score jitter (`DEDUPE.md` rows 1 to 3). So this is a reason to gate owned work, not a gap.

## 4. The lock code the candidate concerns

- A node takes a table cutoff only from **its own** entry: `search.cpp:1165-1170` (non-PV, no excluded move, depth sufficient, rule-50 below 90, bound in the right direction).
- A child's key is computed before the move is made, but only to prefetch the child's table cluster: `search.cpp:1379-1383` in `search`, `1066-1070` in `qsearch`.
- No line reads a child's entry.

So when a node has no usable entry of its own, but one of its moves leads to a position whose stored upper bound already refutes the node, the lock does not know. It searches its moves in order until one of them reaches that position, or another move cuts first.

## 5. Replica measurement

### 5.1 What was built

`tools/etc_probe/etc_probe.cpp` is an original fixed-depth search written for this measurement: principal-variation search, a table with the lock's cluster shape, null move, reverse futility, late-move reductions and pruning, the check extension, and a quiescence search. It links the unmodified lock files `bitboard.cpp`, `board.cpp`, `eval.cpp`, `eval_params.cpp` (hashes in `data/lock_source_hashes.tsv`) and uses the lock's move generator, keys, `key_after`, SEE, repetition test and hand-crafted evaluation. It does not contain or link the lock's `search.cpp`.

**What it lacks compared with the lock.** Singular extensions, multi-cut, ProbCut, razoring, continuation, capture and correction history, the counter move and the net. Whether its move ordering makes the mechanism look better or worse than it would in the lock is not known.

**Known limits of the harness.**

- At a node with an en-passant square, `key_after` gives no key, so the harness looks up no child there. Opportunities after double pawn pushes are under-counted.
- It is built at `-O2` without profile-guided optimisation and without the net. The lock is built differently and spends most of its time in the net. The lookup cost as a share of time may not transfer.
- Rule item 2 ("the plain search also fails high") is close to true by construction in this replica, because the plain search meets the same child entry when it reaches that move.

**Build.** Compiler `C:\opus_5h\...\llvm-mingw-20261104-ucrt-x86_64\bin\clang++.exe`, sha256 `d05fee2c...`, the same binary Engine QA's receipt names for the lock. Flags in `tools/etc_probe/build_and_run.ps1`. Three builds of the harness were used, and each later one reproduces the earlier node counts exactly where they overlap:

| Harness exe sha256 | Used for | What changed |
|---|---|---|
| `f0409ac2...` | the first runs and the three timing repeats | - |
| `775b9b62...` | placebo, variants, supplementary run | adds the placebo and the "no store" and "return beta" variants |
| `7fc3bf0f...` | the pawn-ending grid | adds an optional argument for the size of the placebo change |

All runs on CPU 3-6 at Idle, 16 MB table unless stated.

**How representative the trees are.** On the 24 base positions at the same depths, the unmodified lock exe searched 36.9 million nodes and the replica 25.5 million. Per position the ratio runs from 0.40 to 7.5 (`data/lock_baseline_24.jsonl` against `data/etc_probe_deep.tsv`). Same order of magnitude, not the same tree.

### 5.2 Position sets

| Set | What it is | Size |
|---|---|---|
| First set | 24 positions I chose: 14 middlegames, 10 endgames | 24 |
| Wide set | the first set, plus positions the plain replica reached by playing its own best move 4, 8 and 12 plies on from each | 95 lines, **91 distinct boards**, 24 clusters |
| Supplementary set | 48 openings taken at a fixed stride from an opening file on the PC, each played on by the plain replica; see section 5.7 | 336 distinct boards, 48 clusters |

Weaknesses of the wide set, found by the reviewer:

- Four generated boards repeat an earlier line. The numbers below leave them out.
- A base position and the positions generated from it are not independent. The "by base" ranges below treat each base and its generated positions as one cluster.
- The generated positions were searched two plies shallower than their bases.
- Eight of the 95 lines share the pawn structure of section 5.8.

### 5.3 Kinds of run

- **Plain:** the search as written.
- **Counting:** the same tree, but at each eligible node every child is looked up and the harness only counts. Its node count must equal the plain run.
- **Cutoff taken:** the mechanism is applied. Two variants were added after the review: "no store" (the node takes the cutoff but writes nothing to the table) and "return beta" (the node returns beta instead of the child's bound).
- **Placebo:** the plain search with one history constant changed by 1 (`-32` to `-31` in the history bonus). It is not a mechanism. It shows how far the same numbers move under an arbitrary small change.

Rule names: `cutN` means expected cut nodes with at least N plies left. `allN` means every non-PV node. `nohmN` means expected cut nodes that have no hash move.

**Controls, all met.** The counting run had the plain node count in every position for every rule. The plain run repeated had identical node counts in every position.

### 5.4 How often a child entry already proves the cutoff

Wide set, 91 distinct positions, 57.0 million plain nodes (`data/etc_probe_wide_summary.md`).

| Rule | Group | Eligible nodes, share of all nodes | Of those, a child entry proves the cutoff | First proving child is the hash move | Nodes below such nodes, share of all nodes |
|---|---|---|---|---|---|
| cut4 | middlegame (56) | 4.74 % | 4.7 % | 19.8 % | 3.05 % |
| cut4 | endgame (35) | 6.66 % | 19.5 % | 25.2 % | 15.25 % |
| cut6 | middlegame | 1.44 % | 4.2 % | 24.6 % | 1.96 % |
| cut6 | endgame | 2.80 % | 17.7 % | 29.4 % | 11.07 % |
| cut6 | all (91) | 2.17 % | 13.5 % | 29.0 % | 6.85 % |
| cut8 | middlegame | 0.41 % | 3.9 % | 29.9 % | 1.21 % |
| cut8 | endgame | 1.22 % | 17.1 % | 33.7 % | 7.76 % |
| cut8 | all (91) | 0.84 % | 14.2 % | 33.4 % | 4.73 % |

- **"Nodes below such nodes"** is the share of all plain-search nodes spent underneath nodes where the cutoff was already available. It is a first-order estimate of the saving. **It is not a ceiling.** Taking a cutoff changes later table contents, and the realised change was larger than this estimate in some groups and smaller in others.
- **"First proving child is the hash move"** counts only the first proving child the harness meets, in move-generation order. The share of nodes where the hash move would also prove the cutoff is at least this large.
- The opportunity is mostly an endgame effect in these sets.
- Restricting to nodes without a hash move leaves little: 0.3 to 0.8 % of all nodes lie below such nodes (first set, rules `nohm6` and `nohm4`). Most of the opportunity sits at nodes that have a hash move. Whether that hash move would have cut just as fast is not measured.

### 5.5 Taking the cutoff, against a placebo

Wide set, 91 distinct positions. Node ratio = nodes of the run / nodes of the plain run. "Geo" is the geometric mean over positions (`data/etc_probe_wide_summary.md`, `data/etc_probe_wide_variants_summary.md`).

| Run | Geo | 95 % range, positions independent | 95 % range, by base | Geo without the two smallest ratios | Smallest and largest single ratio | Best move differs from plain | Score differs by half a pawn or more |
|---|---|---|---|---|---|---|---|
| **Placebo** | 0.984 | [0.900, 1.075] | [0.878, 1.080] | 1.021 | 0.080 and 3.271 | 18 of 91 | 3 of 91 |
| cut4 | 0.950 | [0.864, 1.045] | [0.836, 1.070] | 0.986 | 0.165 and 3.503 | 19 of 91 | 6 of 91 |
| cut6 | 0.950 | [0.870, 1.037] | [0.829, 1.072] | 0.989 | 0.079 and 1.995 | 20 of 91 | 4 of 91 |
| cut8 | 0.919 | [0.831, 1.016] | [0.806, 1.030] | 0.970 | 0.064 and 2.498 | 15 of 91 | 5 of 91 |
| cut6, no store | 0.900 | [0.813, 0.997] | [0.790, 1.003] | 0.941 | 0.101 and 2.523 | 16 of 91 | 7 of 91 |
| cut6, return beta | 0.924 | [0.855, 0.999] | [0.821, 1.027] | 0.955 | 0.160 and 2.664 | 16 of 91 | 7 of 91 |
| cut8, no store | 0.931 | [0.858, 1.011] | [0.822, 1.041] | 0.963 | 0.117 and 2.336 | 18 of 91 | 3 of 91 |
| cut8, return beta | 0.950 | [0.859, 1.051] | [0.840, 1.059] | 1.005 | 0.058 and 2.036 | 20 of 91 | 5 of 91 |

**Reading.**

- **No setting shows a node saving once clusters are respected.** Every "by base" range includes 1.00.
- **The placebo moves the numbers about as far as the mechanism does.** It changes the best move in 18 of 91 positions (the mechanism: 15 to 20). Its single-position ratios run from 0.08 to 3.3 (the mechanism: 0.06 to 3.5). So the swings and the best-move changes are properties of this replica under any small change. They are not evidence against the mechanism, and an earlier version of this file was wrong to present them that way.
- **Most of the measured saving of cut6 and cut8 comes from two positions** where the search with the cutoff became much smaller: the pawn ending of section 5.8, and `e8_bishop_knight_p4`, where the score also moved from -21 to 0. Without the two smallest ratios the mean is 0.97 to 0.99 for the three planned rules.
- **Two of the four variants have a range just below 1.00 when positions are treated as independent** (upper ends 0.997 and 0.999). They were added after the first results were known, four variants were tried, and neither holds by base. I do not count this as a result.
- **Base positions against generated ones.** On the 24 bases alone the geometric mean is 0.87 (cut6) and 0.85 (cut8); on the 67 generated positions it is 0.98 and 0.95. The placebo gives 1.07 and 0.96 on the same two groups. The generated positions were searched two plies shallower, so this split mixes a depth effect with the sample.

**The first set on its own.** On the 24 base positions rule cut6 gave 0.870 with range [0.761, 0.995], and rule all3 gave 0.782 [0.655, 0.935]. Rule cut6 would have passed all five items of the rule in section 6. That rule was written after this run was seen, so the first set cannot count as a test of it. Six rules were tried with the cutoff taken on that set, and one of them (`nohm6`, middlegames) came out clearly worse than plain: 1.116 [1.042, 1.195].

### 5.6 Time

**What was measured.** The counting run does the lookups and nothing else, on the identical tree. Its wall time against the plain run is the cost of the lookups in this harness. I measured it four times on the wide set: once in the first run and three times in a repeat made after the review (`data/etc_probe_wide_timing_rep1.tsv` to `rep3`).

| Rule | Group | Lookup time, four measurements | Nodes below hit nodes (section 5.4) |
|---|---|---|---|
| cut6 | all (91) | +5.5 %, +4.6 %, +4.3 %, +3.4 % | 6.85 % |
| cut6 | middlegame | +5.7 %, +4.5 %, +4.1 %, +7.9 % | 1.96 % |
| cut6 | endgame | +5.0 %, +4.9 %, +4.7 %, -2.2 % | 11.07 % |
| cut8 | all (91) | +2.9 %, +2.1 %, +1.5 %, +4.3 % | 4.73 % |
| cut8 | middlegame | +2.5 %, +2.0 %, +1.5 %, +7.4 % | 1.21 % |
| cut8 | endgame | +3.8 %, +2.2 %, +1.6 %, +0.5 % | 7.76 % |

Rule cut4 was measured once: +13.3 %.

**What can be said.**

- The lookups cost a few percent of time in this harness: roughly 3 to 6 % for cut6 and 1.5 to 4 % for cut8.
- That is the same order as the first-order saving. In the middlegame group every measurement of the cost is above the first-order saving. In the endgame group every measurement is below it.
- **That comparison does not settle anything**, for two reasons.
  - The first-order saving is a weak guide. The realised node change in the middlegame group is anywhere between 8 % fewer and 7 % more nodes (section 5.5 ranges by group, in `data/etc_probe_wide_summary.md`).
  - The clock is noisy. The machine was running other jobs and my runs were at Idle priority. In the fourth measurement the plain run against itself varied by 24.6 % per position (3.8 to 4.8 % in the other three). The wall time of the same cut8 search, with identical node counts, was 0.97 times plain in one run and 1.37 times plain in another.
- So I make no claim that the mechanism is slower or faster. An earlier version of this file said "in middlegames the lookups cost more than they save". The data do not support that sentence, and the reviewer was right to reject it.
- The repeat runs recorded wall time on purpose. If that counts as a timing run under the brief, it was outside it; `STATUS.md` records the ruling. A proper timing needs a quiet machine and an interleaved pattern, which is QA's to schedule.

### 5.7 Supplementary run on independent openings

The review showed that the wide set is small, clustered and partly duplicated. So I made one more run, on a set whose positions I did not choose. Its reading rule was committed and pushed before the run started (`data/SUPPLEMENT_RULE.md`, commit `03aa2def`, 21:52 PT; the run started at 21:54 PT). The rule says the run cannot change the verdict. It decides how the size of the effect is worded.

**Set.** 48 openings taken at a fixed stride from an opening file on the PC. From each, the plain replica played its own best move at depth 10, and the position was written every 12 plies, six times. That gives 336 positions, no board twice, in 48 clusters of seven. Search depth 16 with more than six pieces (213 positions), 20 with three to six (102), 24 with two or fewer (21). "Pieces" means knights, bishops, rooks and queens of both sides. 222.3 million plain nodes. Harness exe `775b9b62...`, built from the committed source.

**Validity.** No search hit the node cap. The counting runs had the plain node count in 336 of 336 positions.

| Run | Group | Geo | 95 % range by opening | Smallest and largest single ratio | Best move differs from plain | Score differs by half a pawn or more |
|---|---|---|---|---|---|---|
| Placebo | all (336) | 0.999 | [0.962, 1.037] | 0.195 and 3.683 | 95 of 336 | 18 of 336 |
| **cut6 (primary)** | all (336) | **0.987** | **[0.954, 1.022]** | 0.369 and 4.003 | 80 of 336 | 10 of 336 |
| cut8 | all (336) | 0.986 | [0.958, 1.015] | 0.302 and 2.429 | 72 of 336 | 14 of 336 |
| Placebo | more than six pieces (213) | 0.993 | [0.957, 1.046] | 0.195 and 3.036 | 63 of 213 | 6 of 213 |
| cut6 | more than six pieces | 1.016 | [0.981, 1.053] | 0.426 and 3.325 | 51 of 213 | 3 of 213 |
| cut8 | more than six pieces | 1.005 | [0.975, 1.047] | 0.384 and 2.429 | 51 of 213 | 5 of 213 |
| Placebo | six pieces or fewer (123) | 1.009 | [0.960, 1.112] | 0.425 and 3.683 | 32 of 123 | 12 of 123 |
| cut6 | six pieces or fewer | 0.939 | [0.868, 1.010] | 0.369 and 4.003 | 29 of 123 | 7 of 123 |
| cut8 | six pieces or fewer | 0.954 | [0.893, 1.029] | 0.302 and 2.124 | 21 of 123 | 9 of 123 |

**Reading, by the committed rule: not shown either way.** The primary range includes 1.00.

What else the run says. The rule lists these as reported without a decision.

- **Size.** The range excludes a saving larger than about 5 % in this replica on positions of this kind. The best estimate is 1.3 %.
- **By material.** With more than six pieces there is no sign of a saving. With six or fewer the estimate is 5 to 6 %, and the range still includes 1.00.
- **Best moves and scores.** The mechanism changes the best move less often than the placebo does (72 to 80 positions against 95) and moves fewer scores by half a pawn (10 to 14 against 18). On this measure it does no harm that a placebo does not also do.
- **Opportunity.** A child entry proves the cutoff at 4.0 % (cut6) and 3.2 % (cut8) of eligible nodes with more than six pieces, and at 9.0 % and 7.8 % with six or fewer. The nodes below such nodes are 4.0 % (cut6) and 2.6 % (cut8) of all nodes. These are lower than on the wide set (17 %, and 6.9 % and 4.7 %), whose endgames I had typed by hand.
- **Time.** Wall time of the lookups in this run: +7.5 % (cut6) and +0.7 % (cut8). Indicative only, as in section 5.6.
- **Openings against generated positions.** The split has the opposite sign to the wide set: openings 1.07 to 1.08, generated positions 0.97. I read nothing into either split.

Data: `data/etc_probe_supp.tsv`, summary `data/etc_probe_supp_summary.md`.

### 5.8 A counter-witness: the classic pawn ending

Position 70 of Fine's *Basic Chess Endings* (`8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1`) is the standard test of a transposition table. White wins only with 1.Kb1; 1.Kb2 draws. Data: `data/etc_probe_fine70_variants.tsv` (replica) and `data/lock_fine70_d40.json` (lock exe). Each replica setting was run at depths 24, 26, 28, 30, 32, 34, 36 and 40. The first table is the baseline run, with the replica's constants as written.

| Setting | Best move at the eight depths | Score at depth 40 | Nodes at depth 40 | Plain nodes divided by these |
|---|---|---|---|---|
| Lock exe (the real engine) | Kb1 at each, from depth 22 on | +2783 | 168.3 M | - |
| Replica, plain | Kb1 at each | +320 | 15.39 M | 1 |
| Replica, placebo | Kb1 at each | +400 | 24.62 M | 0.62 |
| cut4 | Kb1 at each | +551 | 2.28 M | 6.7 |
| cut6 | Kb1 at each | +576 | 1.23 M | 12.5 |
| cut6, no store | Kb1 at each | +190 | 0.83 M | 18.6 |
| cut6, return beta | Kb1 at each | +186 | 6.94 M | 2.2 |
| **cut8** | **Kb2 at each**, score falling from +49 to 0 | 0 | 0.18 M | wrong move |
| cut8, no store | Kb1 at each | +445 | 2.72 M | 5.7 |
| **cut8, return beta** | **Kb2 at depths 24 to 36**, Kb1 at depth 40 | +209 | 1.45 M | 10.6 |
| **all3** | **Kb2 at depth 24**, Kb1 from depth 26 | +401 | 1.58 M | 9.7 |

**What is observed.**

- Five of the eight settings of the mechanism keep 1.Kb1 at every depth and need 2 to 19 times fewer nodes than the plain replica at depth 40.
- Three settings play the drawing move at some depth. One of them plays it at every depth tested and its score sinks to zero.
- The plain replica and its placebo play 1.Kb1 at every depth. At depth 40 the placebo needs 1.6 times the plain nodes.
- The lock exe plays 1.Kb1 from depth 22 on, with scores from +829 to +2783.

**How much weight this carries.**

- **It is one trajectory per setting, not eight tests.** A depth-40 run repeats the depth-24 run and goes on. "Wrong at every depth" is one wrong turn that is never corrected.
- **Table size is not an independent check here.** Plain, cut6 and cut8 were repeated with 1, 2, 4, 8, 64 and 256 MB tables (`data/etc_probe_fine70_hash*.tsv`). The best moves are the same at every size, and the node counts are the same from 4 MB up, because this position does not fill the table.
- **The plain replica never shows a won score.** Its scores stay between +206 and +320. It finds the move, not the win. Only the lock exe shows the win.
- **The failure is not monotone.** In this baseline run cut4 and cut6 take more cutoffs than cut8 and keep the winning move.

**The placebo control.** A single wrong trajectory could be chance. So I repeated everything under ten placebo-size changes of one history constant (default -32; values -40 to -24), each run plain and with every setting (`data/etc_probe_fine70_grid.tsv`, summary `data/etc_probe_fine70_grid.md`).

| Setting | Runs with 1.Kb1 at every depth | Runs with another move at some depth | Runs with another move at depth 40 |
|---|---|---|---|
| Plain | 10 of 10 | 0 | 0 |
| cut4 | 6 of 10 | 4 | 0 |
| cut6 | 10 of 10 | 0 | 0 |
| cut6, no store | 9 of 10 | 1 | 0 |
| cut6, return beta | 10 of 10 | 0 | 0 |
| cut8 | 4 of 10 | 6 | 2 |
| cut8, no store | 5 of 10 | 5 | 0 |
| cut8, return beta | 4 of 10 | 6 | 1 |
| all3 | 1 of 10 | 9 | 0 |

- **This is not chance.** The plain replica keeps the winning move in all ten runs. The settings of the mechanism miss it at some depth in 31 of 80.
- **It is mostly a delay.** Nearly all misses are at depths 24 to 36. At depth 40 only 3 of the 80 runs still play another move.
- **It depends on the setting.** Rule cut6 and its "return beta" variant never miss. Rule all3 misses in nine of ten.
- **Not storing is not a cure.** With the default constant the failure of cut8 went away when the node stored nothing. Under the ten changes that variant still missed in five of ten.
- **Node counts swing widely here too.** At depth 40 the plain replica needs between 3.9 and 41.4 million nodes over the ten runs, and rule cut6 between 1.0 and 17.9 million.

**The cause is not established.** The reviewer checked the harness line by line and found no unsound cutoff: bound direction, depth requirement, repetition test and mate exclusion are right. A plausible reading is that the mechanism makes the search lean harder on stored bounds that depend on the path they were found on (draw scores from repetitions). That is a hypothesis. It is also one position, in a replica.

## 6. The rule and the verdict

The rule is `data/QUALIFICATION_RULE.md`, committed at 20:55:44 PT (`30b96b42`). The 95-position run finished writing at 20:55:51 PT.

| Item | cut6 | cut8 |
|---|---|---|
| 1. Controls hold | pass | pass |
| 2. Plain search agrees at 99 % or more | pass (100.0 %) | pass (100.0 %) |
| 3. Range of the node ratio entirely below 1.00 | **fail** (upper end 1.042) | **fail** (upper end 1.025) |
| 4. First-order net positive in middlegames, or time clearly below 1 | **fail** (net -3.7 %; time 1.072) | **not decidable** (net -1.2 %; time 0.978 in that run; see below) |
| 5. Middlegame node ratio at or below 1.00 | pass (0.993) | pass (0.989) |

Item 3 fails for both rules. It uses node counts only, so the timing noise of section 5.6 cannot change it. It also fails with the four duplicate boards removed (upper ends 1.037 and 1.016) and with ranges by base (1.072 and 1.030). **Verdict: NO QUALIFIED GAP.**

**Weaknesses of the rule, found by the reviewer.** They do not change the verdict, but they change how much it says.

- **Low power.** The log of the node ratio has a standard deviation of about 0.45 per position. With 95 positions the rule could detect a saving of about 12 to 13 %. The measured 4 to 8 % was below what it could see. So a failed item 3 means "not shown", not "absent".
- **Two rules were tested** (cut6 and cut8), which makes a chance pass more likely, not less.
- **Item 4 is not well defined.** "Twice the A/A time deviation" can be read with the deviation of the totals (0.0001) or of single positions (4.8 %). An earlier version of this file used the lenient reading and called cut8 a pass on time. A later run of the same search took 1.37 times the plain time, so the time part is noise and the item cannot be decided for cut8.
- **Item 5 passes on a point estimate** with no range.
- **No correctness item.** The rule has no check of best moves, scores or solved positions. A mechanism that makes searches smaller by breaking them could have passed item 3. Any later rule needs such an item, measured against a placebo.

## 7. Things I noticed that are outside this job

- At depth 17 on the fourth move-generator test position (`rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8`) the lock exe's best move is the rook underpromotion `d7c8r` (score +660). Promoting to a queen on the same square loses the new piece to the same recapture, so this is probably a tie between equal moves and not a defect. Files named `ROOK_UNDERPROMO_PASS_*` in `forge_push` suggest the crew already tracks it. Reported, not investigated.
- `CURRENT_LOCK.json` names the AL1 source folder as the lock's `tree`, although the lock exe was built from a later source (`COVERAGE.md` section 2).
