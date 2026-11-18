# Sol — Job 34 kF and r15d whole-game readback at the loop limit

## Step 0. Source, builds, net768 and pins

I extracted the PC r15 patch from the pinned handoff and checked its SHA-256. I applied it, the speed patch and the e1 evasion patch in that order to an exact scratch copy of `6b98f2170a3210e71beed04bbd2553972c253ed7`. The stack patch on that r15d tree made kF. All four `patch -p1 -F0` invocations exited 0 without offsets, fuzz or rejections. Both 29-file manifests passed `sha256sum -c`. [Inputs and pinned commits](sol/job34/inputs/provenance.txt) · [Patch hashes](sol/job34/build-evidence/patch-sha256.txt) · [r15d source check](sol/job34/build-evidence/r15d.source-check.txt) · [kF source check](sol/job34/build-evidence/kF.source-check.txt)

The raw patch output follows in apply order.

`pc_r15.patch`

```text
patching file include/forge/b4.hpp
patching file include/forge/board.hpp
patching file include/forge/nnue.hpp
patching file include/forge/nnue_v3.hpp
patching file include/forge/search.hpp
patching file src/board.cpp
patching file src/eval_params.cpp
patching file src/nnue.cpp
patching file src/nnue_v3.cpp
patching file src/search.cpp
patching file src/uci.cpp
```

`a_speed_pc20_v3.patch.txt`

```text
patching file include/forge/nnue_v3.hpp
patching file include/forge/search.hpp
patching file src/board.cpp
patching file src/nnue_v3.cpp
patching file src/search.cpp
patching file src/uci.cpp
```

`e1_legal_check_evasions.patch.txt`

```text
patching file include/forge/board.hpp
patching file src/board.cpp
patching file src/search.cpp
```

`stack_r15d_to_final.patch.txt`

```text
patching file include/forge/b4.hpp
patching file include/forge/board.hpp
patching file include/forge/eval.hpp
patching file include/forge/nnue_v3.hpp
patching file include/forge/search.hpp
patching file src/board.cpp
patching file src/nnue_v3.cpp
patching file src/search.cpp
patching file src/uci.cpp
```

Both builds used GCC 14.2.0 and the specified `-march=native` flags. The preprocessor defined `__AVX512F__`, `__AVX512BW__` and `__BMI2__` as 1. The r15d executable SHA-256 was `9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671`. The kF executable SHA-256 was `c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb`. [r15d compile command](sol/job34/build-evidence/r15d.build.txt) · [kF compile command](sol/job34/build-evidence/kF.build.txt) · [Native ISA](sol/job34/build-evidence/native-isa.txt)

The pinned standard-library generator produced a 9,463,528-byte synthetic net768, SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. The v3 checksum was `30ab43b4ba5db5f3`. Every net-enabled pin and game-run log records both the load and `NNUE v3 active` with that checksum. [Generator receipt](sol/job34/net-evidence/net768-generation.txt)

| Settings | Command | r15d nodes | kF nodes |
|---|---|---:|---:|
| Defaults | `bench 11` | 312866 | 312866 |
| Defaults | `bench 13` | 862329 | 862329 |
| Defaults | `go perft 5` | 4865609 | 4865609 |
| PC20 | `bench 11` | 278024 | 278024 |
| PC20 | `bench 13` | 587276 | 587276 |
| PC20 and active net768 | `bench 11` | 882074 | 882074 |
| PC20 and active net768 | `bench 13` | 4275906 | 4275906 |

All 14 fresh-process pins matched. [r15d raw pins](sol/job34/pin-evidence/r15d.raw.txt) · [kF raw pins](sol/job34/pin-evidence/kF.raw.txt)

## K24 and C24 controls

Both used r15d with net768, Threads 1, Hash 16 and `go softnodes 2000` on physical UHO lines 1001–1020. K24 used PC20 with `LmrQuietBase 93`. C24 changed it to 60 for the control arm.

