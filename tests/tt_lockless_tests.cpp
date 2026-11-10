// tt_lockless_tests.cpp - opus2 SMP pack (FORGE_SMP_LAYOUT=1): tests of the lockless TT mode, opus_smp_layout/SPEC.md 5.1.
// Own test code (no copied source). Every concurrent access in this file goes through the table API or std::atomic_ref,
// so a ThreadSanitizer report here is a real race in the code under test.
//   1 round trip    decode(encode(e)) == e for random and edge entries; decode == a field-by-field decoder for random
//                   word pairs; tag32(0) == 0; raw readers == decoded fields; tag detection: every single-bit change
//                   and every small field difference of D changes the tag
//   2 differential  legacy table vs lockless table, one thread, same random op stream: equal probes and equal contents
//   3 contention    4 / 8 threads on 1 / 4 / 16 clusters, payload = f(key): every hit must carry f(key) (no incoherent hit)
//   4 control       the same fixture on a test-only UNVALIDATED two-word table must see incoherent hits (fixture can fail)
//   5 lifecycle     new_search / resize / clear / mode toggle between joined phases; stale handles are rejected
#include "forge/search.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <random>
#include <string>
#include <thread>
#include <vector>

#if !FORGE_SMP_LAYOUT
#error "tt_lockless_tests needs FORGE_SMP_LAYOUT=1 (CMake option FORGE_SMP_LAYOUT=ON)"
#endif

namespace {

using forge::Bound;
using forge::Move;
using forge::TTEntry;
using forge::TTProbe;
using forge::TranspositionTable;

int failures = 0;

void check(bool ok, const std::string& what) {
    if (!ok) {
        ++failures;
        if (failures <= 40) std::cout << "FAIL " << what << "\n";
    }
}

bool same_entry(const TTEntry& a, const TTEntry& b) { return std::memcmp(&a, &b, sizeof(TTEntry)) == 0; }

std::string describe(const TTEntry& e) {
    return "key32=" + std::to_string(e.key32) + " move=" + std::to_string(e.move.from) + "/" + std::to_string(e.move.to) +
           " score=" + std::to_string(e.score) + " eval=" + std::to_string(e.eval) + " depth=" + std::to_string(e.depth) +
           " gb=" + std::to_string(e.gen_bound) + " r50=" + std::to_string(e.rule50_clock);
}

std::uint64_t splitmix(std::uint64_t x) {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27U)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31U);
}

// Seconds from the environment (CI under TSan may give more), default given.
double seconds_env(const char* name, double fallback) {
    const char* v = std::getenv(name);
    if (v == nullptr) return fallback;
    const double s = std::atof(v);
    return s > 0.0 ? s : fallback;
}

// ---------------------------------------------------------------- 1 round trip
// A difference delta = D1 - D2 (mod 2^64, generation bits cleared) can give equal tags only if high32(y) is 0, or is
// 0xFFFFFFFF with a non-zero low half: tag32(D1) = high32(x + y) and tag32(D2) = high32(x) with x = D2' * TagMul,
// y = delta * TagMul, and high32(x + y) = high32(x) + high32(y) + carry (a carry needs low32(y) != 0). A delta that
// fails this condition can never collide, whatever the two words are.
bool delta_can_collide(std::uint64_t delta) {
    const std::uint64_t y = delta * forge::ttlockless::TagMul;
    const auto high = static_cast<std::uint32_t>(y >> 32U);
    return high == 0U || (high == 0xFFFFFFFFU && static_cast<std::uint32_t>(y) != 0U);
}

// Field differences as they appear in D: score and eval are stored as uint16, so a signed difference t of two values
// is t, t - 65536 or t + 65536 in the stored words (when the two values sit on both sides of zero).
std::vector<std::int64_t> u16_deltas(int limit) {
    std::vector<std::int64_t> out;
    for (int t = -limit; t <= limit; ++t) {
        out.push_back(t);
        if (t > 0) out.push_back(static_cast<std::int64_t>(t) - 65536);
        if (t < 0) out.push_back(static_cast<std::int64_t>(t) + 65536);
    }
    return out;
}

