# T05C sources (one line per source read: url or repo@sha | licence tier | what it gave | card id or "no card")

Sub-track T05C: node-identical speed of board, move generation, make/unmake, legality and SEE (own code).
Worker start 23:57 PC clock (2026-11-04); research stop at 01:17 (80 min) at the latest.

## Local (own code and records, read-only; not counted as web sources)

## Web sources
- L1. Lock source include/forge/bitboard.hpp (194 lines) + src/bitboard.cpp (174 lines), read in full: sliders use
  "fancy" magics (struct Magic {mask, magic, table*, shift} = 32 B per square, index = ((occ & mask) * magic) >> shift,
  bitboard.hpp:143-171), magics searched at start-up from a fixed PRNG + per-rank seeds (bitboard.cpp:63-108), shared
  tables 0x19000 rook + 0x1480 bishop entries (= 800 KiB + 41 KiB), no PEXT/BMI2 path anywhere; Between/Line 64x64
  tables (32 KiB each); pop_lsb / countr_zero helpers | own | T05C-01 (PEXT), BOARD_COST
- L2. Lock source include/forge/board.hpp (205 lines), read in full: Move = 4 x uint8 (from, to, promotion, flags),
  MoveList = std::array<Move,256> + size_t (1,032 B), Undo = 40 B struct (captured, castling, ep, halfmove, fullmove,
  key, pawn_key, checkers, plies_from_null), Board = mailbox squares_[64] (Piece is int: 256 B) + 13 piece bitboards +
  2 colour bitboards + king squares + key/pawn_key + checkers_ + std::vector key_history_; no pinned / check-square
  caches; make_move returns bool (legality checked inside) | own | BOARD_COST, T05C-02
- L3. Lock source src/board.cpp (1,058 lines), read in full: is_legal (577-598) tests EVERY pseudo-legal move with a
  full king-attack test on the post-move occupancy (pawn/knight/king tables + one bishop + one rook magic lookup), no
  pinned-piece fast path; gives_check (671-701) recomputes direct + discovered checks with up to 4 magic lookups per
  call, no cached check squares / king blockers; make_move (719-790) copies a 40-B Undo, recomputes checkers with a
  full attackers_to (2 magic lookups) at every move (786) and re-runs has_legal_en_passant_capture() to remove the old
  ep key (733); see_ge (932-1023) is a threshold swap loop that recomputes pins from scratch at every exchange step
  (972-993); static_exchange (1025-1034) is a binary search over see_ge (~12 calls); is_pseudo_legal (600-669);
  perft (872-890) = pseudo-legal gen + is_legal per move; Zobrist table constexpr (115-141), pawn key incremental
  | own | T05C-02, T05C-03, BOARD_COST
- L4. Lock source src/search.cpp, the board calls (grep + read of 319-556, 599-630, 692-702, 775-864, 1035-1170):
  MovePicker (319-556) holds moves_ std::array<Scored,256>{} (2 KiB), bad_captures_ std::array<Move,64>{} and a
  MoveList buffer_ (1,032 B; Move has default member initialisers, so the array is constructed element by element)
  -> about 3.3 KiB zeroed per picker construction (main search AND qsearch); generate_quiets / generate_evasions
  (523-555) call generate_pseudo_legal(captures_only = false) = the FULL list again and then skip captures and
  promotions; init_check_squares (462-472) builds check squares for quiet ordering only; pick_best (488-503) =
  selection-swap for the first 4 picks then std::sort (so removing illegal entries changes tie order: not
  node-identical); the main loop calls is_legal (1051) then gives_check (1056) for every move, see_ge in pruning
  (1071, 1083, 1113); qsearch calls is_draw at every node BEFORE the TT probe (780), and is_draw (692-702) runs
  has_legal_move() (stalemate test) at every non-check node; make_move then a TT prefetch (846-847, 1125-1126)
  | own | T05C-01, T05C-02, T05C-03, BOARD_COST
