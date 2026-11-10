# EVIDENCE: what was observed, and what it does and does not support

## Key points

- **The gate record shows no failure that points to an unowned search mechanism.** Of 126 gate rows, 80 were capped without a decision. The rest are explained by weak nets, time losses, a changed book and thread count, and old baselines.
- **Six in ten gate games end by threefold repetition.** That is observed in 54,667 logged games. The mechanisms that target repetition are all owned already.
- **Time losses are new and concentrated.** All 70 sit in 8 rows, 67 of them in rows recorded on 2026-11-07 to 2026-11-09. Their logs are gone, so the cause is UNVERIFIED.
- **The one unowned mechanism was measured in a replica search on the lock's own board and evaluation code.** A cutoff is already available from a child entry at about 4 % of eligible middlegame nodes and 17 % of endgame nodes. Taking it did not give a statistically clear node saving on 95 positions, and in middlegames the lookups cost more than they save.
- **On the classic pawn-ending test position the replica either gains a factor of 7 to 12 in nodes or loses the win entirely, depending on one threshold.** The lock exe solves that position unaided.
- **The rule fixed before that run was read gives NO QUALIFIED GAP.**

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
| In the replica, a child entry already proves the cutoff at 3.9 to 4.7 % of eligible middlegame nodes and 17.3 to 19.5 % of eligible endgame nodes | observed | `data/etc_probe_wide_summary.md` |
| In the replica, taking that cutoff changes the node count by a factor of 0.93 to 0.96 with a 95 % range that includes 1.00 | observed | same |
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

**Noise and low power: the main cause.** 56 of the 77 option-line rows are capped. The crew's own arithmetic says a 3,000-game run resolves about ±5.9 Elo and that singles worth +1 to +4 end "UNPROVEN at the cap by construction" (`opus-deepres-20261104@2231439c:opus_deepres/notes/RANKING_FINAL.md:32-35`). Repeats of the same exe and option line show the spread directly:

| Candidate | First run | Repeat |
|---|---|---|
| net `f006` | +29.44 Elo, 698 games, H1 | +7.18, 1,500 games, capped |
| net file `o30...soupU8` | +16.50, 2,528 games, H1 | +3.04, 4,000 games, capped |
| `EvalOptimism=40` | +6.95, 3,000 games, capped | -5.30, 2,360 games, H0 |
| `BundlePreset=B1` | +11.25, 2,100 games, H1 | +8.34, 3,000 games, capped |

A single capped result, and even a single H1, says little about the size of a mechanism.

**Net strength, not search.** Six net-file rows are H0 at -86 to -116 Elo and three more are NOT CLEAN at -96 to -124. The four early stops are net builds too. These are about the net.

**Time control, threads and book.** Fifteen rows name the UHO book, most with the note that it is "NOT poolable" with the older book. The manifest entry of the newest such gate (`uhoB70_packanpc_w50_vs_AL1lp` in `...\forge_push\autorestart\forge_gates.json`) says `threads = 2`, `concurrency = 4`. All 51 surviving logs say "10+0.1, 1t, 16MB, 8moves_v3". Rows from the two regimes cannot be compared.

**Crashes and time losses.** Zero crashes. 70 time losses in 8 rows:

| Gate | Games | Time losses | Recorded |
|---|---|---|---|
| R5A-2 | 3,000 | 3 | 2026-10-30 23:28 |
| CAN1 | 1,316 | 6 | 2026-11-07 16:33 |
| UT1 | 498 | 6 | 2026-11-08 21:35 |
| NPTW4S5-B07 | 256 | 1 | 2026-11-08 22:10 |
| NPTW4S5-FIN | 286 | 15 | 2026-11-08 22:50 |
| NPTW4S6-FIN | 242 | 5 | 2026-11-08 23:23 |
| UB69 | 748 | 12 | 2026-11-09 01:08 |
| UB70W50 | 746 | 22 | 2026-11-09 16:55 |

The 51 older logs (54,667 games) contain no time loss at all. UB70W50 lost 22 of 746 games on time and was read as H0 at -24 Elo. If the candidate was the side that forfeited, the time losses alone are about that size. I could not check, because those logs are missing. These verdicts should not be read as evidence about the search. Whether the engine itself overruns its clock under load is an open question; the lock checks the clock every 1,024 nodes (`search.cpp:992`, `:1125`, `:891-902`), which at 2 million nodes per second is about every half millisecond, so I have no code-level reason to suspect it. That is reasoning, not a measurement.

**Paired-game imbalance.** The pentanomial counts are recorded for every row. I found no row whose verdict depends on an imbalance, and did not analyse this further.

**Obsolete baselines.** The base changed six times: 7 rows against `ep10`, 62 against `h256_e12`, 16 against the AL1 net lock, 23 against its LTO build, 8 against trial_w6, 6 labelled combo29, 4 against job-local bases. Half the table is measured against a base two net generations old.

Two things follow that are not new mechanisms but matter for reading the record:

