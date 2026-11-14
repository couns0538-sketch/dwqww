# AspCappedReopen

One UCI check, `AspCappedReopen`, default false. Listed in the `uci` answer. Off, the root loop is the previous one. On, a root fail reseeds only the failed bound.

## Where the idea comes from

Iterative deepening already searches depth 4 and up in a window around the previous score (`AspirationDelta`, 18). A fail moves that side by `delta`, then grows `delta` with `delta += delta / 2 + 4`. A fail-low also sets beta to the midpoint of the old window. That is the usual aspiration window: a narrow band around the last score, reopened on the side that failed. The public write-up of that technique is the Chess Programming Wiki page Aspiration Windows (https://www.chessprogramming.org/Aspiration_Windows). No source from another engine was used.

`AspCappedReopen` is the extra rule from this task, written into that loop. On a fail, the failed bound sits 13 centipawns past the score that came back, and that step does not grow. If the score is a mate (`is_mate_score`) or at or beyond ±640, that side is set to `-Infinite` or `Infinite` before the re-search. 13 and 640 were chosen here. 13 is below this engine's own first delta of 18, so the first fail is already a different window. 640 is the line treated as decisive. Mate scores in this engine are already past 640; the mate test is still written out so a mate opens fully on its own.

The fail-low midpoint update of beta is unchanged with the option on. The initial window, before any fail, is still the previous score ± `AspirationDelta`.

## What changed

- `forge-combo29/include/forge/search.hpp`: `tune::AspCappedReopen`.
- `forge-combo29/src/search.cpp`: the flag, `capped_fail_low`, `capped_fail_high`, and the root fail branch.
- `forge-combo29/src/uci.cpp`: the option line and `setoption`.
- `forge-combo29/tests_r3_08/asp_legal_test.cpp`: 200 depth-10 searches, plus a checked king, a promoting pawn, checkmate, and stalemate.

`git diff --numstat` on `src` and `include`: 41 insertions, 3 deletions (44 changed source lines).

`option name AspCappedReopen type check default false`

## Pins

Threads 1, Hash 16, OwnBook false, every other option at default. Measured before the edit, after the edit, and again at 2026-11-14T14:36:18Z on this branch:

| check | nodes |
| --- | --- |
| bench 11 | 312866 |
| bench 13 | 862329 |
| go perft 5 from the start position | 4865609 |

Build: `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j`

With the option on, the same release binary, same Threads / Hash / OwnBook settings. The 14:36Z re-check measured bench 13. Turning the option back off in that same process returned bench 13 to 862329.

| check | nodes |
| --- | --- |
| bench 13 | 850997 |
| bench 11 | 347390 |

bench 13 moving from 862329 to 850997 is the liveness check. No strength claim. bench 11 with the option on is from the first measurement, not the 14:36Z re-check.

## Sanitizer

`tests_r3_08/asp_legal_test.cpp` turns `AspCappedReopen` on, builds 200 positions by walking legal moves from the start position, and searches each to depth 10 with Hash 16 and one thread. Every returned move has to be in that position's legal move list. A terminal root has to return no move. The same run also searches a king in check, a pawn that can promote, a checkmate, and a stalemate.

Clang 18 could not link its ASan runtime (`libclang_rt.asan` is not installed). The run used g++-14 with `-fsanitize=address,undefined -fno-sanitize-recover=address,undefined`, plus the portable release defines (`FORGE_PORTABLE` switches, `-ffp-contract=off -fno-fast-math -march=x86-64-v3`) and `-DFORGE_UCI_NO_MAIN`.

Rebuilt and run again at 2026-11-14T14:36:21Z. Result: `asp_legal ok searches 200 legal 200 terminals 0 edges 4 depth 10`, exit 0. No ASan or UBSan report.

## Not verified

Playing strength was not measured. How often the mate or ±640 full-open branch ran during bench or the 200 searches was not counted. MultiPV and clock games with the option on were not given their own pins.

setoption name AspCappedReopen value true

bench 13 nodes 850997

## Follow-up screen

Screen only. Same binary, `AspCappedReopen` on against off. Not a strength claim.

CPU has AVX-512F and BMI2, so the binary is the owner build: `cmake -S forge-combo29 -B /tmp/forge-owner-build -DCMAKE_BUILD_TYPE=Release` with the file's defaults (`FORGE_MARCH=x86-64-v4`, `FORGE_PORTABLE=OFF`). No `CMakeLists.txt` edit and no `FORGE_*` override. Pins on that binary, Threads 1, Hash 16, OwnBook false, option off: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

Book: `UHO_Lichess_4852_v1.epd`, 2632036 positions, sequential order, both colors per opening. Match tool: fastchess alpha 1.8.3 `20261113-3d7a4db`. Engine id: Chess Engine Forge 6.4.24 candidate. Compiler: Ubuntu clang 18.1.3. CMake 3.28.3.

sha256 forge `580ca05934c3b0f24e92d401664a2f1beea1f870db6efad0b20a319646a9dc51`
sha256 fastchess `936811dcaea97a853a762d3f1e6fb600610c1be3c1f759f2f2fefa2e6500b21e`
sha256 book `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`

bench 13, five alternating runs, off first, same binary. Nodes stay 862329 off and 850997 on. nps is machine time, not a speed claim:

| run | side | nodes | ms | nps |
| --- | --- | --- | --- | --- |
| 1 | off | 862329 | 843 | 1022928 |
| 2 | on | 850997 | 606 | 1404285 |
| 3 | off | 862329 | 667 | 1292847 |
| 4 | on | 850997 | 698 | 1219193 |
| 5 | off | 862329 | 917 | 940380 |

Chunk 001 is openings 1-10, 20 games, `nodes=50000`, concurrency 2. Option on is the first engine. W-L-D 3-7-10. Elo 95% -70.44 +/- 92.08. LOS 5.69%. Pentanomial (0-2) [1, 3, 5, 1, 0]. The interval covers both sides of 0.

Chunk 002 is openings 11-210, 400 games, finished 2026-11-14T16:01:02Z, exit 0, no illegal moves or disconnects. W-L-D 105-104-191. Elo 95% 0.87 +/- 22.16. LOS 53.07%. Pentanomial [9, 49, 82, 52, 8].

Chunk 003 is openings 211-450, 480 games, finished 2026-11-14T16:33:21Z, exit 0. W-L-D 122-128-230. Elo 95% -4.34 +/- 19.26. LOS 32.91%. Pentanomial [7, 67, 98, 61, 7].

Chunk 004 is openings 451-690, 480 games, finished 2026-11-14T17:05:33Z, exit 0. W-L-D 137-126-217. Elo 95% 7.96 +/- 21.67. LOS 76.47%. Pentanomial [13, 57, 91, 64, 15].

Chunk 005 is openings 691-930, 480 games, finished 2026-11-14T17:33:50Z, exit 0. W-L-D 110-119-251. Elo 95% -6.52 +/- 18.56. LOS 24.54%. Pentanomial [7, 65, 102, 62, 4].

Chunk 006 is openings 931-1170, 480 games, finished 2026-11-14T17:53:57Z, exit 0. W-L-D 114-127-239. Elo 95% -9.41 +/- 19.50. LOS 17.17%. Pentanomial [11, 62, 102, 59, 6].

Cumulative 2340 games: W-L-D 591-611-1138. Elo 95% -2.97 +/- 8.99. LOS 25.86%. Pentanomial [48, 303, 480, 299, 40]. Still a screen. The interval covers 0.

PGNs and summaries are under `forge-combo29/tests_r3fu_08/`. `pgn_screen.cpp` recounts them. Later chunks continue at opening 1171.