- W1. https://github.com/Disservin/chess-library/blob/430266434aeb42f19bb5baa84597d671824889ff/README.md + comparison/comparison.md
  | MIT (copy with notice) | perft on a Ryzen 9 5950X: kiwipete d5 193,690,690 nodes 430 ms = 449.4 Mnps WITH move-list
  preallocation vs 538 ms = 359.4 Mnps without (comparison.md) = +25 % from not constructing a move list per node;
  start position d7 355.5 Mnps; surge 230.0 Mnps, THC 38.4 Mnps on the same kiwipete d5 | evidence for T05C-02
  (move-list construction cost), BOARD_COST
- W2. https://github.com/Disservin/chess-library/blob/430266434aeb42f19bb5baa84597d671824889ff/src/attacks_fwd.hpp
  (lines 1-40, 150-170) + src/attacks.hpp (110-157) + src/movelist.hpp + src/move.hpp | MIT (copy with notice) |
  slider index by _pext_u64(occ, mask) behind the build macro CHESS_USE_PEXT (struct Magic {mask, attacks*} = 16 B)
  else the fancy-magic multiply-shift (mask, magic, attacks*, shift = 32 B); the SAME table sizes 0x19000 / 0x1480 as
  Forge; tables filled by walking the mask subsets with the chosen index function; Movelist = std::array<Move,256> +
  int size with Move() = default and 2 x 16-bit members (move, score), so a new list is not zero-filled | T05C-01,
  T05C-02
- W3. https://github.com/Disservin/chess-library/blob/430266434aeb42f19bb5baa84597d671824889ff/src/movegen.hpp (grep +
  lines 55-200, 286-302 skimmed) | MIT (copy with notice) | fully legal generation: checkMask (55) = checker + the
  squares between it and the king, pinMask (104) split into straight / diagonal pin rays, seenSquares (123) = enemy
  attacks with our king removed, for king moves; pawns / pieces are masked by both before emitting; ep checked
  separately (286) | T05C-03 (pin / check masks for the boolean tests), dead end (legal generation in the picker)
- W4. tools/mine_commits.py Witek902/Caissa --grep speed/pext/movegen/legal + --show 7ed119c 0dc61c8 5a6f623
  | MIT (copy with notice) | 7ed119c "Fix pext/pdep and MulHi64 falling back to software on non-Windows builds", no
  functional change: +3.01 +- 1.84, 5+0.05 Threads=1 Hash=8MB, SPRT [0,2] LLR 2.95, N=37,274 (hardware pext/pdep vs a
  software fallback, nps not logged); 0dc61c8 "Use threats info to generate less illegal king moves" +1.31 +- 1.92,
  8+0.08, [-1,2], N=59,368; 5a6f623 movegen / threat codegen tuning (no functional change) -0.03 +- 1.27, 5+0.05,
  [-3,0], N=81,872 | T05C-01 (evidence that slider-lookup speed shows up in Elo), TABLE (dead end for codegen-only)
- W5. https://github.com/Witek902/Caissa/blob/57cae7ef71/src/backend/Bitboard.cpp (lines 10-44, 186-200, 290-330)
  | MIT (copy with notice) | under USE_BMI2 the slider index is ParallelBitsExtract(blockers, mask) into a plain
  102,400 + 5,248-entry table (AttackData {mask, uint32 offset}); without BMI2 a magic path with hand-optimised index
  widths (some squares one bit narrower, "5 bits -> 4 bits optimized") and smaller tables of 84,480 + 4,800 entries
  (MagicData {mask, magic, uint32 shift, uint32 offset}) | T05C-01