void test_tag_detection() {
    namespace L = forge::ttlockless;
    // Every single-bit change outside GenMask, in either direction: delta = +-2^bit.
    for (int bit = 0; bit < 64; ++bit) {
        if ((L::GenMask >> bit) & 1U) continue;
        const std::uint64_t up = 1ULL << bit;
        check(!delta_can_collide(up) && !delta_can_collide(0U - up), "single-bit change of D bit " + std::to_string(bit) + " can keep the tag");
    }
    // Small field differences: |score| and |eval| differences <= 32 (with the uint16 wrap), |depth| <= 8, any bound/pv
    // change, |rule50| <= 4, in every combination except all-zero (38 million deltas).
    long long scanned = 0, bad = 0;
    const std::vector<std::int64_t> ds = u16_deltas(32);
    for (const std::int64_t dscore : ds) {
        for (const std::int64_t deval : ds) {
            for (std::int64_t ddepth = -8; ddepth <= 8; ++ddepth) {
                for (std::int64_t dbound = -7; dbound <= 7; ++dbound) {
                    for (std::int64_t dr50 = -4; dr50 <= 4; ++dr50) {
                        const std::int64_t delta = dscore + deval * 65536 + ddepth * (std::int64_t{1} << 32) +
                                                   dbound * (std::int64_t{1} << 40) + dr50 * (std::int64_t{1} << 48);
                        if (delta == 0) continue;
                        ++scanned;
                        if (delta_can_collide(static_cast<std::uint64_t>(delta))) {
                            if (++bad <= 5) check(false, "small field difference can keep the tag: score " + std::to_string(dscore) +
                                                             " eval " + std::to_string(deval) + " depth " + std::to_string(ddepth) +
                                                             " bound " + std::to_string(dbound) + " r50 " + std::to_string(dr50));
                        }
                    }
                }
            }
        }
    }
    // Differences only in bits 32..63 (depth, bound, pv, rule50, padding): delta = B * 2^32 with B != 0 mod 2^32, so
    // high32(delta * TagMul) = B * TagMul mod 2^32 is odd * B != 0 and the carry is 0: never a collision. Sampled check.
    std::mt19937_64 rng(31);
    for (int i = 0; i < 100000; ++i) {
        const std::uint64_t high = (rng() << 32U) & ~L::GenMask;
        if (high == 0) continue;
        const std::uint64_t d = rng() & ~L::GenMask;
        check(L::tag32(d) != L::tag32(d ^ high), "high-part difference kept the tag");
    }
    std::cout << "tag detection: 59 single bits x 2 directions, " << scanned << " small field differences, bad " << bad << "\n";
}

// Field-by-field reference decoder, independent of decode's bit_cast and of the layout asserts.
TTEntry decode_fields(std::uint64_t key, std::uint64_t data) {
    TTEntry entry;
    const auto move32 = static_cast<std::uint32_t>(key >> 32U);
    entry.key32 = static_cast<std::uint32_t>(key) ^ forge::ttlockless::tag32(data);
    entry.move.from = static_cast<std::uint8_t>(move32);
    entry.move.to = static_cast<std::uint8_t>(move32 >> 8U);
    entry.move.promotion = static_cast<std::uint8_t>(move32 >> 16U);
    entry.move.flags = static_cast<std::uint8_t>(move32 >> 24U);
    entry.score = static_cast<std::int16_t>(static_cast<std::uint16_t>(data));
    entry.eval = static_cast<std::int16_t>(static_cast<std::uint16_t>(data >> 16U));
    entry.depth = static_cast<std::uint8_t>(data >> 32U);
    entry.gen_bound = static_cast<std::uint8_t>(data >> 40U);
    entry.rule50_clock = static_cast<std::uint8_t>(data >> 48U);
    entry.padding = static_cast<std::uint8_t>(data >> 56U);
    return entry;
}

