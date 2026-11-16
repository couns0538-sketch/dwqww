#!/usr/bin/env python3
"""Variant F (INSTRUMENT ONLY, never a candidate): print the per-root-move node vector.

The engine already accumulates `root_move_nodes_[slot]` for every root move (search.cpp:2041) but
never emits it. This patch prints one line after every finished root iteration:

    info string rootnodes <depth> <uci>:<nodes> <uci>:<nodes> ...

so the whole per-root-move node vector can be compared between a position and its colour mirror.
Nothing about the search changes - only an extra info line - but the pins are still re-measured.

usage: make_variant_f.py BASE_SEARCH_CPP OUT
"""
import sys

src, out = sys.argv[1:3]
text = open(src).read()

# Emit right before the per-iteration bookkeeping that already reads root_move_nodes_ (the
# TmNodeShare block at ~2592). Anchor on the depth-finished point: just before it.
ANCHOR = """        const int iteration_previous_score = previous_score;
        previous_score = score;"""
assert ANCHOR in text

PRINT = """        const int iteration_previous_score = previous_score;
        previous_score = score;
        // INSTRUMENT (swarm seat 06, variant F): the per-root-move node vector for this depth.
        // Nothing else changes; the pins are re-measured anyway.
        if (emit_info) {
            std::uint64_t total_root = 0;
            std::string line = "info string rootnodes " + std::to_string(depth);
            for (std::size_t slot = 0; slot < root_effort_count_; ++slot) {
                total_root += root_move_nodes_[slot];
                line += " " + Board::move_to_uci(root_effort_moves_[slot]) + ":" +
                        std::to_string(root_move_nodes_[slot]);
            }
            line += " total:" + std::to_string(total_root);
            const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
            std::cout << line << std::endl;
        }"""

text = text.replace(ANCHOR, PRINT, 1)
if '#include <string>' not in text:
    text = text.replace('#include <algorithm>', '#include <algorithm>\n#include <string>', 1)
open(out, "w").write(text)
print("wrote", out)
