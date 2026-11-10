# opus_smp_layout — BENCH (evidence; every row says EXECUTED or PENDING)

Machine: AMD Ryzen 7 9850X3D (8 cores / 16 logical CPUs, SMT pairs (2k, 2k+1)). Every local run is pinned to CPUs 12-15 at Idle, i.e. two physical cores on a shared PC, while CPUs 0-3 run other work. Times are Vienna (HTTPS Date header). Compiler: MSYS2 g++ 15.2.0 (Rev14); CI: g++-14 14.2.0 on ubuntu-24.04.

## 1. Identity of the builds (EXECUTED)
| build | source | kit v2.3 `-Expose` LTO+PGO exe sha256 (pc1 = pc2) | node identity in the kit |
|---|---|---|---|
| parent P | `7ce10a05` | `4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` = trial_w6 (md5 331EA9BF…) | OFF pins, perft, bench_fens: ALL OK |
| **OFF** (compile-time 0) | `893b78d` as is | **`4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` = P byte for byte** | ALL OK |
| **GATE** (compile-time 1, `TtLockless` default false) | `893b78d` + the one define line flipped | **`6c07563b8dfdeca2109c62e0d15df2877f62ca4cf084bc39c4f810c6bdecfe91`** | OFF: ALL OK; `TtLockless=true`: ALL OK (bench d11-22 = pins, perft = pins, plain = LTO+PGO), "IDENTICAL to OFF" |

- Macro-0 preprocessing: `g++ -E -P` with the kit flags, blank lines stripped, is identical to P for all 8 units (`tools/pp_identity.ps1`, `logs/pp_identity_macro0.txt`).
- The plain twins differ from P's plain twin only in PE bytes 137-138 and 217-218 (timestamp and checksum; 4 bytes, `cmp -l`).
- Kit: QA kit_v23 copy at Idle, without termination (IDEA_SOURCE.md). Wrapper `tools/kit_build.ps1`. Logs in `logs/kit/`.

## 2. Layout measured (EXECUTED for P; gate PENDING)
`tools/layout_probe.cpp`, built against each tree with the kit flags at -O2:

| item | parent P (macro 0) | gate (macro 1) |
|---|---|---|
| sizeof/alignof Worker | 377664 / 64 | PENDING |
| `nodes_` offset, line | 377496, line 5898 | PENDING |
| members sharing `nodes_`'s line | root_effort_count_, pondering_, start_, **local_nodes_** (owner writes every node), all_workers_, node_limit_, node_limit_specified_ | PENDING |
| 4 heap workers: nodes_ and local_nodes_ on the same line | YES for all 4 | PENDING |
| SharedSearchState: stop / ponder_hit_ns | line 1025, alone (TT object ends at line 1024): **no change needed** | PENDING |
| distance between heap workers | MB apart (no adjacency) | PENDING |

## 3. Tests (EXECUTED)
| test | where | result |
|---|---|---|
| `forge_tt_lockless_tests` | native, CPUs 12-15, 1.5 s per config | round trip; differential: 300,000 probes and 224,119 hits with tables equal; contention, 4/8 threads × 1/4/16 clusters: **0 incoherent hits in 453,850,112 probes (75,459,423 hits)**; positive control (unvalidated two-word table): **1,673,288 incoherent hits**, so the fixture can detect tearing; lifecycle OK |
| `forge_smp_lifecycle_tests` | native | Threads 1/2/4/8 × both modes: every best move legal; stop, ponderhit and lifecycle cases bounded; T1 three-way identity (shared / exclusive / lockless) equal cold and warm on 6 FENs |
| `forge_tt_tests` (existing 12 groups) | native, macro 1 | PASS |
| CI run 42673707949 (`893b78d`) | ubuntu-24.04, g++-14 | release: identity ALL OK (pins, perft, FMA 0), tests PASS; ASan+UBSan: PASS, no report; **TSan: both new tests PASS, "TSan: 0 reports"**; known-failure check PASS (only the 4 known forge_tests lines) |
| CI run 42674616047 (`4a8f12b`; engine sources = `893b78d`, 0-line diff) | ubuntu-24.04, g++-14, TSan build + `opus_round1/opus2_smp/tsan_extra.sh` | **under TSan**: contention 4/8 threads × 1/4/16 clusters gave 47,133,184 probes and 7,793,150 hits with **0 incoherent**; positive control 3,898,550 hits with **464,076 incoherent** (the fixture detects tearing under TSan too); lifecycle PASS; **real TSan engine over UCI** (go movetime / nodes / infinite+stop / ponder+ponderhit / Clear Hash / Hash / Threads / ucinewgame / quit) with TtLockless false and true at Threads 2 and 4: exit 0 and 5 bestmoves each; **"TSan: 0 reports"**; release and ASan+UBSan green |

## 4. L3 / L3b identity at Threads 1 (PENDING)
## 5. Race / stress (PENDING)
## 6. Advisory NPS (PENDING; never a verdict)