- **K24 PASS.** Both runs completed 20 games and produced matching bytes for all 2,384 records. The last-info node sum was 10,344,434 in each run. [Exact comparison and hashes](sol/job34/K24.txt)
- **C24 PASS.** The control differed on all 20 games. Its first differing record on book line 1001, ply 0, was `1001 0 b2b4 5106` with base 93 against `1001 0 g1f3 3773` with base 60. The control completed 2,096 records and 8,690,108 last-info nodes. [First difference and opening](sol/job34/C24.txt)

The forecast was the sole file in commit `362028d`, after both controls and before T1. [Frozen prediction](sol/job34/prediction.txt)

## Prediction grades

| T1 forecast | Observed | Grade |
|---|---|---|
| 0–5 differing games out of 1,000 | 0 out of 1,000 | Met |
| Node columns equal | All 117,462 corresponding values equal | Met |

## T1. Soft nodes on physical lines 1001–2000

Both pinned builds used PC20, `go softnodes 2000`, active net768, Threads 1 and Hash 16. The node field came from the last literal `info` line, which was `info string softnodes nodes` in T1.

| Record file | Status | Completed games | Records | Bytes | SHA-256 | Node-column sum |
|---|---|---:|---:|---:|---|---:|
| `raw/T1-r15d.records.txt` | complete | 1000 | 117462 | 2135547 | `6d844acbd66e8f2c4b9542d121f7ee8d605fc0aac1e265a800d8d455b92f4a32` | 489799089 |
| `raw/T1-kF.records.txt` | complete | 1000 | 117462 | 2135547 | `6d844acbd66e8f2c4b9542d121f7ee8d605fc0aac1e265a800d8d455b92f4a32` | 489799089 |

**IDENTICAL.** Compared 1000 common games. Differing common games 0. Equal node columns yes.

[Original `cmp` output](sol/job34/T1.cmp.txt) · [r15d T1 records](sol/job34/raw/T1-r15d.records.txt) · [kF T1 records](sol/job34/raw/T1-kF.records.txt)

## T2. Hard nodes on physical lines 2001–2200

**The original numeric record streams match through 196 completed games.** Both used the same build-specific executable, PC20, active net768, Threads 1, Hash 16 and `go nodes 2000`. Both stopped at physical line 2197, zero-based ply 57, where the entire response was `bestmove c6c5`. There was no `info` line to supply a node field. The strict driver kept completed games only. This leaves the full numeric T2 comparison incomplete.

| Record file | Status | Completed games | Records | Bytes | SHA-256 | Node-column sum |
|---|---|---:|---:|---:|---|---:|
| `raw/T2-r15d.records.txt` | incomplete | 196 | 22503 | 401343 | `03a53910bbb982543f3678feb7f0df308c8625b9cee854198972c252b8b803a3` | 26854000 |
| `raw/T2-kF.records.txt` | incomplete | 196 | 22503 | 401343 | `03a53910bbb982543f3678feb7f0df308c8625b9cee854198972c252b8b803a3` | 26854000 |

**IDENTICAL.** Compared 196 common games. Differing common games 0. Equal node columns yes.

Incomplete coverage. The difference count uses common recorded games only.
- Left only book lines [].
- Right only book lines [].
- Missing from both [2197, 2198, 2199, 2200].

[Original `cmp` output](sol/job34/T2.cmp.txt) · [r15d strict T2 metadata](sol/job34/raw/T2-r15d.records.txt.meta) · [kF strict T2 metadata](sol/job34/raw/T2-kF.records.txt.meta)

I reran the whole 200-game slice on each binary with the exact same UCI commands. The diagnostic driver recorded `NA` when the engine gave a legal best move without any `info` line. The original files remain published. The diagnostic streams match byte for byte across all moves, all emitted node fields and the one unavailable field. The full diagnostic preserves the exact strict-record prefix on both builds.

## Full T2 diagnostic readback

Both passes used the exact original hard-node protocol and settings. NA marks a missing info line. The node sum includes only values emitted by the engine.

| Build | Games | Records | Missing node fields | Sum of emitted node fields | SHA-256 |
|---|---:|---:|---:|---:|---|
| r15d | 200 | 22,923 | 1 | 27,335,916 | `e18f15dce8d23b0259248fd2cef87d40a2f4f6b2a3219d9dc26cf4670f40341c` |
| kF | 200 | 22,923 | 1 | 27,335,916 | `e18f15dce8d23b0259248fd2cef87d40a2f4f6b2a3219d9dc26cf4670f40341c` |

