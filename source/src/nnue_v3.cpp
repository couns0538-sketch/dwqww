// JOB E (2026-11-11): ported unchanged from branch fable-fb2-j1 (FB1 NNUE v3); compiled only with FORGE_NNUE_V3=1.
#include "forge/nnue.hpp"
#if FORGE_NNUE_V3
#include "forge/nnue_v3.hpp"
#if FORGE65
#include "forge/forge65.hpp"
#endif

#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <new>
#include <sstream>

#if defined(__AVX2__) || defined(__AVX512BW__)
#include <immintrin.h>
#endif
#if defined(__AVX2__)
#define FORGE_NNUE_V3_AVX2 1
#else
#define FORGE_NNUE_V3_AVX2 0
#endif
#if defined(__AVX512F__) && defined(__AVX512BW__)
#define FORGE_NNUE_V3_AVX512 1
#else
#define FORGE_NNUE_V3_AVX512 0
#endif

namespace forge::nnue::v3 {

bool requested = false;

namespace {

std::unique_ptr<Net> g_net;
std::string g_problem;
std::uint64_t g_generation = 0;

std::uint32_t read_u32(const std::uint8_t* p) {
    return static_cast<std::uint32_t>(p[0]) | (static_cast<std::uint32_t>(p[1]) << 8U) |
           (static_cast<std::uint32_t>(p[2]) << 16U) | (static_cast<std::uint32_t>(p[3]) << 24U);
}

std::int32_t read_i32(const std::uint8_t* p) { return static_cast<std::int32_t>(read_u32(p)); }

std::int16_t read_i16(const std::uint8_t* p) {
    return static_cast<std::int16_t>(static_cast<std::uint16_t>(p[0]) | static_cast<std::uint16_t>(static_cast<std::uint16_t>(p[1]) << 8U));
}

std::uint64_t read_u64(const std::uint8_t* p) {
    return static_cast<std::uint64_t>(read_u32(p)) | (static_cast<std::uint64_t>(read_u32(p + 4)) << 32U);
}

bool fail(std::string* error, const std::string& text) {
    if (error != nullptr) *error = text;
    return false;
}

std::size_t cache_index(const Net& net, Color perspective, KingKey key) {
    return (static_cast<std::size_t>(perspective) * static_cast<std::size_t>(net.king_buckets) + key.bucket) * 2 +
           (key.flip != 0 ? 1 : 0);
}

inline void add_column_scalar(std::int16_t* acc, const std::int16_t* col, int hidden) {
    for (int h = 0; h < hidden; ++h) acc[h] = static_cast<std::int16_t>(acc[h] + col[h]);
}

inline void sub_column_scalar(std::int16_t* acc, const std::int16_t* col, int hidden) {
    for (int h = 0; h < hidden; ++h) acc[h] = static_cast<std::int16_t>(acc[h] - col[h]);
}

#if FORGE_NNUE_V3_AVX2
inline void add_column_avx2(std::int16_t* acc, const std::int16_t* col, int hidden) {
    for (int h = 0; h < hidden; h += 16) {
        _mm256_store_si256(reinterpret_cast<__m256i*>(acc + h),
                           _mm256_add_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(acc + h)),
                                            _mm256_load_si256(reinterpret_cast<const __m256i*>(col + h))));
    }
}

inline void sub_column_avx2(std::int16_t* acc, const std::int16_t* col, int hidden) {
    for (int h = 0; h < hidden; h += 16) {
        _mm256_store_si256(reinterpret_cast<__m256i*>(acc + h),
                           _mm256_sub_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(acc + h)),
                                            _mm256_load_si256(reinterpret_cast<const __m256i*>(col + h))));
    }
}
#endif

#if FORGE_NNUE_V3_AVX512
inline void add_column_avx512(std::int16_t* acc, const std::int16_t* col, int hidden) {
    for (int h = 0; h < hidden; h += 32) {
        _mm512_store_si512(reinterpret_cast<__m512i*>(acc + h),
                           _mm512_add_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(acc + h)),
                                            _mm512_load_si512(reinterpret_cast<const __m512i*>(col + h))));
    }
}

inline void sub_column_avx512(std::int16_t* acc, const std::int16_t* col, int hidden) {
    for (int h = 0; h < hidden; h += 32) {
        _mm512_store_si512(reinterpret_cast<__m512i*>(acc + h),
                           _mm512_sub_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(acc + h)),
                                            _mm512_load_si512(reinterpret_cast<const __m512i*>(col + h))));
    }
}
#endif

// The best compiled kernel is the one the search uses.
#if FORGE_NNUE_V3_AVX512
inline void add_column(std::int16_t* acc, const std::int16_t* col, int hidden) { add_column_avx512(acc, col, hidden); }
inline void sub_column(std::int16_t* acc, const std::int16_t* col, int hidden) { sub_column_avx512(acc, col, hidden); }
#elif FORGE_NNUE_V3_AVX2
inline void add_column(std::int16_t* acc, const std::int16_t* col, int hidden) { add_column_avx2(acc, col, hidden); }
inline void sub_column(std::int16_t* acc, const std::int16_t* col, int hidden) { sub_column_avx2(acc, col, hidden); }
#else
inline void add_column(std::int16_t* acc, const std::int16_t* col, int hidden) { add_column_scalar(acc, col, hidden); }
inline void sub_column(std::int16_t* acc, const std::int16_t* col, int hidden) { sub_column_scalar(acc, col, hidden); }
#endif

// ---- output kernels (sum of SCReLU terms; see the header) ----
#if FORGE_NNUE_V3_AVX2
inline std::int64_t hsum_epi32_pair_avx2(__m256i sum0, __m256i sum1) {
    const __m256i total32 = _mm256_add_epi32(sum0, sum1);
    const __m128i lo128 = _mm256_castsi256_si128(total32);
    const __m128i hi128 = _mm256_extracti128_si256(total32, 1);
    const __m256i sum64 = _mm256_add_epi64(_mm256_cvtepi32_epi64(lo128), _mm256_cvtepi32_epi64(hi128));
    const __m128i s128 = _mm_add_epi64(_mm256_castsi256_si128(sum64), _mm256_extracti128_si256(sum64, 1));
    const __m128i hi64 = _mm_unpackhi_epi64(s128, s128);
    return _mm_cvtsi128_si64(_mm_add_epi64(s128, hi64));
}

