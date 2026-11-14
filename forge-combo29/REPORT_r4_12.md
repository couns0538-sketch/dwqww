# R4-12 — empty move UCI string

Finding 12 from `audit/lock-source` at `302a08a272fbe8e8c4463731f3b9cd72d72d3f48` (`forge-combo29/AUDIT_lock_source.md`). Proof in that audit was by reading `src/board.cpp`.

`Board::move_to_uci(Move::none())` formatted the empty move as `a1a1`. `Move::none()` is `from == 0`, `to == 0`, and `is_none()` is `from == to`, so the formatter printed square a1 twice. UCI null moves are `0000`. The UCI loop already special-cased `from == to` before printing `bestmove`; the public formatter did not.

## Reproduction on `e04556ddc`

`forge-combo29/tests_r4_12/empty_move_uci.cpp`, built with address and undefined sanitizers against the base sources (the one-line guard not yet present):

```text
move_to_uci(none)=a1a1
FAIL empty move formatted as "a1a1" expected "0000"
```

Exit code 1.

## Fix

`forge-combo29/src/board.cpp`, `Board::move_to_uci`:

```cpp
if (move.is_none()) return "0000";
```

That is the audit's proposed change. No `CMakeLists.txt` edit. No new option, and the existing search options stay off by default. Ordinary moves are unchanged (`e2e4`, `a1b1`, `a7a8q`).

## Sanitizer run

`g++` 13.3.0. Definitions are the lock set from `forge-combo29/CMakeLists.txt` (`FORGE_NNUE_HIDDEN=256`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_PREFETCH_EARLY=1`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`) plus `-O1 -g -ffp-contract=off -fno-fast-math -march=x86-64-v4 -UNDEBUG -fsanitize=address,undefined -fno-sanitize-recover=address,undefined -fno-omit-frame-pointer`.

Command: `bash forge-combo29/tests_r4_12/run_f12.sh`

`ASAN_OPTIONS=halt_on_error=1:abort_on_error=1` and `UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1:print_stacktrace=1`. A failed check in the test returns 1. A sanitizer finding aborts.

```text
move_to_uci(none)=0000
move_to_uci(e2e4)=e2e4 move_to_uci(a1b1)=a1b1 move_to_uci(a7a8q)=a7a8q
bench11 312866 bench13 862329 perft5 4865609
depth10 searches 200 legal_ok 1 total_nodes 4020860
PASS r4_12 empty move uci
```

Exit code 0. No address or undefined sanitizer report.

Pins held at the defaults: bench depth 11 `312866`, bench depth 13 `862329`, startpos perft 5 `4865609`. The 200 depth-10 searches (same position walk as `tests_t22`) each returned a legal best move, and every move on a non-empty PV was legal in sequence.
