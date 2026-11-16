"""prefetch_lite.py : job3 variant — prefetch only the two REMOVE columns, one block ahead.

The full prefetch (six requests per 16-float step) cost ~8 % (see REPORT_job3.md). This variant asks for
half as many lines, so it tests whether the loss was the request volume rather than prefetching itself.
Still architecturally a no-op for values.
"""

p = "src/nnue.cpp"
s = open(p).read()

old_fuse = """    __m512 sum = zero;
    for (int h = 0; h < HiddenSize; h += 16) {
        const std::size_t base = static_cast<std::size_t>(h);
        __m512 ours = _mm512_sub_ps(_mm512_loadu_ps(our_src + base), _mm512_loadu_ps(our_sub0 + base));"""
new_fuse = """    __m512 sum = zero;
    for (int h = 0; h < HiddenSize; h += 16) {
        const std::size_t base = static_cast<std::size_t>(h);
        if (h + 16 < HiddenSize) {
            const std::size_t next = base + 16;
            _mm_prefetch(reinterpret_cast<const char*>(our_sub0 + next), _MM_HINT_T0);
            _mm_prefetch(reinterpret_cast<const char*>(their_sub0 + next), _MM_HINT_T0);
        }
        __m512 ours = _mm512_sub_ps(_mm512_loadu_ps(our_src + base), _mm512_loadu_ps(our_sub0 + base));"""
assert old_fuse in s
s = s.replace(old_fuse, new_fuse, 1)
open(p, "w").write(s)
print("prefetch_lite applied")
