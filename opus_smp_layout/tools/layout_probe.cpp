// layout_probe.cpp - opus2 SMP pack tool (NOT part of the engine). Measures the cache-line layout SPEC.md section 4 is
// about, on the tree it is compiled against (parent P with FORGE_SMP_LAYOUT 0, or the gate source with 1):
//   * sizeof / alignof of the TT and worker types;
//   * byte offset, size and 64-byte line of every Worker member (via the existing SearcherTestProbe friendship);
//   * which members share the 64-byte line(s) of the cross-thread counter Worker::nodes_;
//   * SharedSearchState member offsets (tt, stop, ponder_hit_ns);
//   * heap addresses / lines of 4 workers created exactly as Searcher::set_threads creates them (std::make_unique<Worker>).
// Build: g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -march=znver5 -pthread -I<tree>/include layout_probe.cpp
//        <tree>/src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp -o layout_probe.exe
#include "forge/search.hpp"

#include <cstdint>
#include <cstdio>
#include <memory>
#include <string>
#include <vector>

#ifndef FORGE_SMP_LAYOUT
#define FORGE_SMP_LAYOUT_PROBE_VALUE -1
#else
#define FORGE_SMP_LAYOUT_PROBE_VALUE FORGE_SMP_LAYOUT
#endif

namespace forge {
struct SearcherTestProbe {
    struct Field { std::string name; long long offset; std::size_t size; };
    static long long off(const Worker& w, const void* p) {
        return static_cast<long long>(reinterpret_cast<const char*>(p) - reinterpret_cast<const char*>(&w));
    }
    static std::vector<Field> fields(const Worker& w) {
        std::vector<Field> f;
#define FORGE_PROBE_FIELD(m) f.push_back({#m, off(w, &w.m), sizeof(w.m)})
        FORGE_PROBE_FIELD(id_);
        FORGE_PROBE_FIELD(evaluator_);
        FORGE_PROBE_FIELD(main_history_);
        FORGE_PROBE_FIELD(capture_history_);
        FORGE_PROBE_FIELD(continuation_history_);
        FORGE_PROBE_FIELD(counter_moves_);
        FORGE_PROBE_FIELD(correction_history_);
        FORGE_PROBE_FIELD(material_correction_);
        FORGE_PROBE_FIELD(stack_);
        FORGE_PROBE_FIELD(root_effort_moves_);
        FORGE_PROBE_FIELD(root_move_nodes_);
        FORGE_PROBE_FIELD(root_effort_count_);
        FORGE_PROBE_FIELD(pondering_);
        FORGE_PROBE_FIELD(start_);
        FORGE_PROBE_FIELD(nodes_);
        FORGE_PROBE_FIELD(local_nodes_);
        FORGE_PROBE_FIELD(all_workers_);
        FORGE_PROBE_FIELD(node_limit_);
        FORGE_PROBE_FIELD(node_limit_specified_);
        FORGE_PROBE_FIELD(soft_limit_ms_);
        FORGE_PROBE_FIELD(hard_limit_ms_);
        FORGE_PROBE_FIELD(time_managed_);
        FORGE_PROBE_FIELD(aborted_);
#if FORGE_SPD_TT_NOTLS
        FORGE_PROBE_FIELD(tt_owned_);
#endif
        FORGE_PROBE_FIELD(seldepth_);
        FORGE_PROBE_FIELD(root_depth_);
        FORGE_PROBE_FIELD(root_history_index_);
        FORGE_PROBE_FIELD(root_moves_);
        FORGE_PROBE_FIELD(root_restricted_);
        FORGE_PROBE_FIELD(null_tries_);
        FORGE_PROBE_FIELD(null_cutoffs_);
#undef FORGE_PROBE_FIELD
        return f;
    }
    static const void* nodes_address(const Worker& w) { return &w.nodes_; }
    static const void* local_nodes_address(const Worker& w) { return &w.local_nodes_; }
};
} // namespace forge

namespace {
long long line_of(long long offset) { return offset >= 0 ? offset / 64 : -1 - ((-offset - 1) / 64); }
std::uintptr_t addr(const void* p) { return reinterpret_cast<std::uintptr_t>(p); }
} // namespace

