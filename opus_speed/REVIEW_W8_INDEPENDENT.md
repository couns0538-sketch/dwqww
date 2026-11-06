# Independent review of the W8 switches (T12B_BADCAP, NNUE_AVX512) on trial_w8

Reviewer: worker fable (speed-w8review), read-only. PC clock (`date`): claim 17:44, code and checks 17:44 -> 17:52,
file written from 17:52. Nothing was edited, built, linked or run as an engine; the only commands were `diff`,
`objdump -p` (PE header of existing exes) and `g++ -E -P` / `g++ -fsyntax-only` at Idle on CPUs 0-1
(`cmd /c start /B /WAIT /LOW /AFFINITY 3`, g++ 15.2 ucrt64, `-std=c++20 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -march` = the
kit's target). Scratch output only in the session scratchpad.

Headline: **no BLOCKER, no SHOULD; two LOW notes (a timing observation and a stack-budget note), no code defect found.**

## Findings

| id | severity | switch | file:line (trial_w8) | defect / observation | concrete scenario | suggested action |
|---|---|---|---|---|---|---|
| W1 | LOW (timing only) | T12B_BADCAP with NO_ZERO_MOVELISTS = 0 (bundle c) | `src/search.cpp:567` | With NZM at 0 the T12B array keeps its `{}`, so every `MovePicker` zero-fills 1024 B of `bad_captures_` instead of the lock's 256 B (one picker per `search` / `qsearch` node, two in nodes that run ProbCut). | CONFIRMED by reading; no wrong result possible. Bundle (c) carries this fill on every node; bundles (a) and (d) (NZM = 2) do not. QA's own single `x_t12b` had the same `{}` (its preprocess is byte-identical to T12B=1 at NZM 0), so (c) is a fair reproduction of what QA timed, only slower than the NZM bundles would be. | None for the stack. If bundle (c) is ever timed against (a)/(d), read its result with this in mind. |
| W2 | LOW (budget note) | T12B_BADCAP | `src/search.cpp:561`, `:567` | `sizeof(MovePicker)` grows from 3488 B to 4256 B (+768 B; measured with a compile-time size readout, unchanged by NZM). Every `Worker::search` and `Worker::qsearch` frame holds one picker (`search` holds two in disjoint scopes: ProbCut and main). | PLAUSIBLE only as arithmetic, no failing input found: worst case two frames per ply (main + singular / verification re-entry at the same ply) x 128 plies = 256 frames -> +192 KB (+384 KB if the compiler gives the two `search` pickers separate slots) on the 2 MB thread stack (kit exes: PE `SizeOfStackReserve` 0x200000, also the default for `std::thread`). The lock's own worst case on that path is about 1.15 MB, so the margin shrinks from about 0.85 MB to about 0.45-0.65 MB; realistic searches use a small fraction. | Keep a deep-ply stress in QA's extreme-FEN step (a position whose `seldepth` reaches 100+, e.g. a perpetual-check or long capture chain, Threads 1, `go depth 20`) for every bundle with T12B; both exes must answer and exit 0. |

Not findings: `Weights::b1` gets `alignas(64)` under AVX512 (`nnue.cpp:55-59`) although no 512-bit intrinsic loads it
(`acc = w.b1` is a plain array copy) - harmless, same as the crew file. The morning review's L3 (bit-equality of the
16-lane kernel needs no FMA contraction; the kit passes `-ffp-contract=off`) applies unchanged to bundles (a)-(d);
the new AVX-512 add / sub / update helpers contain no multiply, so no contraction is possible there.

## Point 1 - new code under `#if`, lock text verbatim under `#else`

- Hunk reading (`patches/b3_t12b_badcap_after_w6.patch`, `b3_nnue_avx512_after_w6t12b.patch`, `trial_w8.patch`): every
  lock line is either untouched or sits in the `#else` arm (T12B declaration: the lock's `std::array<Move, 64>
  bad_captures_{}` is the NZM = 0 / T12B = 0 arm, `search.cpp:569`; `b1` and `w2` alignas, `Accumulator` alignas, the
  add / sub helpers, the two update loops, the kernel chain). The T12B `assert` and the two `#error` blocks are pure
  additions with no lock text to preserve. `trial_w8.patch` removes 0 lines.
- Mechanical: `g++ -E -P` (kit flags) of all eight `.cpp` of trial_w8 with every switch at its default 0 is
  **byte-identical** to the lock's preprocessed text for all 8 TUs (without `-DNDEBUG` the only differences are the
  `assert` file / line strings). Consistent with the coordinator's switch-0 build = FD3A5190.

## Point 2 - T12B = 1 equals QA's edit; interaction with NZM and the picker