void test_round_trip() {
    namespace L = forge::ttlockless;
    {
        // decode == the field-by-field decoder for arbitrary word pairs (not only encoded ones).
        std::mt19937_64 words(4711);
        for (int i = 0; i < 200000; ++i) {
            const std::uint64_t k = words(), d = words();
            if (!same_entry(L::decode(k, d), decode_fields(k, d))) {
                check(false, "decode differs from the field-by-field decoder at K=" + std::to_string(k) + " D=" + std::to_string(d));
                break;
            }
        }
    }
    check(L::tag32(0) == 0, "tag32(0) == 0");
    check(L::tag32(L::GenMask) == 0, "the generation bits are outside the tag");
    check(same_entry(L::decode(0, 0), TTEntry{}), "decode(0,0) is the empty entry");
    const TTEntry zero{};
    check(L::data_word(zero) == 0 && L::key_word(zero, 0) == 0, "empty entry encodes to two zero words");
    std::mt19937_64 rng(20261109);
    for (int i = 0; i < 200000; ++i) {
        TTEntry e;
        const std::uint64_t a = rng(), b = rng();
        // TTEntry is trivially copyable (16 bytes, no padding): any byte pattern is a valid value.
        std::memcpy(static_cast<void*>(&e), &a, 8);
        std::memcpy(static_cast<void*>(reinterpret_cast<char*>(&e) + 8), &b, 8);
        const std::uint64_t d = L::data_word(e);
        const std::uint64_t k = L::key_word(e, d);
        const TTEntry back = L::decode(k, d);
        if (!same_entry(e, back)) { check(false, "round trip " + describe(e) + " -> " + describe(back)); break; }
        // The raw readers the probe decides on give exactly the decoded fields.
        if (L::key32_of(k, d) != e.key32 || L::occupied_of(d) != e.occupied() || L::generation_of(d) != e.generation() ||
            L::depth_of(d) != e.depth || L::gen_bound_of(d) != e.gen_bound) {
            check(false, "raw readers differ from the decoded entry " + describe(e));
            break;
        }
        // A generation-only change of D keeps K valid (CAS refresh, SPEC 3.4).
        const std::uint64_t d2 = L::with_gen_bound(d, static_cast<std::uint8_t>((e.gen_bound & 7U) | (((e.gen_bound >> 3U) + 1U) << 3U)));
        const TTEntry g = L::decode(k, d2);
        if (g.key32 != e.key32) { check(false, "generation-only change broke the tag"); break; }
        // Any other single-bit change of D breaks the tag (always: test_tag_detection); checked on real words here.
        const int bit = static_cast<int>(rng() % 64U);
        if ((L::GenMask >> bit) & 1U) continue;
        const TTEntry t = L::decode(k, d ^ (1ULL << bit));
        if (t.key32 == e.key32) { check(false, "flipping D bit " + std::to_string(bit) + " kept the tag"); break; }
    }
    test_tag_detection();
}

// ---------------------------------------------------------------- 2 differential (one thread)
Move random_move(std::mt19937_64& rng) {
    Move m;
    m.from = static_cast<std::uint8_t>(rng() % 64U);
    m.to = static_cast<std::uint8_t>(rng() % 64U);
    m.promotion = static_cast<std::uint8_t>(rng() % 3U == 0 ? rng() % 7U : 0U);
    m.flags = static_cast<std::uint8_t>(rng() % 16U);
    if (rng() % 8U == 0) m = Move{};   // none
    return m;
}

void compare_tables(const TranspositionTable& a, const TranspositionTable& b, const std::string& where) {
    check(a.cluster_count() == b.cluster_count(), where + ": cluster counts");
    for (std::size_t c = 0; c < a.cluster_count(); ++c) {
        for (int s = 0; s < 4; ++s) {
            const TTEntry ea = a.debug_entry(c, s), eb = b.debug_entry(c, s);
            if (!same_entry(ea, eb)) {
                check(false, where + ": cluster " + std::to_string(c) + " slot " + std::to_string(s) + " legacy " + describe(ea) +
                                 " lockless " + describe(eb));
                return;
            }
        }
    }
}

