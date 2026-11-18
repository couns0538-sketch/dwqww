Forge Combo29 — `curated_sp_bundle.patch.txt` 10-Piece Zero-Fuzz Review Stack (`r15d` -> `curated`)
====================================================================================================
Base tree: `r15d` (`6b98f217/forge-combo29` + `pc_r15.patch` + `forge-combo29/carbon2/a_speed_pc20_v3.patch.txt` + `forge-combo29/carbon2/job3/e1_legal_check_evasions.patch.txt`).
Application order (each applies cleanly with `patch -p1 -F0`, zero fuzz, onto the tree left by the preceding piece):
  `01_S4.patch.txt` -> `02_S5.patch.txt` -> `03_S5_assert.patch.txt` -> `04_S7.patch.txt` -> `05_G1.patch.txt`
  -> `06_G2.patch.txt` -> `07_G3.patch.txt` -> `08_G4.patch.txt` -> `09_W1.patch.txt` -> `10_W2.patch.txt`
Byte-for-byte telescoping guarantee (`forge-combo29/carbon2/job13/stack_byte_for_byte_diff_raw.txt`):
  `r15d` + `01_S4..10_W2` (`patch -p1 -F0`) == `r15d` + `forge-combo29/carbon2/job11/curated_sp_bundle.patch.txt`,
  verified by `diff -r stack_replayed/src curated_direct/src && diff -r stack_replayed/include curated_direct/include` (`0` bytes output, exit code `0`).

----------------------------------------------------------------------------------------------------
Piece 01: `01_S4.patch.txt` (`S4`: Slim `MovePicker` Stack Frame & Hoisted AVX-512 `pick_best_scored`)
----------------------------------------------------------------------------------------------------
- Diffstat / size: `+85 / -38` (`282` total lines; `include/forge/search.hpp`, `src/search.cpp`).
- Functions & types touched:
  * `forge::Worker` (`picker_scratch_`, `evasion_scratch_`, `quiet_hist_epoch_` members in `search.hpp`).
  * `FORGE_SDK_BADCAP_PREFIX` (`0 -> 1` in `search.cpp`, reusing already-yielded `moves_[0..bad_count_-1]` prefix slots for losing captures instead of `bad_captures_[256]`).
  * `forge::MovePicker`: removes `MoveList buffer_` and `std::array<Bitboard, 64> legal_to_by_from_` (`sizeof(MovePicker)` shrinks by `~2.5 KB/ply`), updates `MovePicker::next` (`QuietMoves` & `Evasions`), `MovePicker::pick_best_scored` / `MovePicker::pick_best` (hoisting `odd_idx16` outside the 16-lane/8-lane `vpermt2d` selection scan), `MovePicker::generate_captures`, `MovePicker::generate_quiets`, and `MovePicker::generate_evasions` (`[[gnu::noinline]]`, tagging illegal tie-break pseudo-legal slots as `Move::none()` in place).
- Invariant relied on:
  1. `Worker` searches one `MovePicker` stage generation (`generate_captures`, `generate_quiets`, or `generate_evasions`) to completion on its own thread before recursing into any child node, so per-`Worker` `picker_scratch_` and `evasion_scratch_` are never aliased across active plies.
  2. In `GoodCaptures`, each candidate is popped from `moves_[index_++]` before `bad_count_` is incremented, so `bad_count_ <= index_` always holds and storing losing captures into `moves_[0..bad_count_-1]` never overwrites an unpopped good-capture candidate.
  3. In `generate_evasions` tie-fallback, replacing illegal pseudo-legal entries with `Move::none()` while keeping their exact scores preserves `pick_best_scored()`'s 4 selection swaps and `std::sort` (`introsort`) tie-break order identically to filtering via `legal_to_by_from_` after `pick_best()`.
