# SPEC_SPEED: implementation specs for the node-identical speed rows S1-S4 (T05C-02, T05C-03, T05B-02, T05D-01)

Started 05:06 PC clock (`date`), planned stop 05:41. Status: COMPLETE (all four specs and the shared part written by
05:18 `date`; own review only, not independent; the 10 FIX items of notes/SPEC_SPEED_REVIEW.md (SPECREV2, no blocker) were applied
by SPECFIX2, each marked "(review fix) [id]", log in notes/FIXES_APPLIED.md Round 7). Layout as notes/SPEC_SEARCH2.md where it fits. Lock FD3A5190 = AL1 s198 source, read-only:
`C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean`. Nothing here edits, builds or runs
the engine; every Forge-side number is UNPROVEN. No card was edited.

## Reading record
- Lock (read-only, 05:07-05:15): search.cpp :180-230 (lease, has_exclusive_access, lock_stripe), :245-312 (TT probe /
  store / hashfull), :436-556 (MovePicker arrays, pick_best, generators), :586-597 (material_key), :636-657
  (corrected_eval, update_correction), :1004-1007, :1274-1340 and :1463-1466 (root lists), :1498-1531
  (Searcher::search); board.cpp :425-576 (generate_pseudo_legal, legal_moves, has_legal_move), :872-875 (perft);
  board.hpp :28-73 (Move, MoveList); bitboard.hpp :143-171; bitboard.cpp :20-26, :63-112; search.hpp :114-180 (TT
  class), :257 (CorrectionSize); book.hpp :38. Greps: lock_stripe / has_exclusive_access lines, every default-initialised
  `Move` / `MoveList` declaration, every reader of RookMagics / BishopMagics.
- Notes: SPEC_SEARCH2.md, RANKING_FINAL.md rows S1-S4 (and S9, line 146), the four cards (+ the T05C-04 pointer),
  T12-02, T12-03, notes/T05C/BOARD_COST.md rows 1-14, notes/T05C/VERIFY.md rows for T05C-02 / -03, skill
  forge-speed-stack steps 5-6.
