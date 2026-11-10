// tt_microbench.cpp - opus2 SMP pack tool (NOT part of the engine; needs FORGE_SMP_LAYOUT=1 and FORGE_SPD_TT_NOTLS=1).
// Advisory, low-noise look at the TT mechanism itself: throughput of the engine's real per-access TT dispatch
// (Worker::probe_tt + Worker::store_tt, reached through the existing SearcherTestProbe friendship), legacy vs lockless:
//   Threads 1: legacy = the engine's owned path (tt_owned_ = true: no stripe lock, as UCI go / bench at Threads 1)
//              vs lockless (atomic_ref + XOR-tag decode)  -> the per-access cost of the lockless encoding;
//   Threads 2/4: legacy = striped-lock path (tt_owned_ = false, as the engine at Threads >= 2) vs lockless.
// One Worker per thread (as Searcher makes them), one shared table. Workloads: random keys (mostly misses and
// replacements) and a hot pool of 4096 keys (mostly hits). Each run lasts a fixed time; ops = probe + store pairs.
// Rounds alternate the order of the configs: L (legacy), X (lockless), A (legacy again = A/A noise floor).
// Usage: tt_microbench [seconds_per_run=1.5] [rounds=6] [threads=1,2,4]   (pin it from outside: run_pinned.ps1, CPUs 12-15,
//        Idle; threads is a comma list of 1, 2 and/or 4)
#include "forge/search.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#if !FORGE_SMP_LAYOUT || !FORGE_SPD_TT_NOTLS
#error "tt_microbench needs FORGE_SMP_LAYOUT=1 and FORGE_SPD_TT_NOTLS=1"
#endif
#ifndef NDEBUG
// The legacy Threads-1 config calls probe_owned / store_owned (tt_owned_ = true) without taking the table's
// ExclusiveLease, whose assert(has_exclusive_access()) would fire (fable bug hunt NIT-4). Build with -DNDEBUG, as the
// engine is built; the measured path is then exactly the engine's owned path.
#error "tt_microbench must be built with -DNDEBUG"
#endif

namespace forge {
struct SearcherTestProbe {
    static void set_owned(Worker& w, bool owned) { w.tt_owned_ = owned; }
    static TTProbe probe(const Worker& w, std::uint64_t key) { return w.probe_tt(key); }
    static void store(Worker& w, const TTProbe& p, std::uint64_t key, int score, int eval, Move move, int depth, Bound bound,
                      bool pv, std::uint16_t hmc) {
        w.store_tt(p, key, score, eval, move, depth, bound, pv, hmc);
    }
};
} // namespace forge

namespace {
std::uint64_t splitmix(std::uint64_t x) {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27U)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31U);
}

struct Config { char tag; bool lockless; };

double run_once(forge::SharedSearchState& shared, std::vector<std::unique_ptr<forge::Worker>>& workers, int threads,
                bool lockless, bool hot, double seconds, std::uint64_t seed) {
    using forge::SearcherTestProbe;
    shared.tt.set_lockless(lockless);   // quiescent; reallocates (empty) only when the mode changes
    shared.tt.clear();
    shared.tt.new_search();
    for (int t = 0; t < threads; ++t) SearcherTestProbe::set_owned(*workers[static_cast<std::size_t>(t)], threads == 1);
    std::vector<std::uint64_t> pool(4096);
    for (std::size_t i = 0; i < pool.size(); ++i) pool[i] = splitmix(seed + i);
    std::atomic<bool> go{false}, stop{false};
    std::vector<std::uint64_t> ops(static_cast<std::size_t>(threads), 0);
    std::vector<std::thread> th;
    for (int t = 0; t < threads; ++t) {
        th.emplace_back([&, t]() {
            forge::Worker& w = *workers[static_cast<std::size_t>(t)];
            std::uint64_t x = splitmix(seed * 31U + static_cast<std::uint64_t>(t) + 1U), n = 0, sink = 0;
            while (!go.load(std::memory_order_acquire)) std::this_thread::yield();
            while (!stop.load(std::memory_order_relaxed)) {
                for (int i = 0; i < 1024; ++i) {
                    x ^= x << 13U; x ^= x >> 7U; x ^= x << 17U;
                    const std::uint64_t key = hot ? pool[x & 4095U] : x;
                    const forge::TTProbe p = SearcherTestProbe::probe(w, key);
                    sink += p.hit ? static_cast<std::uint64_t>(p.entry.depth) : 1U;
                    forge::Move m;
                    m.from = static_cast<std::uint8_t>(key & 63U);
                    m.to = static_cast<std::uint8_t>(((key >> 6U) & 63U) ^ 1U);
                    SearcherTestProbe::store(w, p, key, static_cast<int>(key % 2001U) - 1000, static_cast<int>((key >> 11U) % 2001U) - 1000, m,
                                             1 + static_cast<int>((key >> 22U) % 40U), static_cast<forge::Bound>(1U + (key >> 30U) % 3U),
                                             ((key >> 33U) & 1U) != 0, static_cast<std::uint16_t>((key >> 40U) % 100U));
                }
                n += 1024;
            }
            ops[static_cast<std::size_t>(t)] = n + (sink & 1U);   // keep the probes observable
        });
    }
    const auto t0 = std::chrono::steady_clock::now();
    go.store(true, std::memory_order_release);
    std::this_thread::sleep_for(std::chrono::duration<double>(seconds));
    stop.store(true, std::memory_order_relaxed);
    for (auto& x : th) x.join();
    const double secs = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    std::uint64_t total = 0;
    for (const auto v : ops) total += v;
    return static_cast<double>(total) / secs / 1e6;   // million probe+store pairs per second
}

