STATE: READY FOR TIMING

# b2_no_zero_movelists: FORGE_SPD_NO_ZERO_MOVELISTS (spec S1: no zero fill of the move arrays; value 2 adds quiets-only generation)

Worker b2mg (fable), job B part 2, branch opus-speed-20261105. Builds 09:20-09:30, checks 09:30-09:48 PC clock (chain log
`F:/ospd/jobb/b2/no_zero_movelists/chain_a.log`), notes finished 09:50 (`date`).
Patch: `F:/ospd/wt/opus_speed/patches/b2_no_zero_movelists.patch` (adds 192 lines, removes none; files board.hpp, board.cpp,
search.cpp; applies with `patch -p1` to a fresh lock copy and reproduces `F:/ospd/src/b2_no_zero_movelists`: apply test in
`F:/ospd/src/b2_applytest_no_zero_movelists`). One switch line `#define FORGE_SPD_NO_ZERO_MOVELISTS 0` in board.hpp
(flip to 1 = steps 1-2, to 2 = steps 1-3; both values were checked). Verify variant (not for stacking, no patch written):
`F:/ospd/src/b2_no_zero_movelists_verify`. Deliverable patches of this job: b2_nnue_zmm, b2_no_zero_movelists, b2_matkey_fast,
b2_pickbest, b2_slider_pext (b2_nnue_zmm_verify.patch in the same folder is a record of the verify variant, not a deliverable).