void test_differential() {
    TranspositionTable legacy(1), lockless(1);
    lockless.set_lockless(true);
    check(!legacy.lockless() && lockless.lockless(), "modes set");
    const std::size_t clusters = legacy.cluster_count();
    std::mt19937_64 rng(77);
    // Key pool: 8 crowded clusters (16 keys each, many replacements) + 256 spread keys.
    std::vector<std::uint64_t> keys;
    for (int c = 0; c < 8; ++c) {
        const std::uint64_t top = (rng() % clusters) * (~0ULL / clusters + 1U);   // lands in one cluster
        for (int k = 0; k < 16; ++k) keys.push_back((top & ~((1ULL << 40U) - 1U)) | (rng() & ((1ULL << 40U) - 1U)));
    }
    for (int k = 0; k < 256; ++k) keys.push_back(rng());
    std::vector<std::pair<TTProbe, std::uint64_t>> stale_legacy, stale_lockless;   // handle + the key it was made for
    long long ops = 0, hits = 0;
    for (int step = 0; step < 300000; ++step) {
        const std::uint64_t key = keys[rng() % keys.size()];
        const TTProbe pa = legacy.probe(key);
        const TTProbe pb = lockless.probe(key);
        ++ops;
        if (pa.hit != pb.hit || !same_entry(pa.entry, pb.entry)) {
            check(false, "differential probe step " + std::to_string(step) + " hit " + std::to_string(pa.hit) + "/" + std::to_string(pb.hit) +
                             " legacy " + describe(pa.entry) + " lockless " + describe(pb.entry));
            return;
        }
        if (pa.hit) ++hits;
        const int score = static_cast<int>(rng() % 70000U) - 35000;   // exercises the clamp
        const int eval = static_cast<int>(rng() % 70000U) - 35000;
        const int depth = static_cast<int>(rng() % 300U) - 20;        // exercises the clamp
        // BoundNone too: such a store leaves an unoccupied slot with data in it (miss snapshots of such slots).
        const Bound bound = static_cast<Bound>(rng() % 4U);
        const bool pv = (rng() & 1U) != 0;
        const std::uint16_t hmc = static_cast<std::uint16_t>(rng() % 130U);
        const Move move = random_move(rng);
        if (rng() % 10U != 0) {
            legacy.store(pa, key, score, eval, move, depth, bound, pv, hmc);
            lockless.store(pb, key, score, eval, move, depth, bound, pv, hmc);
        }
        if (rng() % 97U == 0) { stale_legacy.emplace_back(pa, key); stale_lockless.emplace_back(pb, key); }
        if (step % 211 == 0) { legacy.new_search(); lockless.new_search(); }
        if (step % 4999 == 0 && !stale_legacy.empty()) {
            // Handles from an older epoch must be rejected by both tables (contents are compared below).
            for (std::size_t i = 0; i < stale_legacy.size(); ++i) {
                legacy.store(stale_legacy[i].first, stale_legacy[i].second, 1, 1, Move{}, 9, forge::BoundExact, false, 0);
                lockless.store(stale_lockless[i].first, stale_lockless[i].second, 1, 1, Move{}, 9, forge::BoundExact, false, 0);
            }
            stale_legacy.clear(); stale_lockless.clear();
        }
        if (step % 1000 == 0) {
            check(legacy.hashfull() == lockless.hashfull(), "hashfull at step " + std::to_string(step));
        }
        if (step % 25000 == 0) compare_tables(legacy, lockless, "contents at step " + std::to_string(step));
        if (step == 150000) { legacy.clear(); lockless.clear(); }
    }
    compare_tables(legacy, lockless, "final contents");
    std::cout << "differential: " << ops << " probes, " << hits << " hits, tables equal\n";
}

// ---------------------------------------------------------------- 3 + 4 contention fixture
struct Payload {
    Move move{};
    std::int16_t score = 0;
    std::int16_t eval = 0;
    std::uint8_t depth = 0;
    Bound bound = forge::BoundNone;
    bool pv = false;
    std::uint8_t rule50 = 0;
};

