# Independent review of the six bit-exact speed patches (trial_w6)

Reviewer: worker fable (speed-patchreview), read-only. Time span (PC clock, `date`): 12:26 -> 12:44 reading and
analysis, file written from 12:44. Nothing was built or run; the only file created is this one.

## 1. Scope

I read the whole stacked patch `F:\ospd\wt\opus_speed\patches\trial_w6.patch` (lock -> trial_w6) and then, in the
patched tree `F:\ospd\src\trial_w6`, every file it touches in full: `include/forge/search.hpp`, `board.hpp`,
`bitboard.hpp`, `nnue.hpp`, `src/search.cpp`, `board.cpp` (lock generator, `key_after`, `make_move`, Zobrist tables,
castling masks, `has_legal_en_passant_capture`), `bitboard.cpp`, `nnue.cpp`, plus `src/uci.cpp` (command sequencing,
`stop_search` before every state change), `book.hpp`/`book.cpp` (the one `Move` member outside the patch) and the
kit's build line in `tools/build_variants.ps1` (`-std=c++20 -O3 -DNDEBUG -ffp-contract=off -fno-fast-math`, the
kit's `-march` target, `-static -pthread`). I formed the view below from the code first and only then read the
authors' notes in `jobb/*.md`; nothing in those notes changed a conclusion, and no claim below rests on them.
Focus, per the brief: Threads > 1, option changes and command sequences between searches, reads of slots that lost
their zero fill, bounds, AVX-512 alignment, start-up order, MSVC-vs-g++ differences, exception paths.

Headline: **no BLOCKER and no SHOULD finding.** With all six switches on, every path I could trace executes the
lock's statements in the lock's order on the lock's data; the differences are which cache line is prefetched and
when, which index addresses the same slider-attack entry, which register width carries the same sixteen partial
sums, whether a thread-local lookup that always returned "deferred" is still made, and whether memory that is never
read before it is written is zero-filled. Five LOW items are recorded, three of them robustness of the proof
rather than of the code, one pre-existing in the lock and unchanged by the patches.

## 2. Findings

| id | severity | switch | file:line (trial_w6) | defect | concrete failure scenario | suggested fix |
|---|---|---|---|---|---|---|
| L1 | LOW (pre-existing in the lock; the patch neither introduces nor worsens it) | NO_ZERO_MOVELISTS | `src/search.cpp:457` (write), `:557` (array) | `bad_captures_[bad_count_++] = move` has no bound against the 64-slot array, unlike `quiets_tried` / `captures_tried` (`:1428-1429`, bounded). The patch only removes the array's zero fill; the write path is the lock's. | PLAUSIBLE, contrived positions only: a node whose capture stage yields more than 64 SEE-negative entries (queen captures of pawn-defended pieces plus quiet promotions onto defended empty squares count 4 each) overflows into `bad_count_` / `bad_index_` -> the BadCaptures stage then returns slots beyond the array -> `is_legal` / `make_move` on a garbage move (`squares_[from]` with `from` up to 255). Identical in the lock exe. Not reached by bench, the 12k FENs or gate play as far as the existing proofs show. | Bound the write like the other two arrays (`if (bad_count_ < bad_captures_.size())`) or size the array 256. Belongs to a separate correctness item on the lock, not to the speed stack (it would change no node in any position the proofs cover but is a code change outside the switches). |
| L2 | LOW | SLIDER_PEXT | `include/forge/bitboard.hpp:14-16` | The guard `#if !defined(__BMI2__) #error` is keyed on a macro MSVC never defines, although MSVC's `<immintrin.h>` has `_pext_u64`. | CONFIRMED (the coordinator's OWN_CHECKS #6 had to pass `/D__BMI2__=1`): any MSVC build (the ASan rows) of a source with the switch at 1 stops at the `#error`; a build that forgets the define silently loses its sanitizer coverage of the PEXT path. No run-time effect on the g++ kit exe. | `#if !defined(__BMI2__) && !defined(_MSC_VER)` (MSVC: require `__AVX2__` from `/arch:AVX2` or higher instead), or document the define in the kit. |
| L3 | LOW (robustness of the proof) | NNUE_ZMM | `src/nnue.cpp:182-201` vs the AVX2 kernel `:203-217` | Bit-equality of the two kernels needs that neither `mul`+`add` pair is contracted into an FMA. The kit line carries `-ffp-contract=off`; g++ in its GNU-dialect mode (`-std=gnu++20`, the CMake default when extensions are on) defaults to `fast` and may contract vector intrinsics, and nothing in the source pins the choice. | PLAUSIBLE only off the kit line: a build without `-ffp-contract=off` can contract the AVX-512 kernel and the AVX2 reference differently -> different `out` bits -> different evaluations -> node identity lost, with no diagnostic. On the kit line and in CI with the switch at its default 0 nothing changes. | Keep a `vfn?m(add|sub)` count = 0 gate on the *kit* exe in `speed_pack.ps1` / `bitexact_check.ps1` (the authors counted on plain builds only), or add `#pragma GCC optimize ("fp-contract=off")` around the kernel with a comment. |
| L4 | LOW | PREFETCH_EARLY | `include/forge/search.hpp:131-137`, `src/search.cpp:1039-1041`, `:1352-1354` | `TranspositionTable::prefetch` is a no-op on a compiler without `__builtin_prefetch` (the `#else` branch, e.g. MSVC), but the switch still computes `key_after` for every searched move. | CONFIRMED by reading: a non-GNU build with the switch at 1 pays the `key_after` work (one table walk per move) for no prefetch at all; never a wrong result, only a slower exe. Not the kit's case. | Make the switch imply the GNU path: `#if FORGE_SPD_PREFETCH_EARLY && !(defined(__GNUC__) \|\| defined(__clang__))` -> `#error` or auto-disable. |
| L5 | LOW (maintenance) | TT_NOTLS | `src/search.cpp:1766-1773`, `include/forge/search.hpp:376-386` | The lock-free path is correct because of an invariant that lives in two places: `Searcher::search` takes the lease only with one worker and then runs `workers_.front()` on the same thread. Only the assert build (`assert(has_exclusive_access())` in `probe_owned` / `store_owned`, `:304`, `:337`) checks it; the `-DNDEBUG` kit exe does not. | PLAUSIBLE, future code only: a later change that moves the main worker to another thread, or takes the lease elsewhere, turns the owned path into an unlocked access from a thread that is not the lease holder; a Threads 1 gate would still show identical nodes because no other thread touches the table, so it would surface only in a multi-threaded or library use. Today's tree is correct (see section 3). | Keep the assert build as a CI row for every stack that carries the switch; optionally store the lease-holder `std::thread::id` in the scope guard and compare it in a debug-only check inside `probe_tt` / `store_tt`. |

