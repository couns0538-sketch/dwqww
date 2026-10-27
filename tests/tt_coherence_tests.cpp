// Standalone regression/stress checks for the proposed opaque TTProbe API.
// Link against the actual instrumented forge_core; no engine games are run.
#include "forge/search.hpp"

#include <array>
#include <atomic>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <new>
#include <stdexcept>
#include <random>
#include <thread>

namespace {
std::atomic<bool> fail_next_aligned_array{false};
}

// Bounded deterministic fault injection for make_unique<TTCluster[]> only.
// Delegate successful aligned-array allocations to the ordinary aligned scalar
// allocator, with matching delete overloads. No giant allocation is attempted.
void* operator new[](std::size_t size, std::align_val_t alignment) {
    if (fail_next_aligned_array.exchange(false, std::memory_order_relaxed)) throw std::bad_alloc();
    return ::operator new(size, alignment);
}
void operator delete[](void* memory, std::align_val_t alignment) noexcept {
    ::operator delete(memory, alignment);
}
void operator delete[](void* memory, std::size_t, std::align_val_t alignment) noexcept {
    ::operator delete(memory, alignment);
}

namespace {
// UCI LocklessTT: every group runs with the locked table and again with the
// lockless one (main). Single-threaded results must be identical; under
// concurrency the lockless table may turn a slot written by two threads at
// once into a miss (its key check fails), but must never return a torn entry.
bool g_lockless = false;

void apply_mode(forge::TranspositionTable& tt) { tt.set_lockless(g_lockless); }
}