Payload payload_of(std::uint64_t key) {
    const std::uint64_t h = splitmix(key);
    Payload p;
    p.move.from = static_cast<std::uint8_t>(h & 63U);
    p.move.to = static_cast<std::uint8_t>((h >> 6U) & 63U);
    if (p.move.to == p.move.from) p.move.to = static_cast<std::uint8_t>((p.move.from + 1U) & 63U);
    p.move.flags = static_cast<std::uint8_t>((h >> 12U) & 7U);
    p.score = static_cast<std::int16_t>(static_cast<int>((h >> 16U) % 20001U) - 10000);
    p.eval = static_cast<std::int16_t>(static_cast<int>((h >> 32U) % 20001U) - 10000);
    p.depth = static_cast<std::uint8_t>(1U + (h >> 48U) % 60U);
    p.bound = static_cast<Bound>(1U + (h >> 54U) % 3U);
    p.pv = ((h >> 56U) & 1U) != 0;
    p.rule50 = static_cast<std::uint8_t>((h >> 57U) % 101U);
    return p;
}

bool matches(const TTEntry& e, const Payload& p) {
    return e.move == p.move && e.score == p.score && e.eval == p.eval && e.depth == p.depth && e.bound() == p.bound &&
           e.pv() == p.pv && e.rule50_clock == p.rule50;
}

// Test-only positive control: two words per slot behind std::atomic_ref (TSan-clean), but the tag covers only the key
// word, so a key word from one store paired with a data word from another store passes as a hit.
class NaiveTable {
public:
    explicit NaiveTable(std::size_t clusters) : clusters_(clusters), words_(clusters * 8U, 0) {}
    // returns true and fills e on a hit
    bool probe(std::uint64_t key, TTEntry& e) {
        const std::size_t c = index(key);
        const std::uint32_t tag = static_cast<std::uint32_t>(key);
        for (std::size_t s = 0; s < 4; ++s) {
            const std::uint64_t k = std::atomic_ref<std::uint64_t>(words_[c * 8U + 2U * s]).load(std::memory_order_relaxed);
            if (static_cast<std::uint32_t>(k) != tag || k == 0) continue;
            const std::uint64_t d = std::atomic_ref<std::uint64_t>(words_[c * 8U + 2U * s + 1U]).load(std::memory_order_relaxed);
            e = forge::ttlockless::decode(0, d);   // payload from D (no tag over it)
            const std::uint32_t mv = static_cast<std::uint32_t>(k >> 32U);
            e.move.from = static_cast<std::uint8_t>(mv); e.move.to = static_cast<std::uint8_t>(mv >> 8U);
            e.move.promotion = static_cast<std::uint8_t>(mv >> 16U); e.move.flags = static_cast<std::uint8_t>(mv >> 24U);
            e.key32 = tag;
            return true;
        }
        return false;
    }
    void store(std::uint64_t key, const Payload& p, std::uint32_t slot_pick) {
        const std::size_t c = index(key), s = slot_pick % 4U;
        TTEntry e;
        e.key32 = static_cast<std::uint32_t>(key);
        e.move = p.move; e.score = p.score; e.eval = p.eval; e.depth = p.depth; e.rule50_clock = p.rule50;
        e.gen_bound = static_cast<std::uint8_t>((p.pv ? 4U : 0U) | static_cast<unsigned>(p.bound));
        const std::uint64_t d = forge::ttlockless::data_word(e);
        const std::uint64_t k = static_cast<std::uint64_t>(e.key32) | (static_cast<std::uint64_t>(forge::ttlockless::move_bits(e.move)) << 32U);
        std::atomic_ref<std::uint64_t>(words_[c * 8U + 2U * s + 1U]).store(d, std::memory_order_relaxed);
        std::atomic_ref<std::uint64_t>(words_[c * 8U + 2U * s]).store(k, std::memory_order_relaxed);
    }
private:
    std::size_t index(std::uint64_t key) const { return static_cast<std::size_t>(splitmix(key >> 32U) % clusters_); }
    std::size_t clusters_;
    std::vector<std::uint64_t> words_;
};

struct FixtureResult { long long probes = 0, hits = 0, bad = 0; };

