# DeadMaterial

## Where the idea comes from

This is the ordinary endgame fact, written for this engine and not taken from another engine's code, constants, or tables.

King against king, king and one knight or one bishop against king, and king and two knights against king have no forced mate, so the score is 0. King, bishop and knight against king is won by driving the lone king into a corner of the bishop's colour. In this program `DarkSquares` has bit 0 set, so a1 is dark. A dark-squared bishop uses a1 and h8. A light-squared bishop uses h1 and a8.

The attacker score, in centipawns, is

`48 + 28 * (7 - corner distance) + 12 * (7 - distance between the kings)`.

`corner distance` is the Chebyshev distance from the lone king to the nearer of those two corners. The corner term is larger than the king term, so a step toward that corner still raises the score when the kings move farther apart. The number is from the attacker's point of view, then negated when the lone king is the side to move.

## What the option does

`DeadMaterial` is a UCI check option, default false, and it is listed in the `uci` answer.

With it off, evaluation and the draw shortcut are the previous code. Bench and perft stay on the lock.

With it on, `Worker::static_evaluate` returns the score above before it refreshes an accumulator or calls the network. `corrected_eval` does not add correction history on top of that score. The `eval` command uses the same rule and leaves the hand-crafted and network fields at 0.

Bare kings and king plus one minor are no longer cut off as insufficient material, so the 0 comes from this evaluation and those king moves are searched. Repetition, the fifty-move rule, stalemate, and other insufficient material (such as bishops all on one colour) still draw the old way. Two knights against a king were not an insufficient-material cutoff; they now score 0 when evaluated. Bishop and knight against a king was not a cutoff either; it now gets the corner score instead of the network.

Nothing here is a strength claim. No games were played.

## Pins

Build: `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`, then `cmake --build build -j`. Compiler: g++ 13.3. The `c++` driver on this machine is Clang and does not link `libstdc++`; the pins below were taken with g++ and match the lock.

Threads 1, Hash 16, OwnBook false, every other option left at default. Printed before any edit and again on the final tree:

- bench 11: 312866 nodes
- bench 13: 862329 nodes
- `go perft 5` from the start position: 4865609 nodes

## Tests

`forge-combo29/tests_r3_11/dead_material_test.cpp` checks:

- bare kings, white or black knight, white or black bishop, and two knights on one side, from both sides to move, all score 0
- the start position, a queen, a rook, a pawn, a knight on each side, two bishops, a bishop and a pawn, and bishop plus knight plus a pawn are not these endings
- a light bishop and a dark bishop each score the matching corner above the other corner
- a closer attacking king scores higher, and stepping the lone king toward a8 with a light bishop does not lower the score
- flipping the side to move negates the bishop-and-knight score
- the start position's evaluation components do not change when the option flips
- with the option on, the bishop-and-knight total equals this formula and both the hand-crafted and network fields stay 0; with it off, the network term is not 0 and the total differs
- depth 5 on that bishop-and-knight position: 675 nodes off, 514 nodes on
- 200 generated positions plus five fixtures, searched to depth 10 with the option on: every best move, and every move of the PV, is in the legal move list
- search play, option on, repeats the engine's best move. Distance is Chebyshev distance from the lone king to the nearer corner of the bishop's colour. A dark bishop uses a1 and h8; a light bishop uses h1 and a8. Lone king on a8 against a dark bishop, depth 8 for 16 plies: distance 7 to 3. Lone king on h8 against a light bishop, depth 12 for 20 plies: distance 7 to 4.

Two further lines, same rule, not folded into the test binary: a lone king on d5 against a dark bishop, depth 12 for 20 plies, distance 4 to 3; a lone king on d4 against a light bishop and knight, depth 10 for 40 plies, goes to a1 first (distance 7, the other colour) and is then pushed toward h1, best distance 2, ending distance 3. That is the score pulling the king. It is not a measure of playing strength.

Release run of the test: 0 failures, drive 7 to 3 and 7 to 4, 205 searches, 2275 ms.

Pins were printed again on this tree after that test, with the same three default counts and the same option-on bench count as below.

Sanitizer, `-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all`, halt on error, leak detection on. One run of the depth-10 searches alone: exit 0, 0 failures, 205 searches, 21110 ms. The run that also plays the two corner lines: exit 0, drive 7 to 3 and 7 to 4, 0 failures, 205 searches, 21365 ms. No sanitizer report.

Source diff against `e04556dd` in `forge-combo29/src` and `forge-combo29/include`: 96 insertions and 4 deletions, 100 changed lines.

setoption name DeadMaterial value true

bench 13 with it on: 862343 nodes
