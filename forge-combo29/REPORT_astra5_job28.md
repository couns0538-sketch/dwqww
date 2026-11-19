# Job 28 · Forge’s finish rule and soft time divisor

## 1. Step 0 passed

The host reported `nproc 5`. The Job 26 binary had SHA-256 `9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3`. Five fresh processes reproduced 312,866 and 862,329 nodes at default bench depths 11 and 13, 4,865,609 leaves at perft depth 5, and 882,074 and 4,275,906 bench nodes under PC20 with net768. A fresh A0 replay at NodeClock 1000 reproduced the Job 26 row signature `424d931234dd3ff9` and total charge **98,026 node-ms**. [Build and host](astra5/job28/build.txt) · [Five pins](astra5/job28/step0/nc/checks.txt) · [A0 replay](astra5/job28/step0/A0/summary.txt)

The new A0 rows, per-search table, interrupted-iteration table and summary equal the corresponding files in both Jobs 26 and 27 byte for byte. [Cross-job file checks](astra5/job28/step0/A0/prior-jobs-compare.txt)

## 2. Controls against the PC

Each row covers the first 20 searches from the starting position. The hash covers each ply number, stopped-node count and best move, with one space between fields and one LF after each row. [Six comparisons and first-three-row checks](astra5/job28/controls/K28/comparison.tsv)

| Pair | A settings, in option order | A's color | Measured SHA prefix | PC SHA prefix | Measured ΣN | PC ΣN |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | TmFinishIteration on, TmSoftDivisor 20 | White | `f49482fe2b9738aa` | `f49482fe2b9738aa` | 470,764 | 470,764 |
| 1 | TmFinishIteration on, TmSoftDivisor 20 | Black | `749f902e91070fc2` | `749f902e91070fc2` | 507,873 | 507,873 |
| 2 | TmSoftDivisor 16 | White | `f7dc1451fef2f337` | `f7dc1451fef2f337` | 583,536 | 583,536 |
| 2 | TmSoftDivisor 16 | Black | `af5f929dd8c03cc2` | `af5f929dd8c03cc2` | 551,293 | 551,293 |
| 3 | TmSoftDivisor 30 | White | `fb0a79e5c1ffcd06` | `fb0a79e5c1ffcd06` | 433,827 | 433,827 |
| 3 | TmSoftDivisor 30 | Black | `749f902e91070fc2` | `749f902e91070fc2` | 507,873 | 507,873 |

K28 passed all six SHA, node-sum and first-three-row checks. With A as White, the clocks after plies 19 and 20 were 3,290 for White and 4,084 for Black in pair 2, and 4,661 and 4,211 in pair 3. Both pairs reproduce the PC’s clock values. [Clock checks](astra5/job28/controls/K28/gate.json)

The **first 20 search rows** matched byte for byte in three historical comparisons. Pair 1 game 1 matched K27 pair 1 game 1 over those 20 rows. Both pair 1 game 2 and pair 3 game 2 matched the first 20 rows of K27 pair 2 game 2. In the color-matched divisor comparison, the first 20 rows of pair 1 game 2 differed from K27 pair 1 game 2. [Independent cross-job row checks](astra5/job28/audit/K28-independent.json)

The earliest claimable repetition was in game 4 after 57 applied plies. The side to move could announce `b8d8` on ply 58. The first 20 searches therefore finish before the draw-claim convention can affect any of the six checks. [First claimable plies](astra5/job28/audit/K28-first-claim.tsv)

C28 passed. Setting A’s divisor explicitly to B’s default of 22 produced 20 opening rows with SHA prefix `492d271d43b7ce03` and 485,583 nodes (PC `492d271d43b7ce03`, 485,583). The corresponding divisor-16 row set had prefix `f7dc1451fef2f337`. C28 is excluded from the match scores. [Explicit-default control](astra5/job28/controls/C28/comparison.tsv)

## 3. Frozen prediction

Commit `c60f7a142f61` froze the predictions after the controls and before the first match game. [Frozen prediction](astra5/job28/prediction.txt) · [Commit and first game receipts](astra5/job28/audit/prediction-sequence.txt)

| Quantity | Prediction | Observed | Grade |
| --- | --- | --- | --- |
| M4 Elo | -22 to 12 | -10.41 | Inside |
| M4 reading | LEVEL | LEVEL | Correct |
| M5 Elo | -18 to 20 | -14.82 | Inside |
| M5 reading | LEVEL | B BETTER | Miss |
| M6 Elo | -24 to 8 | -14.42 | Inside |
| M6 reading | LEVEL | B BETTER | Miss |
| Time losses across counted matches | 0 to 4 | 0 | Inside |
| Complete common blocks by minute 45 | 8 to 9 | 9 | Inside |

