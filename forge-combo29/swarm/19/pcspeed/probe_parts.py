"""probe_parts.py : scratch-only split of probe_body's cost into index / scan / remainder, via rdtsc buckets.

NOT a patch, NOT proposed. rdtsc around hot code inflates what it measures; the RATIO is the deliverable.

Buckets:
  index : from entry into probe_body to the cluster address being computed (cluster_for + address arithmetic)
  scan  : the four-way key32/occupied() walk over the 64-byte cluster  (the LOAD + comparison part)
  after : everything from after the scan to the return (generation refresh on a hit, or the miss/replacement
          path and the snapshot copy)
"""

import re

p = "src/search.cpp"
s = open(p).read()

s = s.replace("#include <algorithm>", "#include <algorithm>\n#include <x86intrin.h>\n#include <cstdio>", 1)

anchor = "#if FORGE_SPD_TT_NOTLS\ntemplate <bool TakeLock>\nTTProbe TranspositionTable::probe_body"
assert anchor in s
decl = """namespace {
struct ProbeParts {
    unsigned long long calls = 0, index = 0, scan = 0, after = 0;
};
inline ProbeParts& probe_parts() {
    static thread_local ProbeParts c;
    return c;
}
} // namespace

"""
s = s.replace(anchor, decl + anchor, 1)

old_head = """    TTCluster& cluster = cluster_for(key);
    const std::size_t index = static_cast<std::size_t>(&cluster - clusters_.get());"""
new_head = """    ProbeParts& pp = probe_parts();
    ++pp.calls;
    const unsigned long long t0 = __rdtsc();
    TTCluster& cluster = cluster_for(key);
    const std::size_t index = static_cast<std::size_t>(&cluster - clusters_.get());
    pp.index += __rdtsc() - t0;"""
assert old_head in s
s = s.replace(old_head, new_head, 1)

old_scan = """    TTEntry* found = nullptr;
#pragma GCC unroll 1
    for (TTEntry& entry : cluster.entries) {
        if (entry.key32 == key32 && entry.occupied()) {
            found = &entry;
            break;
        }
    }"""
new_scan = """    TTEntry* found = nullptr;
    const unsigned long long t1 = __rdtsc();
#pragma GCC unroll 1
    for (TTEntry& entry : cluster.entries) {
        if (entry.key32 == key32 && entry.occupied()) {
            found = &entry;
            break;
        }
    }
    pp.scan += __rdtsc() - t1;"""
assert old_scan in s
s = s.replace(old_scan, new_scan, 1)

# one exit point for the "after" bucket: wrap the two returns
s = s.replace("""        return snapshot(*found, true);
    }""",
"""        TTProbe hit_result = snapshot(*found, true);
        pp.after += __rdtsc() - t1;
        return hit_result;
    }""", 1)
s = s.replace("""    return snapshot(*replace, false);
}

TTProbe TranspositionTable::probe(std::uint64_t key) const""",
"""    TTProbe miss_result = snapshot(*replace, false);
    pp.after += __rdtsc() - t1;
    return miss_result;
}

TTProbe TranspositionTable::probe(std::uint64_t key) const""", 1)

s += """
namespace forge {
void dump_probe_parts() {
    const ProbeParts& p = probe_parts();
    const double tot = double(p.index + p.scan + p.after);
    std::fprintf(stderr,
                 "PROBEPARTS calls=%llu index=%llu (%.1f%%) scan=%llu (%.1f%%) after=%llu (%.1f%%)"
                 " per_call index=%.2f scan=%.2f after=%.2f total=%.2f cycles\\n",
                 p.calls, p.index, tot > 0 ? 100.0 * double(p.index) / tot : 0.0,
                 p.scan, tot > 0 ? 100.0 * double(p.scan) / tot : 0.0,
                 p.after, tot > 0 ? 100.0 * double(p.after) / tot : 0.0,
                 p.calls ? double(p.index) / double(p.calls) : 0.0,
                 p.calls ? double(p.scan) / double(p.calls) : 0.0,
                 p.calls ? double(p.after) / double(p.calls) : 0.0,
                 p.calls ? tot / double(p.calls) : 0.0);
}
} // namespace forge
"""
open(p, "w").write(s)
print("probe_parts applied")
