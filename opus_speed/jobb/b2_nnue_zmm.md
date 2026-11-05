STATE: READY FOR TIMING

# b2_nnue_zmm: FORGE_SPD_NNUE_ZMM (AVX-512 output kernel of the lock NNUE, bit-identical)

Worker b2mg (fable), job B part 2, branch opus-speed-20261105. Checks (a)-(c) done 09:13-09:19 PC clock (`date`); notes written 09:21.
Patch: `F:/ospd/wt/opus_speed/patches/b2_nnue_zmm.patch` (96 lines, +88 / -8 counting the context-free lines; files nnue.hpp, nnue.cpp; applies with
`patch -p1` to a fresh lock copy and reproduces `F:/ospd/src/b2_nnue_zmm` exactly: apply test in `F:/ospd/src/b2_applytest_nnue_zmm`).
Source copy: `F:/ospd/src/b2_nnue_zmm` (LF, like the lock). Verify variant (not for stacking): `F:/ospd/src/b2_nnue_zmm_verify`,
`patches/b2_nnue_zmm_verify.patch`. 12k FENs: `fens_12k.txt` holds placement-only lines that the lock rejects
("FEN must contain six fields", tested on the lock plain exe), so the runs use `F:/opus_scratch/r10/parity/fens_12k_v2.txt`
(same 12,000 placements with side / castling / ep / clocks, same read-only folder). No timing was run; no nps number here.

## Design (own words)
The lock's output layer forms sixteen independent partial sums: lane j holds the hidden units h with h mod 16 == j in
increasing h order (src/nnue.cpp design note :164-167), kept as two 256-bit registers `sums[0]` (lanes 0-7) and `sums[1]`
(lanes 8-15), then stores them into `lanes[16]` and adds `b2 + lanes[0] + ... + lanes[15]` in source order. The switch keeps
exactly that association with one 512-bit register: zmm lane j = units h + j for h = 0, 16, 32, ... (the same unit sequence
per lane as lane j of `sums[j / 8]`), the same per-unit expression with separate `_mm512_mul_ps` / `_mm512_add_ps`
(a = min(max(x, 0), 1); term = (a*a)*w2a + (b*b)*w2b; sum += term), one `_mm512_store_ps(lanes, sum)`, and the lock's
scalar reduction loop verbatim. Every lane therefore executes the identical IEEE operation sequence in the identical
order; nothing is reassociated (the build has -ffp-contract=off -fno-fast-math, intrinsics are not contracted; vfmadd
count 0 in every exe). `_mm512_max_ps(x, 0)` and `_mm256_max_ps(x, 0)` have the same NaN / signed-zero rule (second
operand); GCC compiles both as `vcmpgtps` + zeroing masked move, which is the same function of x.
Alignment: `Accumulator::values` and `Weights::w2` are `alignas(32)` in the lock, so a 512-bit aligned load would fault on
half of the search-stack accumulators; under the switch both become `alignas(64)` (the `#else` keeps the lock text), and
the kernel uses `_mm512_load_ps` (a misalignment would crash loudly, it did not). HiddenSize * 4 = 1024 B keeps the
second w2 half aligned. Side effect of the alignment (not measured, UNPROVEN): the already zmm-vectorised accumulator
update / refresh loads and stores stop crossing cache lines (see the codegen section).

## Lines touched (lock numbering)
- include/forge/nnue.hpp :22 (after SigmoidK): the switch default block `#ifndef FORGE_SPD_NNUE_ZMM / #define 0 / #endif`
  (one block, in the header every user includes); :32 `alignas(32)` of `Accumulator::values` -> `alignas(64)` under the switch.
- src/nnue.cpp :18-20 (after the `__AVX2__` include block): under the switch `#error` without `__AVX512F__` + `<immintrin.h>`;
  :49 `Weights::w2` `alignas(64)` under the switch; :171-211 the kernel chain `#if __AVX2__ / #elif SSE / #else` wrapped as
  `#if FORGE_SPD_NNUE_ZMM <zmm kernel> #else <lock chain verbatim> #endif`; :212-215 (reduction, scaling, clamp) untouched.
- Switch 0: `g++ -E -P` of src/nnue.cpp and src/search.cpp (which includes nnue.hpp) is byte-identical to the lock's
  (`F:/ospd/jobb/b2/nnue_zmm/pp/`), and the switch-0 exe equals the lock plain exe except the PE link bytes (check (a)).

## Why node-identical
Same inputs (accumulators, w2, b2), same per-lane operation sequence, same reduction order, no contraction, no fast-math:
the 16 lane values are bit-identical, so `out`, the centipawn float and the clamped int are the same at every evaluation.
Proven dynamically (check (c)) over 2.55 M evaluations, and by node identity (check (b)) over bench d11-d22 and the 8 bench
FENs at d13 with the net on, plus the net-off run (kernel not used: a layout-only regression check).

## Checks
(a) switch-0 build vs lock plain build: `cmp -l` differs only at bytes 137 138 217 218 (PE timestamp / checksum). PASS.
    exes: `F:/ospd/jobb/b2/lock/forge_lock_plain.exe` (sha256 88d6db42...), `F:/ospd/jobb/b2/nnue_zmm/forge_zmm_off.exe` (5a14c7f1...).
    Build logs: `<exe>.build.log` next to each exe (plain lock line, inside the source copy, warnings 0, vfmadd 0).