std::int64_t output_sum_avx2(const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket) {
    const int hidden = net.hidden;
    const std::int16_t* w2_us = net.w2.data() + static_cast<std::size_t>(bucket) * 2 * static_cast<std::size_t>(hidden);
    const std::int16_t* w2_them = w2_us + hidden;
    const __m256i zero = _mm256_setzero_si256();
    const __m256i qa = _mm256_set1_epi16(static_cast<short>(QA));
    __m256i sum0 = zero;
    __m256i sum1 = zero;
    for (int h = 0; h < hidden; h += 16) {
        const __m256i a = _mm256_min_epi16(_mm256_max_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(ours + h)), zero), qa);
        const __m256i b = _mm256_min_epi16(_mm256_max_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(theirs + h)), zero), qa);
        const __m256i wa = _mm256_load_si256(reinterpret_cast<const __m256i*>(w2_us + h));
        const __m256i wb = _mm256_load_si256(reinterpret_cast<const __m256i*>(w2_them + h));
        sum0 = _mm256_add_epi32(sum0, _mm256_madd_epi16(_mm256_mullo_epi16(a, wa), a));
        sum1 = _mm256_add_epi32(sum1, _mm256_madd_epi16(_mm256_mullo_epi16(b, wb), b));
    }
    return hsum_epi32_pair_avx2(sum0, sum1);
}
#endif

#if FORGE_NNUE_V3_AVX512
inline std::int64_t hsum_epi32_pair_avx512(__m512i sum0, __m512i sum1) {
    const __m512i total32 = _mm512_add_epi32(sum0, sum1);
    const __m256i lo256 = _mm512_castsi512_si256(total32);
    const __m256i hi256 = _mm512_extracti32x8_epi32(total32, 1);
    const __m512i sum64 = _mm512_add_epi64(_mm512_cvtepi32_epi64(lo256), _mm512_cvtepi32_epi64(hi256));
    return _mm512_reduce_add_epi64(sum64);
}

std::int64_t output_sum_avx512(const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket) {
    const int hidden = net.hidden;
    const std::int16_t* w2_us = net.w2.data() + static_cast<std::size_t>(bucket) * 2 * static_cast<std::size_t>(hidden);
    const std::int16_t* w2_them = w2_us + hidden;
    const __m512i zero = _mm512_setzero_si512();
    const __m512i qa = _mm512_set1_epi16(static_cast<short>(QA));
    __m512i sum0 = zero;
    __m512i sum1 = zero;
    __m512i sum2 = zero;
    __m512i sum3 = zero;
    int h = 0;
    for (; h + 64 <= hidden; h += 64) {
        const __m512i a0 = _mm512_min_epi16(_mm512_max_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(ours + h)), zero), qa);
        const __m512i b0 = _mm512_min_epi16(_mm512_max_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(theirs + h)), zero), qa);
        const __m512i wa0 = _mm512_load_si512(reinterpret_cast<const __m512i*>(w2_us + h));
        const __m512i wb0 = _mm512_load_si512(reinterpret_cast<const __m512i*>(w2_them + h));
        sum0 = _mm512_add_epi32(sum0, _mm512_madd_epi16(_mm512_mullo_epi16(a0, wa0), a0));
        sum1 = _mm512_add_epi32(sum1, _mm512_madd_epi16(_mm512_mullo_epi16(b0, wb0), b0));

        const __m512i a1 = _mm512_min_epi16(_mm512_max_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(ours + h + 32)), zero), qa);
        const __m512i b1 = _mm512_min_epi16(_mm512_max_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(theirs + h + 32)), zero), qa);
        const __m512i wa1 = _mm512_load_si512(reinterpret_cast<const __m512i*>(w2_us + h + 32));
        const __m512i wb1 = _mm512_load_si512(reinterpret_cast<const __m512i*>(w2_them + h + 32));
        sum2 = _mm512_add_epi32(sum2, _mm512_madd_epi16(_mm512_mullo_epi16(a1, wa1), a1));
        sum3 = _mm512_add_epi32(sum3, _mm512_madd_epi16(_mm512_mullo_epi16(b1, wb1), b1));
    }
    for (; h < hidden; h += 32) {
        const __m512i a = _mm512_min_epi16(_mm512_max_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(ours + h)), zero), qa);
        const __m512i b = _mm512_min_epi16(_mm512_max_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(theirs + h)), zero), qa);
        const __m512i wa = _mm512_load_si512(reinterpret_cast<const __m512i*>(w2_us + h));
        const __m512i wb = _mm512_load_si512(reinterpret_cast<const __m512i*>(w2_them + h));
        sum0 = _mm512_add_epi32(sum0, _mm512_madd_epi16(_mm512_mullo_epi16(a, wa), a));
        sum1 = _mm512_add_epi32(sum1, _mm512_madd_epi16(_mm512_mullo_epi16(b, wb), b));
    }
    return hsum_epi32_pair_avx512(_mm512_add_epi32(sum0, sum2), _mm512_add_epi32(sum1, sum3));
}
#endif

// ---- change kernels: destination = source +/- up to four columns in one pass ----
struct Changes {
    const std::int16_t* columns[4] = {nullptr, nullptr, nullptr, nullptr};
    bool adds[4] = {false, false, false, false};
    int count = 0;
};

Changes collect_changes(const Net& net, KingKey key, Color perspective, const DirtyPieces& dirty) {
    Changes c;
    c.count = dirty.count;
    for (int i = 0; i < dirty.count; ++i) {
        const PieceChange& change = dirty.changes[static_cast<std::size_t>(i)];
        c.columns[i] = column(net, feature_index(key, perspective, change.piece, change.square));
        c.adds[i] = change.add;
    }
    return c;
}

void apply_changes_scalar(const std::int16_t* source, std::int16_t* destination, const Changes& c, int hidden) {
    const int count = c.count;
    const std::int16_t* col0 = c.columns[0];
    const std::int16_t* col1 = c.columns[1];
    const std::int16_t* col2 = c.columns[2];
    const std::int16_t* col3 = c.columns[3];
    const int sign0 = c.adds[0] ? 1 : -1;
    const int sign1 = c.adds[1] ? 1 : -1;
    const int sign2 = c.adds[2] ? 1 : -1;
    const int sign3 = c.adds[3] ? 1 : -1;
    for (int h = 0; h < hidden; ++h) {
        int v = source[h];
        if (count > 0) v += sign0 * col0[h];
        if (count > 1) v += sign1 * col1[h];
        if (count > 2) v += sign2 * col2[h];
        if (count > 3) v += sign3 * col3[h];
        destination[h] = static_cast<std::int16_t>(v);
    }
}

void apply_changes_pair_scalar(const std::int16_t* source0, std::int16_t* destination0, const Changes& c0,
                               const std::int16_t* source1, std::int16_t* destination1, const Changes& c1, int hidden) {
    for (int h = 0; h < hidden; ++h) {
        int v0 = source0[h];
        for (int i = 0; i < c0.count; ++i) v0 += c0.adds[i] ? c0.columns[i][h] : -c0.columns[i][h];
        destination0[h] = static_cast<std::int16_t>(v0);
        int v1 = source1[h];
        for (int i = 0; i < c1.count; ++i) v1 += c1.adds[i] ? c1.columns[i][h] : -c1.columns[i][h];
        destination1[h] = static_cast<std::int16_t>(v1);
    }
}

