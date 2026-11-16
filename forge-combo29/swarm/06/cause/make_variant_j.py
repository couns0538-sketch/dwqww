#!/usr/bin/env python3
"""Variant J (INSTRUMENT ONLY): at the ROOT of a depth-1 search, log each move as it is tried, with its
own node delta and how many of those nodes were qsearch nodes.

The question: the whole asymmetry is already present as an 8-vs-9 node difference at depth 1 with
identical scores and identical picker vectors. At depth 1 the only things that can differ are
  (a) a move tried on one side and not the other, or
  (b) a different number of qsearch nodes under the same move.
So count exactly those.

Implementation: a thread-local counter `g_logged` for qsearch entries taken at root-child ply, plus a
per-root-move log line emitted right after each root move's subtree is searched. Nothing about the
search changes; pins are re-measured anyway.

usage: make_variant_j.py BASE_SEARCH_CPP OUT
"""
import sys

src, out = sys.argv[1:3]
text = open(src).read()

# 1) a counter for qsearch nodes counted per root move
COUNTER_ANCHOR = """int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {"""
COUNTER = """namespace { thread_local std::uint64_t g_qnodes_since_root_move = 0; }

int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {
    ++g_qnodes_since_root_move;"""
assert COUNTER_ANCHOR in text
text = text.replace(COUNTER_ANCHOR, COUNTER, 1)

# 2) root-move logging: reset the counter before the subtree, emit after
OLD = """        const std::uint64_t nodes_before = local_nodes_;
        std::size_t root_effort_index = 0;"""
NEW = """        const std::uint64_t nodes_before = local_nodes_;
        const std::uint64_t qnodes_before = g_qnodes_since_root_move;
        std::size_t root_effort_index = 0;"""
assert OLD in text
text = text.replace(OLD, NEW, 1)

OLD2 = """        if (root_node && root_effort_index < root_effort_count_)
            root_move_nodes_[root_effort_index] += local_nodes_ - nodes_before;
"""
NEW2 = """        if (root_node && root_effort_index < root_effort_count_)
            root_move_nodes_[root_effort_index] += local_nodes_ - nodes_before;
        if (root_node) {
            const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
            std::cout << "info string rootmove " << Board::move_to_uci(move)
                      << " nodes " << (local_nodes_ - nodes_before)
                      << " qnodes " << (g_qnodes_since_root_move - qnodes_before)
                      << " score " << score
                      << " depth " << depth
                      << " n " << move_count << std::endl;
        }
"""
assert OLD2 in text
text = text.replace(OLD2, NEW2, 1)

if '#include <string>' not in text:
    text = text.replace('#include <algorithm>', '#include <algorithm>\n#include <string>', 1)
open(out, "w").write(text)
print("wrote", out)
