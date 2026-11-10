#include "forge/search.hpp"
#include <atomic>
#include <barrier>
#include <climits>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace {
using namespace forge;
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
std::uint64_t key(unsigned tag) {
#if defined(__SIZEOF_INT128__)
    return tag; // 1 MB multiply-high index: small keys all select cluster zero.
#else
    return static_cast<std::uint64_t>(tag) << 32; // Modulo index, high-bit tag.
#endif
}
Move move_for(int marker) {
    return Move{static_cast<std::uint8_t>(marker % 64),
                static_cast<std::uint8_t>((marker % 64 + 1 + (marker / 64) % 63) % 64),
                static_cast<std::uint8_t>(marker % 5),
                static_cast<std::uint8_t>(marker % 2)};
}
void store(TranspositionTable& tt, const TTProbe& probe, std::uint64_t k,
           int marker, int depth = 16, Bound bound = BoundExact) {
    tt.store(probe, k, marker, -marker, move_for(marker), depth, bound,
             marker % 2, static_cast<std::uint16_t>(marker % 101));
}
void rejection() {
    TranspositionTable a(1), b(1);
    const auto k = key(9);
    store(a, TTProbe{}, k, 10);
    require(!a.probe(k).hit, "default handle admitted");
    store(a, b.probe(k), k, 10);
    require(!a.probe(k).hit, "foreign handle admitted");
    store(a, a.probe(k), key(10), 10);
    require(!a.probe(key(10)).hit, "mismatched key admitted");
    for (int operation = 0; operation < 3; ++operation) {
        a.clear();
        store(a, a.probe(k), k, 11);
        const auto stale = a.probe(k);
        if (operation == 0) a.clear();
        if (operation == 1) a.resize(2);
        if (operation == 2) a.new_search();
        store(a, a.probe(k), k, 22);
        store(a, stale, k, 33);
        require(a.probe(k).entry.score == 22, "lifecycle-stale handle admitted");
    }
    // Immutable snapshots must not change with subsequent stores.
    const auto snapshot = a.probe(k);
    store(a, a.probe(k), k, 44);
    require(snapshot.entry.score == 22, "probe snapshot changed");
    std::cout << "PASS default/foreign/key/stale rejection and immutable snapshots\n";
}
void generation_and_replacement() {
    TranspositionTable tt(1);
    store(tt, tt.probe(key(0)), key(0), 7);
    auto stale = tt.probe(key(0));
    for (int generation = 1; generation <= 64; ++generation) {
        tt.new_search();
        require(tt.generation() == generation % 32, "generation wrap mismatch");
        const auto p = tt.probe(key(0));
        require(p.hit && p.entry.generation() == generation % 32 && p.entry.score == 7,
                "generation refresh corrupted payload");
    }
    store(tt, stale, key(0), 99);
    require(tt.probe(key(0)).entry.score == 7, "wrapped generation revived stale handle");
    tt.clear();
    for (unsigned i = 0; i < 4; ++i) store(tt, tt.probe(key(i)), key(i), 10 + i, 10 + 10*i);
    store(tt, tt.probe(key(4)), key(4), 40, 40);
    require(!tt.probe(key(0)).hit && tt.probe(key(4)).hit, "shallowest replacement mismatch");
    for (unsigned i = 1; i < 4; ++i) require(tt.probe(key(i)).hit, "wrong cluster victim");
    tt.clear();
    for (unsigned i = 0; i < 4; ++i) store(tt, tt.probe(key(i)), key(i), 10 + i, 20);
    tt.new_search();
    for (unsigned i = 1; i < 4; ++i) (void)tt.probe(key(i));
    store(tt, tt.probe(key(4)), key(4), 40, 20);
    require(!tt.probe(key(0)).hit, "age-sensitive replacement mismatch");
    // A valid probe can refer to a slot displaced since probing; its store must
    // still produce a coherent new entry, not preserve the victim's move.
    const auto displaced = tt.probe(key(5));
    store(tt, tt.probe(key(6)), key(6), 61);
    store(tt, displaced, key(5), 51);
    require(tt.probe(key(5)).hit && tt.probe(key(5)).entry.move == move_for(51),
            "displaced-slot store payload mismatch");
    std::cout << "PASS generation wrap/refresh and same-cluster replacement\n";
}
void boundnone_hole_preserves_later_hit() {
    TranspositionTable tt(1);
    const auto a = key(1), b = key(2), c = key(3);
    // Fresh same-cluster stores occupy the first two slots in this order.
    store(tt, tt.probe(a), a, 11, 5, BoundExact);
    store(tt, tt.probe(b), b, 22, 5, BoundExact);
    // BoundNone is a public enum value; the admitted store clears occupancy.
    store(tt, tt.probe(a), a, 11, 5, BoundNone);
    const auto hole = tt.probe(a);
    require(!hole.hit && !hole.entry.occupied() && hole.entry.score == 11,
            "BoundNone did not produce the expected first-slot hole");
    const auto later = tt.probe(b);
    require(later.hit && later.entry.score == 22 && later.entry.eval == -22 &&
            later.entry.move == move_for(22), "hit after first empty slot was lost");
    // Model the rejected optimization on the observed first two slots. This is
    // a hypothetical scan, not a production change or a new engine defect.
    const std::array<TTEntry, 2> observed_prefix{hole.entry, later.entry};
    const auto early_exit_hit = [&] {
        for (const auto& entry : observed_prefix) {
            if (!entry.occupied()) return false;
            if (entry.key32 == later.entry.key32) return true;
        }
        return false;
    }();
    require(!early_exit_hit, "counterexample did not defeat first-empty termination");
    const auto missing = tt.probe(c);
    require(!missing.hit && !missing.entry.occupied() && missing.entry.key32 == hole.entry.key32,
            "miss did not preserve first-empty replacement selection");
    store(tt, missing, c, 33, 5, BoundExact);
    require(tt.probe(c).hit && tt.probe(b).hit, "refilling hole lost later entry");
    std::cout << "PASS BoundNone hole: first_slot_occupied=0 later_B_hit=1 "
                 "hypothetical_first_empty_hit=0 refill_preserves_B=1\n";
}

