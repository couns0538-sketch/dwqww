# Job 26 · Forge on a node clock

1. **Step 0 passed.** `nproc` returned 5. The original Job 16 r15d binary reproduced 312,866 and 862,329 nodes at bench depths 11 and 13, and 4,865,609 leaves at perft depth 5. With PC20 and net768 it reproduced 882,074 and 4,275,906 bench nodes. Each pin used a fresh process. Both net runs reported the active checksum `30ab43b4ba5db5f3`. [Five pins](astra5/job26/step0/r15d/checks.txt) · [Hashes, book and build](astra5/job26/build.txt)
2. **The patch and its known answers.** The patch adds 27 source lines and removes 11 across three files. It adds the UCI spin option, uses integer division of total nodes by the configured rate for the search clock and five time reads, and emits the stopped-node count at the normal search footer. At zero the original wall-clock expressions still run. Pondering and ponderhit are unsupported under the node clock. Patch SHA-256 `2b65934e5dad80660712dcb7f42376c805de70d67637cc70e53a9654a4fbb58e`. [Unified diff](astra5/job26/nodeclock_r15d.patch.txt) · [Source locations](astra5/job26/P/changes.txt)

   KP0 passed. The patched build at zero repeated the five pins. At depth 12 the 200 O positions totaled 8,315,168 nodes and the 353 G positions totaled 17,611,204. The final footer equaled the final depth count on every one. The ten-game driver-S replay produced 1,183 records, zero missing counts and 4,863,663 nodes. Its record file is byte-identical to both Job 23 K23 files, SHA-256 `b85eb5f01afbbb12771b1a8cf5c579f3c6db3873fa0779f9fce94ca0c5b25a76`. [Patched pins](astra5/job26/KP0/nc/checks.txt) · [O](astra5/job26/KP0/b/O/comparison.txt) · [G](astra5/job26/KP0/b/G/comparison.txt) · [Replay readback](astra5/job26/KP0/c/comparison.txt)

   The next five runs each used one fresh process, one thread and built-in evaluation. The engine received `ucinewgame` and `isready` before each position. The hash covers the position number, final completed depth, its node count and the best move. T sums the integer charge from each search’s stopped-node footer. “Over” counts searches that stopped inside a later iteration, after the last depth line.

   | Run | Positions | Row SHA-256 prefix | T, node-ms | Over | N on each over |
   | --- | ---: | --- | ---: | ---: | ---: |
   | [O0](astra5/job26/KP1/O0/summary.txt) | 200 | `3eac50dd8fd5297e` | 54,326 | 0 | — |
   | [A0](astra5/job26/KP1/A0/summary.txt) | 353 | `424d931234dd3ff9` | 98,026 | 1 | 1,585,152 |
   | [A1](astra5/job26/KP1/A1/summary.txt) | 353 | `5a85f018917c736f` | 82,001 | 1 | 1,585,152 |
   | [B0](astra5/job26/KP1/B0/summary.txt) | 353 | `244776b6649f2ce1` | 45,372 | 2 | 675,840 |
   | [C0](astra5/job26/KP1/C0/summary.txt) | 353 | `4e8210e936e59fd5` | 20,715 | 7 | 174,080 |

   Every row signature, charge total and over count reproduced the earlier PC single-search reference. In A1, 162 of 353 searches emitted a hold. A0 and A1 used the same positions at 6000+60. The switch reduced the total charge by 16,025 node-ms (16.35%) and changed the chosen move on nine positions. [A0 rows](astra5/job26/KP1/A0/rows.txt) · [A1 rows](astra5/job26/KP1/A1/rows.txt)

   CP1 passed. Changing NodeClock from 1000 to 2000 on A0 changed 323 of 353 rows and 31 best moves. Its row signature changed from `424d931234dd3ff9` to `66c6190bdd842693`. [Doubled-clock control](astra5/job26/kp1-qa/CP1-audit.txt) · [Nine A0/A1 move changes](astra5/job26/kp1-qa/paired-moves.tsv)

