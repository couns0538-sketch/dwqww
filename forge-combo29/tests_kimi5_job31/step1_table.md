# kimi5 job 31 — Step 1 reading table: r15d → kF under "Windows x64, clang 23, llvm-mingw libstdc++"

Diff read: `diff -ru r15d/include kF/include` + `diff -ru r15d/src kF/src` = 2,450 lines, 9 files
(evidence: `step1_diff_include.txt`, `step1_diff_src.txt`; trees sha-verified 29/29 each, step 0 pins met on both).
Reference platform here: Linux x86-64, g++ 13.3.0, AVX-512+BMI2 native. Target: Windows x64 (LLP64: long 32 bit,
size_t 64 bit), clang 23.1.5 (llvm-mingw 20261104, x86_64-w64-mingw32), libstdc++, -march=znver5, ThinLTO+PGO.
Per row: kF file:line | class | what my Linux g++ build does | what the PC build does | verdict + one-line reason + the check that would show it.
Verdicts: SAFE = same behaviour by reading (a reading, not a test); DIFFERS = behaviour can differ; UNSURE = cannot decide by reading.

## DIFFERS and UNSURE rows first

| # | kF file:line | class | Linux g++ 13.3 | PC clang 23 / mingw | verdict |
|---|---|---|---|---|---|
| E1 | src/search.cpp:1199-1202 | (e) | `std::sort(moves_+index_, moves_+count_, [](const Scored&a,const Scored&b){return a.score>b.score;})`: equal-scored moves keep whatever order g++ 13.3's introsort leaves; ties are common (zeroed histories at every search start, the +12000 check bonus :1028, zero cont rows :1010). Ties DO occur and decide move order (job 28 rows are tie-order-dependent trees) | MinGW's libstdc++ comes from another GCC release than 13.3; `std::sort`'s equal-element order is unspecified and set by the implementation's introsort. A different order of equals = a different pick order = a different tree | **UNSURE** — the one line in the stack whose result is library-version-defined and search-visible. Check: PC bench pins (bench 11=312866 / 13=862329 reach quiet ties in iteration 1), then the 553 W1 rows on the PC; C3 here probes that ties exist and move results. No repair that keeps node counts exists if it differs (any tie-break changes the order vs g++ 13.3) — see report §8 |

## SAFE rows, by class

### (a) sizes
| # | kF file:line | what it is | verdict |
|---|---|---|---|
| A1 | whole diff (evidence: greps in report §4) | No `long`/`unsigned long` object, no `1L`/`1UL` shift, no printf/scanf length letter in any added or changed line. Indexing is std::size_t (64-bit under LLP64), keys/nodes std::uint64_t, entries fixed-width | SAFE — LLP64's 32-bit long touches nothing the stack reads. Check: the quoted greps |
| A2 | include/forge/search.hpp:305-308 | `cluster_index`: `(u128)key * cluster_count_ >> 64U`, guarded `#if defined(__SIZEOF_INT128__)`; size_t is 64-bit on Windows x64 | SAFE — probed: clang for x86_64-w64-mingw32 defines `__SIZEOF_INT128__ 16` (step2 `clang_macros.txt`; clang 18 feature-flag probe, znver5 set). Fallback `%` (:310) and the hi32 tag of `verification_key` (:298-305) are NOT taken on the PC; if a toolchain ever dropped __int128 both index and tag change — bench pins catch that |

### (b) alignment
| # | kF file:line | what it is | verdict |
|---|---|---|---|
| B1 | include/forge/search.hpp:246 (`probe_owned_fast`), src/search.cpp:605 (`store_owned_fast`), :987 | `_mm512_load_si512(reinterpret_cast<const __m512i*>(&cluster))`; memory = `make_unique<TTCluster[]>` (src/search.cpp:450), `struct alignas(64) TTCluster` (search.hpp:131), layout pinned by static_asserts (search.hpp:133-136: sizeof 64, offsetof key32/depth/gen_bound) | SAFE — C++17 aligned new guarantees 64 B on both; MinGW libstdc++ provides aligned new (else: loud link error). Failure would be a loud crash, not a silent diff. Checked here by job 28 C13a/C13b (111M probes, 0 fails); on PC: bench pins |
| B2 | src/nnue_v3.cpp:395-450 (fused one-refresh), :1077-1120 (`refresh_from_pieces` AVX-512) | `_mm512_load/store_si512` on: `Accumulator::values` (alignas(64), nnue_v3.hpp:120), `RefreshCache::Entry::values` (alignas(64), :133) — std::vector of over-aligned types → aligned new; w1/w2 columns via `column()` (nnue_v3.hpp:186) from `AlignedInt16` = `::operator new(n, align_val_t{64})` (nnue_v3.cpp:522) with matching aligned delete (:527). Stride 32 int16 = 64 B; MaxHidden 1024 ≥ hidden (256 built-in, 768 PC-class net); hidden % 32 == 0 for both | SAFE — every base is 64-aligned by construction on any host with aligned new. Suspicion (unproven, in report): loops assume hidden % 32 == 0; a net without it would read past a w1 column's end |
| B3 | src/search.cpp:814-846 (`pick_best_scored`) | `_mm512_loadu_si512` / `_mm256_*` on `moves_` — unaligned intrinsics only; `static_assert(sizeof(Scored)==8)` (:815) | SAFE — no alignment requirement at all |

