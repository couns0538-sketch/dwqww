"""instrument_probe_parts.py : scratch-only split of probe_body's cost into (a) cluster index, (b) the 4-way
scan, (c) the miss/replacement path — using rdtsc buckets.

This is NOT a patch and NOT proposed: rdtsc around hot code perturbs what it measures, so the absolute numbers
are inflated. What it CAN answer is the RATIO between the three parts, which is what the owner needs to know
whether to chase layout/prefetch (load) or key comparison order (scan).

Counters are thread_local to keep them out of the hot path's cache lines.
"""
p = "src/search.cpp"
s = open(p).read()

s = s.replace("#include <algorithm>", "#include <algorithm>\n#include <x86intrin.h>", 1)

s = s.replace("""struct TTCounters {""",
"""struct ProbePartCycles {
    std::uint64_t index = 0, scan = 0, miss = 0, calls = 0;
};
inline ProbePartCycles& probe_parts() {
    static thread_local ProbePartCycles c;
    return c;
}

struct TTCounters {""", 1)

# instrument the three regions
s = s.replace("""TTProbe TranspositionTable::probe_body(std::uint64_t key) const {
    TTCounters& tc = tt_counters();
    ++tc.calls;
    TTCluster& cluster = cluster_for(key);
    const std::size_t index = static_cast<std::size_t>(&cluster - clusters_.get());""",
"""TTProbe TranspositionTable::probe_body(std::uint64_t key) const {
    TTCounters& tc = tt_counters();
    ++tc.calls;
    ProbePartCycles& pp = probe_parts();
    ++pp.calls;
    std::uint64_t t0 = __rdtsc();
    TTCluster& cluster = cluster_for(key);
    const std::size_t index = static_cast<std::size_t>(&cluster - clusters_.get());
    std::uint64_t t1 = __rdtsc();
    pp.index += t1 - t0;""", 1)

s = s.replace("""    TTEntry* found = nullptr;
#pragma GCC unroll 1
    for (TTEntry& entry : cluster.entries) {
        if (entry.key32 == key32 && entry.occupied()) {
            found = &entry;
            break;
        }
    }""",
"""    TTEntry* found = nullptr;
    std::uint64_t t2 = __rdtsc();
#pragma GCC unroll 1
    for (TTEntry& entry : cluster.entries) {
        if (entry.key32 == key32 && entry.occupied()) {
            found = &entry;
            break;
        }
    }
    pp.scan += __rdtsc() - t2;""", 1)

s = s.replace("""    if (found != nullptr) {
        ++tc.hit;""",
"""    std::uint64_t t3 = __rdtsc();
    if (found != nullptr) {
        pp.miss += __rdtsc() - t3;
        ++tc.hit;""", 1)

s = s.replace("""    ++tc.full;
    return snapshot(*replace, false);
}""",
"""    ++tc.full;
    pp.miss += __rdtsc() - t3;
    return snapshot(*replace, false);
}""", 1)

s = s.replace("#include <cstdio>", "#include <cstdio>", 1)
if "#include <cstdio>" not in s:
    s = s.replace("#include <x86intrin.h>", "#include <cstdio>\n#include <x86intrin.h>", 1)

s += """
namespace forge {
void dump_probe_parts() {
    const ProbePartCycles& p = probe_parts();
    const double tot = double(p.index + p.scan + p.miss);
    std::fprintf(stderr,
                 "PROBEPARTS calls=%llu index_cyc=%llu (%.1f%%) scan_cyc=%llu (%.1f%%) miss_cyc=%llu (%.1f%%) "
                 "per_call index=%.1f scan=%.1f miss=%.1f\\n",
                 (unsigned long long)p.calls,
                 (unsigned long long)p.index, tot > 0 ? 100.0 * double(p.index) / tot : 0.0,
                 (unsigned long long)p.scan, tot > 0 ? 100.0 * double(p.scan) / tot : 0.0,
                 (unsigned long long)p.miss, tot > 0 ? 100.0 * double(p.miss) / tot : 0.0,
                 p.calls ? double(p.index) / double(p.calls) : 0.0,
                 p.calls ? double(p.scan) / double(p.calls) : 0.0,
                 p.calls ? double(p.miss) / double(p.calls) : 0.0);
}
} // namespace forge
"""
open(p, "w").write(s)
print("instrument_probe_parts applied")
