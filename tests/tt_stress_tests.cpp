// Multi-thread transposition-table stress (O1-LTT, UCI LocklessTT).
// N threads probe and store a shared table with a small, colliding key set.
// The data of every stored entry is a function of its key (score, eval,
// depth, move, bound, pv, rule-50 clock), so any probe hit whose data does not
// match its key is a corrupted entry, e.g. a torn read that passed the key
// check. Locked tables (the default) and lockless tables must both return 0
// corrupted entries; misses are expected in both modes (replacement, and in
// lockless mode slots that two threads wrote at the same time).
// usage: forge_tt_stress_tests [--threads N] [--ops M] [--mode lockless|locked]
//        [--clusters C] [--keys K] [--expect-corruption]
//   --ops is the total over all threads (default 10,000,000). With
//   --expect-corruption the exit code is 0 only if corruption WAS observed
//   (the planted-bug check: a build whose key check is disabled).
#include "forge/search.hpp"

#include <algorithm>
#include <atomic>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

namespace {

using forge::Move;
using forge::TranspositionTable;

struct Expected {
    int score;
    int eval;
    int depth;
    Move move;
    forge::Bound bound;
    bool pv;
    std::uint16_t clock;
};

std::uint64_t mix(std::uint64_t z) {
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

Expected expected_for(std::uint64_t key) {
    const std::uint64_t h = mix(key);
    Expected e{};
    e.score = static_cast<int>(h % 16001U) - 8000;
    e.eval = static_cast<int>((h >> 16) % 16001U) - 8000;
    e.depth = 1 + static_cast<int>((h >> 32) % 60U);
    const auto from = static_cast<std::uint8_t>((h >> 40) % 64U);
    const auto to = static_cast<std::uint8_t>((from + 1 + (h >> 46) % 63U) % 64U);
    e.move = Move{from, to, 0, 0};
    e.bound = forge::BoundExact;  // always admitted: every store writes the whole entry
    e.pv = ((h >> 52) & 1U) != 0;
    e.clock = static_cast<std::uint16_t>((h >> 53) % 90U);
    return e;
}

std::uint64_t parse(std::string_view text) {
    std::uint64_t value = 0;
    const auto r = std::from_chars(text.data(), text.data() + text.size(), value);
    if (r.ec != std::errc{} || r.ptr != text.data() + text.size()) throw std::runtime_error("bad number");
    return value;
}

} // namespace

int main(int argc, char** argv) {
    try {
        unsigned threads = 4;
        std::uint64_t ops = 10000000;
        bool lockless = true;
        std::uint64_t clusters = 4;
        std::uint64_t key_count = 64;
        bool expect_corruption = false;
        for (int i = 1; i < argc; ++i) {
            const std::string_view a = argv[i];
            if (a == "--expect-corruption") {
                expect_corruption = true;
                continue;
            }
            if (i + 1 >= argc) throw std::runtime_error("missing value");
            const std::string_view v = argv[++i];
            if (a == "--threads") threads = static_cast<unsigned>(parse(v));
            else if (a == "--ops") ops = parse(v);
            else if (a == "--clusters") clusters = parse(v);
            else if (a == "--keys") key_count = parse(v);
            else if (a == "--mode") {
                if (v != "lockless" && v != "locked") throw std::runtime_error("mode is lockless or locked");
                lockless = v == "lockless";
            } else {
                throw std::runtime_error("unknown option");
            }
        }
        if (threads == 0 || clusters == 0 || key_count == 0 || clusters > 16384) throw std::runtime_error("bad arguments");
#if !defined(__SIZEOF_INT128__)
        throw std::runtime_error("the key layout below assumes multiply-high TT indexing");
#endif
        TranspositionTable tt(1);  // 16384 clusters: cluster index = key >> 50
        tt.set_lockless(lockless);
        tt.new_search();
        std::vector<std::uint64_t> keys(key_count);
        for (std::uint64_t i = 0; i < key_count; ++i) keys[i] = ((i % clusters) << 50U) + 0x10000U + i;

        std::atomic<std::uint64_t> probes{0}, hits{0}, stores{0}, corrupted{0};
        std::atomic<unsigned> ready{0};
        std::atomic<bool> go{false};
        auto worker = [&](unsigned id) {
            std::uint64_t state = 0x9E3779B97F4A7C15ULL * (id + 1);
            std::uint64_t local_probes = 0, local_hits = 0, local_stores = 0, local_corrupted = 0;
            const std::uint64_t my_ops = ops / threads + (id < ops % threads ? 1U : 0U);
            ready.fetch_add(1, std::memory_order_release);
            while (!go.load(std::memory_order_acquire)) std::this_thread::yield();
            for (std::uint64_t n = 0; n < my_ops; ++n) {
                state = mix(state + 0x9E3779B97F4A7C15ULL);
                const std::uint64_t key = keys[state % key_count];
                const auto probe = tt.probe(key);
                ++local_probes;
                if (probe.hit) {
                    ++local_hits;
                    const Expected x = expected_for(key);
                    const auto& e = probe.entry;
                    if (e.score != x.score || e.eval != x.eval || e.depth != x.depth || e.move != x.move ||
                        e.bound() != x.bound || e.pv() != x.pv || e.rule50_clock != x.clock) {
                        ++local_corrupted;
                    }
                }
                if ((state >> 40) % 2 == 0) {
                    const Expected x = expected_for(key);
                    tt.store(probe, key, x.score, x.eval, x.move, x.depth, x.bound, x.pv, x.clock);
                    ++local_stores;
                }
            }
            probes.fetch_add(local_probes);
            hits.fetch_add(local_hits);
            stores.fetch_add(local_stores);
            corrupted.fetch_add(local_corrupted);
        };
        std::vector<std::thread> pool;
        for (unsigned id = 0; id < threads; ++id) pool.emplace_back(worker, id);
        while (ready.load(std::memory_order_acquire) != threads) std::this_thread::yield();
        const auto start = std::chrono::steady_clock::now();
        go.store(true, std::memory_order_release);
        for (auto& t : pool) t.join();
        const double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
        std::cout << "tt stress: mode " << (lockless ? "lockless" : "locked") << " threads " << threads << " clusters "
                  << clusters << " keys " << key_count << " | probes " << probes << " hits " << hits << " stores "
                  << stores << " corrupted " << corrupted << " | " << seconds << " s\n";
        const bool clean = corrupted.load() == 0;
        if (expect_corruption) {
            std::cout << (clean ? "FAIL: no corruption observed (planted-bug check expected some)\n"
                                : "PASS: corruption observed, as expected for this planted bug\n");
            return clean ? 1 : 0;
        }
        std::cout << (clean ? "PASS: 0 corrupted entries returned\n" : "FAIL: corrupted entries returned\n");
        return clean ? 0 : 1;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 2;
    }
}
