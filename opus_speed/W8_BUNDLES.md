# W8 bundles: T12B-01 + AVX512 NNUE switches on top of trial_w6 (follow-up, 2026-11-05, logged 17:30-17:53 PC clock)

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
| (a) `bundle_a_w6_t12b` | the six (TT_NOTLS, NZM=2, SPEED2, PREFETCH_EARLY, SLIDER_PEXT, NNUE_ZMM) + T12B_BADCAP | `3f3e734416a17f9f16ecc0dd68d5acfb2fe8dd3fb39137f3a6a7a9d2adf7818d` | **PASS**: L1 10 / 10, L2 2 / 2 | L3 2,000 / 2,000 PASS; L4 MSVC ASan 2587341 (= lock source under ASan) + UBSan 3024920, 0 reports, PASS |
| (b) `bundle_b_w6_avx512` | five (ZMM dropped) + NNUE_AVX512 | `e005003b04f5fc03c4e9b021d6b91906fcd5df6097e292895c8b4b4ff715d1da` | **PASS**: L1 10 / 10, L2 2 / 2 | L3 2,000 / 2,000 PASS; L4 ASan + UBSan PASS |
| (c) `bundle_c_t12b_avx512` | T12B_BADCAP + NNUE_AVX512 (none of the six) | `a30dd384607e14a80e12a424e8fff9f44a89716de0a93466ed955854b71e085b` | **PASS**: L1 10 / 10, L2 2 / 2 | L3 2,000 / 2,000 PASS; L4 ASan + UBSan PASS |
| (d) `bundle_d_w6_t12b_avx512` | five (ZMM dropped) + T12B_BADCAP + NNUE_AVX512; started after (a)-(c) had a verdict (17:48:53) | `ad0611a0c59ee07b16b546457e9447fd406249392466c55ca100606ef97291c0` | **PASS**: L1 10 / 10, L2 2 / 2 | L3 2,000 / 2,000 PASS; L4 ASan + UBSan PASS |

Every pack's facts:
- Built twice with pc1 = pc2: same sha256, quick pins OK on both sides.
- speed_pack confirmed `lock + trial_w8.patch = the built source` (md5 ba7f733f).
- Verdict `BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)`.

Pin values: net on 312866 / 862329 / 3024920 / 12389307 / 34048354, net off 375354 / 907205 / 2448617 / 13573040 / 24506465, perft 5 startpos 4865609 and kiwipete 193690690. The bundles equal the lock on every one.

Records:
- packs: `F:\ospd\packs\bundle_*` (SUMMARY.md, signature.txt, `bitexact\bitexact.log`, `src_kit`);
- candidate files: `opus_speed/candidates/bundle_*.md`;
- chain log: `F:\ospd\logs\w8_chain.out`.

**Independent review:** `REVIEW_W8_INDEPENDENT.md` (worker patchrev, read-only, 17:44-17:55) found no BLOCKER and no SHOULD, and two LOW notes:
- W1 (timing only): bundle (c) zero-fills 1 KB of `bad_captures_` per MovePicker, as QA's own T12B source does.
- W2: `sizeof(MovePicker)` grows 3488 -> 4256 B. By estimate the stack margin stays positive. The review suggests a deep-ply stress FEN per T12B bundle for QA.

It also confirms the switch-0 preprocessed text equals the lock for all 8 units, and that the alignment and `__restrict` uses are sound. The file went into commit 146cabf8: `commit_push.sh`'s `git add -A` took it in while the worker was finishing, and it is unchanged since.

**No ABBA and no lock.** Speed is UNPROVEN until QA times the bundles. The skill's lock path also needs L3b warm-table identity, a Threads 2-4 smoke and QA's re-time, and none of these ran here.
