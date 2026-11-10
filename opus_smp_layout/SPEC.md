# opus_smp_layout — SPEC (fixed before any engine code; 2026-11-09 ~19:15 Vienna)

Scope: the missing lockless-TT correctness/layout change and the worker false-sharing fix on parent P (= trial_w6 source,
commit 7ce10a05). Default OFF. No search, eval, voting or history change.

## 1. Names (fixed; no existing name changes)
| kind | name | default | where |
|---|---|---|---|
| compile-time switch | `FORGE_SMP_LAYOUT` | `0` | `include/forge/search.hpp`: `#ifndef FORGE_SMP_LAYOUT` / `#define FORGE_SMP_LAYOUT 0` / `#endif`. This is the single `#define FORGE_SMP_LAYOUT 0` line a kit source copy flips (speed_pack convention: the kit takes no `-D`) |
| UCI option | `TtLockless` | `false` (type check) | advertised and accepted only when `FORGE_SMP_LAYOUT=1` |
| CMake option | `FORGE_SMP_LAYOUT` | `OFF` | `ON` adds `FORGE_SMP_LAYOUT=1` to `forge_core` (PUBLIC) and registers the two new tests. CI on this branch configures `ON` |

Everything new in engine sources is inside `#if FORGE_SMP_LAYOUT … #endif`, including `#include` lines. There are no new
`src/*.cpp` files, because the kit compiles all of them.

## 2. Builds and what each must show
| build | source | must hold |
|---|---|---|
| **OFF** (compile-time 0) | branch tip as is | `g++ -E -P` of all 8 units with the kit flags is identical to P. The kit LTO+PGO exe is `4181a589…` = P = trial_w6 (pc1 = pc2). `uci` lists no `TtLockless` |
| **GATE** (compile-time 1) | tip with the one define flipped to 1 | pc1 = pc2. `TtLockless` advertised, default false |
| GATE, `TtLockless=false` | — | P node-identical: pins net on and off, perft, full fens12k net on and off at go depth 13, warm-state identity (Threads 1) |
| GATE, `TtLockless=true` | — | the same checks at Threads 1 (node-identical by construction, §3.2), plus the race/stress evidence of §6 |

Any node or eval difference at Threads 1 is a failed qualification, reported as SEARCH/EVAL CHANGE (UNPROVEN) and never as a speed result.

## 3. Lockless TT protocol (`TtLockless=true`)
### 3.1 Storage: one typed array per mode
- Legacy mode (option false) keeps P's storage and code: `std::unique_ptr<TTCluster[]> clusters_` (TTEntry structs), the 1024 stripes and the ExclusiveLease, unchanged.
- Lockless mode uses `std::unique_ptr<TTLocklessCluster[]> lockless_clusters_`, where `struct alignas(64) TTLocklessCluster { std::array<std::uint64_t, 8> words; }` holds 4 entries of 2 words (64 B). Internal type name; the fixed public names are those of §1. Cluster count and index mapping are the same as `cluster_for` (multiply-high on `__int128`, modulo otherwise).
- Exactly one of the two arrays is allocated; the other pointer is null.
- While workers run, every access to `words[]` is a `std::atomic_ref<std::uint64_t>` load, store or `compare_exchange_strong` with `memory_order_relaxed` (C++20). Static asserts:
  - `std::atomic_ref<std::uint64_t>::is_always_lock_free`;
  - `alignof(std::uint64_t) >= std::atomic_ref<std::uint64_t>::required_alignment`;
  - `sizeof(TTLocklessCluster) == 64`.
- No word is accessed non-atomically while any worker runs. Allocation (value-initialisation) and clearing happen only when quiescent (§3.6).
- There is no union or type punning between the two layouts, no seqlock, and no plain racy field.