(b) switch-on exe `F:/ospd/jobb/b2/nnue_zmm/forge_zmm_on.exe` (sha256 7e610373...):
    - net on: `zmm_on_neton.json` vs `F:/ospd/jobb/b2/lock/lock_plain_neton.json` with pins d11=312866 d13=862329 d16=3024920
      d20=12389307 d22=34048354, perft startpos=4865609 kiwipete=193690690: 24/24 rows OK, "NODE IDENTITY: ALL OK"
      (`F:/ospd/jobb/b2/nnue_zmm/zmm_on_neton.compare.log`, run log `zmm_on_neton.run.log`, UCI log `zmm_on_neton.json.uci.log`).
    - net off (`--opt UseNNUE=false`): `zmm_on_netoff.json` vs `lock_plain_netoff.json` with the net-off pins 375354 / 907205 /
      2448617 / 13573040 / 24506465 + perft pins: 24/24 OK, "NODE IDENTITY: ALL OK" (`zmm_on_netoff.compare.log`).
    - lock plain exe itself hits all pins both ways (`F:/ospd/jobb/b2/lock/lock_plain_neton.run.log`, `lock_plain_netoff.run.log`).
(c) change-specific proof, verify exe `F:/ospd/jobb/b2/nnue_zmm/forge_zmm_verify.exe` (sha256 2cdd46b9..., ZMM=1 + VERIFY=1:
    the lock's AVX2 kernel runs next to the zmm kernel at every evaluation, all 16 lanes memcmp'd, abort + lane dump on a
    mismatch, counter printed at exit; the result is taken from the lock kernel so the exe must also hit the pins):
    - `bench 16`: nodes 3024920 (= pin), "FORGE_SPD_NNUE_ZMM_VERIFY: 1803616 evaluations compared, 0 mismatches"
      (`zmm_verify_bench16.log`, `.stderr`).
    - 12k FENs (`fens_12k_v2.txt`, `go depth 2`, one process, driver `F:/ospd/jobb/b2/tools/uci_fens.py`): 12000/12000 FENs
      answered, "744964 evaluations compared, 0 mismatches", engine exit 0 (`zmm_verify_12k_d2.run.log`, `.tsv`, `.tsv.stderr`).
    - objdump: vfmadd / vfnmadd / vfmsub / vfnmsub count 0 in the off, on and verify exes (build logs).
(d) 12k exe identity (switch-on exe vs lock plain exe, same driver, depth 2): see the appendix line at the end (added when run).

## Codegen evidence (`F:/ospd/jobb/b2/nnue_zmm/objdump/`, plain -O3 znver5 builds, not LTO+PGO)
- `evaluate` lock plain (`lock_plain_evaluate.dis`, 91 lines): loop over 16 iterations, each 2 x {2 vmovups ymm, 2 vcmpgtps +
  zeroing vmovaps (the max with 0), 2 vminps ymm, 4 vmulps ymm (2 with w2 memory operands), 2 vaddps ymm}; whole exe: 4 vaddps
  ymm, 8 vmulps ymm, 4 vminps ymm, 0 vmaxps (GCC's cmp + masked-zero form), 0 vfmadd.
- `evaluate` switch on (`zmm_on_evaluate.dis`, 86 lines): 16 iterations of {2 vmovups zmm, 2 vcmpgtps + zeroing vmovaps, 2 vminps
  zmm, 4 vmulps zmm (2 with memory operands), 2 vaddps zmm} = half the vector uops per iteration count of the lock's unrolled
  pair; whole exe: 0 ymm vaddps / vmulps / vminps left, vaddps zmm 64 -> 66, vmulps zmm 2 -> 6, vminps zmm 0 -> 2, vmovaps zmm
  0 -> 3, vfmadd 0. The reduction tail is the same ordered vaddss chain (lanes 0..15) in both.
- `update` and `refresh` (`*_update.dis`, `*_refresh.dis`): byte-identical between the two exes apart from addresses (diff
  empty). The lock plain `update` already holds 128 vmovups zmm, 48 vaddps zmm, 64 vsubps zmm (the three paths fully unrolled
  to 16 zmm ops each, no scalar remainder, no calls in the loops); `refresh` 32 vmovups zmm + 16 vaddps zmm. This confirms the
  deep-research reading (auto-vectorised to zmm). Worth a switch? No: there is no vector work left to add; the only lever
  is alignment: the loads are `vmovups` on 32-byte-aligned accumulators (half of the 64-byte accesses split a cache line in
  the lock) and on 16-byte-aligned w1 columns (`make_unique<float[]>`; R13 FORGE_ALIGN_WEIGHTS measured that neutral within
  the A/A noise, skill forge-speed-stack). This switch's `alignas(64)` on `Accumulator::values` already removes the
  accumulator splits for free; a separate switch for w1 alignment is not worth a new ABBA after R13's result. UNPROVEN.

## Risks
- The gain is bounded by the kernel's share (~0.3-1 % by the T05 list's static count, UNPROVEN); the ABBA decides.
- `alignas(64)` on Accumulator grows SearchStack by 32 B per ply (136 entries); on Weights nothing visible. Not a node matter.
- The switch needs an AVX-512F target: `#error` otherwise (the lock kit builds -march=znver5; a generic / Zen 2 side cannot
  enable it, so a wrong machine fails at compile time, never at run time).
- Not run here: the kit LTO+PGO build (coordinator), T12-03 level 3 / 5 drivers, CI sanitizer row, valgrind (no Linux here).