- Oracles / identity checks that catch a fault in it:
  * `forge-combo29/carbon2/job8/test_w1_movepicker_oracle.cpp` (`2,010` all-stages `MovePicker` sequences, `job5/s4_planted_fault.patch.txt` caught in Job 5 `s4_oracle_and_fault_raw.txt`).
  * `forge-combo29/carbon2/job3/test_e1_evasion_oracle.cpp` (`55,868` in-check evasion `MovePicker` sequences).
  * `PC20 + net512/net768` `bench 11/13/16` and `250`-position depth-9 suite (`stack_identity_raw.txt`).
- Relation to earlier job patch files:
  * Same logic as `forge-combo29/carbon2/job5/s4_slim_movepicker_and_vpermt2d_hoist.patch.txt` (and `S4` inside `forge-combo29/carbon2/job5/bundle.patch.txt`, built on the PC as `r15e`), **not verbatim text-equal** because in Job 5 `S1` and `S2` preceded `S4` (`S1` introduced the un-hoisted AVX-512 `pick_best` loop and `S2` renamed `pick_best()` -> `pick_best_scored()` + `quiet_gen_epoch_` fields). Since `S1` and `S2` are dropped from `curated_sp_bundle`, `01_S4.patch.txt` introduces `pick_best_scored()` and the hoisted AVX-512 `odd_idx16` block directly on `r15d`.

----------------------------------------------------------------------------------------------------
Piece 02: `02_S5.patch.txt` (`S5`: `Board::make_move` Early `precomputed_key` Reuse & Lazy `king_lines_` `Undo`)
----------------------------------------------------------------------------------------------------
- Diffstat / size: `+39 / -25` (`171` total lines; `include/forge/board.hpp`, `src/board.cpp`, `src/search.cpp`).
- Functions & types touched:
  * `forge::Board::make_move` (`board.hpp`, `board.cpp`: optional `const std::uint64_t* precomputed_key = nullptr`; skips incremental Zobrist XORs when `precomputed_key != nullptr` and copies `undo.king_lines` only when `king_lines_.valid`).
  * `forge::Board::unmake_move`, `forge::Board::make_null_move`, `forge::Board::unmake_null_move` (`board.cpp`: copies `king_lines_` only when `valid == true`, otherwise marks `valid = false`).
  * `forge::Worker::qsearch` and `forge::Worker::search` (`search.cpp`: passes `early_key ? &child_key : nullptr` from `board.key_after(move, child_key)` into `board.make_move`).
- Invariant relied on:
  1. Whenever `Board::key_after(move, child_key)` returns `true` (`early_key == true`), `child_key` equals the exact post-move Zobrist key `key_` (including legal en-passant target file rules and castling-rights masks); when `key_after` returns `false` (king/castling/EP/double-push edge cases), `early_key` is `false` and `precomputed_key == nullptr` runs the full incremental Zobrist path.
  2. When `king_lines_.valid == false`, no reader consults `king_lines_.pinned`, `discoverers`, or `check_squares` before calling `refresh_king_lines()`, so eliding the `72`-byte struct copy on invalid `KingLines` is unobservable.
- Oracles / identity checks that catch a fault in it:
  * `forge-combo29/carbon2/job5/test_s5_make_move_oracle.cpp` (differential `make_move`/`unmake_move` Zobrist & board-state oracle; caught `job5/s5_planted_fault.patch.txt` in `job5/s5_oracle_and_fault_raw.txt`).
  * Piece `03_S5_assert.patch.txt` (`-UNDEBUG` `assert(key_ == dbg_key)` check in `job11/curated_oracles_and_fault_raw.txt`).
  * `PC20 + net512/net768` `bench 11/13/16` and `250`-position depth-9 suite (`stack_identity_raw.txt`).
- Relation to earlier job patch files:
  * **Every `+` and `-` line (`39` added, `25` removed) is 100% identical** (`plus_minus_eq = True`) to `forge-combo29/carbon2/job5/s5_make_move_early_key_and_slim_undo.patch.txt` (and `S5` inside `job5/bundle.patch.txt` / `r15e`); only 2 trailing context lines in `src/search.cpp` differ because dropped `S3`'s `prefetch_correction(board, ss + 1);` line is absent.