### (c) intrinsics and macros (guard; does -march=znver5 under clang 23 define it)
| # | kF file:line | guard macro | verdict |
|---|---|---|---|
| C1 | include/forge/search.hpp:154-156 (`#include <immintrin.h>`), :245; src/search.cpp:604, :814 | `__AVX512F__` | SAFE — znver5 has AVX-512F/BW/VL/DQ; clang defines the macros for the mingw target (probed, `clang_macros.txt`); immintrin.h ships in llvm-mingw |
| C2 | src/nnue_v3.cpp:22-26 (`FORGE_NNUE_V3_AVX512`), :89, :108, :151, :390, :1070 | `__AVX512F__ && __AVX512BW__` | SAFE — both defined on the PC. Fallback rows (FORGE_NNUE_V3_AVX2 at :18-20, scalar `#else`) are NOT taken on the PC and untested everywhere here |
| C3 | include/forge/search.hpp:251, :257; src/search.cpp:611, :826, :843 | `__builtin_ctz` | SAFE — clang builtin; every call is dominated by a nonzero test (`hit_m != 0U` :250, `occ_m != 0x8888U` :231, `chunk_max > best_score` :824/:840 ⇒ mask ≠ 0). No ctz(0) |
| C4 | include/forge/search.hpp:177-180; call sites src/search.cpp:2353, :2364, :2367, :2604, :2655, :2871, :2884 | `__builtin_prefetch` | SAFE — clang lowers it on Windows x64; a hint, result-neutral |
| C5 | include/forge/search.hpp:210, :351, :356; src/search.cpp:551, :690, :1233, :1257, :1586; src/uci.cpp:67 | `[[gnu::always_inline]]`, `[[gnu::noinline]]`, `[[gnu::hot]]` | SAFE — clang accepts all three on mingw; inlining choices may differ (performance only, never node counts) |
| C6 | include/forge/bitboard.hpp:10-15 + src/bitboard.cpp:66 (`FORGE_SPD_SLIDER_PEXT`, r15d code, in the -D list); src/nnue.cpp:26-28 (`FORGE_SPD_NNUE_ZMM`) | `__BMI2__`, `__AVX512F__` | SAFE — both guards are `#error` (loud, never silent); `__BMI2__` and `__AVX512F__` probed defined for the target |
| C7 | include/forge/search.hpp:307 | `__extension__ using u128 = unsigned __int128` | SAFE — clang supports __int128 on the mingw x86_64 target (probed) |

### (d) undefined / implementation-defined behaviour
| # | kF file:line | what it is | verdict |
|---|---|---|---|
| D1 | include/forge/b4.hpp:39-62 (`lesser_threats` lazy Rook/Queen) | `by_type[Rook]`/`[Queen]` are left unset when the side has no R/Q — but `std::array<Bitboard,7> by_type{}` (b4.hpp:36) zero-initialises them; reads (`threat_set_for_piece`, search.hpp:324-331) return 0 | SAFE — zero-initialised member, not an indeterminate read; platform-independent |
| D2 | src/board.cpp:67-71, :154-160, :186 (`dbg_key` + `assert(key_ == dbg_key)`), include/forge/search.hpp asserts | `#ifndef NDEBUG` / `assert` | SAFE — `-DNDEBUG` on both recipes; compiles out identically |
| D3 | include/forge/search.hpp:246; src/search.cpp:605; src/nnue_v3.cpp:395-450, :861, :878, :1077-1120 | reads through `reinterpret_cast<const __m512i*>` of int16/byte storage | SAFE — GCC/clang intrinsic vector types carry may_alias, so the puns are defined on both compilers (no `-fno-strict-aliasing` needed or set on either). Check: C1 — a clang build must reproduce every row, exercising these loads ~10^11 times |
| D4 | src/search.cpp:553-563 (`replace_full_cluster_slot`), :1025-1031 (`PieceContRows::extra`), :1060/:1096/:1152 (blend), :896-901 (promo scores) | int arithmetic bounded: depth−4·age ≥ −124; extra ≤ 32767·2+16383+12000; blend ≤ 32767·4; promo ≤ 10·(v+900−100)+32767+20000 | SAFE — all ≈ ≤1.6·10^5 ≪ 2^31; no signed overflow on either compiler |
| D5 | src/search.cpp:897, :909, :1028, :1099 (`>> move.from/to` on ULL); include/forge/search.hpp:308 (u128 `>> 64U`) | shifts | SAFE — operands are 64-bit with counts 0..63, or 128-bit with count 64 < 128. No shift ≥ width |
| D6 | include/forge/search.hpp:645-649 + src/search.cpp:1706-1707 (`threat_map_ready_`/`threat_maps_`), :648-649 (`picker_scratch_`, `evasion_scratch_`) | uninitialised-value reads | SAFE — ready-flags are zero-initialised members, reset by memset in `Worker::clear`; scratch lists are `clear()`ed before every fill; `WorkerTTProbe` fully initialised on every return path |

