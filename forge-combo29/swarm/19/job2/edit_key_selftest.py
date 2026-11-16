"""edit_key_selftest.py : adds a hidden `keycheck` command that prints the cached material key and the value
computed from scratch, for the current position. Test-only edit on a scratch copy, not part of the patch.

`keycheck` output:  KEYCHECK <cached> <computed> <fen>
If the two ever differ, the cache is wrong on that position.
"""

p = "src/uci.cpp"
s = open(p).read()
old = """        } else if (command == "bench") {"""
new = """        } else if (command == "keycheck") {
            // scratch-only: compare the cached material key with a from-scratch computation
            const std::uint64_t cached = board.material_key();
            const std::uint64_t computed = board.compute_material_key();
            std::cout << "KEYCHECK " << cached << " " << computed << " " << board.fen() << std::endl;
        } else if (command == "bench") {"""
assert old in s
s = s.replace(old, new, 1)
open(p, "w").write(s)

# compute_material_key is private; expose it for the scratch build only
h = "include/forge/board.hpp"
t = open(h).read()
t = t.replace("""    [[nodiscard]] std::uint64_t compute_material_key() const;""",
"""public:
    [[nodiscard]] std::uint64_t compute_material_key() const;
private:""", 1)
open(h, "w").write(t)
print("edit_key_selftest applied")