#if FORGE_NNUE_V3_AVX2
void apply_changes_avx2(const std::int16_t* source, std::int16_t* destination, const Changes& c, int hidden) {
    const int count = c.count;
    const std::int16_t* col0 = c.columns[0];
    const std::int16_t* col1 = c.columns[1];
    const std::int16_t* col2 = c.columns[2];
    const std::int16_t* col3 = c.columns[3];
    const bool add0 = c.adds[0];
    const bool add1 = c.adds[1];
    const bool add2 = c.adds[2];
    const bool add3 = c.adds[3];
    for (int h = 0; h < hidden; h += 16) {
        __m256i v = _mm256_load_si256(reinterpret_cast<const __m256i*>(source + h));
        if (count > 0) {
            const __m256i col = _mm256_load_si256(reinterpret_cast<const __m256i*>(col0 + h));
            v = add0 ? _mm256_add_epi16(v, col) : _mm256_sub_epi16(v, col);
        }
        if (count > 1) {
            const __m256i col = _mm256_load_si256(reinterpret_cast<const __m256i*>(col1 + h));
            v = add1 ? _mm256_add_epi16(v, col) : _mm256_sub_epi16(v, col);
        }
        if (count > 2) {
            const __m256i col = _mm256_load_si256(reinterpret_cast<const __m256i*>(col2 + h));
            v = add2 ? _mm256_add_epi16(v, col) : _mm256_sub_epi16(v, col);
        }
        if (count > 3) {
            const __m256i col = _mm256_load_si256(reinterpret_cast<const __m256i*>(col3 + h));
            v = add3 ? _mm256_add_epi16(v, col) : _mm256_sub_epi16(v, col);
        }
        _mm256_store_si256(reinterpret_cast<__m256i*>(destination + h), v);
    }
}

void apply_changes_pair_avx2(const std::int16_t* source0, std::int16_t* destination0, const Changes& c0,
                             const std::int16_t* source1, std::int16_t* destination1, const Changes& c1, int hidden) {
    if (c0.count == 2 && c1.count == 2 && !c0.adds[0] && c0.adds[1] && !c1.adds[0] && c1.adds[1]) {
        const std::int16_t* const s0 = c0.columns[0];
        const std::int16_t* const a0 = c0.columns[1];
        const std::int16_t* const s1 = c1.columns[0];
        const std::int16_t* const a1 = c1.columns[1];
        for (int h = 0; h < hidden; h += 16) {
            const __m256i v0 = _mm256_add_epi16(
                _mm256_sub_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(source0 + h)),
                                 _mm256_load_si256(reinterpret_cast<const __m256i*>(s0 + h))),
                _mm256_load_si256(reinterpret_cast<const __m256i*>(a0 + h)));
            _mm256_store_si256(reinterpret_cast<__m256i*>(destination0 + h), v0);
            const __m256i v1 = _mm256_add_epi16(
                _mm256_sub_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(source1 + h)),
                                 _mm256_load_si256(reinterpret_cast<const __m256i*>(s1 + h))),
                _mm256_load_si256(reinterpret_cast<const __m256i*>(a1 + h)));
            _mm256_store_si256(reinterpret_cast<__m256i*>(destination1 + h), v1);
        }
        return;
    }
    if (c0.count == 3 && c1.count == 3 && !c0.adds[0] && !c0.adds[1] && c0.adds[2] &&
        !c1.adds[0] && !c1.adds[1] && c1.adds[2]) {
        const std::int16_t* const s0a = c0.columns[0];
        const std::int16_t* const s0b = c0.columns[1];
        const std::int16_t* const a0 = c0.columns[2];
        const std::int16_t* const s1a = c1.columns[0];
        const std::int16_t* const s1b = c1.columns[1];
        const std::int16_t* const a1 = c1.columns[2];
        for (int h = 0; h < hidden; h += 16) {
            const __m256i v0 = _mm256_add_epi16(
                _mm256_sub_epi16(
                    _mm256_sub_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(source0 + h)),
                                     _mm256_load_si256(reinterpret_cast<const __m256i*>(s0a + h))),
                    _mm256_load_si256(reinterpret_cast<const __m256i*>(s0b + h))),
                _mm256_load_si256(reinterpret_cast<const __m256i*>(a0 + h)));
            _mm256_store_si256(reinterpret_cast<__m256i*>(destination0 + h), v0);
            const __m256i v1 = _mm256_add_epi16(
                _mm256_sub_epi16(
                    _mm256_sub_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(source1 + h)),
                                     _mm256_load_si256(reinterpret_cast<const __m256i*>(s1a + h))),
                    _mm256_load_si256(reinterpret_cast<const __m256i*>(s1b + h))),
                _mm256_load_si256(reinterpret_cast<const __m256i*>(a1 + h)));
            _mm256_store_si256(reinterpret_cast<__m256i*>(destination1 + h), v1);
        }
        return;
    }
    for (int h = 0; h < hidden; h += 16) {
        __m256i v0 = _mm256_load_si256(reinterpret_cast<const __m256i*>(source0 + h));
        for (int i = 0; i < c0.count; ++i) {
            const __m256i col = _mm256_load_si256(reinterpret_cast<const __m256i*>(c0.columns[i] + h));
            v0 = c0.adds[i] ? _mm256_add_epi16(v0, col) : _mm256_sub_epi16(v0, col);
        }
        _mm256_store_si256(reinterpret_cast<__m256i*>(destination0 + h), v0);
        __m256i v1 = _mm256_load_si256(reinterpret_cast<const __m256i*>(source1 + h));
        for (int i = 0; i < c1.count; ++i) {
            const __m256i col = _mm256_load_si256(reinterpret_cast<const __m256i*>(c1.columns[i] + h));
            v1 = c1.adds[i] ? _mm256_add_epi16(v1, col) : _mm256_sub_epi16(v1, col);
        }
        _mm256_store_si256(reinterpret_cast<__m256i*>(destination1 + h), v1);
    }
}
#endif

#if FORGE_NNUE_V3_AVX512
void apply_changes_avx512(const std::int16_t* source, std::int16_t* destination, const Changes& c, int hidden) {
    const int count = c.count;
    const std::int16_t* col0 = c.columns[0];
    const std::int16_t* col1 = c.columns[1];
    const std::int16_t* col2 = c.columns[2];
    const std::int16_t* col3 = c.columns[3];
    const bool add0 = c.adds[0];
    const bool add1 = c.adds[1];
    const bool add2 = c.adds[2];
    const bool add3 = c.adds[3];
    for (int h = 0; h < hidden; h += 32) {
        __m512i v = _mm512_load_si512(reinterpret_cast<const __m512i*>(source + h));
        if (count > 0) {
            const __m512i col = _mm512_load_si512(reinterpret_cast<const __m512i*>(col0 + h));
            v = add0 ? _mm512_add_epi16(v, col) : _mm512_sub_epi16(v, col);
        }
        if (count > 1) {
            const __m512i col = _mm512_load_si512(reinterpret_cast<const __m512i*>(col1 + h));
            v = add1 ? _mm512_add_epi16(v, col) : _mm512_sub_epi16(v, col);
        }
        if (count > 2) {
            const __m512i col = _mm512_load_si512(reinterpret_cast<const __m512i*>(col2 + h));
            v = add2 ? _mm512_add_epi16(v, col) : _mm512_sub_epi16(v, col);
        }
        if (count > 3) {
            const __m512i col = _mm512_load_si512(reinterpret_cast<const __m512i*>(col3 + h));
            v = add3 ? _mm512_add_epi16(v, col) : _mm512_sub_epi16(v, col);
        }
        _mm512_store_si512(reinterpret_cast<__m512i*>(destination + h), v);
    }
}

