# Independent read-only review: the 30-h job's engine patches (v2port.patch, expose22.patch, O30Tuned, tune_spsa.py)

Reviewer: the independent agent session (same one that reviewed the R14 finish and the GPU-window code); it authored
none of this code. Read-only: no build, no engine run, no git state change, nothing touched that runs. Started
2026-11-04 12:27 PC clock (`date`); patched sources read with `git -C D:/o30/repos/v2root show 9037f2a:<path>`.
Line numbers below are those of the patched tree at 9037f2a.

## Scope and identity
- `D:\o30\wt\opus_30h\a\v2port.patch` md5 926ada2cc6b2212c05cd72cf70feefc9 = `git diff fe0da8d 9037f2a` of
  D:\o30\repos\v2root (re-hashed: identical). Files: include/forge/nnue_v2.hpp (new, 338 lines),
  include/forge/search.hpp (+2), src/nnue.cpp (+191), src/search.cpp (+92/-1), src/uci.cpp (+22).
- `D:\o30\wt\opus_30h\b\expose22.patch` md5 73cd35917a872d2a00b8ce6219d6f7d7 (src/search.cpp only).
- `D:\o30\wt\opus_30h\b\o30_tuned_patch.py` (111 lines), `D:\o30\wt\opus_30h\b\tune_spsa.py` (368 lines).
- Background read: a/RESULTS.md (R-A1 self-review, R-A2 root fix, lockstep, rematches), the loader checklist skill
  (`forge-nnue-loader-checklist`, SKILL.md in the project's skills folder of D:\grok-pc-data\dwqww), the lock-side
  code the patch relies on
  (nnue.hpp Accumulator / DirtyPieces, nnue.cpp refresh / update / evaluate / dirty_pieces, search.cpp
  static_evaluate / record_move / record_null_move / set_threads / search start, eval.cpp runtime PSQT, uci.cpp
  command loop), the live SPSA run's params.csv and config (D:\o30\spsa\stc8_main).

## Findings

| ID | severity | file:line | one line |
|---|---|---|---|
| E-001 | SHOULD | src/uci.cpp:272-283 (v2port) | A failed `EvalFileV2` load leaves the compiled-in (lock) net active with only an `info string ERROR`; a gate line with a mistyped net path measures the lock against the lock and reads as "neutral". Mitigation that exists: pin_check's ON-line "dead option" test (ON bench = lock bench) - it must stay in every gate recipe; the checklist's alternative (eval OFF after a failed explicit load) would make the mistake visible in play. |
| E-002 | SHOULD | b/o30_tuned_patch.py:64-73,92 | `O30Tuned=false` writes the params CSV's `start` column as "the lock value"; the script checks only that the name exists in search.cpp, not that `start` equals the source literal (`int <Name> = <lit>;`). A wrong CSV start makes "true then false" differ from the untouched exe for that parameter; the dummy-set test covers only the tested set. Fix: parse the literal from src/search.cpp and refuse a mismatch. |
| E-003 | NIT | include/forge/nnue_v2.hpp:179, src/nnue.cpp:417 (v2port) | `std::clamp(worker_id, 0, MaxWorkers-1)` would silently make two workers share one refresh cache (a data race on the accumulator cache) if ids ever exceeded 255; unreachable today (Threads clamped to 1-256 at uci.cpp:301 / search.cpp:1569, ids 0..count-1 at search.cpp:1572). Prefer `assert`/fail-closed over clamp. |
| E-004 | NIT | src/uci.cpp:283 (v2port) | `clear_hash()` after a net change clears the TT and worker caches but not the correction histories, which hold net-dependent corrections; harmless for gates (the option is set once before `ucinewgame`), inconsistent for a net swap mid-game. |
| E-005 | NIT | src/search.cpp:685 (v2port) | The OFF path pays one global load + predicted branch per static evaluation (`active_net != nullptr`); measured 1.02x advisory by the author - stated, not a defect. |
| E-006 | NIT | b/tune_spsa.py:120-121 | `plus` and `minus` are rounded to integers independently; with a per-parameter `c_end` below 0.5 both can round to the same value and the batch's R (pure noise) still moves theta. Not the case in stc8 (c_end 5-384, so plus and minus differ by >= 10 before rounding); add a guard for future configs. |
| E-007 | NIT | b/tune_spsa.py:156-168 | The CPU-overlap wait sees only `fastchess.exe`; a match driven by another runner on the same CPUs is not detected (noise, not bias). All matches of this job use fastchess, so it held here. |
| E-008 | NIT | b/o30_tuned_patch.py:31-43,89-95 | A duplicated name in TUNED_OPTIONS.txt is accepted and the last value wins silently in the generated loop; a tuned value equal to the lock value is accepted as a no-op. Refuse duplicates. |
| E-009 | NIT | src/uci.cpp:270 (v2port) | Trailing spaces of the path are trimmed (a path ending in a space cannot be given); harmless. |
| E-010 | NIT (latent, unreachable in every exe of this job) | src/search.cpp:712 vs 608-611 (v2port) | `record_move` returns early when `!nnue::available()` (no compiled-in net), while `static_evaluate_v2` checks only `nnue::enabled`: on a build without the compiled-in net a loaded v2 net would never get dirty pieces recorded or child accumulators invalidated, and stale stack accumulators would be evaluated. Every exe of this job compiles the net in (`FORGE_HAS_NNUE != 0`), so it cannot occur there; the v2 path's correctness should not depend on that flag. Fix: `if (!nnue::enabled \|\| (!nnue::available() && nnue::v2::active_net == nullptr)) return;` in record_move (or bail out of static_evaluate_v2 on `!available()` the same way). |

No BLOCKER. Nothing found that makes OFF differ from the lock, that makes the incremental, cache-refresh and full-refresh
accumulators differ, that races between threads, that reads out of range on a hostile file, or that changes a default
away from the lock literal. Details and the evidence for each "checked" item follow.

## v2port.patch - what was checked and how

### OFF = lock (bit-identical)
- The default path changes in exactly two places: `Worker::static_evaluate` (search.cpp:685) gains
  `if (nnue::v2::active_net != nullptr) [[unlikely]] return static_evaluate_v2(board, ss);` and the search start
  (search.cpp:1452-1459) gains `active_net == nullptr &&` on the existing refresh condition plus an `else if` for
  the v2 root refresh. With `active_net == nullptr` (the constant-initialised default, nnue.cpp:252) both reduce to
  the lock's code; `record_move` / `record_null_move` (search.cpp:709-722) are untouched; `static_evaluate_v2`
  (search.cpp:608-682) sits in its own section (`.text.forge_v2`, noinline) so the surrounding functions keep their
  layout. uci.cpp adds the
  option line and the handler only. The author's OFF proofs (pin_check -Full on every build, kit pc1 = pc2) are
  consistent with this reading; I did not run a bench.

### Loader (src/nnue.cpp:302-398) against the checklist
- Order of checks before any allocation: open; size (seekg/tellg, rejects < 168 bytes and > file_bytes(32, 16));
  160-byte header read; magic; version 2; header_bytes 160; feature_set 0; inputs 768; hidden == engine HiddenSize;
  king buckets 1-32; output buckets 1-16; unknown flag bits; the three scales / sigmoid K exactly equal (float
  compare, no tolerance); every king_map entry < king_buckets (64); every output_map entry < output_buckets (33);
  reserved bytes zero; then `size == file_bytes(kb, ob)` exactly; only then the whole file is read and the stored
  little-endian FNV-1a 64 (nnue.cpp:371, bytes n-8..n-1) is compared with the hash of every preceding byte. A failed
  check before `loaded_net = net.release()` leaves `active_net == nullptr` (unload() at the top of load();
  `active_net` is constant-initialised to nullptr at nnue.cpp:254).
- Index safety downstream: `king_key()` indexes king_map by a 0-63 square (nnue_v2.hpp:147-150), `feature()` <
  king_buckets x 768 because the map entries were range-checked, `output_bucket()` indexes output_map by
  `min(popcount(occupied), 32)` (nnue_v2.hpp:272-274), `w2 + bucket*2*HiddenSize` < output_buckets x 2 x HiddenSize.
  No read can leave the allocated arrays for a file that passed the header checks.
- De-quantisation int16 / 4096 (w1, b1) and / 4096 (w2, b2) = the compiled-in `weights()` (nnue.cpp:390-393 vs the
  lock's loader); values are multiples of 2^-12 with |value| <= 8, so an accumulator (<= 32 pieces + bias) stays
  below 2^12 in magnitude and every float add / subtract on it is exact (24-bit mantissa) - the header comment's
  claim holds; the int16-accumulator overflow rule of the checklist does not apply (float accumulators).
- Load happens only from `setoption`, which calls `stop_search()` first (uci.cpp:145-154, 193: join of the search
  thread), so `unload()`'s `delete` can never race a worker reading `active_net`.
- Hostile files tried by the author's fuzz (21 kinds, a/RESULTS.md) match the code paths above; I did not run them.

### Accumulator scheme (search.cpp:608-682 `static_evaluate_v2`) vs the compiled-in one (search.cpp:685-707)
- Same lazy scheme: walk back to the nearest valid ancestor (`back` loop, identical), full refresh when none
  (including the root: the four entries below `stack_[4]` are invalidated at every search start, search.cpp:1446-1451,
  so `(ss - 1)` of the root is never a stale valid entry), else replay every ply and mark it valid.
- King-bucket / mirror handling: the ancestor's king squares are rebuilt by undoing `changes[0]` of every replayed
  ply (search.cpp:626-632); `dirty_pieces()` (nnue.cpp:225-244) records the mover's removal first for every move
  type - castling adds the rook changes after the king's, en passant removes the captured pawn from its own square,
  promotion removes the pawn and adds the promoted piece - so `changes[0]` is the king exactly when the king moved.
  On a replayed ply where the mover is color c's king, the destination is the `add` change of the same piece
  (search.cpp:643-647; castling: changes[1]); if its (bucket, flip) key differs from the key in use (search.cpp:649),
  that perspective is rebuilt through the worker's refresh cache from the placement of that ply (`pieces_of(board)`
  minus the later plies' changes, `undo()` nnue_v2.hpp:169-176, which inverts add/remove correctly for captures, promotions, en
  passant and castling), the key is replaced, and the ply's `update` for that color is skipped (`continue`). The
  other perspective's key depends only on its own king, so its `update` is correct. A mirror-flip crossing (d-file
  to e-file) changes `flip` and takes the same path (`KingKey::operator==` compares bucket and flip).
