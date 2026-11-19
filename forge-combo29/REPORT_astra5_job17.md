# Astra5 job 17 — whole-game records at the gate and confirmation node limits

## 1. Step 0 — build identities, slots and known answers

Both unguarded job 16 executables passed all seven fresh-process checks. `nproc` returned 5. Each build used **S = 2** fixed slots. A slot kept one White engine and one Black engine for the run, each single-threaded. This gives at most 4 simultaneously searching engines across the two builds. [Binary, net and slot identities](astra5/job17/step0/gates/identities.txt)

| Build | Executable SHA-256 |
| --- | --- |
| r15d | `9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671` |
| kF | `c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb` |

The synthetic net768 SHA-256 was `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. Both builds reported `NNUE v3 active` with checksum `30ab43b4ba5db5f3` in the net-enabled checks. The unchanged executables used C++20, `-O3 -ffp-contract=off -fno-fast-math -march=native` and the defines `FORGE_EXPOSE_TUNABLES=1`, `FORGE_NNUE_HIDDEN=256`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_NNUE_ZMM=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SPD_PREFETCH_EARLY=1`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_TT_NOTLS=1`, `FORGE_MATE_ALPHA_GUARD=1`, `FORGE_NNUE_V3=1`, `NDEBUG`. The generated `FORGE_NNUE_WEIGHTS` pointed into each build’s source tree. The compiler exposed `__AVX512F__`, `__AVX512BW__` and `__BMI2__`. [Job 16 r15d flags](astra5/job16/step0/base/build.txt) · [kF compiler and provenance](astra5/job16/step0/kf/kF-provenance.txt)

| Evaluation and options | Command | r15d nodes | kF nodes |
| --- | --- | --- | --- |
| defaults | `bench 11` | 312,866 | 312,866 |
| defaults | `bench 13` | 862,329 | 862,329 |
| defaults | `go perft 5` | 4,865,609 | 4,865,609 |
| PC20 | `bench 11` | 278,024 | 278,024 |
| PC20 | `bench 13` | 587,276 | 587,276 |
| PC20 + net768 | `bench 11` | 882,074 | 882,074 |
| PC20 + net768 | `bench 13` | 4,275,906 | 4,275,906 |

[r15d gate transcript](astra5/job17/step0/gates/r15d/checks.txt) · [kF gate transcript](astra5/job17/step0/gates/kF/checks.txt)

## 2. K17 and C17 — repeatability and sensitivity

On book lines 3401–3410, two r15d runs with `go nodes 50000` produced byte-identical records. Changing only `LmrQuietBase` from 93 to 60 in C17 produced differences on 10 of 10 openings. The first difference was on book line 3401, played ply 1. All three arms used PC20 with the indicated LMR value, net768, Threads 1 and Hash 16 MiB. [K17 independent audit](astra5/job17/audit/K17/summary.txt) · [C17 independent audit](astra5/job17/audit/C17/summary.txt)

| Arm | Games | Ply records | NA records | Sum of numeric nodes | SHA-256 of records |
| --- | --- | --- | --- | --- | --- |
| K17-1 | 10 | 728 | 0 | 22,804,439 | `a032365e12fdfc92f48a9c4e50c65fce7330cd1c677f2b184126d4fe2787b2fc` |
| K17-2 | 10 | 728 | 0 | 22,804,439 | `a032365e12fdfc92f48a9c4e50c65fce7330cd1c677f2b184126d4fe2787b2fc` |
| C17 | 10 | 806 | 0 | 25,563,612 | `cadc9a5b5ffe5523b9d817d9c723675fba59831d7518b2e46f1b599535d30df8` |

```text
K17  3401 1 g1h1 11928
C17  3401 1 g1h1 13090
```

## 3. Frozen prediction

> G1: I predict 0 of the 200 games will differ between r15d and kF, with a range of 0 to 2 games. I predict that the complete node columns will be equal, including any NA entries.
> I predict 0 NA records for r15d and 0 NA records for kF. With 50,000 nodes available per move, I expect a completed iteration to print an info line before almost every stop. The clean soft-node comparisons in job 16 support the game forecast, while the hard limit and separate engine histories leave room for uncertainty.

[Frozen prediction](astra5/job17/prediction.txt) · [Prediction-only commit](https://github.com/couns0538-sketch/dwqww/commit/c10d5ee3011a22d141ee372a35a1f44c27f255ae)

| Forecast item | Frozen prediction | Observed | Grade |
| --- | --- | --- | --- |
| G1 games with different records | 0 games, range 0–2 | 0 | Point hit, inside range |
| G1 node columns, including NA | Equal | Equal | Hit |
| G1 r15d NA records | 0 | 0 | Hit |
| G1 kF NA records | 0 | 0 | Hit |

## 4. G1 and G2 — hard-node results

PC20, net768, Threads 1, Hash 16 MiB and OwnBook false were common to all arms. Each slot retained its two processes across its assigned openings. With 2 slots, slot 1 played the first opening and every other opening after it. Slot 2 played the intervening openings. Before each game both engines received `ucinewgame` and acknowledged `isready`. For each ply only the moving side received the opening FEN, accumulated UCI moves and the search command. Games ended on a rules outcome with draw claims enabled or after 300 plies. [Two-process driver](astra5/job17/selfplay.py)

Each sorted row contains book line, played ply, best move and the node count from the last info line. `NA` records a best move with no preceding info line in that search. The numeric sums omit those rows. Under a hard cap the last reported info count can precede the final stop, so these sums describe the logged counts.

| Run | Build | Node limit | Completed games | Ply records | NA records | Sum of numeric nodes | SHA-256 of records |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | r15d | 50,000 | 200/200 | 18,616 | 0 | 581,994,913 | `7b9b5b93ec51161c7e3daedd25e9937bf5932a1661db59d0a10517f1a786a96e` |
| G1 | kF | 50,000 | 200/200 | 18,616 | 0 | 581,994,913 | `7b9b5b93ec51161c7e3daedd25e9937bf5932a1661db59d0a10517f1a786a96e` |
| G2 | r15d | 250,000 | 40/40 | 3,289 | 0 | 526,599,769 | `dff0630c12ad2549f22405b20a4f962454f98afccc0634d07a9912b05184639b` |
| G2 | kF | 250,000 | 40/40 | 3,289 | 0 | 526,599,769 | `dff0630c12ad2549f22405b20a4f962454f98afccc0634d07a9912b05184639b` |

**G1 — IDENTICAL.** On book lines 3401–3600, `cmp -s` returned 0. Across 200 games, 0 had different records, 0 had different move lists and 0 had different node sequences including any `NA` entries. [G1 independent audit](astra5/job17/audit/G1/summary.txt) · [r15d records](astra5/job17/G1-r15d/records.txt) · [kF records](astra5/job17/G1-kF/records.txt)

**G2 — IDENTICAL.** On book lines 3601–3640, `cmp -s` returned 0. Across 40 games, 0 had different records, 0 had different move lists and 0 had different node sequences including any `NA` entries. [G2 independent audit](astra5/job17/audit/G2/summary.txt) · [r15d records](astra5/job17/G2-r15d/records.txt) · [kF records](astra5/job17/G2-kF/records.txt)

## Facts

Every logged search returned a legal move. The two record fields used to compare search behavior were the move and the last reported node count. Across the two r15d arms there were 0 `NA` entries in 21,905 played plies; the kF records matched them in the same positions.

## Suspicions

A difference in the timing of the hard stop could change the last reported iteration or the chosen move. These records compare those two outputs directly.

## What I did not do

I did not measure Elo or wall-clock speed.

**What this cannot see**, in the job’s words

> the PC's engine build (clang 23 for Windows, its profile), its trained nets (net768 is made up), fastchess itself (your driver stands in for it), more than one thread, openings outside these lines.

## What I am not sure about

The last info line does not reveal the unreported work between the final completed iteration and the hard stop. Those node visits cannot be compared from these records.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job17`.

