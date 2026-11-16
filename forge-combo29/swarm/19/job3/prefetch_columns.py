"""prefetch_columns.py : the change of job3/prefetch_columns.patch.txt, applied to a fresh copy.

Software-prefetch the next 16-float block of every weight column that fuse_columns / update stream through,
one block ahead. `_mm_prefetch` is architecturally a no-op: it cannot change a value, a rounding, a branch,
or a node count. It only asks the hardware to start the cache line fill earlier.
"""

# ---------------- src/nnue.cpp ----------------
p = "src/nnue.cpp"
s = open(p).read()

old_fuse = """    const __m512 zero = _mm512_setzero_ps();
    const __m512 one = _mm512_set1_ps(1.0F);
    __m512 sum = zero;
    for (int h = 0; h < HiddenSize; h += 16) {
        const std::size_t base = static_cast<std::size_t>(h);
        __m512 ours = _mm512_sub_ps(_mm512_loadu_ps(our_src + base), _mm512_loadu_ps(our_sub0 + base));"""
new_fuse = """    const __m512 zero = _mm512_setzero_ps();
    const __m512 one = _mm512_set1_ps(1.0F);
    __m512 sum = zero;
    for (int h = 0; h < HiddenSize; h += 16) {
        const std::size_t base = static_cast<std::size_t>(h);
        // The weight columns are far larger than L2 and are walked one 64-byte
        // block at a time; ask for the next block while this one is computed.
        if (h + 16 < HiddenSize) {
            const std::size_t next = base + 16;
            _mm_prefetch(reinterpret_cast<const char*>(our_sub0 + next), _MM_HINT_T0);
            _mm_prefetch(reinterpret_cast<const char*>(their_sub0 + next), _MM_HINT_T0);
            _mm_prefetch(reinterpret_cast<const char*>(our_add + next), _MM_HINT_T0);
            _mm_prefetch(reinterpret_cast<const char*>(their_add + next), _MM_HINT_T0);
            if constexpr (NSub == 2) {
                _mm_prefetch(reinterpret_cast<const char*>(our_sub1 + next), _MM_HINT_T0);
                _mm_prefetch(reinterpret_cast<const char*>(their_sub1 + next), _MM_HINT_T0);
            }
        }
        __m512 ours = _mm512_sub_ps(_mm512_loadu_ps(our_src + base), _mm512_loadu_ps(our_sub0 + base));"""
assert old_fuse in s
s = s.replace(old_fuse, new_fuse, 1)

old_upd2 = """            const float* added_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, added.piece, added.square)) * HiddenSize;
            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                destination[index] = (source[index] - removed_column[index]) + added_column[index];
            }"""
new_upd2 = """            const float* added_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, added.piece, added.square)) * HiddenSize;
            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                // Both columns are streamed once and are cold; fetch the line 16 floats ahead.
                if (h + 16 < HiddenSize) {
                    _mm_prefetch(reinterpret_cast<const char*>(removed_column + h + 16), _MM_HINT_T0);
                    _mm_prefetch(reinterpret_cast<const char*>(added_column + h + 16), _MM_HINT_T0);
                }
                destination[index] = (source[index] - removed_column[index]) + added_column[index];
            }"""
assert old_upd2 in s
s = s.replace(old_upd2, new_upd2, 1)

old_upd3 = """            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                destination[index] = ((source[index] - removed0_column[index]) - removed1_column[index]) + added_column[index];
            }"""
new_upd3 = """            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                if (h + 16 < HiddenSize) {
                    _mm_prefetch(reinterpret_cast<const char*>(removed0_column + h + 16), _MM_HINT_T0);
                    _mm_prefetch(reinterpret_cast<const char*>(removed1_column + h + 16), _MM_HINT_T0);
                    _mm_prefetch(reinterpret_cast<const char*>(added_column + h + 16), _MM_HINT_T0);
                }
                destination[index] = ((source[index] - removed0_column[index]) - removed1_column[index]) + added_column[index];
            }"""
assert old_upd3 in s
s = s.replace(old_upd3, new_upd3, 1)

# the AVX2 fuse_columns (used on targets without AVX-512) gets the same treatment
old_avx2 = """    __m256 sums[2] = {zero, zero};
    for (int h = 0; h < HiddenSize; h += 16) {
        for (int k = 0; k < 2; ++k) {
            const std::size_t base = static_cast<std::size_t>(h + 8 * k);
            __m256 ours = _mm256_sub_ps(_mm256_load_ps(our_src + base), _mm256_load_ps(our_sub0 + base));"""
new_avx2 = """    __m256 sums[2] = {zero, zero};
    for (int h = 0; h < HiddenSize; h += 16) {
        for (int k = 0; k < 2; ++k) {
            const std::size_t base = static_cast<std::size_t>(h + 8 * k);
            if (h + 16 < HiddenSize) {
                const std::size_t next = static_cast<std::size_t>(h + 16 + 8 * k);
                _mm_prefetch(reinterpret_cast<const char*>(our_sub0 + next), _MM_HINT_T0);
                _mm_prefetch(reinterpret_cast<const char*>(their_sub0 + next), _MM_HINT_T0);
                _mm_prefetch(reinterpret_cast<const char*>(our_add + next), _MM_HINT_T0);
                _mm_prefetch(reinterpret_cast<const char*>(their_add + next), _MM_HINT_T0);
                if constexpr (NSub == 2) {
                    _mm_prefetch(reinterpret_cast<const char*>(our_sub1 + next), _MM_HINT_T0);
                    _mm_prefetch(reinterpret_cast<const char*>(their_sub1 + next), _MM_HINT_T0);
                }
            }
            __m256 ours = _mm256_sub_ps(_mm256_load_ps(our_src + base), _mm256_load_ps(our_sub0 + base));"""
assert old_avx2 in s
s = s.replace(old_avx2, new_avx2, 1)
open(p, "w").write(s)
print("prefetch_columns applied")