### 3.2 Encoding: an exact bijection TTEntry ⇄ (K, D)
- **D** (data word): bits 0-15 = score (two's complement), 16-31 = eval, 32-39 = depth, 40-47 = gen_bound, 48-55 = rule50_clock, 56-63 = padding.
- **K** (key word): bits 32-39 = move.from, 40-47 = move.to, 48-55 = move.promotion, 56-63 = move.flags. Bits 0-31 = `key32 XOR tag32(D)`. `GenMask = 0xF8 << 40` marks the five generation bits of gen_bound.
- **tag32**(d) = `uint32(((d & ~GenMask) * 0x9E3779B97F4A7C15 mod 2^64) >> 32)`. This is multiply-shift hashing: one multiply and one shift. Revision 2 (enc2) replaced the original 3-multiply `mix32(move32, d)`. The move is not hashed: it travels inside K, so a K/D pair can never mix two moves.
- `tag32(0) = 0`, so zeroed storage decodes to the all-zero TTEntry, the same empty entry as P's value-initialised clusters.
- `decode(encode(e)) == e` holds for every 16-byte TTEntry value. With one thread, every probe and store therefore sees exactly P's entries, and the search tree is identical. This is tested by the differential test in §5.

### 3.3 Atomic publication, validation, torn reads and key/payload coherence
- A writer publishes one entry as two relaxed single-copy-atomic stores: D first, then K. A reader loads K and D with two relaxed loads, so a word can never be torn.
- The **pair** may still mix two stores: another writer between the reader's two loads, or two writers interleaving their four stores.
  - Decoding K with a foreign D gives `key32_K ^ tag32(D_K) ^ tag32(D_read)`.
  - It equals the probed tag only if `tag32(D_K) == tag32(D_read)`. The mixed pair then reads as a foreign entry: a miss, or a replacement candidate.
  - Generation-only differences are harmless. Generation is replacement metadata and is never read by search.
- **Strength of the tag.** Let `delta = D_K' - D_read'` (mod 2^64, generation bits cleared) and `y = delta * TagMul`. The two tags can be equal only if `high32(y) == 0`, or if `high32(y) == 0xFFFFFFFF` with `low32(y) != 0` (a carry). So:
  - **Never collides** (proven for the odd multiplier, and checked exhaustively by `tools/tag_scan.cpp` and test group 1):
    - two entries that differ only in depth, bound, pv or rule50 (bits 32-55), in any combination;
    - any single-bit difference;
    - every small field difference: |score| and |eval| ≤ 32 (with the int16 wrap), |depth| ≤ 8, any bound/pv change, |rule50| ≤ 4, in every combination (38 million deltas).
  - **Score/eval-only differences:** exactly the deltas listed by `tag_scan` part 1 can collide (BENCH §9).
  - **Everything else:** over the choice of an odd multiplier, `P[collision] ≤ 2^-31` per pair (multiply-shift universality, Dietzfelbinger et al. 1997). That is about one bit weaker than a perfect 32-bit tag, in exchange for the structural guarantees above.
- A **validated hit** therefore carries key, move, score, eval, depth, bound, pv and rule50_clock from **one** store, except with probability about 2^-31 per torn read whose two data words differ in score/eval and elsewhere. On top of that is P's own 32-bit tag-collision rate (`verification_key` unchanged).
- No ordering beyond relaxed is needed. The entry carries all its data in its two words, and nothing else is published through the TT (no pointers, no indices into other memory).
- Search keeps its own TT-move checks, unchanged: `MovePicker` drops a move that is not `is_pseudo_legal`, and every move is `is_legal`-checked before it is made.
- Collision correctness is P's. Torn pairs add no new class of wrong hit beyond the 2^-31 term above.

### 3.4 probe (mirrors P's `probe_body` step by step)
1. Compute the index. Load the 4 (K, D) pairs (8 relaxed loads). The decisions read the fields straight from these raw copies (`key32_of`, `occupied_of`, `generation_of`, `depth_of`; test group 1 checks that they equal the decoded fields). Only the returned slot is decoded into the snapshot (enc2; before, all four slots were decoded).
2. First pass, slots 0..3: the first slot with a tag match that is `occupied()` is the hit.
   - If its generation differs from `generation_`, do `compare_exchange_strong(D_loaded → D with the current generation)`. K stays valid because GenMask is outside the tag.
   - If the CAS fails, the entry changed under us and the refresh is skipped. It never fails with one thread.
   - The snapshot is the decoded entry with the refreshed gen_bound, as in P.
3. Otherwise apply the replacement rule to the same 4 raw copies, as in P:
   - the first unoccupied slot returns at once;
   - else the strictly smallest `depth - 4 * relative_age` wins, and a tie keeps the earlier slot.
4. The TTProbe snapshot fields (`owner_`, `cluster_`, `slot_`, `epoch_`, `key_`) are as in P.

### 3.5 store (mirrors P's `store_body`)
1. Same handle gate: owner, epoch, key, `cluster < count`, `slot < 4`.
2. Load K and D of the slot, decode, and apply P's rules unchanged:
   - keep the old move if the new move is none and it is the same position;
   - rewrite fully on an exact bound, a different position, depth + 4 > old depth, or an old generation.
3. Encode. Store D if it changed, then K if it changed, both relaxed.
- A racing writer can cause a **lost update**, or a **mismatched pair** that reads as foreign (§3.3). It cannot cause an incoherent hit, apart from the 2^-31 term.

**hashfull:** relaxed loads of D in the first `min(1000, count)` clusters, counting entries that are occupied with `generation == generation_` (raw readers). Same arithmetic as P.
**prefetch:** the same index on the active array (`base + idx * 64`). A null array is never prefetched.

### 3.6 Lifetime, clear and resize synchronisation
- `resize`, `clear`, `new_search` and the mode toggle are allowed only while no worker runs. The existing call sites already guarantee this:
  - UCI `stop_search()` stops and joins the search thread before `ucinewgame`, `setoption`, `position`, `go` and `bench`;
  - `Searcher::search` joins its helpers before it returns;
  - tests join their threads.
- Thread start and join create the happens-before edges. The plain fields (`generation_`, `epoch_`, `cluster_count_`, the mode flag, the array pointers) and the value-initialisation of a new array therefore need no atomics.
- **Mode toggle** (`TranspositionTable::set_lockless(bool)`; no-op if unchanged):
  - allocate the other type with the same cluster count first (value-initialised = empty), then free the old array: a failed allocation leaves the table unchanged, as in P's `resize` (R1 review MINOR-3);
  - set `generation_ = 0` and `++epoch_`, so stores through old TTProbe handles are rejected.
  - The TT is therefore cleared when `TtLockless` changes.
- `resize` and `clear` act on the active array with P's semantics (`generation_ = 0`, `++epoch_`).
- **Mode of the bench searcher** (it has its own TT): UCI `bench` calls `set_tt_lockless(true)` on it when `TtLockless` is true, so bench pins also exercise the ON path.
- `probe_tt`/`store_tt` read the table's own `lockless_` flag (written only while quiescent) before P's `tt_owned_` branch. There is no per-worker copy that could go stale after a toggle, so a direct `Worker::search` (test harnesses) also follows the current mode (R1 review MINOR-1; regression test in `smp_lifecycle_tests`).
- The public `probe`/`store`/`probe_owned`/`store_owned`/`hashfull`/`prefetch` all follow the table's mode, so no path touches the inactive (null) array.

## 4. Worker cache-line layout (measure first, change only what is measured)
- Tool `tools/layout_probe.cpp` (a test executable, not in the engine) prints sizeof, alignof and offsets, with 64-byte line numbers, of the Worker hot fields, SharedSearchState, TranspositionTable members, TTCluster/TTLocklessCluster, SearchStack and Accumulator, plus the heap addresses of 4 workers. It runs for P (macro 0) and the gate build (macro 1).
- Rule: pad or align only a line that one thread writes while another reads it during search. The known candidate is `Worker::nodes_`:
  - its owner stores it in `should_stop`; every other worker loads it in `total_nodes()` (every node under `go nodes`, else every 1024 nodes and at info output);
  - in P it shares a line with the owner's per-node fields (`local_nodes_` and its neighbours).
- Fix (macro 1): `alignas(64)` on `nodes_` **and** on the member after it, `local_nodes_`. `nodes_` then sits alone on its 64-byte line (measured: BENCH §2), so remote loads no longer invalidate the owner's per-node fields. Publication frequency and node-limit semantics are unchanged.
- Anything else changes only with a measured reason, recorded in BENCH.md. No blanket padding.

## 5. Tests (CTest; built when CMake `FORGE_SMP_LAYOUT=ON`; run natively and under TSan / ASan+UBSan in CI)
1. `forge_tt_lockless_tests` (`tests/tt_lockless_tests.cpp`):
   1. **round trip:** `decode(encode(e)) == e` for random and edge entries; `tag32(0) = 0`; the raw readers equal the decoded fields. **Tag detection** (enc2): every single-bit difference and every small field difference of §3.3 can never collide (exact delta criterion), and so can no difference confined to bits 32-55 (100k-sample check of that proven case).
   2. **differential:** a legacy table and a lockless table get the same random probe/store/new_search/clear/hashfull stream (one thread, small tables, many collisions). Every probe result (hit and entry bytes) and every hashfull value must be equal, and so must the full table contents, every slot of every cluster compared through `debug_entry` (which also covers slot choice and stale-handle rejection).
   3. **contention/collision fixture:** 4-8 threads on 1-16 clusters store `payload = f(key)` and probe. Every hit must satisfy `payload == f(key)` (zero incoherent hits), with CAS and store races included.
   4. **positive control:** the same fixture against a test-only *unvalidated* two-word table (no XOR tag) must observe incoherent hits. This shows the fixture can detect tearing. Since R1 MINOR-2 this is a failing check: with ≥ 2 hardware threads, more than 100k control hits with 0 incoherent ones fails the test (blind fixture). Only with 1 hardware thread is it reported as INCONCLUSIVE.
   5. **lifecycle:** resize, clear and mode toggles between joined phases. Old handles are rejected after each.
2. `forge_smp_lifecycle_tests` (`tests/smp_lifecycle_tests.cpp`): a Searcher at Threads 1/2/4/8 in both TT modes.
   - Each run does repeated depth- and node-limited searches, an external `stop()` from another thread mid-search, an infinite search plus stop, and `clear_hash`/`resize_hash`/`set_threads`/mode toggles between searches.
   - Pass conditions: every bestmove is in the legal move list, every case finishes within its time bound, destruction is clean, and with Threads 1 the nodes of both modes are equal.
3. The existing 12 groups of `forge_tt_tests` and every other existing CTest stay green.

## 6. Race/stress evidence (before any strength handoff)
- CI TSan, ASan+UBSan and release runs on the pushed commit. The verdict names the run id and the log hashes.
- If CI cannot build or run TSan, that claim is **UNVERIFIED**. Nothing is ever called "race proof".
- Native evidence on CPUs 12-15, labelled oversubscribed: CTests repeated, plus `tools/uci_lifecycle_stress.ps1` on the gate exe with both modes at Threads 1/4/8.
- Commands for anything not run go to COMMANDS.md as PREPARED-ONLY.

## 7. Not changed
- Search and eval decisions.
- Per-thread histories.
- SmpV2 (not in trial_w6).
- Thread voting and best-thread choice.
- Node publication frequency.
- The legacy stripe and lease code.
- The trial_w6 switches.
- The TtReplaceCache pack (it overlaps textually and is separate).
