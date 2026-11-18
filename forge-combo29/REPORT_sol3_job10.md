# sol3 — Job 10 owned AVX-512 transposition-table checks

**Step 0 passed.** The pinned r15d, k11v, k11f, net768 and Carbon2 patch hashes matched. The piece-13 file from commit `6d4876d281db74f6a0b851db81d9ab1f01db2761` matched `a6d66722e690c5fe3f1fb397405a3f8470b8dd1bd300887a5e2442ae132e02eb`. It applied to the k11v scratch tree with `patch -p1 -F0`, without offset, fuzz or reject. k13 built to SHA-256 `0a54e59a8500958605476814d424e00f9d392fa719e706284ef61ecc70c096a3`. The PC20 runs activated net768 with checksum `30ab43b4ba5db5f3`. [Input pins](sol3/job10/stage0/input_hashes.txt) · [Patch receipt](sol3/job10/stage0/patch_apply.txt) · [Build](sol3/job10/stage0/build_13.txt) · [Bench readback](sol3/job10/stage0/pins.txt)

| Build | Default bench 11 | Default bench 13 | Default perft 5 | PC20 net768 bench 11 | PC20 net768 bench 13 |
| --- | ---: | ---: | ---: | ---: | ---: |
| k11v | 312866 | 862329 | 4865609 | 882074 | 4275906 |
| k13 | 312866 | 862329 | 4865609 | 882074 | 4275906 |

**Prediction grade.** k13 matched all seven warm pins and every captured row. k13f matched 389/389 rows in each of the four hard-node cells. All three controls changed the legacy trace. C1 and C3 first differed at game 0, ply 8, as predicted. C2 first differed at game 1, ply 143, later than the forecast of game 0, ply 28. The standalone prediction was pushed first at `cbcded0e483a5db9448685312999e3ccb7cd655c`. [Prediction](sol3/job10/prediction.txt) · [Step stamps](sol3/job10/stamps.txt)

### Step 1 warm workload

I reran the unchanged Job 6 driver for 60 games with net768, PC20, one thread, Hash 16 MiB, default MultiPV 1, seed 20261117, eight random opening plies, a 300-ply maximum and `go softnodes 2000` with a hard cap of 8000. The k13 and k11v traces matched in every game, ply, position, move, score, last-iteration nodes, final nodes and terminal status. The readback independently recomputed both traces. [Command and SHA-256 records](sol3/job10/step1/run.meta) · [Readback](sol3/job10/step1/readback.json) · [Full k13 trace](sol3/job10/step1/trace.jsonl)

| Build | Searches | Last-iteration nodes | Legacy trace | Terminal | Final sum | At 8000 | Final trace |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| k11v | 8612 | 29333343 | `5c705841c3ea17b4` | 42 | 35918624 | 971 | `5356dbb3a5f1bee3` |
| k13 | 8612 | 29333343 | `5c705841c3ea17b4` | 42 | 35918624 | 971 | `5356dbb3a5f1bee3` |

### Step 2 cold hard-node labels

k13f is k13 plus the exact Job 5 final-node probe. It applied with zero fuzz and an offset of 131 lines reported by `patch`. k13f built to SHA-256 `f96b034be515fdae43fab2cbe8182a596c4178c03e6f52f024b90444321042fe`. I used the same 389 FENs and Job 7 harness with a ready barrier after each `ucinewgame`, PC20, Threads 1, Hash 16 MiB and MultiPV 1. B2 uses embedded AL1 s198 and N2 uses the pinned standalone net768. [Probe application](sol3/job10/step2/patch_apply.txt) · [Build and hashes](sol3/job10/step2/build_and_helper.sha256.txt) · [Independent checker](sol3/job10/step2/check_cold.py)

| Limit | Cell | k13f/k11f final count, bestmove and score equal | k11f at cap | k13f at cap | Above cap |
| ---: | --- | ---: | ---: | ---: | ---: |
| 50000 | [B2](sol3/job10/step2/50000/B2/gate.txt) | 389/389 | 389 | 389 | 0 |
| 50000 | [N2](sol3/job10/step2/50000/N2/gate.txt) | 389/389 | 389 | 389 | 0 |
| 250000 | [B2](sol3/job10/step2/250000/B2/gate.txt) | 389/389 | 388 | 388 | 0 |
| 250000 | [N2](sol3/job10/step2/250000/N2/gate.txt) | 389/389 | 389 | 389 | 0 |

In the B2/250000 cell, k11f and k13f both completed row 165 at depth 64, 220357 nodes, bestmove `g1h1`, score `mate -4`. [Exact FEN and both raw lines](sol3/job10/step2/below_limit.txt)

### Step 3 one-line owned-table controls