FixtureResult run_lockless_fixture(int threads, int crowded_clusters, double seconds) {
    TranspositionTable table(1);
    table.set_lockless(true);
    const std::size_t clusters = table.cluster_count();
    std::mt19937_64 rng(1000U + static_cast<unsigned>(threads * 31 + crowded_clusters));
    std::vector<std::uint64_t> keys;
    for (int c = 0; c < crowded_clusters; ++c) {
        const std::uint64_t top = (rng() % clusters) * (~0ULL / clusters + 1U);
        for (int k = 0; k < 24; ++k) keys.push_back((top & ~((1ULL << 40U) - 1U)) | (rng() & ((1ULL << 40U) - 1U)));
    }
    FixtureResult total;
    const int phases = 3;
    for (int phase = 0; phase < phases; ++phase) {
        std::atomic<bool> go{false};
        std::atomic<long long> probes{0}, hits{0}, bad{0};
        std::vector<std::thread> pool;
        const auto stop_at = std::chrono::steady_clock::now() + std::chrono::duration<double>(seconds / phases);
        for (int t = 0; t < threads; ++t) {
            pool.emplace_back([&, t]() {
                std::mt19937_64 local(splitmix(static_cast<std::uint64_t>(t) + 97U * static_cast<std::uint64_t>(phase)));
                long long p = 0, h = 0, b = 0;
                while (!go.load(std::memory_order_acquire)) std::this_thread::yield();
                while (true) {
                    for (int i = 0; i < 256; ++i) {
                        const std::uint64_t key = keys[local() % keys.size()];
                        const TTProbe probe = table.probe(key);
                        ++p;
                        const Payload want = payload_of(key);
                        if (probe.hit) {
                            ++h;
                            if (!matches(probe.entry, want)) ++b;
                        }
                        if ((local() & 3U) != 0) {
                            table.store(probe, key, want.score, want.eval, want.move, want.depth, want.bound, want.pv, want.rule50);
                        }
                    }
                    if (std::chrono::steady_clock::now() >= stop_at) break;
                }
                probes += p; hits += h; bad += b;
            });
        }
        go.store(true, std::memory_order_release);
        for (auto& th : pool) th.join();
        total.probes += probes.load(); total.hits += hits.load(); total.bad += bad.load();
        table.new_search();   // quiescent: all threads joined (generation CAS path is exercised in the next phase)
    }
    return total;
}

FixtureResult run_naive_fixture(int threads, double seconds) {
    NaiveTable table(1);
    std::mt19937_64 rng(4242);
    std::vector<std::uint64_t> keys;
    for (int k = 0; k < 24; ++k) keys.push_back(rng() | 1U);
    std::atomic<bool> go{false};
    std::atomic<long long> probes{0}, hits{0}, bad{0};
    std::vector<std::thread> pool;
    const auto stop_at = std::chrono::steady_clock::now() + std::chrono::duration<double>(seconds);
    for (int t = 0; t < threads; ++t) {
        pool.emplace_back([&, t]() {
            std::mt19937_64 local(splitmix(static_cast<std::uint64_t>(t) + 5U));
            long long p = 0, h = 0, b = 0;
            while (!go.load(std::memory_order_acquire)) std::this_thread::yield();
            while (true) {
                for (int i = 0; i < 256; ++i) {
                    const std::uint64_t key = keys[local() % keys.size()];
                    TTEntry e;
                    ++p;
                    if (table.probe(key, e)) { ++h; if (!matches(e, payload_of(key))) ++b; }
                    table.store(key, payload_of(key), static_cast<std::uint32_t>(local()));
                }
                if (std::chrono::steady_clock::now() >= stop_at) break;
            }
            probes += p; hits += h; bad += b;
        });
    }
    go.store(true, std::memory_order_release);
    for (auto& th : pool) th.join();
    return FixtureResult{probes.load(), hits.load(), bad.load()};
}

