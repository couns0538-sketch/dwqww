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

bench 13 with it on, before the follow-up restored the draw cutoff: 862343 nodes

## Follow-up

The bishop-and-knight score was 48 to 316 centipawns. That sits below the hand-written value of keeping the bishop and the knight, so a search would rather not trade into the won ending. The score is now that material value plus the same corner drive.

The material value uses the hand-written piece values and the same taper as the rest of the evaluation. A bishop and a knight are phase 2 of 24. Middlegame values 365 and 337, endgame values 297 and 281:

`(702 * 2 + 578 * 22) / 24 = 588`

The drive is still `28 * (7 - corner distance) + 12 * (7 - distance between the kings)`. Added to 588, the attacker score is at least 588, and higher when the lone king is nearer a corner of the bishop's colour and the kings are closer. The sign is unchanged: positive for the side with the bishop and knight when that side is to move, and the negation when the lone king is to move.

Bare kings and king plus one minor are an immediate draw cutoff again. The special case in `is_draw` is gone. Two knights against a king still score 0 only when evaluation is reached; they were not part of that cutoff.

Owner build: this machine has AVX-512F and BMI2, so the binary is the CMake default (`FORGE_PORTABLE` off, `-march=x86-64-v4`, PEXT and the AVX-512 network kernel). No `CMakeLists.txt` edit and no extra `FORGE_*` override. `c++` on this machine is Clang and cannot link `libstdc++`, so the compiler is g++ 13.3.0. Option off, Threads 1, Hash 16, OwnBook false:

- bench 11: 312866 nodes
- bench 13: 862329 nodes
- start-position perft 5: 4865609 nodes

bench 13 with the option on, five alternating runs, all 862329 nodes. nps in order off, on, off, on, off: 1357998, 1122824, 1105550, 1451732, 1512857.

Mate test `forge-combo29/tests_r3fu_11/kbnk_mate_test.cpp`: 20 positions, each with both colours holding the bishop and knight, option on, 200000 nodes per move. All 40 games mated the lone king inside 50 moves. Exit 0. A failed check returns non-zero.

Screen: `DeadMaterialOn` first against `DeadMaterialOff`, `nodes=50000`, Threads 1, Hash 16, OwnBook false, book `UHO_Lichess_4852_v1.epd` (sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`). fastchess alpha 1.8.3 (`091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f`). Engine binary sha256 is recorded on each chunk summary. Chunks run for up to six hours and are under `forge-combo29/tests_r3fu_11/screen/`. Each summary has W-L-D for the option-on engine first, Elo with the 95% interval, LOS, pentanomial, the command, and the versions.

setoption name DeadMaterial value true

bench 13 with it on: 862329 nodes
