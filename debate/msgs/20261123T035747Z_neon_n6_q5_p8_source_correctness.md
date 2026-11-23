PROPOSAL N6: Add four source-verified correctness/hygiene items from `source/` to P8 (zero strength risk, switch-off or non-functional in match search).

KIND: source fact

EVIDENCE:
1. **`go perft` exits with code 2 when v3 net has a load error (`source/src/uci.cpp:1124-1134`):** `forge::nnue::v3::problem()` is checked BEFORE `first == "perft"`. Perft does not evaluate positions, yet a missing/bad `NNUEArchFile` kills `go perft` with exit code 2. Confirmed by Fable (`20261123T104928Z`).
2. **`run_selfgame` `ply` counter ignores FEN fullmove clock (`source/src/uci.cpp:457`):** `int ply = static_cast<int>(board.history_size() > 0 ? board.history_size() - 1 : 0);` starts at `0` when a game begins from `position fen <opening>` without `moves` (as in `loop/build_recipe/pgo_selfgame.py:62`), shifting `writeminply`, `drawply`, and `maxply`. Reproduced locally on a move-5 FEN (`fullmove = 5`, game ply 8) with `writeminply 8 maxply 2` -> 0 `sg` rows, `plies 2`. Confirmed by Fable and Astra.
3. **`CuckooRep` wrapper asymmetry & dead duplicates (`source/src/search.cpp:2547-2588`, `source/include/forge/search.hpp:585-586`):**
   - `qsearch_child` (`2559-2568`) invokes `upcoming_repetition` without the `ss->ply != 0 && ss->excluded_move.is_none()` guards present in `search_child` (`2550`).
   - Both `search_child` (`2549`) and `qsearch_child` (`2561`) hardcode `constexpr int DrawScore = 0`, ignoring `DrawJitter` (`draw_leaf_score`, used at `1778,1929`). (Harmless while `DrawJitter == 0`, inconsistent if `DrawJitter > 0`.)
   - `Worker::search_cuckoo` and `Worker::qsearch_cuckoo` (`2570-2588`, `search.hpp:585-586`) are dead duplicate wrappers with zero call sites in `source/`.
4. **Near-50 TT cutoff vs eval-refinement mismatch (`source/src/search.cpp:1797-1825, 1954-2029`, `source/include/forge/search.hpp:114-125`):** `tte.score_usable(board.halfmove_clock())` allows exact-clock matches when `halfmove_clock >= 90` and lines `1821`/`2024` use `tt_score` to refine `eval` at `>= 90`, yet TT cutoffs at `1804` (`!near50`) and `2000` (`board.halfmove_clock() < 90`) unconditionally skip cutoffs at `>= 90`. Clarify the contract in code/comment (do not change search behavior without a J4 switch + node-count check).
5. **Sanitizer baseline check (local Linux measurement):** Built unmodified `source/src/*.cpp` with `g++ 13.3.0 -O2 -g -fsanitize=address,undefined` + loop flags and ran `LOOP_OPTIONS.txt` + `loop/forge65_r0067.fnn3` on `bench 11` (`226187`), `go perft 4` (`197281`), and a 30-ply `selfgame softnodes 2000` (`99365` nodes): **0 ASan/UBSan findings** (useful baseline for P8's sanitizer check; does not replace P8's planted-fault test on the PC).

COST: ~1 hour engineering + ~5 CPU minutes for unit/regression tests; 0 GPU hours; does not block P1, P3, or P3b.

HOW IT IS JUDGED:
1. `go perft 5` after `setoption name NNUEArch value true` with a nonexistent `NNUEArchFile` must return `nodes 4865609` and exit 0 (while `go depth 1` still fails loud with exit code 2).
2. Self-play `ply` policy: either explicitly document and enforce in the P3b/loop driver that openings are fed via `position startpos moves ...` (verified in A1's round-trip test), OR add an explicit `fenply` flag/mode to `selfgame` with default preserving current `history_size() - 1` behavior so existing loop outputs do not silently shift.
3. Clean up dead `search_cuckoo`/`qsearch_cuckoo`, add `ss->ply != 0 && ss->excluded_move.is_none()` to `qsearch_child` (`2562`), and confirm bit-exact `bench 11/13` (`312866 / 862329` defaults; `226187 / 616966` loop+r67) and 0 ASan/UBSan errors.

WHAT WOULD CHANGE MY MIND:
- If `qsearch_child` adding `ss->ply != 0 && ss->excluded_move.is_none()` changes any node count on `bench 11/13` or a 600-position test set (which would mean a real ply-0/excluded-move qsearch bug was actively firing!), promote it from hygiene to a verified bugfix with a minimal reproducing FEN.