- The search bundle `BundlePreset=B4` is H1 twice against `h256_e12` (+14.08 and +11.05 Elo). I found no clean result for it against any later base. The later bundle rows (UB69, UB70W50) are both NOT CLEAN.
- The CSV labels UB70W50's base as combo29, while its manifest entry names the older LTO lock exe as `base_override`. Which exe played is UNVERIFIED.

**Real search defects in the record.** The only ones I found are already owned: the two lock bugs fixed by today's `t12b` candidate.

## 3. What the game endings say

`tools/gate_log_miner.py` over the 51 surviving logs in `D:\grok-pc-data\forge_push` (all 10+0.1, one thread, 16 MB hash, 8moves_v3, no adjudication):

| Ending | Games | Share |
|---|---|---|
| Threefold repetition | 32,723 | 59.9 % |
| Checkmate | 14,351 | 26.3 % |
| Fifty-move rule | 3,780 | 6.9 % |
| Insufficient material | 3,716 | 6.8 % |
| Stalemate | 97 | 0.2 % |
| Time loss, illegal move, disconnect | 0 | 0 % |

Draws are 73.7 % of games and 81.2 % of draws are repetitions. Without PGNs I cannot tell how many repetitions came from better positions. The mechanisms aimed at this are owned: the upcoming-repetition test, the twofold rule by node type and the draw-score jitter (`DEDUPE.md` rows 1 to 3). So this is a reason to gate owned work, not a gap.

## 4. The lock code the candidate concerns

- A node takes a table cutoff only from **its own** entry: `search.cpp:1165-1170` (non-PV, no excluded move, depth sufficient, rule-50 below 90, bound in the right direction).
- A child's key is computed before the move is made, but only to prefetch the child's table cluster: `search.cpp:1379-1383` in `search`, `1066-1070` in `qsearch`.
- No line reads a child's entry.

So when a node has no usable entry of its own, but one of its moves leads to a position whose stored upper bound already refutes the node, the lock does not know. It searches its moves in order until one of them reaches that position, or another move cuts first.

## 5. Replica measurement

**What was built.** `tools/etc_probe/etc_probe.cpp` is an original fixed-depth search written for this measurement: principal-variation search, a table with the lock's cluster shape, null move, reverse futility, late-move reductions and pruning, the check extension, and a quiescence search. It links the unmodified lock files `bitboard.cpp`, `board.cpp`, `eval.cpp`, `eval_params.cpp` (hashes in `data/lock_source_hashes.tsv`) and uses the lock's move generator, keys, `key_after`, SEE, repetition test and hand-crafted evaluation. It does not contain or link the lock's `search.cpp`.

**What it lacks compared with the lock.** Singular extensions, ProbCut, razoring, continuation, capture and correction history, the counter move and the net. Its move ordering is weaker than the lock's.

**Build.** Compiler `C:\opus_5h\...\llvm-mingw-20261104-ucrt-x86_64\bin\clang++.exe`, sha256 `d05fee2c...`, the same binary Engine QA's receipt names for the lock. Flags in `tools/etc_probe/build_and_run.ps1`. Harness exe sha256 `f0409ac2c39bd5541c3903eaee7dc7bf243192e36cb1b44279ede51bbef32beb`. All runs on CPU 3-6 at Idle, 16 MB table.

**How representative the trees are.** On the 24 base positions at the same depths, the unmodified lock exe searched 36.9 million nodes and the replica 25.5 million. Per position the ratio runs from 0.40 to 7.5 (`data/lock_baseline_24.jsonl` against `data/etc_probe_deep.tsv`). Same order of magnitude, not the same tree.

**Three kinds of run per position.**

- Plain: the search as written.
- Counting: the same tree, but at each eligible node every child is looked up and the harness only counts. Its node count must equal the plain run.
- Cutoff taken.

**Controls, all met.** The counting run had the plain node count in 95 of 95 positions for every rule. The plain run repeated had identical node counts in 95 of 95. Summed over 95 positions the repeat's time was 0.9999 of the first; per position the ratio had a standard deviation of 4.8 %. Where a child entry would cut, the plain search also failed high in 99.8 to 100 % of cases.

**Results on 95 positions (57.9 million plain nodes).** Rule `cutN` means expected cut nodes at remaining depth N or more.

| Rule | Group | Eligible nodes | Cutoff available | Of those, via the hash move | Nodes below such nodes | Lookup cost in time | Node ratio, cutoff taken (geo mean, 95 % range) | Time ratio |
|---|---|---|---|---|---|---|---|---|
| cut4 | middlegame (56) | 4.74 % | 4.7 % | 19.8 % | 3.05 % | +14.0 % | 0.995 [0.911, 1.086] | 1.052 |
| cut4 | endgame (39) | 6.69 % | 19.5 % | 25.5 % | 15.15 % | +12.1 % | 0.906 [0.750, 1.093] | 1.327 |
| cut6 | middlegame | 1.44 % | 4.2 % | 24.6 % | 1.96 % | +5.7 % | 0.993 [0.924, 1.068] | 1.050 |
| cut6 | endgame | 2.84 % | 17.7 % | 29.8 % | 10.99 % | +5.1 % | 0.903 [0.751, 1.085] | 1.110 |
| cut6 | all (95) | 2.20 % | 13.7 % | 29.4 % | 6.87 % | +5.5 % | 0.955 [0.876, 1.042] | 1.072 |
| cut8 | middlegame | 0.41 % | 3.9 % | 29.9 % | 1.21 % | +2.5 % | 0.989 [0.918, 1.065] | 0.973 |
| cut8 | endgame | 1.25 % | 17.3 % | 34.2 % | 7.72 % | +3.7 % | 0.852 [0.691, 1.051] | 0.987 |
| cut8 | all (95) | 0.86 % | 14.5 % | 33.9 % | 4.75 % | +2.9 % | 0.930 [0.844, 1.025] | 0.978 |