```text
A  forge-combo29/REPORT_astra5_job17.md
M  forge-combo29/astra5/job17/stamps.txt
forge-combo29/astra5/job17:
C17
G1-kF
G1-r15d
G2-kF
G2-r15d
K17-1
K17-2
arm.py
audit
compare_stage.py
prediction.txt
selfplay.py
stamps.txt
step0

forge-combo29/astra5/job17/C17:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot2

forge-combo29/astra5/job17/C17/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/C17/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/G1-kF:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot2

forge-combo29/astra5/job17/G1-kF/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/G1-kF/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/G1-r15d:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot2

forge-combo29/astra5/job17/G1-r15d/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/G1-r15d/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/G2-kF:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot2

forge-combo29/astra5/job17/G2-kF/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/G2-kF/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/G2-r15d:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot2

forge-combo29/astra5/job17/G2-r15d/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/G2-r15d/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/K17-1:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot2

forge-combo29/astra5/job17/K17-1/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/K17-1/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/K17-2:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot2

forge-combo29/astra5/job17/K17-2/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/K17-2/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job17/audit:
C17
G1
G2
K17
audit.py
check_driver.py
driver-evidence.txt
hard-node-source-audit.txt
parser-test.txt
protocol

forge-combo29/astra5/job17/audit/C17:
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
live-first-difference.txt
summary.txt

forge-combo29/astra5/job17/audit/G1:
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job17/audit/G2:
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job17/audit/K17:
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job17/audit/protocol:
driver-audit.txt
hard-node-source-audit.txt
protocol-G1.txt
protocol-G2.txt
protocol-check.py
protocol-controls.txt

forge-combo29/astra5/job17/step0:
base
gates

forge-combo29/astra5/job17/step0/base:
build-inputs.txt
capacity.txt
kF-source-check.txt
r15d-source-check.txt

forge-combo29/astra5/job17/step0/gates:
identities.txt
kF
pc20.txt
r15d

forge-combo29/astra5/job17/step0/gates/kF:
PC20-bench-11.txt
PC20-bench-13.txt
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt

forge-combo29/astra5/job17/step0/gates/r15d:
PC20-bench-11.txt
PC20-bench-13.txt
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
```