int main() {
    using namespace forge;
    std::printf("layout_probe: FORGE_SMP_LAYOUT=%d FORGE_SPD_TT_NOTLS=%d\n", FORGE_SMP_LAYOUT_PROBE_VALUE, static_cast<int>(FORGE_SPD_TT_NOTLS));
    std::printf("sizeof/alignof: TTEntry %zu/%zu TTCluster %zu/%zu TTProbe %zu/%zu TranspositionTable %zu/%zu "
                "SharedSearchState %zu/%zu SearchStack %zu/%zu nnue::Accumulator %zu/%zu Worker %zu/%zu Searcher %zu/%zu\n",
                sizeof(TTEntry), alignof(TTEntry), sizeof(TTCluster), alignof(TTCluster), sizeof(TTProbe), alignof(TTProbe),
                sizeof(TranspositionTable), alignof(TranspositionTable), sizeof(SharedSearchState), alignof(SharedSearchState),
                sizeof(SearchStack), alignof(SearchStack), sizeof(nnue::Accumulator), alignof(nnue::Accumulator),
                sizeof(Worker), alignof(Worker), sizeof(Searcher), alignof(Searcher));
#if FORGE_SMP_LAYOUT
    std::printf("sizeof/alignof: TTLocklessCluster %zu/%zu\n", sizeof(TTLocklessCluster), alignof(TTLocklessCluster));
#endif
    auto shared = std::make_unique<SharedSearchState>(16);
    const char* sbase = reinterpret_cast<const char*>(shared.get());
    const long long off_tt = reinterpret_cast<const char*>(&shared->tt) - sbase;
    const long long off_stop = reinterpret_cast<const char*>(&shared->stop) - sbase;
    const long long off_ph = reinterpret_cast<const char*>(&shared->ponder_hit_ns) - sbase;
    std::printf("SharedSearchState: tt @%lld (size %zu, lines %lld..%lld) | stop @%lld line %lld | ponder_hit_ns @%lld line %lld | "
                "heap addr%%64 = %llu\n", off_tt, sizeof(shared->tt), line_of(off_tt), line_of(off_tt + static_cast<long long>(sizeof(shared->tt)) - 1),
                off_stop, line_of(off_stop), off_ph, line_of(off_ph), static_cast<unsigned long long>(addr(shared.get()) % 64));
    std::printf("SharedSearchState: stop shares a line with the TT object's tail: %s\n",
                line_of(off_stop) == line_of(off_tt + static_cast<long long>(sizeof(shared->tt)) - 1) ? "YES" : "no");

    std::vector<std::unique_ptr<Worker>> workers;
    for (int i = 0; i < 4; ++i) workers.push_back(std::make_unique<Worker>(*shared, i));
    const auto f = SearcherTestProbe::fields(*workers[0]);
    std::printf("Worker members (offset size line_first..line_last):\n");
    for (const auto& x : f) {
        std::printf("  %-24s @%-8lld %-7zu %lld..%lld\n", x.name.c_str(), x.offset, x.size, line_of(x.offset),
                    line_of(x.offset + static_cast<long long>(x.size) - 1));
    }
    long long nodes_off = -1; std::size_t nodes_size = 0;
    for (const auto& x : f) if (x.name == "nodes_") { nodes_off = x.offset; nodes_size = x.size; }
    const long long nl0 = line_of(nodes_off), nl1 = line_of(nodes_off + static_cast<long long>(nodes_size) - 1);
    std::printf("members sharing a 64-byte line with nodes_ (lines %lld..%lld; object-relative, worker addr%%64 shown below):", nl0, nl1);
    int shared_count = 0;
    for (const auto& x : f) {
        if (x.name == "nodes_") continue;
        const long long a = line_of(x.offset), b = line_of(x.offset + static_cast<long long>(x.size) - 1);
        if (b >= nl0 && a <= nl1) { std::printf(" %s", x.name.c_str()); ++shared_count; }
    }
    std::printf("%s\n", shared_count == 0 ? " (none)" : "");
    for (int i = 0; i < 4; ++i) {
        const Worker& w = *workers[static_cast<std::size_t>(i)];
        const std::uintptr_t a = addr(&w);
        const std::uintptr_t na = addr(SearcherTestProbe::nodes_address(w));
        const std::uintptr_t la = addr(SearcherTestProbe::local_nodes_address(w));
        const long long dist = i == 0 ? 0 : static_cast<long long>(a) - static_cast<long long>(addr(workers[static_cast<std::size_t>(i) - 1].get()));
        std::printf("worker %d: addr%%64 %llu | nodes_ line 0x%llx | local_nodes_ line 0x%llx | same line: %s | distance to previous worker %lld B\n",
                    i, static_cast<unsigned long long>(a % 64), static_cast<unsigned long long>(na / 64),
                    static_cast<unsigned long long>(la / 64), (na / 64) == (la / 64) ? "YES" : "no", dist);
    }
    return 0;
}
