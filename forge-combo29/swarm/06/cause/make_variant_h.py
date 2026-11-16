#!/usr/bin/env python3
"""Variant H: make the move generator's EMISSION ORDER mirror-invariant.

This is the one lever the one-position dump points at, and it is a different patch from all seven
already tried (those changed the SORT or the picker; this changes the seed order the generator hands over).

`fill_pseudo_legal` walks squares with `pop_lsb`, i.e. lowest square index first (a1 -> h8). Under a colour
mirror (square ^ 56) that order maps to itself only for vertically symmetric positions, so the two sides of a
mirrored pair receive the moves in a different sequence, which alpha-beta then prunes differently.

This variant keeps the walk but, at the END of generation, re-sorts the emitted list into a canonical order
expressed in the MOVER's own frame: by (relative from-square, relative to-square, promotion). Since the engine's
`Move` carries `from`/`to` as absolute squares, the relative key is `x ^ 56`, which is exactly the mirror.

The reorder is a stable insertion reorder over the same list, so the move SET is untouched - perft must be
identical, and that is the check that it is a pure reorder.

usage: make_variant_h.py BASE_BOARD_CPP OUT
"""
import sys

src, out = sys.argv[1:3]
text = open(src).read()

# Insert a canonical reorder helper and call it at the end of fill_pseudo_legal.
ANCHOR = """template <Board::GenMode Mode>
void fill_pseudo_legal(const Board& board, MoveList& moves) {"""
assert ANCHOR in text

HELPER = """// Symmetry experiment (swarm seat 06): the generator walks squares lowest-index first (pop_lsb, a1 -> h8).
// A colour mirror maps that walk to a different sequence, so a mirrored pair receives the same moves in a
// different order and alpha-beta prunes different subsets. Reorder the finished list into a canonical order in
// the MOVER's frame (square ^ 56). Same move SET, so perft must be unchanged - that is the check.
inline void canonical_order(MoveList& moves, std::size_t first) {
    const std::size_t n = moves.size();
    if (n <= first + 1) return;
    auto key = [](const Move m) {
        const unsigned f = static_cast<unsigned>(m.from ^ 56U);
        const unsigned t = static_cast<unsigned>(m.to ^ 56U);
        return (f << 16U) | (t << 8U) | static_cast<unsigned>(m.promotion);
    };
    // insertion sort: the list is short (<= 218) and this runs once per node
    for (std::size_t i = first + 1; i < n; ++i) {
        const Move cur = moves[i];
        const unsigned ck = key(cur);
        std::size_t j = i;
        while (j > first && key(moves[j - 1]) > ck) {
            moves[j] = moves[j - 1];
            --j;
        }
        moves[j] = cur;
    }
}

template <Board::GenMode Mode>
void fill_pseudo_legal(const Board& board, MoveList& moves) {"""
text = text.replace(ANCHOR, HELPER, 1)

open(out, "w").write(text)
# append the canonical reorder at the end of fill_pseudo_legal (the closing brace before generate_pseudo_legal)
OLD_TAIL = """        }
    }
}

void Board::generate_pseudo_legal(MoveList& moves, GenMode mode) const {"""
NEW_TAIL = """        }
    }
    canonical_order(moves, 0);
}

void Board::generate_pseudo_legal(MoveList& moves, GenMode mode) const {"""
text2 = open(out).read()
assert OLD_TAIL in text2
text2 = text2.replace(OLD_TAIL, NEW_TAIL, 1)
open(out, "w").write(text2)
print("appended reorder call")
print("wrote", out)