void apply_changes_pair_avx512(const std::int16_t* source0, std::int16_t* destination0, const Changes& c0,
                               const std::int16_t* source1, std::int16_t* destination1, const Changes& c1, int hidden) {
    if (c0.count == 2 && c1.count == 2 && !c0.adds[0] && c0.adds[1] && !c1.adds[0] && c1.adds[1]) {
        const std::int16_t* const s0 = c0.columns[0];
        const std::int16_t* const a0 = c0.columns[1];
        const std::int16_t* const s1 = c1.columns[0];
        const std::int16_t* const a1 = c1.columns[1];
        for (int h = 0; h < hidden; h += 32) {
            const __m512i v0 = _mm512_add_epi16(
                _mm512_sub_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(source0 + h)),
                                 _mm512_load_si512(reinterpret_cast<const __m512i*>(s0 + h))),
                _mm512_load_si512(reinterpret_cast<const __m512i*>(a0 + h)));
            _mm512_store_si512(reinterpret_cast<__m512i*>(destination0 + h), v0);
            const __m512i v1 = _mm512_add_epi16(
                _mm512_sub_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(source1 + h)),
                                 _mm512_load_si512(reinterpret_cast<const __m512i*>(s1 + h))),
                _mm512_load_si512(reinterpret_cast<const __m512i*>(a1 + h)));
            _mm512_store_si512(reinterpret_cast<__m512i*>(destination1 + h), v1);
        }
        return;
    }
    if (c0.count == 3 && c1.count == 3 && !c0.adds[0] && !c0.adds[1] && c0.adds[2] &&
        !c1.adds[0] && !c1.adds[1] && c1.adds[2]) {
        const std::int16_t* const s0a = c0.columns[0];
        const std::int16_t* const s0b = c0.columns[1];
        const std::int16_t* const a0 = c0.columns[2];
        const std::int16_t* const s1a = c1.columns[0];
        const std::int16_t* const s1b = c1.columns[1];
        const std::int16_t* const a1 = c1.columns[2];
        for (int h = 0; h < hidden; h += 32) {
            const __m512i v0 = _mm512_add_epi16(
                _mm512_sub_epi16(
                    _mm512_sub_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(source0 + h)),
                                     _mm512_load_si512(reinterpret_cast<const __m512i*>(s0a + h))),
                    _mm512_load_si512(reinterpret_cast<const __m512i*>(s0b + h))),
                _mm512_load_si512(reinterpret_cast<const __m512i*>(a0 + h)));
            _mm512_store_si512(reinterpret_cast<__m512i*>(destination0 + h), v0);
            const __m512i v1 = _mm512_add_epi16(
                _mm512_sub_epi16(
                    _mm512_sub_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(source1 + h)),
                                     _mm512_load_si512(reinterpret_cast<const __m512i*>(s1a + h))),
                    _mm512_load_si512(reinterpret_cast<const __m512i*>(s1b + h))),
                _mm512_load_si512(reinterpret_cast<const __m512i*>(a1 + h)));
            _mm512_store_si512(reinterpret_cast<__m512i*>(destination1 + h), v1);
        }
        return;
    }
    for (int h = 0; h < hidden; h += 32) {
        __m512i v0 = _mm512_load_si512(reinterpret_cast<const __m512i*>(source0 + h));
        for (int i = 0; i < c0.count; ++i) {
            const __m512i col = _mm512_load_si512(reinterpret_cast<const __m512i*>(c0.columns[i] + h));
            v0 = c0.adds[i] ? _mm512_add_epi16(v0, col) : _mm512_sub_epi16(v0, col);
        }
        _mm512_store_si512(reinterpret_cast<__m512i*>(destination0 + h), v0);
        __m512i v1 = _mm512_load_si512(reinterpret_cast<const __m512i*>(source1 + h));
        for (int i = 0; i < c1.count; ++i) {
            const __m512i col = _mm512_load_si512(reinterpret_cast<const __m512i*>(c1.columns[i] + h));
            v1 = c1.adds[i] ? _mm512_add_epi16(v1, col) : _mm512_sub_epi16(v1, col);
        }
        _mm512_store_si512(reinterpret_cast<__m512i*>(destination1 + h), v1);
    }
}

