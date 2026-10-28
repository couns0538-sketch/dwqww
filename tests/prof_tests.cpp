// Profile-counter tests (FORGE_PROF builds only). Sol's S08 fixtures, with the shared-bank thread test
// replaced for S08-2: every search worker owns one bank, and Searcher::profile_snapshot() merges them.
#include "forge/board.hpp"
#include "forge/profile.hpp"
#include "forge/search.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <thread>
#include <vector>

int main() {
    using namespace forge::prof;
    int failures=0;
    auto check=[&](bool value,const std::string& message) {
        if (!value) {std::cerr << "FAIL " << message << '\n';++failures;}
    };
    const auto nodes_index=static_cast<std::size_t>(Counter::Nodes);
    Bank outer,inner;
    {
        Scope one(&outer);count(Counter::Nodes);
        {Scope two(&inner);count(Counter::Nodes,2);}
        count(Counter::Nodes,3);
        {Scope disabled(nullptr);count(Counter::Nodes,99);}
        count(Counter::Nodes,4);
    }
    check(outer.snapshot_quiescent().values[nodes_index]==8,"nested scope restores previous bank");
    check(inner.snapshot_quiescent().values[nodes_index]==2,"independent nested bank");
    count(Counter::Nodes,999);
    check(outer.snapshot_quiescent().values[nodes_index]==8,"scope exit disables counting");

    // S08-2: one bank per thread, merged after the threads are joined (no shared counters).
    std::array<Bank,4> banks;
    std::array<std::thread,4> threads;
    for (std::size_t t=0;t<threads.size();++t) threads[t]=std::thread([&banks,t] {
        Scope scope(&banks[t]);
        for (std::size_t i=0;i<1000+t;++i) count(Counter::Nodes);
    });
    for (auto& thread:threads) thread.join();
    Snapshot merged;
    for (std::size_t t=0;t<banks.size();++t) {
        check(banks[t].snapshot_quiescent().values[nodes_index]==1000+t,"per-thread bank holds only its own thread's counts");
        merge(merged,banks[t].snapshot_quiescent());
    }
    check(merged.values[nodes_index]==4006 && !merged.overflow,"merge sums the per-thread banks");

    outer.reset_quiescent();
    outer.add(Counter::Nodes,std::numeric_limits<std::uint64_t>::max());
    outer.add(Counter::Nodes,2);
    auto wrapped=outer.snapshot_quiescent();
    check(wrapped.values[nodes_index]==1 && wrapped.overflow,"unsigned wrap marks unusable totals");
    outer.reset_quiescent();
    check(outer.snapshot_quiescent().values[nodes_index]==0 && !outer.snapshot_quiescent().overflow,"quiescent reset clears values and overflow");
    Snapshot total;
    total.values[nodes_index]=std::numeric_limits<std::uint64_t>::max();
    Snapshot delta;delta.values[nodes_index]=2;merge(total,delta);
    check(total.values[nodes_index]==1 && total.overflow,"aggregation reports wrap");
    Snapshot sticky; Snapshot flagged; flagged.overflow=true; merge(sticky,flagged);
    check(sticky.overflow,"a worker bank's overflow survives the merge");

    // S08-2: real searches at Threads 1/2/4. Each worker's bank counts exactly that worker's nodes,
    // every worker counts into its own bank, and the merged total is their sum.
    for (const int thread_count:{1,2,4}) {
        const std::string tag=" (Threads "+std::to_string(thread_count)+")";
        forge::Searcher searcher(16,thread_count);
        searcher.set_profiling(true);
        forge::Board board;
        forge::SearchLimits limits;
        limits.depth=9;
        const auto info=searcher.search(board,limits,false);
        check(searcher.profiling_active(),"profiling active for the search"+tag);
        const auto per_worker=searcher.profile_worker_snapshots();
        const auto worker_nodes=searcher.profile_worker_nodes();
        check(per_worker.size()==static_cast<std::size_t>(thread_count) &&
              worker_nodes.size()==static_cast<std::size_t>(thread_count),"one bank per worker"+tag);
        std::uint64_t sum=0;
        for (std::size_t w=0;w<per_worker.size() && w<worker_nodes.size();++w) {
            check(per_worker[w].values[nodes_index]==worker_nodes[w],
                  "worker "+std::to_string(w)+" bank nodes "+std::to_string(per_worker[w].values[nodes_index])+
                  " == worker nodes "+std::to_string(worker_nodes[w])+tag);
            check(per_worker[w].values[nodes_index]>0,"worker "+std::to_string(w)+" counted into its own bank"+tag);
            sum+=worker_nodes[w];
        }
        const auto all=searcher.profile_snapshot();
        check(all.values[nodes_index]==sum && !all.overflow,"merged nodes == sum of worker nodes"+tag);
        check(all.values[static_cast<std::size_t>(Counter::MainNodes)]+all.values[static_cast<std::size_t>(Counter::QsNodes)]==
              all.values[nodes_index],"main + quiescence nodes == nodes"+tag);
        if (thread_count==1) check(info.nodes==all.values[nodes_index],"Threads 1: merged nodes == reported search nodes");
        searcher.set_profiling(false);
        (void)searcher.search(board,limits,false);
        check(!searcher.profiling_active(),"profiling off for the next search"+tag);
        check(searcher.profile_snapshot().values[nodes_index]==0,"banks reset and idle when profiling is off"+tag);
    }
    if (!failures) std::cout << "PASS profiling counters, nested TLS, per-worker banks and merge\n";
    return failures ? 1 : 0;
}
