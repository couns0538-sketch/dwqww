#!/usr/bin/env python3
"""Variant K (INSTRUMENT ONLY): print the transposition KEY and the PAWN key at every root move's node,
plus at the qsearch child, so the two sides of a mirror pair can be compared directly.

Also prints, for the two nodes that differ, the full entry the TT would store: the key32, the bound,
the depth, the score and the eval.

usage: make_variant_k.py BASE_SEARCH_CPP OUT
"""
import sys

src, out = sys.argv[1:3]
text = open(src).read()

# print the key at each root move (alongside the existing move name)
ANCHOR = """        if (root_node && root_effort_index < root_effort_count_)
            root_move_nodes_[root_effort_index] += local_nodes_ - nodes_before;"""
assert ANCHOR in text
NEW = ANCHOR + """
        if (root_node) {
            const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
            std::cout << "info string rootkey " << Board::move_to_uci(move)
                      << " key " << board.key()
                      << " pawnkey " << board.pawn_key()
                      << " nodes " << (local_nodes_ - nodes_before) << std::endl;
        }"""
text = text.replace(ANCHOR, NEW, 1)
if '#include <string>' not in text:
    text = text.replace('#include <algorithm>', '#include <algorithm>\n#include <string>', 1)
open(out, "w").write(text)
print("wrote", out)
