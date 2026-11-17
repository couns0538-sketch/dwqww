// Census of the compiled-in book, independent of the walk.
//
// Build (from forge-combo29/):
//   g++ -std=c++20 -O2 -Iinclude -DFORGE_NNUE_HIDDEN=256 \
//       -DFORGE_NNUE_WEIGHTS=\"$PWD/src/nnue_weights.inc\" \
//       swarm/65/scripts/book_census.cpp src/board.cpp src/bitboard.cpp src/book.cpp \
//       src/eval.cpp src/eval_params.cpp src/nnue.cpp -o /tmp/book_census -lpthread
//
// Reports: total entries, distinct keys, duplicate (key,move) pairs, weight
// distribution, castling-encoded moves, promotion-encoded moves, zero-weight
// entries, and the sorted-order invariant that `candidates()` relies on.

#include "forge/board.hpp"
#include "forge/book.hpp"

#include <algorithm>
#include <cstdio>
#include <map>
#include <set>
#include <tuple>

int main() {
    forge::book::Book book;
    book.load_embedded();
    const auto& entries = book.entries();

    std::set<std::uint64_t> keys;
    std::set<std::pair<std::uint64_t, std::uint16_t>> unique_key_move;
    std::map<std::uint16_t, int> weight_hist;
    int zero_weight = 0;
    int promotion_encoded = 0;
    int castle_encoded = 0;
    int nonsorted = 0;
    for (std::size_t i = 0; i < entries.size(); ++i) {
        const auto& e = entries[i];
        keys.insert(e.key);
        unique_key_move.insert({e.key, e.move});
        ++weight_hist[e.weight];
        if (e.weight == 0) ++zero_weight;
        if (((e.move >> 12) & 7) != 0) ++promotion_encoded;
        if (i > 0 && entries[i - 1].key > e.key) ++nonsorted;
        // from == to is the encoding of an all-zero move: decodes to none.
        if ((e.move & 0xFFFU) == 0) ++castle_encoded;  // a1a1 placeholder, counted separately below
    }

    std::printf("entries           %zu\n", entries.size());
    std::printf("distinct_keys     %zu\n", keys.size());
    std::printf("distinct_key_move %zu\n", unique_key_move.size());
    std::printf("exact_duplicates  %zu\n", entries.size() - unique_key_move.size());
    std::printf("zero_weight       %d\n", zero_weight);
    std::printf("promotion_encoded %d\n", promotion_encoded);
    std::printf("entries_out_of_order %d\n", nonsorted);

    std::printf("\nweight histogram (weight:count, top 20 by count):\n");
    std::vector<std::pair<int, std::uint16_t>> by_count;
    for (const auto& [w, c] : weight_hist) by_count.push_back({c, w});
    std::sort(by_count.rbegin(), by_count.rend());
    for (std::size_t i = 0; i < by_count.size() && i < 20; ++i) {
        std::printf("  %5u: %d\n", by_count[i].second, by_count[i].first);
    }
    std::printf("distinct weights %zu\n", weight_hist.size());

    // Per-key move-count histogram.
    std::map<std::uint64_t, int> per_key;
    for (const auto& e : unique_key_move) ++per_key[e.first];
    std::map<int, int> fanout;
    for (const auto& [k, c] : per_key) ++fanout[c];
    std::printf("\nmoves per key (moves:keys):\n");
    for (const auto& [m, k] : fanout) std::printf("  %d: %d\n", m, k);
    return 0;
}