## Design (own words)
Value 1 (spec steps 1-2): `Move` loses its four `= 0` default member initialisers, so it is trivially default-constructible.
`Move{}` and `Move::none()` are value-initialised (all zero) as before; only default-initialised objects lose the fill:
`MoveList::data_` (the 0x400 part of every `MoveList`), the picker's `moves_` (256 x 8 B = 0x800), `bad_captures_`,
`check_squares_`, and the main node's `quiets_tried` / `captures_tried`. Every read of those is below a count that was
written first (pick_best reads `moves_[index_ < count_]`; `bad_captures_[bad_index_ < bad_count_]`; `check_squares_[1..6]`
after `init_check_squares`, index 0 never read; the stats readers take `quiet_count` / `capture_count`; `MoveList` reads
below `size_`). The bare `Move x;` at search.cpp:827 (qsearch), :1005 (ProbCut) and :1044 (main) are assigned in their
`while` condition before any read; `Book::Candidate` is only ever aggregate-initialised (book.cpp:154), so book.hpp is
untouched; every other `Move` member keeps its `{}` (killers_, counter_, SearchStack, TTEntry, root arrays).
Value 2 (spec step 3): `Board::generate_pseudo_legal` gets a `GenMode {All, Captures, Quiets}` entry (the bool entry stays
as an inline wrapper for the lock's callers); Quiets emits single and double pawn pushes, then N, B, R, Q, K over the
empty squares in bit order, then castling under the same `checkers_ == 0` test, and skips the promotion-push, pawn-capture
and en-passant loops. `MovePicker::generate_quiets` calls it and drops the `is_capture() || is_promotion()` filter.
Why the same order: in the full list the pushes come first and the castles last; each piece's targets (`~own`) are popped
in bit order with captures and quiets interleaved; the filter removes exactly the captures, promotions and ep moves, and
what is left per piece is the bit-ordered pop of (attacks & empty) - the quiets list. Evasions, legal_moves,
has_legal_move and perft keep the lock's generator (they only lose the fill through value 1).

## Lines touched (lock numbering)
- include/forge/board.hpp: switch block before `struct Move` (:34); :35-38 members without `= 0` under the switch;
  :109 the `GenMode` enum + overload + wrapper under `>= 2` (lock declaration under `#else`).
- src/board.cpp: :425-540 `generate_pseudo_legal` body with the mode under `>= 2`, the lock function verbatim under `#else`.
- src/search.cpp: :450 `moves_`, :453 `bad_captures_`, :459 `check_squares_`, :1034-1035 `quiets_tried` / `captures_tried`
  without `{}` under the switch; :523-536 `generate_quiets` quiets-mode body under `>= 2`, lock body under `#else`.
- Switch 0: `g++ -E -P` of all eight .cpp files is byte-identical to the lock's (`F:/ospd/jobb/b2/no_zero_movelists/pp/`),
  and the switch-0 exe equals the lock plain exe except the PE link bytes (check (a)).

## Checks
(a) switch-0 exe `forge_nzm_off.exe` (sha256 fd830736...) vs lock plain: `cmp -l` differs only at bytes 137 138 217 218. PASS.
(b) value 1 `forge_nzm_on1.exe` (fdfa21f5...): net on vs `lock_plain_neton.json` with the pins: 24/24 OK, NODE IDENTITY ALL OK
    (`nzm_on1_neton.compare.log`); net off (UseNNUE=false) with the net-off pins: 24/24 OK (`nzm_on1_netoff.compare.log`).
    value 2 `forge_nzm_on2.exe` (3aa38e13...): net on 24/24 OK (`nzm_on2_neton.compare.log`); net off 24/24 OK
    (`nzm_on2_netoff.compare.log`). All under `F:/ospd/jobb/b2/no_zero_movelists/`, chain log `chain_a.log`.
(c) poison build value 1 `forge_nzm_verify1.exe` (81d9dbcb...; every array that lost its fill, and every MoveList, is
    memset to 0xA5 at construction): lp_check net on = pins + 8 FENs d13 + bestmoves all equal to the lock (24/24 OK,
    `nzm_verify1_neton.compare.log`) -> no read depends on the fill.
    poison + assertion build value 2 `forge_nzm_verify2.exe` (7018ea78...; poison as above, and at every generate_quiets
    call the lock's filtered full list is compared element by element with the quiets list, abort on a difference,
    count printed at exit):
    - lp_check net on: 24/24 OK, NODE IDENTITY ALL OK (`nzm_verify2_neton.compare.log`);
    - `bench 16`: nodes 3024920 (= pin), "FORGE_SPD_NO_ZERO_MOVELISTS_ASSERT: 296865 generate_quiets calls compared,
      0 mismatches" (`nzm_verify2_bench16.log`, `.stderr`);
    - 12k FENs (`fens_12k_v2.txt`: `fens_12k.txt` holds placement-only lines the lock rejects, "FEN must contain six fields";
      `go depth 2`, one process, driver `F:/ospd/jobb/b2/tools/uci_fens.py`): 12000/12000 answered, engine exit 0,
      "51059 generate_quiets calls compared, 0 mismatches" (`nzm_verify2_12k_d2.run.log`, `.tsv`, `.tsv.stderr`).
    objdump liveness (plain -O3 builds, `objdump/`): lock plain has memset calls of 0x800 + 0x400 in Worker::search (2 x) and
    qsearch (1 x) and 0x408 (MoveList) in legal_moves, has_legal_move, pseudo_legal_moves, perft, parse_uci; value 1 / 2:
    all of those are gone (0x800: 6 -> 3, 0x400: 7 -> 4, 0x408: 6 -> 0); the survivors sit in Searcher::set_threads, the
    Worker constructor, the Searcher-level Worker::search (root arrays, per search) and nnue update / refresh (the lock's
    own). `rep stos` 13 -> 13, all in CRT / libstdc++ functions (perft's fill was the 0x408 memset here, not rep stos).
    vfmadd 0 in every exe (build logs).
    Not run: valgrind / MSan (no Linux here; CI item for the coordinator).

## Risks
- Reading an unwritten slot would be UB; the poison build shows no read depends on the fill over the pins, the 8 FENs and
  (value 2) the 12k FENs, but it cannot prove the absence of a read on a path those runs never take. The audit above
  covers every reader of the changed arrays in the lock source.
- Value 2 touches the generator entry: any later edit of the full generator's order must be mirrored in the Quiets mode
  (the assertion build catches it).
