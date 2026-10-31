#!/usr/bin/env python3
"""port_align.py - R13 P2 step 1a: build switch FORGE_ALIGN_WEIGHTS (default 0) on the stack tree (r10fix1 + S1).

With FORGE_ALIGN_WEIGHTS=1, net weight storage that is not in large pages starts on a 64-byte boundary:
- the lock net's float w1 (nnue.cpp, via large_pages::make_weight_array; S1's large-page path is 2 MiB aligned anyway),
- the HalfKA net's weight vectors (nnue_halfka.cpp: ft_weight, ft_bias, per-stack weights/biases, via WeightVector).
With 0 every type and call is S1's (WeightVector = std::vector, make_weight_array = make_array), so the build is the
same code. Weight values and order never change, so nodes are identical in both builds (checked by bench).
Every anchor must match exactly once. LF bytes in, LF bytes out.
usage: python -I -B port_align.py <stack scratch repo>
"""
import sys

root = sys.argv[1]


def edit(rel, pairs):
    p = f'{root}/{rel}'
    s = open(p, 'rb').read().decode()
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, f'{rel}: anchor found {n}x: {old[:80]!r}'
        s = s.replace(old, new)
    assert '\r' not in s
    open(p, 'wb').write(s.encode())


edit('include/forge/large_pages.hpp', [
    ('#include <type_traits>\n',
     '#include <type_traits>\n#include <new>\n#include <vector>\n'),
    ('enum class Kind : unsigned char { Heap, WindowsLarge, LinuxHuge };\n',
     '// FORGE_ALIGN_WEIGHTS (R13 P2 step 1a, build switch, default 0): net weight storage that is not in large pages\n'
     '// starts on a 64-byte boundary (one cache line), so no 64-byte SIMD load of a weight row splits two lines. 0 = the\n'
     '// S1 / lock allocation (new T[n]() and std::vector: 16-byte aligned on MinGW-w64). Large pages are 2 MiB aligned\n'
     '// either way. Weight values and order are unchanged, so search nodes are identical.\n'
     '#ifndef FORGE_ALIGN_WEIGHTS\n#define FORGE_ALIGN_WEIGHTS 0\n#endif\n'
     'inline constexpr std::size_t WeightAlignment = 64;\n'
     '\n'
     'enum class Kind : unsigned char { Heap, WindowsLarge, LinuxHuge, HeapAligned };\n'
     '[[nodiscard]] constexpr bool is_large(Kind kind) { return kind == Kind::WindowsLarge || kind == Kind::LinuxHuge; }\n'),
    ('        if (kind == Kind::Heap) delete[] pointer;\n',
     '        if (kind == Kind::Heap) delete[] pointer;\n'
     '        else if (kind == Kind::HeapAligned) ::operator delete[](static_cast<void*>(pointer), std::align_val_t{WeightAlignment});\n'),
    ('[[nodiscard]] std::string describe(const Report& report, const char* what);\n',
     '// Net weights: make_array, but under FORGE_ALIGN_WEIGHTS the heap block (no large pages, or their fallback) is\n'
     '// 64-byte aligned. The large-page report of a requested attempt is kept.\n'
     'template <class T>\n'
     '[[nodiscard]] Array<T> make_weight_array(std::size_t n, bool large, Report& report) {\n'
     '#if FORGE_ALIGN_WEIGHTS\n'
     '    if (large) {\n'
     '        Array<T> block = make_array<T>(n, true, report);\n'
     '        if (report.ok) return block;\n'
     '    } else {\n'
     '        report = Report{};\n'
     '    }\n'
     '    T* elements = static_cast<T*>(::operator new[](n * sizeof(T), std::align_val_t{WeightAlignment}));\n'
     '    std::uninitialized_value_construct_n(elements, n);\n'
     '    return Array<T>(elements, Deleter{Kind::HeapAligned, n * sizeof(T)});\n'
     '#else\n'
     '    return make_array<T>(n, large, report);\n'
     '#endif\n'
     '}\n'
     '\n'
     '// Allocator for heap weight vectors under FORGE_ALIGN_WEIGHTS (64-byte aligned blocks).\n'
     'template <class T>\n'
     'struct AlignedAllocator {\n'
     '    using value_type = T;\n'
     '    AlignedAllocator() noexcept = default;\n'
     '    template <class U>\n'
     '    AlignedAllocator(const AlignedAllocator<U>&) noexcept {}\n'
     '    [[nodiscard]] T* allocate(std::size_t n) {\n'
     '        return static_cast<T*>(::operator new(n * sizeof(T), std::align_val_t{WeightAlignment}));\n'
     '    }\n'
     '    void deallocate(T* pointer, std::size_t) noexcept { ::operator delete(pointer, std::align_val_t{WeightAlignment}); }\n'
     '    template <class U>\n'
     '    bool operator==(const AlignedAllocator<U>&) const noexcept { return true; }\n'
     '    template <class U>\n'
     '    bool operator!=(const AlignedAllocator<U>&) const noexcept { return false; }\n'
     '};\n'
     '#if FORGE_ALIGN_WEIGHTS\n'
     'template <class T>\n'
     'using WeightVector = std::vector<T, AlignedAllocator<T>>;\n'
     '#else\n'
     'template <class T>\n'
     'using WeightVector = std::vector<T>;\n'
     '#endif\n'
     '\n'
     '[[nodiscard]] std::string describe(const Report& report, const char* what);\n'),
])