void policy_and_clamping() {
    TranspositionTable tt(1);
    auto k = key(1);
    for (unsigned clock = 0; clock <= 110; ++clock) {
        tt.store(tt.probe(k), k, 12, -12, move_for(12), 7, BoundExact, false, clock);
        const auto e = tt.probe(k).entry;
        for (unsigned current = 0; current <= 110; ++current) {
            const auto a = std::min(clock, 100U), b = std::min(current, 100U);
            require(e.score_usable(current) == ((a < 90 && b < 90) || a == b),
                    "rule50 usability mismatch");
        }
    }
    tt.store(tt.probe(k), k, INT_MAX, INT_MIN, move_for(12), 1000, BoundLower, true, 65535);
    auto e = tt.probe(k).entry;
    require(e.score == 32767 && e.eval == -32767 && e.depth == 255 && e.rule50_clock == 100 &&
            e.bound() == BoundLower && e.pv(), "upper clamping/bound mismatch");
    tt.store(tt.probe(k), k, INT_MIN, INT_MAX, move_for(13), -1000, BoundExact, false, 0);
    e = tt.probe(k).entry;
    require(e.score == -32767 && e.eval == 32767 && e.depth == 0 &&
            e.bound() == BoundExact && !e.pv(), "lower clamping/bound mismatch");
    store(tt, tt.probe(k), k, 20, 100);
    const auto before = tt.probe(k).entry;
    store(tt, tt.probe(k), k, 30, 1, BoundUpper);
    e = tt.probe(k).entry;
    require(e.score == before.score && e.eval == before.eval && e.depth == before.depth &&
            e.rule50_clock == before.rule50_clock && e.move == move_for(30),
            "shallow rejection must preserve score payload but may update move");
    tt.store(tt.probe(k), k, 40, -40, Move::none(), 101, BoundExact, false, 80);
    require(tt.probe(k).entry.move == move_for(30), "same-key empty move must preserve old move");
    std::cout << "PASS rule50 matrix, clamping, bounds and partial-update policy\n";
}
void concurrent_payload() {
    TranspositionTable tt(1);
    std::barrier start(4);
    std::atomic<int> failures{0}, hits{0};
    std::vector<std::thread> workers;
    for (int id = 0; id < 4; ++id) workers.emplace_back([&, id] {
        start.arrive_and_wait();
        for (int i = 0; i < 5000; ++i) {
            const int marker = 1 + id * 5000 + i;
            const auto k = key(static_cast<unsigned>(i % 8));
            store(tt, tt.probe(k), k, marker, marker % 256);
            const auto p = tt.probe(k);
            if (!p.hit) continue; // A contending collider may legitimately evict it.
            ++hits;
            const int observed = p.entry.score;
            if (observed < 1 || observed > 20000 || p.entry.eval != -observed ||
                p.entry.move != move_for(observed) || p.entry.depth != observed % 256 ||
                p.entry.rule50_clock != observed % 101 || p.entry.pv() != bool(observed % 2) ||
                p.entry.bound() != BoundExact || p.entry.generation() != 0) ++failures;
            if ((i & 255) == 0) (void)tt.hashfull();
        }
    });
    for (auto& worker : workers) worker.join();
    require(hits > 0 && failures == 0, "concurrent exact-store payload incoherent");
    std::cout << "PASS concurrent public probe/store: 4 threads x 5000 iterations, hits=" << hits
              << ", incoherent=" << failures << '\n';
}
}
int main(int argc, char**) {
    try {
        if (argc > 1) {
            forge::TranspositionTable tt(1);
            store(tt, tt.probe(key(1)), key(1), 10, 100);
            store(tt, tt.probe(key(1)), key(1), 20, INT_MAX, forge::BoundLower);
            require(tt.probe(key(1)).entry.score == 20 && tt.probe(key(1)).entry.depth == 255,
                    "INT_MAX depth was not admitted/clamped");
            return 0;
        }
        rejection(); generation_and_replacement(); boundnone_hole_preserves_later_hit();
        policy_and_clamping(); concurrent_payload();
        std::cout << "ALL TT CONTRACT CHECKS PASSED\n";
    } catch (const std::exception& error) {
        std::cerr << "FAIL " << error.what() << '\n';
        return 1;
    }
}
