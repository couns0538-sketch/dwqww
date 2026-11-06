# Review of FORGE_SPD_KING_LINES (b4_king_lines_after_w8.patch, md5 21ecde2e) - SELF-REVIEW, NOT independent

Written by the main session on 2026-11-05 after 18:39 (PC clock). The independent reviewer (worker patchrev) ran out of
model credits before it started. This review reads the patch and the `trial_w9` tree; it ran no builds and no engines.
**Verdict: no BLOCKER, no SHOULD, three LOW notes.**

## What was checked
1. **Switch 0 = lock text.** Every new block sits under `#if FORGE_SPD_KING_LINES`, and the lock's `is_legal` /
   `gives_check` bodies are verbatim under `#else`. The patch removes 0 lines. The w9sw0 lp_v1 build is
   sha256 FD3A5190, byte for byte.
2. **`is_legal` fast path.** It applies when not in check, not en passant and not a king move. The move is then legal
   iff the mover is not pinned or `aligned(own king, from, to)`.
   - A capture of the pinner is aligned.
   - A capture never opens a line, because its target stays occupied.
   - Pins come from enemy rook-like / bishop-like snipers on empty-board rays from the own king, with exactly one
     blocker (either colour) on `between`, masked to own pieces.
   - Castling is a king move, so it keeps the full test, as do en passant and any position in check.
3. **`gives_check` fast path.** It applies to every move except en passant, castling and promotions.
   - Direct check uses the destination in the pre-move check squares of the mover's type. Exact: a slider whose origin
     lay between the king and its destination already saw the king, which a legal position excludes. Pawn and knight
     checks do not depend on occupancy.
   - Discovered check: the mover is a sole blocker of an own slider's line to the enemy king, and it leaves that line
     (`!aligned`). The own king is included in `occupied(us)`, so a king move that discovers check is covered.
   - King check squares are 0.
4. **Cache validity.**
   - make_move and make_null_move save the cache into `Undo` / `NullUndo` and invalidate it.
   - unmake_move and unmake_null_move restore it.
   - `set_fen` invalidates it; this was the bug the worker's harness found.
   - The only other writers of `squares_` / sides are `put_piece` / `remove_piece`, called only from `set_fen` (lines
     337, 341) and make / unmake (1019-1083). No other mutator exists in board.cpp.
5. **Caller contract.** The fast `is_legal` path assumes a pseudo-legal move. Every caller passes one:
   - generated lists: `legal_moves`, perft, the `has_legal_move` loop;
   - the `has_legal_move` witness: a quiet push of an own pawn to an empty non-promotion square;
   - search: MovePicker output. The TT move is checked with `is_pseudo_legal` (search.cpp:422), killers and the counter
     move through `is_valid_quiet` -> `is_pseudo_legal` (:627-629).
6. **Composition with the W8 switches.** make_stack applied the patch on trial_w8 with no fuzz. The MovePicker's own
   `check_squares_` (NZM / SPEED2) is a separate member. Both packs (alone, on (d)) are BIT-EXACT L1-L4 (quick L3).
   The worker's differential harness found 0 mismatches over 30.5M moves, alone and with bundle (d)'s defines.

## LOW notes
- **K1, stack budget.** `Undo` and `NullUndo` each grow by `sizeof(KingLines)` (about 80 B) per ply. This is the same
  kind of note as W2 for T12B. Covered by the deep-ply stress FEN suggested for T12B bundles; run it on this switch too.
- **K2, threads.** The cache is a `mutable` member filled inside const methods. That is safe only while no Board
  object is shared between threads; each search worker owns its copy. No Threads 2-4 soak has run with this switch
  (lock-path step 3 is owed).
- **K3, contract.** The `is_legal` fast path is exact only for pseudo-legal input, and every current caller satisfies
  that (point 5). A future caller passing an unvalidated move would get a different answer than the lock.
  `board.hpp` should say so next to `is_legal` if the switch is kept.
