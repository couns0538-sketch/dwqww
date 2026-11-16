"""fast_tt_scan.py : the vectorised four-way key compare that 19-F39 named as the next experiment.

NOT a proposal yet — it is a test. The change:

  before: for (TTEntry& e : cluster.entries) if (e.key32 == key32 && e.occupied()) { found = &e; break; }
  after : load all four key32 fields with one 128-bit gather-free load pattern, compare them at once, then
          check occupied() only for the single matching lane.

TTEntry is 16 bytes with key32 at offset 0, so the four key32 values sit at byte offsets 0, 16, 32, 48 of the
64-byte cluster. Four scalar loads into one __m128i, one _mm_cmpeq_epi32, one movemask. The FIRST match in index
order must win (the original breaks at the first), so take the lowest set bit.

Nothing about the table's contents, replacement policy, generation handling or the snapshot changes.
"""
import re

p = "src/search.cpp"
s = open(p).read()

old = """    TTEntry* found = nullptr;
#pragma GCC unroll 1
    for (TTEntry& entry : cluster.entries) {
        if (entry.key32 == key32 && entry.occupied()) {
            found = &entry;
            break;
        }
    }"""
new = """    TTEntry* found = nullptr;
#if FORGE_SPD_TT_VEC_SCAN
    {
        // One vector compare over the four key32 fields (offsets 0/16/32/48 of the 64-byte cluster),
        // then the occupied() test only on the matching lanes. Lowest index wins, as the loop did.
        const __m128i keys = _mm_setr_epi32(static_cast<int>(cluster.entries[0].key32),
                                           static_cast<int>(cluster.entries[1].key32),
                                           static_cast<int>(cluster.entries[2].key32),
                                           static_cast<int>(cluster.entries[3].key32));
        const __m128i want = _mm_set1_epi32(static_cast<int>(key32));
        const int mask = _mm_movemask_ps(_mm_castsi128_ps(_mm_cmpeq_epi32(keys, want)));
        int lane = 0;
        while (lane < 4 && (mask & (1 << lane)) == 0) ++lane;
        while (lane < 4) {
            if (cluster.entries[static_cast<std::size_t>(lane)].occupied()) {
                found = &cluster.entries[static_cast<std::size_t>(lane)];
                break;
            }
            ++lane;
        }
    }
#else
#pragma GCC unroll 1
    for (TTEntry& entry : cluster.entries) {
        if (entry.key32 == key32 && entry.occupied()) {
            found = &entry;
            break;
        }
    }
#endif"""
assert old in s
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("fast_tt_scan applied")