3. **K26 and C26 passed.** A enabled TmFinishIteration and B disabled it. The two K26 runs played the first ten openings in opposite orders. All 20 move lists and every stopped-node count matched across 2,602 searches per run. With A at NodeClock 2000, 20 of the 20 games differed, 20 in moves and 20 in node counts. At game 1 ply 1, A changed from f3e1 at 286,152 nodes to a2a4 at 1,392,631 nodes. [Independent control comparison](astra5/job26/audit/controls-independent.json)

   C26 lost four games on time, all by A, with the clock rate doubled and the runner still charging one unit per 1,000 nodes. [Control time losses](astra5/job26/audit/C26/time-losses.tsv)

   | Game | Ply | Stopped N | Clock before |
   | ---: | ---: | ---: | ---: |
   | 1 | 191 | 115,819 | 108 |
   | 6 | 128 | 86,016 | 82 |
   | 17 | 139 | 480,256 | 411 |
   | 18 | 78 | 232,448 | 204 |

4. **Frozen prediction.** Commit `0ff080bacf6a` contains only the prediction file. The outcomes use complete match pairs. [Original prediction](astra5/job26/prediction.txt)

   | Quantity | Frozen range | Observed | Grade |
   | --- | ---: | ---: | --- |
   | Elo | -45 to 45 | -5.46 | Inside |
   | A mean used | 105 to 150 | 130.55 | Inside |
   | B mean used | 115 to 155 | 141.40 | Inside |
   | Time losses | 0 to 2 | 0 | Inside |
   | Pairs by minute 45 | 105 to 170 | 156 | Inside |

5. **Match.** 159 complete opening pairs, 318 games. A scored 45 wins, 50 losses and 223 draws. The pentanomial counts were 2, 31, 98, 26, 2 for A scoring 0, ½, 1, 1½ and 2 points per opening pair. The Job 21 paired estimate was **-5.46 Elo**, 95% interval **[-23.76, +12.83]**. [Full match summary](astra5/job26/audit/M/summary.json) · [Opening pairs](astra5/job26/audit/M/paired-ends.tsv)

   | Ending | Games |
   | --- | ---: |
   | checkmate | 95 |
   | stalemate | 1 |
   | insufficient | 8 |
   | threefold | 211 |
   | fifty | 3 |
   | time | 0 |
   | cap | 0 |

   | Engine | Searches | Mean charged node-ms | Searches with a hold | Mean clock left per game |
   | --- | ---: | ---: | ---: | ---: |
   | A | 18,222 | 130.550 | 8,133 | 1957.381 |
   | B | 18,233 | 141.396 | 0 | 1333.060 |

   By color, White finished with a mean clock of 1655.182 node-ms and Black with 1635.258. [Checked game clocks](astra5/job26/audit/M/game-readback.tsv)

   **TIME LOSSES** 0. [Time-loss receipts](astra5/job26/audit/M/time-losses.tsv)

6. **LEVEL.** The 95% opening-paired Elo interval includes zero.

## Facts

A workspace interruption ended the first C26 process after 19 finished games. The 43rd search of game 20 was canceled. The fresh control replayed all 20 games. All 1,994 search rows in the 19 finished games and all 42 complete rows from game 20 matched exactly. Its measurements are counted once. [Interruption and rerun](astra5/job26/games/reconnect-note.txt) · [Same-input replay comparison](astra5/job26/audit/C26/attempt1-vs-repeat.txt)

The match used the original Job 24 book in file order starting at opening 11, with colors reversed per opening. Each game started two new processes on the same patched binary. A enabled TmFinishIteration and B used the default off. Both started at 6000 node-ms with 60 per move, and each search spent its final N divided by 1000, rounded down. The independent readback replayed every legal move and rebuilt every clock in the 318 counted games. [Readback and scoring](astra5/job26/audit/method.txt) · [Game starts](astra5/job26/games/M/launch.tsv)