void test_contention() {
    const double seconds = seconds_env("FORGE_TT_LOCKLESS_SECONDS", 1.5);
    for (const int threads : {4, 8}) {
        for (const int crowded : {1, 4, 16}) {
            const FixtureResult r = run_lockless_fixture(threads, crowded, seconds);
            std::cout << "contention threads " << threads << " clusters " << crowded << ": probes " << r.probes << " hits " << r.hits
                      << " incoherent " << r.bad << "\n";
            check(r.hits > 0, "contention fixture produced hits");
            check(r.bad == 0, "lockless table returned an incoherent hit (threads " + std::to_string(threads) + ")");
        }
    }
    // Positive control: a validation-free two-word table under the same load must show incoherent hits.
    long long control_bad = 0, control_hits = 0;
    for (int round = 0; round < 4 && control_bad == 0; ++round) {
        const FixtureResult r = run_naive_fixture(8, seconds);
        control_bad += r.bad; control_hits += r.hits;
    }
    std::cout << "positive control (unvalidated two-word table, 8 threads): hits " << control_hits << " incoherent " << control_bad
              << (control_bad > 0 ? " -> fixture CAN detect tearing" : " -> no tearing observed") << "\n";
    // R1 review MINOR-2: a fixture that cannot see tearing proves nothing, so this is a gate, not a log line.
    // With >= 2 hardware threads and > 100k hits of an 8-thread, 24-key, one-cluster store-every-iteration load,
    // zero incoherent hits means the oracle is blind. One hardware thread can legitimately see no tearing: INCONCLUSIVE.
    const unsigned hw = std::thread::hardware_concurrency();
    if (hw >= 2) {
        check(!(control_hits > 100000 && control_bad == 0), "positive control saw no tearing: the contention fixture is blind");
    } else {
        std::cout << "positive control INCONCLUSIVE: hardware_concurrency " << hw << " (< 2)\n";
    }
}

// ---------------------------------------------------------------- 5 lifecycle
void test_lifecycle() {
    TranspositionTable t(1);
    t.set_lockless(true);
    const std::uint64_t key = 0x123456789ABCDEF1ULL;
    const Payload p = payload_of(key);
    TTProbe probe = t.probe(key);
    t.store(probe, key, p.score, p.eval, p.move, p.depth, p.bound, p.pv, p.rule50);
    probe = t.probe(key);
    check(probe.hit && matches(probe.entry, p), "stored entry is found");
    const TTProbe old = t.probe(key);
    t.new_search();
    t.store(old, key, 7, 7, Move{}, 200, forge::BoundExact, false, 0);
    const TTProbe after = t.probe(key);
    check(after.hit && after.entry.depth == p.depth, "a stale handle (new_search) is rejected");
    t.resize(2);
    check(!t.probe(key).hit, "resize empties the lockless table");
    t.store(old, key, 7, 7, Move{}, 200, forge::BoundExact, false, 0);
    check(!t.probe(key).hit, "a stale handle (resize) is rejected");
    probe = t.probe(key);
    t.store(probe, key, p.score, p.eval, p.move, p.depth, p.bound, p.pv, p.rule50);
    check(t.probe(key).hit, "store after resize");
    t.clear();
    check(!t.probe(key).hit, "clear empties the lockless table");
    probe = t.probe(key);
    t.store(probe, key, p.score, p.eval, p.move, p.depth, p.bound, p.pv, p.rule50);
    t.set_lockless(true);   // unchanged mode: no-op
    check(t.probe(key).hit, "set_lockless(same) keeps contents");
    const TTProbe before_toggle = t.probe(key);
    t.set_lockless(false);
    check(!t.lockless() && !t.probe(key).hit, "toggle to legacy empties the table");
    t.store(before_toggle, key, 7, 7, Move{}, 200, forge::BoundExact, false, 0);
    check(!t.probe(key).hit, "a stale handle (mode toggle) is rejected");
    probe = t.probe(key);
    t.store(probe, key, p.score, p.eval, p.move, p.depth, p.bound, p.pv, p.rule50);
    check(t.probe(key).hit && matches(t.probe(key).entry, p), "legacy mode works after the toggle");
    t.set_lockless(true);
    check(t.lockless() && !t.probe(key).hit, "toggle back empties the table");
    check(t.hashfull() == 0, "hashfull of an empty lockless table");
}

} // namespace

int main() {
    test_round_trip();
    test_differential();
    test_lifecycle();
    test_contention();
    if (failures == 0) {
        std::cout << "All tt_lockless groups passed\n";
        return 0;
    }
    std::cout << failures << " tt_lockless failure(s)\n";
    return 1;
}
