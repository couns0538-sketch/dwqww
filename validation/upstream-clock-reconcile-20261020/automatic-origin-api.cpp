// Linux diagnostic: observe actual helper creation without injecting delays.
// Export pthread_create from this executable so libstdc++ shared calls are seen.
// Delegate through RTLD_NEXT; this diagnostic is not linked into Forge.
#include "forge/search.hpp"

#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <dlfcn.h>
#include <iostream>
#include <pthread.h>
#include <string_view>

namespace {
using Clock = std::chrono::steady_clock;
std::atomic<bool> observing{false};
std::atomic<std::int64_t> first_create_ns{0};
std::atomic<std::int64_t> last_created_ns{0};
std::atomic<int> creation_count{0};
std::int64_t now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();
}
}

extern "C" int pthread_create(pthread_t* thread, const pthread_attr_t* attr,
                                     void* (*start)(void*), void* arg) {
    using Create = int (*)(pthread_t*, const pthread_attr_t*, void* (*)(void*), void*);
    static const auto real_create = reinterpret_cast<Create>(dlsym(RTLD_NEXT, "pthread_create"));
    if (real_create == nullptr) std::abort();
    const bool record = observing.load();
    if (record) {
        std::int64_t expected = 0;
        (void)first_create_ns.compare_exchange_strong(expected, now_ns());
    }
    const int result = real_create(thread, attr, start, arg);
    if (record && result == 0) {
        last_created_ns.store(now_ns());
        creation_count.fetch_add(1);
    }
    return result;
}

namespace forge {
struct SearcherTestProbe {
    static Clock::time_point origin(Searcher& searcher) { return searcher.main_worker().start_; }
};
}

int main() {
    forge::Board board;
    forge::Searcher searcher(1, 4);
    int failures = 0;
    auto run = [&](std::string_view label, forge::SearchLimits limits, bool clocked) {
        first_create_ns.store(0);
        last_created_ns.store(0);
        creation_count.store(0);
        searcher.reset_stop();
        observing.store(true);
        const forge::SearchInfo info = searcher.search(board, limits);
        observing.store(false);
        const auto origin = std::chrono::duration_cast<std::chrono::nanoseconds>(
            forge::SearcherTestProbe::origin(searcher).time_since_epoch()).count();
        const auto first = first_create_ns.load();
        const auto last = last_created_ns.load();
        const bool valid = creation_count.load() == 3 && first > 0 && last >= first &&
                           !info.best_move.is_none() &&
                           board.parse_uci(forge::Board::move_to_uci(info.best_move)).has_value();
        const bool epoch = clocked ? origin <= first : origin >= last;
        const bool passed = valid && epoch;
        std::cout << (passed ? "PASS " : "FAIL ") << label
                  << " clocked=" << clocked << " origin_ns=" << origin
                  << " first_create_ns=" << first << " last_created_ns=" << last
                  << " helpers=" << creation_count.load() << " nodes=" << info.nodes << '\n';
        if (!passed) ++failures;
    };
    forge::SearchLimits limits;
    limits.depth = 1;
    run("untimed-depth", limits, false);
    limits.nodes_specified = true;
    limits.nodes = 100;
    run("untimed-nodes", limits, false);
    limits.nodes_specified = false;
    limits.nodes = 0;
    limits.mate_moves = 1;
    run("untimed-mate", limits, false);
    limits.mate_moves = 0;
    limits.movetime_ms = 60000;
    run("timed-depth", limits, true);
    limits.movetime_ms = -1;
    limits.time_ms = 60000;
    run("clock-depth", limits, true);
    limits.infinite = true;
    run("infinite-with-clock", limits, false);
    limits.infinite = false;
    limits.ponder = true;
    run("ponder-with-clock", limits, false);
    std::cout << "origin contract failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
