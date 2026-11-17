#pragma once

// Diagnostic counters for the transposition table. Not part of the shipped
// engine: FORGE_TT_TRACE is undefined in the lock build, and every use below is
// inside `#if FORGE_TT_TRACE`, so a default build compiles exactly the shipped
// code. The counters are plain integers, not atomics, because the trace build is
// only ever run at Threads 1 under the table's ExclusiveLease.

#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>

#ifndef FORGE_TT_TRACE
#define FORGE_TT_TRACE 0
#endif

#if FORGE_TT_TRACE

namespace forge::tttrace {

struct Counters {
    // Probes, split by the outcome the search actually acts on.
    std::uint64_t probe = 0;
    std::uint64_t probe_hit = 0;
    std::uint64_t probe_miss = 0;
    // A hit whose entry was shallower than the depth being searched. This is the
    // "entry written under a different depth" case: the search reads a move and
    // a bound produced by a shorter search of the same position.
    std::uint64_t hit_shallower = 0;
    std::uint64_t hit_equal = 0;
    std::uint64_t hit_deeper = 0;
    // Hits whose stored depth cannot reach the requested depth by more than 2,
    // i.e. the shallow-entry cases that can plausibly change a cutoff.
    std::uint64_t hit_shallower_by_3plus = 0;
    // A hit on an entry from an older generation: the position was found but the
    // entry has been superseded at least once.
    std::uint64_t hit_stale_generation = 0;
    // A probe whose 32-bit tag matched but whose full key did not. This is a
    // correctness defect, not a strength one: the search would read another
    // position's score. Requires the shadow key array to be enabled.
    std::uint64_t false_hit = 0;
    std::uint64_t false_hit_detector_armed = 0;

    // Stores.
    std::uint64_t store = 0;
    std::uint64_t store_admit = 0;
    std::uint64_t store_reject = 0;
    // Admitted into a slot that held no position.
    std::uint64_t store_into_empty = 0;
    // Admitted over the same position, at a depth at least as deep.
    std::uint64_t store_same_key = 0;
    // Displacement: an admitted store whose slot held a DIFFERENT position. This
    // is the only store that loses information, and the only one a collision
    // account can be built on.
    std::uint64_t store_displace = 0;
    // Depth of the displaced entry, by depth. Mass above depth 0 means real
    // search entries are being lost; mass only at 0 means qsearch leaves are.
    std::uint64_t displaced_depth[256] = {};

    // Occupancy actually reached in the cluster the probe landed in, summed, so a
    // mean cluster fill can be reported without sampling 1000 clusters.
    std::uint64_t probe_cluster_fill_sum = 0;
    std::uint64_t store_cluster_fill_sum = 0;

    // Set by uci when the search ends.
    std::uint64_t nodes_reported = 0;
    int depth_reported = 0;
    int seldepth_reported = 0;

    void reset() { *this = Counters{}; }

    void dump(std::FILE* out, const char* tag) const {
        std::fprintf(out, "{\"tag\":\"%s\"", tag);
        std::fprintf(out, ",\"probe\":%llu,\"probe_hit\":%llu,\"probe_miss\":%llu",
                     (unsigned long long)probe, (unsigned long long)probe_hit,
                     (unsigned long long)probe_miss);
        std::fprintf(out, ",\"hit_shallower\":%llu,\"hit_equal\":%llu,\"hit_deeper\":%llu",
                     (unsigned long long)hit_shallower, (unsigned long long)hit_equal,
                     (unsigned long long)hit_deeper);
        std::fprintf(out, ",\"hit_shallower_by_3plus\":%llu,\"hit_stale_generation\":%llu",
                     (unsigned long long)hit_shallower_by_3plus,
                     (unsigned long long)hit_stale_generation);
        std::fprintf(out, ",\"false_hit\":%llu,\"false_hit_detector_armed\":%llu",
                     (unsigned long long)false_hit, (unsigned long long)false_hit_detector_armed);
        std::fprintf(out, ",\"store\":%llu,\"store_admit\":%llu,\"store_reject\":%llu",
                     (unsigned long long)store, (unsigned long long)store_admit,
                     (unsigned long long)store_reject);
        std::fprintf(out, ",\"store_into_empty\":%llu,\"store_same_key\":%llu,\"store_displace\":%llu",
                     (unsigned long long)store_into_empty, (unsigned long long)store_same_key,
                     (unsigned long long)store_displace);
        std::fprintf(out, ",\"nodes\":%llu,\"depth\":%d,\"seldepth\":%d",
                     (unsigned long long)nodes_reported, depth_reported, seldepth_reported);
        std::fprintf(out, ",\"probe_cluster_fill_mean\":%.3f,\"store_cluster_fill_mean\":%.3f",
                     probe > 0 ? double(probe_cluster_fill_sum) / double(probe) : 0.0,
                     store > 0 ? double(store_cluster_fill_sum) / double(store) : 0.0);
        std::fprintf(out, ",\"displaced_depth\":{");
        bool first = true;
        for (int d = 0; d < 256; ++d) {
            if (displaced_depth[d] == 0) continue;
            std::fprintf(out, "%s\"%d\":%llu", first ? "" : ",", d,
                         (unsigned long long)displaced_depth[d]);
            first = false;
        }
        std::fprintf(out, "}}\n");
    }
};

inline Counters g{};

// Depth of the search frame that is about to probe. Set by Worker::search /
// Worker::qsearch immediately before each probe, read by probe_body. Only the
// trace build touches it; it is a plain int on purpose.
inline int g_probe_depth = 0;
inline int g_probe_ply = 0;

// Diagnosis arms. Both default off, so the trace build searches exactly the
// shipped tree unless a UCI command turns one on. They exist to separate two
// accounts that the counters alone cannot distinguish:
//
//  no_cutoff  — the table still orders moves and still stores, but a probe never
//               returns early on a bound. If the answer is still size-dependent
//               with this on, the divergence is not caused by TT cutoffs.
//  no_move    — the table still stores and still cuts, but a probe never supplies
//               a move to order with. If the divergence survives this too, the
//               table is not changing the tree through move ordering either.
inline bool g_no_tt_cutoff = false;
inline bool g_no_tt_move = false;
// Null control: no probe result reaches the search at all. Stores still happen,
// so the table is still written exactly as before; only the read path is gone.
// Used to prove that the harness measures the table and not something else.
inline bool g_no_read = false;

// Event log. Empty path disables it. Used only to align two runs event by event
// and find the first place the smaller table behaves differently.
struct EventLog {
    std::FILE* file = nullptr;
    std::uint64_t seq = 0;
    bool enabled() const { return file != nullptr; }
    void write(const char* fmt, ...) __attribute__((format(printf, 2, 3)));
};

inline EventLog& log() {
    static EventLog instance = [] {
        EventLog l;
        if (const char* path = std::getenv("FORGE_TT_TRACE_FILE"); path != nullptr && *path != '\0') {
            l.file = std::fopen(path, "w");
        }
        return l;
    }();
    return instance;
}

#include <cstdarg>
inline void EventLog::write(const char* fmt, ...) {    if (file == nullptr) return;
    std::va_list args;
    va_start(args, fmt);
    std::fprintf(file, "%llu ", (unsigned long long)seq++);
    std::vfprintf(file, fmt, args);
    std::fputc('\n', file);
    va_end(args);
}

inline void flush() {
    if (log().file != nullptr) std::fflush(log().file);
}

} // namespace forge::tttrace

#endif // FORGE_TT_TRACE
