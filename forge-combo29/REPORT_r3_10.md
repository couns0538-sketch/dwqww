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

`forge-combo29/tests_r3_10/evasion_ordering_test.cpp` was compiled with the same portable defines and `-fsanitize=address,undefined` (and `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3`). The option was on for the search loop. Each returned root move has to be legal, and each move of the principal variation has to be legal in the position it is played from.

First run, before the principal-variation walk was added:

- default pins: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609
- bench 13 with the option on: 772890
- 200 searches at depth 10: 9 roots in check, 0 illegal root moves
- no AddressSanitizer or UndefinedBehaviorSanitizer output, exit 0
- bench 13 after clearing the flag: 862329

Second and third runs, with the line walk:

- same three default pins, same 772890, same restored 862329
- 200 searches, 9 roots in check, 2360 principal-variation moves, 0 illegal
- both runs exited 0 with no sanitizer output

## Re-check

The same release binary was measured again in fresh processes, still Threads 1, Hash 16, OwnBook false, other options default. g++ 13.3, portable `x86-64-v3` build.

| check | result |
| --- | ---: |
| bench 11, option off | 312866 |
| bench 13, option off | 862329 |
| startpos perft 5 | 4865609 |
| bench 13, EvasionOrdering on | 772890 |
| bench 11 after turning it off again | 312866 |
| bench 13 after turning it off again | 862329 |

Repeated once more in one process: 312866, 862329, 4865609, then 772890 with the option on, then 312866 and 862329 after turning it off. No strength claim. The different node count only shows that the option changes the tree.

## Not claimed

No games were played. Nothing here is an elo estimate.

setoption name EvasionOrdering value true

bench 13 nodes 772890

## Follow-up screen

Screening only. Not a strength claim. The sentence above that no games were played belongs to the implementation pass. This section is the later on-versus-off screen of the same owner binary.

The CPU has AVX-512F and BMI2, so the binary is the default owner build: `x86-64-v4`, PEXT and the AVX-512 ZMM kernel, no `CMakeLists.txt` edit and no `FORGE_*` override. Pins on that binary stayed 312866, 862329, and 4865609. Bench 13 with the option on stayed 772890 nodes.

Five alternating bench 13 runs, off then on: nps 1752701, 1784965, 1933473, 1908370, 1903596, 1740743, 1639408, 1889706, 1937817, 1797418. Means 1833399 off and 1824240 on. The trees have different node counts, so this is not an equal-work speed comparison.

The match is the same binary twice at 50000 nodes, Threads 1, Hash 16, OwnBook false, `EvasionOrdering` on against off. Openings are `UHO_Lichess_4852_v1.epd` in sequential chunks of 250 openings, each played with colors swapped. W-L-D counts the option-on side first. Details, the command, versions, and sha256 sums are in `forge-combo29/tests_r3fu_10/screen-setup.txt`. Chunk PGNs and their summaries land in that directory as they finish.

Chunk 001, openings 1–250, 500 games, finished 15:44 UTC, exit 0. W-L-D 123-126-251. Elo -2.08 +/- 18.84 (95%). LOS 41.41%. Ptnml(0-2) 3 77 101 58 11. The interval includes zero. PGN `forge-combo29/tests_r3fu_10/chunk-001.pgn`, sha256 `fe8fa418fe6f812772787c1791166cb55e887cad3ffa375cb1eec92e525e878e`.
