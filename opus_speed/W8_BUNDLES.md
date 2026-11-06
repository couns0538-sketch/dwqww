# W8 bundles: T12B-01 + AVX512 NNUE switches on top of trial_w6 (follow-up, 2026-11-05 from 17:00 PC clock)

Brief (owner, leftover usage): add QA's two separately timed bit-exact winners as default-0 build switches,
build bundles (a)-(d) with the existing speed_pack / LTO+PGO path (lp_v1 = QA kit v2.3 lines, `-Twice`, pc1 = pc2) on
CPUs 0-1 at Idle, and pin-check every bundle against the lock FD3A5190: net on and net off at d11/13/16/20/22, plus
perft 5 startpos and kiwipete. **No ABBA here** (QA times the bundles on CPU 10). This file makes **no lock claim and
no Elo claim**.

## Switches (default 0; new code under `#if`, lock text verbatim under `#else`)
| switch | files | what it does | equality with the source QA timed |
|---|---|---|---|
| `FORGE_SPD_T12B_BADCAP` | `include/forge/search.hpp` (default), `src/search.cpp` | QA item T12B-01: MovePicker's `bad_captures_` becomes `std::array<Move, MoveList::Capacity>` instead of 64 entries, with `assert(bad_count_ < bad_captures_.size())` before the write (a no-op under the kit's `-DNDEBUG`). The switch sits inside both `FORGE_SPD_NO_ZERO_MOVELISTS` branches of the declaration. | `g++ -E -P` (kit flags, `-march=znver5`) of trial_w8 `search.cpp` with T12B=1 against QA's `x_t12b\t12b\src\search.cpp` (md5 539274a7): 79,118 / 79,118 non-blank lines identical. |
| `FORGE_SPD_NNUE_AVX512` | `include/forge/nnue.hpp` (default + `#error`), `src/nnue.cpp` | The crew's float AVX-512 path: `crew-nnue-avx512-pc-20261105` `src/nnue.cpp` md5 08d8f5b3 with `FORGE_NNUE_USE_AVX512` = 1 and VNNI 0. It brings `b1`, `w2` and the Accumulator to `alignas(64)`. Feature add / sub (refresh and the generic update) and the `update_quiet` / `update_capture` helpers (`__restrict`) use 16-lane zmm with the lock's per-lane order. The output layer is the 16-lane kernel. Not carried: the int16 VNNI path, `<cstring>`, `WeightScaleI`, `Accel`. No compiler `-D` (the crew kit's added `-DFORGE_NNUE_USE_AVX512=1` is not used); the pack flips the default line. | `g++ -E -P` of trial_w8 `nnue.cpp` with AVX512=1 against the crew file, compared from `bool enabled = true;` to the end. The only differences are `const auto*` vs `const float*` (the same type at VNNI 0) and the braces around the shared kernel block. Before that point: the header differs only by `WeightScaleI` / `Accel` and the system headers that `<cstring>` and the earlier `<immintrin.h>` pull in. |

**ZMM vs AVX512 fight on the same lines.**
- FORGE_SPD_NNUE_ZMM's output kernel is token-identical to the crew's AVX-512 kernel.
- Both raise the same two alignment lines: Accumulator `values` and Weights `w2`.
- In trial_w8 those three places read `#if FORGE_SPD_NNUE_ZMM || FORGE_SPD_NNUE_AVX512`.
- `#if FORGE_SPD_NNUE_ZMM && FORGE_SPD_NNUE_AVX512` is an `#error`.

So every bundle with AVX512 keeps AVX512 and **drops ZMM** (bundles b and d). Bundle (a) keeps trial_w6's ZMM.

## Shared tree and patches
| file | md5 | what |
|---|---|---|
| `patches/b3_t12b_badcap_after_w6.patch` | 92ce4980 | trial_w6 tree -> + T12B switch |
| `patches/b3_nnue_avx512_after_w6t12b.patch` | 658dbe87 | the above -> + AVX512 switch (merged with ZMM as described) |
| `patches/trial_w8.patch` | ba7f733f | lock -> trial_w8 (all 8 switches at 0); written by `make_stack.sh trial_w8 trial_w6.patch <the two above>` (no fuzz). make_stack reports 8 switches at default 0; the patch adds 700 lines and **removes 0 lock lines**. |

**Switch-0 identity.** `build_variants.ps1 -Variant lp_v1` of `F:\ospd\src\trial_w8` (build `F:\ospd\builds\w8sw0_lp_v1`, 17:30) gives `forge_lp_v1.exe` sha256 `fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072`. That is **lock FD3A5190 byte for byte**.

That build's quick-pin step then timed out, so the folder holds a FAILED marker:
- The tool had been started from the agent's PowerShell tool. Launched that way, the engine never sees `uci`, and it exits 0 when stdin closes.
- The same script started from Git Bash gets `uciok` in 0.11 s.
- The exe bytes are the lock's, so the identity stands.
- All later runs start the tools from Git Bash.

## Bundles
Source `F:/ospd/src/trial_w8`. `speed_pack.ps1 -Quick -SkipAbba`; each pack flips its switch lines in `F:\ospd\packs\<name>\src_kit`.

| bundle | switches on | exe sha256 | pins: L1 net on + off d11/13/16/20/22, L2 perft 5 x2 | extra: L3 2,000 FENs d13, L4 sanitizers |
|---|---|---|---|---|
| (a) `bundle_a_w6_t12b` | the six (TT_NOTLS, NZM=2, SPEED2, PREFETCH_EARLY, SLIDER_PEXT, NNUE_ZMM) + T12B_BADCAP | (pending) | (pending) | (pending) |
| (b) `bundle_b_w6_avx512` | five (ZMM dropped) + NNUE_AVX512 | (pending) | (pending) | (pending) |
| (c) `bundle_c_t12b_avx512` | T12B_BADCAP + NNUE_AVX512 (none of the six) | (pending) | (pending) | (pending) |
| (d) `bundle_d_w6_t12b_avx512` | five (ZMM dropped) + T12B_BADCAP + NNUE_AVX512; started after (a)-(c) had a verdict | (pending) | (pending) | (pending) |
