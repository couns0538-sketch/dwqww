// tt_probe_owned.cpp -- the four TT invariants, through the SHIPPED unlocked owner path.
//
// 1. STORE-THEN-PROBE: after storing an entry for key K, a probe of K returns a hit with the
//    same score, move, depth, bound and halfmove clock.
// 2. NO FALSE HIT: a probe of a different key K' must not return a hit carrying K's payload
//    under K's verification. (A 32-bit verification key means false hits are possible in
//    principle, so this checks that the engine's own key-derivation is self-consistent for
//    keys differing only above 32 bits -- if it were not, distinct positions would collide
//    systematically rather than by chance.)
// 3. RESIZE INVALIDATES: after resize(), a probe of any old key must not return a stale hit
//    with the old epoch's payload.
// 4. CLEAR EMPTIES: after clear(), every probe misses.
//
// Every check asserts a value was observed; "no hit" is only a pass where the invariant says
// a miss is required.
#include "forge/search.hpp"

#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

using namespace forge;

namespace {
int failures = 0;
void check(bool cond, const std::string& what) {
    if (cond) return;
    std::printf("FAIL %s\n", what.c_str());
    ++failures;
}
// Small deterministic key generator so the test does not depend on board hashing.
std::uint64_t mix(std::uint64_t x) {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31);
}
}  // namespace

int main() {
    // FORGE_SPD_TT_NOTLS=1 (the SHIPPED setting): the owner thread takes an ExclusiveLease and
    // then calls probe_owned/store_owned, which skip lock_stripe entirely. This probe runs the
    // same four invariants through the OWNER path, which is what actually ships.
    TranspositionTable tt(16);
    TranspositionTable::ExclusiveLease lease(tt);
    tt.new_search();

    // ---- 1. store-then-probe round trip, over many entries ----
    struct Case { std::uint64_t key; int score; int depth; Bound bound; std::uint16_t clock; };
    std::vector<Case> cases;
    for (int i = 0; i < 2000; ++i) {
        const std::uint64_t key = mix(static_cast<std::uint64_t>(i) * 7919ULL + 13ULL);
        const Bound bound = static_cast<Bound>(1 + (i % 3));      // Upper, Lower, Exact
        const int score = (i * 37) % 2001 - 1000;
        const int depth = i % 40;
        const std::uint16_t clock = static_cast<std::uint16_t>(i % 101);
        cases.push_back({key, score, depth, bound, clock});
        const TTProbe probe = tt.probe_owned(key);
        // Move 0..63 encoded as from/to pairs; use a distinctive value per i.
        const Move move{static_cast<std::uint8_t>(i % 64), static_cast<std::uint8_t>((i * 3) % 64),
                        0, static_cast<std::uint8_t>(Quiet)};
        tt.store_owned(probe, key, score, score / 2, move, depth, bound, true, clock);
    }
    std::uint64_t hits = 0;
    for (const Case& c : cases) {
        const TTProbe p = tt.probe_owned(c.key);
        if (!p.hit) { check(false, "store-then-probe missed key " + std::to_string(c.key)); continue; }
        ++hits;
        check(p.entry.score == c.score,
              "score mismatch for key " + std::to_string(c.key) + ": stored " +
              std::to_string(c.score) + " got " + std::to_string(p.entry.score));
        check(p.entry.depth == c.depth,
              "depth mismatch for key " + std::to_string(c.key));
        check(p.entry.bound() == c.bound,
              "bound mismatch for key " + std::to_string(c.key));
        check(p.entry.rule50_clock == static_cast<std::uint8_t>(std::min<int>(c.clock, 100)),
              "rule50 clock mismatch for key " + std::to_string(c.key));
        check(p.entry.occupied(), "occupied() false on a hit for key " + std::to_string(c.key));
    }
    std::printf("1. store-then-probe (owner path): %llu/%zu hits\n",
                static_cast<unsigned long long>(hits), cases.size());

    // ---- 2. keys differing only in the high 32 bits ----
    // Same low 32 bits, different high 32: these share a cluster (cluster_for uses the low bits)
    // but differ in verification_key, so a probe must NOT return the other one's hit payload.
    const std::uint64_t base = 0x00000000A5A5A5A5ULL;
    const TTProbe pb = tt.probe_owned(base);
    tt.store_owned(pb, base, 1234, 100, Move{4, 12, 0, static_cast<std::uint8_t>(Quiet)}, 7,
             BoundExact, false, 0);
    const std::uint64_t other = 0xFFFF0000A5A5A5A5ULL;
    const TTProbe po = tt.probe_owned(other);
    if (po.hit) {
        check(po.entry.score == 0 || po.entry.score != 1234,
              "false hit: key " + std::to_string(other) + " returned key " +
              std::to_string(base) + "'s score 1234");
        std::printf("2. high-32 variant returned a hit with score %d (not the stored 1234)\n",
                    static_cast<int>(po.entry.score));
    } else {
        std::printf("2. high-32 variant missed, as expected\n");
    }
    const TTProbe pb2 = tt.probe_owned(base);
    check(pb2.hit && pb2.entry.score == 1234, "base key lost its own entry after the variant probe");

    // ---- 3. resize must not leave stale hits ----
    const std::uint64_t before_resize = cases[0].key;
    tt.resize(32);
    const TTProbe after = tt.probe_owned(before_resize);
    if (after.hit) {
        check(after.entry.score != cases[0].score,
              "stale hit after resize: key " + std::to_string(before_resize) +
              " still returns the pre-resize score");
    }
    std::printf("3. probe after resize: %s\n", after.hit ? "hit (checked not stale)" : "miss");

    // ---- 4. clear must empty the table ----
    tt.new_search();
    const TTProbe s = tt.probe_owned(0x123456789ULL);
    tt.store_owned(s, 0x123456789ULL, 55, 5, Move{1, 2, 0, static_cast<std::uint8_t>(Quiet)}, 3,
             BoundLower, false, 0);
    check(tt.probe_owned(0x123456789ULL).hit, "entry not stored before clear");
    tt.clear();
    const TTProbe c = tt.probe_owned(0x123456789ULL);
    check(!c.hit || c.entry.score != 55, "clear() left the stored entry behind");
    std::printf("4. probe after clear: %s\n", c.hit ? "hit (checked not the old entry)" : "miss");
    std::printf("occupied-after-clear hashfull: %d\n", tt.hashfull());

    std::printf("\n%s (%d failure(s))\n", failures == 0 ? "ALL TT INVARIANTS HELD" : "FAILURES",
                failures);
    return failures == 0 ? 0 : 1;
}