double median(std::vector<double> v) {
    std::sort(v.begin(), v.end());
    const std::size_t n = v.size();
    return n == 0 ? 0.0 : (n % 2 ? v[n / 2] : 0.5 * (v[n / 2 - 1] + v[n / 2]));
}
} // namespace

int main(int argc, char** argv) {
    const double seconds = argc > 1 ? std::atof(argv[1]) : 1.5;
    const int rounds = argc > 2 ? std::atoi(argv[2]) : 6;
    std::vector<int> thread_list;
    {
        const std::string list = argc > 3 ? argv[3] : "1,2,4";
        std::size_t pos = 0;
        while (pos < list.size()) {
            const std::size_t comma = list.find(',', pos);
            const int t = std::atoi(list.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos).c_str());
            if (t == 1 || t == 2 || t == 4) thread_list.push_back(t);
            if (comma == std::string::npos) break;
            pos = comma + 1;
        }
        if (thread_list.empty()) {
            std::printf("threads must be a comma list of 1, 2 and/or 4\n");
            return 2;
        }
    }
    std::printf("tt_microbench: seconds/run %.2f rounds %d hw_concurrency %u (pin externally; advisory only)\n", seconds, rounds,
                std::thread::hardware_concurrency());
    std::printf("%-6s %-7s %-3s | %-14s %-14s %-14s | %-9s %-9s | spreads L/X/A %%\n", "hashMB", "keys", "T",
                "L legacy Mops", "X lockless", "A legacy(A/A)", "X/L", "A/L");
    const Config cfgs[3] = {{'L', false}, {'X', true}, {'A', false}};
    for (const std::size_t mb : {std::size_t{16}, std::size_t{256}}) {
        forge::SharedSearchState shared(mb);
        std::vector<std::unique_ptr<forge::Worker>> workers;
        for (int i = 0; i < 4; ++i) workers.push_back(std::make_unique<forge::Worker>(shared, i));
        for (const bool hot : {false, true}) {
            for (const int threads : thread_list) {
                std::vector<double> res[3];
                for (int r = 0; r < rounds; ++r) {
                    for (int k = 0; k < 3; ++k) {
                        const int idx = (r % 2 == 0) ? k : 2 - k;   // alternate order: L X A / A X L
                        res[idx].push_back(run_once(shared, workers, threads, cfgs[idx].lockless, hot, seconds,
                                                    1000U * static_cast<std::uint64_t>(r) + static_cast<std::uint64_t>(idx)));
                    }
                }
                double med[3], spread[3];
                for (int k = 0; k < 3; ++k) {
                    med[k] = median(res[k]);
                    const auto mm = std::minmax_element(res[k].begin(), res[k].end());
                    spread[k] = med[k] > 0 ? 100.0 * (*mm.second - *mm.first) / med[k] : 0.0;
                }
                std::printf("%-6zu %-7s %-3d | %-14.2f %-14.2f %-14.2f | %-9.4f %-9.4f | %.1f/%.1f/%.1f\n", mb, hot ? "hot4096" : "random",
                            threads, med[0], med[1], med[2], med[1] / med[0], med[2] / med[0], spread[0], spread[1], spread[2]);
                std::fflush(stdout);
            }
        }
    }
    return 0;
}