- `g++ -E -P` of trial_w8 `search.cpp` with `-DFORGE_SPD_T12B_BADCAP=1` (NZM 0) against QA's
  `D:\qa_simd_pc_20261105\x_t12b\t12b\src\search.cpp` (md5 539274a7, with its own `include`): **byte-identical**.
- Touch points of the array in trial_w8 `search.cpp`: write `:458-460` (assert + `bad_captures_[bad_count_++] = move`),
  reset `:494` (`bad_index_ = 0`), read `:497` (`bad_captures_[bad_index_++]` only while `bad_index_ < bad_count_`),
  declarations `:561/:563/:567/:569`, counters `:572-573` (per-picker, start at 0). Nothing else reads or writes it;
  SPEED2 (`generate_captures` / `generate_quiets` / `generate_evasions`, `QuietScorer`) and the TT / prefetch switches
  never touch it.
- Bound: every bad capture comes from `buffer_` (a `MoveList`, at most `Capacity` = 256 entries), one write per picked
  capture, so `bad_count_ <= count_ <= 256`; the array now has 256 slots, so the lock's unbounded write (morning L1)
  is closed and the `assert(bad_count_ < bad_captures_.size())` can never fire (it is compiled out under the kit's
  `-DNDEBUG` anyway).
- With NZM >= 1 the 256 slots are indeterminate at construction (`:561`); the only read is below `bad_count_`, which is
  exactly NZM's write-before-read rule (same rule as the 64-slot array in trial_w6). `Move` stays an aggregate, so the
  slots are plain storage; nothing walks the array to an `is_none()` sentinel (grep of every `is_none()` use).

## Point 3 - AVX512 = 1 equals the crew path at AVX512 = 1 / VNNI = 0; alignment; `__restrict`

- `g++ -E -P` of trial_w8 `nnue.cpp` with `-DFORGE_SPD_NNUE_AVX512=1` against the crew `nnue.cpp` (md5 08d8f5b3, its
  own `include`, its defaults `FORGE_NNUE_USE_AVX512 1`, VNNI 0): from `bool enabled = true;` to the end the only
  differences are `const auto*` vs `const float*` for the six column pointers (the same type at VNNI 0) and the braces
  around the shared kernel block; before that point the crew header adds `WeightScaleI`, `using Accel = float` (so its
  `Accumulator` spells `Accel` where trial_w8 spells `float`) and the `<cstring>` declarations - none reaches code.
  No VNNI token (`_mm512_dpwssd_epi32`, `adds_epi16`, `int16_t` weights) exists in the trial_w8 expansion; no `-D` is
  needed (the pack flips the default line, verified on the four `src_kit` trees below).
- Equality with the lock's arithmetic: `update_quiet` / `update_capture` / `add_feature` / `sub_feature` perform, per
  lane, `(s - r) + a`, `((s - r0) - r1) + a`, `acc + c`, `acc - c` in the lock's operation order with IEEE single
  ops; no multiply, so no contraction is possible; feature order in `refresh` and the generic update is unchanged
  (same loops around the helpers). The kernel is the morning review's 16-lane kernel (identical text).
- Alignment of every `_mm512_load_ps` / `_mm512_store_ps` (all addresses are `acc.data() + h`, `source + h`,
  `destination + h`, `ours/theirs.data() + base`, `w.w2.data() + base` or `+ HiddenSize + base`, `lanes`):
  - The only `nnue::Accumulator` objects in the program are `SearchStack::accumulator` (`search.hpp:308`); every
    `SearchStack` lives in `Worker::stack_` (`std::array<SearchStack, MaxPly + 8>`, `search.hpp:354`), and every
    `Worker` is created by `std::make_unique<Worker>` (`search.cpp:1739`) -> `alignof(Worker)` = 64 -> C++17 aligned
    `operator new` (the lock already took this path with `alignas(32)` > the 16-byte default). No `std::vector
    <SearchStack>`, no `new SearchStack`, no accumulator in `SearchInfo`, uci.cpp, book or eval (grep). The temporaries
    `SearchStack{}` in `Worker::clear` have automatic storage, which honours `alignas`, and are copied by the
    implicit assignment (no intrinsic, no alignment requirement). Helper threads use their own heap `Worker`s; the
    TT_NOTLS paths never touch accumulators.
  - `values[1]` and `w2 + HiddenSize` sit at +1024 B (`HiddenSize` 256 by the kit `-D`, 128 by the header default;
    both multiples of 16, `static_assert`ed in `add_feature` and `evaluate`), so the second perspective and the
    second half of `w2` keep 64-byte alignment. `Weights` is a function-local static (`alignas(64)` honoured in static
    storage); `lanes` is `alignas(64)` automatic storage. `w1` columns are read with `_mm512_loadu_ps` only (16-byte
    `make_unique<float[]>` storage) - correct.
  - "Copied into a buffer with less alignment": no such copy exists (no serialisation, no byte buffers, no packed
    structs; the `SearchStack` copy assignment is member-wise between two 64-byte-aligned objects).
