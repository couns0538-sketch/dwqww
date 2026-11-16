#!/usr/bin/env python3
"""Variant L (INSTRUMENT ONLY): log every node the search visits, canonically identified.

For the depth-4 bisection: a node is identified by its NORMALISED position, so "the same position
visited on both sides" is decidable. Normalisation folds the colour mirror: take the position's FEN,
and use min(fen, mirror(fen)) as the identity. That way a position and its mirror get the SAME id,
which is exactly the comparison the question needs (the two searches are mirror images, so a node on
one side corresponds to the mirrored node on the other).

Also prints, per node: the static evaluation and whether it is in check.

usage: make_variant_l.py BASE_SEARCH_CPP OUT
"""
import sys

src, out = sys.argv[1:3]
text = open(src).read()

# emit a per-node line from Worker::search, right after the static eval is known is complicated;
# simpler and sufficient: emit at node entry with the position and its static evaluation.
ANCHOR = """    ++local_nodes_;
    seldepth_ = std::max(seldepth_, ply);"""
assert ANCHOR in text

NEW = """    ++local_nodes_;
    seldepth_ = std::max(seldepth_, ply);
    // INSTRUMENT (swarm seat 06, variant L): log this node's position, ply, static eval and in-check
    // flag. Canonicalisation (mirror folding) is done in the Python analyser, not here.
    {
        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
        std::cout << "info string node ply " << ply
                  << " eval " << static_evaluate(board, ss)
                  << " check " << (board.in_check() ? 1 : 0)
                  << " fen " << board.fen() << std::endl;
    }"""
text = text.replace(ANCHOR, NEW, 1)
if '#include <functional>' not in text:
    text = text.replace('#include <algorithm>', '#include <algorithm>\n#include <functional>\n#include <string>', 1)
open(out, "w").write(text)
print("wrote", out)