Not findings, recorded for completeness: the SPEED2 comment at `board.hpp:247-248` says entries 13..15 of
`PieceTypeTable` carry "the same values as the modulo form" - they are 0 where the modulo form gives 1..3; no valid
`Piece` reaches them and no caller passes an out-of-range value, so no behaviour depends on it (comment only).

## 3. Checked and fine

**TT_NOTLS (Threads > 1, option changes, lifecycle).** The owned flag is a copy of `exclusive.has_value()`
(`search.cpp:1759-1773`), and `exclusive` is emplaced only when `table_access == Exclusive && workers_.size() == 1`.
With Threads > 1 the flag is false on every worker (helpers never set it; it is a per-Worker member with default
`false`), so every TT access is `probe_body<true>` / `store_body<true>`, whose text is the lock's `probe` / `store`
line for line including `lock_stripe` and the handle check as the first statement of the store. With one worker and
the lease, the lock's `lock_stripe` returned a deferred (unlocked) `unique_lock` after a thread-local read, so skipping
it changes no memory access; foreign accessors are still drained and blocked by the untouched lease code, and
`hashfull()` (called from `emit` on the same thread) still goes through `lock_stripe`. The scope guard is declared
after `exclusive`, so it is destroyed before the lease and restores the previous flag on return and on throw; a nested
search on the same thread restores correctly through `previous`. The UCI loop calls `stop_search()` (join) before
every `setoption` (Hash resize, Clear Hash, Threads, UseNNUE), `position`, `go`, `ucinewgame`, `bench`, so `resize` /
`clear` (which bump `epoch_` and invalidate old probes exactly as in the lock) never run next to an owned access; the
`bench` Searcher is a separate table with one worker. `probe_body<false>` / `store_body<false>` are private and only
reachable through `Worker::probe_tt` / `store_tt` (friend under the switch). The six call sites keep their
arguments and order (qsearch probe `:977`, stand-pat store `:1012`, final qsearch store `:1077`; search probe `:1123`,
ProbCut store `:1246`, final store `:1457`).