std::int64_t apply_pair_and_sum_avx512(const Net& net, const std::int16_t* source0, std::int16_t* destination0,
                                       const Changes& c0, const std::int16_t* source1, std::int16_t* destination1,
                                       const Changes& c1, Color us, int bucket) {
    const int hidden = net.hidden;
    const std::int16_t* const w2_base = net.w2.data() + static_cast<std::size_t>(bucket) * 2 * static_cast<std::size_t>(hidden);
    const std::int16_t* const w0 = us == White ? w2_base : (w2_base + hidden);
    const std::int16_t* const w1 = us == White ? (w2_base + hidden) : w2_base;
    const __m512i zero = _mm512_setzero_si512();
    const __m512i qa = _mm512_set1_epi16(static_cast<short>(QA));
    __m512i sum0 = zero;
    __m512i sum1 = zero;

    if (c0.count == 2 && c1.count == 2 && !c0.adds[0] && c0.adds[1] && !c1.adds[0] && c1.adds[1]) {
        const std::int16_t* const s0 = c0.columns[0];
        const std::int16_t* const a0 = c0.columns[1];
        const std::int16_t* const s1 = c1.columns[0];
        const std::int16_t* const a1 = c1.columns[1];
        for (int h = 0; h < hidden; h += 32) {
            const __m512i v0 = _mm512_add_epi16(
                _mm512_sub_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(source0 + h)),
                                 _mm512_load_si512(reinterpret_cast<const __m512i*>(s0 + h))),
                _mm512_load_si512(reinterpret_cast<const __m512i*>(a0 + h)));
            _mm512_store_si512(reinterpret_cast<__m512i*>(destination0 + h), v0);
            const __m512i v1 = _mm512_add_epi16(
                _mm512_sub_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(source1 + h)),
                                 _mm512_load_si512(reinterpret_cast<const __m512i*>(s1 + h))),
                _mm512_load_si512(reinterpret_cast<const __m512i*>(a1 + h)));
            _mm512_store_si512(reinterpret_cast<__m512i*>(destination1 + h), v1);

            const __m512i c_v0 = _mm512_min_epi16(_mm512_max_epi16(v0, zero), qa);
            const __m512i c_v1 = _mm512_min_epi16(_mm512_max_epi16(v1, zero), qa);
            sum0 = _mm512_add_epi32(sum0, _mm512_madd_epi16(_mm512_mullo_epi16(c_v0, _mm512_load_si512(reinterpret_cast<const __m512i*>(w0 + h))), c_v0));
            sum1 = _mm512_add_epi32(sum1, _mm512_madd_epi16(_mm512_mullo_epi16(c_v1, _mm512_load_si512(reinterpret_cast<const __m512i*>(w1 + h))), c_v1));
        }
        return hsum_epi32_pair_avx512(sum0, sum1);
    }

    if (c0.count == 3 && c1.count == 3 && !c0.adds[0] && !c0.adds[1] && c0.adds[2] &&
        !c1.adds[0] && !c1.adds[1] && c1.adds[2]) {
        const std::int16_t* const s0a = c0.columns[0];
        const std::int16_t* const s0b = c0.columns[1];
        const std::int16_t* const a0 = c0.columns[2];
        const std::int16_t* const s1a = c1.columns[0];
        const std::int16_t* const s1b = c1.columns[1];
        const std::int16_t* const a1 = c1.columns[2];
        for (int h = 0; h < hidden; h += 32) {
            const __m512i v0 = _mm512_add_epi16(
                _mm512_sub_epi16(
                    _mm512_sub_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(source0 + h)),
                                     _mm512_load_si512(reinterpret_cast<const __m512i*>(s0a + h))),
                    _mm512_load_si512(reinterpret_cast<const __m512i*>(s0b + h))),
                _mm512_load_si512(reinterpret_cast<const __m512i*>(a0 + h)));
            _mm512_store_si512(reinterpret_cast<__m512i*>(destination0 + h), v0);
            const __m512i v1 = _mm512_add_epi16(
                _mm512_sub_epi16(
                    _mm512_sub_epi16(_mm512_load_si512(reinterpret_cast<const __m512i*>(source1 + h)),
                                     _mm512_load_si512(reinterpret_cast<const __m512i*>(s1a + h))),
                    _mm512_load_si512(reinterpret_cast<const __m512i*>(s1b + h))),
                _mm512_load_si512(reinterpret_cast<const __m512i*>(a1 + h)));
            _mm512_store_si512(reinterpret_cast<__m512i*>(destination1 + h), v1);

            const __m512i c_v0 = _mm512_min_epi16(_mm512_max_epi16(v0, zero), qa);
            const __m512i c_v1 = _mm512_min_epi16(_mm512_max_epi16(v1, zero), qa);
            sum0 = _mm512_add_epi32(sum0, _mm512_madd_epi16(_mm512_mullo_epi16(c_v0, _mm512_load_si512(reinterpret_cast<const __m512i*>(w0 + h))), c_v0));
            sum1 = _mm512_add_epi32(sum1, _mm512_madd_epi16(_mm512_mullo_epi16(c_v1, _mm512_load_si512(reinterpret_cast<const __m512i*>(w1 + h))), c_v1));
        }
        return hsum_epi32_pair_avx512(sum0, sum1);
    }

    apply_changes_pair_avx512(source0, destination0, c0, source1, destination1, c1, hidden);
    return output_sum_avx512(net, us == White ? destination0 : destination1,
                             us == White ? destination1 : destination0, bucket);
}
#endif

} // namespace

AlignedInt16::~AlignedInt16() { release(); }

void AlignedInt16::allocate(std::size_t count) {
    release();
    data_ = static_cast<std::int16_t*>(::operator new(count * sizeof(std::int16_t), std::align_val_t{64}));
    size_ = count;
    std::fill(data_, data_ + count, static_cast<std::int16_t>(0));
}

void AlignedInt16::release() {
    if (data_ != nullptr) ::operator delete(data_, std::align_val_t{64});
    data_ = nullptr;
    size_ = 0;
}

std::uint64_t fnv1a64(const std::uint8_t* data, std::size_t size, std::uint64_t hash) {
    for (std::size_t i = 0; i < size; ++i) {
        hash ^= static_cast<std::uint64_t>(data[i]);
        hash *= 1099511628211ULL;
    }
    return hash;
}

std::size_t file_size_for(int hidden, int king_buckets, int output_buckets) {
    const std::size_t h = static_cast<std::size_t>(hidden);
    return static_cast<std::size_t>(HeaderBytes) +
           2 * static_cast<std::size_t>(king_buckets) * static_cast<std::size_t>(InputsPerBucket) * h +   // w1
           2 * h +                                                                                          // b1
           2 * static_cast<std::size_t>(output_buckets) * 2 * h +                                           // w2
           4 * static_cast<std::size_t>(output_buckets) +                                                   // b2
           8;                                                                                               // checksum
}

const char* kernel_name() { return FORGE_NNUE_V3_AVX512 ? "avx512" : FORGE_NNUE_V3_AVX2 ? "avx2" : "scalar"; }

Kernel best_kernel() { return FORGE_NNUE_V3_AVX512 ? Kernel::Avx512 : FORGE_NNUE_V3_AVX2 ? Kernel::Avx2 : Kernel::Scalar; }

bool kernel_available(Kernel kernel) {
    switch (kernel) {
    case Kernel::Scalar: return true;
    case Kernel::Avx2: return FORGE_NNUE_V3_AVX2 != 0;
    case Kernel::Avx512: return FORGE_NNUE_V3_AVX512 != 0;
    }
    return false;
}

const char* kernel_name(Kernel kernel) {
    switch (kernel) {
    case Kernel::Scalar: return "scalar";
    case Kernel::Avx2: return "avx2";
    case Kernel::Avx512: return "avx512";
    }
    return "?";
}

