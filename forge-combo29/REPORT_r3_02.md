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

`forge-combo29/tests_r3_02/threat_history_test.cpp` checks the option text and the default, the threat index on hand positions (pawn, knight-attacked rook, equal-value bishop, pawn-attacked queen, destination-only pawn attack, queen not cheaper than a rook, both squares attacked by a queen, king not cheaper), that a depth-8 search of the Kiwipete position changes node count when the option is on (16646 off, 16740 on), and that 200 depth-10 searches with the option on each return a move present in `legal_moves()` that also passes `is_pseudo_legal` and `is_legal`. CMakeLists.txt was not changed; the test is not part of the `forge` target.

The same test was compiled with g++ 13 `-O2 -fsanitize=address,undefined -fno-sanitize-recover=undefined` and the engine’s portable search defines. It exited 0. No ASan or UBSan report. All 200 moves were legal.

Not measured: playing strength, multi-thread searches, or time-control searches. Clang’s compiler-rt archive was not installed, so the sanitizer run used g++ rather than the Clang release binary. `tests_t16/options.expected.txt` still snapshots the old option list and was left untouched.

option.ThreatHistory=true
bench 13 nodes 643379
