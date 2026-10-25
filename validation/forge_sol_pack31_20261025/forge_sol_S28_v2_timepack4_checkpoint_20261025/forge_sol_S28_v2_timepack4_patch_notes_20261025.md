# S28-3 timepack4 documentation/format fix — 2026-10-25

Status: source/patch checks PASS; no native run in this bounded subtask. Strength/speed UNPROVEN. Immutable v1 SHA256: `791f432b6c82f76e478c25bee98a0439e2c91a42abb662fbeeafc24e8b6638c9`.

New patch: `forge_sol_S28_v2_timepack4_20261025.patch`, SHA256 `4db4069bbd26bf98a880db5a5ce61cda8dbdb7ccdd709545a033c1ca5070cb73`. It adds the exact requested IDEA paragraph and proper Git extended headers/new-file mode100644, with five-line context and a/b prefixes.

> timepack4: TmDecisiveWinStable = timepack3 TmDecisiveWin (own; DR P25A spec 450 cp / depth 8) + CR F3 skip on falling eval or best-move change; own code, no engine code copied

Actual legacy Git-check and GNU zero-fuzz apply PASS on L/L'/B. The first producer incorrectly expected legacy Git rejection; it was corrected rather than inventing a RED. Separate actual required-header-format and IDEA-presence assertions are RED on v1 and GREEN on v2. Conventional unified-diff acceptance is distinct from the requested extended-header format.

New Git-check and GNU zero-fuzz dry-run/application PASS on all three minimal target-file copies. Removing only the new IDEA block recovers each complete original IDEA file, preserving Job C/S01/buffix notes. No authoritative source, published v1, main tool, project Git or source C++ value/body changed.

All three C++ files and CMake are byte-identical after old/new application on each same base. Decoded C++ add/delete operations and CMake additions also match exactly.

| Base | File | Applied v1/v2 identical SHA256 |
|---|---|---|
| L | `CMakeLists.txt` | `e24d9a8fe252112abca6f2df6596dba6574a80e1c43f5dbb973c5363de2bb00f` |
| L | `include/forge/search.hpp` | `6a42e3baa6d213d2fe432fe2dace9e43a30488886b380914f049d5979d59743b` |
| L | `src/search.cpp` | `477effcfb5b6ce845fb14fa10a312aa24cc06ec42ef1b75a2d8ecb7a4e57d726` |
| L | `tests/timepack4_tests.cpp` | `e3c1c041a10f94dd6e702422862214ab8071ff46c578024ee71fddf20f53d80a` |
| Lp | `CMakeLists.txt` | `e24d9a8fe252112abca6f2df6596dba6574a80e1c43f5dbb973c5363de2bb00f` |
| Lp | `include/forge/search.hpp` | `6a42e3baa6d213d2fe432fe2dace9e43a30488886b380914f049d5979d59743b` |
| Lp | `src/search.cpp` | `477effcfb5b6ce845fb14fa10a312aa24cc06ec42ef1b75a2d8ecb7a4e57d726` |
| Lp | `tests/timepack4_tests.cpp` | `e3c1c041a10f94dd6e702422862214ab8071ff46c578024ee71fddf20f53d80a` |
| B | `CMakeLists.txt` | `4b43c412d9da90dffcc511edf4c6c87cc8a0bf0a924320087712470e1d95e968` |
| B | `include/forge/search.hpp` | `6a42e3baa6d213d2fe432fe2dace9e43a30488886b380914f049d5979d59743b` |
| B | `src/search.cpp` | `a636e412aa01824c654011878d4bee00a259809cfaf672093bb6bbf172b52c65` |
| B | `tests/timepack4_tests.cpp` | `e3c1c041a10f94dd6e702422862214ab8071ff46c578024ee71fddf20f53d80a` |

Diffstat: 5 files, +169 −1.

Optional S28-4 is fully deferred: default/range, 450-cp/depth-8 constants, clock/ponder guards and unused include stay exactly v1. Runtime/native qualification and other S28 v2 requirements belong to the main tool owner. No lock promotion, benchmark, build or speed/Elo claim.

Receipts contain commands, lossless original streams, exits, legacy Git-PASS observations, format/IDEA RED→GREEN, decoded-operation hashes and per-base file hashes. Private scratch Git is used only for patch generation/application checks.