"Nodes below such nodes" is the share of all plain-search nodes spent underneath nodes where the cutoff was already available. It is a first-order ceiling on the saving.

**Reading.**

- The opportunity is real and it is mostly an endgame effect. In middlegames it is about 1 to 3 % of nodes.
- The lookups are not free. At depth 4 and up they cost more than four times what they could save in middlegames (14.0 % of time against 3.05 % of nodes).
- Taking the cutoff changes later table contents and scores, so single positions swing between 0.2 and 2.2 times the plain node count. Across 95 positions the mean saving is 4 to 7 % and is not statistically distinguishable from zero.
- The best time result is 2 % faster (cut8). The other two rules are slower.
- The first run on 24 positions looked better (geometric mean 0.85 to 0.87, `data/etc_probe_deep_summary.md`). The wider set shrank it. Small position sets mislead for this kind of change.
- Restricting to nodes without a hash move removes the effect: 0.2 to 0.4 % of middlegame nodes (24-position run, rules `nohm4`, `nohm6`). Almost all of the opportunity sits at nodes that do have a hash move pointing elsewhere.

**A counter-witness: the classic pawn ending.** Position 70 of Fine's *Basic Chess Endings* (`8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1`) is the standard test of a transposition table. White wins only with 1.Kb1. Data: `data/etc_probe_fine70.tsv` (replica) and `data/lock_fine70_d40.json` (lock exe).

| Depth | Lock exe: move, score, nodes | Replica plain | Replica cut4 | Replica cut6 | Replica cut8 | Replica all3 |
|---|---|---|---|---|---|---|
| 24 | Kb1, +829, 0.27 M | Kb1, 127 k | Kb1, 46 k | Kb1, 46 k | **Kb2**, +49, 33 k | **Kb2**, +67, 23 k |
| 28 | Kb1, +1140, 1.28 M | Kb1, 347 k | Kb1, 75 k | Kb1, 56 k | **Kb2**, +49, 47 k | Kb1, 65 k |
| 32 | Kb1, +1185, 1.71 M | Kb1, 1.31 M | Kb1, 216 k | Kb1, 391 k | **Kb2**, +26, 84 k | Kb1, 385 k |
| 36 | Kb1, +2504, 40.5 M | Kb1, 3.94 M | Kb1, 468 k | Kb1, 485 k | **Kb2**, +3, 137 k | Kb1, 933 k |
| 40 | Kb1, +2783, 168.3 M | Kb1, 15.39 M | Kb1, 2.28 M | Kb1, 1.23 M | **Kb2**, 0, 177 k | Kb1, 1.58 M |

Two things are observed here at once. With three of the four rules the replica reaches the same winning move with 7 to 12 times fewer nodes at depth 40. With the fourth rule it plays the drawing move at every depth from 24 to 40 and its score sinks to zero. The lock exe itself solves the position from depth 22 on. I did not establish why that one rule fails. A plausible reading is that the cutoff makes the search lean harder on stored bounds that depend on the path they were found on (draw scores from repetitions), a known weakness of transposition tables; that is a hypothesis. Whatever the cause, the outcome is erratic: a large gain or a lost win, decided by a threshold.

## 6. The rule and the verdict

The rule is `data/QUALIFICATION_RULE.md`, committed at 20:55 PT (`30b96b42`) before the 95-position summary was read.

| Item | cut6 | cut8 |
|---|---|---|
| 1. Controls hold | pass | pass |
| 2. Plain search agrees at 99 % or more | pass (100.0 %) | pass (100.0 %) |
| 3. Range of the node ratio entirely below 1.00 | **fail** (upper end 1.042) | **fail** (upper end 1.025) |
| 4. First-order net positive in middlegames, or time clearly below 1 | **fail** (-3.7 %; time 1.072) | pass on time only (0.978; net -1.2 %) |
| 5. Middlegame node ratio at or below 1.00 | pass (0.993) | pass (0.989) |

Item 3 fails for both rules. **Verdict: NO QUALIFIED GAP.**

## 7. Things I noticed that are outside this job

- At depth 17 on the fourth move-generator test position (`rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8`) the lock exe's best move is the rook underpromotion `d7c8r` (score +660). Files named `ROOK_UNDERPROMO_PASS_*` in `forge_push` suggest the crew already tracks this. Reported, not investigated.
- `CURRENT_LOCK.json` names the AL1 source folder as the lock's `tree`, although the lock exe was built from a later source (`COVERAGE.md` section 2).
