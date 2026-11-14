# NullSeeVeto

`NullSeeVeto` is one UCI check option. It defaults to false. With it left off, null-move pruning is the same search as before.

The rule comes from this task, not from another engine. Null-move pruning cuts a node off when the side to move can pass and the position still fails high. That cutoff is refused when the opponent already has a legal capture of a dearer piece by a cheaper one, and this engine's static exchange evaluation does not call that capture a material loss (`see_ge` at threshold 0). A piece can be attacked by a cheaper piece and still be safe: if the exchange loses material for the capturer, the cutoff stays allowed. The prices are this engine's `SeePieceValue`. Knights and bishops share that price, so one taking the other is not a cheaper-for-dearer capture. The king is ranked above the queen because `SeePieceValue` stores 0 for the king as a sentinel inside the exchange walk, not as a material price. No table, constant, or routine was copied from another engine.

The check runs only when a null-move cutoff would otherwise be attempted, and only when the option is on. The board is restored before search continues. Turning the option off does not call the check.

## Default pins

Threads 1, Hash 16, OwnBook false, every other option at its default. Measured on the release build (`cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`) before the source change, and again after it.

Before the change, at `e04556dd`:

- bench 11: 312866
- bench 13: 862329
- `go perft 5` from the start position: 4865609

After the change, option off (also after turning the option on and then off, and again on a Clang address/undefined build):

- bench 11: 312866
- bench 13: 862329
- `go perft 5` from the start position: 4865609

An invalid `setoption name NullSeeVeto value maybe` leaves the option off. The next bench 13 stayed 862329.

## Option on

`setoption name NullSeeVeto value true`, then bench 13: 929140 nodes. Same count on the Clang sanitizer binary. That is a different tree from 862329, so the option is live. This is not a strength result.

## Tests

`forge-combo29/tests_r3_07/null_see_veto_test.cpp` checks the predicate on constructed positions, including a loose queen taken by a knight, a rook defended by a pawn whose exchange still wins for the knight, and a rook on the promotion rank whose recapturing pawn promotes and whose exchange loses. The last of those must not veto. Equal captures, a bishop taking a pawn, a pinned capture, and an en-passant position must not veto either. Each of 200 searches to depth 10, with the option on, Hash 16, and one thread, returned a best move that was in the legal list. Every move of the returned principal variation was legal in sequence. The positions are a deterministic walk from the start position.

The same test was built with Clang 18.1.3 `-fsanitize=address,undefined -fno-omit-frame-pointer` against objects built the same way, and run with halt-on-error for both sanitizers and leak detection on. It printed `positions ok`, `searches 200 legal`, and `NullSeeVeto tests passed`, and exited 0 with no sanitizer diagnostic. An earlier g++ 13.3.0 build with the same sanitizers also exited 0 on 200 depth-10 searches of this search code.

Engine diff against `e04556dd`: 39 insertions and 4 deletions in `include/forge/search.hpp`, `src/search.cpp`, and `src/uci.cpp`. `CMakeLists.txt` was not changed.

Repeated at 14:01 UTC and again at 14:37 UTC on the same release binary: bench 11 was 312866, bench 13 was 862329, and start-position perft 5 was 4865609, both before `NullSeeVeto` was enabled and after it was set back to false. bench 13 with the option on was 929140 on both repeats. The Clang address/undefined test printed `searches 200 legal` with exit 0 and no sanitizer diagnostic on both repeats.

Not verified: playing strength, match score, or whether 929140 is better or worse than 862329. No games were played.

option name NullSeeVeto type check default false

bench 13 with NullSeeVeto on: 929140
