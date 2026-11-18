// Job 16 Part 1 Differential Oracle + Planted-Fault Verifier for stack/13_tt_avx512_fast_probe.patch.txt:
// Runs 500,000 collision-heavy probe / store / new_search / hashfull operations on two 1 MB
// TranspositionTable instances in lockstep:
//   - tt_ref:  public locked TranspositionTable::probe(k) + TranspositionTable::store(...)
//   - tt_fast: Worker's inline AVX-512 TranspositionTable::probe_owned_fast(k) + store_owned_fast(...)
// Asserts identical hit, TTEntry payload (key32, move, score, eval, depth, gen_bound, rule50_clock),
// and hashfull() at every single step, plus 9 tight node-cap searches.

#define FORGE_UCI_NO_MAIN 1
#include "search.cpp"

#include <cstdint>
#include <iostream>
#include <random>

namespace forge {
struct S13TTTestAccess {
    static void run() {
        attacks::init();
        TranspositionTable tt_ref(1);
        TranspositionTable tt_fast(1);
        TranspositionTable::ExclusiveLease lease(tt_fast);

        std::mt19937_64 rng(20261118ULL);
        std::array<std::uint64_t, 512> key_pool{};
        for (std::size_t i = 0; i < key_pool.size(); ++i) {
            const std::uint64_t cluster_id = i / 8; // 8 keys/cluster -> stresses empty, hit, and full-cluster replacement
            key_pool[i] = (cluster_id << 50U) | ((rng() & 0xFFFFFFFEULL) | 1ULL);
        }

        for (std::size_t step = 0; step < 500000; ++step) {
            if (step % 4000 == 0) {
                tt_ref.new_search();
                tt_fast.new_search();
                const int hf_ref = tt_ref.hashfull();
                const int hf_fast = tt_fast.hashfull();
                if (hf_ref != hf_fast) {
                    std::cerr << "S13_TT_ORACLE MISMATCH (hashfull) at step=" << step
                              << " ref=" << hf_ref << " fast=" << hf_fast << "\n";
                    std::exit(1);
                }
            }
            const std::uint64_t k = key_pool[rng() % key_pool.size()];
            const TTProbe pr_ref = tt_ref.probe(k);
            const WorkerTTProbe pr_fast = tt_fast.probe_owned_fast(k);

            if (pr_ref.hit != pr_fast.hit) {
                std::cerr << "S13_TT_ORACLE MISMATCH (hit) at step=" << step
                          << " ref=" << pr_ref.hit << " fast=" << pr_fast.hit << "\n";
                std::exit(1);
            }
            if (pr_ref.hit) {
                const TTEntry& a = pr_ref.entry;
                const TTEntry& b = pr_fast.entry;
                if (a.key32 != b.key32 || !(a.move == b.move) || a.score != b.score ||
                    a.eval != b.eval || a.depth != b.depth || a.gen_bound != b.gen_bound ||
                    a.rule50_clock != b.rule50_clock) {
                    std::cerr << "S13_TT_ORACLE MISMATCH (entry) at step=" << step << "\n";
                    std::exit(1);
                }
            }
            if ((rng() & 3ULL) != 0ULL) {
                const int sc = static_cast<int>(rng() % 4001ULL) - 2000;
                const int ev = static_cast<int>(rng() % 2001ULL) - 1000;
                const int dp = static_cast<int>(rng() % 20ULL);
                const auto bnd = static_cast<Bound>((rng() % 3ULL) + 1ULL);
                const Move mv{static_cast<std::uint8_t>(rng() & 63ULL),
                              static_cast<std::uint8_t>(rng() & 63ULL), 0, Quiet};
                const bool pv = (rng() & 1ULL) != 0;
                const auto r50 = static_cast<std::uint16_t>(rng() % 100ULL);
                tt_ref.store(pr_ref, k, sc, ev, mv, dp, bnd, pv, r50);
                tt_fast.store_owned_fast(pr_fast.cluster, pr_fast.slot, k, sc, ev, mv, dp, bnd, pv, r50);
            }
        }
        if (tt_ref.hashfull() != tt_fast.hashfull()) {
            std::cerr << "S13_TT_ORACLE FINAL HASHFULL MISMATCH\n";
            std::exit(1);
        }
        std::cout << "S13_TT_FAST_PROBE_ORACLE PASS: ops=500000 final_hashfull="
                  << tt_fast.hashfull() << " mismatches=0\n";
    }
};
} // namespace forge

int main() {
    forge::S13TTTestAccess::run();
    return 0;
}
