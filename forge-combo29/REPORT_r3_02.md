# ThreatHistory (r3-02)

A second quiet-move history table, off unless UCI option `ThreatHistory` is set. Default search is unchanged.

## Idea

The idea is Stockfish’s threat-indexed quiet history (public Stockfish search work, about 2024–2025): keep the usual from-to quiet history, and add another from-to table whose index also records whether the moving piece is attacked by a strictly cheaper enemy piece and whether the destination square is. Every line here was written for this engine. No Stockfish source, constants, or tables were copied.

“Cheaper” uses this engine’s existing `SeePieceValue` order (pawn, then knight and bishop equal, then rook, then queen). A king is never cheaper: that table stores the king as 0, which would invert the comparison. Nothing is cheaper than a pawn, so pawn quiets stay in bucket 0. The destination is judged against the mover, the piece that would stand there, using the position as it is before the move. The bonus and penalty use the existing history gravity update (`HistoryMax` 16384), the same amount already applied to the main quiet history, including the quarter bonus on a quiet PV move that does not cut.

## Behaviour

`ThreatQuietHistory` is `[side][0..3][from][to]`. Bit 1 of the middle index means the mover is threatened. Bit 0 means the destination is. `Worker::quiet_history` adds the entry, so history pruning and late-move reduction see it. The speed-2 move picker adds the same entry when it scores quiets and evasions. Updates follow the main quiet history: the cutoff move, the quiets that failed, and the non-cutting PV quiet. With the option off those paths add 0 and do not write the table.

`uci` lists `option name ThreatHistory type check default false`. `setoption name ThreatHistory value true|false` stores it. Any other value is rejected.

Source diff in `forge-combo29/src` and `forge-combo29/include`: 64 insertions, 7 deletions.

## Pins

Threads 1, Hash 16, OwnBook false, every option at default, before the change and again after it:

- bench 11 = 312866
- bench 13 = 862329
- `position startpos` / `go perft 5` = 4865609

Release build: `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` then `cmake --build build -j` (Clang 18).

## Tests

`forge-combo29/tests_r3_02/threat_history_test.cpp` checks the option text and the default, the threat index on hand positions (pawn, knight-attacked rook, equal-value bishop, pawn-attacked queen, destination-only pawn attack, queen not cheaper than a rook, both squares attacked by a queen, king not cheaper), and the same index against `attackers_to` plus `SeePieceValue` on 1630 quiet moves from walked games. A depth-8 search of the Kiwipete position changes node count when the option is on (16646 off, 16740 on). Two hundred depth-10 searches with the option on each return a move present in `legal_moves()` that also passes `is_pseudo_legal` and `is_legal`. CMakeLists.txt was not changed; the test is not part of the `forge` target.

The same test was compiled with g++ 13 `-O2 -fsanitize=address,undefined -fno-sanitize-recover=undefined` and the engine’s portable search defines. It exited 0. No ASan or UBSan report. All 200 moves were legal.

## Re-check

Repeated on `grok47/r3-02-threat-history` at `e4daba905` plus the oracle test, without treating the first run as final. Release binary rebuilt with the same Clang 18 CMake command. Threads 1, Hash 16, OwnBook false.

At 2026-11-14T13:54:51Z, defaults again: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. `ThreatHistory` still defaults to false. With `setoption name ThreatHistory value true`, bench 13 = 643379.

At 2026-11-14T13:57:04Z the g++ 13 ASan/UBSan binary exited 0: oracle agreed on 1630 quiet moves, depth 8 was 16646 off and 16740 on, and all 200 depth-10 moves were legal.

At 2026-11-14T14:16:50Z the same release binary repeated the defaults (bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609) and ThreatHistory bench 13 = 643379.

At 2026-11-14T14:35:25Z those four counts were unchanged. At 2026-11-14T14:36:09Z a fresh g++ 13 `-fsanitize=address,undefined -fno-sanitize-recover=undefined` build exited 0 again: 1630 oracle agreements, depth 8 nodes 16646 off and 16740 on, and 200 legal depth-10 moves.

Not measured: playing strength, multi-thread searches, or time-control searches. Clang’s compiler-rt archive was not installed, so the sanitizer run used g++ rather than the Clang release binary. `tests_t16/options.expected.txt` still snapshots the old option list and was left untouched.

## Follow-up

The destination threat bit used the position occupancy with the mover still on its origin. A slider on the same line, with the mover between it and the destination, did not count. The destination test now uses occupancy with the origin square cleared. The origin test is unchanged. No `FORGE_*` define was added or removed, and `CMakeLists.txt` was not edited.

The CPU has AVX-512F and BMI2, so the binary is the owner release build: `cmake -S forge-combo29 -B build-owner -DCMAKE_BUILD_TYPE=Release` (default `-march=x86-64-v4`, PEXT and ZMM on). Threads 1, Hash 16, OwnBook false, ThreatHistory left off: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

`tests_r3fu_02/xray_destination_test.cpp` covers the queen move whose destination is behind the mover on a rook file (index 3), the square between the rook and the queen (index 3), and a destination off that file (index 2). The earlier threat-history suite still passes, including the attacker oracle on 1630 quiet moves.

Bench 13 nps on this binary, five alternating runs, option off then on. Node counts stayed 862329 and 643389.

| run | off nps | on nps |
| --- | ---: | ---: |
| 1 | 1850491 | 1620627 |
| 2 | 1796518 | 1649715 |
| 3 | 1834742 | 1653956 |
| 4 | 1684236 | 1557842 |
| 5 | 1724658 | 1596498 |

Screening uses that same binary. ThreatHistoryOn is listed first. Each chunk is 500 sequential openings from `UHO_Lichess_4852_v1.epd`, both colors (`-rounds 500 -games 2`), `nodes=50000`, Threads 1, Hash 16, OwnBook false, concurrency 2. Chunks continue until 6 hours from the start of the screen. This is a screen, not a strength claim.

```
/tmp/screen-r3-02/fastchess-linux-x86-64/fastchess \
  -engine cmd=/tmp/screen-r3-02/forge name=ThreatHistoryOn option.Threads=1 option.Hash=16 option.OwnBook=false option.ThreatHistory=true \
  -engine cmd=/tmp/screen-r3-02/forge name=ThreatHistoryOff option.Threads=1 option.Hash=16 option.OwnBook=false option.ThreatHistory=false \
  -each nodes=50000 \
  -openings file=/tmp/screen-r3-02/UHO_Lichess_4852_v1.epd format=epd order=sequential start=N \
  -rounds 500 -games 2 -concurrency 2 -ratinginterval 100 -recover \
  -pgnout file=chunkNNN.pgn nodes=true
```

Versions: engine `Chess Engine Forge 6.4.24 candidate` (UCI), Clang 18.1.3, fastchess alpha 1.8.3 compiled for ubuntu-22.04 20261107-d7b47e8. Book sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Binary sha256 `9949d8950cea9334e5e325221e2da28e7d7b94a098ebb46a76eb00b18d1bae1f`. Per-chunk W-L-D, Elo 95%, LOS, and pentanomial are in `tests_r3fu_02/`.

Chunk 001 finished at 2026-11-14T16:48:10Z (openings 1-500, 1000 games, fastchess exit 0). ThreatHistory on: 249-279-472, Elo -10.43 +/- 13.68, LOS 6.73%, Ptnml(0-2) [26, 122, 225, 110, 17]. See `tests_r3fu_02/chunk001_summary.md`. Not a strength claim.

option.ThreatHistory=true
bench 13 nodes 643389