**NO_ZERO_MOVELISTS value 1 (indeterminate slots).** `Move` keeps aggregate status; `Move{}`, `Move::none()`,
`std::array<Move, N> x{}`, `killers = {}`, `TTEntry::move{}`, `SearchStack` members, `TTCluster{}`,
`make_unique<TTCluster[]>` (value-init) and `make_unique<CounterMoveTable>()` all remain all-zero. Objects that lose
the fill and every read of them: `MovePicker::moves_` read only in `pick_best` over `[index_, count_)` and by
`std::sort` over the same range; `bad_captures_` read over `[0, bad_count_)`; `check_squares_` read at indices 1..6
(`piece_type` of a generated move's mover, never Empty) only inside `generate_quiets` / `generate_evasions` after
`init_check_squares()` wrote 1..6; `quiets_tried` / `captures_tried` read in `update_quiet_stats` /
`update_capture_stats` below `quiet_count` / `capture_count`; `MoveList::data_` read below `size_` (`begin()..end()`,
`operator[]` in `legal_moves` below the written prefix, `front()` only behind `!empty()` checks at `:1566`, `:1576`,
`:1584`, `:1711` and in `book.cpp:163-180` on a non-empty vector). The three bare `Move move;` (`:1025`, `:1224`,
`:1276`) are assigned in their loop condition before any read. No code walks a move list to an `is_none()` sentinel
(grep of every `is_none()` use). `Book::Candidate::move` is only ever aggregate-initialised (`book.cpp:154`).

**NO_ZERO_MOVELISTS value 2 (quiets-only generation = the lock's filtered list, same order).** Lock full list:
single pushes, double pushes (both from `regular = pawns & ~seventh`), promotion pushes, pawn captures, en passant,
then N, B, R, Q, K each over `attacks & ~own` in bit order with captures and quiets interleaved, then castling under
`!captures_only && checkers_ == 0`. The picker's filter drops exactly the moves with `Capture`, `EnPassant` or
`Promotion`. Quiets mode (`board.cpp:425-536`): the same two push loops (`!captures_only`), none of the three
`!quiets_only`-guarded loops, pieces over `attacks & empty` (the bit-ordered subsequence of `~own` that is not
enemy, flagged `Quiet` because `to` is never enemy-occupied), castling under the same test. `GenMode::All` and
`GenMode::Captures` take the lock's two bool paths unchanged (promotion pushes still emitted under `Captures` because
`quiets_only` is false there); the bool overload is an exact match for the lock's callers, no int literal is passed
anywhere. Evasions, `legal_moves`, `has_legal_move`, `perft` and `parse_uci` keep the full generator.

**SPEED2 (rebased onto the value-2 generator).** `QuietScorer::score` = `main[from][to] + cont1[p][to] + cont2[p][to]`
in the lock's order with the same null checks, plus 12000 on the same `check_squares_` test; `generate_captures`
computes `10 * capture_value + capture_history[moved][to][victim]` with the same indices as `capture_value` /
`capture_history_value`; the extra prefetches after the null move and the ProbCut make are hints only; `piece_type`
table equals the modulo form for every `Piece` value 0..12. `(ss - 1)` / `(ss - 2)` are read for ply 0 too, as in the
lock (`stack_[2..3]` exist and hold the `[Empty][0]` continuation pointer).

**PREFETCH_EARLY (`key_after` vs `make_move`, `board.cpp:848-872` vs `:875-946`).** Term by term: captured piece at
`to` (`Z.piece[Empty][*] == 0` so a non-capture adds nothing), mover off `from`, mover or promoted piece on `to`, the
rook pair for a castle, `Z.castling[old] ^ Z.castling[old & masks[from] & masks[to]]`, `Z.side`. The en-passant terms
are the only conditional ones: the current square's term is removed by `make_move` only when
`has_legal_en_passant_capture()` holds, so `key_after` refuses every position with `ep_square_ >= 0` and every
en-passant capture; the child's term is added only when `attacks::pawn(us, passed) & pieces(them, Pawn)` is non-empty
(the candidate test inside `has_legal_en_passant_capture` after the side flips), which is exactly the double-push case
`key_after` refuses. Any mismatch could only prefetch another cluster (`cluster_for` maps every key in range): the
searched tree cannot change. `assert(child_key == board.key())` is compiled out under `-DNDEBUG`.

**SLIDER_PEXT.** Index = `pext(occ, mask)` is a bijection from the 2^popcount(mask) subsets onto
`[0, 2^popcount)`, the same per-square region size the multiply magics use (`shift = 64 - popcount`), so the lock's
0x19000 / 0x1480 tables and offsets hold; bits outside the mask are ignored by PEXT as by `& mask`. Tables are filled
by the same `sliding_attack` reference, read-only after `attacks::init()`, which the `Board` constructor runs before
any position exists (unchanged order; `RookMagics` / `BishopMagics` are constant-initialised zero before that, as in
the lock). The `Magic` record shrinks to 16 bytes; every reader goes through `index()` / `table`.

**NNUE_ZMM (alignment, lane order, arithmetic).** `Accumulator::values` and `Weights::w2` become `alignas(64)`; the
second perspective and `w2 + HiddenSize` sit at 1024-byte offsets (`HiddenSize` 256, static_assert multiple of 16), so
every `_mm512_load_ps` is aligned; `lanes` is `alignas(64)`. `SearchStack` lives in `Worker::stack_` and `Worker` is
heap-allocated with `std::make_unique` -> C++17 aligned `new` (the lock already required 32-byte alignment through the
same path); `Weights` is a function-local static. Lane m of the zmm sum takes units h + m for h = 0, 16, ...; the AVX2
kernel's `lanes[8k + j]` = `sums[k]` lane j takes units h + 8k + j: the same unit sequence per lane, the same
`min(max(x,0),1)`, `(a*a)*w2a + (b*b)*w2b`, `sum += term` order, the same final scalar reduction, no contraction on the
kit line (L3). `_mm512_min_ps` / `_mm512_max_ps` and the 256-bit forms have the same NaN / signed-zero rule.

**Bounds.** `MoveList` and `moves_` hold 256 >= the 218-move maximum (pseudo-legal lists are longer than legal ones but
the lock's capacity is unchanged and its push_back assert is compiled out as before); `quiets_tried` (128) and
`captures_tried` (64) are bounded at the write; `bad_captures_` is L1 (lock's bound). No patch adds a buffer.

**Start-up / static init.** No new static object with a dynamic initialiser; the PEXT fill removes the magic
search and its three function-local statics; `Weights` keeps its magic-static init. **Exceptions.** Only the scope
guard is new and it is RAII. **MSVC vs g++.** L2, L4; `alignas(64)` members and aligned `new` are standard C++17 on
both; the template conditional `TakeLock ? lock_stripe(index) : std::unique_lock<std::mutex>()` is well-formed on
both (same prvalue type in both arms). **Switch-0 = lock.** The coordinator's byte-for-byte build equality of the
all-switches-0 tree covers the `#else` branches; I additionally diffed each `#else` body against the lock text in
the patch hunks.

## 4. What the existing proofs miss - tests for QA (all Threads 1 unless stated; stack exe vs lock exe, exact diff of
`info` / `bestmove` lines with `nps` and `time` fields dropped)

Every identity proof so far ran on a fresh table (`bench` clears per FEN, the 12k run sent `ucinewgame` per FEN) and
a fixed `Hash`. The copied TT bodies are only exercised through aging (`generation() != generation_`) and
`relative_age` replacement on a warm table, and the owned flag is only exercised across state changes:

1. Warm-TT replay, no `ucinewgame`: one script, 40-60 half-moves of a game as successive
   `position startpos moves ...` + `go depth 10`; then the same with `setoption name Hash value 1`,
   `setoption name Hash value 64`, `setoption name Clear Hash`, `setoption name UseNNUE value false` / `true`
   interleaved every ~10 moves. Deterministic -> the two exes must print identical lines.
2. `go nodes 20000` on 100 of the 12k FENs without `ucinewgame` (node-limited searches are deterministic at Threads 1).
3. `go infinite` then `stop` after 300 ms; `go ponder` then `ponderhit`; `go ponder` then `stop`; `go mate 3` on a
   mate-in-3 FEN; `go movetime 100` x 20 without `ucinewgame`: a `bestmove` must arrive each time, exit code 0
   (timing searches are not compared for nodes).
4. Threads soak: `setoption name Threads value 2` and `4`, 50 FENs x `go movetime 300` with `Hash` and `Threads`
   changed between searches, then `setoption name Threads value 1` and `bench 13` must print 862329 (flag and lease
   state after helpers existed). No identity is possible at Threads > 1; TSan is not available on this toolchain
   (CI item).
5. Poison build of the *stacked* source (trial_w6 or stack_w2): `memset(0xA5)` of `moves_`, `bad_captures_`,
   `check_squares_`, `quiets_tried`, `captures_tried` and `MoveList::data_` at construction, then `bench 16`
   (3024920) and 1k FENs at `go depth 13` against the lock. The authors' poison proof ran on the value-1/2 source
   alone, before the SPEED2 rebase of `generate_quiets` / `generate_evasions` / `generate_captures` (new readers of the
   same slots).
6. Extreme positions at `go depth 8` and `go perft 3`, both exes compared, and the same under the MSVC ASan build
   (with `/D__BMI2__=1`): the 218-legal-move position `R6R/3Q4/1Q4Q1/4Q3/2Q4Q/Q4Q2/pp1Q4/kBNN1KB1 w - - 0 1`, a
   mass-promotion position such as `k7/P1P1P1P1/8/8/8/8/p1p1p1p1/K7 w - - 0 1`, and a many-captures position
   (queens versus a defended pawn chain) for L1.
7. For NNUE_ZMM: `objdump -d <kit exe> | grep -c -E 'vfn?m(add|sub)'` = 0 on both the lock kit exe and the stack kit
   exe (L3), and a net-off (`UseNNUE false`) pass over a 2k subset of the 12k FENs at depth 13 (the 12k run was net
   on; net off routes every node through the HCE with the same TT / picker / generator paths).
8. First-command robustness: start the exe and send `bench 1` and `go perft 1` as the very first commands (tables
   built by the global `Board` before any `position`), then `quit`; exit code 0.