The runner recorded “minute45 no new pair”. It launched 318 games. 156 pairs had completed by minute 45, and 159 had completed when playing ended. Openings 170–234 were unplayed at the cutoff. [Stop receipt](astra5/job26/games/M/end.json) · [Pair completion times](astra5/job26/games/M/pairs.tsv)

During control validation the first independent summary added Black’s clock to engine B’s clock. I corrected the grouping and checked each player’s total two ways, from final game receipts and from starting balances, increments and recorded charges. The error affected two reported control means. [Correction and original values](astra5/job26/audit/clock-correction.txt)

Across complete match games A used 10.85 node-ms less per search on average (7.67% relative to B). These averages include the different positions and clock states each player reached. The matched single-position comparison above fixes the starting clock and position. [Match search totals](astra5/job26/audit/M/summary.json)

## Suspicions

A hold records a decision to return the move from a completed depth because the next iteration may exceed the remaining soft allocation. The extra balance may be available on a later move. A causal test of where that balance matters would require holding the subsequent positions fixed. [What the clock rule measures](astra5/job26/P/interpretation.txt)

## What I did not do

The assignment specifies the following limits.

> the PC's net and build (the built-in evaluation plays here); the wall clock (its overhead, the system timer); NodeClock values other than 1000 and 2000; more than one thread; other time controls; TmNodeShare (not played); a difference smaller than about 40 Elo, which a few hundred games cannot see.

## What I am not sure about

The paired interval describes these openings and this clock rule. The receipts identify when the hold fired, how much each search spent, and who won. They do not identify which individual hold, saved node, or later search caused a particular result. The patch also has pre-existing early-return paths that bypass its normal footer. [Early-return paths](astra5/job26/P/interpretation.txt) · [Observed range](astra5/job26/audit/M/summary.json)

## Pre-commit working tree and evidence files