- Null move: `record_null_move` sets `dirty.count = 0`; `update()`'s generic branch (nnue_v2.hpp:264-268) then
  copies parent to child (`apply_columns<0,0>`), as the compiled-in generic branch (nnue.cpp:152-163) does; the king
  reconstruction skips it (`dirty.count > 0`).
- Update kernels: (1 sub, 1 add), (2, 1), (2, 2) and the generic fallback apply the same subtract-then-add order per
  lane; because every operand is a multiple of 2^-12 below 2^12 the order cannot change the bits, so incremental,
  cache-refresh (`refresh_cached`, nnue_v2.hpp:209-246: per (perspective, bucket, flip) entry, at most one removal
  and one addition per square, entry initialised to the bias with an empty placement = the empty-board
  accumulator) and full refresh (`refresh`, nnue_v2.hpp:196-205) agree bit for bit. The author's in-search verify
  build (`FORGE_NNUE_V2_VERIFY`, search.cpp:666-676: every evaluated accumulator compared with a full refresh) and
  the 830k / 1.1M-ply walks are the runtime evidence; I did not run them.
- Residual: `evaluate_runtime(board, runtime_psqt) + network`, clamped to the mate window, with the same
  `update_runtime_psqt` chain and the same `if (!valid) refresh` fallback as the compiled-in path (search.cpp:677-681
  vs 702-706); `update_runtime_psqt` copies the parent's `valid` (eval.cpp:502-517), so an invalid ancestor cannot
  produce a wrongly valid child. The network term uses the same `* 400 / SigmoidK`, clamp +-30000 and truncation as
  `nnue::evaluate` (nnue_v2.hpp:333-336 vs nnue.cpp:221-222).
