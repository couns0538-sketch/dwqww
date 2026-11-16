#!/usr/bin/env python3
"""Variant G (INSTRUMENTED TEST, never a candidate): clear the transposition table before every
root move, so no root move can read a TT entry written by an earlier root move.

Hypothesis this tests. The evidence chain:
  - `go depth N searchmoves <one move>` gives mirror-identical node counts for every root move
    (probe_root_moves.py) - in that call the root is restricted, so each move is the FIRST thing
    searched and the TT is empty.
  - inside the FULL search the same root moves differ (variant F's rootnode vector): 5 of 18 at
    depth 1, with identical capture frontiers and identical results with and without S14.
  - an empty TT is the one thing the restricted call has that the full search does not.
So: the TT is reused ACROSS root moves, the root move order differs between a position and its
mirror (any tie-order difference does that), and therefore a different set of transpositions is
cached when each later move is searched. That would produce exactly the observed picture.

usage: make_variant_g.py BASE_SEARCH_CPP OUT
"""
import sys

src, out = sys.argv[1:3]
text = open(src).read()

# Clear the table at the top of each root move, before the subtree is searched.
ANCHOR = """        const std::uint64_t nodes_before = local_nodes_;
        std::size_t root_effort_index = 0;"""
assert ANCHOR in text

REPL = """        const std::uint64_t nodes_before = local_nodes_;
        // INSTRUMENTED TEST (swarm seat 06, variant G): clear the TT so this root move cannot read
        // anything written by an earlier root move. This ISOLATES root moves exactly like
        // `searchmoves <one move>` does, but keeps the root loop and its ordering intact.
        if (root_node && depth >= 1) shared_.tt.clear();
        std::size_t root_effort_index = 0;"""

text = text.replace(ANCHOR, REPL, 1)
open(out, "w").write(text)
print("wrote", out)