The diagnostic streams match byte for byte. The missing fields stayed explicitly unavailable.

- r15d book line 2197, ply 57, `c6c5`, last-info nodes unavailable.
- kF book line 2197, ply 57, `c6c5`, last-info nodes unavailable.

[Diagnostic `cmp` output](sol/job34/T2-observed.cmp.txt) · [r15d diagnostic metadata](sol/job34/raw/T2-observed-r15d.records.txt.meta) · [kF diagnostic metadata](sol/job34/raw/T2-observed-kF.records.txt.meta) · [Independent whole-game readback](sol/job34/independent-T2-observed.txt)

I reproduced the exact no-info reply in fresh processes by replaying game 2197 through its preceding 57 searches. Two shorter probes searched the reached FEN alone and the original FEN with its UCI move trail alone. Both reported completed depths on both builds. The scripts and replies preserve all three versions per build. [Exact reproduction and alternatives](sol/job34/missing-info-repro/result.txt) · [All UCI scripts and responses](sol/job34/missing-info-repro)

## Facts

- The source-list validator initially rejected a legitimate text-mode digest marker on `CMakeLists.txt`. I corrected it and regenerated the scratch base before the final applications. The preserved earlier and final logs show clean patch applications. GNU `sha256sum` verified all 29 r15d entries directly, and both final trees matched all 29 entries each. [Validator retry receipt](sol/job34/build-evidence/retry-note.txt) · [Earlier application records](sol/job34/build-evidence/first-clean-applications) · [Direct r15d check](sol/job34/r15d.root-source-check.txt)
- T1 reached the remote at 22:49:29 UTC before T2 began. The strict hard-node files were published at 22:50:04. The full diagnostic followed at 22:53:24. Both independent readbacks recomputed the counts and verified the committed bytes. [Independent original runs](sol/job34/independent-job34.txt) · [Independent full diagnostic](sol/job34/independent-T2-observed.txt) · [UTC stamps](sol/job34/stamps.txt)
- In both pinned sources the hard-node abort can bypass completed-depth `info`, and the UCI layer still emits a legal fallback best move. The final numeric summary is emitted for soft-node searches. The exact hard-node reproducibility check captured no numeric field at the affected ply. [Source trace](sol/job34/missing-info-repro/source-receipt.txt)

## Suspicions

The exact warm prefix reproduces the missing field on both binaries. The shorter position-only tests produce depth output. That makes prior search state relevant, though these records do not identify which internal state caused the first iteration to hit the hard cap. [Recorded UCI replies](sol/job34/missing-info-repro/result.txt)

## What this check cannot see

The PC's engine build (clang 23 for Windows, its profile), its trained net (net768 is made up), more than one
thread, Hash sizes other than 16, openings outside these lines.

## What I did not do

I built and played in the cloud with synthetic weights. I left the tracked engine source alone, ran no training and did no work on the owner's PC. This job checks exact search behavior. It did not benchmark comparative speed.

## What I am not sure about

The tested slice covers a fixed set of openings and one worker at each limit. The record comparison leaves open whether the optimized stop check behaves identically with a clock, more workers, or the trained net.

## Reproduction

Each independent run used one Forge engine process for both colors. The driver reset with `ucinewgame` and `isready` once per game, then sent the original FEN and the full UCI move trail before each search. It stopped at `board.is_game_over(claim_draw=True)` or 300 plies. Each `.records.txt` row carries a one-based physical book line, zero-based ply, UCI best move and the node count from the last literal `info` line. [Driver](sol/job34/whole_games34.py) · [Raw run metadata](sol/job34/raw)

The runs used PC20, Threads 1, Hash 16 and active net768 on UHO SHA-256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. I used distinct cores 1 and 2 for r15d and kF during each measured phase. [Exact run commands](sol/job34/run-cell.sh) · [Comparator](sol/job34/compare_games34.py)

[UTC stamps](sol/job34/stamps.txt) · [Final archive readback](sol/job34/readback.txt) · [Precommit tree](sol/job34/precommit-readback.txt)
