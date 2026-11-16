"""instrument_tt.py : scratch-only counters inside TranspositionTable::probe_body.

Counts, to split the probe's 5.77 % into its parts before proposing anything:
  T_CALLS       every probe
  T_HIT         matched key32 and occupied  (returns on the hit path)
  T_HIT_SLOT    which slot the hit was found in (0..3), as four counters
  T_STALE_GEN   hits whose generation differed, so a write to the entry happened
  T_FULL        misses where every slot was occupied, so the age/depth scan ran
  T_FIRST_EMPTY which slot the first-empty short-circuit returned from (0..3)
  T_EMPTY_NONE  misses that found no empty slot (impossible given T_FULL, kept as a cross-check)
"""
import re

p = "src/search.cpp"
s = open(p).read()

s = s.replace("""#if FORGE_SPD_TT_NOTLS
template <bool TakeLock>
TTProbe TranspositionTable::probe_body(std::uint64_t key) const {
    TTCluster& cluster = cluster_for(key);""",
"""struct TTCounters {
    std::uint64_t calls = 0, hit = 0, stale_gen = 0, full = 0, empty_none = 0;
    std::uint64_t hit_slot[4] = {0, 0, 0, 0};
    std::uint64_t empty_slot[4] = {0, 0, 0, 0};
};
inline TTCounters& tt_counters() {
    static TTCounters c;
    return c;
}

#if FORGE_SPD_TT_NOTLS
template <bool TakeLock>
TTProbe TranspositionTable::probe_body(std::uint64_t key) const {
    TTCounters& tc = tt_counters();
    ++tc.calls;
    TTCluster& cluster = cluster_for(key);""", 1)

s = s.replace("""    if (found != nullptr) {
        // Reused entries remain recent even when search returns a TT cutoff.
        if (found->generation() != generation) {""",
"""    if (found != nullptr) {
        ++tc.hit;
        ++tc.hit_slot[static_cast<std::size_t>(found - cluster.entries.data())];
        // Reused entries remain recent even when search returns a TT cutoff.
        if (found->generation() != generation) {
            ++tc.stale_gen;""", 1)

s = s.replace("""    for (TTEntry& entry : cluster.entries) {
        if (!entry.occupied()) return snapshot(entry, false);
        const int age = static_cast<int>((32U + generation - entry.generation()) & 31U);""",
"""    for (TTEntry& entry : cluster.entries) {
        if (!entry.occupied()) {
            ++tc.empty_slot[static_cast<std::size_t>(&entry - cluster.entries.data())];
            return snapshot(entry, false);
        }
        const int age = static_cast<int>((32U + generation - entry.generation()) & 31U);""", 1)

s = s.replace("""    return snapshot(*replace, false);
}

TTProbe TranspositionTable::probe(std::uint64_t key) const""",
"""    ++tc.full;
    return snapshot(*replace, false);
}

TTProbe TranspositionTable::probe(std::uint64_t key) const""", 1)

s = s.replace("#include <algorithm>", "#include <algorithm>\n#include <cstdio>", 1)
s += """
namespace forge {
void dump_tt_counters() {
    const TTCounters& c = tt_counters();
    std::fprintf(stderr,
                 "TTPROBE calls=%llu hit=%llu stale_gen=%llu full=%llu empty_none=%llu "
                 "hit_slot=%llu/%llu/%llu/%llu empty_slot=%llu/%llu/%llu/%llu\\n",
                 (unsigned long long)c.calls, (unsigned long long)c.hit,
                 (unsigned long long)c.stale_gen, (unsigned long long)c.full,
                 (unsigned long long)c.empty_none,
                 (unsigned long long)c.hit_slot[0], (unsigned long long)c.hit_slot[1],
                 (unsigned long long)c.hit_slot[2], (unsigned long long)c.hit_slot[3],
                 (unsigned long long)c.empty_slot[0], (unsigned long long)c.empty_slot[1],
                 (unsigned long long)c.empty_slot[2], (unsigned long long)c.empty_slot[3]);
}
} // namespace forge
"""
open(p, "w").write(s)
print("instrument_tt applied")
