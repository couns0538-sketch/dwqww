#!/usr/bin/env python3
"""Variant D: ROOT WINDOW PURITY. Every root move is searched with a true full window
(-Infinite, Infinite), the root never accumulates alpha, and the root never takes a fail-high
cutoff. Nothing else changes.

Rationale: probe_root_moves.py showed every root move's own subtree is mirror-identical when searched
alone, while the whole-position search is not. The only state that crosses root moves is the
accumulated alpha (search.cpp:2043-2060), so this variant removes exactly that.

Implementation: the root bypasses the PVS / LMR / full-depth-re-search ladder and does one search per
move at new_depth with a full window. best_move is chosen by the highest score, which is now
comparable across moves because every move was searched under the same window.

usage: make_variant_d.py BASE_SEARCH_CPP OUT
"""
import sys

src, out = sys.argv[1:3]
text = open(src).read()

# ---- the search-window ladder inside the move loop, replaced for root nodes -------------
OLD_LADDER = """        bool full_depth_needed = !pv_node || move_count > 1;
        if (mate_moves_ == 0 && board.halfmove_clock() + new_depth < 100 && depth >= 2 &&"""
assert OLD_LADDER in text

NEW_LADDER = """        bool full_depth_needed = !pv_node || move_count > 1;
        if (root_node) {
            // ROOT WINDOW PURITY (swarm seat 06 experiment): search this root move under exactly
            // the window every other root move gets, so no information crosses root moves.
            full_depth_needed = false;
            score = -search(board, ss + 1, new_depth, -Infinite, Infinite, false);
        } else if (mate_moves_ == 0 && board.halfmove_clock() + new_depth < 100 && depth >= 2 &&"""

text = text.replace(OLD_LADDER, NEW_LADDER, 1)

# The old ladder body used `if (...)` with a compound condition; the `else if` keeps it intact.
# Now guard the two trailing ladder calls so they never run at a root node.
OLD_TAIL1 = """        if (full_depth_needed && !aborted_) {
            score = -search(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
        }
        if (pv_node && !aborted_ && (move_count == 1 || score > alpha)) {
            score = -search(board, ss + 1, new_depth, -beta, -alpha, false);
        }"""
NEW_TAIL1 = """        if (!root_node && full_depth_needed && !aborted_) {
            score = -search(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
        }
        if (!root_node && pv_node && !aborted_ && (move_count == 1 || score > alpha)) {
            score = -search(board, ss + 1, new_depth, -beta, -alpha, false);
        }"""
assert OLD_TAIL1 in text
text = text.replace(OLD_TAIL1, NEW_TAIL1, 1)

# ---- the accumulation itself: at a root node alpha never moves and there is no cutoff -----
OLD_ACC = """        if (score > best_score) {
            best_score = score;
            if (score > alpha) {
                best_move = move;
                if (pv_node) {
                    ss->pv[0] = move;
                    std::copy_n((ss + 1)->pv.begin(), (ss + 1)->pv_length, ss->pv.begin() + 1);
                    ss->pv_length = (ss + 1)->pv_length + 1;
                }
                if (score >= beta) {
                    ++ss->cutoff_count;
                    break;
                }
                alpha = score;
            }
        }"""
NEW_ACC = """        if (score > best_score) {
            best_score = score;
            // At the root every move was searched under the same window, so a better score is
            // directly comparable and always becomes the best move; alpha never accumulates and
            // there is no root fail-high cutoff.
            if (root_node || score > alpha) {
                best_move = move;
                if (pv_node) {
                    ss->pv[0] = move;
                    std::copy_n((ss + 1)->pv.begin(), (ss + 1)->pv_length, ss->pv.begin() + 1);
                    ss->pv_length = (ss + 1)->pv_length + 1;
                }
                if (!root_node && score >= beta) {
                    ++ss->cutoff_count;
                    break;
                }
                if (!root_node) alpha = score;
            }
        }"""
assert OLD_ACC in text
text = text.replace(OLD_ACC, NEW_ACC, 1)

open(out, "w").write(text)
print("wrote", out)