- Output kernel: `output()` (nnue_v2.hpp:277-330) is the compiled-in `evaluate()` (nnue.cpp:166-223) with w2 / b2
  taken from the selected output bucket: the same sixteen ordered lanes, the same clamp-square-multiply-add per lane
  for AVX2, SSE and the scalar fallback, the same final ordered sum; the only differences are the bucket row offset
  and `FORGE_NNUE_V2_SCALAR` for the parity builds. Alignment: `Accumulator::values` is `alignas(32)`
  (nnue.hpp:32), w1 / w2 are 64-byte allocations (AlignedFloats), the bucket row offset is a multiple of 1024
  bytes, so every `_mm256_load_ps` / `_mm_load_ps` is aligned.
- Threads: accumulators live in each worker's own `SearchStack` (search.hpp:281); the refresh cache is per worker id
  (`Net::caches[id]`, created and used only by that worker, nnue.cpp:416-427); ids are unique 0..count-1 and Threads
  is clamped to 256 = MaxWorkers; the `Net` is otherwise immutable after load. A Threads change re-creates workers with
  the same ids, which reuse the existing cache slots - any cached placement is a valid starting point. No shared
  mutable state is written during the search except each worker's own slot.
- Root fix (search.cpp:1455-1459, R-A2): the root is evaluated once at search start through `static_evaluate_v2`,
  which builds its accumulators from the cache and sets `runtime_psqt`; nodes are unchanged by construction (the
  accumulator values are identical to the lazy ones), as the author's bench / game-position comparison states.
- UCI: `setoption name EvalFileV2 value <path with spaces>` is reassembled from the first token plus the rest of
  the line (uci.cpp:267-270); empty / `<empty>` unloads; success and failure both print one `info string`; the hash
  is cleared after either (E-004). The option is advertised as `type string default <empty>` (uci.cpp:175).