bool load(const std::string& path, std::string* error) {
    // No silent fallback: whatever happens below, a failed load leaves nothing loaded.
    g_net.reset();
#if FORGE65
    // forge6.5: the path <forge65> names the net compiled into the exe; every other path is a file, as before.
    // The built-in bytes pass through all the checks below like a file's.
    std::vector<std::uint8_t> bytes;
    if (path == forge65::NetPath) {
        bytes.assign(forge65::net_data(), forge65::net_data() + forge65::net_size());
    } else {
        std::ifstream in(path, std::ios::binary);
        if (!in) return fail(error, "cannot open " + path);
        bytes.assign((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    }
#else
    std::ifstream in(path, std::ios::binary);
    if (!in) return fail(error, "cannot open " + path);
    std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
#endif
    if (bytes.size() < static_cast<std::size_t>(HeaderBytes) + 8) return fail(error, path + ": file too small for a v3 header");
    const std::uint8_t* h = bytes.data();
    if (std::memcmp(h, "FORGENN3", 8) != 0) return fail(error, path + ": bad magic (expected FORGENN3)");
    if (read_u32(h + 8) != 3U) return fail(error, path + ": unsupported version " + std::to_string(read_u32(h + 8)));
    if (read_u32(h + 12) != static_cast<std::uint32_t>(HeaderBytes)) return fail(error, path + ": header_bytes must be 192");
    if (read_u32(h + 16) != static_cast<std::uint32_t>(InputsPerBucket)) return fail(error, path + ": inputs must be 768");
    const std::uint32_t hidden = read_u32(h + 20);
    const std::uint32_t king_buckets = read_u32(h + 24);
    const std::uint32_t output_buckets = read_u32(h + 28);
    const std::uint32_t flags = read_u32(h + 32);
    const std::int32_t qa = read_i32(h + 36);
    const std::int32_t qb = read_i32(h + 40);
    const std::int32_t eval_scale = read_i32(h + 44);
    if (hidden < static_cast<std::uint32_t>(MinHidden) || hidden > static_cast<std::uint32_t>(MaxHidden) || hidden % 32U != 0U) {
        return fail(error, path + ": hidden must be a multiple of 32 in 32..1024, got " + std::to_string(hidden));
    }
    if (king_buckets < 1U || king_buckets > static_cast<std::uint32_t>(MaxKingBuckets)) {
        return fail(error, path + ": king_buckets must be 1..32, got " + std::to_string(king_buckets));
    }
    if (output_buckets < 1U || output_buckets > static_cast<std::uint32_t>(MaxOutputBuckets)) {
        return fail(error, path + ": output_buckets must be 1..16, got " + std::to_string(output_buckets));
    }
    if ((flags & ~(FlagResidual | FlagMirror)) != 0U) return fail(error, path + ": unknown flag bits");
    if (qa != QA || qb != QB) return fail(error, path + ": quantisation must be qa 255 / qb 64");
    if (eval_scale < 1 || eval_scale > MaxEvalScale) return fail(error, path + ": eval_scale must be 1..10000");
    for (int i = 145; i < HeaderBytes; ++i) {
        if (h[i] != 0) return fail(error, path + ": reserved header bytes must be zero");
    }
    const std::size_t expected = file_size_for(static_cast<int>(hidden), static_cast<int>(king_buckets), static_cast<int>(output_buckets));
    if (bytes.size() != expected) {
        return fail(error, path + ": file size " + std::to_string(bytes.size()) + " != expected " + std::to_string(expected));
    }
    const std::uint64_t stored = read_u64(bytes.data() + bytes.size() - 8);
    const std::uint64_t computed = fnv1a64(bytes.data(), bytes.size() - 8);
    if (stored != computed) return fail(error, path + ": checksum mismatch");

    auto net = std::make_unique<Net>();
    net->path = path;
    net->hidden = static_cast<int>(hidden);
    net->king_buckets = static_cast<int>(king_buckets);
    net->output_buckets = static_cast<int>(output_buckets);
    net->eval_scale = eval_scale;
    net->residual = (flags & FlagResidual) != 0U;
    net->mirror = (flags & FlagMirror) != 0U;
    net->checksum = stored;
    for (int i = 0; i < 64; ++i) {
        net->king_map[static_cast<std::size_t>(i)] = h[48 + i];
        if (h[48 + i] >= king_buckets) return fail(error, path + ": king_bucket_map entry out of range");
    }
    for (int i = 0; i < 33; ++i) {
        net->output_map[static_cast<std::size_t>(i)] = h[112 + i];
        if (h[112 + i] >= output_buckets) return fail(error, path + ": output_bucket_map entry out of range");
    }
    const std::size_t hs = static_cast<std::size_t>(net->hidden);
    const std::size_t w1_count = static_cast<std::size_t>(net->king_buckets) * static_cast<std::size_t>(InputsPerBucket) * hs;
    const std::size_t w2_count = static_cast<std::size_t>(net->output_buckets) * 2 * hs;
    net->w1.allocate(w1_count);
    net->b1.allocate(hs);
    net->w2.allocate(w2_count);
    net->b2.assign(static_cast<std::size_t>(net->output_buckets), 0);
    const std::uint8_t* p = h + HeaderBytes;
    int max_w1 = 0;
    for (std::size_t i = 0; i < w1_count; ++i, p += 2) {
        const std::int16_t v = read_i16(p);
        net->w1.data()[i] = v;
        max_w1 = std::max(max_w1, std::abs(static_cast<int>(v)));
    }
    int max_b1 = 0;
    for (std::size_t i = 0; i < hs; ++i, p += 2) {
        const std::int16_t v = read_i16(p);
        net->b1.data()[i] = v;
        max_b1 = std::max(max_b1, std::abs(static_cast<int>(v)));
    }
    int max_w2 = 0;
    for (std::size_t i = 0; i < w2_count; ++i, p += 2) {
        const std::int16_t v = read_i16(p);
        net->w2.data()[i] = v;
        max_w2 = std::max(max_w2, std::abs(static_cast<int>(v)));
    }
    for (std::size_t i = 0; i < static_cast<std::size_t>(net->output_buckets); ++i, p += 4) net->b2[i] = read_i32(p);
    net->max_abs_w1 = max_w1;
    net->max_abs_b1 = max_b1;
    net->max_abs_w2 = max_w2;
    if (max_w2 > MaxW2) return fail(error, path + ": |w2| must be <= 127, got " + std::to_string(max_w2));
    if (max_b1 + MaxPieces * max_w1 > 32767) {
        return fail(error, path + ": accumulator range: max|b1| + 32 * max|w1| = " + std::to_string(max_b1 + MaxPieces * max_w1) + " > 32767");
    }
    net->generation = ++g_generation;
    g_net = std::move(net);
    return true;
}

void unload() { g_net.reset(); }

const Net* loaded() { return g_net.get(); }

std::string describe(const Net& net) {
    std::ostringstream out;
    out << "v3 " << net.path << " hidden " << net.hidden << " king_buckets " << net.king_buckets
        << (net.mirror ? " mirrored" : "") << " output_buckets " << net.output_buckets
        << (net.residual ? " residual" : " standalone") << " eval_scale " << net.eval_scale
        << " checksum " << std::hex << net.checksum << std::dec
        << " max|w1| " << net.max_abs_w1 << " max|b1| " << net.max_abs_b1 << " max|w2| " << net.max_abs_w2
        << " kernel " << kernel_name();
    return out.str();
}

bool pending() { return requested && loaded() == nullptr && g_problem.empty(); }

std::string problem() {
    if (!requested) return {};
    if (loaded() == nullptr) {
        if (!g_problem.empty()) return g_problem;
        return "NNUEArch is on but no v3 network is loaded (set NNUEArchFile)";
    }
    return {};
}

void set_problem(const std::string& text) { g_problem = text; }

KingKey king_key(const Net& net, Color perspective, int king_square) {
    const int kr = perspective == White ? king_square : king_square ^ 56;
    KingKey key;
    key.bucket = net.king_map[static_cast<std::size_t>(kr)];
    key.flip = (net.mirror && (kr & 7) >= 4) ? 7 : 0;
    return key;
}

int feature_index(KingKey key, Color perspective, Piece piece, int square) {
    const int relative_color = color_of(piece) == perspective ? 0 : 1;
    const int type = piece_type(piece) - 1;
    const int relative_square = (perspective == White ? square : square ^ 56) ^ static_cast<int>(key.flip);
    return static_cast<int>(key.bucket) * InputsPerBucket + (relative_color * 6 + type) * 64 + relative_square;
}

int output_bucket(const Net& net, const Board& board) {
    const int pieces = std::min(popcount(board.occupied()), MaxPieces);
    return net.output_map[static_cast<std::size_t>(pieces)];
}

Pieces pieces_of(const Board& board) {
    Pieces pieces{};
    for (int piece = WP; piece <= BK; ++piece) pieces[static_cast<std::size_t>(piece)] = board.pieces(static_cast<Piece>(piece));
    return pieces;
}

// ---- scalar reference path ----

void refresh_perspective(const Net& net, const Board& board, Color perspective, Accumulator& accumulator) {
    const int hidden = net.hidden;
    auto& acc = accumulator.values[static_cast<std::size_t>(perspective)];
    const int king_square = board.king_square(perspective);
    const KingKey key = king_key(net, perspective, king_square);
    accumulator.keys[static_cast<std::size_t>(perspective)] = key;
    accumulator.king_sq[static_cast<std::size_t>(perspective)] = static_cast<std::uint8_t>(king_square);
    const std::int16_t* b1 = net.b1.data();
    for (int h = 0; h < hidden; ++h) acc[static_cast<std::size_t>(h)] = b1[h];
    Bitboard occupied = board.occupied();
    while (occupied != 0) {
        const int square = pop_lsb(occupied);
        add_column_scalar(acc.data(), column(net, feature_index(key, perspective, board.piece_at(square), square)), hidden);
    }
}

void refresh(const Net& net, const Board& board, Accumulator& accumulator) {
    refresh_perspective(net, board, White, accumulator);
    refresh_perspective(net, board, Black, accumulator);
    accumulator.valid = true;
}

std::int64_t output_sum_scalar(const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket) {
    const int hidden = net.hidden;
    const std::int16_t* w2 = net.w2.data() + static_cast<std::size_t>(bucket) * 2 * static_cast<std::size_t>(hidden);
    std::int64_t sum = 0;
    for (int h = 0; h < hidden; ++h) {
        const int a = std::clamp(static_cast<int>(ours[h]), 0, QA);
        sum += static_cast<std::int64_t>(a * a * static_cast<int>(w2[h]));
    }
    for (int h = 0; h < hidden; ++h) {
        const int b = std::clamp(static_cast<int>(theirs[h]), 0, QA);
        sum += static_cast<std::int64_t>(b * b * static_cast<int>(w2[hidden + h]));
    }
    return sum;
}

int finish(const Net& net, std::int64_t sum, int bucket) {
    const std::int64_t out = sum / QA + static_cast<std::int64_t>(net.b2[static_cast<std::size_t>(bucket)]);
    const std::int64_t centipawns = out * static_cast<std::int64_t>(net.eval_scale) / static_cast<std::int64_t>(QA * QB);
    return static_cast<int>(std::clamp<std::int64_t>(centipawns, -30000, 30000));
}

int evaluate_reference(const Net& net, const Board& board) {
    auto accumulator = std::make_unique<Accumulator>();
    refresh(net, board, *accumulator);
    const Color us = board.side_to_move();
    const int bucket = output_bucket(net, board);
    return finish(net, output_sum_scalar(net, accumulator->values[static_cast<std::size_t>(us)].data(),
                                         accumulator->values[static_cast<std::size_t>(opposite(us))].data(), bucket), bucket);
}

// ---- fast path ----

std::int64_t output_sum(const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket) {
#if FORGE_NNUE_V3_AVX512
    return output_sum_avx512(net, ours, theirs, bucket);
#elif FORGE_NNUE_V3_AVX2
    return output_sum_avx2(net, ours, theirs, bucket);
#else
    return output_sum_scalar(net, ours, theirs, bucket);
#endif
}

std::int64_t output_sum_with(Kernel kernel, const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket) {
    switch (kernel) {
    case Kernel::Scalar: return output_sum_scalar(net, ours, theirs, bucket);
#if FORGE_NNUE_V3_AVX2
    case Kernel::Avx2: return output_sum_avx2(net, ours, theirs, bucket);
#endif
#if FORGE_NNUE_V3_AVX512
    case Kernel::Avx512: return output_sum_avx512(net, ours, theirs, bucket);
#endif
    default: return output_sum_scalar(net, ours, theirs, bucket);
    }
}

void add_column_with(Kernel kernel, std::int16_t* acc, const std::int16_t* col, int hidden, bool add) {
    switch (kernel) {
#if FORGE_NNUE_V3_AVX2
    case Kernel::Avx2: if (add) add_column_avx2(acc, col, hidden); else sub_column_avx2(acc, col, hidden); return;
#endif
#if FORGE_NNUE_V3_AVX512
    case Kernel::Avx512: if (add) add_column_avx512(acc, col, hidden); else sub_column_avx512(acc, col, hidden); return;
#endif
    default: if (add) add_column_scalar(acc, col, hidden); else sub_column_scalar(acc, col, hidden); return;
    }
}

int evaluate(const Net& net, const Board& board, const Accumulator& accumulator) {
    const Color us = board.side_to_move();
    const int bucket = output_bucket(net, board);
    return finish(net, output_sum(net, accumulator.values[static_cast<std::size_t>(us)].data(),
                                  accumulator.values[static_cast<std::size_t>(opposite(us))].data(), bucket), bucket);
}

void prepare(const Net& net, WorkerState& state, int stack_size) {
    if (state.generation == net.generation && state.stack.size() == static_cast<std::size_t>(stack_size)) return;
    state.stack.assign(static_cast<std::size_t>(stack_size), Accumulator{});
    state.valid_flags.assign(static_cast<std::size_t>(stack_size), static_cast<std::uint8_t>(0));
    state.cache.entries.assign(static_cast<std::size_t>(2 * net.king_buckets * 2), RefreshCache::Entry{});
    for (RefreshCache::Entry& entry : state.cache.entries) {
        // An entry starts as the empty board: bias only, no pieces.
        std::copy_n(net.b1.data(), net.hidden, entry.values.data());
        entry.pieces.fill(0);
    }
    state.cache.generation = net.generation;
    state.cache.refreshes = 0;
    state.cache.columns = 0;
    state.generation = net.generation;
}

void apply_changes(const Net& net, const std::int16_t* source, std::int16_t* destination, KingKey key, Color perspective,
                   const DirtyPieces& dirty) {
    const Changes c = collect_changes(net, key, perspective, dirty);
#if FORGE_NNUE_V3_AVX512
    apply_changes_avx512(source, destination, c, net.hidden);
#elif FORGE_NNUE_V3_AVX2
    apply_changes_avx2(source, destination, c, net.hidden);
#else
    apply_changes_scalar(source, destination, c, net.hidden);
#endif
}

void apply_changes_pair(const Net& net, const std::int16_t* source0, std::int16_t* destination0, KingKey key0,
                        const std::int16_t* source1, std::int16_t* destination1, KingKey key1,
                        const DirtyPieces& dirty) {
    const Changes c0 = collect_changes(net, key0, White, dirty);
    const Changes c1 = collect_changes(net, key1, Black, dirty);
#if FORGE_NNUE_V3_AVX512
    apply_changes_pair_avx512(source0, destination0, c0, source1, destination1, c1, net.hidden);
#elif FORGE_NNUE_V3_AVX2
    apply_changes_pair_avx2(source0, destination0, c0, source1, destination1, c1, net.hidden);
#else
    apply_changes_pair_scalar(source0, destination0, c0, source1, destination1, c1, net.hidden);
#endif
}

void apply_changes_with(Kernel kernel, const Net& net, const std::int16_t* source, std::int16_t* destination, KingKey key,
                        Color perspective, const DirtyPieces& dirty) {
    const Changes c = collect_changes(net, key, perspective, dirty);
    switch (kernel) {
#if FORGE_NNUE_V3_AVX2
    case Kernel::Avx2: apply_changes_avx2(source, destination, c, net.hidden); return;
#endif
#if FORGE_NNUE_V3_AVX512
    case Kernel::Avx512: apply_changes_avx512(source, destination, c, net.hidden); return;
#endif
    default: apply_changes_scalar(source, destination, c, net.hidden); return;
    }
}

int apply_pair_and_evaluate(const Net& net, const Accumulator& parent, Accumulator& child,
                            KingKey key0, int king0, KingKey key1, int king1,
                            const DirtyPieces& dirty, const Board& board) {
    child.king_sq[0] = static_cast<std::uint8_t>(king0);
    child.keys[0] = key0;
    child.king_sq[1] = static_cast<std::uint8_t>(king1);
    child.keys[1] = key1;
    child.valid = true;
    const Changes c0 = collect_changes(net, key0, White, dirty);
    const Changes c1 = collect_changes(net, key1, Black, dirty);
    const Color us = board.side_to_move();
    const int bucket = output_bucket(net, board);
#if FORGE_NNUE_V3_AVX512
    const std::int64_t sum = apply_pair_and_sum_avx512(
        net, parent.values[0].data(), child.values[0].data(), c0,
        parent.values[1].data(), child.values[1].data(), c1, us, bucket);
    return finish(net, sum, bucket);
#else
    apply_changes_pair(net, parent.values[0].data(), child.values[0].data(), key0,
                       parent.values[1].data(), child.values[1].data(), key1, dirty);
    return finish(net, output_sum(net, child.values[static_cast<std::size_t>(us)].data(),
                                  child.values[static_cast<std::size_t>(opposite(us))].data(), bucket), bucket);
#endif
}

void refresh_from_pieces(const Net& net, RefreshCache& cache, const Pieces& pieces, Color perspective, int king_square,
                         std::int16_t* destination) {
    const KingKey key = king_key(net, perspective, king_square);
    RefreshCache::Entry& entry = cache.entries[cache_index(net, perspective, key)];
    const int hidden = net.hidden;
    ++cache.refreshes;
    const std::int16_t* subs[32];
    const std::int16_t* adds[32];
    int n_sub = 0;
    int n_add = 0;
    for (int piece = WP; piece <= BK; ++piece) {
        const auto pi = static_cast<std::size_t>(piece);
        Bitboard removed = entry.pieces[pi] & ~pieces[pi];
        Bitboard added = pieces[pi] & ~entry.pieces[pi];
        while (removed != 0) {
            const int square = pop_lsb(removed);
            subs[n_sub++] = column(net, feature_index(key, perspective, static_cast<Piece>(piece), square));
        }
        while (added != 0) {
            const int square = pop_lsb(added);
            adds[n_add++] = column(net, feature_index(key, perspective, static_cast<Piece>(piece), square));
        }
        entry.pieces[pi] = pieces[pi];
    }
    cache.columns += static_cast<std::uint64_t>(n_sub + n_add);
    std::int16_t* const acc = entry.values.data();
#if FORGE_NNUE_V3_AVX512
    int s = 0;
    for (; s + 4 <= n_sub; s += 4) {
        const std::int16_t *c0 = subs[s], *c1 = subs[s + 1], *c2 = subs[s + 2], *c3 = subs[s + 3];
        for (int h = 0; h < hidden; h += 32) {
            __m512i v = _mm512_load_si512(reinterpret_cast<const __m512i*>(acc + h));
            v = _mm512_sub_epi16(v, _mm512_load_si512(reinterpret_cast<const __m512i*>(c0 + h)));
            v = _mm512_sub_epi16(v, _mm512_load_si512(reinterpret_cast<const __m512i*>(c1 + h)));
            v = _mm512_sub_epi16(v, _mm512_load_si512(reinterpret_cast<const __m512i*>(c2 + h)));
            v = _mm512_sub_epi16(v, _mm512_load_si512(reinterpret_cast<const __m512i*>(c3 + h)));
            _mm512_store_si512(reinterpret_cast<__m512i*>(acc + h), v);
        }
    }
    for (; s < n_sub; ++s) sub_column_avx512(acc, subs[s], hidden);
    int a = 0;
    for (; a + 4 <= n_add; a += 4) {
        const std::int16_t *c0 = adds[a], *c1 = adds[a + 1], *c2 = adds[a + 2], *c3 = adds[a + 3];
        for (int h = 0; h < hidden; h += 32) {
            __m512i v = _mm512_load_si512(reinterpret_cast<const __m512i*>(acc + h));
            v = _mm512_add_epi16(v, _mm512_load_si512(reinterpret_cast<const __m512i*>(c0 + h)));
            v = _mm512_add_epi16(v, _mm512_load_si512(reinterpret_cast<const __m512i*>(c1 + h)));
            v = _mm512_add_epi16(v, _mm512_load_si512(reinterpret_cast<const __m512i*>(c2 + h)));
            v = _mm512_add_epi16(v, _mm512_load_si512(reinterpret_cast<const __m512i*>(c3 + h)));
            _mm512_store_si512(reinterpret_cast<__m512i*>(acc + h), v);
        }
    }
    for (; a < n_add; ++a) add_column_avx512(acc, adds[a], hidden);
#else
    for (int s = 0; s < n_sub; ++s) sub_column(acc, subs[s], hidden);
    for (int a = 0; a < n_add; ++a) add_column(acc, adds[a], hidden);
#endif
    std::copy_n(acc, hidden, destination);
}

void refresh_cached(const Net& net, RefreshCache& cache, const Board& board, Accumulator& accumulator) {
    const Pieces pieces = pieces_of(board);
    for (const Color p : {White, Black}) {
        const auto pi = static_cast<std::size_t>(p);
        const int king_square = board.king_square(p);
        accumulator.king_sq[pi] = static_cast<std::uint8_t>(king_square);
        accumulator.keys[pi] = king_key(net, p, king_square);
        refresh_from_pieces(net, cache, pieces, p, king_square, accumulator.values[pi].data());
    }
    accumulator.valid = true;
}

} // namespace forge::nnue::v3
#endif // FORGE_NNUE_V3