- `__restrict` (`nnue.cpp:104-125`): `destination` = `child.values[p]`, `source` = `parent.values[p]`; the sole caller
  of `nnue::update` is `Worker::static_evaluate` (`search.cpp` replay loop) with `(ss - i - 1)->accumulator` and
  `(ss - i)->accumulator`, two different stack entries, so destination and source never alias. The column pointers
  address `w1` (a separate heap block) and are only read; for a quiet move `removed` (piece, from) and `added` (piece or
  promoted piece, to) are different features because from != to; for a capture `removed1` has the captured piece's
  colour, so it differs from `added` and from `removed0`. Even an aliasing pair of read-only restrict pointers would be
  well-defined; none occurs.

## Point 4 - the ZMM / AVX512 merge

- Shared lines read `#if FORGE_SPD_NNUE_ZMM || FORGE_SPD_NNUE_AVX512`: `Accumulator` alignas (`nnue.hpp:56`), the
  `<immintrin.h>` + `__AVX512F__` `#error` block (`nnue.cpp:22`), `w2` alignas (`nnue.cpp:60`), the kernel
  (`nnue.cpp:237`). `b1` alignas (`nnue.cpp:55`) is AVX512-only, correctly (ZMM alone never loads `b1` with a 512-bit
  intrinsic; neither does AVX512, see "not findings").
- `#if FORGE_SPD_NNUE_ZMM && FORGE_SPD_NNUE_AVX512` -> `#error` (`nnue.hpp:44-46`): a syntax-only compile with both at
  1 stops at that line (checked); it sits after both `#ifndef` defaults and is reached by every TU that includes
  `nnue.hpp` (nnue.cpp, search.cpp).
- Bundles (b) and (d) (ZMM 0, AVX512 1): the preprocessed `nnue.cpp` contains the 16-lane kernel
  (`_mm512_store_ps(lanes, sum)` once, the AVX2 kernel's `_mm256_store_ps(lanes + 8 * k, sums[k])` absent) and the
  `update_quiet` / `update_capture` calls.

## Point 5 - the four bundle switch sets compose

- `g++ -fsyntax-only -Wall -Wextra` (kit flags) of `nnue.cpp`, `search.cpp`, `board.cpp`, `bitboard.cpp` with each
  bundle's defines: (a) the six + T12B, (b) the five (ZMM 0) + AVX512, (c) T12B + AVX512, (d) the five + T12B +
  AVX512 -> 0 errors, 0 warnings for all 16 compiles.
- `diff -r F:\ospd\src\trial_w8 F:\ospd\packs\bundle_*\src_kit`: each kit tree differs from trial_w8 only in its switch
  default lines - (a) 7 lines (TT_NOTLS 1, NZM 2, SPEED2 1, PREFETCH_EARLY 1, SLIDER_PEXT 1, NNUE_ZMM 1, T12B 1),
  (b) 6 (the five + NNUE_AVX512 1), (c) 2 (T12B 1, NNUE_AVX512 1), (d) 7 (the five + T12B 1 + NNUE_AVX512 1).
- Pairs that needed a hand merge and have one: (NZM, SPEED2) in `generate_quiets` (trial_w6), (NZM, T12B) nested `#if`
  in the declaration (`search.cpp:559-570`), (ZMM, AVX512) the `||` lines plus the `&&` `#error`. Every other pair
  touches disjoint lines (TT_NOTLS: TT class and six call sites; PREFETCH_EARLY: `key_after` and the two prefetch
  sites; SPEED2: picker scoring and two extra prefetches; SLIDER_PEXT: bitboard only; T12B: the array and its write;
  AVX512: nnue only). No switch changes the behaviour of another's code path.

## For QA (beyond the pins the chain runs)

1. The morning review's section 4 still applies to every bundle (warm-TT replay without `ucinewgame` with Hash /
   Clear Hash / UseNNUE changes, `go nodes N` diffs, infinite + stop / ponder + ponderhit, Threads 2/4 soak then
   Threads 1 `bench 13` = 862329, extreme FENs, first-command robustness).
2. For (b)-(d): the accumulator paths are new code, so a net-ON pass matters most (the chain's L1 net on + L3 FENs
   cover it); add the poison build of the stacked source (0xA5 fill of the picker arrays) once per AVX512 bundle - the
   AVX-512 helpers never read an indeterminate slot by construction, but the poison run is the cheap proof.
3. W2: one deep-ply stress FEN at Threads 1 for every T12B bundle (both exes answer, exit 0).
