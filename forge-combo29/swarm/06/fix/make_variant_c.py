#!/usr/bin/env python3
"""Variant C: the COMPLETE mirror-invariant tie-break, including `seeded_` in push_scored.

VA patched pick_best's scan and the tail sort but missed push_scored, which records the FIRST
arrival of the maximum score ("seeded") and hands that move out first. With ties present, the first
arrival is decided by generator order, so VA still breaks ties by position. VC adds the same
(mirror-invariant) tie_key rule to the seeding decision.

usage: make_variant_c.py BASE_SEARCH_CPP OUT
"""
import sys

src, out = sys.argv[1:3]
text = open(src).read()

HELPER_ANCHOR = """    // Most nodes need only the first few moves: select those on demand and
    // sort the remainder once if the search gets that far."""
HELPER = """    // Symmetry patch (swarm seat 06): a canonical order for EQUAL move scores, expressed in the
    // mover's own frame (square ^ 56 flips the board without touching the side to move), so a
    // position and its colour mirror break every tie the same way.
    [[nodiscard]] static std::uint16_t tie_key(const Move move) {
        const unsigned rel_from = static_cast<unsigned>(move.from ^ 56U);
        const unsigned rel_to = static_cast<unsigned>(move.to ^ 56U);
        return static_cast<std::uint16_t>((rel_from << 8U) | rel_to);
    }

    // Most nodes need only the first few moves: select those on demand and
    // sort the remainder once if the search gets that far."""
assert HELPER_ANCHOR in text
c = text.replace(HELPER_ANCHOR, HELPER, 1)

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
assert OLD_TAIL in c
c = c.replace(OLD_TAIL, NEW_TAIL, 1)

OLD_CHUNK = """                    if (chunk_max > best_score) {
                        const __m128i equal = _mm_cmpeq_epi32(scores, _mm_set1_epi32(chunk_max));
                        const int mask = _mm_movemask_ps(_mm_castsi128_ps(equal));
                        best = i + static_cast<std::size_t>(__builtin_ctz(mask));
                        best_score = chunk_max;
                    }"""
NEW_CHUNK = """                    if (chunk_max >= best_score) {
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
assert OLD_CHUNK in c
c = c.replace(OLD_CHUNK, NEW_CHUNK, 1)

OLD_SORT = """                std::sort(moves_.begin() + static_cast<std::ptrdiff_t>(index_),
                          moves_.begin() + static_cast<std::ptrdiff_t>(count_),
                          [](const Scored& a, const Scored& b) { return a.score > b.score; });"""
NEW_SORT = """                std::stable_sort(moves_.begin() + static_cast<std::ptrdiff_t>(index_),
                                 moves_.begin() + static_cast<std::ptrdiff_t>(count_),
                                 [](const Scored& a, const Scored& b) {
                                     if (a.score != b.score) return a.score > b.score;
                                     return tie_key(a.move) < tie_key(b.move);
                                 });"""
assert OLD_SORT in c
c = c.replace(OLD_SORT, NEW_SORT, 1)

OLD_SEED = """    void push_scored(Move move, int score) {
        if (!seeded_ || score > seeded_score_) {
            seeded_ = true;
            seeded_score_ = score;
            seeded_at_ = count_;
        }
        moves_[count_++] = Scored{move, score};
    }"""
NEW_SEED = """    void push_scored(Move move, int score) {
        // The seed is the move handed out first. It must be chosen by the same canonical rule as
        // pick_best, otherwise the first arrival of the maximum score - a generator-order fact -
        // decides which of several equal-scoring moves is searched first.
        if (!seeded_ || score > seeded_score_ ||
            (score == seeded_score_ && tie_key(move) < tie_key(moves_[seeded_at_].move))) {
            seeded_ = true;
            seeded_score_ = score;
            seeded_at_ = count_;
        }
        moves_[count_++] = Scored{move, score};
    }"""
assert OLD_SEED in c
c = c.replace(OLD_SEED, NEW_SEED, 1)

c = c.replace('#include <algorithm>', '#include <algorithm>\n#include <cstdint>', 1)
open(out, "w").write(c)
print("wrote", out)
