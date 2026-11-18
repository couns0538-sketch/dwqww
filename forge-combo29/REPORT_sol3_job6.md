# sol3 — Job 6 warm final counts and piece 12 legal-move audit

**Step 0 passed.** The retained executables and net matched their prescribed hashes. Piece 12 SHA-256 `58a69dba9f7a336f8aa4b37b21194fbbe51448100255d020b6365ee96ad3e7fd` applied to k11 with zero fuzz, offsets or rejects. k12 executable SHA-256 was **`9b50324e42ea8fe42f3246149d7389726f8994650080790349018e956d60eca7`**, also reported by Sol2’s independent build. With embedded AL1 s198, Threads 1, Hash 16 MiB, MultiPV 1, and other search options at defaults, the k12 pins were **312866** at bench 11, **862329** at bench 13, and **4865609** at startpos perft 5. Its synthetic net768 readiness line showed checksum `30ab43b4ba5db5f3`. [Executable/build](sol3/job6/build_12.txt) · [Applied patch](sol3/job6/patch12.txt) · [Raw pins](sol3/job6/pins_12.summary.txt) · [Sol2 readback](https://github.com/couns0538-sketch/dwqww/blob/d36d89c9afe3abc430d308c2535bd73516296820/forge-combo29/REPORT_sol2_job5.md)

**Step 1 passed.** r15d reproduced **8612 searches**, **29333343 last-iteration nodes**, and legacy trace **`5c705841c3ea17b4`**. The corrected terminal rule supplied zero for 42 missing final lines on terminal last searches, 41 with `bestmove 0000` and one with a returned move and zero last-info nodes. The first was game index 0, ply 83. Final nodes summed to **35918624**, with **971** at the 8000 hard cap, and final trace **`5356dbb3a5f1bee3`**. The driver and separate trace reader agreed. [Original JSON](sol3/job6/r15d_step1.json) · [Independent readback](sol3/job6/r15d_step1_readback.json) · [Exact corrected driver diff](sol3/job6/driver_final.diff)

**Prediction grade.** Both cap-hit predictions matched at 971. k10, k11 and k12 matched all six predicted fields against r15d, and P changed the final hash. The in-search prediction of 30,000,000 calls was 317,580 below the measured 30,317,580. The forecasts of 200 in-check calls and 1500 no-move calls substantially underestimated 35743 and 19188 respectively. The zero-mismatch prediction held. The prediction was published alone at `810052e9` before any Step 2 search. [Predictions](sol3/job6/prediction.txt) · [Counters](sol3/job6/hlm_search.gate.txt)

### Step 2 warm final-count table

All rows used PC20, Threads 1, Hash 16 MiB, MultiPV 1, synthetic standalone net768 with SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`, and `go softnodes 2000` with an 8000 hard cap. The corrected driver ran 60 startpos games in one engine process per tree, reset once per game, with seed 20261117, eight random opening plies, and a 300-ply cap. Engine path, hash, `id name`, and exact commands are in the per-tree metadata. [Evidence and metadata](sol3/job6)

| Tree | Searches | Last-iteration nodes | Legacy trace | Terminal | Final nodes | At cap | Final trace |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| r15d | 8612 | 29333343 | 5c705841c3ea17b4 | 42 | 35918624 | 971 | 5356dbb3a5f1bee3 |
| 10 | 8612 | 29333343 | 5c705841c3ea17b4 | 42 | 35918624 | 971 | 5356dbb3a5f1bee3 |
| 11 | 8612 | 29333343 | 5c705841c3ea17b4 | 42 | 35918624 | 971 | 5356dbb3a5f1bee3 |
| 12 | 8612 | 29333343 | 5c705841c3ea17b4 | 42 | 35918624 | 971 | 5356dbb3a5f1bee3 |
| P | 8411 | 28780871 | 8abf1410863ec7f5 | 42 | 34968406 | 1 | b7dc296d8bc1ebbb |

The r15d repeat and k10, k11 and k12 matched search by search on the captured position, last-iteration move/nodes/score, final count and terminal classification. P changed the final hash and the legacy trace. Its first difference was game index 0, ply 54 (search 47), where the last iteration held 1725 nodes, `cp -88` and `e4d5` in both trees, while the final line changed from `info string softnodes nodes 8000` to `info string softnodes nodes 8001`. The first later difference in the legacy fields was game index 1, ply 176 (search 245), on the same position command. k11 reported 4233 nodes and `cp 1050`, P reported 4604 and `cp 984`, and both played `h2h4`. [Exact first differing records](sol3/job6/arm_P.first_difference.json) · [First legacy difference](sol3/job6/arm_P.first_legacy_difference.json)

### Step 3 k12 cold identity against k11

Each cell used the fixed 389-position Job 3 fixture, PC20, Threads 1, Hash 16 MiB and MultiPV 1. B cells used embedded AL1 s198. N cells used the synthetic standalone net768. The unchanged Job 4 harness was used with its output label `11`, and the filenames were relabeled `12` after running the k12 executable. [Command and raw output](sol3/job6)

| Cell | Command | Last-iteration rows equal byte for byte | Final soft-node totals equal |
| --- | --- | ---: | ---: |
| B2 | `go nodes 20000` | 389/389 | — |
| B3 | `go softnodes 2000` | 389/389 | 389/389 |
| N2 | `go nodes 20000` | 389/389 | — |
| N3 | `go softnodes 2000` | 389/389 | 389/389 |
| ND | `go depth 8` | 389/389 | — |

### Step 4a legal-move predicate against the full generator

The k12 probe replayed all original warm root commands, with the entire game history, and traversed each fixture root and every legal path through two plies. Counts retain duplicate and transposed paths. The full generator ran on a board copy so its cache updates could not affect the predicate’s original live return value. The control returned true at the start of `has_legal_move`. [Probe](sol3/job6/hlm_probe.diff) · [Control](sol3/job6/hlm_control.diff) · [Raw comparison](sol3/job6/hlm_oracle.stdout.txt) · [Raw control](sol3/job6/hlm_control.stdout.txt)

| Set | Check split | Positions | In check | No legal move | k12 mismatches | Always-true control mismatches |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Whole-game roots | All | 8612 | 1578 | 41 | 0 | 41 |
| Whole-game roots | In check | 1578 | 1578 | 41 | 0 | 41 |
| Whole-game roots | Out of check | 7034 | 0 | 0 | 0 | 0 |
| Fixture paths | All | 399125 | 10805 | 59 | 0 | 59 |
| Fixture paths | In check | 10805 | 10805 | 59 | 0 | 59 |
| Fixture paths | Out of check | 388320 | 0 | 0 | 0 | 0 |
| Combined | All | 407737 | 12383 | 100 | 0 | 100 |
| Combined | In check | 12383 | 12383 | 100 | 0 | 100 |
| Combined | Out of check | 395354 | 0 | 0 | 0 | 0 |

### Step 4b legal-move predicate inside actual search

The instrumented k12 executable SHA-256 was `b33bef9f7b76cbb6d6bb25fb5fba1a0ae4ca05283b4653bc23aa215d72b1874b`. The comparison ran on every `has_legal_move()` call during the same 60-game PC20/net768 soft-node workload. It returned the original predicate result and recorded one counter line per search, including a terminal reply. The separate parser summed exactly **8612** raw lines. [Search probe](sol3/job6/hlm_search_probe.diff) · [Executable and command](sol3/job6/hlm_search.meta) · [All counter lines](sol3/job6/hlm_raw) · [Independent sums](sol3/job6/hlm_search.gate.txt)

| Calls | In check | No legal move | Mismatches |
| ---: | ---: | ---: | ---: |
| 30317580 | 35743 | 19188 | 0 |

The original and instrumented k12 searches matched in order, with the same 29333343 last-iteration nodes, 35918624 final nodes, 42 terminal replies, 971 hard-cap hits, and both trace hashes. The comparison produced no first mismatch. [Engine and driver JSON](sol3/job6/hlm_search.json) · [Exact first-difference readback](sol3/job6/hlm_search.first_difference.json)

## Facts

- The independent k12 Release build used CMake 4.2.3, GCC 14.2.0, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and the Job 4 flags. Piece 12 came from Carbon2’s pinned source commit `ba2de7672095eb0306b3d8d9a7d1bc1b15cae32c`. The probes retained the same compiler settings. [Patch hash check](sol3/job6/patch12_input.txt) · [Compile log](sol3/job6/build_12.txt)
- The corrected driver accepts a missing final line only when the existing game-stop branch applies. It still hashes this search in both streams. The independent reader checked that each logged position was the exact preceding move sequence plus the previous reply, and reproduced both trace hashes. The 8612 original warm UCI position commands were committed in numbered shards with an explicit recombination SHA-256. [Commands](sol3/job6/root_positions) · [Line count and hashes](sol3/job6/positions_commands.count-sha256.txt)
- The fixture traversal covered 389 depth-zero positions, 12058 one-ply paths and 386678 two-ply paths. The 41 no-move warm roots were all in check, as expected. The always-true control found exactly those 41 and the 59 no-move fixture paths. [Raw oracle](sol3/job6/hlm_oracle.stdout.txt) · [Gate](sol3/job6/hlm_4a.gate.txt)
- Git smart HTTP was returning 503 during Job 6. I used the GitHub connector to append each local checkpoint’s exact tree to the authorized branch and checked that the stored remote tree SHA matched. Local and remote commit SHA values differ because the commits were created by different transports. [Inbox checks](sol3/job6/inbox_receipt.txt)

## Suspicions

The planted build’s first overrun left the completed iteration intact. Its later same-position difference is consistent with effects from state carried between searches, though this run does not isolate which retained state changed. The 35743 in-check `has_legal_move()` calls arise from the hundred-halfmove path in `src/search.cpp:1951–1960`. The ordinary draw check calls it only when out of check, after repetition and insufficient-material checks.

## What I did not do

I made no engine source change in the repository, ran no match or training, and performed no work on the owner’s PC. Scratch builds contained the test probes. Only text scripts, diffs, logs and reports were committed.

## What I am not sure about

More than one thread, a clock, MultiPV, speed (no timing in this job), positions the workload and the set do not reach, a fault in the full generator itself.

The 4a no-move cases in these fixtures were all in check. The aggregate in-search counts distinguish both check status and no-move results, without cross-tabulating those two counters. The result supports identity on the stated cold and warm workloads. [Clock stamps](sol3/job6/stamps.txt)
