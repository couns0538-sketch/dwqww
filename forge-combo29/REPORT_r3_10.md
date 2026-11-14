# Evasion ordering (r3-10)

`EvasionOrdering` is a UCI check option, default `false`. With it off, move ordering is unchanged. With it on, a node that is in check — in the main search and in quiescence — orders its evasions as follows:

- a capturing evasion scores `2000000 + victim value + capture history`
- a quiet evasion scores the same quiet-history mix the non-check quiet picker already uses (main history, plus the two previous continuation histories, plus the existing direct-check bonus)
- the capture band sits above quiet history and above the old promotion scores, so captures are tried first

The transposition-table move is still tried before that list. Non-capturing promotions keep the previous most-valuable-victim score. They stay below captures and above quiets.

## Where the idea comes from

When the king is in check, the only legal moves are evasions: captures of the checker, blocks, and king steps. Trying captures before quiet evasions is the usual alpha-beta policy, because a capture changes material and often ends the check at once. Among those captures, a flat most-valuable-victim / least-valuable-attacker order ignores which captures have actually cut off in this search. Adding the engine's own capture-history entry to the victim's piece value lets a capture that has been failing drop behind one that has been working, while a queen is still ahead of a pawn when the histories are equal.

Quiet evasions have no victim. They are interpositions and king moves, so the right rank is the quiet-history mix this picker already uses for non-check quiets: the side-to-move butterfly history plus continuation history. That mix was already the quiet-evasion score. The option does not replace it.

No table, constant, or source line was taken from another engine. Victim values are this tree's `SeePieceValue` (pawn 100, knight 300, bishop 300, rook 500, queen 900). Capture history is `Worker::capture_history_value`. Quiet scores go through the existing quiet scorer. The `2000000` band is only there so a capture stays ahead of the `1000000` band this file already uses for promotions, and ahead of a quiet score (a few `int16` history terms plus the existing `12000` check bonus).

Both search modes already share one picker. If `board.in_check()` is true, the picker enters the evasion stages whether the caller is the main search or quiescence. The new score is in `MovePicker::generate_evasions`, so both see it. Quiescence that is not in check still generates captures only.

## Default engine

Measured on the unmodified tree at `e04556dd`, then again after the patch with the option left off. Threads 1, Hash 16, OwnBook false, every option at its default. The build was

`cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DCMAKE_CXX_COMPILER=g++`

and `cmake --build build -j`. GCC 13.3. The machine's default `c++` is Clang 18, and it cannot link `libstdc++` here (it looks for a GCC 14 library that is not installed), so the prescribed flags were compiled with `g++`.

| check | before any change | after, option off |
| --- | ---: | ---: |
| bench 11 | 312866 | 312866 |
| bench 13 | 862329 | 862329 |
| startpos perft 5 | 4865609 | 4865609 |

Turning the option back off after a run with it on returns bench 13 to 862329.

Source diff in `forge-combo29/src` and `forge-combo29/include`: 18 insertions, 4 deletions. `CMakeLists.txt` was not touched.

## Proof the option is live

Same release binary, after `setoption name EvasionOrdering value true`:

bench 13 = 772890 nodes.

That is not a strength result. It only shows the search walks a different tree.

## Legality under sanitizers

`forge-combo29/tests_r3_10/evasion_ordering_test.cpp` was compiled with the same portable defines and `-fsanitize=address,undefined` (and `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3`), then run once. The option was on.

- default pins inside that binary: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609
- bench 13 with the option on: 772890
- 200 fixed-depth searches at depth 10, one thread, 16 MB hash: 9 of the roots were in check, 0 returned moves were illegal
- AddressSanitizer and UndefinedBehaviorSanitizer printed nothing
- the process exited 0 (`PASS evasion_ordering`)
- bench 13 after clearing the flag: 862329

## Not claimed

No games were played. Nothing here is an elo estimate.

setoption name EvasionOrdering value true

bench 13 nodes 772890