namespace {
using forge::BoundExact;
using forge::BoundUpper;
using forge::Move;
using forge::TranspositionTable;

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

// Distinct verification tags in one low-index cluster for both indexing paths.
std::uint64_t collision_key(const TranspositionTable& tt, unsigned number) {
#if defined(__SIZEOF_INT128__)
    (void)tt;
    return static_cast<std::uint64_t>(number) + 1;
#else
    const std::uint64_t count = tt.cluster_count();
    const std::uint64_t step = (((std::uint64_t{1} << 32U) + count - 1) / count) * count;
    return 1 + static_cast<std::uint64_t>(number) * step;
#endif
}

Move move_for(int score) {
    const auto from = static_cast<std::uint8_t>(score % 64);
    // from==to means Move::none(), whose correct store policy preserves the
    // previous move. Publish a nonempty move so the whole tuple is correlated.
    const auto to = static_cast<std::uint8_t>((from + 1 + (score / 64) % 63) % 64);
    return Move{from, to, 0, 0};
}

void put(TranspositionTable& tt, std::uint64_t key, int score, int depth = 8,
         Move move = Move::none(), forge::Bound bound = BoundExact,
         std::uint16_t clock = 0) {
    const auto probe = tt.probe(key);
    tt.store(probe, key, score, -score, move, depth, bound, (score & 1) != 0, clock);
}

int score_of(const TranspositionTable& tt, std::uint64_t key) {
    const auto probe = tt.probe(key);
    require(probe.hit, "expected occupied key");
    return probe.entry.score;
}

void test_snapshot_and_current_slot_admission() {
    TranspositionTable tt(1);
    apply_mode(tt);
    const auto key = collision_key(tt, 0);
    put(tt, key, 101, 8, move_for(101));
    auto old = tt.probe(key);
    old.entry.score = -123;
    old.entry.key32 ^= 0xffffffffU;
    old.hit = false;
    require(score_of(tt, key) == 101, "mutating a local snapshot changed table");
    tt.store(old, key, 202, -202, move_for(202), 20, BoundExact, false, 0);
    require(score_of(tt, key) == 202, "local snapshot mutation changed private destination");
    require(old.entry.score == -123 && !old.hit, "store mutated caller snapshot");

    // Admission must use the CURRENT selected slot, not the old entry snapshot.
    const auto stale_contents = tt.probe(key);
    put(tt, key, 303, 30, move_for(303));
    tt.store(stale_contents, key, 404, -404, Move::none(), 1, BoundUpper, false, 0);
    auto current = tt.probe(key);
    require(current.entry.score == 303 && current.entry.depth == 30 &&
            current.entry.move == move_for(303), "store admitted shallow payload using stale snapshot");
    tt.store(stale_contents, key, 404, -404, move_for(404), 1, BoundUpper, false, 0);
    current = tt.probe(key);
    require(current.entry.score == 303 && current.entry.move == move_for(404),
            "rejected shallow payload did not preserve baseline independent move update");
    require(stale_contents.entry.score == 202, "intervening overwrite mutated snapshot");
}

void test_delayed_store_keeps_probe_destination() {
    TranspositionTable tt(1);
    apply_mode(tt);
    const auto x = collision_key(tt, 0), y = collision_key(tt, 1);
    const auto before_x = tt.probe(x); // Empty slot0 is frozen in this handle.
    require(!before_x.hit, "empty table unexpectedly hit");
    put(tt, y, 111); // Independent probe also chooses empty slot0.
    tt.store(before_x, x, 222, -222, move_for(222), 8, BoundExact, false, 0);
    require(!tt.probe(y).hit && score_of(tt, x) == 222,
            "delayed miss store reselected another slot or rejected ordinary overwrite");
    require(!before_x.entry.occupied(), "old empty snapshot changed after intervening store");
}

void test_replacement_ties_age_and_late_changes() {
    TranspositionTable tt(1);
    apply_mode(tt);
    std::array<std::uint64_t, 6> keys{};
    for (unsigned i = 0; i < keys.size(); ++i) keys[i] = collision_key(tt, i);
    for (unsigned i = 0; i < 4; ++i) put(tt, keys[i], 100 + static_cast<int>(i), 8);
    // A later matching key must be found even if an earlier slot is empty.
    tt.store(tt.probe(keys[0]), keys[0], 0, 0, Move::none(), 30, forge::BoundNone, false, 0);
    require(tt.probe(keys[2]).hit, "probe chose earlier empty slot before later matching key");
    tt.clear();
    for (unsigned i = 0; i < 4; ++i) put(tt, keys[i], 100 + static_cast<int>(i), 8);
    put(tt, keys[4], 200, 8);
    require(!tt.probe(keys[0]).hit && tt.probe(keys[1]).hit && tt.probe(keys[2]).hit &&
            tt.probe(keys[3]).hit, "equal-priority replacement did not choose first slot");

    // Freeze slot1 as the lowest-depth victim. Then make slot2 even lower.
    put(tt, keys[1], 201, 1);
    const auto delayed = tt.probe(keys[5]);
    put(tt, keys[2], 202, 0);
    tt.store(delayed, keys[5], 203, -203, Move::none(), 8, BoundExact, false, 0);
    require(!tt.probe(keys[1]).hit && tt.probe(keys[2]).hit && tt.probe(keys[5]).hit,
            "store reselected victim after another slot's priority changed");

    tt.clear();
    put(tt, keys[0], 301, 4); // generation0 priority4, later priority0 after aging.
    tt.new_search();
    put(tt, keys[1], 302, 1);
    put(tt, keys[2], 303, 8);
    put(tt, keys[3], 304, 8);
    put(tt, keys[4], 305, 8);
    require(!tt.probe(keys[0]).hit && tt.probe(keys[1]).hit,
            "generation aging did not preserve depth-minus-four-age victim policy");
}

void test_invalid_handles_and_lifecycle() {
    TranspositionTable tt(1), other(1);
    apply_mode(tt);
    apply_mode(other);
    const auto key = collision_key(tt, 0), same_cluster = collision_key(tt, 1);
    const auto elsewhere = std::numeric_limits<std::uint64_t>::max();
    put(tt, key, 101);
    const auto valid = tt.probe(key);
    tt.store(forge::TTProbe{}, key, 999, -999, Move::none(), 8, BoundExact, false, 0);
    tt.store(other.probe(key), key, 999, -999, Move::none(), 8, BoundExact, false, 0);
    tt.store(valid, same_cluster, 999, -999, Move::none(), 8, BoundExact, false, 0);
    tt.store(valid, elsewhere, 999, -999, Move::none(), 8, BoundExact, false, 0);
    require(score_of(tt, key) == 101 && !tt.probe(same_cluster).hit && !tt.probe(elsewhere).hit,
            "default/foreign/key-mismatched handle changed table");

    tt.new_search();
    tt.store(valid, key, 999, -999, Move::none(), 8, BoundExact, false, 0);
    require(score_of(tt, key) == 101, "new_search did not invalidate old handle");
    put(tt, key, 202);
    auto before_clear = tt.probe(key);
    tt.clear();
    tt.store(before_clear, key, 999, -999, Move::none(), 8, BoundExact, false, 0);
    require(!tt.probe(key).hit && before_clear.entry.score == 202,
            "clear did not invalidate handle/preserve local snapshot");
    put(tt, key, 303);
    const auto before_resize = tt.probe(key);
    tt.resize(2);
    tt.store(before_resize, key, 999, -999, Move::none(), 8, BoundExact, false, 0);
    require(!tt.probe(key).hit && before_resize.entry.score == 303, "resize did not invalidate handle");
    put(tt, key, 404);
    const auto before_shrink = tt.probe(key);
    tt.resize(1);
    tt.store(before_shrink, key, 999, -999, Move::none(), 8, BoundExact, false, 0);
    require(!tt.probe(key).hit, "shrinking table left stale handle usable");
    put(tt, key, 505);
    require(score_of(tt, key) == 505, "fresh handle failed after lifecycle transitions");
}

void test_resize_allocation_failure_preserves_table() {
    static_assert(alignof(forge::TTCluster) > __STDCPP_DEFAULT_NEW_ALIGNMENT__,
                  "fault injector requires over-aligned TTCluster array allocation");
    TranspositionTable tt(1);
    apply_mode(tt);
    const auto key = collision_key(tt, 0);
    put(tt, key, 101);
    const auto before = tt.probe(key);
    const auto count = tt.cluster_count();
    const auto generation = tt.generation();
    fail_next_aligned_array.store(true, std::memory_order_relaxed);
    bool threw = false;
    try { tt.resize(2); } catch (const std::bad_alloc&) { threw = true; }
    const bool unconsumed = fail_next_aligned_array.exchange(false, std::memory_order_relaxed);
    require(threw && !unconsumed, "deterministic TT allocation fault was not exercised");
    require(tt.cluster_count() == count && tt.generation() == generation && score_of(tt, key) == 101,
            "failed resize changed published count/generation/storage");
    tt.store(before, key, 202, -202, Move::none(), 8, BoundExact, false, 0);
    require(score_of(tt, key) == 202, "failed resize invalidated still-live old handle");
}

void test_hashfull_current_generation_and_wrap() {
    TranspositionTable tt(1);
    apply_mode(tt);
    for (unsigned i = 0; i < 4; ++i) put(tt, collision_key(tt, i), 100 + static_cast<int>(i));
    require(tt.hashfull() == 1, "four entries in sampled cluster must yield one permille");
    tt.new_search();
    require(tt.hashfull() == 0, "hashfull counted old-generation entries");
    for (unsigned i = 0; i < 4; ++i) put(tt, collision_key(tt, i), 200 + static_cast<int>(i));
    require(tt.hashfull() == 1, "hashfull missed current-generation stores");
    for (int i = 0; i < 31; ++i) tt.new_search();
    require(tt.generation() == 0, "generation did not wrap at32");
    put(tt, collision_key(tt, 0), 300);
    require(score_of(tt, collision_key(tt, 0)) == 300, "fresh handle failed after generation wrap");
}

void test_score_context_tracks_admitted_payload() {
    TranspositionTable tt(1);
    apply_mode(tt);
    const auto key = collision_key(tt, 0);
    put(tt, key, 101, 30, move_for(101), BoundExact, 99);
    auto probe = tt.probe(key);
    require(probe.hit && probe.entry.rule50_clock == 99 &&
            !probe.entry.score_usable(0) && !probe.entry.score_usable(98) &&
            probe.entry.score_usable(99), "near-limit score context is not selective");

    tt.store(probe, key, 202, -202, move_for(202), 1, BoundUpper, false, 0);
    probe = tt.probe(key);
    require(probe.entry.move == move_for(202) && probe.entry.score == 101 &&
            probe.entry.rule50_clock == 99,
            "independent move update changed rejected score's context");
    put(tt, key, 303, 30, move_for(303), BoundExact, 0);
    probe = tt.probe(key);
    require(probe.entry.score == 303 && probe.entry.rule50_clock == 0 &&
            probe.entry.score_usable(89) && !probe.entry.score_usable(90),
            "admitted score did not update clock or retain below90 reuse");

    put(tt, key, 404, 30, move_for(404), BoundExact,
        std::numeric_limits<std::uint16_t>::max());
    probe = tt.probe(key);
    require(probe.entry.rule50_clock == 100 && probe.entry.score_usable(65535) &&
            !probe.entry.score_usable(99), "rule50 clock storage did not saturate safely");
}

// Compare every stored field except the intentionally refreshed generation bits.
bool same_payload_except_generation(const forge::TTEntry& a, const forge::TTEntry& b) {
    return a.key32 == b.key32 && a.move == b.move && a.score == b.score &&
           a.eval == b.eval && a.depth == b.depth && a.rule50_clock == b.rule50_clock &&
           a.padding == b.padding && (a.gen_bound & 7U) == (b.gen_bound & 7U);
}

void test_generation_refresh_payload_and_handles() {
    TranspositionTable tt(1);
    apply_mode(tt);
    const auto key = collision_key(tt, 0), other_key = collision_key(tt, 1);
    for (const auto bound : {BoundUpper, forge::BoundLower, BoundExact}) {
        for (const bool pv : {false, true}) {
            tt.clear();
            tt.store(tt.probe(key), key, 123, -456, move_for(123), 23, bound, pv, 97);
            const auto before = tt.probe(key);
            tt.new_search();
            const auto refreshed = tt.probe(key);
            require(refreshed.hit && refreshed.entry.generation() == tt.generation() &&
                    same_payload_except_generation(refreshed.entry, before.entry),
                    "old occupied hit did not refresh only generation bits");
            require(before.entry.generation() == 0, "refresh mutated an older local snapshot");
            const auto repeated = tt.probe(key);
            require(repeated.entry.gen_bound == refreshed.entry.gen_bound &&
                    same_payload_except_generation(repeated.entry, refreshed.entry),
                    "current-generation repeated hit changed payload");

            // A newly refreshed hit is current for admission, even if the
            // requested nonexact score is shallower. Move updates stay independent.
            tt.store(refreshed, key, 777, -888, Move::none(), 1, BoundUpper, false, 0);
            require(same_payload_except_generation(tt.probe(key).entry, refreshed.entry),
                    "refresh failed to suppress age-only shallow overwrite or retain move");
            auto expected = refreshed.entry;
            expected.move = move_for(777);
            tt.store(refreshed, key, 777, -888, expected.move, 1, BoundUpper, false, 0);
            require(same_payload_except_generation(tt.probe(key).entry, expected),
                    "rejected shallow payload lost independent move update");

            // Refresh neither revives a previous epoch nor weakens key ownership.
            tt.store(before, key, 999, -999, Move::none(), 30, BoundExact, false, 0);
            tt.store(refreshed, other_key, 999, -999, Move::none(), 30, BoundExact, false, 0);
            require(same_payload_except_generation(tt.probe(key).entry, expected) &&
                    !tt.probe(other_key).hit, "refresh accepted stale or mismatched handle");
        }
    }
}

void test_generation_refresh_misses_and_zero_key() {
    TranspositionTable tt(1);
    apply_mode(tt);
    tt.new_search();
    const auto empty = tt.probe(0);
    require(!empty.hit && !empty.entry.occupied() && empty.entry.gen_bound == 0 &&
            tt.hashfull() == 0, "empty zero-tag slot was refreshed or treated as a hit");
    // Zero is a valid occupied verification key, not an empty-slot sentinel.
    tt.store(empty, 0, 101, -101, move_for(101), 23, BoundExact, true, 97);
    const auto zero_before = tt.probe(0);
    tt.new_search();
    const auto zero_after = tt.probe(0);
    require(zero_after.hit && zero_after.entry.generation() == tt.generation() &&
            same_payload_except_generation(zero_after.entry, zero_before.entry),
            "occupied zero key was not refreshed");
    tt.store(zero_after, 0, 202, -202, move_for(202), 30, forge::BoundNone, true, 98);
    const auto unoccupied_before = tt.probe(0);
    tt.new_search();
    const auto unoccupied_after = tt.probe(0);
    require(!unoccupied_before.hit && !unoccupied_after.hit &&
            unoccupied_after.entry.gen_bound == unoccupied_before.entry.gen_bound &&
            same_payload_except_generation(unoccupied_after.entry, unoccupied_before.entry),
            "matching BoundNone tag was refreshed");

    tt.clear();
    for (unsigned i = 0; i < 4; ++i) put(tt, collision_key(tt, i), 100 + static_cast<int>(i));
    tt.new_search();
    const auto first = tt.probe(collision_key(tt, 4));
    const auto again = tt.probe(collision_key(tt, 4));
    require(!first.hit && first.entry.occupied() && first.entry.generation() == 0 &&
            !again.hit && again.entry.gen_bound == first.entry.gen_bound &&
            same_payload_except_generation(again.entry, first.entry) && tt.hashfull() == 0,
            "miss refreshed its occupied replacement candidate or changed first-slot tie");
}

void test_generation_refresh_replacement_hashfull_and_wrap() {
    TranspositionTable tt(1);
    apply_mode(tt);
    std::array<std::uint64_t, 5> keys{};
    for (unsigned i = 0; i < keys.size(); ++i) keys[i] = collision_key(tt, i);
    put(tt, keys[0], 301, 12);
    tt.new_search();
    for (unsigned i = 1; i < 4; ++i) put(tt, keys[i], 301 + static_cast<int>(i), 8);
    // Old A has priority12-4=8, tying B/C/D. A miss alone keeps A the victim.
    const auto old_victim = tt.probe(keys[4]);
    require(!old_victim.hit && old_victim.entry.score == 301 &&
            old_victim.entry.generation() == 0 && tt.hashfull() == 0,
            "unreused old first-slot tie or hashfull changed");
    require(tt.probe(keys[0]).entry.generation() == 1 && tt.hashfull() == 1,
            "reused old occupied entry did not count toward current-generation hashfull");
    const auto new_victim = tt.probe(keys[4]);
    require(!new_victim.hit && new_victim.entry.score == 302,
            "refreshed depth12 slot was still evicted before current depth8 slot");
    tt.store(new_victim, keys[4], 305, -305, Move::none(), 8, BoundExact, false, 0);
    require(tt.probe(keys[0]).hit && !tt.probe(keys[1]).hit &&
            tt.probe(keys[2]).hit && tt.probe(keys[3]).hit && tt.probe(keys[4]).hit,
            "refresh replacement policy did not retain reused entry and evict slot1");

    tt.clear();
    for (int i = 0; i < 31; ++i) tt.new_search();
    put(tt, keys[0], 505, 23, move_for(505), forge::BoundLower, 99);
    const auto before_wrap = tt.probe(keys[0]);
    tt.new_search();
    const auto after_wrap = tt.probe(keys[0]);
    require(tt.generation() == 0 && before_wrap.entry.generation() == 31 &&
            after_wrap.hit && after_wrap.entry.generation() == 0 &&
            same_payload_except_generation(after_wrap.entry, before_wrap.entry),
            "31-to0 refresh changed payload, flags or old snapshot");
    tt.store(before_wrap, keys[0], 999, -999, Move::none(), 30, BoundExact, false, 0);
    require(same_payload_except_generation(tt.probe(keys[0]).entry, after_wrap.entry),
            "generation wrap revived a stale lifecycle handle");
}

void test_generation_refresh_concurrent_aged_hits() {
    TranspositionTable tt(1);
    apply_mode(tt);
    std::array<std::uint64_t, 4> keys{};
    for (unsigned i = 0; i < keys.size(); ++i) keys[i] = collision_key(tt, i);
    auto publish = [&](int value, unsigned bucket) {
        tt.store(tt.probe(keys[bucket]), keys[bucket], value, -value, move_for(value),
                 1 + value % 64, BoundExact, (value & 1) != 0,
                 static_cast<std::uint16_t>(value % 101));
    };
    for (unsigned i = 0; i < keys.size(); ++i) publish(1 + static_cast<int>(i), i);
    const auto old_snapshot = tt.probe(keys[0]);
    tt.new_search(); // All accessors quiescent; no lifecycle operation in threads.
    require(old_snapshot.entry.generation() == 0 && tt.hashfull() == 0,
            "aged concurrent fixture did not start with old occupied entries");
    std::atomic<int> ready{0}, aged_readers{0}, errors{0}, hits{0};
    std::atomic<bool> start{false};
    auto gate = [&] {
        ready.fetch_add(1, std::memory_order_release);
        while (!start.load(std::memory_order_acquire)) std::this_thread::yield();
    };
    auto check = [&](unsigned bucket, int expected_initial = 0) {
        const auto probe = tt.probe(keys[bucket]);
        const auto& e = probe.entry;
        const int value = e.score;
        // Lockless: a slot that two threads wrote at once reads as a miss.
        if (!probe.hit && g_lockless && expected_initial == 0) return;
        hits.fetch_add(1, std::memory_order_relaxed);
        if (!probe.hit || value < 1 || value > 10004 ||
            (expected_initial != 0 && value != expected_initial) ||
            e.eval != -value || e.depth != 1 + value % 64 || e.move != move_for(value) ||
            e.pv() != ((value & 1) != 0) || e.bound() != BoundExact ||
            e.generation() != 1 || e.rule50_clock != value % 101)
            errors.fetch_add(1, std::memory_order_relaxed);
    };
    auto wait_for_aged_reads = [&] {
        while (aged_readers.load(std::memory_order_acquire) != 2) std::this_thread::yield();
    };
    constexpr int Iterations = 10000;
    auto reader = [&](unsigned parity) {
        gate();
        // Disjoint keys and a writer barrier guarantee four actual aged hits,
        // rather than allowing stores to refresh everything before readers run.
        for (unsigned bucket = parity; bucket < keys.size(); bucket += 2)
            check(bucket, 1 + static_cast<int>(bucket));
        aged_readers.fetch_add(1, std::memory_order_release);
        wait_for_aged_reads();
        for (int i = 0; i < Iterations; ++i) check(static_cast<unsigned>(i) % 4);
    };
    std::thread writer([&] {
        gate();
        wait_for_aged_reads();
        for (int i = 1; i <= Iterations; ++i) publish(i + 4, static_cast<unsigned>(i) % 4);
    });
    std::thread r1(reader, 0), r2(reader, 1);
    std::thread monitor([&] {
        gate();
        for (int i = 0; i < 128; ++i) {
            const int count = tt.hashfull();
            if (count < 0 || count > 1) errors.fetch_add(1, std::memory_order_relaxed);
        }
    });
    while (ready.load(std::memory_order_acquire) != 4) std::this_thread::yield();
    start.store(true, std::memory_order_release);
    writer.join(); r1.join(); r2.join(); monitor.join();
    require(aged_readers.load(std::memory_order_relaxed) == 2 &&
            errors.load(std::memory_order_relaxed) == 0 && hits.load(std::memory_order_relaxed) >= 4 &&
            (g_lockless ? tt.hashfull() <= 1 : tt.hashfull() == 1) &&
            old_snapshot.entry.generation() == 0,
            "concurrent aged-hit refresh tore payload, lost recency or mutated snapshot");
}

void test_concurrent_correlated_snapshots_and_hashfull() {
    TranspositionTable tt(1);
    apply_mode(tt);
    const std::array<std::uint64_t, 2> keys{collision_key(tt, 0), collision_key(tt, 1)};
    auto publish = [&](int value, unsigned bucket) {
        const auto probe = tt.probe(keys[bucket]);
        tt.store(probe, keys[bucket], value, -value, move_for(value), 1 + value % 64,
                 BoundExact, (value & 1) != 0, static_cast<std::uint16_t>(value % 101));
    };
    publish(1, 0);
    publish(2, 1);
    std::atomic<int> ready{0}, errors{0};
    std::atomic<bool> start{false};
    auto gate = [&] {
        ready.fetch_add(1, std::memory_order_release);
        while (!start.load(std::memory_order_acquire)) std::this_thread::yield();
    };
    constexpr int Iterations = 10000;
    auto writer = [&](int offset) {
        gate();
        for (int i = 1; i <= Iterations; ++i) publish(offset + i, static_cast<unsigned>(i & 1));
    };
    std::atomic<int> hits{0};
    auto reader = [&] {
        gate();
        for (int i = 0; i < Iterations; ++i) {
            const auto probe = tt.probe(keys[static_cast<unsigned>(i & 1)]);
            const auto& e = probe.entry;
            const int value = e.score;
            if (!probe.hit && g_lockless) continue;  // a slot written by both writers at once
            hits.fetch_add(1, std::memory_order_relaxed);
            if (!probe.hit || value < 1 || value > 2 * Iterations || e.eval != -value ||
                e.depth != 1 + value % 64 || e.move != move_for(value) ||
                e.pv() != ((value & 1) != 0) || e.bound() != BoundExact || e.generation() != 0 ||
                e.rule50_clock != value % 101)
                errors.fetch_add(1, std::memory_order_relaxed);
        }
    };
    std::thread w1(writer, 0), w2(writer, Iterations), r1(reader), r2(reader);
    std::thread monitor([&] {
        gate();
        for (int i = 0; i < 128; ++i) {
            const int count = tt.hashfull();
            if (count < 0 || count > 1000) errors.fetch_add(1, std::memory_order_relaxed);
        }
    });
    while (ready.load(std::memory_order_acquire) != 5) std::this_thread::yield();
    start.store(true, std::memory_order_release);
    w1.join(); w2.join(); r1.join(); r2.join(); monitor.join();
    require(errors.load(std::memory_order_relaxed) == 0 && hits.load(std::memory_order_relaxed) > 0,
            "concurrent probe observed a torn tuple");
}

// ---- UCI LocklessTT only ---------------------------------------------------

forge::TTEntry random_entry(std::mt19937_64& rng) {
    forge::TTEntry e;
    const std::uint64_t a = rng(), b = rng();
    std::memcpy(&e, &a, sizeof a);
    std::memcpy(reinterpret_cast<unsigned char*>(&e) + 8, &b, sizeof b);
    return e;
}

bool same_bytes(const forge::TTEntry& a, const forge::TTEntry& b) { return std::memcmp(&a, &b, sizeof a) == 0; }

void test_lockless_encoding_round_trip() {
    std::mt19937_64 rng(0x0b1e55ed5eed0001ULL);
    for (int i = 0; i < 200000; ++i) {
        const auto e = random_entry(rng);
        const auto words = TranspositionTable::encode_lockless(e);
        require(same_bytes(TranspositionTable::decode_lockless(words[0], words[1]), e),
                "lockless encode/decode is not the identity");
    }
}

// Two writes to one slot interleaved leave the first word of one and the second
// word of the other. Such a torn slot must not decode to the key of either
// write (a probe for that position then misses). The common case in a search is
// two threads storing the same position with different data, so most pairs
// share the key; one in four has an unrelated key.
void test_lockless_torn_pairs_detected() {
    std::mt19937_64 rng(0x0b1e55ed5eed0002ULL);
    long long torn = 0, accepted = 0;
    for (int i = 0; i < 1000000; ++i) {
        const auto a = random_entry(rng);
        auto b = random_entry(rng);
        if (i % 4 != 3) b.key32 = a.key32;
        if (i % 8 == 1) b.move = a.move;                                          // only the payload differs
        if (i % 8 == 2) std::memcpy(reinterpret_cast<unsigned char*>(&b) + 8,     // only the move differs
                                    reinterpret_cast<const unsigned char*>(&a) + 8, 8);
        const auto wa = TranspositionTable::encode_lockless(a);
        const auto wb = TranspositionTable::encode_lockless(b);
        for (const auto& mixed : {TranspositionTable::decode_lockless(wa[0], wb[1]),
                                  TranspositionTable::decode_lockless(wb[0], wa[1])}) {
            if (same_bytes(mixed, a) || same_bytes(mixed, b)) continue;  // not torn: equals one write
            ++torn;
            if (mixed.key32 == a.key32 || mixed.key32 == b.key32) ++accepted;
        }
    }
    std::cout << "lockless torn pairs: " << torn << " torn slots, " << accepted << " decoded to a written key\n";
    require(torn > 1500000 && accepted == 0, "a torn lockless slot decoded to the key of one of its writes");
}

// Single-threaded, the lockless table makes exactly the locked table's
// decisions (probe hits, replacement victims, admission, generation refresh,
// hashfull): the reason a search with Threads=1 is unchanged.
void test_lockless_matches_locked_sequence() {
    TranspositionTable locked(1), lockless(1);
    lockless.set_lockless(true);
    std::mt19937_64 rng(0x0b1e55ed5eed0003ULL);
    std::array<std::uint64_t, 48> keys{};
    for (unsigned i = 0; i < keys.size(); ++i) {
        // 48 keys over 6 clusters: constant replacement pressure.
        keys[i] = (static_cast<std::uint64_t>(i % 6) << 50U) + collision_key(locked, i);
    }
    for (int step = 0; step < 300000; ++step) {
        if (step % 20000 == 19999) {
            locked.new_search();
            lockless.new_search();
        }
        const std::uint64_t key = keys[static_cast<std::size_t>(rng() % keys.size())];
        const auto p1 = locked.probe(key);
        const auto p2 = lockless.probe(key);
        require(p1.hit == p2.hit && same_bytes(p1.entry, p2.entry), "lockless probe differs from the locked probe");
        if (rng() % 3 != 0) {
            const int score = static_cast<int>(rng() % 4001) - 2000;
            const int depth = static_cast<int>(rng() % 40);
            const Move move = rng() % 5 == 0 ? Move::none() : move_for(static_cast<int>(rng() % 4096) + 1);
            const auto bound = static_cast<forge::Bound>(1 + rng() % 3);
            const bool pv = (rng() & 1U) != 0;
            const auto clock = static_cast<std::uint16_t>(rng() % 120);
            locked.store(p1, key, score, -score, move, depth, bound, pv, clock);
            lockless.store(p2, key, score, -score, move, depth, bound, pv, clock);
        }
        if (step % 5000 == 0) require(locked.hashfull() == lockless.hashfull(), "lockless hashfull differs");
    }
    for (const auto key : keys) {
        const auto p1 = locked.probe(key);
        const auto p2 = lockless.probe(key);
        require(p1.hit == p2.hit && same_bytes(p1.entry, p2.entry), "final lockless table state differs");
    }
}

void test_lockless_mode_switch_clears() {
    TranspositionTable tt(1);
    const auto key = collision_key(tt, 0);
    put(tt, key, 77);
    tt.set_lockless(true);
    require(tt.lockless() && !tt.probe(key).hit, "switching to lockless did not clear the table");
    put(tt, key, 78);
    tt.set_lockless(true);
    require(score_of(tt, key) == 78, "setting the same mode cleared the table");
    tt.set_lockless(false);
    require(!tt.lockless() && !tt.probe(key).hit, "switching back to locked did not clear the table");
}
} // namespace

int main() {
    try {
        int groups = 0;
        for (const bool lockless : {false, true}) {
            g_lockless = lockless;
            test_snapshot_and_current_slot_admission();
            test_delayed_store_keeps_probe_destination();
            test_replacement_ties_age_and_late_changes();
            test_invalid_handles_and_lifecycle();
            test_resize_allocation_failure_preserves_table();
            test_hashfull_current_generation_and_wrap();
            test_score_context_tracks_admitted_payload();
            test_generation_refresh_payload_and_handles();
            test_generation_refresh_misses_and_zero_key();
            test_generation_refresh_replacement_hashfull_and_wrap();
            test_generation_refresh_concurrent_aged_hits();
            test_concurrent_correlated_snapshots_and_hashfull();
            groups += 12;
            std::cout << "12 TT coherence/regression groups passed (" << (lockless ? "LocklessTT" : "locked") << " table)\n";
        }
        g_lockless = false;
        test_lockless_encoding_round_trip();
        test_lockless_torn_pairs_detected();
        test_lockless_matches_locked_sequence();
        test_lockless_mode_switch_clears();
        groups += 4;
        std::cout << "4 LocklessTT groups passed\nAll " << groups << " TT groups passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
