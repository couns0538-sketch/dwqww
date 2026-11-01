#!/usr/bin/env python3
"""port_sparse.py - R13 P2 step 2: build switch FORGE_SPARSE_L1 (default 0) in src/nnue_halfka.cpp (stack tree).

The existing block kernels (AVX-512 VNNI and AVX2) become block_affine_dense (unchanged bodies). block_affine is:
- FORGE_SPARSE_L1 = 0: block_affine_dense (inlined; same code as before);
- FORGE_SPARSE_L1 = 1: find-nnz. Phase 1 writes the indices of the non-zero 4-byte input blocks of the clipped
  activations into a list (ascending, same masks as the dense kernel); phase 2 runs the int8 dot products only over
  that list with independent accumulator chains (4 when NQ = 1, else 2), summed at the end. dpbusd / madd sums are
  int32 without saturation (maddubs pairs stay inside int16 as in the dense kernel: x <= 127, |w| <= 128), so the
  order of the additions does not change any sum: outputs are bit-identical to the dense kernel.
Own code (the find-nnz idea is public; no GPL code used). Every anchor must match exactly once.
usage: python -I -B port_sparse.py <stack scratch repo>
"""
import sys

p = f'{sys.argv[1]}/src/nnue_halfka.cpp'
s = open(p, 'rb').read().decode()


def rep(old, new):
    global s
    n = s.count(old)
    assert n == 1, f'anchor found {n}x: {old[:80]!r}'
    s = s.replace(old, new)


rep('#if defined(__AVX512VNNI__) && defined(__AVX512BW__)\n// Block kernel: s[k] = sum_i w[k][i] * x[i] for NQ x 16 outputs.',
    '// FORGE_SPARSE_L1 (R13 P2 step 2, build switch, default 0): find-nnz block kernel, see block_affine below.\n'
    '#ifndef FORGE_SPARSE_L1\n#define FORGE_SPARSE_L1 0\n#endif\n\n'
    '#if defined(__AVX512VNNI__) && defined(__AVX512BW__)\n// Block kernel: s[k] = sum_i w[k][i] * x[i] for NQ x 16 outputs.')
rep('template <int NQ>\nvoid block_affine(const std::uint8_t* x, int in, const std::int8_t* wb, std::int32_t* s) {\n    __m512i acc[NQ];',
    'template <int NQ>\nvoid block_affine_dense(const std::uint8_t* x, int in, const std::int8_t* wb, std::int32_t* s) {\n    __m512i acc[NQ];')
rep('template <int NQ>\nvoid block_affine(const std::uint8_t* x, int in, const std::int8_t* wb, std::int32_t* s) {\n    __m256i acc[NQ];',
    'template <int NQ>\nvoid block_affine_dense(const std::uint8_t* x, int in, const std::int8_t* wb, std::int32_t* s) {\n    __m256i acc[NQ];')
