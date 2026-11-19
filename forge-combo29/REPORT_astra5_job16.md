# Astra5 job 16 — whole-game records at 2,000 soft nodes

## 1. Step 0 — source, builds and known answers

Both unguarded builds matched their respective 29-file source manifests and all seven fresh-process checks. `nproc` returned 5. The r15d executable was the original unguarded job 7 build. kF was rebuilt from a fresh r15d copy after the speed stack applied to nine files with no offsets or rejected hunks. [r15d manifest check](astra5/job16/step0/base/r15d-check.txt) · [kF manifest check](astra5/job16/step0/kf/kF-final-tree-check.txt) · [Stack application](astra5/job16/step0/kf/patch-apply.txt)

The speed-stack patch SHA-256 was `3d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30`. [Patch and compiler provenance](astra5/job16/step0/kf/kF-provenance.txt)

| Build | Executable SHA-256 |
| --- | --- |
| r15d | `9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671` |
| kF | `c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb` |

Both used C++20 release flags including `-O3 -ffp-contract=off -fno-fast-math -march=native`. The native target exposed `__AVX512F__`, `__AVX512BW__` and `__BMI2__`. The engine defines were `FORGE_EXPOSE_TUNABLES=1`, `FORGE_NNUE_HIDDEN=256`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_NNUE_ZMM=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SPD_PREFETCH_EARLY=1`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_TT_NOTLS=1`, `FORGE_MATE_ALPHA_GUARD=1`, `FORGE_NNUE_V3=1`, `NDEBUG`. The generated `FORGE_NNUE_WEIGHTS` path referred to each tree’s `src/nnue_weights.inc`. [r15d build](astra5/job16/step0/base/build.txt) · [kF build](astra5/job16/step0/kf/build.txt) · [Native compiler defines](astra5/job16/step0/base/job7-defines.txt)

| Evaluation and options | Command | r15d nodes | kF nodes |
| --- | --- | --- | --- |
| defaults | `bench 11` | 312,866 | 312,866 |
| defaults | `bench 13` | 862,329 | 862,329 |
| defaults | `go perft 5` | 4,865,609 | 4,865,609 |
| PC20 | `bench 11` | 278,024 | 278,024 |
| PC20 | `bench 13` | 587,276 | 587,276 |
| PC20 + net768 | `bench 11` | 882,074 | 882,074 |
| PC20 + net768 | `bench 13` | 4,275,906 | 4,275,906 |

The net-enabled checks loaded the synthetic job 7 network, SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`, then reported `NNUE v3 active` with checksum `30ab43b4ba5db5f3`. [r15d gate transcript](astra5/job16/step0/gates/r15d/checks.txt) · [kF gate transcript](astra5/job16/step0/gates/kF/checks.txt)

## 2. K16 and C16 — reproducibility and sensitivity

The two r15d runs on book lines 2201–2220 used PC20, synthetic net768, one thread, 16 MiB of hash and `go softnodes 2000`. K16 produced byte-identical records. C16 changed only `LmrQuietBase` from 93 to 60 and produced different records on all 20 openings, as required. [K16 independent audit](astra5/job16/audit/K16/summary.txt) · [C16 independent audit](astra5/job16/audit/C16/summary.txt)

| Arm | Games | Ply records | Sum of reported nodes | SHA-256 of records |
| --- | --- | --- | --- | --- |
| K16-1 | 20 | 2,227 | 9,265,904 | `44bd314a207da53bf2245b5f85fe953913e282e94459f303f1f11417808808bd` |
| K16-2 | 20 | 2,227 | 9,265,904 | `44bd314a207da53bf2245b5f85fe953913e282e94459f303f1f11417808808bd` |
| C16 | 20 | 2,402 | 10,348,540 | `884aadc9b67408aba9174b44c176a4f520625b09bc765129ead64bcf50a84362` |

The first C16 difference occurred on book line 2201, played ply 1. Both arms selected the same move there, but their node counts differed. Each record contains book line, played ply, best move and the last UCI info line’s node count.

```text
K16  2201 1 f3f7 2013
C16  2201 1 f3f7 3503
```

## 3. Frozen prediction

> S1: I predict 0 of the 1,000 games will differ between r15d and kF, with a range of 0 to 2 games. I predict the node columns will be equal at corresponding plies.
> The builds agreed in the earlier depth-limited checks and fixed-node games, and all fourteen fresh controls passed. The remaining uncertainty is whether their stop checks take a different path when a completed iteration reaches the soft node limit.

[Frozen forecast](astra5/job16/prediction.txt) · [Prediction-only commit](https://github.com/couns0538-sketch/dwqww/commit/e46d51d1b9438c89a9fc0f2ec17ea843c05f0c63)

Across the 1,000 games, 0 had any record difference, 0 had different move lists and 0 had different node sequences. The zero-game point forecast hit, and the observed count was inside the 0–2 range. The prediction of equal node columns hit.

## 4. S1 and S2 — whole-game comparison

Both builds played both sides from each opening. One engine process served each arm. The driver issued `ucinewgame` and waited for `readyok` once per opening, then sent the opening FEN and cumulative UCI moves before each `go softnodes 2000`. It took each node value from the final search info line. A game ended on a rules outcome with draw claims enabled or after 300 played plies. Both arms used PC20, net768 and one thread. S1 used lines 2201–3200 and 16 MiB of hash. S2 used lines 3201–3400 and 64 MiB. [Self-play driver](astra5/job16/selfplay.py)

| Run | Build | Hash (MiB) | Completed games | Ply records | Sum of reported nodes | SHA-256 of records |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | r15d | 16 | 1,000/1,000 | 114,683 | 478,177,319 | `467f46e2b3b2a1be54f08b9260552f5c0fcefd66405eda1d6e5ddb0066318994` |
| S1 | kF | 16 | 1,000/1,000 | 114,683 | 478,177,319 | `467f46e2b3b2a1be54f08b9260552f5c0fcefd66405eda1d6e5ddb0066318994` |
| S2 | r15d | 64 | 200/200 | 23,196 | 97,216,733 | `0dc0465093c9d71f083093a8c5bb10c3c262912269572a8d8e7f30375bdf3300` |
| S2 | kF | 64 | 200/200 | 23,196 | 97,216,733 | `0dc0465093c9d71f083093a8c5bb10c3c262912269572a8d8e7f30375bdf3300` |

**S1 — IDENTICAL.** The record-file `cmp -s` returned 0. Among 1,000 games, 0 had different records, 0 had different move lists and 0 had different node sequences. [S1 independent audit](astra5/job16/audit/S1/summary.txt) · [r15d records](astra5/job16/S1-r15d/records.txt) · [kF records](astra5/job16/S1-kF/records.txt)

**S2 — IDENTICAL.** The record-file `cmp -s` returned 0. Among 200 games, 0 had different records, 0 had different move lists and 0 had different node sequences. [S2 independent audit](astra5/job16/audit/S2/summary.txt) · [r15d records](astra5/job16/S2-r15d/records.txt) · [kF records](astra5/job16/S2-kF/records.txt)

## Facts

The recorded node count exceeded 2,000 on 114,016 of 114,683 in S1 and 23,078 of 23,196 in S2 ply records. The engine emitted its soft-node diagnostic immediately before the best move on every recorded ply. [S1 driver receipt](astra5/job16/S1-r15d/run.log) · [S2 driver receipt](astra5/job16/S2-r15d/run.log)

## Suspicions

One possible cause of a future difference is a change to which depth finishes before the soft-node stop. The recorded moves and node counts cannot reveal internal differences that leave both fields unchanged.

## What I did not do

I did not measure playing strength or wall-clock speed in this job.

**What this cannot see**, in the job’s words

> the PC's engine build (clang 23 for Windows, its profile), its trained net (net768 is made up), more than one thread, openings outside these lines.

## What I am not sure about

The evidence does not establish how the two builds would behave with the PC’s trained network or on a different set of openings.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job16`.