### Not verified for v2port
- No build, bench, parity, walk, verify or fuzz was run; the correctness claims rest on the code reading above plus
  the author's recorded proofs (identity to d22 with the lock net as v2, parity 10000/10000 x 3 kernels, walk, in-search
  verify, lockstep 727 plies at 200k nodes).
- The exporter side (export_v2r.py / o30_v2net.py layouts) was reviewed in the GPU-window review; the loader's layout
  matches it ([kb][768][H], [ob][2H]).

## expose22.patch - every default against the lock literal (all 22 equal)

| option | default | lock literal (removed line) | identical at the default? |
|---|---|---|---|
| NmpEvalDepthMargin / NmpEvalBase | 24 / 180 | `beta - 24 * depth + 180` | yes |
| NullMoveEvalMax | 3 | `std::min(..., 3)` | yes |
| NullMoveVerifyDepth | 14 | `depth < 14` | yes |
| ProbcutImproving | 50 | `- 50 * improving` | yes |
| ProbcutReduction | 4 | `depth - 4` | yes |
| SingularTtDepth | 3 | `tt_depth >= depth - 3` | yes |
| SingularDoubleMargin / SingularDoubleLimit | 24 / 6 | `singular_beta - 24`, `<= 6` | yes |
| LmrTtPv, LmrNotImproving, LmrTtCapture, LmrGivesCheck, LmrInCheck, LmrCutoffCount | 1024 | `r -= 1` / `r += 1` | yes: `r1024 = 1024 * reduction +- 1024 ...; r = r1024 / 1024` is an exact integer multiple at the defaults, positive or negative (C++ truncation on an exact multiple) |
| LmrCutNode | 2048 | `r += 2` | yes |
| HistoryMalusPercent | 100 | `-bonus` | yes: `bonus * 100 / 100 == bonus` for every integer bonus |
| HistoryDepthBonusMargin | 100 | `best_score > beta + 100` | yes |
| AspirationMinDepth | 4 | `depth >= 4` | yes |
| AspirationGrowPercent / AspirationGrowAdd | 50 / 4 | `delta += delta / 2 + 4` | yes: floor(delta * 50 / 100) == floor(delta / 2) for every non-negative integer delta |
| QuietCheckBonus | 12000 | `+= 12000` (two sites) | yes |

Ranges contain every default (NmpEvalBase 180 in [-200, 600], LmrCutNode 2048 in [0, 6144], ...). The options are plain
`int`s set from `setoption` only (search stopped first), read by all workers - the same model as the lock's existing
tunables. For TUNED values the author's note stands: the LMR terms are summed in 1/1024 ply and truncated toward zero.

## o30_tuned_patch.py and tune_spsa.py
- O30Tuned handler (generated, o30_tuned_patch.py:85-101): `true` / `false` writes every set member clamped to its
  option range and calls `tune::refresh()`; any other value is reported; the three anchors must be unique (the
  namespace anchor at least once, replaced once); a tree that already has O30Tuned, an unknown name, an out-of-range
  value or a non-integer start is refused. E-002 and E-008 above.
- tune_spsa.py: SPSA in game pairs with `c_k = c_end N^gamma / (k+1)^gamma`, `a_k = r_end c_end^2 (A+N)^alpha / (k+1+A)^alpha`,
  `theta += a_k / c_k * R * delta` (R = plus wins - losses over the batch; sign correct: a better `plus` moves theta
  along +delta); delta is seeded by (seed, k), so a retry of a failed batch and a resume reuse the same perturbation;
  openings are sequential from `k % n_openings + 1` (stc8 sets `book_openings` 2,632,036 = the line count of the UHO
  EPD, so the index never runs off the book), every pair with colours swapped (`-games 2 -repeat`), so there is no
  colour or opening bias between plus and minus. At a range bound the clamp makes the perturbation one-sided (plus
  pinned to max, minus at theta - c) while the step still assumes +-c - standard SPSA boundary behaviour, not a bias
  in the interior. State: one fsynced
  JSON record per batch, a torn last line is skipped, a resume refuses a changed config (threads / cpus excepted) or
  params CSV; stop by named event, deadline, pair caps or disk floors; never kills. The live stc8 run (8 parameters,
  tc 8+0.08, 1800 pairs planned, 2 pairs per batch, alpha 0.602, gamma 0.101, A 0.1 N) has c_end 5-384, so E-006 does
  not bite. Nothing found that biases or corrupts a run.

## Not verified overall
- No compilation or execution of any patched code (rules of this task); the O30Tuned handler's compile is known only
  from the author's dummy-set build; the SPSA simulation / self-test results are the author's.
- E-004 confirmed from the header: `Worker::clear_caches()` is `evaluator_.clear()` (search.hpp:307, the hand-crafted
  evaluation's caches); `Searcher::clear_hash` (search.cpp:1578-1581) clears the TT and those caches, not the
  correction histories (`Searcher::clear` on `ucinewgame` does).
