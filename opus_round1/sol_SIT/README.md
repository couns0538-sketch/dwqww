# S-IT: intended-threefold claim (FIDE 9.2.1), UCI `IntendedThreefold` (default false)

## What it does
`setoption name IntendedThreefold value true`: at every non-root search node and every quiescence node, the side
to move may claim a draw when one of its legal moves would create the third occurrence of a position (FIDE 9.2.1).
That right is a floor at the draw score (0):
- `beta <= 0`: the node returns 0 (fail high on the claim alone).
- Otherwise alpha is raised to 0 and the node's value is `max(search value, 0)`, so a mate still beats the
  optional draw (mate precedence).
- The value depends on the game history. At such a node no TT score is used (no cutoff, no eval refinement), the
  result is not stored, and correction history is not taught.

`Board::can_claim_threefold_by_next_move()` (include/forge/board.hpp, src/board.cpp):
- window: positions after the last irreversible move and strictly after the most recent null move, on the
  resulting position's side-to-move parity; fewer than 8 plies means no claim;
- an exactly duplicated key must exist in that window (a 64-bucket mask only skips comparisons);
- then each legal quiet non-pawn move is checked: its exact resulting key must occur at least twice. Captures,
  pawn moves and promotions are irreversible, and castling drops a right every window position still had.

The root is not claimed: there is no UCI draw-claim action.

## Files
- Engine: `include/forge/board.hpp`, `src/board.cpp`, `include/forge/search.hpp`, `src/search.cpp`,
  `src/uci.cpp`.
- Tests: `tests/intended_threefold_tests.cpp` (CTest `forge_intended_threefold_tests`), `tools/uci_regression.py`
  (process-level check), `CMakeLists.txt`.
- `opus_round1/sol_SIT/`: `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `nps_ab_opts.py`, `mutate_sit.py`,
  `logs/`, `FILES.txt`, `SHA256SUMS`.

## Reproduce
```
nice -n 19 bash <b>/tools/build_pc.sh "$PWD" F:/opus_scratch/build/SIT/forge_sit.exe
python -I -B <LA>/2_build/uci_check.py F:/opus_scratch/build/SIT/forge_sit.exe --full          # option off = lock
g++ <box flags> src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp tests/intended_threefold_tests.cpp -o t.exe && t.exe
python -I -B tools/uci_regression.py F:/opus_scratch/build/SIT/forge_sit.exe --log uci.log
python -I -B opus_round1/sol_SIT/nps_ab_opts.py <lock.exe> <sit.exe> 8 16 20
python -I -B opus_round1/sol_SIT/nps_ab_opts.py --opts-a IntendedThreefold=false --opts-b IntendedThreefold=true <sit.exe> <sit.exe> 8 16 20
python -I -B opus_round1/sol_SIT/mutate_sit.py <tree> <new dir> <mutant>   # planted bugs, see REPORT.md
```
UCI reproduction of the issue (the option on gives `score cp 0`, off gives about +391; the control gives +391 both
ways):
```
setoption name IntendedThreefold value true
position fen 8/7k/8/8/8/8/8/K1R5 w - - 0 1 moves a1a2 h7h8 a2a1 h8h7 a1a2 h7h8
go depth 1 searchmoves a2a1
```