## 4. The three matches

Each opening contributed two color-reversed games per match. A applied the settings in the table. B used the common defaults, finish rule off and divisor 22. The five bins count openings on which A scored 0, ½, 1, 1½ or 2 points out of two. Elo and its 95% interval use the Job 26 paired calculation. [Independent score and clock totals](astra5/job28/audit/final/independent.json) · [Replay and interval method](astra5/job28/audit/method28.txt)

| Match | A setting | Pairs | A W–L–D | Pentanomial | A Elo | 95% interval | Time losses | Mean used A / B | A searches with hold / total | Mean end clock A / B | Peak simultaneous games in this arm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M4 | TmFinishIteration on, TmSoftDivisor 20 | 434 | 160–186–522 | 10 / 120 / 199 / 96 / 9 | -10.41 | [-23.80, +2.98] | 0 | 138.49 / 145.44 | 20,972 / 53,868 | 1,129.04 / 698.01 | 4 |
| M5 | TmSoftDivisor 16 | 434 | 141–178–549 | 14 / 109 / 223 / 76 / 12 | -14.82 | [-28.11, -1.52] | 0 | 149.61 / 145.55 | — | 479.39 / 728.37 | 4 |
| M6 | TmSoftDivisor 30 | 434 | 144–180–544 | 13 / 114 / 210 / 90 / 7 | -14.42 | [-27.60, -1.24] | 0 | 141.32 / 146.97 | — | 1,080.22 / 736.47 | 4 |

Mean used and end clocks are in node-ms. A hold counts once per search containing at least one `TmFinishIteration hold` line. A completed search spends its final N divided by 100, rounded down. The runner started both clocks at 6,000 and awarded 60 after each move that fit the clock.

| Independently replayed ending | M4 | M5 | M6 |
| --- | --- | --- | --- |
| Checkmate | 346 | 319 | 324 |
| Stalemate | 2 | 1 | 2 |
| Insufficient material | 41 | 44 | 40 |
| Claimable threefold repetition | 470 | 498 | 497 |
| Claimable fifty-move rule | 9 | 6 | 5 |
| Time | 0 | 0 | 0 |
| 600-ply cap | 0 | 0 | 0 |

Mean final clocks by color (White / Black, node-ms) were M4 924.02 / 903.03, M5 608.42 / 599.34, M6 902.22 / 914.47. [Clocks by color and engine](astra5/job28/audit/final/independent.json)

**TIME LOSSES** 0 in the counted matches.

## 5. Declared readings

**M4 LEVEL** · **M5 B BETTER** · **M6 B BETTER**. A BETTER requires a lower bound above zero. B BETTER requires an upper bound below zero. Every interval that includes zero reads LEVEL.

For each shared opening, subtract A’s pair score in the second match from A’s pair score in the first. Each score is on a 0-to-2-point scale. The 95% interval uses the sample SD of the paired differences divided by the square root of the number of openings, with the two-sided normal multiplier. The independent width uses each match’s own pair-score variance on those same openings and treats the covariance as zero. Both widths are full lower-to-upper distances. [One row per opening](astra5/job28/comparisons/per_opening.tsv) · [Descriptive statistics](astra5/job28/comparisons/comparisons.tsv)

| Comparison | Shared openings | Mean difference | SD of differences | 95% interval of mean | Paired width | Independent width |
| --- | --- | --- | --- | --- | --- | --- |
| M4-M1 | 434 | -0.0138 | 0.5446 | [-0.0651, +0.0374] | 0.1025 | 0.1062 |
| M5-M6 | 434 | -0.0012 | 0.5442 | [-0.0524, +0.0500] | 0.1024 | 0.1076 |

Playing the same openings made M4-M1 narrower by 0.0038 pair points (3.53%) and M5-M6 narrower by 0.0052 pair points (4.87%).

**M4 READS AS M1** — M4 LEVEL [-23.80, +2.98] Elo · Job 27 M1 LEVEL [-18.30, +7.09] Elo. [Historical M1 score and pair source](astra5/job28/comparisons/source.txt)

## Facts

All three matches used Job 27’s ordered 434-opening L27 file, SHA-256 `271cea0cd131935998b72aeee5e6bda336f8bea8f48bcf060088895f1765b21c`. The common score covers 9 of 9 blocks, blocks 1–9 and openings 1–434. 9 common blocks finished by minute 45. The runner exhausted L27. [L27 identity and cross-job check](astra5/job28/build.txt) · [Per-block eligibility and timing](astra5/job28/audit/final/stages-independent.tsv)

