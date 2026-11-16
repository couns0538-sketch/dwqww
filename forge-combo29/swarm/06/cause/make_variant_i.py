#!/usr/bin/env python3
"""Variant I (INSTRUMENT ONLY): print the MovePicker's SCORE for every root move, before any subtree
is searched.

The question this answers: at the root, do the two sides of a colour-mirrored pair already have DIFFERENT
picker score vectors (history + threat + continuation tables), or are the vectors identical and the
divergence only appears deeper?

If the vectors differ at the root -> the accumulating tables are the cause and the fix direction is clear.
If they are identical at the root -> the cause is below the root, not in the picker's initial scores.

The print is emitted once per root iteration, from inside generate_quiets() when it is the ROOT node, so
the values are exactly what the picker will sort on - nothing is re-derived.

usage: make_variant_i.py BASE_SEARCH_CPP OUT
"""
import sys

src, out = sys.argv[1:3]
text = open(src).read()

# generate_quiets(): the FORGE_SEARCH_SPEED2 loop that scores each quiet. Emit the vector for root nodes.
OLD = """        const QuietScorer scorer(board_, searcher_, ss_);
        for (const Move move : buffer_) {
            push_scored(move, scorer.score(move, check_squares_));
        }"""
NEW = """        const QuietScorer scorer(board_, searcher_, ss_);
        // INSTRUMENT (swarm seat 06, variant I): dump the picker's own score for every move at the ROOT,
        // before any subtree of this iteration is searched. Nothing about the search changes.
        const bool dump_root_picker = (ss_ != nullptr && ss_->ply == 0);
        std::string picker_line;
        for (const Move move : buffer_) {
            const int picker_score = scorer.score(move, check_squares_);
            if (dump_root_picker) {
                picker_line += " " + Board::move_to_uci(move) + ":" + std::to_string(picker_score);
            }
            push_scored(move, picker_score);
        }
        if (dump_root_picker) {
            const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
            std::cout << "info string rootpicker" << picker_line << std::endl;
        }"""
assert OLD in text, "anchor not found"
text = text.replace(OLD, NEW, 1)
if '#include <string>' not in text:
    text = text.replace('#include <algorithm>', '#include <algorithm>\n#include <string>', 1)
open(out, "w").write(text)
print("wrote", out)
