# NnueInt8Vnni - STATUS

**Last update:** step 2d, 2026-11-06 ~17:00 PC clock.

## Done

### 2a - QUANT_SCHEME.md + `tools/int8_convert.py` (commit f6d2da2c)
- The converter output is `gen/nnue_int8_weights.inc`, md5 25982cc2.

### 2b - scalar int8 path + eval-diff proof (commit 9dfd9b30)
- **Source change.** `int8_vnni_after_w6.patch` (md5 d8c37703) is the diff from trial_w6 (all switches at their source
  default 0). It touches four files: include/forge/nnue.hpp, src/nnue.cpp, src/nnue_int8_weights.inc (new) and
  src/uci.cpp.
  - Every new line sits inside `#if FORGE_NNUE_INT8_VNNI`.
  - Apply-proof: `patch -p1 -F0` on a fresh `F:\ospd\src\trial_w6` copy gives the same tree.
- **Preprocessor identity at macro 0.** `tools/pp_identity.sh` ran with the lock flags and the six lock switches. All 8
  units are the same as the parent (IDENTICAL).
- **Macro 1** compiles with -Wall -Wextra and gives no warnings.
- **Harness.** `tools/int8_evaldiff.cpp`, built with `tools/build_harness.sh` (a plain g++ -O3 build of the gate tree).
  Output: `logs/evaldiff_2b.txt`, seed 20261106.
  - Inputs: startpos + the first 2000 FENs of fens_12k_v2.txt (2001 roots, 0 bad) + random legal walks of 16 plies each,
    33,978 positions in total.
  - Network term, ON vs the float lock path, roots only: |diff| max **20 cp**, mean **3.01 cp**, mean signed +0.95 cp.
    Counts: >= 5 cp 449, >= 10 cp 52, >= 20 cp 1, >= 50 cp 0. Sign flips of the total static eval: 13 of 2001.
  - Roots + walks: |diff| max **27 cp**, mean **3.46 cp**, mean signed +1.27 cp. Counts: >= 10 cp 1444, >= 20 cp 33,
    >= 50 cp 0. Sign flips of the total: 112 of 33,978.
  - **Incremental == refresh:** 0 mismatches over 31,977 walk positions.
  - **Largest |A| seen: 6293.** The int16 limit is 32767. The loose proof bound comes in 2c.
- **Mate probe.** `tools/mate_probe.ps1`, 22 FENs, 3M nodes, plain gate exe d44b6a0e, NnueInt8Vnni 0 vs 1.
  - Mate found: OFF 19, ON 21.
  - LOST (or sign flip) by ON: **0**. LONGER by ON: 4 (fens 1, 8, 10, 13). GAINED: 2. SHORTER: 1.
  - 30M re-check of the 4 LONGER positions: all 4 now give the same mate and the same bestmove OFF and ON (LOST 0,
    LONGER 0; `logs/mate_probe_2b_30m_SUMMARY.txt`).
- **Note:** the hand-crafted part of the "total" is the public `Evaluator::evaluate`. `evaluate_runtime` is private to
  Worker. The same value enters both totals.

### 2c - overflow bounds (commit a472d836)
- `tools/int8_bounds.py` and BOUNDS.md: ALL BOUNDS HOLD.
  - FT \|A\| <= 21,236 < 32,767.
  - Activation <= 254; c*c + 128 <= 65,153 (fits u16).
  - L1 \|sum\| <= 1,608,582 < 2^24.
  - vpdpbusd lane <= 1,032,256.
  - An AVX2 pmaddubsw pair can saturate (64,516), so there is no AVX2 fallback.

- 2b identity: LTO+PGO lp_v1 of `int8_id` (the 2b source): pc1 = pc2 = 4181a589 = trial_w6, byte for byte.

### 2d - AVX-512 VNNI kernel (this commit)
- **The kernel.** `int8_l1_sum` works on 64 hidden units per step:
  - clip 0..255, then `mullo_epi16` +128 `>> 8` in 16-bit lanes;
  - `packus_epi16` to 64 u8, with the weights pre-permuted (`w2p`) to match the byte order;
  - one `vpdpbusd` per step, into two accumulators;
  - a final `reduce_add`.
- **ISA guard.** `#error` unless AVX-512 F + BW + VNNI are present.
- **Verify macro.** `FORGE_NNUE_INT8_VERIFY` is a test-only macro, default 0.
- **Patch.** `int8_vnni_after_w6.patch` is now md5 9a2ad0b4. Apply-proof: identical tree. pp_identity at macro 0:
  IDENTICAL in all 8 units again.
- **Kernel == scalar.** Run on the full 12k set (12,001 roots) + 16-ply walks = 203,724 positions
  (`logs/evaldiff_2d_12k.txt`):
  - kernel != scalar: **0**;
  - incremental != refresh: **0** (191,723 walk positions);
  - net |diff| vs float: max 33 cp, mean 3.52 cp, mean signed +1.31 cp; >= 20 cp: 302; >= 50 cp: 0;
  - sign flips of the total: 635 (0.31 %);
  - max |A| = 6509.
- **Verify build.** Bench with the scalar check on every eval (`logs/verify_2d_bench.txt`): ON d13 760,289 and d16
  3,282,449, no abort; OFF d13 862,329 = lock pin.

## In progress
- 2e LTO+PGO builds: `int8v2_id` (must give 4181a589 for pc1 and pc2) and `int8v2_gate` (pc1 = pc2), both lp_v1 -Twice.

## Exact next step
2e: once the builds finish:
1. Check the gate exe: pins OFF (net on + net off), both perfts.
2. Record ON bench d11 / d13 / d16 / d20 / d22.
3. Write BENCH.md and pack the exe to `D:\opus_5h\int8_vnni\pack\`.
4. Hand the pack to Code Review.

## Resume commands
```
cd /f/ospd/wt && git checkout opus-nnue-int8-vnni-20261106
# trees: D:\opus_5h\int8_vnni\src\{w6 (parent copy), int8 = int8v2 (2d source, macro 0), int8v2_id, int8v2_gate}; int8_id = 2b
bash opus_nnue_int8_vnni/tools/pp_identity.sh /f/ospd/src/trial_w6 /d/opus_5h/int8_vnni/src/int8
bash opus_nnue_int8_vnni/tools/build_harness.sh /d/opus_5h/int8_vnni/src/int8_gate <new dir>
<new dir>/int8_evaldiff.exe F:/ospd/wt/opus_speed/data/fens_12k_v2.txt 2000 16 20261106
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'F:\ospd\wt\opus_speed\tools\build_variants.ps1' \
  -SrcDir 'D:\opus_5h\int8_vnni\src\int8_id' -Tag int8_id -Variant lp_v1 -Twice -Work 'D:\opus_5h\int8_vnni\builds'
```

## Unproven / not claimed
- No strength or speed claim.
- The eval diffs above are measured on the 2001-root slice and its walks, not on the full 12k set.
- The kernel was proven against the scalar reference on 203,724 positions plus every eval of bench d13/d16. That is
  not a proof for all inputs. The integer argument for all inputs is in BOUNDS.md.

## Disk
D: had 47.8 GiB free at the start, below the 50 GB floor of earlier jobs. This brief names D: for builds. The own
footprint is about 0.1 GB so far.
