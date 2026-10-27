# S-IT: intended-threefold claim (FIDE 9.2.1), UCI `IntendedThreefold` (default false)

## What it does
`setoption name IntendedThreefold value true`: at every non-root search node and every quiescence node, the side
to move may claim a draw when one of its legal moves would create the third occurrence of a position (FIDE 9.2.1).
That right is a floor at the draw score (0):
- `beta <= 0`: the node returns 0 (fail high on the claim alone).
- Otherwise alpha is raised to 0 and the node's value is `max(search value, 0)`, so a mate still beats the
  optional draw (mate precedence). In search() a window (a, 1) with a < 0 becomes the null window (0, 1) and is
  searched as one (pv_node is recomputed), and a node whose alpha the floor raised does not give the parent's
  move the fail-low continuation bonus (its value 0 lies inside the original window).
- The value depends on the game history. At such a node no TT score is used (no cutoff, no eval refinement), no
  score is stored (main, stand-pat and ProbCut stores) and correction history is not taught. The main stores of
  search() and qsearch() keep only a placeholder: the best move and the static evaluation with the raw score
  `ValueNone` (BoundUpper, depth 0), written only into an empty slot or over an earlier placeholder. Every probe
  then reads `tt_score == ValueNone`, and every use of the score or the bound requires a score.

`Board::can_claim_threefold_by_next_move()` (include/forge/board.hpp, src/board.cpp):
- window: positions after the last irreversible move and strictly after the most recent null move, on the
  resulting position's side-to-move parity; fewer than 8 plies means no claim;
- every key that occurs at least twice in that window is collected (exact matches; a 64-bucket mask only skips
  comparisons); an empty set means no claim;
- otherwise the quiet moves of knights, bishops, rooks, queens and the king (the Quiet moves of
  generate_pseudo_legal()) are walked: the resulting key is computed incrementally and tested against the set;
  only a hit is tested for legality. Captures, pawn moves and promotions are irreversible, and castling drops a
  right every window position still had.

The root is not claimed: there is no UCI draw-claim action.

## Files
- Engine: `include/forge/board.hpp`, `src/board.cpp`, `include/forge/search.hpp`, `src/search.cpp`,
  `src/uci.cpp`.
- Tests: `tests/intended_threefold_tests.cpp` (CTest `forge_intended_threefold_tests`), `tools/uci_regression.py`
  (process-level check; the IntendedThreefold checks run only when the engine advertises the option),
  `CMakeLists.txt`.
- `opus_round1/sol_SIT/`: `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `nps_ab_opts.py`, `mutate_sit.py`,
  `ci_sit.sh`, `logs/`, `FILES.txt`, `SHA256SUMS`.

## Reproduce
```
nice -n 19 bash <b>/tools/build_pc.sh "$PWD" F:/opus_scratch/build/SIT/forge_sit.exe
python -I -B <LA>/2_build/uci_check.py F:/opus_scratch/build/SIT/forge_sit.exe --full          # option off = lock
g++ <box flags> src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp tests/intended_threefold_tests.cpp -o t.exe && t.exe
python -I -B tools/uci_regression.py F:/opus_scratch/build/SIT/forge_sit.exe --log uci.log
python -I -B tools/uci_regression.py <lock.exe> --known-v56 --log uci_lock.log                 # option checks skipped
python -I -B opus_round1/sol_SIT/nps_ab_opts.py <lock.exe> <sit.exe> 8 16 20
python -I -B opus_round1/sol_SIT/nps_ab_opts.py --opts-a IntendedThreefold=false --opts-b IntendedThreefold=true <sit.exe> <sit.exe> 8 16 20
python -I -B opus_round1/sol_SIT/mutate_sit.py --list                                           # planted bugs
python -I -B opus_round1/sol_SIT/mutate_sit.py <tree> <new dir> <mutant>   # each mutant must fail the unit test
```
UCI reproduction of the issue (the option on gives `score cp 0`, off gives about +391; the control gives +391 both
ways):
```
setoption name IntendedThreefold value true
position fen 8/7k/8/8/8/8/8/K1R5 w - - 0 1 moves a1a2 h7h8 a2a1 h8h7 a1a2 h7h8
go depth 1 searchmoves a2a1
```
With material for the claimer (code review): `position fen 7k/1r6/8/8/8/8/8/K2Q4 w - - 0 1 moves a1a2 b7b8 a2a1
b8b7 a1a2 b7b8` + `go depth 2 searchmoves a2a1` gives cp 0 with the option on; `position fen 2r5/7k/8/8/8/8/8/K1Q5
w - - 0 1 moves a1a2 h7h8 a2a1 h8h7 a1a2 h7h8` + `go depth 1 searchmoves a2a1` gives cp -424 both ways.
