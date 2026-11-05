# T05C board cost per node: what the lock pays in board / movegen / legality / SEE code

Counted from the lock source (FD3A5190 = src_al1s198_clean, read-only) and from a static disassembly of the lock exe
(forge_ltopgo_x_al1s198_v23.exe, sha256 fd3a51903e73dc1f..., listing F:/odr/work/T05C/lock_v23.dis). **Nothing here
is measured**: call counts per node are not known (no counters in the lock), cycle figures are static estimates.
Scale: the lock's game-position probe runs ~2.24 Mnps (T05 SPEED_LIST, 30-h counters), i.e. ~2,200 cycles per node at
~5 GHz (clock assumed), so 100 cycles per node = ~4.5 % of a node. "Lookup" below = one magic slider lookup
(load the 32-B Magic {mask, magic, table*, shift}, and, imul, shr, load the table entry; the exe has 0 pext / pdep).

| # | operation (lock file:line) | when it runs | work per call (static) | node-identical fix | card |
|---|---|---|---|---|---|
| 1 | is_draw -> has_legal_move (search.cpp:692-702, called at :780 qsearch and :893 search, BEFORE the TT probe; board.cpp:558-575) | every non-root node that is not in check (after the repetition and material tests) | witness path: one is_legal of the lowest quiet non-promotion pawn push (3 table tests + 2 lookups); fallback (no such push, or that pawn is pinned off its line): CRT memset of 1,032 B (codegen: `mov $0x408,%r8d; call memset` in has_legal_move) + the FULL pseudo-legal list (one lookup per slider, ~20-40 pushes) + is_legal until the first legal move | pin-aware existence test without a list (unpinned knight / pawn / slider with any target, then king steps, ep last); same boolean by construction | T05C-01 |
| 2 | MovePicker construction (search.cpp:323-341, arrays :447-459) + quiets_tried / captures_tried (:1034-1035) | every node that reaches its move loop (qsearch after stand-pat, main search after pruning) | codegen: TWO out-of-line CRT memset calls per picker (0x800 = 2,048 B moves_, 0x400 = 1,024 B MoveList data; memset is an import thunk `jmp *__imp_memset`) + 4 (qsearch) / 19 (search) inline 64-B zmm zero stores; ~3.3 KiB (qsearch) / ~4.3 KiB (search) zeroed per node | default-initialise the arrays (no `{}`), a trivially constructible move type in buffers; every slot is written before it is read | T05C-02 |
| 3 | generate_quiets (search.cpp:523-536) | main nodes that reach the quiet stage | init_check_squares (2 lookups) + generate_pseudo_legal(false): the captures and promotions are generated AGAIN and then skipped by the filter | quiets-only mode that emits the identical quiet subsequence (same loop order; piece targets & empty; no capture / promotion / ep loops) | T05C-02 |
| 4 | generate_evasions (search.cpp:538-555) | in-check nodes | the FULL pseudo-legal list; every entry later goes through is_legal (:829, :1051), most fail | is_legal fast path with a check mask (row 5); an evasion-only GENERATOR is NOT node-identical (pick_best swap order + unstable std::sort see a different input) | T05C-01 (fast path), dead end (generator) |
| 5 | is_legal per picked move (board.cpp:577-598; search.cpp:829, :1007, :1051) | every move the picker returns | occupancy edit + king-attack test: 3 table tests + 1 bishop + 1 rook lookup | not in check: non-king, non-ep, non-castle move of an unpinned piece = legal without the test (pinned piece: legal iff aligned(from, to, king)); single check adds to in between(king, checker) or = checker; double check = king moves only; king / ep / castle keep the lock test | T05C-01 |
| 6 | gives_check per legal move (board.cpp:671-701; search.cpp:1056 every move, :832 qsearch non-check) | ~every searched move | occupancy edit + direct test (0-2 lookups by piece type) + discovered test (up to 2 lookups) | check squares per piece type + our blockers of the enemy king, once per node; ep / castle / promotion keep the lock path | T05C-01 |
| 7 | make_move checkers (board.cpp:786) | every make_move | attackers_to(enemy king): 4 table tests + 2 lookups, even when the move gives no check | skip when the caller passes gives_check = false (main loop has it for every move; qsearch only in non-check nodes, so a tri-state hint) | T05C-01 |
| 8 | make_move ep key (board.cpp:733-735, 783-785) | ep square set (start) / double push (end) | has_legal_en_passant_capture(): per adjacent pawn a king-attack test (2 lookups) | remember "ep file is in the key" in the board / Undo instead of re-testing at the start | none (< 1 %: ep squares are rare) |
| 9 | see_ge (board.cpp:932-1023; search.cpp:360, :838, :1008, :1071, :1083, :1113) | every good-capture pick, qsearch captures, SEE pruning of quiets and captures, check extension | early exits; otherwise attackers_to (2 lookups) + per exchange step a fresh pin scan (3 table tests + 2 empty-board lookups + between() per aligned enemy slider) | none found: the per-step pin scan uses the CURRENT occupancy (pins can appear / vanish during the exchange), so a per-node pin cache changes results; hoisting only the empty-board lookups saves well under 1 % | dead end |
| 10 | static_exchange (board.cpp:1025-1034, a binary search of ~12 see_ge) | NO caller in search.cpp (grep: only board.hpp / board.cpp) | - | - | dead end (not hot) |
| 11 | is_pseudo_legal (board.cpp:600-669; search.cpp:326, :370-379) | TT move per picker, killers / counter (<= 3) when the stage is reached | branchy; one lookup for a slider | fine as is | none |
| 12 | material_key (search.cpp:588-596) in corrected_eval (:641-642, from :809 / :937) and update_correction (:655, from :1222); MaterialCorrectionWeight = 100 by default (search.cpp:50) | every node that computes a static eval, and each correction update | 10 popcounts + a 10-deep dependent multiply chain + 1 multiply (~35-45 cycles latency) | keep the value in Board, recompute with the SAME formula only after a capture or promotion, restore from Undo | T05B-02 (existing card; T05C-04 was a duplicate, MERGED into TABLE row 18) |
| 13 | key_history_ push / pop (board.cpp:788, 793, 838, 842) | every make / unmake | std::vector push_back (capacity check; reserve 512 at board.cpp:176) | fixed array + index | none (< 1 %) |
| 14 | Move list layout: Move = 4 x uint8 (board.hpp:34-47), MoveList = 256 x Move + size_t (1,032 B), Scored = {Move, int} (8 B), Undo 40 B (board.hpp:75-85), Board mailbox squares_ = 64 x int Piece = 256 B (board.hpp:170) | - | - | uint8 Piece mailbox (64 B) touches 1 line instead of 4; not counted as a card (< 1 % expected) | none |

