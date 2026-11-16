"""edit_material_key.py : test-only edit (NOT a proposal). Memoises material_key per (board key).

This is a probe of how much headroom the material_key() loop has, not a patch candidate: the memo is
keyed on the full position key, which is not a sound identity for material in general, and it lives in
thread_local state, which is a real change in behaviour. Its only purpose is the headroom number.
"""

p = "src/search.cpp"
s = open(p).read()
old = """[[nodiscard]] std::uint64_t material_key(const Board& board) {
    std::uint64_t key = 0;"""
new = """thread_local std::uint64_t t_last_board_key = ~0ULL;
thread_local std::uint64_t t_last_material = 0;
[[nodiscard]] std::uint64_t material_key(const Board& board) {
    if (board.key() == t_last_board_key) return t_last_material;
    std::uint64_t key = 0;"""
assert old in s
s = s.replace(old, new, 1)
old2 = """    return key * 0x9E3779B97F4A7C15ULL;
}

// Hash of non-pawn piece placements of one side"""
new2 = """    t_last_board_key = board.key();
    t_last_material = key * 0x9E3779B97F4A7C15ULL;
    return t_last_material;
}

// Hash of non-pawn piece placements of one side"""
assert old2 in s
s = s.replace(old2, new2, 1)
open(p, "w").write(s)
print("edit_material_key applied")