The runner completed each block in M4, M5, M6 order on the same openings before advancing. The controls ran one game at a time. In matches, up to four games ran side by side on a host with five available CPUs. The operating system placed the processes. Each game used two fresh one-thread processes sharing that game’s turn, so only one color searched at a time. Arms ran one after another. [Control configuration](astra5/job28/controls/K28/inputs.json) · [Match CPU allocation](astra5/job28/matches/run.json)

The independent reader replayed 2,604 counted games with python-chess, checking move legality, both clocks and the terminal position. A charge exceeding the mover’s remaining clock lost on time. A game also ended at mate, stalemate, insufficient material, claimable threefold repetition or 50 moves, or the 600-ply cap. [Replayed scores, endings and clock balances](astra5/job28/audit/final/independent.json) · [Independent replay procedure](astra5/job28/audit/method28.txt)

The work budget began when the assignment was read at 22:14:52 UTC. The claim followed at 22:14:59 UTC. The runner used the earlier timestamp for its minute-45 and minute-50 limits, seven seconds before the corresponding claim-based limits. [Timing convention](astra5/job28/timing-provenance.txt) · [Enforced cutoffs](astra5/job28/matches/run.json)

Every opening was played in all three matches. [End-of-run receipt](astra5/job28/matches/schedule-end.json)

## Suspicions

With the finish rule on, A used 138.49 node-ms per search at divisor 20, compared with 136.62 in Job 27 at divisor 22 (+1.87 node-ms). Its mean final balance was 1,129.04 versus 1,301.07 node-ms (-172.03). These M4 and M1 averages cover 434 and 434 opening pairs respectively. A lower divisor increases the soft time allocation on a given turn. The two means also reflect the different positions and clock balances each setting reached. [M4 search charges and clocks](astra5/job28/audit/final/independent.json) · [Job 27 M1 search charges and clocks](astra5/job27/audit/final/independent.json)

## What I did not do

The assignment sets the following limits.

> the PC's net and build (the built-in evaluation plays here); the wall clock; NodeClock values other than 100; divisors other than 16, 20 and 30; the other nine numbers of the time model; more than one thread; time controls other than 6000 + 60; a difference smaller than the interval the played pairs give.

## What I am not sure about

A hold records the decision to stop after a completed iteration. The totals do not identify which later search used a particular saving or which hold changed an outcome. The per-opening differences measure scores against the common B on these openings. A direct head-to-head match between the settings would answer a different question. [Opening-matched differences](astra5/job28/comparisons/per_opening.tsv)

## Pre-commit working tree and evidence files

