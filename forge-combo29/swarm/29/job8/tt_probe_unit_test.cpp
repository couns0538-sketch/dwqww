// Direct unit test for the 29-F12 / 29-F14 TT probe changes, aimed at the fault class my search-output stress
// test could NOT reach (29-N9): an unoccupied slot whose key32 matches, ahead of an occupied matching slot.
//
// IMPORTANT: this program does not assert an absolute expectation about replacement, because the engine's
// replacement policy is what it is; it prints the OBSERVED behaviour of the table it was linked against, so the
// base and the patched build can be compared line by line. Identical output from both builds is the property
// under test. Uses the PUBLIC interface only; no engine header is modified.

#include "forge/search.hpp"

#include <cstdint>
#include <cstdio>
#include <map>
#include <vector>

using namespace forge;

namespace {
std::uint64_t g_stored_depths_mask = 0;
}

int main() {
    TranspositionTable tt(1);
    std::vector<std::uint64_t> four;
    std::map<std::size_t, std::vector<std::uint64_t>> by_cluster;
    for (std::uint64_t k = 1; k < 4000000ULL; ++k) {
        const std::size_t idx = static_cast<std::size_t>(
            (static_cast<unsigned __int128>(k) * tt.cluster_count()) >> 64U);
        auto& v = by_cluster[idx];
        v.push_back(k);
        if (v.size() == 4) { four = v; break; }
    }
    if (four.size() != 4) { std::printf("SKIP\n"); return 0; }
    std::printf("cluster-mate keys:");
    for (auto k : four) std::printf(" %llu", (unsigned long long)k);
    std::printf("\n");

    for (std::size_t i = 0; i < 4; ++i) {
        const TTProbe p = tt.probe(four[i]);
        tt.store(p, four[i], 10 + (int)i, 0, Move{}, 5 + (int)i, BoundExact, false, 0);
        std::printf("after storing key %llu (depth %zu):\n", (unsigned long long)four[i], 5 + i);
        for (std::size_t j = 0; j < 4; ++j) {
            const TTProbe q = tt.probe(four[j]);
            std::printf("   probe key %llu -> hit=%d depth=%d\n",
                        (unsigned long long)four[j], (int)q.hit, (int)q.entry.depth);
        }
    }
    // Overflow a full cluster: a fifth key must be a miss, and the four-mate picture after it must match base.
    const std::size_t cluster0 = static_cast<std::size_t>(
        (static_cast<unsigned __int128>(four[0]) * tt.cluster_count()) >> 64U);
    for (std::uint64_t k = 4000000ULL; k < 9000000ULL; ++k) {
        const std::size_t idx = static_cast<std::size_t>(
            (static_cast<unsigned __int128>(k) * tt.cluster_count()) >> 64U);
        if (idx != cluster0) continue;
        bool mate = false;
        for (auto f : four) if (f == k) mate = true;
        if (mate) continue;
        const TTProbe p = tt.probe(k);
        std::printf("stranger key %llu in the same cluster: hit=%d\n", (unsigned long long)k, (int)p.hit);
        tt.store(p, k, 99, 0, Move{}, 12, BoundExact, false, 0);
        std::printf("after storing the stranger:\n");
        for (std::size_t j = 0; j < 4; ++j) {
            const TTProbe q = tt.probe(four[j]);
            std::printf("   probe key %llu -> hit=%d depth=%d\n",
                        (unsigned long long)four[j], (int)q.hit, (int)q.entry.depth);
        }
        break;
    }
    return 0;
}