----------------------------------------------------------------------------------------------------
Piece 03: `03_S5_assert.patch.txt` (`S5_assert`: Debug-Only Incremental Zobrist Verification of `precomputed_key`)
----------------------------------------------------------------------------------------------------
- Diffstat / size: `+35 / -0` (`95` total lines; `src/board.cpp`).
- Functions & types touched:
  * `forge::Board::make_move` (`src/board.cpp`: `#include <cassert>` and `#ifndef NDEBUG` shadow computation `dbg_key` across EP clear, capture, piece move, promotion, castling rook move, castling rights, side, and new legal EP square, asserting `assert(key_ == dbg_key)` whenever `precomputed_key != nullptr`).
- Invariant relied on:
  * Under `-DNDEBUG` (all release/production builds), every added line compiles out to zero instructions; under `-UNDEBUG` (debug/sanitizer builds), `dbg_key` computes the exact incremental Zobrist transition that the `precomputed_key == nullptr` path computes, aborting immediately if `*precomputed_key` ever diverges by 1 bit.
- Oracles / identity checks that catch a fault in it:
  * `-UNDEBUG` corrupted-key test (`k ^= 1ULL` aborts at `Assertion 'key_ == dbg_key' failed` in `forge-combo29/carbon2/job11/curated_oracles_and_fault_raw.txt` and `job7/bundle3_debug_and_fault_raw.txt`).