Each control reproduced the Step 1 setup and warm workload with only its listed source line changed. C1 misaligns the tag and occupancy masks in `probe_owned_fast`. C2 maps the selected full-cluster victim to its neighboring occupied slot with XOR 1. C3 rotates the existing-tag store selection forward within the four-slot cluster. Each changed the warm legacy trace from `5c705841c3ea17b4`, so the prescribed conditional 250000-node N2 check was unnecessary. Game and ply below are zero-based driver coordinates. [C1 diff](sol3/job10/step3/C1.patch.txt) · [C2 diff](sol3/job10/step3/C2.patch.txt) · [C3 diff](sol3/job10/step3/C3.patch.txt)

| Arm | Code path | Legacy trace | First row | Game | Ply | Final nodes k13 → control |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| [C1](sol3/job10/step3/C1/warm_gate.txt) | Owned probe hit mask | `30f45873fc46d7b4` | 1 | 0 | 8 | 2864 → 3037 |
| [C2](sol3/job10/step3/C2/warm_gate.txt) | Full-cluster victim | `9e49d83c9f8feb6a` | 212 | 1 | 143 | 7388 → 7389 |
| [C3](sol3/job10/step3/C3/warm_gate.txt) | Owned store matched slot | `5bea98dc710bf6c3` | 1 | 0 | 8 | 2864 → 4020 |

#### C1 at game 0, ply 8

Both builds returned `b3b4`. [C1 first differing records](sol3/job10/step3/C1/readback.json)

```text
k13  info depth 7 seldepth 12 score cp -222 nodes 2864 nps 1432000 hashfull 0 time 2 pv b3b4 e5g6 d1b3 d8b6 g2g4 b6b4 b3c3
C1   info depth 8 seldepth 8 score cp -125 nodes 3037 nps 3037000 hashfull 0 time 1 pv b3b4 e5g6 g1f3 a5b4
```

#### C2 at game 1, ply 143

Both builds returned `g7f7`. [C2 first differing records](sol3/job10/step3/C2/readback.json)

```text
k13  info depth 9 seldepth 21 score cp -713 nodes 7388 nps 1477600 hashfull 7 time 5 pv g7f7 e4f4 f7e6 g5g6 e6e5 f4g4 e5f5 g4g5 f5e4 g5h5 e4d4
C2   info depth 9 seldepth 21 score cp -713 nodes 7389 nps 1847250 hashfull 7 time 4 pv g7f7 e4f4 f7e6 g5g6 e6e5 f4g4 e5f5 g4g5 f5e4 g5h5 e4d4
```

#### C3 at game 0, ply 8

Both builds returned `b3b4`. [C3 first differing records](sol3/job10/step3/C3/readback.json)

```text
k13  info depth 7 seldepth 12 score cp -222 nodes 2864 nps 1432000 hashfull 0 time 2 pv b3b4 e5g6 d1b3 d8b6 g2g4 b6b4 b3c3
C3   info depth 8 seldepth 9 score cp -198 nodes 4020 nps 2010000 hashfull 0 time 2 pv b3b4 e5g6 h2h3 d8b6 g1f3 b6b4 d1d2
```

## Facts

- The k13 and control builds used GCC 14.2.0, Debian libstdc++ from GCC 14.2.0-19, CMake Release and `-march=x86-64-v4`. GCC defines `__AVX512F__` with these flags. The reported tests use the single-thread owned-table path. [k13 build](sol3/job10/stage0/build_13.txt) · [Compiler macro](sol3/job10/step3/avx512_macro.txt) · [C1 build](sol3/job10/step3/C1/build.txt) · [C2 build](sol3/job10/step3/C2/build.txt) · [C3 build](sol3/job10/step3/C3/build.txt)
- C2's first visible effect was one additional node, with the same score and move. C1 and C3 first changed both the completed score and nodes, with the same move. The three first-divergence records each preserve the exact position command, last completed iteration, final nodes line and bestmove. [C1 raw record](sol3/job10/step3/C1/warm_gate.txt) · [C2 raw record](sol3/job10/step3/C2/warm_gate.txt) · [C3 raw record](sol3/job10/step3/C3/warm_gate.txt)

## Suspicions

A full-cluster victim can change before that change affects a recorded search row. The first C2 difference measures the earliest visible effect in this replay. This job did not record the first full-cluster replacement itself.

## What I did not do

I ran no speed or strength comparison. The conditional cold control replay was skipped after each control changed the warm legacy trace. Source trees and build outputs stayed in the scratch workspace.

## What I am not sure about

More than one thread (`probe_locked_fast` and `store_locked_fast` are not on a one-thread path), Hash sizes other than 16, a game clock, speed (no timing in this job), the PC's own net and compiler.

The observations establish identity of the recorded search outputs within the tested fixtures and budgets. They do not count every probe, store or replacement or compare the table's byte state. [UTC checkpoints](sol3/job10/stamps.txt)