## Attack generation on Zen 5 (asked by the brief)
- The lock uses "fancy" magics: per square a 32-B struct, index ((occ & mask) * magic) >> shift, tables 0x19000 rook +
  0x1480 bishop entries = 800 KiB + 41 KiB (bitboard.cpp:23-24), magics searched at start-up from a fixed seed. The
  exe built with -march=znver5 contains 0 pext and 0 pdep (objdump count), 487 imul in total.
- PEXT is a single fast instruction on Zen 3 and later (it was microcoded and slow on Zen 1 / Zen 2), so on this PC the
  BMI2 index costs one pext instead of and + imul + shr; the table stays 841 KiB unless the attack sets are stored as
  16-bit PEXT-compressed values and re-expanded with PDEP (~210 KiB). The working set of one search thread (841 KiB
  attack tables + 786 KiB lock float w1 + ~1.55 MiB histories) is larger than Zen 5's 1 MiB L2, so the compressed form
  is the variant worth timing (T05C-03).

## Per-card static budget (counted, not measured; every figure UNPROVEN until step 0 of the microbenchmark plan)
| card | rows above | what goes away per node | what is added per node | static estimate |
|---|---|---|---|---|
| T05C-01 check info | 1, 4 (fast path), 5, 6, 7 | per picked move: the king-attack test (2 lookups) and most of gives_check (up to 4 lookups); per make_move without check: attackers_to (2 lookups); per non-check node: the has_legal_move fallback (memset 1,032 B + full list) when the pawn-push witness fails | one lazy build per node of pinned / blockers (2 x-ray lookups + a loop over aligned sliders) and check squares (2 lookups + table reads) | +1 to +3 % nps, more in endgames without a free pawn push |
| T05C-02 no zero fill | 2, 3 | 2 CRT memset calls (3 KiB) + 4-19 zmm stores per picker; the captures / promotions generated twice in the quiet stage | one mode flag in the generator | +1 to +3 % nps (quiets-only part +0 to +1 %) |
| T05C-03 PEXT slider index | every lookup in rows 1-9 and the HCE's 10 call sites | and + imul + shr per lookup; with 16-bit entries 841 KiB -> 210 KiB of slider tables in the L2-contended set | one pext (+ one pdep for value 2 / 3) per lookup | 0 to +1 % (value 1), +0.5 to +3 % (value 2 / 3) |
The cards touch disjoint code (T05C-01 board.cpp tests, T05C-02 search.cpp picker arrays + generator mode, T05C-03
bitboard tables), so they can be timed one by one and then together in one speed exe; T05C-01 and T05C-03 overlap in
benefit (fewer lookups vs cheaper lookups), so the combined gain is less than the sum. Order: T05C-02 first (smallest
change, simplest proof), T05C-03 value 2 second (exhaustive table test), T05C-01 last (largest proof surface).
Every candidate considered, with its verdict: notes/T05C/TABLE.md.