- Relation to earlier job patch files:
  * **Every `+` line (`35` added, `0` removed) is verbatim equal** to hunks 1–7 of the `src/board.cpp` section of `forge-combo29/carbon2/job7/o0_drop_s7p3_and_s5_assert.patch.txt` (hunk 8 of `o0`'s `board.cpp` section, `assert(compute_checkers() == 0)`, sits inside `if (known_gives_check == 0)` and therefore appears in `07_G3.patch.txt`).

----------------------------------------------------------------------------------------------------
Piece 04: `04_S7.patch.txt` (`S7`: Zero-Allocation `std::string_view` UCI `position`/`go` Parser & `Worker::clear` `memset`)
----------------------------------------------------------------------------------------------------
- Diffstat / size: `+171 / -85` (`459` total lines; `src/search.cpp`, `src/uci.cpp`).
- Functions & types touched:
  * `src/uci.cpp`: `PositionCache` (`fen_parts`, `canonical_moves` prefix cache), `is_uci_ws`, `next_uci_token`, `apply_position_sv` (replaces `std::istringstream` + `std::vector<std::string>` move replay with zero-allocation `std::string_view` prefix matching and tail replay), `is_go_keyword(std::string_view)`, `parse_limits_sv` (32-token stack buffer with heap fallback), `uci_loop` (`SearchTask` reuse without clobbering `pending_task`, `string_view` command dispatch for `ucinewgame`, `setoption`, `position`, `go`, `perft`, `bench`).
  * `src/search.cpp`: `forge::Worker::clear()` (explicit `std::memset` / `fill` on history and correction tables instead of `*table = Table{}`), and `forge::Searcher::search` (`std::move(board)` when `helpers.empty()`).
- Invariant relied on:
  1. `is_uci_ws` matches the exact 6 ASCII whitespace characters (`' '`, `'\t'`, `'\n'`, `'\r'`, `'\v'`, `'\f'`) skipped by `std::istringstream::operator>>` in the `"C"` locale, so `next_uci_token` tokenizes arbitrary UCI lines identically (including non-canonical multi-space or tab-delimited `position` lines via the token-by-token fallback loop).
  2. When `canonical_moves` matches the prefix of `moves_sv` on the same root FEN/startpos, replaying only `tail_sv` onto the cached `board` reaches the exact same `Board` state and `key_history_` as replaying from the root; any invalid FEN or prefix mismatch rebuilds cleanly from scratch, and an illegal move mid-list preserves all prior legal moves and prints the identical `info string illegal move <tok>` line.
  3. Every history/correction table cleared via `std::memset(..., 0, sizeof(*t))` is a flat `std::array` of primitive `int16_t` / `int32_t` / POD `LesserThreats` integers whose value-initialized state `T{}` is all-bits-zero, and `Worker::clear()` runs unconditionally on every `ucinewgame` (**`S7` part 3's `v1_eval_dirty_` / `threat_history_dirty_` flags are completely excluded**).
- Oracles / identity checks that catch a fault in it:
  * `forge-combo29/carbon2/job5/test_s7_uci_oracle.py` (fuzz/edge-case `position` & `go` parser differential oracle; caught `job5/s7_planted_fault.patch.txt` in `job5/s7_oracle_and_fault_raw.txt`; also verified on the PC across `53,208` commands and `1,000` protocol stress cycles at Threads 1 & 4 per `FABLE_TO_carbon2_10.md`).
  * `PC20 + net512/net768` `bench 11/13/16` and `250`-position depth-9 suite (`stack_identity_raw.txt`).
- Relation to earlier job patch files:
  * The entire `src/uci.cpp` diff (`15` hunks, `407` lines) and the `Searcher::search` hunk are **100% verbatim text-equal** (ignoring file timestamps) to `forge-combo29/carbon2/job5/s7_uci_zero_alloc_and_selective_clear.patch.txt` and `forge-combo29/carbon2/job5/bundle.patch.txt` (already built and checked on the PC as `r15e`), while `Worker::clear()` keeps only `S7` part 2 (`std::memset`) and omits `S7` part 3 (`threat_history_dirty_` / `v1_eval_dirty_`), matching `r15e` and `job7/o0_drop_s7p3_and_s5_assert.patch.txt`.

----------------------------------------------------------------------------------------------------
Piece 05: `05_G1.patch.txt` (`G1`: Cached `SearchStack::corr_mat_idx` & Inline `has_dead_material_candidates`)
----------------------------------------------------------------------------------------------------
- Diffstat / size: `+28 / -5` (`100` total lines; `include/forge/eval.hpp`, `include/forge/search.hpp`, `src/search.cpp`).
- Functions & types touched:
  * `forge::has_dead_material_candidates(const Board&)` (`eval.hpp`: inline bitboard OR `(Pawn | Rook | Queen) == 0` guard before calling out-of-line `dead_material_score`).
  * `forge::SearchStack::corr_mat_idx` (`search.hpp`: cached 16-bit `material_key(board) & (CorrectionSize - 1U)` index, validity bit `8U` in `corr_valid`).
  * `forge::Worker::static_evaluate`, `Worker::record_move`, `Worker::record_null_move`, `Worker::corrected_eval`, and `Worker::update_correction` (`search.cpp`).
- Invariant relied on:
  1. `dead_material_score(board, score)` returns `true` only for recognized bare-minor endgames (`KK`, `KBK`, `KNK`, `KNNK`, `KBNK`), none of which can contain a Pawn, Rook, or Queen; therefore `(Pawn | Rook | Queen) != 0` implies `dead_material_score` is guaranteed `false`.
  2. `material_key(board)` depends exclusively on per-piece-type popcounts (`popcount(board.pieces(c, pt))`); a move changes piece counts if and only if `captured != Empty || move.is_promotion()` (null moves and quiet non-promotions leave all 12 piece counts unchanged), so propagating `corr_mat_idx` when `captured == Empty && !move.is_promotion()` and invalidating bit `8U` otherwise always matches `material_key(board) & (CorrectionSize - 1U)`.
- Oracles / identity checks that catch a fault in it:
  * `1,000`-position static eval suite + `250`-position depth-9 suite + `PC20 + net512/net768` `bench 11/13/16` (caught `job6/g1_planted_fault.patch.txt` — failing to invalidate `8U` on promotion — in `job6/g1_planted_fault_raw.txt`).
- Relation to earlier job patch files:
  * Same code as `forge-combo29/carbon2/job6/g1_cached_material_corr_and_inline_dead_mat.patch.txt` (`eval.hpp` and `search.hpp` hunks are verbatim equal; `search.cpp` omits only the two hunks inside dropped `S7` part 3's selective `stack_` reset loop and dropped `S3`'s `prefetch_correction`).

----------------------------------------------------------------------------------------------------
Piece 06: `06_G2.patch.txt` (`G2`: `Board::see_ge` Fast No-Recapture Exit & Unified Contact/Slider Attacker Init)
----------------------------------------------------------------------------------------------------
- Diffstat / size: `+33 / -3` (`56` total lines; `src/board.cpp`).
- Functions & types touched:
  * `forge::Board::see_ge(const Move& move, int threshold) const` (`src/board.cpp`).
- Invariant relied on:
  1. After the initial capture puts `swap = attacker_value - swap > 0` in the opponent's (`them`) favor to recapture on `to`, if `them` has zero contact attackers (`them_contact == 0`) AND zero sliders even on empty-board rays through `to` (`them_ray_sliders == 0`), `them` cannot possibly attack `to` on `occupancy`, so the exchange terminates immediately and `see_ge` is `true`.
  2. Otherwise, computing `b_atk = attacks::bishop(to, occupancy) & diagonals` and `r_atk = attacks::rook(to, occupancy) & lines` once yields both the exact slider recapture check `((them_contact | ((b_atk | r_atk) & them_live)) == 0) -> return true` and, combined with `us_contact`, the exact full initial `attackers` bitboard `attackers_to_fast(*this, to, occupancy)` without scanning `b_atk` or `r_atk` twice.
- Oracles / identity checks that catch a fault in it:
  * `forge-combo29/carbon2/job5/test_s6_see_oracle.cpp` (exhaustive `see_ge` threshold sweep oracle across all pseudo-legal moves of `positions_1000.txt`; caught `job6/g2_planted_fault.patch.txt` in `job6/g2_oracle_and_fault_raw.txt`).
  * `forge-combo29/carbon2/job8/test_w1_movepicker_oracle.cpp` (`GoodCaptures` / `BadCaptures` SEE split across `2,010` sequences) and `bench 11/13/16` + `250` depth-9 rows (`stack_identity_raw.txt`).
- Relation to earlier job patch files:
  * Matches `forge-combo29/carbon2/job6/g2_see_fast_no_recapture_and_hoist_unify.patch.txt` on the active `#if FORGE_SDK_SEE_HOIST` path except that `S6`'s pawn-recapture sniper block inside `#if FORGE_SDK_SEE_HOIST` is omitted (kept only in the inactive `#else` branch of `curated_sp_bundle.patch.txt`).

----------------------------------------------------------------------------------------------------
Piece 07: `07_G3.patch.txt` (`G3`: `known_gives_check` in `make_move`, `KingLines` Reuse, & Off-Ray Pawn `has_legal_move`)
----------------------------------------------------------------------------------------------------
- Diffstat / size: `+47 / -19` (`165` total lines; `include/forge/board.hpp`, `src/board.cpp`, `src/search.cpp`).
- Functions & types touched:
  * `forge::Board`: `make_move(..., int known_gives_check = -1)`, `cached_king_lines()`, and `ensure_king_lines()` (`board.hpp`).
  * `forge::Board::generate_legal_evasions` (`taboo` filter skipping enemy pawn attacks & enemy king neighborhood before `square_attacked_with_occupancy`), `Board::has_legal_move` (immediate `true` when any friendly pawn strictly off the king's rook+bishop rays has a pseudo-legal push or capture, plus ray-empty skip before `single_blockers`), and `Board::make_move` (`if (known_gives_check == 0) { checkers_ = 0; assert(compute_checkers() == 0); }`) (`board.cpp`).
  * `forge::MovePicker::init_check_squares` (`board_.ensure_king_lines().check_squares`), `Worker::qsearch`, and `Worker::search` (forwarding already-computed `gives_check` as `0`/`1` into `board.make_move`) (`search.cpp`).
- Invariant relied on:
  1. When `checkers_ == 0`, a non-king, non-en-passant move can be illegal only if the moving piece lies on `king_lines_.pinned`, which is a subset of `rook_ray(ksq) | bishop_ray(ksq)`; hence any pawn push or normal pawn capture from a square outside `k_rays` is unconditionally legal (`has_legal_move() == true`).
  2. A king evasion to a square attacked by an enemy pawn (the pawn cannot be captured on its attack square unless the pawn itself is on a different square, wait: `pawn_attacks_bb(them, pieces(them, Pawn))` is the set of squares attacked by `them`'s pawns, and capturing one pawn does not remove another pawn's attack on a different square — wait: even if the king captures a pawn, a pawn on `X` does NOT attack `X` itself! So if `to` is in `pawn_attacks_bb(them, pieces(them, Pawn))`, the attacking enemy pawn sits diagonally behind `to`, NOT on `to`, so moving the king to `to` NEVER captures that attacking pawn!) or adjacent to the enemy king is never legal.
  3. `Board::gives_check(move)` before `make_move` is exact for all legal moves (direct, discovered, promotion, castling, and en passant), so `known_gives_check == 0` guarantees `compute_checkers() == 0` after `make_move` (verified by `assert(compute_checkers() == 0)` in `-UNDEBUG`).
- Oracles / identity checks that catch a fault in it:
  * `forge-combo29/carbon2/job6/test_g3_board_oracle.cpp` (`1,005` positions, `21,765` moves checking `has_legal_move`, `gives_check`, and post-`make_move` `checkers()`; caught `job6/g3_planted_fault.patch.txt` in `job6/g3_oracle_and_fault_raw.txt` and `job12/loo6_oracles_and_fault_raw.txt`).
  * `forge-combo29/carbon2/job3/test_e1_evasion_oracle.cpp` (`55,868` in-check evasion sequences across `313,716` visited nodes).
  * `PC20 + net512/net768` `bench 11/13/16` and `250`-position depth-9 suite (`stack_identity_raw.txt`).
- Relation to earlier job patch files:
  * Same code as `forge-combo29/carbon2/job6/g3_known_gives_check_kinglines_and_stalemate.patch.txt`, plus `cached_king_lines()` (`1` line in `board.hpp`, originally in `S2`) and `assert(compute_checkers() == 0);` (`1` line in `board.cpp`, from `job7/o0_drop_s7p3_and_s5_assert.patch.txt`), and omitting the 2 `prefetch_correction` context lines from dropped `S3`.

----------------------------------------------------------------------------------------------------
Piece 08: `08_G4.patch.txt` (`G4`: Per-Search `v3_active_net_` Snapshot, Hoisted `nnue::v3::prepare`, & Direct `king_square`)
----------------------------------------------------------------------------------------------------
- Diffstat / size: `+64 / -42` (`217` total lines; `include/forge/board.hpp`, `include/forge/nnue_v3.hpp`, `include/forge/search.hpp`, `src/nnue_v3.cpp`, `src/search.cpp`).
- Functions & types touched:
  * `forge::Board::piece_bitboards()` (`board.hpp`), inline `forge::nnue::v3::king_key` (`nnue_v3.hpp`, `nnue_v3.cpp`), `forge::nnue::v3::prepare` (`nnue_v3.cpp`: `resize` + metadata reset without zero-filling `int16_t` accumulator/cache payload arrays before bias copy).
  * `forge::Worker` (`nnue_active_`, `v3_active_net_` in `search.hpp`; snapshotted once at search entry in `Worker::search` alongside hoisted `nnue::v3::prepare`, replacing per-node `nnue::enabled && nnue::available() && nnue::v3::active()` checks in `static_evaluate`, `record_move`, `record_null_move`, `Worker::search`, and `static_evaluate_v3`; `static_evaluate_v3` reads `board.king_square(White/Black)` directly instead of scanning `dirty.changes` and skips `king_key` when `king0 == parent.king_sq[0] && king1 == parent.king_sq[1]`).
- Invariant relied on:
  1. UCI options (`UseNNUE`, `NNUEArch`, `NNUEArchFile`) cannot change while a search is running (`uci.cpp` calls `stop_search()` before mutating options or nets), so `nnue_active_` and `v3_active_net_` are invariant for the entire duration of `Worker::search`, and calling `nnue::v3::prepare` at search entry guarantees `v3_state_ != nullptr` at every ply.
  2. `board.king_square(White)` and `board.king_square(Black)` at `ss` always equal the post-move king squares resulting from replaying `frame->dirty` onto `parent.king_sq[0/1]`; when `king_sq` is unchanged, `king_key(net, c, king_sq)` is pure and equals `parent.keys[c]`.
  3. In `nnue::v3::prepare`, `valid_flags` are all set to `0` and every `RefreshCache::Entry::values` is immediately overwritten by `std::copy_n(net.b1.data(), net.hidden, ...)`, so skipping redundant zero-initialization of `Accumulator::values` and `Entry::values` before overwrite never exposes uninitialized values.
- Oracles / identity checks that catch a fault in it:
  * `1,000`-position static eval suite on both `net768` and `net512` (`job2/eval_1000_net768_rows.txt`, `eval_1000_net512_rows.txt`; caught `job6/g4_planted_fault.patch.txt` in `job6/g4_planted_fault_raw.txt`).
  * `PC20 + net512/net768` `bench 11/13/16` and `250`-position depth-9 suite (`stack_identity_raw.txt`).
- Relation to earlier job patch files:
  * Same logic as `forge-combo29/carbon2/job6/g4_snapshot_v3_net_hoist_prepare_and_king_sq.patch.txt`, adapted to `r15d`'s `static_evaluate_v3` without dropped `S1`'s `refresh_one_and_evaluate` branch and without dropped `S7` part 3's `v1_eval_dirty_` lines (plus `Board::piece_bitboards()` in `board.hpp`).

----------------------------------------------------------------------------------------------------
Piece 09: `09_W1.patch.txt` (`W1`: Fused `MovePicker` Generation, Single-Pass `QuietMoves` Pin-Legality/`gives_check`, & Lazy `LesserThreats`)
----------------------------------------------------------------------------------------------------
- Diffstat / size: `+375 / -38` (`579` total lines; `include/forge/b4.hpp`, `include/forge/search.hpp`, `src/search.cpp`).
- Functions & types touched:
  * `forge::b4::lesser_threats` (`b4.hpp`: skips building `by_minor` when `us` has neither Rook nor Queen, and skips building `by_rook` when `us` has no Queen).
  * `forge::Worker` (`threat_map_ready_`, `quiet_base_to_`, `ensure_threat_map`, `threat_set_for_piece` in `search.hpp`; lazy invalidation `threat_map_ready_[ply] = 0U` in `Worker::clear`, `Worker::qsearch`, `Worker::search`, and on-demand lookup in `Worker::quiet_history` / `Worker::rework_entry` in `search.cpp`).
  * `forge::MovePicker`: direct-to-`moves_[]` `generate_captures` and `generate_quiets` (eliminating intermediate `MoveList` round-trip under `FORGE_SPD_NO_ZERO_MOVELISTS >= 2 && FORGE_SEARCH_SPEED2`), caching `pinned_`, `discoverers_`, `own_king_sq_`, `enemy_king_sq_` in `init_check_squares()`, and checking pin-ray legality + direct/discovered `gives_check` inside `MovePicker::next` (`QuietMoves`) so `Worker::search` skips redundant `board.is_legal(move)` and `board.gives_check(move)` calls on `QuietMoves`.
- Invariant relied on:
  1. `LesserThreats::by_type[Rook]` (`by_minor`) is only ever indexed when scoring/updating a friendly `Rook` move, and `by_type[Queen]` (`by_rook`) is only ever indexed for a friendly `Queen` move; for `Pawn`, `Knight`, and `Bishop` (`pt <= Bishop`), `by_type[pt]` is always `pawn_attacks_bb(them, board.pieces(them, Pawn))`, so computing `by_pawn` inline before `QuietsInit` and skipping `by_minor`/`by_rook` when `us` lacks `Rook`/`Queen` yields bit-identical threat bits on every read.
  2. Fused `generate_captures` and `generate_quiets` traverse pieces and bitboards in the exact same square/piece/promotion/castling order as `fill_pseudo_legal<Captures>` and `fill_pseudo_legal<Quiets>`, producing identical `(Move, score)` arrays before `pick_best_scored()`.
  3. Every move in `QuietMoves` has `checkers_ == 0` and `(move.flags & EnPassant) == 0` (en passant is a capture); therefore a non-king quiet move is legal iff `((pinned_ >> move.from) & 1) == 0 || attacks::aligned(own_king_sq_, move.from, move.to)`, and gives check iff it lands on `check_squares_[pt]` or (for non-castling) starts on `discoverers_` and leaves the line to `enemy_king_sq_` (castling delegates to `board_.gives_check(move)`).
- Oracles / identity checks that catch a fault in it:
  * `forge-combo29/carbon2/job8/test_w1_movepicker_oracle.cpp` (`2,010` all-stages `MovePicker` sequences verifying every `(move, score, known_legal, cached_gives_check)` tuple; caught `job8/w1_planted_fault.patch.txt` at sequence 446 in `job8/w1_oracles_and_fault_raw.txt`).
  * `forge-combo29/carbon2/job3/test_e1_evasion_oracle.cpp` (`55,868` in-check evasion sequences).
  * `PC20 + net512/net768` `bench 11/13/16` and `250`-position depth-9 suite (`stack_identity_raw.txt`).
- Relation to earlier job patch files:
  * Same code as `forge-combo29/carbon2/job8/w1_fused_simd_movepicker_and_lazy_threats.patch.txt` (`b4.hpp` and `search.hpp` hunks are verbatim equal; `search.cpp` differs only on 2 context lines where dropped `S2`'s `cached_quiet_history` was absent).

----------------------------------------------------------------------------------------------------
Piece 10: `10_W2.patch.txt` (`W2`: Direct 1D Continuation Row Pointers & `[[gnu::noinline]]` Stage Generators)
----------------------------------------------------------------------------------------------------
- Diffstat / size: `+41 / -53` (`219` total lines; `include/forge/search.hpp`, `src/search.cpp`).
- Functions & types touched:
  * `forge::Worker`: removes `quiet_base_to_[64]` (`search.hpp`).
  * `forge::MovePicker::generate_captures` and `forge::MovePicker::generate_quiets` (`search.cpp`: marks both `[[gnu::noinline]]` to keep `MovePicker::next` compact, and replaces `W1`'s 64-square `build_base_to(pt)` pre-sum loop with `PieceContRows` 1D row pointers `c1`, `c2` [defaulting to `kZeroContRow`], `c4`, and `chk` loaded only on actual quiet target squares `to`).
- Invariant relied on:
  * For every piece `p = make_piece(us, pt)` and target square `to`, `static_cast<int>(c1[to]) + static_cast<int>(c2[to]) + (c4 ? static_cast<int>(c4[to]) / 2 : 0) + (((chk >> to) & 1ULL) ? 12000 : 0)` (with `kZeroContRow[to] == 0` when `cont1`/`cont2` is `nullptr`, and signed C++ `/ 2` truncation toward zero matching `_mm512_srai_epi32(v4 + (v4 >>> 31), 1)`) equals `base_to[to]` bit-for-bit on every quiet move.
- Oracles / identity checks that catch a fault in it:
  * `forge-combo29/carbon2/job8/test_w1_movepicker_oracle.cpp` (`2,010` all-stages `MovePicker` sequences; caught `job8/w2_planted_fault.patch.txt` / `job11/curated_planted_fault.patch.txt` — dropping `c2[to]` — at sequence 0 in `job11/curated_oracles_and_fault_raw.txt`).
  * `PC20 + net512/net768` `bench 11/13/16`, `250`-position depth-9 suite (`stack_identity_raw.txt`), `1,000` evals, and 48-run `Hash 16` self-play trace `ee465caeff9c0fcf`.
- Relation to earlier job patch files:
  * **100% hunk-for-hunk and line-for-line identical** (`norm_hunks_eq = True`, `plus_minus_eq = True`, `219` lines, `+41 / -53`) to `forge-combo29/carbon2/job8/w2_direct_row_scorer_and_noinline_movegen.patch.txt` (only file timestamps and `@@` line offsets differ).