```text
$ git status --short && ls -R forge-combo29/astra5/job26
 A forge-combo29/REPORT_astra5_job26.md
M  forge-combo29/astra5/job26/stamps.txt
forge-combo29/astra5/job26:
KP0
KP1
P
audit
build.txt
games
kp1-qa
nodeclock_r15d.patch.txt
prediction.txt
stamps.txt
step0

forge-combo29/astra5/job26/KP0:
b
c
check_depth.py
check_pins.py
check_replay.py
nc

forge-combo29/astra5/job26/KP0/b:
G
O

forge-combo29/astra5/job26/KP0/b/G:
comparison.txt
rows.tsv
uci.log

forge-combo29/astra5/job26/KP0/b/O:
comparison.txt
rows.tsv
uci.log

forge-combo29/astra5/job26/KP0/c:
comparison.txt
raw-last
results

forge-combo29/astra5/job26/KP0/c/raw-last:
K23-1.txt

forge-combo29/astra5/job26/KP0/c/results:
K23-1

forge-combo29/astra5/job26/KP0/c/results/K23-1:
games.tsv
no-info.tsv
openings.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job26/KP0/nc:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt

forge-combo29/astra5/job26/KP1:
A0
A1
B0
C0
CP1
O0
run_kp1.py

forge-combo29/astra5/job26/KP1/A0:
over.tsv
rows.txt
run.meta
searches.tsv
summary.txt
uci.log

forge-combo29/astra5/job26/KP1/A1:
over.tsv
rows.txt
run.meta
searches.tsv
summary.txt
uci.log

forge-combo29/astra5/job26/KP1/B0:
over.tsv
rows.txt
run.meta
searches.tsv
summary.txt
uci.log

forge-combo29/astra5/job26/KP1/C0:
over.tsv
rows.txt
run.meta
searches.tsv
summary.txt
uci.log

forge-combo29/astra5/job26/KP1/CP1:
over.tsv
rows.txt
run.meta
searches.tsv
summary.txt
uci.log

forge-combo29/astra5/job26/KP1/O0:
over.tsv
rows.txt
run.meta
searches.tsv
summary.txt
uci.log

forge-combo29/astra5/job26/P:
apply.txt
build.txt
changes.txt
interpretation.txt
r15d-source-check.txt
uci.txt

forge-combo29/astra5/job26/audit:
C26
K26-1
K26-2
M
M-checkpoint-106
M-checkpoint-65
audit_games.py
check_clocks.py
check_job21.py
clock-correction.txt
controls-independent.json
controls.py
final-checks.txt
job21-known-answers.txt
method.txt
reader-selfcheck.txt
retry_c26.py
stats_seed.py
test_reader.py

forge-combo29/astra5/job26/audit/C26:
attempt1-vs-repeat.tsv
attempt1-vs-repeat.txt
clock-conservation.txt
game-readback.tsv
paired-ends.tsv
summary.json
time-losses.tsv

forge-combo29/astra5/job26/audit/K26-1:
clock-conservation.txt
game-readback.tsv
paired-ends.tsv
summary.json
time-losses.tsv

forge-combo29/astra5/job26/audit/K26-2:
clock-conservation.txt
game-readback.tsv
paired-ends.tsv
summary.json
time-losses.tsv

forge-combo29/astra5/job26/audit/M:
clock-conservation.txt
game-readback.tsv
paired-ends.tsv
summary.json
time-losses.tsv

forge-combo29/astra5/job26/audit/M-checkpoint-106:
clock-conservation.txt
game-readback.tsv
paired-ends.tsv
summary.json
time-losses.tsv

forge-combo29/astra5/job26/audit/M-checkpoint-65:
clock-conservation.txt
game-readback.tsv
paired-ends.tsv
summary.json
time-losses.tsv

forge-combo29/astra5/job26/games:
C26
C26-attempt1
C26-repeat-process.log
K26-1
K26-2
M
game26.py
reconnect-note.txt
stage26.py

forge-combo29/astra5/job26/games/C26:
compare.json
end.json
g0001
g0002
g0003
g0004
g0005
g0006
g0007
g0008
g0009
g0010
g0011
g0012
g0013
g0014
g0015
g0016
g0017
g0018
g0019
g0020
games.tsv
inputs.json
launch.tsv
pair-001.tsv
pair-002.tsv
pair-003.tsv
pair-004.tsv
pair-005.tsv
pair-006.tsv
pair-007.tsv
pair-008.tsv
pair-009.tsv
pair-010.tsv
pairs.tsv

forge-combo29/astra5/job26/games/C26/g0001:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0002:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0003:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0004:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0005:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0006:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0007:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0008:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0009:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0010:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0011:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0012:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0013:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0014:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0015:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0016:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0017:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0018:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0019:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26/g0020:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1:
end.json
g0001
g0002
g0003
g0004
g0005
g0006
g0007
g0008
g0009
g0010
g0011
g0012
g0013
g0014
g0015
g0016
g0017
g0018
g0019
g0020
games.tsv
inputs.json
launch.tsv
pairs.tsv
stop.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0001:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0002:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0003:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0004:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0005:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0006:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0007:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0008:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0009:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0010:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0011:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0012:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0013:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0014:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0015:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0016:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0017:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0018:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0019:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/C26-attempt1/g0020:
engines.json
interruption.txt
opening.txt
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1:
end.json
g0001
g0002
g0003
g0004
g0005
g0006
g0007
g0008
g0009
g0010
g0011
g0012
g0013
g0014
g0015
g0016
g0017
g0018
g0019
g0020
games.tsv
inputs.json
launch.tsv
pair-001.tsv
pair-002.tsv
pair-003.tsv
pair-004.tsv
pair-005.tsv
pair-006.tsv
pair-007.tsv
pair-008.tsv
pair-009.tsv
pair-010.tsv
pairs.tsv

forge-combo29/astra5/job26/games/K26-1/g0001:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0002:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0003:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0004:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0005:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0006:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0007:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0008:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0009:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0010:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0011:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0012:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0013:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0014:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0015:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0016:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0017:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0018:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0019:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-1/g0020:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2:
compare.json
end.json
g0001
g0002
g0003
g0004
g0005
g0006
g0007
g0008
g0009
g0010
g0011
g0012
g0013
g0014
g0015
g0016
g0017
g0018
g0019
g0020
games.tsv
inputs.json
launch.tsv
pair-001.tsv
pair-002.tsv
pair-003.tsv
pair-004.tsv
pair-005.tsv
pair-006.tsv
pair-007.tsv
pair-008.tsv
pair-009.tsv
pair-010.tsv
pairs.tsv

forge-combo29/astra5/job26/games/K26-2/g0001:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0002:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0003:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0004:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0005:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0006:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0007:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0008:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0009:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0010:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0011:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0012:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0013:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0014:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0015:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0016:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0017:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0018:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0019:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/K26-2/g0020:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M:
end.json
g0021
g0022
g0023
g0024
g0025
g0026
g0027
g0028
g0029
g0030
g0031
g0032
g0033
g0034
g0035
g0036
g0037
g0038
g0039
g0040
g0041
g0042
g0043
g0044
g0045
g0046
g0047
g0048
g0049
g0050
g0051
g0052
g0053
g0054
g0055
g0056
g0057
g0058
g0059
g0060
g0061
g0062
g0063
g0064
g0065
g0066
g0067
g0068
g0069
g0070
g0071
g0072
g0073
g0074
g0075
g0076
g0077
g0078
g0079
g0080
g0081
g0082
g0083
g0084
g0085
g0086
g0087
g0088
g0089
g0090
g0091
g0092
g0093
g0094
g0095
g0096
g0097
g0098
g0099
g0100
g0101
g0102
g0103
g0104
g0105
g0106
g0107
g0108
g0109
g0110
g0111
g0112
g0113
g0114
g0115
g0116
g0117
g0118
g0119
g0120
g0121
g0122
g0123
g0124
g0125
g0126
g0127
g0128
g0129
g0130
g0131
g0132
g0133
g0134
g0135
g0136
g0137
g0138
g0139
g0140
g0141
g0142
g0143
g0144
g0145
g0146
g0147
g0148
g0149
g0150
g0151
g0152
g0153
g0154
g0155
g0156
g0157
g0158
g0159
g0160
g0161
g0162
g0163
g0164
g0165
g0166
g0167
g0168
g0169
g0170
g0171
g0172
g0173
g0174
g0175
g0176
g0177
g0178
g0179
g0180
g0181
g0182
g0183
g0184
g0185
g0186
g0187
g0188
g0189
g0190
g0191
g0192
g0193
g0194
g0195
g0196
g0197
g0198
g0199
g0200
g0201
g0202
g0203
g0204
g0205
g0206
g0207
g0208
g0209
g0210
g0211
g0212
g0213
g0214
g0215
g0216
g0217
g0218
g0219
g0220
g0221
g0222
g0223
g0224
g0225
g0226
g0227
g0228
g0229
g0230
g0231
g0232
g0233
g0234
g0235
g0236
g0237
g0238
g0239
g0240
g0241
g0242
g0243
g0244
g0245
g0246
g0247
g0248
g0249
g0250
g0251
g0252
g0253
g0254
g0255
g0256
g0257
g0258
g0259
g0260
g0261
g0262
g0263
g0264
g0265
g0266
g0267
g0268
g0269
g0270
g0271
g0272
g0273
g0274
g0275
g0276
g0277
g0278
g0279
g0280
g0281
g0282
g0283
g0284
g0285
g0286
g0287
g0288
g0289
g0290
g0291
g0292
g0293
g0294
g0295
g0296
g0297
g0298
g0299
g0300
g0301
g0302
g0303
g0304
g0305
g0306
g0307
g0308
g0309
g0310
g0311
g0312
g0313
g0314
g0315
g0316
g0317
g0318
g0319
g0320
g0321
g0322
g0323
g0324
g0325
g0326
g0327
g0328
g0329
g0330
g0331
g0332
g0333
g0334
g0335
g0336
g0337
g0338
games.tsv
inputs.json
launch.tsv
pair-011.tsv
pair-012.tsv
pair-013.tsv
pair-014.tsv
pair-015.tsv
pair-016.tsv
pair-017.tsv
pair-018.tsv
pair-019.tsv
pair-020.tsv
pair-021.tsv
pair-022.tsv
pair-023.tsv
pair-024.tsv
pair-025.tsv
pair-026.tsv
pair-027.tsv
pair-028.tsv
pair-029.tsv
pair-030.tsv
pair-031.tsv
pair-032.tsv
pair-033.tsv
pair-034.tsv
pair-035.tsv
pair-036.tsv
pair-037.tsv
pair-038.tsv
pair-039.tsv
pair-040.tsv
pair-041.tsv
pair-042.tsv
pair-043.tsv
pair-044.tsv
pair-045.tsv
pair-046.tsv
pair-047.tsv
pair-048.tsv
pair-049.tsv
pair-050.tsv
pair-051.tsv
pair-052.tsv
pair-053.tsv
pair-054.tsv
pair-055.tsv
pair-056.tsv
pair-057.tsv
pair-058.tsv
pair-059.tsv
pair-060.tsv
pair-061.tsv
pair-062.tsv
pair-063.tsv
pair-064.tsv
pair-065.tsv
pair-066.tsv
pair-067.tsv
pair-068.tsv
pair-069.tsv
pair-070.tsv
pair-071.tsv
pair-072.tsv
pair-073.tsv
pair-074.tsv
pair-075.tsv
pair-076.tsv
pair-077.tsv
pair-078.tsv
pair-079.tsv
pair-080.tsv
pair-081.tsv
pair-082.tsv
pair-083.tsv
pair-084.tsv
pair-085.tsv
pair-086.tsv
pair-087.tsv
pair-088.tsv
pair-089.tsv
pair-090.tsv
pair-091.tsv
pair-092.tsv
pair-093.tsv
pair-094.tsv
pair-095.tsv
pair-096.tsv
pair-097.tsv
pair-098.tsv
pair-099.tsv
pair-100.tsv
pair-101.tsv
pair-102.tsv
pair-103.tsv
pair-104.tsv
pair-105.tsv
pair-106.tsv
pair-107.tsv
pair-108.tsv
pair-109.tsv
pair-110.tsv
pair-111.tsv
pair-112.tsv
pair-113.tsv
pair-114.tsv
pair-115.tsv
pair-116.tsv
pair-117.tsv
pair-118.tsv
pair-119.tsv
pair-120.tsv
pair-121.tsv
pair-122.tsv
pair-123.tsv
pair-124.tsv
pair-125.tsv
pair-126.tsv
pair-127.tsv
pair-128.tsv
pair-129.tsv
pair-130.tsv
pair-131.tsv
pair-132.tsv
pair-133.tsv
pair-134.tsv
pair-135.tsv
pair-136.tsv
pair-137.tsv
pair-138.tsv
pair-139.tsv
pair-140.tsv
pair-141.tsv
pair-142.tsv
pair-143.tsv
pair-144.tsv
pair-145.tsv
pair-146.tsv
pair-147.tsv
pair-148.tsv
pair-149.tsv
pair-150.tsv
pair-151.tsv
pair-152.tsv
pair-153.tsv
pair-154.tsv
pair-155.tsv
pair-156.tsv
pair-157.tsv
pair-158.tsv
pair-159.tsv
pair-160.tsv
pair-161.tsv
pair-162.tsv
pair-163.tsv
pair-164.tsv
pair-165.tsv
pair-166.tsv
pair-167.tsv
pair-168.tsv
pair-169.tsv
pairs.tsv
process.log

forge-combo29/astra5/job26/games/M/g0021:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0022:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0023:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0024:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0025:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0026:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0027:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0028:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0029:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0030:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0031:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0032:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0033:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0034:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0035:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0036:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0037:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0038:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0039:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0040:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0041:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0042:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0043:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0044:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0045:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0046:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0047:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0048:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0049:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0050:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0051:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0052:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0053:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0054:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0055:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0056:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0057:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0058:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0059:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0060:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0061:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0062:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0063:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0064:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0065:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0066:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0067:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0068:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0069:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0070:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0071:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0072:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0073:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0074:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0075:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0076:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0077:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0078:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0079:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0080:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0081:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0082:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0083:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0084:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0085:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0086:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0087:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0088:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0089:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0090:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0091:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0092:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0093:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0094:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0095:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0096:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0097:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0098:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0099:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0100:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0101:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0102:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0103:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0104:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0105:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0106:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0107:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0108:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0109:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0110:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0111:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0112:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0113:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0114:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0115:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0116:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0117:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0118:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0119:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0120:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0121:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0122:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0123:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0124:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0125:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0126:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0127:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0128:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0129:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0130:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0131:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0132:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0133:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0134:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0135:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0136:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0137:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0138:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0139:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0140:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0141:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0142:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0143:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0144:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0145:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0146:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0147:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0148:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0149:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0150:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0151:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0152:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0153:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0154:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0155:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0156:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0157:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0158:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0159:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0160:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0161:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0162:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0163:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0164:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0165:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0166:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0167:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0168:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0169:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0170:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0171:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0172:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0173:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0174:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0175:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0176:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0177:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0178:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0179:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0180:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0181:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0182:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0183:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0184:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0185:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0186:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0187:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0188:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0189:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0190:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0191:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0192:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0193:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0194:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0195:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0196:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0197:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0198:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0199:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0200:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0201:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0202:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0203:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0204:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0205:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0206:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0207:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0208:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0209:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0210:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0211:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0212:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0213:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0214:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0215:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0216:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0217:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0218:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0219:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0220:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0221:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0222:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0223:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0224:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0225:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0226:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0227:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0228:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0229:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0230:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0231:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0232:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0233:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0234:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0235:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0236:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0237:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0238:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0239:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0240:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0241:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0242:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0243:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0244:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0245:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0246:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0247:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0248:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0249:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0250:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0251:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0252:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0253:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0254:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0255:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0256:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0257:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0258:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0259:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0260:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0261:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0262:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0263:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0264:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0265:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0266:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0267:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0268:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0269:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0270:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0271:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0272:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0273:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0274:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0275:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0276:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0277:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0278:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0279:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0280:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0281:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0282:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0283:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0284:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0285:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0286:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0287:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0288:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0289:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0290:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0291:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0292:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0293:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0294:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0295:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0296:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0297:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0298:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0299:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0300:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0301:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0302:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0303:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0304:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0305:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0306:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0307:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0308:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0309:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0310:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0311:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0312:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0313:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0314:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0315:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0316:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0317:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0318:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0319:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0320:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0321:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0322:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0323:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0324:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0325:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0326:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0327:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0328:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0329:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0330:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0331:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0332:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0333:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0334:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0335:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0336:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0337:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/games/M/g0338:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job26/kp1-qa:
A0-audit.txt
A1-audit.txt
B0-audit.txt
C0-audit.txt
CP1-audit.txt
O0-audit.txt
check_single.py
paired-moves.tsv

forge-combo29/astra5/job26/step0:
build.txt
dataset-sources.txt
pc20.txt
r15d

forge-combo29/astra5/job26/step0/r15d:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
```
