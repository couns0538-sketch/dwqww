# LmrLateParentRelief

## Idea

The behaviour is the assigned LmrLateParentRelief rule, applied inside this engine's existing late-move reduction in `forge-combo29/src/search.cpp`. That reduction already grows with depth and with how late the current move is, then shifts by a ply for PV nodes, improving, cut nodes, checks, and history. A parent that was itself tried only after many earlier moves is a speculative attempt. The first replies are the ones most likely to refute it, so those replies are reduced one ply less. The two cutoffs were chosen for this search and are not taken from another engine: the parent counts as late at tried index 7 or higher, and the relief applies to replies with tried index 4 or lower. Replies that never enter reduction are unchanged.

## Option

One new UCI check, advertised in the `uci` answer, default off:

`option name LmrLateParentRelief type check default false`

`setoption name LmrLateParentRelief value true` enables it. `false` disables it. Any other value is rejected and the stored flag stays as it was. With the flag off, the reduction formula is the previous one. The search still records the parent tried index, and that store does not change the tree.

## Default pins

Printed from `build/forge` before the edit, and again after it, with Threads 1, Hash 16, OwnBook false, and every other option left at its default. The same three numbers came back from the sanitized test binary.

| check | nodes |
| --- | ---: |
| bench 11 | 312866 |
| bench 13 | 862329 |
| startpos perft 5 | 4865609 |

Build: `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` then `cmake --build build -j`. This machine's `/usr/bin/c++` is Clang 18 and cannot link `libstdc++`, so the configure step used `CXX=g++` (GCC 13.3.0). The pins above are from that binary.

## What changed

`SearchStack::arrival_index` stores the 1-based index of the move that entered the node. The main move loop writes it after singular extension and before the child search. Null-move and probcut children store 0, because those lines are not a late move from the main list. When the option is on and `arrival_index >= 7` and the reply's `move_count <= 4`, the reduction `r` is decremented by one before the usual depth clamp. The futility, history, and SEE depth estimate earlier in the move loop stays on the unreduced formula, so a reply can still be pruned before that one-ply relief applies.

Source diff against `e04556dd` in `forge-combo29/src` and `forge-combo29/include`: 18 insertions, 3 deletions. No `CMakeLists.txt` change.

## Proof the option is live

With the option on, the same release binary and the same Threads 1 / Hash 16 / OwnBook false defaults:

bench 13 = 818656

Turning the option back off returns bench 11 = 312866, bench 13 = 862329, and perft 5 = 4865609.

## Sanitizer

`forge-combo29/tests_r3_04/late_parent_relief.cpp` was compiled with the engine sources, the release defines (`FORGE_PORTABLE` equivalents, `NDEBUG`, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3`), and `-fsanitize=address,undefined -fno-sanitize-recover=address,undefined`. `ASAN_OPTIONS=halt_on_error=1:detect_leaks=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`.

The run checked the `uci` option line, both benches, perft 5, then 200 searches to depth 10 with the option on (3,670,382 nodes). Every returned move was in the position's legal move list and passed `is_legal`. stderr was empty. Exit status 0. After `setoption name LmrLateParentRelief value false`, the three default pins matched again.

## Re-check

Release binary, 2026-11-14 13:53 UTC, same option defaults: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. With `LmrLateParentRelief` on, bench 13 = 818656. Turning it off restored bench 13 = 862329.

The sanitized test was rebuilt and run again at 13:56 UTC with the same sanitizer flags. It repeated those pins, then walked every move of the PV for the 200 depth-10 searches. Failures 0, 3,670,382 nodes, stderr empty, exit 0. Defaults after the run matched again.

A later release pass at 14:35 UTC printed the same three default pins, bench 13 = 818656 with the option on, and bench 13 = 862329 after turning it off.

No strength claim. Node-count change only shows that the flag affects search.

setoption name LmrLateParentRelief value true
bench 13 nodes 818656

## Follow-up screen

Screening only. Not a strength claim. Same owner binary, `LmrLateParentRelief` on versus off, `nodes=50000`, Threads 1, Hash 16, OwnBook false. The CPU has AVX-512F and BMI2, so the binary is the default Release build (`-march=x86-64-v4`, PEXT sliders, AVX-512 NNUE). No `CMakeLists.txt` change and no `FORGE_*` override. `CXX=g++` was required because `/usr/bin/c++` cannot link `libstdc++`.

Pins on that binary stayed bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. Option on, bench 13 = 818656.

Book `UHO_Lichess_4852_v1.epd` sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Binary sha256 `8919bd97dd07407c40e2d3f14793b691da7b672f4878d366af4e374363e2f7ac`. Source commit `f3ecae11d4cdf9fb58925853e25a340f921b53ba`. Implementation commit `cc48d5aad409661d085e05e0cfae709d5f349c04`. fastchess `alpha 1.8.3 20261107-d7b47e8`, commit `d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75`. The printed Elo +/- uses fastchess 95% z = 1.959963984540054. `Ptnml(0-2)` is LL, LD, WL+DD, WD, WW for the option-on engine.

bench 13 nps, five alternating off/on runs at 15:27 UTC: off 1664727, 1759855, 1735068, 1721215, 1742078; on 1634043, 1663934, 1694939, 1614706, 1640593.

Chunks of 500 sequential openings, two games each, option on named first, stop at 9 chunks or 6 hours. Per-chunk PGN and summary files are under `forge-combo29/tests_r3fu_04/`. The full command is in `forge-combo29/tests_r3fu_04/screen-setup.txt`.

### Chunk 0001

Openings 1-500. 1000 games. 00:51:10. Option on first. W-L-D 257-259-484. Elo 95% -0.69 +/- 13.86. LOS 46.08%. Ptnml(0-2) [25, 115, 215, 127, 18]. Points 499.0 (49.90%). Screening measurement only.