### (e) library and system
| # | kF file:line | what it is | verdict |
|---|---|---|---|
| E2 | include/forge/search.hpp:196 (`static thread_local const ExclusiveLease* active_lease_`, kept under FORGE_SPD_TT_NOTLS=1) | thread-local storage | SAFE — native TLS on llvm-mingw x86_64; unchanged by the stack |
| E3 | src/search.cpp:3217-3219, :3733-3736; src/uci.cpp:497 | `std::chrono::steady_clock` | SAFE — QPC-backed on Windows; feeds time management only, never node counts at fixed depth/nodes |
| E4 | src/uci.cpp:46-58 (`is_uci_ws`, `next_uci_token`), :67 (`apply_position_sv`), :184 (`parse_limits_sv`) | whitespace/tokenising replaces istringstream | SAFE — ASCII-explicit, locale-independent (stricter than r15d's istringstream); equivalence = job 28 piece 04 items 1-2 (rows equal over 1,700+ searches) and C1 here |
| E5 | src/uci.cpp:250-260, :383-395; src/search.cpp:3227-3229 | `std::from_chars` / `std::to_chars` on integers | SAFE — locale-independent, identical results on both |
| E6 | whole diff | POSIX-only API | SAFE — none: allocation via C++17 aligned new (nnue_v3.cpp:522, search.cpp:450), not posix_memalign; no mmap/unistd/sysconf; nothing Windows names otherwise |
| E7 | src/search.cpp:1007-1012 area (picker `MoveList buffer_` removed → Worker-shared scratch, include/forge/search.hpp:648-649) | stack use per ply | SAFE — kF uses no more per-ply stack than r15d; recursion depth is compile-bounded (MaxPly); Windows 1 MB thread stack covers it. Check on PC: bench 16 |
| E8 | src/search.cpp:1690-1707 (`Worker::clear` memsets) | memset == value-init for flat POD tables | SAFE — proven job 28 piece 04 item 3; same libstdc++-independent semantics |
| E9 | CMakeLists.txt:19,29 (`FORGE_NNUE_HIDDEN` default 256, always passed as -D); include/forge/nnue.hpp:18-21 (header default 128); src/nnue.cpp:61 + src/nnue_weights.inc:5 (static_asserts) | the PC recipe omits `-DFORGE_NNUE_HIDDEN=256` | SAFE — here CMake adds =256 regardless; if the PC's script bypassed CMake with the wrong value, the shape static_asserts fail the build loudly. The PC's own net is out of scope (job text) |

### (f) the info line under `go nodes`
| # | kF file:line | what it is | verdict |
|---|---|---|---|
| F1 | src/search.cpp:3216 (`emit` lambda in `Worker::search`), :3240 (`put_lit("info depth ", 11)`), :3220 (nodes = `total_nodes()`); call sites :3543, :3554, :3633, :3647 | the periodic info line | ANSWERED — a node-limit-stopped search prints NO further line: the single-PV loop breaks on `if (aborted_) break;` (:3645) BEFORE `emit(depth, score, result.pv)` (:3647), and both abort-publish emits are guarded by `!stopped_by_nodes_` (:3538, :3545, :3547; flag set at :2036, cleared :3127). The last printed line is the last COMPLETED iteration, whose nodes sit below the limit — exactly job 28 §4.3's inference, now from the print code itself (its C13a proof: 200×20,000 TT probes) |

## Fallback paths the PC does NOT take (named per the job)
- search.hpp:237-258 scalar TT probe loop (`#else` of `__AVX512F__`); search.cpp:613-619 scalar store re-scan.
- search.hpp:310-312 `cluster_index` modulo + search.hpp:303 hi32 tag (`#else` of `__SIZEOF_INT128__`).
- src/nnue_v3.cpp:452-458 scalar fused-refresh `#else`; FORGE_NNUE_V3_AVX2 path (:18-20).
- src/search.cpp:848-874 AVX2-only pick block (`#if defined(__AVX2__)` after the AVX-512 block) — compiled on both, reached only for remainders < 8 after the AVX-512 chunks; same on the PC.
None of these is reached differently on the PC: every guard macro is defined there (probed) exactly as here.

## What this check cannot see (per the job)
The PC itself: its Windows loader, the llvm-mingw runtime, the profile step, Zen 5. A row marked SAFE is a reading, not a test.
Additionally: clang 18 here does not know `-march=znver5` (added in clang 19), so C1 runs `-march=native` on this AVX-512
host and the znver5 macro claims rest on the feature probe + the hardware facts; the MinGW libstdc++ VERSION (E1) no
Linux check can see; the PGO profile and ThinLTO (codegen only, not results unless UB exists — D-rows say none added).