- L5. Static disassembly (objdump -d, no run) of the lock exe C:/Users/Administrator/grok-pc/forge_push/locks/
  lock_AL1_s198_ltopgo_x_20261030/forge_ltopgo_x_al1s198_v23.exe (sha256 fd3a51903e73dc1f...), listing kept at
  F:/odr/work/T05C/lock_v23.dis: Worker::search (recursive, 0x1400edd40) calls the CRT memset (an import thunk,
  jmp *__imp_memset) with 0x800 = 2,048 B (MovePicker moves_) and 0x400 = 1,024 B (MoveList data) per picker, plus 19
  inline 64-B zmm zero stores in the function (bad_captures_, quiets_tried, captures_tried); Worker::qsearch
  (0x1400fa980) the same two memset calls (0x800, 0x400) plus 4 zmm zero stores; Board::has_legal_move (0x14000aa00)
  calls memset 0x408 = 1,032 B on its fallback path (the pawn-push witness failed); Board::perft (0x140101786)
  rep stos 0x102 dwords = 1,032 B per node; Board::see_ge has one rep stos (the inlined promotion exchange's 256-B
  gain array, rare path). The exe has NO pext / pdep instruction for sliders (slider index = imul + shr) | own |
  T05C-02, T05C-01, BOARD_COST
- Note on fetch size: cl_movegen.hpp (888 lines) and ca_Bitboard.cpp (740 lines) were downloaded whole by mistake
  (over the ~300-line cap); only the grep hits and the line windows named in W3 / W5 were read.
- W6. tools/mine_commits.py Adam-Kulju/Patricia --since 2023-01-01 (grep speed / legal / pin / movegen / pext / SEE,
  and the top 40 by Elo) | MIT | no board / movegen speed commit with a logged number | no card
- W7. Stockfish commit messages (GPL-3.0: commit text only, no source): e17725f445 "Constexpr attacks (pext only)"
  (2026-04-26, PR 6706): compile-time tables shared through the binary, "Using pdep reduces table size 4x", STC SPRT
  [0,2] LLR 2.97, 38,400 games W 10057 L 9749 D 18594, no functional change; ee72cf49fe "Optimize RankAttacks"
  (2026-07-26, PR 6998): RankAttacks 4x smaller and compile-time, STC [0,2] LLR 3.01, 212,800 games W 55208 L 54665;
  99489f57dd "Simplify out pext attacks" (2026-07-03, PR 6939): after PR 6845 "pext attacks are slower or equal to
  parallel-hyperbola attacks", non-regression <-1.75,0.25> passed on avx512icl (81,632 games) and bmi2 (78,112) |
  GPL ideas only | T05C-03 (re-framed: small / shared / table-free slider attacks)
- W8. https://github.com/official-stockfish/Stockfish/pull/6845 "HQ attacks for AVX2" (PR text only, GPL-3.0): hyperbola
  quintessence for file and bishop attacks in parallel plus a much smaller rank lookup table instead of magics; STC
  SPRT [0,2] LLR 2.93, 29,792 games W 7759 L 7465 D 14568; local speed test 100 runs: master 1,136,025 nps vs patch
  1,171,370 nps, diff +35,346 +- 3,275, speedup +3.11 %, P(speedup > 0) = 1.0; the PR text credits the smaller table |
  GPL ideas only | T05C-03
- W9. https://github.com/official-stockfish/Stockfish/pull/6706 "Constexpr attacks (pext only)" (PR text only, GPL):
  same SPRT as W7 (LLR 2.97, 38,400 games); pdep "reduces table size by 4x"; compile-time generation lengthens the
  build; for non-pext tables the generation "takes forrrever, and bloats the binary"; no nps number given | GPL ideas
  only | T05C-03
- W10. gh search commits official-stockfish/Stockfish "initialization moves" / "uninitialized" (commit titles only,
  GPL) | GPL ideas only | no commit about zero-filling move lists; nothing usable | no card
- W11. https://uops.info/html-instr/PEXT_R64_R64_R64.html | measurement table (facts) | PEXT r64: Zen 5 latency 3 / 3,
  throughput 0.33 c (1 uop); Zen 3 and Zen 4 latency 3, TP 1.00 (ALU1); Zen 2 latency 18 (mask operand), TP 19.00,
  7 uops (microcoded); Zen+ TP 18.00; Alder Lake-P latency 3, TP 1.00. PDEP not fetched | T05C-03
