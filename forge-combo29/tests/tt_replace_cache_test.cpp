// Public-API oracle: original strict-min scan, including BoundNone holes.
#define main existing_contract_main
#include "tt_contract_test.cpp"
#undef main
#include <array>
int main() {
    rejection(); generation_and_replacement(); boundnone_hole_preserves_later_hit();
    policy_and_clamping(); concurrent_payload();
    TranspositionTable tt(1);
    unsigned random = 0x20261110U;
    auto next = [&] { random ^= random << 13; random ^= random >> 17; random ^= random << 5; return random; };
    for (unsigned trial = 0; trial < 4096; ++trial) {
        tt.clear();
        std::array<TTEntry, 4> model{};
        for (unsigned slot = 0; slot < 4; ++slot) {
            for (unsigned n = (trial % 8 == 0 ? 0 : next() % 40); n; --n) tt.new_search();
            int depth = trial % 8 == 0 ? 16 : next() % 256;
            auto p = tt.probe(key(slot + 1));
            store(tt, p, key(slot + 1), slot + 100, depth);
            model[slot] = tt.probe(key(slot + 1)).entry;
        }
        for (unsigned n = next() % 65; n; --n) tt.new_search();
        // Sometimes clear any slot, without moving later occupied entries.
        if (trial % 3 == 0) {
            unsigned hole = next() % 4;
            auto p = tt.probe(key(hole + 1));
            store(tt, p, key(hole + 1), hole + 100, 255, BoundNone);
            model[hole].gen_bound = 0;
        }
        unsigned best = 0;
        auto score = [&](unsigned i) { return int(model[i].depth) - 4 * int((32 + tt.generation() - model[i].generation()) & 31U); };
        for (unsigned i = 0; i < 4; ++i) {
            if (!model[i].occupied()) { best = i; break; }
            if (score(i) < score(best)) best = i;
        }
        auto missing = tt.probe(key(1000));
        require(!missing.hit && missing.entry.score == int(best + 100), "replacement differs from strict-min oracle");
        for (unsigned i = 0; i < 4; ++i) {
            if (!model[i].occupied()) continue;
            auto hit = tt.probe(key(i + 1));
            require(hit.hit && hit.entry.score == int(i + 100) && hit.entry.generation() == tt.generation(), "hit scan/generation differs");
        }
    }
    std::cout << "PASS 4096 selected-slot oracle cases: depth extremes, ages/wrap, ties, holes, hits\n";
}
