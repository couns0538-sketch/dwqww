# Independent Bullet → Forge R10 contract review, 2026-10-30

Read-only evidence: `/tmp/astra-r10-loader-recon.cpp`, exact Forge 7f79c349; official MIT Bullet clone `/tmp/astra-bullet-upstream` commit da426a49b2a4b79a55a87031cd51c89bdf1ff030. No other engine implementation read/copied.

## Critical contract

* Bullet `optimiser_state/weights.bin` records are ASCII ID + LF + native `usize` byte count in little endian + count float32 little-endian values. It contains no tensor shape, net architecture, feature definition or scale. Pin 64-bit checkpoint length width explicitly; reject duplicate/missing/unknown IDs, truncated values, nonfinite floats and incompatible tensor sizes. Do not infer architecture from a filename.
* Bullet stores tensors column-major `[output,input]`. FT output×feature column-major is already Forge `[feature,output]`; dense matrices must be transposed to output-major file order and explicitly separated into32 stack slices. Raw `.bin` has even less metadata; prefer named weights file plus reviewed graph/manifest.
* Bullet quantization promotes stored float32 to float64 then multiplies by integer scale. Default truncates toward zero. `.round()` means Rust float round, ties away from zero. NumPy rint uses ties-even and is wrong for that mode. Reject rather than silently clip integer overflow.
* Forge version 0x6A448AFA; feature hash 0xAB005CEF. L1 >=64, divisible64, <=4096. L2/L3 even,2..64. FT hash `feature_hash ^ (2*L1)`; net hash `fc_hash ^ feature_hash ^(2*L1)`. All hash arithmetic must wrap modulo2^32. Each stack repeats `fc_hash` before bias+weights.
* File order: u32 version/net-hash/description-byte-length; description raw bytes; u32 FT hash; L1 int16 bias;67584×L1 int8 FT weights;32 stacks each u32 FC hash, L2 int32 bias, L2×pad32(L1) int8 weights, L3 int32 bias,L3×pad32(2L2) int8 weights,1int32 bias,pad32(2L2+2L3) int8 weights. All little-endian, padding zero, no footer.
* FT safety must satisfy per-column `abs(bias)+32*max(abs(weight))<=32767`. Also bound dense dot+bias within signed32. R10 loader does not check dense bounds; `st.b3+dot` is added as int32 before assignment to int64, so unsafe b3 must be rejected by exporter.

## Reference arithmetic

Coordinates a1=0. For perspective p, orient square with xor56 if black, xor7 if original own king file<4. Let oriented own king `(r,f)` with f4..7. Kingbucket=`31 - 4*r - (f-4)`. Material state=2 if opposing queen exists,else1 if anyrook/queen exists,else0. Fullbucket=32*state+kingbucket. Pieceplane=min(2*(type(P,N,B,R,Q,K)-1)+opposingcolor,10), so both kings share plane10. Feature=704*bucket+64*plane+oriented square.

Stack=`((piece_count-1)//4)*4 +2*STM_hasQueen+other_hasQueen`; require legal <=32piece positions to avoid out-of-range.

FT each perspective is bias+sum active rows. Pairwise: clamp first and second halves to[0,255], product>>9. Concatenate STM half then opponent half. First dense sum s1 uses int32; square=min127,(s1*s1+20)>>21;linear=clamp(s1>>7,0,127). Second dense sees [square1,linear1], zero padded. Its square=min127,(s2*s2+5)>>19;linear=clamp(s2>>6,0,127). Final sees[square1,linear1,square2,linear2],zero padded. Total=b3+dot+s1[L2-2]-s1[L2-1]. Raw=truncTowardZero(total*19200/32768);cp=truncTowardZero(raw/16). Python `//` is wrong for negative final divisions. Use int64 before squares and all reference sums.

## Test priorities

1. Deliberately asymmetric per-stack/per-input weights identify column-major transposition and stack slicing mistakes; all-zero/simple constant nets cannot prove layout.
2. White/black perspective mirrors, both king mirror sides, queen-presence states, all material stacks, promotion-rich boards, negative output.
3. Quantization boundaries±0.5,±1.5, integer endpoints, NaN/Inf, and f32 value precision vs original JSON decimal.
4. Corrupt a demonstrably active final-layer weight in a nonzero fixture and confirm native/reference mismatch. Merely changing an unused weight can produce unchanged12k outputs. Checksum detection is useful but not arithmetic parity proof.
5. Run exact Forge public `halfka_tool eval` on exported bytes; output raw and cp; tool separately checks SIMD==scalar. Treat shell exit0 as inadequate without expected12000 rows and0mismatches in independently compared raw output.
6. `.nnue` has no payload checksum: same-size valid weight corruption usually loads; expected failure belongs in parity/integrity harness, not Forge loader.
7. Fresh export manifest should include checkpoint SHA, architecture/quantization contract SHA, exporter SHA, output SHA and build/parity identities. A hand-built compatible checkpoint is a synthetic serialization fixture, not Bullet training evidence.

## Platform limitation

Bullet no-feature ExecutionContext is MockGpu, explicitly for typechecking, and its kernel_launch/BLAS return errors. It cannot train on CPU. CUDA/ROCm/Metal training requires corresponding hardware/runtime. No CPU-trained substitute may be labeled Bullet-trained.