## Proof recipe (shared by T05C-01 .. -03; follows T12-03, T12-02)
1. Build: kit pc1 = pc2 exe sha256; the switch OFF build must equal the lock exe's behaviour (pins below).
2. Pins: bench d11 / d13 / d16 / d20 / d22 = 312866 / 862329 / 3024920 / 12389307 / 34048354; perft startpos 5 =
   4,865,609; kiwipete 5 = 193,690,690; plus a perft suite (the chess-library README FENs: positions 3-6 incl. the
   promotion / ep / castling-rights cases) at depth 5-6 vs published counts.
3. Per-position identity: the 12k gate FENs (r12_fens12k) at `go nodes 20000`: bestmove, score, nodes equal.
4. Differential verify build (compile switch, not shipped): old and new function side by side on every call during
   bench + the 12k FENs + 1M random legal plies; assert equal booleans / bitboards / values (T12-03 level 8).
5. Sanitizers: the existing ASan + UBSan self-play CI row on the switch-ON build (catches reads of uninitialised
   move slots for T05C-02).

## Microbenchmark plan
- Step 0 (counting build, node-identical): counters per node for has_legal_move witness / fallback, is_legal calls
  (by stage: captures / quiets / evasions), gives_check calls, make_move with an ep square, see_ge calls that enter the
  loop, picker constructions per node; on bench d16 and the 200-position game probe. This sizes every row above.
- perft nps (exercises generate_pseudo_legal, is_legal, make / unmake, the checkers recompute, the MoveList memset per
  node; NEVER has_legal_move, gives_check, see_ge or the MovePicker): startpos d6, kiwipete d5, position 3 d7, one
  pawnless ending d7; 9 runs each, palindromic A B B A, one logical CPU with its SMT sibling idle, fresh exe copy per
  run, an A/A arm (T12-02).
- Search nps (covers the rest): bench d16 + the standard 200-position `go movetime 200` probe (T05 SPEED_LIST), same
  ABBA rules; plus an endgame-only subset of the probe (pawnless / blocked) for the has_legal_move fallback.
- Gate: node-identical speed changes = nps ABBA only (no SPRT); keep a change at a point estimate >= +1 % with the
  A/A interval containing 0 (T12-02).