```text
$ git status --short && ls -R forge-combo29/astra5/job28
 A forge-combo29/REPORT_astra5_job28.md
M  forge-combo29/astra5/job28/stamps.txt
forge-combo29/astra5/job28:
audit
build.txt
comparisons
controls
crosscheck
driver
matches
prediction.txt
reference.txt
stamps.txt
step0
timing-provenance.txt

forge-combo29/astra5/job28/audit:
C28-independent.json
C28-independent.tsv
K28-first-claim.tsv
K28-independent.json
K28-independent.tsv
bind_archive.py
checked-compact
checkpoints
compact-progress.log
compact28.py
final
final-checks.txt
gates28.py
method28.txt
prediction-sequence.txt
replay28.py
score28.py
stage-summaries
stage28.py
stats_seed.py
verify_penta.py
verify_quit.py

forge-combo29/astra5/job28/audit/checked-compact:
final-agreement.txt

forge-combo29/astra5/job28/audit/checkpoints:
common-01.json
common-02.json
common-03.json
common-04.json
common-05.json
common-06.json
common-07.json
common-08.json
common-09.json

forge-combo29/astra5/job28/audit/final:
M4-pairs.tsv
M5-pairs.tsv
M6-pairs.tsv
blocks-independent.tsv
git-archive-binding.txt
independent.json
penta-independent.txt
prediction-independent.txt
shutdowns-independent.txt
stages-independent.tsv
time-losses.tsv

forge-combo29/astra5/job28/audit/stage-summaries:
block001
block002
block003
block004
block005
block006
block007
block008
block009

forge-combo29/astra5/job28/audit/stage-summaries/block001:
M4.json
M5.json
M6.json

forge-combo29/astra5/job28/audit/stage-summaries/block002:
M4.json
M5.json
M6.json

forge-combo29/astra5/job28/audit/stage-summaries/block003:
M4.json
M5.json
M6.json

forge-combo29/astra5/job28/audit/stage-summaries/block004:
M4.json
M5.json
M6.json

forge-combo29/astra5/job28/audit/stage-summaries/block005:
M4.json
M5.json
M6.json

forge-combo29/astra5/job28/audit/stage-summaries/block006:
M4.json
M5.json
M6.json

forge-combo29/astra5/job28/audit/stage-summaries/block007:
M4.json
M5.json
M6.json

forge-combo29/astra5/job28/audit/stage-summaries/block008:
M4.json
M5.json
M6.json

forge-combo29/astra5/job28/audit/stage-summaries/block009:
M4.json
M5.json
M6.json

forge-combo29/astra5/job28/comparisons:
compare28.py
comparison-table.md
comparisons.tsv
input-hashes.tsv
method.txt
moment-check.json
per_opening.tsv
source.txt

forge-combo29/astra5/job28/controls:
C28
K28

forge-combo29/astra5/job28/controls/C28:
comparison.tsv
controller.log
first20-g0003.txt
g0003
games.tsv
gate.json
inputs.json

forge-combo29/astra5/job28/controls/C28/g0003:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job28/controls/K28:
comparison.tsv
controller.log
first20-g0001.txt
first20-g0002.txt
first20-g0003.txt
first20-g0004.txt
first20-g0005.txt
first20-g0006.txt
g0001
g0002
g0003
g0004
g0005
g0006
games.tsv
gate.json
inputs.json

forge-combo29/astra5/job28/controls/K28/g0001:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job28/controls/K28/g0002:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job28/controls/K28/g0003:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job28/controls/K28/g0004:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job28/controls/K28/g0005:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job28/controls/K28/g0006:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job28/crosscheck:
contrasts28.py
flag-and-equality.tsv
input-sha256.tsv
pair-check.txt
pair-contrast-inputs.tsv
pair-contrast-points.tsv
pair-contrast-statistics.tsv
recount.txt
recount28.py

forge-combo29/astra5/job28/driver:
controls28.py
game28.py
holds28.py
pack_arm28.py
schedule28.py

forge-combo29/astra5/job28/matches:
block001
block002
block003
block004
block005
block006
block007
block008
block009
events.jsonl
run.json
schedule-end.json
scheduler.log

forge-combo29/astra5/job28/matches/block001:
M4
M5
M6
receipt.json

forge-combo29/astra5/job28/matches/block001/M4:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block001/M4/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block001/M5:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block001/M5/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block001/M6:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block001/M6/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block002:
M4
M5
M6
receipt.json

forge-combo29/astra5/job28/matches/block002/M4:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block002/M4/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block002/M5:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block002/M5/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block002/M6:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block002/M6/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block003:
M4
M5
M6
receipt.json

forge-combo29/astra5/job28/matches/block003/M4:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block003/M4/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block003/M5:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block003/M5/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block003/M6:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block003/M6/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block004:
M4
M5
M6
receipt.json

forge-combo29/astra5/job28/matches/block004/M4:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block004/M4/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block004/M5:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block004/M5/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block004/M6:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block004/M6/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block005:
M4
M5
M6
receipt.json

forge-combo29/astra5/job28/matches/block005/M4:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block005/M4/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block005/M5:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block005/M5/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block005/M6:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block005/M6/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block006:
M4
M5
M6
receipt.json

forge-combo29/astra5/job28/matches/block006/M4:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block006/M4/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block006/M5:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block006/M5/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block006/M6:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block006/M6/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block007:
M4
M5
M6
receipt.json

forge-combo29/astra5/job28/matches/block007/M4:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block007/M4/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block007/M5:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block007/M5/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block007/M6:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block007/M6/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block008:
M4
M5
M6
receipt.json

forge-combo29/astra5/job28/matches/block008/M4:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block008/M4/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block008/M5:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block008/M5/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block008/M6:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block008/M6/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block009:
M4
M5
M6
receipt.json

forge-combo29/astra5/job28/matches/block009/M4:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block009/M4/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block009/M5:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block009/M5/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/matches/block009/M6:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job28/matches/block009/M6/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job28/step0:
A0
nc

forge-combo29/astra5/job28/step0/A0:
over.tsv
prior-jobs-compare.txt
rows.txt
run.meta
searches.tsv
summary.txt
uci.log

forge-combo29/astra5/job28/step0/nc:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
```
