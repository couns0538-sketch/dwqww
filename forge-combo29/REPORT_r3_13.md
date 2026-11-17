# QuietExtinction

`QuietExtinction` is one UCI check option. It defaults to false. With every option left at its default, including this one, the engine is unchanged.

## Where the idea comes from

The behaviour was specified for this task. Nothing in the search change was copied from another engine: not the gap, not the reduced margin, and not the control flow.

A quiet move that has already been searched, and still sits far below alpha, is a sign that more ordinary quiets in that node are unlikely to raise alpha. The first such miss halves the futility allowance for later ordinary quiets. A second such miss stops the ordinary quiet tail. Captures, promotions, killers, and the counter-move stay in the list.

## What it does

The option is read only at a non-root node that is not in check, not a mate search, not the bare-king mate-fix path, and not within the fifty-move horizon used by the other pruners (`halfmove_clock + depth < 100`). It also stays off when neither side has a knight, bishop, rook, or queen. That is the pure king-and-pawn case, including bare kings.

A searched quiet counts as a wide miss when its score is at least 176 centipawns below alpha and the best score so far is not a mate-sized loss (`best_score > -MateInMaxPly`). While the best score is still a mate-sized loss, the miss is ignored and no quiet is removed.

- After one wide miss, a later quiet that is not a killer and not the counter-move must beat a futility allowance of half `(FutilityBase + FutilityMultiplier * reduced_depth)`. The depth cap stays `FutilityDepth`. Checks, captures, and promotions are not removed by this test.
- After a second wide miss, the move picker stops returning the rest of the ordinary quiet list. Good captures, bad captures, promotions, killers, and the counter-move are still returned. The quiet that just missed has already been searched.

Root moves are never dropped by this rule, so a finished search still returns a move from the legal root list.

## Default signature

Threads 1, Hash 16, OwnBook false, every option at default, before the change and again on the final binary:

- bench 11 = 312866
- bench 13 = 862329
- `go perft 5` from the start position = 4865609

Turning the option back off reproduces those same three numbers.

## Proof it runs

With `setoption name QuietExtinction value true`, bench 13 searched 602141 nodes. That is not the default 862329.

Source diff in `forge-combo29/src` and `forge-combo29/include`: 42 insertions and 5 deletions.

## Sanitizer

`tests_r3_13/quiet_extinction.cpp` was compiled with `-O3 -fsanitize=address,undefined` and `-fno-sanitize-recover=address,undefined`, the same portable search flags, Hash 16, and one thread. It ran 200 searches to depth 10 with the option on: 197 positions reached by playing 1 to 23 legal moves from the start position, plus `4k3/8/8/3p4/3P4/8/8/4K3 w - - 0 1`, `4k3/8/8/8/8/8/8/4QK2 b - - 0 1`, and the start position. Each search had to finish at depth 10. A position that is not an immediate draw had to search at least one node. The returned move had to be legal and `make_move` had to accept it. A terminal position must return no move.

The same process, still sanitized, checked the default pins before those searches and checked bench 13 again after turning the option back off. It printed:

`perft5 4865609 bench11 312866 bench13_off 862329 bench13_on 602141`

`searches 200 illegal 0 nodes 3592220 bench13_restored 862329`

Exit code 0. A second run of that binary printed the same two lines. No address or undefined-behaviour report was produced.

## Re-check

The release binary was asked again, with Threads 1, Hash 16, and OwnBook false. Defaults stayed bench 11 = 312866, bench 13 = 862329, and start-position perft 5 = 4865609. With the option on, bench 13 stayed 602141. Turning the option off returned bench 13 to 862329. That UCI re-check was repeated and the node counts did not move.

The closing pass at 14:38 UTC did the same. The release UCI loop printed bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609, then bench 13 = 602141 with the option on, then bench 13 = 862329 with it off. The sanitized binary printed the same pin line and `searches 200 illegal 0 nodes 3592220 bench13_restored 862329`, and exited 0.

No strength claim is made. No games were played.

## Follow-up: quiet checks stay in a closed tail

Closing the quiet tail used to skip every remaining quiet, including moves that give check. A closed tail now still returns quiet checks, discovered checks included. Captures, promotions, killers, and counters are unchanged. The option still defaults off.

Owner build on this machine (AVX-512F and BMI2 are present): default CMake Release, `FORGE_PORTABLE` off, `-march=x86-64-v4`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`. No CMakeLists edit and no extra `FORGE_*` flag. Threads 1, Hash 16, OwnBook false:

- bench 11 = 312866
- bench 13 = 862329
- start-position perft 5 = 4865609
- QuietExtinction on, bench 13 = 632155

Five alternating bench 13 runs of that binary, off/on/off/on/off, nps 864923, 879214, 873686, 874349, 903908. The off runs stayed at 862329 nodes. The on runs stayed at 632155. sha256 of `build/forge` at those runs: `ad0bcb5fbe83f231042a87fcb72c4e8f605cf0b41f3b3e824f6d4d18596a5185`. id name: Chess Engine Forge 6.4.24 candidate.

`tests_r3fu_13/quiet_tail_checks.cpp` exits non-zero unless both directed cases pass with the option on. In `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1`, depth 10 plays `g3g6` with a mate score and the PV quiet check `g6h7`, which is the only mating move after `c6e5`. After `g3g6` and `a7a6`, the only mate is that same quiet check, and depth 4 plays `g6h7`. A build that drops quiet checks from the closed tail plays `f6h5` instead of the mate line and fails the test.

No strength claim from the search change itself.

setoption name QuietExtinction value true
bench 13 nodes 632155