edit('src/nnue.cpp', [
    ('        w.w1 = large_pages::make_array<float>(W1Count, false, unused);\n',
     '        w.w1 = large_pages::make_weight_array<float>(W1Count, false, unused);\n'),
    ('    const bool is_large = w.w1.get_deleter().kind != large_pages::Kind::Heap;\n',
     '    const bool is_large = large_pages::is_large(w.w1.get_deleter().kind);\n'),
    ('    auto fresh = large_pages::make_array<float>(W1Count, large, report);\n',
     '    auto fresh = large_pages::make_weight_array<float>(W1Count, large, report);\n'),
])

edit('src/nnue_halfka.cpp', [
    ('struct Stack {\n    std::vector<std::int32_t> b1, b2;\n',
     'struct Stack {\n    large_pages::WeightVector<std::int32_t> b1, b2;\n'),
    ('    std::vector<std::int8_t> w1, w2, w3;  // row-major [output][padded input]\n',
     '    large_pages::WeightVector<std::int8_t> w1, w2, w3;  // row-major [output][padded input]\n'),
    ('    std::vector<std::int8_t> w1b, w2b;\n',
     '    large_pages::WeightVector<std::int8_t> w1b, w2b;\n'),
    ('    std::vector<std::int16_t> ft_bias;\n    std::vector<std::int8_t> ft_weight;  // NumFeatures rows of l1 values\n',
     '    large_pages::WeightVector<std::int16_t> ft_bias;\n'
     '    large_pages::WeightVector<std::int8_t> ft_weight;  // NumFeatures rows of l1 values\n'),
    ('std::vector<std::int8_t> regroup(const std::vector<std::int8_t>& w, int out, int in, int outp) {\n'
     '    std::vector<std::int8_t> r(',
     'large_pages::WeightVector<std::int8_t> regroup(const large_pages::WeightVector<std::int8_t>& w, int out, int in, int outp) {\n'
     '    large_pages::WeightVector<std::int8_t> r('),
    ('    template <typename T> bool array(std::vector<T>& out, std::size_t n) {\n'
     '        out.resize(n);\n'
     '        return raw(out.data(), n * sizeof(T));\n',
     '    template <typename V> bool array(V& out, std::size_t n) {\n'
     '        out.resize(n);\n'
     '        return raw(out.data(), n * sizeof(typename V::value_type));\n'),
    ('void layer(const std::uint8_t* x, int in, const std::vector<std::int8_t>& w, const std::vector<std::int8_t>& wb,\n'
     '           const std::vector<std::int32_t>& b, int out, int outp, std::int32_t* s) {\n',
     'void layer(const std::uint8_t* x, int in, const large_pages::WeightVector<std::int8_t>& w,\n'
     '           const large_pages::WeightVector<std::int8_t>& wb, const large_pages::WeightVector<std::int32_t>& b, int out,\n'
     '           int outp, std::int32_t* s) {\n'),
])
s = open(f'{root}/src/nnue_halfka.cpp', 'rb').read().decode()
if '#include "forge/large_pages.hpp"' not in s:
    anchor = '#include "forge/nnue_halfka.hpp"\n'
    assert s.count(anchor) == 1
    s = s.replace(anchor, anchor + '#include "forge/large_pages.hpp"\n')
    open(f'{root}/src/nnue_halfka.cpp', 'wb').write(s.encode())
print('port_align: all anchors applied')
