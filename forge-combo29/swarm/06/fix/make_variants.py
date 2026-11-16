#!/usr/bin/env python3
"""Produce the three symmetric-ordering variants of src/search.cpp for measurement.

V0 = base (unchanged)
VA = "tie-break only in pick_best": equal scores are ordered by a MIRROR-INVARIANT key
     (relative from-square, then relative to-square), used in both the first-four scan and
     the std::stable_sort of the tail. No other change.
VB = VA plus the same canonical order applied at generation time (sort_moves order), which is
     the closest this engine has to "stable_sort at the root" - the root goes through the same
     MovePicker, there is no separate root sort in search.cpp.

usage: make_variants.py BASE_SEARCH_CPP OUT_A OUT_B
"""
import sys

src, out_a, out_b = sys.argv[1:4]
text = open(src).read()

HELPER_ANCHOR = """    // Most nodes need only the first few moves: select those on demand and
    // sort the remainder once if the search gets that far."""

HELPER = """    // Symmetry patch (swarm seat 06): a canonical order for EQUAL move scores, expressed in the
    // mover's own frame (square ^ 56 flips the board without touching the side to move), so a
    // position and its colour mirror break every tie the same way. Without this, equal-scored
    // moves inherit the generator's a1-first traversal order, which a mirror changes.
    [[nodiscard]] static std::uint16_t tie_key(const Move move) {
        const unsigned rel_from = static_cast<unsigned>(move.from ^ 56U);
        const unsigned rel_to = static_cast<unsigned>(move.to ^ 56U);
        return static_cast<std::uint16_t>((rel_from << 8U) | rel_to);
    }

    // Most nodes need only the first few moves: select those on demand and
    // sort the remainder once if the search gets that far."""

assert HELPER_ANCHOR in text
va = text.replace(HELPER_ANCHOR, HELPER, 1)

# 1) first-four scan: replace the scalar tail loop comparison with a (score, tie_key) lexicographic one
OLD_TAIL = """                for (; i < n; ++i) {
                    const int score = moves_[i].score;
                    if (score > best_score) {
                        best_score = score;
                        best = i;
                    }
                }"""
NEW_TAIL = """                std::uint16_t best_key = tie_key(moves_[best].move);
                for (; i < n; ++i) {
                    const int score = moves_[i].score;
                    const std::uint16_t key = tie_key(moves_[i].move);
                    if (score > best_score || (score == best_score && key < best_key)) {
                        best_score = score;
                        best_key = key;
                        best = i;
                    }
                }"""
assert OLD_TAIL in va
va = va.replace(OLD_TAIL, NEW_TAIL, 1)

# 2) the AVX fast path picks the FIRST max of a chunk; keep it (it is a lower bound on the best
#    tie_key only if the chunk's max score beats the running best). Make it consistent by
#    re-scanning a chunk when its max ties the running best score.
OLD_CHUNK = """                    if (chunk_max > best_score) {
                        const __m128i equal = _mm_cmpeq_epi32(scores, _mm_set1_epi32(chunk_max));
                        const int mask = _mm_movemask_ps(_mm_castsi128_ps(equal));
                        best = i + static_cast<std::size_t>(__builtin_ctz(mask));
                        best_score = chunk_max;
                    }"""
NEW_CHUNK = """                    if (chunk_max >= best_score) {
                        // Walk the chunk in index order so the tie_key rule sees every tie.
                        const __m128i equal = _mm_cmpeq_epi32(scores, _mm_set1_epi32(chunk_max));
                        const int mask = _mm_movemask_ps(_mm_castsi128_ps(equal));
                        int bits = mask;
                        std::uint16_t best_key_local = tie_key(moves_[best].move);
                        while (bits != 0) {
                            const int lane = __builtin_ctz(static_cast<unsigned>(bits));
                            const std::size_t idx = i + static_cast<std::size_t>(lane);
                            if (chunk_max > best_score) {
                                best = idx;
                                best_score = chunk_max;
                                best_key_local = tie_key(moves_[idx].move);
                            } else if (tie_key(moves_[idx].move) < best_key_local) {
                                best = idx;
                                best_key_local = tie_key(moves_[idx].move);
                            }
                            bits &= bits - 1;
                        }
                    }"""
assert OLD_CHUNK in va
va = va.replace(OLD_CHUNK, NEW_CHUNK, 1)

# 3) the tail sort: stable_sort with the lexicographic (score, tie_key) comparator
OLD_SORT = """                std::sort(moves_.begin() + static_cast<std::ptrdiff_t>(index_),
                          moves_.begin() + static_cast<std::ptrdiff_t>(count_),
                          [](const Scored& a, const Scored& b) { return a.score > b.score; });"""
NEW_SORT = """                std::stable_sort(moves_.begin() + static_cast<std::ptrdiff_t>(index_),
                                 moves_.begin() + static_cast<std::ptrdiff_t>(count_),
                                 [](const Scored& a, const Scored& b) {
                                     if (a.score != b.score) return a.score > b.score;
                                     return tie_key(a.move) < tie_key(b.move);
                                 });"""
assert OLD_SORT in va
va = va.replace(OLD_SORT, NEW_SORT, 1)

# VA needs <cstdint> / <climits> for the new code
assert '#include <algorithm>' in va
va = va.replace('#include <algorithm>', '#include <algorithm>\n#include <climits>\n#include <cstdint>', 1)
open(out_a, 'w').write(va)

# VB: start from VA and additionally order the generated move list itself, so the input order
# fed to pick_best is already canonical (this is the "stable_sort at the root" analogue).
vb = va
OLD_GEN_TAIL = """        index_ = quiet_start();
        count_ = quiet_start();"""
if OLD_GEN_TAIL in vb:
    vb = vb.replace(OLD_GEN_TAIL, OLD_GEN_TAIL, 1)

# order the whole freshly generated list canonically before scoring is applied
OLD_PUSH = """    void push_scored(Move move, int score) {"""
# Instead of touching push_scored (scores are not known yet), insert the canonical ordering in
# sort_moves(): sort by tie_key first so scores are then applied over a fixed base order.
OLD_SORTMOVES = """    void sort_moves() {
        list_start_ = index_;
        sorted_ = false;
    }"""
NEW_SORTMOVES = """    void sort_moves() {
        list_start_ = index_;
        // Symmetry patch (VB): put the generated list into a canonical, mirror-invariant order
        // before any score is applied, so equal-scored moves inherit a fixed base order that a
        // colour mirror reproduces exactly.
        const std::size_t first = quiet_start();
        if (count_ > first + 1) {
            std::stable_sort(moves_.begin() + static_cast<std::ptrdiff_t>(first),
                             moves_.begin() + static_cast<std::ptrdiff_t>(count_),
                             [](const Scored& a, const Scored& b) { return tie_key(a.move) < tie_key(b.move); });
        }
        sorted_ = false;
    }"""
assert OLD_SORTMOVES in vb
vb = vb.replace(OLD_SORTMOVES, NEW_SORTMOVES, 1)
open(out_b, 'w').write(vb)
print("wrote", out_a, "and", out_b)