- No web read. Mechanisms are own (lock source, the cards' own disassembly) or come through the cards from MIT sources
  (chess-library @430266434a, Caissa @57cae7ef71: nothing opened or copied here) and from Stockfish PR text / commit
  messages (GPL-3.0, ideas only, never source).
- Own arithmetic check (no engine): `F:/odr/work/SPEC4/matkey_check.py` (S3).

## Common parts (all four)
- Build switches, not UCI options: hot paths, and an option would leave a live branch in the PGO profile. Each switch
  is a preprocessor integer, default 0, set only through the kit's compiler flags. At 0 the preprocessor yields the
  lock text, so the switch-0 kit exe must equal FD3A5190 byte for byte (sha256), as SPEED2 de20653c did; kit pc1 = pc2
  is binding for every exe. Byte identity at 0 is a stronger OFF proof than the pins. It holds only if every
  restructure (shared bodies, mode enums, new helpers, and new data members / arrays, which change the class layout or
  the symbol table when they exist at 0 (review fix) [C5]) lives inside the `#if` and the lock text stands verbatim under
  `#else`, duplicated if needed; if a helper must exist at 0, drop the byte-identity claim for that switch and say
  the OFF proof is pins + 12k only (review fix).
- ON identity (the forge-speed-stack method plus T12-03; Threads=1, depth / node limits only, never time):
  1. ON kit exe pc1 = pc2 sha256.
  2. Pins: bench d11 / d13 / d16 / d20 / d22 = 312866 / 862329 / 3024920 / 12389307 / 34048354; perft startpos 5 =
     4,865,609; kiwipete 5 = 193,690,690.
  3. 12k-FEN exe identity: skill step 5, `r12_fens12k.py --cpu 2 --fens opus-r10-halfka:opus_r10/parity/fens_12k.txt
     --depth 2 --exe L=<lock exe> --exe X=<ON exe>` (with the gate's net setting) = 12000/12000; plus T12-03 level 4
     at `go nodes 20000` (bestmove, score, nodes per FEN). r12_fens12k.py has no node limit (flags --out --cpu --net
     --fens --depth --exe --deep-n --deep-depth --wait-timeout; it sends `go depth`): add `--nodes N` to a copy of the
     tool or write a small driver, a fixed one-time cost (crew ~0.5 h, order step 0) (review fix) [C1].
  4. T12-03 level 3 (every info line of the 8 bench FENs at d11-d22, fresh `ucinewgame`) and level 5 (warm-TT replay
     of 50 gate games at `go nodes 50000`, no `ucinewgame`): they catch what one bench total can hide.
  5. Planted mutant per switch (one deliberate wrong bit in the new code) must fail step 2, 3 or the unit test: shows
     the proof can fail.
  6. CI: the ASan + UBSan self-play row with the switch ON.
- Microbench (per spec below): a small timing driver linked to the engine core, one logical CPU whose SMT sibling is
  idle (CPUs 2-3 = one core, forge-opus-tools), Idle class, boost state fixed and recorded, 30 repetitions, median and
  IQR. It is a no-go filter before the ABBA, never the keep decision.
- nps ABBA (T12-02 + skill step 6): arms A = lock exe, B = ON exe, A' = a copy of A (the A/A arm); a fresh byte copy
  of the exe for every slot (R12: an exe vs its own copy read -3.0 % at d16, a fixed per-file bias); each fresh
  copy runs once untimed (bench d1) before its first timed slot, or the ABBA folder is excluded from real-time scanning
  (Windows scans the first run of every new file and the image starts cold; mechanism UNPROVEN, the warm-up is free;
  the slot order stays palindromic) (review fix) [C4]; palindromic
  blocks with A' interleaved; decision workload bench d16; d20 and the 200-position game probe only as a confirmation
  of a candidate that already passed at d16 (review fix) [C2]. Pilot first: 20 pairs of A vs A' only (two fresh copies
  of the lock exe, no B) to measure s (per-pair sd of the log ratio, %) and the per-file bias; B enters the blocks only
  after that pilot's interval contains 0; then n = 8.6 s^2 pairs from the pilot s at d16 (s 2 % -> 35, 3 % -> 78,
  4 % -> ~140, 5 % -> 215; T12-02's own A/A over 15 runs implies s of about 4 %) (review fix) [C2]. Tool:
  `r12_speed.py --cpu 2 --ignore-idle --pairs N --aa-pairs M --depths 16 20 --exe A0=.. --exe A1=..`; its missing
  copy-per-run flag (T12-02) = copy by hand or add `--fresh-copy-per-run` (crew ~2 h, once, T12-02). Not on a gate's
  cores; read the skill's own-process pitfall first. Accept "B faster" only if the A/A interval contains 0 and the B/A
  one-sided 95 % lower bound is > 0; keep only at a point estimate >= +1 % (WORKER_RULES drop rule). The sized n gives
  90 % power to the lower-bound test ("faster than the lock") at a true +1 %; the point estimate >= +1 % is a stricter
  extra filter that a true +1 % change passes only about half the time at that n, and a true 0.75 % change (S3) only a
  minority of the time (about 1 in 4 to 1 in 6, own normal-approximation arithmetic); the crew decision on sub-1 %
  members of a stack (S3) stays open (review fix) [C3].
- Route: node-identical = nps ABBA only, no SPRT (crew rule). Any identity difference = not a speed change: stop and
  find the cause, never gate it as an Elo change.
- Common no-go: switch-0 kit exe not byte-identical to FD3A5190; any difference in steps 2-4; ABBA point < +1 % or an
  A/A interval that excludes 0 (one re-run on a quieter core, then drop).

## S1 T05C-02 FORGE_NO_ZERO_MOVELISTS (no zero fill of move arrays; quiets-only generation)
Source (card): own lock codegen (two CRT memset calls per picker, 0x800 and 0x400 B, plus 19 / 4 zmm zero stores;
has_legal_move fallback memset 0x408; perft `rep stos`); chess-library (MIT) perft 449 vs 359 Mnps only as context,
not a controlled A/B; no search-nps number for this change exists (missing). RANKING_FINAL S1: +1 to +3 % [2 %], 3 h.
- Lock lines: board.hpp:34-47 Move (members `= 0` at :35-38), :46 none() = Move{}, :49-73 MoveList (data_ :71 has no
  `{}`: it is zeroed only through Move's member initialisers, which is the 0x400 fill of buffer_). search.cpp MovePicker
  :438-441 Scored {Move, int}; :447 killers_{} and :448 counter_{} (keep both: is_valid_quiet reads is_none); :450
  moves_{} (256 x 8 B, the 0x800 fill); :453 bad_captures_{} (64 x 4 B); :456 buffer_; :459 check_squares_{} (index 0
  is never read: direct_check :474-477 indexes piece types 1-6, and both callers :532 / evasions run
  init_check_squares :462-472 first); generators :510-521 captures, :523-536 quiets (full list, filter :530), :538-555
  evasions. search.cpp:1034-1035 quiets_tried{} / captures_tried{}, written at :1186-1187 before the reads :1198 /
  :1200 (counts passed). board.cpp:425-540 generate_pseudo_legal, :569 has_legal_move fallback list, :874 perft list.
- Bare `Move x;` that would become indeterminate: search.cpp:827 (qsearch), :1005 (ProbCut), :1044 (main) are each
  assigned in their while condition before any read; :446 tt_move_ is set in the constructor :324; book.hpp:38
  Candidate::move (cold): give it `{}` under the switch. Root list search.cpp:1278: front() at :1330 / :1338 / :1465 runs
  only after the empty-list return at :1311; :1320 is guarded. Every other Move member already has `{}` (search.hpp
  :43-44, :69, :266-268, :325) and keeps its zero.
- Change (own steps):
  1. board.hpp under the switch: Move's four members lose `= 0`. Move stays an aggregate, so `Move{}` / none() and
     `Move{from, to, promo, flags}` keep their values; only bare `Move x;` loses the zero (audit list above).
  2. search.cpp :450, :453, :459, :1034, :1035: drop `{}` under the switch (keep :447, :448).
  3. Board::generate_pseudo_legal gets a quiets-only mode (own design, all of it inside the `#if`: a three-value mode;
     the bool entry stays as a wrapper so lock callers are unchanged; at 0 the lock function text stands; the mode enum and the wrapper are under the switch too (review fix) [C5]). Quiets mode: single pushes :453-458, double pushes :459-462, then for
     N, B, R, Q, K the targets mask = empty squares, then castling :517-539 with the same `checkers_ == 0` test; skip
     the promotion-push loop :464-468, the pawn-capture loop :469-479 and the en-passant block :480-485.
  4. MovePicker::generate_quiets :523-536 calls the quiets mode and drops the filter :530 (under the switch).
  5. Untouched: generate_evasions (an evasion-only generator changes the pick_best swap / std::sort input and is not
     node-identical, card), legal_moves, has_legal_move and perft logic (they lose only the fill, through step 1).
- Why step 3 is the identical subsequence (from the generator text): in the full list pushes come first and castles
  last, each piece's targets are popped in bit order with captures and quiets interleaved, and the filter :530 drops
  every capture, promotion and ep move. Removing them leaves the quiets in the same order, which is what popping
  (attacks & empty) in bit order yields.
- Proof (beyond Common): (a) poison verify build: every dropped array and each new MoveList filled with 0xA5 bytes at
  construction; pins, 12k and level 3 equal (no read depends on the fill); (b) assertion build: at every
  generate_quiets call also build the lock's filtered list and assert same size and element equality (bench d16 +
  12k FENs); (c) Linux CI valgrind memcheck on bench d8 + perft 4 (or a clang MSan build): no uninitialised read;
  (d) objdump of the ON exe: no 0x800 / 0x400 memset in Worker::search / qsearch, no 0x408 memset in has_legal_move,
  no `rep stos` in perft.
- Microbench: on 2,000 of the 12k FENs construct a MovePicker in main and in qsearch mode and drain it (`next()` to
  none) with zeroed histories; ns per picker, lock source vs ON source, same compiler flags; generate_quiets alone;
  side check perft startpos 6 / kiwipete 5 nps (perft is not a gate and over-weights the fill).
- Expected: (a) zero fill +1 to +3 %, (b) quiets-only +0 to +1 % search nps **UNPROVEN** (card: static 70-120 cycles
  of ~2,200 per node).
- Crew hours: 3 (RANKING_FINAL; card 1-2 code + 1-2 proofs).
- No-go: a read of an unwritten slot (poison / valgrind / MSan) that an explicit `{}` at a cold site cannot fix; an
  assertion mismatch in (b) (then ship step 1-2 only); objdump still shows the fills (the compiler re-zeroes: look at
  the codegen before timing); ABBA < +1 % for steps 1-4 together.

## S2 T05C-03 FORGE_SLIDER_ATTACKS (PEXT slider index + 16-bit PDEP entries on Zen 5)
Source (card): Stockfish PR 6845 +3.11 % nps over 100 runs (1,136,025 -> 1,171,370), STC [0,2] LLR 2.93, 29,792 games
(hyperbola variant, AVX2 build; PR text only); Stockfish e17725f445 compile-time PEXT tables with 4x smaller PDEP
entries, STC [0,2] 38,400 games (gain said to come mostly from tables shared between processes); Caissa 7ed119c (MIT)
hardware pext / pdep instead of a software fallback +3.01 +- 1.84, 5+0.05, [0,2], 37,274 games; Zen 5 PEXT latency 3,
throughput 0.33 c (uops.info; Zen 2: 18, microcoded). RANKING_FINAL S2: PEXT alone 0 to +1 %, with PDEP +0.5 to +3 %
[1.75 %], 3.5 h, ABBA after a microbench.
- Lock lines: bitboard.hpp:143-152 Magic {mask, magic, table*, shift} and index(); :154-155 RookMagics /
  BishopMagics; :162-165 bishop(), :166-169 rook(), :170-171 queen() = the only readers of the tables (grep: no user
  outside bitboard.*); bitboard.cpp:23-24 RookAttackTable 0x19000 / BishopAttackTable 0x1480 entries (each = the sum
  over squares of 2^popcount(mask), already dense); :32 sliding_attack (the reference); :63-108 init_magics (mask :76 =
  sliding_attack(sq, 0) minus edges, shift :77, table pointer :78, per-rank seeds :71, rng search :88-91, fill :99,
  offset :106); :112 init().
- Change (own steps; the card's sources are ideas only here, nothing copied):
  1. Mode 1 (PEXT index, lock layout): per square keep {mask, table*} (16 B instead of 32 B); index = pext(occ, mask).
     init fills table[pext(s, mask)] = sliding_attack(sq, s) for every subset s of mask (carry-rippler enumeration)
     and drops the rng magic search (start-up becomes shorter and seed-free). Same table sizes, different entry order,
     so the lock's table contents are not reused.
  2. Mode 2 (16-bit entries): add a second per-square mask ray = sliding_attack(sq, 0) including the edges (rook 14
     bits, bishop 7-13). Entry = uint16 pext(attacks, ray); lookup = pdep(entry, ray). Tables 102,400 x 2 B = 200 KiB
     rook and 5,248 x 2 B = 10.25 KiB bishop (lock: 800 KiB + 41 KiB of 8 B entries). Own layout: three 64-entry arrays
     per piece (mask, ray, uint32 offset), under the switch like mode 1's {mask, table*} array (at 0 the lock's Magic
     arrays and tables stand) (review fix) [C5].
  3. Mode 3 (only after mode 2 keeps): the mode-2 tables emitted at build time into read-only data (a generator that
     writes a header, preferred; constexpr only as a fallback: a 102,400-entry table built through a constexpr pext
     emulation can hit GCC's constexpr operation limit (review fix) [S2-3]), so concurrent gate processes of one exe share the pages.
  4. queen() stays bishop | rook. Modes 1-3 need BMI2: `#error` unless `__BMI2__` is defined; only the -march=znver5
     kit exe sets the switch (never a Zen 1 / 2 or generic side). The CI sanitizer row with the switch ON passes
     `-mbmi2` explicitly (a runner build without -march would stop at the `#error`); on Zen 1 / 2 PEXT / PDEP are
     microcoded (slow, still correct), so a wrong machine is a speed matter, never a wrong result (review fix) [S2-2].
- Proof (beyond Common): exhaustive CTest per mode: every square x every subset of its relevant mask (102,400 rook +
  5,248 bishop cases): new lookup == lock magic lookup == sliding_attack; plus 1M random occupancies with bits outside
  the mask (both index functions ignore them; tested anyway). Mutant: one flipped bit in one entry must fail it.
- Microbench: (i) throughput: 1M (square, occupancy) pairs taken from the 12k FENs (every slider square with that
  position's occupancy), independent lookups summed; (ii) latency: the next occupancy depends on the previous result
  (exposes the pext -> load -> pdep chain against and -> imul -> shr -> load); magic vs mode 1 vs mode 2, ns per
  lookup; (iii) perft kiwipete 5 and startpos 6 nps (movegen-heavy, node-identical). Mode 1 not faster in (i)-(ii)
  = skip its ABBA and go to mode 2; mode 2 not faster in (iii) = stop before the ABBA.
- ABBA: Common, single process. Mode 3 adds one ABBA with 8 copies of each exe running at once (gate-like load, only
  in a window without gates or training on those cores), per-process nps; still no SPRT.
- Expected: mode 1 0 to +1 %; mode 2 0 to +2 % single-process nps **UNPROVEN** (card: +0.5 to +3 %). Per lookup the
  mode-2 chain pext -> load -> pdep is not shorter in latency than the lock's and -> imul -> shr -> load (mode 1 saves
  about two cycles), so a single-process gain can come only from the smaller footprint (210 KiB vs 841 KiB; Zen 5 L1D
  48 KiB, L2 1 MB per core); the cited numbers that name a cause point at page sharing between processes (mode 3) or
  at a software fallback as the baseline. The perft microbench (iii) stays the gate in front of the
  ABBA (review fix) [S2-1].
- Crew hours: 3.5 (RANKING_FINAL; card 3-4) + 3-4 for mode 3; hyperbola quintessence (card, 6-10 h) not first.
- No-go: any exhaustive-test mismatch (a bug: fix before anything else); mode 2 not faster in the microbench; ABBA
  mode 2 < +1 %; a kit side without BMI2.

## S3 T05B-02 FORGE_MATKEY_FAST (exact material key without the serial multiply chain)
Source (card): own only. Lock exe disassembly: three inlined copies (search x2, qsearch x1), each 10 popcnt + 9
dependent imul by 0x100000001b3 + imul $0x3c15 before the material-correction load; own R7 J3 profile corrected_eval
2.76 % self time (a non-lock build). Outside number for this exact change: none (missing). T05C-04 is a merged duplicate
(its design = the card's variant b). RANKING_FINAL S3: +0 to +1.5 % [0.75 %], 1.5 h (a), 3-4 h (b).
- Lock lines: search.cpp:588-596 material_key (loop White then Black, Pawn..Queen: key = key * P + count + 1, P =
  1099511628211 at :592; result * G, G = 0x9E3779B97F4A7C15 at :595); corrected_eval :638-645 (read :642 inside
  `MaterialCorrectionWeight > 0` :641); update_correction :647-656 (write :655, same guard); callers :809 / :937 (eval)
  and :1222 (update), per BOARD_COST row 12; search.hpp:257 CorrectionSize = 1 << 14. Both uses mask the key with
  CorrectionSize - 1: only bits 0-13 ever matter.
- Own arithmetic (F:/odr/work/SPEC4/matkey_check.py, no engine): with c_j the 10 counts in the lock's order (j = 0 White
  pawn ... 9 Black queen), key = K0 + sum_j c_j * K_j (mod 2^64), K_j = G * P^(9-j), K0 = sum_j K_j, because unsigned
  arithmetic is a ring. 200,000 random count vectors (0-10 each): 0 mismatches against an own re-statement of the
  lock's Horner form, for the 64-bit key and for the 14-bit index. Mod 2^14: K0 = 0x1f14; K_0..K_9 = 0x238f 0x10b5
  0x1ff7 0x1ead 0x2e1f 0x33e5 0x3807 0x3e5d 0x17af 0x3c15 (K_9 = G mod 2^14 = the exe's imul $0x3c15). Largest
  unmasked 14-bit sum at counts <= 10: 1,070,556 < 2^32. These values are for the unit test only; the code derives them.
- Change (a), own steps, no Board change:
  1. constexpr table K14[10] and K0_14, computed at compile time from the two lock literals (no typed numbers);
     static_assert CorrectionSize == 1 << 14 and K14[9] == (G & 0x3fff).
  2. material_index(board): 10 independent popcounts, 10 independent 32-bit multiply-adds onto K0_14 summed as a tree,
     `& 0x3fff`. Same value as `material_key(board) & 0x3fff` for every position.
  3. :642 and :655 call material_index under the switch; the `MaterialCorrectionWeight > 0` guards stay.
- Change (b), only if a later card needs a Board key (T04-04 more correction keys; T05D-03 prefetch of the child's
  material entry right after make_move): Board keeps a uint16 index (any width >= 14 bits keeps bits 0-13 exact);
  set_fen fills it via (a); make_move subtracts K14 of the captured kind (en passant: their pawn), on a promotion
  subtracts our pawn and adds the new piece; unmake restores the saved value from Undo; null move leaves it. Board /
  Undo lines were not re-read here (BOARD_COST names board.cpp:733-842 and board.hpp:75-85): read them before coding.
- Proof (beyond Common): unit test closed form == lock Horner on 10^6 random vectors and on every node of bench d13
  (verify build calls both at every corrected_eval / update_correction); (b) adds a make / unmake check board index ==
  recomputed at every node of bench d16 and the 12k FENs (the card's lesson from Stockfish PR 6894: an incremental
  material key broke silently in a move-order refactor). Codegen: no imul by 0x100000001b3 at the three sites. Mutant:
  drop one K14 term = bench nodes change (MaterialCorrectionWeight 100 is live at the lock default, :50).
- Microbench: the 12k FEN boards, material index + load of material_correction[side][index]: (i) throughput sum,
  (ii) latency with the next board chosen from the loaded value; Horner vs (a), ns per call.
- ABBA: the card times S3 only inside a speed exe (alone it sits below the PC's per-file effect). Spec: B = a stack
  with S3, A = the same stack with FORGE_MATKEY_FAST=0, fresh copies, A/A arm, n sized for a 0.75 % effect
  (n = 8.6 s^2 / 0.75^2); report the marginal. The +1 % keep threshold then applies to the stack, not to S3 alone:
  whether a node-identical change under +1 % may ride in a stack is a crew decision (open).
- Expected: +0 to +1.5 % nps **UNPROVEN** (card: ~1 % if half of corrected_eval's 2.76 % is the chain).
- Crew hours: 1.5 for (a); 3-4 for (b) (RANKING_FINAL).
- No-go: any unit-test mismatch (a bug); the chain still in the exe; marginal B/A one-sided 95 % lower bound <= 0 at
  the sized n; for (b) any make / unmake check failure.

## S4 T05D-01 FORGE_TT_NOTLS (TT probe / store without the emulated-TLS lookup; port of the own R7TtExclusive)
Source (card): own R7 J3 option R7TtExclusive (engine 2d9889cf, a different tree, NOT in the lock): +3.59 % [+1.38,
+5.84] d16 and +3.97 % [+1.23, +6.77] d20 wall nps over 15 runs (A/A -0.02 % [-2.24, +2.25]), plain -O3 znver5 build of
opus-r5d-matefix 5882c383, PC 73 % busy - not the lock, not LTO+PGO; gate R7-TTX non-regression [-10, 0] H1 on that
tree (2,534 games). Lock exe: __emutls_get_address inside the inlined probe of Worker::search (two PGO copies) and
qsearch, and in the out-of-line store. RANKING_FINAL S4: +2 to +4 % [3 %], 7 h.
- Lock lines: search.hpp:135 StripeCount 1024, :139-151 ExclusiveLease, :153 `static thread_local` active_lease_, :154
  has_exclusive_access, :155 lock_stripe, :156-158 stripes_ / exclusive_gate_ / exclusive_requested_, :120-122 probe /
  store / hashfull. search.cpp:184 TLS definition; :186-203 lease constructor (drains every stripe), :205-209
  destructor; :211-216 has_exclusive_access (walks the thread's lease chain = the TLS read); :218-228 lock_stripe (:220:
  under the lease it returns a deferred, unlocked lock); probe :246-281 (lock :249); store :283-302 (handle check
  :287-288, lock :289); hashfull :304 (lock :308). Call sites: probe :786 (qsearch) / :910 (search); store :817, :868, :1023,
  :1214. Searcher::search :1498-1531: lease :1512-1515 only for TTAccess::Exclusive with workers_.size() == 1; helpers
  :1516-1521 exist only when size > 1; the main worker runs at :1522 on the calling thread (the lease owner). uci.cpp
  :357 (go) and :403 (bench) pass TTAccess::Exclusive, so gate games at Threads=1 and bench take the lease.
- Change (own steps; R7's tree has another layout, so re-written with the forge-lock-port recipe, not cherry-picked):
  1. Worker gets `bool tt_owned_ = false` (own name); this member and the Searcher scope guard below are under the
     switch, else the switch-0 exe differs (review fix) [S4-1 = C5 for S4]. In Searcher::search, right after the lease is emplaced
     (:1514), set it on workers_.front() and restore the previous value after :1522 returns (a scope guard that saves
     and restores, so an exception or a nested search, which the lease's previous_ chain allows, leaves it right).
     No helper can see it: helpers exist only when size > 1, and then no lease is taken.
  2. TranspositionTable (inside the `#if`; at 0 the lock text stands): probe and store bodies move into one private
     body each with a compile-time "take the stripe lock" parameter; public probe / store keep calling lock_stripe (all
     other callers unchanged); new probe_owned / store_owned run the same body without lock_stripe. The store handle
     check :287-288 stays first in the body.
  3. The six Worker call sites pick `tt_owned_ ? probe_owned : probe` (same for store): one predictable branch per
     access. hashfull, the lease code and every non-search caller keep lock_stripe.
  4. Verify build only: probe_owned / store_owned assert has_exclusive_access() at every call.
- Why node-identical: under the lease has_exclusive_access() is already true for this thread and table, so
  lock_stripe hands back an unlocked lock; skipping it removes only the TLS walk (the emulated lookup with its locked
  `xchg`). Entry choice, aging, replacement and the handle checks are the same text (shared body): the same entries
  are read and written in the same order.
- Proof (beyond Common): dynamic (the real proof, review fix): a counter build counts has_exclusive_access() calls over
  bench d16 and the 12k FENs: OFF at least one per TT access (millions), ON only the lease constructor / destructor and
  hashfull (a handful); its bench nodes must equal the plain build's. Static: objdump shows no emutls call on the hot
  path of Worker::search / qsearch; the locking probe / store stays reachable through step 3's branch, so a surviving
  call in a cold partition or the out-of-line probe / store is expected, not a failure. The verify build's assert holds
  over bench d16 and the 12k FENs; T12-03 level 5 (warm-TT replay) is the key level here; `go depth 12` searches / short games
  at Threads 2 / 4 run without a hang or crash (not node-deterministic) and the TSan CI row stays clean; not bench:
  bench builds its own one-thread Searcher (uci.cpp:395 `Searcher bench_searcher(16)`, search.hpp:375 default
  `threads = 1`), so it ignores Threads (review fix) [S4-2].
- Microbench: one 16 MB table under an ExclusiveLease, 10M probe + store pairs on keys from a fixed generator, plus a
  cache-resident variant (64 KiB of keys) that isolates the call cost from DRAM misses; ns per pair, probe/store vs
  probe_owned/store_owned.
- ABBA: Common; then QA timing together with SPEED2 (card).
- Expected: +2 to +4 % nps **UNPROVEN** (card; the R7 number above is from a non-lock plain -O3 build).
- Crew hours: 7 (RANKING_FINAL; card 6-8: switch, plain + kit pc1 = pc2, pins, 12k, objdump, CI row, ABBA).
- No-go: switch-0 exe not byte-identical; the ON counter build still counts has_exclusive_access() per TT access, or
  the emutls call still sits on the hot path (not just in a cold partition: check before timing); any identity
  difference; a TSan report or a hang in the Threads 2 / 4 `go depth 12` runs (review fix) [S4-2];
  ABBA < +1 %.

## Shared build, order
- Edit sites are disjoint: S1 board.hpp:35-38, board.cpp:425-540 (new mode), search.cpp :450-536 and :1034-1035,
  book.hpp:38; S2 bitboard.hpp:143-171 and bitboard.cpp:20-112 only; S3 search.cpp:586-597, :642, :655 (+ Board /
  Undo for b); S4 search.hpp TT class + Worker, search.cpp:184-312, the six TT call sites and :1512-1522. No two specs
  edit the same line.
- Overlap in effect: S1 step 3 removes repeated movegen work and S2 makes every slider lookup cheaper, so their gains
  are not additive (not quantified). S3 and S4 touch different parts of a node (eval correction vs TT access).
- One kit exe can carry all four ON: one OFF proof (all switches 0 = FD3A5190 byte for byte) and one ON identity set
  for the stack. Keep / drop needs per-switch evidence: build single-switch exes for S1, S2 (mode 2) and S4, each ABBA
  vs the lock; S3 as stack-with vs stack-without; the final number is the kept stack vs the lock, then QA's timing.
- Order (own reading, no Elo claim): 0 one-time tooling (copy-per-run in the ABBA tool ~2 h; a node-limit 12k driver
  ~0.5 h, needed: r12_fens12k.py has none (review fix) [C1]; the T12-03 level 3 / 5 compare driver per T12-03); 1 S1 (best rate 0.67 %/h; its poison and
  assertion builds also exercise the identity tooling); 2 S2 microbench, ABBA only if mode 2 passes it; 3 S4 (largest
  midpoint, own code with a prior own measurement; the line-146 plan names S1, S2 and S4 for ABBA); 4 S3 (a) timed in
  the kept stack; S3 (b) only when T04-04 / T05D-03 need a Board key (RANKING_FINAL: cost the key once for T05D-03).
- Crew hours total: 15 (3 + 3.5 + 1.5 + 7) + ~2.5 one-time tooling; optional S2 mode 3 +3-4 and S3 (b) +2 over (a).
  CPU: at s of about 4 % (n ~140 pairs, three arms) a d16-only comparison is ~20-30 min of one core; with d20 and the
  game probe one pair is 40-60 s, so the confirmation of a candidate that passed at d16 costs 1.5-3.5 h of one core
  (140-215 pairs; n grows with s^2: size it from the pilot). About 5 d16 comparisons plus microbenches: ~3-4 h of one
  core, + 1.5-3.5 h per confirmed candidate (review fix) [C2].
  No SPRT, no GPU.
