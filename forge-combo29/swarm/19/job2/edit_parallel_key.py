"""edit_parallel_key.py : test-only edit used to size the effect of the de-serialised material key.

Rewrites material_key()'s Horner chain as a sum of independent products with precomputed powers of the
multiplier. Identical value modulo 2^64 (multiplication distributes over addition), but the ten
multiplications become independent instead of a ten-deep dependency chain. Used only to check the size of
the effect before writing the patch file; the patch itself is job2/optimize_material_key.patch.txt.
"""

p = "src/search.cpp"
s = open(p).read()
old = """[[nodiscard]] std::uint64_t material_key(const Board& board) {
    std::uint64_t key = 0;
    for (const Color color : {White, Black}) {
        for (int type = Pawn; type <= Queen; ++type) {
            key = key * 1099511628211ULL + static_cast<std::uint64_t>(popcount(board.pieces(color, static_cast<PieceType>(type))) + 1);
        }
    }
    return key * 0x9E3779B97F4A7C15ULL;
}"""
new = """[[nodiscard]] std::uint64_t material_key(const Board& board) {
    constexpr std::uint64_t P = 1099511628211ULL;
    constexpr std::uint64_t w[10] = {
        P * P * P * P * P * P * P * P * P, P * P * P * P * P * P * P * P, P * P * P * P * P * P * P,
        P * P * P * P * P * P, P * P * P * P * P, P * P * P * P, P * P * P, P * P, P, 1ULL};
    std::uint64_t sum = 0;
    int i = 0;
    for (const Color color : {White, Black}) {
        for (int type = Pawn; type <= Queen; ++type) {
            sum += w[i++] * static_cast<std::uint64_t>(popcount(board.pieces(color, static_cast<PieceType>(type))) + 1);
        }
    }
    return sum * 0x9E3779B97F4A7C15ULL;
}"""
assert old in s
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("edit_parallel_key applied")