sparse = r'''
#if defined(__AVX512VNNI__) && defined(__AVX512BW__)
constexpr int SparseGroup = 16;  // int32 outputs per zmm
#elif defined(__AVX2__)
constexpr int SparseGroup = 8;   // int32 outputs per ymm
#endif
#if (defined(__AVX512VNNI__) && defined(__AVX512BW__)) || defined(__AVX2__)
#if FORGE_SPARSE_L1
// find-nnz: phase 1 lists the non-zero 4-byte input blocks (ascending), phase 2 multiplies only those, with Chains
// independent accumulator sets so consecutive multiply-adds do not wait on each other. Integer sums: bit-identical.
constexpr int MaxNnzBlocks = 2048;  // inputs per layer <= 8192 (K32H3 nets: l1 <= 1536)
template <int NQ>
void block_affine(const std::uint8_t* x, int in, const std::int8_t* wb, std::int32_t* s) {
    if (in > 4 * MaxNnzBlocks) [[unlikely]] return block_affine_dense<NQ>(x, in, wb, s);
    std::uint16_t nnz[MaxNnzBlocks];
    int count = 0;
#if defined(__AVX512VNNI__) && defined(__AVX512BW__)
    for (int c = 0; c < in; c += 64) {
        unsigned mask = in - c >= 64 ? static_cast<unsigned>(_mm512_test_epi32_mask(_mm512_loadu_si512(x + c), _mm512_loadu_si512(x + c)))
                                     : static_cast<unsigned>(_mm256_test_epi32_mask(_mm256_loadu_si256(reinterpret_cast<const __m256i*>(x + c)),
                                                                                    _mm256_loadu_si256(reinterpret_cast<const __m256i*>(x + c))));
        while (mask != 0) {
            nnz[count++] = static_cast<std::uint16_t>(c / 4 + std::countr_zero(mask));
            mask &= mask - 1;
        }
    }
    using Vec = __m512i;
    auto zero = [] { return _mm512_setzero_si512(); };
    auto madd = [](Vec acc, Vec xb, const std::int8_t* w) { return _mm512_dpbusd_epi32(acc, xb, _mm512_loadu_si512(w)); };
    auto bcast = [](std::int32_t four) { return _mm512_set1_epi32(four); };
    auto add = [](Vec a, Vec b) { return _mm512_add_epi32(a, b); };
    auto store = [](std::int32_t* dst, Vec v) { _mm512_storeu_si512(dst, v); };
#else
    const __m256i vzero = _mm256_setzero_si256();
    for (int c = 0; c < in; c += 32) {
        const __m256i v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(x + c));
        unsigned mask = static_cast<unsigned>(_mm256_movemask_ps(_mm256_castsi256_ps(_mm256_cmpgt_epi32(v, vzero))));
        while (mask != 0) {
            nnz[count++] = static_cast<std::uint16_t>(c / 4 + std::countr_zero(mask));
            mask &= mask - 1;
        }
    }
    using Vec = __m256i;
    auto zero = [] { return _mm256_setzero_si256(); };
    auto madd = [](Vec acc, Vec xb, const std::int8_t* w) {
        return _mm256_add_epi32(acc, _mm256_madd_epi16(_mm256_maddubs_epi16(xb, _mm256_loadu_si256(reinterpret_cast<const __m256i*>(w))),
                                                       _mm256_set1_epi16(1)));
    };
    auto bcast = [](std::int32_t four) { return _mm256_set1_epi32(four); };
    auto add = [](Vec a, Vec b) { return _mm256_add_epi32(a, b); };
    auto store = [](std::int32_t* dst, Vec v) { _mm256_storeu_si256(reinterpret_cast<__m256i*>(dst), v); };
#endif
    constexpr int Bytes = SparseGroup * 4;  // weight bytes per output group and block
    constexpr int Chains = NQ == 1 ? 4 : 2;
    Vec acc[Chains][NQ];
    for (int h = 0; h < Chains; ++h)
        for (int q = 0; q < NQ; ++q) acc[h][q] = zero();
    auto step = [&](int h, int b) {
        std::int32_t four = 0;
        std::memcpy(&four, x + 4 * b, 4);
        const Vec xb = bcast(four);
        const std::int8_t* w = wb + static_cast<std::size_t>(b) * NQ * Bytes;
        for (int q = 0; q < NQ; ++q) acc[h][q] = madd(acc[h][q], xb, w + q * Bytes);
    };
    int k = 0;
    for (; k + Chains <= count; k += Chains)
        for (int h = 0; h < Chains; ++h) step(h, nnz[k + h]);
    for (; k < count; ++k) step(0, nnz[k]);
    for (int q = 0; q < NQ; ++q) {
        Vec sum = acc[0][q];
        for (int h = 1; h < Chains; ++h) sum = add(sum, acc[h][q]);
        store(s + q * SparseGroup, sum);
    }
}
#else
template <int NQ>
inline void block_affine(const std::uint8_t* x, int in, const std::int8_t* wb, std::int32_t* s) {
    block_affine_dense<NQ>(x, in, wb, s);
}
#endif
#endif
'''
anchor = '\n// s[k] = b[k] + sum_i w[k][i] * x[i] for k < out. SIMD: the block kernel on the regrouped weights'
rep(anchor, sparse + anchor)
assert '\r' not in s
open(p, 'wb').write(s.encode())
print('port_sparse: all anchors applied')