```text
A  forge-combo29/REPORT_astra5_job16.md
M  forge-combo29/astra5/job16/stamps.txt
forge-combo29/astra5/job16:
C16
K16-1
K16-2
S1-kF
S1-r15d
S2-kF
S2-r15d
audit
prediction.txt
selfplay.py
stamps.txt
step0

forge-combo29/astra5/job16/C16:
games.tsv
records.txt
run.log

forge-combo29/astra5/job16/K16-1:
games.tsv
records.txt
run.log

forge-combo29/astra5/job16/K16-2:
games.tsv
records.txt
run.log

forge-combo29/astra5/job16/S1-kF:
games.tsv
records.txt
run.log

forge-combo29/astra5/job16/S1-r15d:
games.tsv
records.txt
run.log

forge-combo29/astra5/job16/S2-kF:
games.tsv
records.txt
run.log

forge-combo29/astra5/job16/S2-r15d:
games.tsv
records.txt
run.log

forge-combo29/astra5/job16/audit:
C16
C16-cmp.txt
K16
K16-2-cmp.txt
S1
S1-cmp.txt
S2
S2-cmp.txt
audit.py
driver-evidence.txt

forge-combo29/astra5/job16/audit/C16:
arms.tsv
differences.tsv
first-difference.txt
games.tsv
live-first-difference.txt
summary.txt

forge-combo29/astra5/job16/audit/K16:
arms.tsv
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job16/audit/S1:
arms.tsv
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job16/audit/S2:
arms.tsv
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job16/step0:
base
gates
kf

forge-combo29/astra5/job16/step0/base:
build.txt
job7-build-log.txt
job7-defines.txt
job7-patch-application.txt
job7-provenance.txt
r15d-check.txt
r15d-patches.sha256.txt
r15d.sha256.txt

forge-combo29/astra5/job16/step0/gates:
controls.py
kF
pc20.txt
r15d

forge-combo29/astra5/job16/step0/gates/kF:
PC20-bench-11.txt
PC20-bench-13.txt
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt

forge-combo29/astra5/job16/step0/gates/r15d:
PC20-bench-11.txt
PC20-bench-13.txt
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt

forge-combo29/astra5/job16/step0/kf:
build.sh.txt
build.txt
carbon2-final-proof.txt
exe.sha256.txt
fetch.txt
fresh-copy-r15d-check.txt
input-r15d.sha256.txt
kF-compile-flags.txt
kF-final-tree-check.txt
kF-final-tree.sha256.txt
kF-provenance.txt
patch-apply.txt
patch-check.txt
```
