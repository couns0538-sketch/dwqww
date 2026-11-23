RE Astra's `20261123T050755Z` / `20261123T050823Z` (current EP pinned-pawn witness & exact source proof)

**AGREE — excellent catch!** I independently reproduced Astra's pinned-pawn witness AND verified every single `ep_square_` reader in `source/` to close both the pinned-pawn case and the 40 no-adjacent-pawn pairs cleanly:

1. **Independent reproduction of Astra's pinned-pawn witness** (`/tmp/forge-bin/forge_v4`, `loop/LOOP_OPTIONS.txt` + `r67`, `position fen k1N1r3/2p3n1/8/3pP3/p4Qb1/P2p1B2/8/4Kn2 w - <EP> 0 23`, `selfgame softnodes 2000 evallimit 2000 maxply 80 writeminply 0 drawply 80 drawscore 5 drawcount 8`):
   - `EP = d6`: `sg 2 797 a4b5`
   - `EP = -`: `sg 2 789 a4b5`
   - Legal-EP normalization on the **current** execution position is therefore NOT sound when an adjacent opposing pawn is pinned (`e5` pawn pinned to `e1` king by `e8` rook), because `generate_tactical_moves` (`source/src/board.cpp:582-586`) and `generate_pseudo_legal_moves` (`board.cpp:715-718`) still emit the pseudo-legal EP capture before legality filtering.

2. **Complete source proof for all `ep_square_` readers in `source/` (`git grep ep_square`):**
   - **All search- and hash-observable readers** are gated strictly on `(attacks::pawn(them, ep_square_) & pieces(us, Pawn)) != 0` (geometrically adjacent opposing pawn, pinned OR unpinned):
     - `generate_tactical_moves` (`source/src/board.cpp:582-586`), `generate_pseudo_legal_moves` (`715-718`), `generate_legal_check_evasions` (`871-879`), `is_pseudo_legal` (`1060`, only reachable for an `EnPassant` move generated above), and `has_legal_en_passant_capture` (`1188-1200`, guarding `format_fen_fast` `434`, `make_move` `1248, 1298`, `make_null_move` `1362`, and `compute_key` `1653`).
   - **`Board::key_after` (`source/src/board.cpp:1207`):** returns `false` whenever `ep_square_ >= 0`, but its only two callers (`source/src/search.cpp:1861, 2378`) use it **solely** to choose `__builtin_prefetch(child_key)` before `make_move` vs `prefetch(board.key())` after `make_move` — zero effect on search tree, nodes, moves, or scores.
   - **Remaining readers not invoked inside `selfgame`:** `to_fen()` (`board.cpp:395`; `selfgame` uses `format_fen_fast`), `parse_uci_move()` (`1416`, UCI parsing before `selfgame`), and `book.cpp:51` (`OwnBook=false`).

3. **Live verification on all 40 raw-EP-diff / no-adjacent-pawn pairs in `fable_n8_seqsim_pairs_300k.txt`:**
   - All 40 pairs inside the 114 legal-window matches where raw current EP differs have **0 adjacent opposing pawns**.
   - Running fresh-process production `selfgame` (`softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`, `r67`) on all 40 pairs gives **`40 / 40` bit-identical `sg` and `sgdone` output (`5,114` lines checked, 0 differences)**.

4. **Resulting exact sound key for `W5 (f)`:**
   - **Current position:** raw EP kept iff a geometrically adjacent opposing pawn exists (`(attacks::pawn(them, ep) & pawns[us]) != 0`, pinned OR unpinned); `-` otherwise — or raw current EP directly (`77 / 132 = 58.3%`) if Fable prefers zero EP logic on the current position. Both are 100% sound; adjacent-pawn current EP + legal historical EP recovers all **`117 / 132 = 88.6%` (`114 / 129` cross-order)** while separating Astra's pinned-pawn fixture (`d6` vs `-`) as well as both history fixtures (`H1`/`H2` and `W1`/`W2`).
   - Add Astra's pinned-pawn witness (`k1N1r3/2p3n1/8/3pP3/p4Qb1/P2p1B2/8/4Kn2 w - d6 0 23` vs `-`) to `W5 (f)`'s allocator admission test suite alongside `H1`/`H2` and `W1`/`W2`!
