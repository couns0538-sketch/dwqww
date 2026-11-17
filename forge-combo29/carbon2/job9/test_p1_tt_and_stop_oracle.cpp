// Step P1 TranspositionTable (500,000 collision-heavy probe/store/new_search/hashfull ops)
// & Node-Cap Stop-Boundary Two-Binary Differential Oracle + Planted-Fault Verifier.

#define FORGE_UCI_NO_MAIN 1
#include "search.cpp"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

static std::uint64_t fnv1a(std::uint64_t h, std::uint64_t v) noexcept {
    for (int b = 0; b < 8; ++b) {
        h ^= (v >> (b * 8)) & 0xFFULL;
        h *= 0x100000001B3ULL;
    }
    return h;
}

static std::string run_tt_and_stop_trace() {
    forge::attacks::init();
    std::uint64_t h = 0xCBF29CE484222325ULL;

    // 1. 500,000 collision-heavy TT probe_owned / store_owned / new_search / hashfull operations on a 1 MB table
    //    restricting keys to 64 hot clusters so replacement victims (slots 0..3, ages, depths) are heavily stressed.
    forge::TranspositionTable tt(1);
    std::mt19937_64 rng(20261117ULL);
    std::array<std::uint64_t, 512> key_pool{};
    for (std::size_t i = 0; i < key_pool.size(); ++i) {
        const std::uint64_t cluster_id = i / 8;
        // Multiply-high on 1 MB (16384 = 2^14 clusters) indexes by key >> 50; low 32 bits are verification_key.
        key_pool[i] = (cluster_id << 50U) | ((rng() & 0xFFFFFFFEULL) | 1ULL);
    }

    for (std::size_t step = 0; step < 500000; ++step) {
        if (step % 4000 == 0) {
            tt.new_search();
            h = fnv1a(h, static_cast<std::uint64_t>(tt.hashfull()));
        }
        const std::uint64_t k = key_pool[rng() % key_pool.size()];
        const forge::TTProbe pr = tt.probe(k);
        h = fnv1a(h, pr.hit ? 1ULL : 0ULL);
        if (pr.hit) {
            h = fnv1a(h, static_cast<std::uint64_t>(static_cast<std::uint16_t>(pr.entry.score)));
            h = fnv1a(h, static_cast<std::uint64_t>(pr.entry.depth));
            h = fnv1a(h, static_cast<std::uint64_t>(pr.entry.gen_bound));
            h = fnv1a(h, static_cast<std::uint64_t>(pr.entry.move.from) |
                         (static_cast<std::uint64_t>(pr.entry.move.to) << 8U));
        }
        if ((rng() & 3ULL) != 0ULL) {
            const int sc = static_cast<int>(rng() % 4001ULL) - 2000;
            const int ev = static_cast<int>(rng() % 2001ULL) - 1000;
            const int dp = static_cast<int>(rng() % 20ULL);
            const auto bnd = static_cast<forge::Bound>((rng() % 3ULL) + 1ULL);
            const forge::Move mv{static_cast<std::uint8_t>(rng() & 63ULL),
                                 static_cast<std::uint8_t>(rng() & 63ULL), 0, forge::Quiet};
            tt.store(pr, k, sc, ev, mv, dp, bnd, (rng() & 1ULL) != 0, static_cast<std::uint16_t>(rng() % 100ULL));
        }
    }

    // 2. Tight node-budget searches (`nodes` = 1, 17, 511, 1023, 1024, 1025, 2048, and `softnodes` = 250, 2000)
    //    verifying exact node stop boundaries across 1024-node periodic boundaries.
    forge::Searcher searcher(4, 1);
    forge::Board board;
    (void)board.set_fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
    for (const std::uint64_t cap : {1ULL, 17ULL, 511ULL, 1023ULL, 1024ULL, 1025ULL, 2048ULL}) {
        forge::SearchLimits lim;
        lim.nodes = cap;
        lim.nodes_specified = true;
        const auto res = searcher.search(board, lim, false, forge::Searcher::TTAccess::Exclusive);
        h = fnv1a(h, res.nodes);
        h = fnv1a(h, static_cast<std::uint64_t>(res.score + 100000));
        h = fnv1a(h, static_cast<std::uint64_t>(res.best_move.from) | (static_cast<std::uint64_t>(res.best_move.to) << 8U));
    }
    for (const std::uint64_t soft : {250ULL, 2000ULL}) {
        forge::SearchLimits lim;
        lim.nodes = soft;
        lim.nodes_specified = true;
        lim.soft_nodes = true;
        const auto res = searcher.search(board, lim, false, forge::Searcher::TTAccess::Exclusive);
        h = fnv1a(h, res.nodes);
        h = fnv1a(h, static_cast<std::uint64_t>(res.score + 100000));
        h = fnv1a(h, static_cast<std::uint64_t>(res.best_move.from) | (static_cast<std::uint64_t>(res.best_move.to) << 8U));
    }

    char hex[32];
    std::snprintf(hex, sizeof(hex), "%016llx", static_cast<unsigned long long>(h));
    return std::string(hex);
}

int main(int argc, char** argv) {
    if (argc < 3) return 1;
    const std::string mode = argv[1];
    const std::string got = run_tt_and_stop_trace();
    if (mode == "--dump") {
        std::ofstream out(argv[2]);
        out << got << "\n";
        std::cout << "P1_TT_STOP_REF_DUMP hash=" << got << "\n";
        return 0;
    }
    if (mode == "--verify") {
        std::ifstream in(argv[2]);
        std::string exp;
        std::getline(in, exp);
        if (got != exp) {
            std::cerr << "P1_TT_STOP_ORACLE MISMATCH: expected=" << exp << " got=" << got << "\n";
            return 1;
        }
        std::cout << "P1_TT_STOP_ORACLE PASS: ops=500000+9_stop_caps hash=" << got << " mismatches=0\n";
        return 0;
    }
    return 1;
}
