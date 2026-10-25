# S28 e48f006 rebase qualification — 2026-10-25

All results are Linux native observations. The accepted lock remains h256_e12. No speed, Elo, gate confirmation or Windows-PC claim.

Depth order: **11 / 13 / 16 / 20 / 22**. Each patch was applied independently to a fresh f006 source copy.

| Base | Queue | Original -F0 dry run | Repair used | OFF nodes | ON nodes | First ON difference |
|---|---|---|---|---|---|---|
| L | P23b | PASS | No | 328459 / 945640 / 3024381 / 9162399 / 20421972 | 330817 / 894651 / 2957682 / 13763680 / 24703864 | 11 |
| L | P27R | PASS | No | 328459 / 945640 / 3024381 / 9162399 / 20421972 | 325245 / 967224 / 3037089 / 13395897 / 20211191 | 11 |
| L | timepack4 | PASS | No | 328459 / 945640 / 3024381 / 9162399 / 20421972 | 328459 / 945640 / 3024381 / 9162399 / 20421972 | null — time-only |
| B | P23b | PASS | No | 328459 / 945640 / 3024381 / 9162399 / 20421972 | 330817 / 894651 / 2957682 / 13763680 / 24703864 | 11 |
| B | P27R | PASS | No | 328459 / 945640 / 3024381 / 9162399 / 20421972 | 325245 / 967224 / 3037089 / 13395897 / 20211191 | 11 |
| B | timepack4 | FAIL (preserved) | necessary CMake-only context rebase | 328459 / 945640 / 3024381 / 9162399 / 20421972 | 328459 / 945640 / 3024381 / 9162399 / 20421972 | null — time-only |

The timepack4 control is `TmDecisiveWinStable=60`, advertised default 0; its runtime scale applies to managed-time search. Fixed-depth ON=OFF and a null precheck are expected. P23b uses `RefutLmr=1`; P27R uses `QsEvasionSeeNonPv=1`; both defaults are 0. Requested controls were advertised and checked before ON runs.

Only the B/timepack4 original failed: two CMake context hunks. Its original failed dry-run is retained before the actual repaired dry-run/application. L used the original unchanged. The repair relocates registration at common EOF; all non-CMake patch bytes equal the original. No engine search change was invented by this rebase.

| Delivered necessary patch | SHA256 | Full patch diffstat |
|---|---|---|
| `forge_sol_S28_rebase_e48f006_timepack4_20261025.patch` | `791f432b6c82f76e478c25bee98a0439e2c91a42abb662fbeeafc24e8b6638c9` | 4 files, +164 −1 (CMakeLists +4; search.hpp +19; search.cpp +17 −1; timepack4_tests +124) |

All ten engines pass both perft5 totals (4865609 / 193690690), whole-executable and NNUE-object FMA counts 0, and the supplied NNUE-evaluate checker. Full CTest retains only the exact four original FAIL lines in forge_tests. These are compatibility/correctness observations, not acceptance of any queued search change.

Original queue patches are referenced by full hash in `forge_sol_S28_native_queue_20261025.json`; they are not resubmitted under new names. Original commands/streams, application receipts, source/binary hashes, complete native manifests and test logs are losslessly preserved in the indexed evidence bundle.
