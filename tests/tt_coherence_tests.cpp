// Standalone regression/stress checks for the proposed opaque TTProbe API.
// Link against the actual instrumented forge_core; no engine games are run.
#include "forge/search.hpp"

#include <array>
#include <atomic>
#include <cstdint>
#include <iostream>
#include <limits>
#include <new>
#include <stdexcept>
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
    return Move{static_cast<std::uint8_t>(score % 64),
                static_cast<std::uint8_t>((score / 64) % 64), 0, 0};
}

void put(TranspositionTable& tt, std::uint64_t key, int score, int depth = 8,
         Move move = Move::none(), forge::Bound bound = BoundExact) {
    const auto probe = tt.probe(key);
    tt.store(probe, key, score, -score, move, depth, bound, (score & 1) != 0);
}

int score_of(const TranspositionTable& tt, std::uint64_t key) {
    const auto probe = tt.probe(key);
    require(probe.hit, "expected occupied key");
    return probe.entry.score;
}

void test_snapshot_and_current_slot_admission() {
    TranspositionTable tt(1);
    const auto key = collision_key(tt, 0);
    put(tt, key, 101, 8, move_for(101));
    auto old = tt.probe(key);
    old.entry.score = -123;
    old.entry.key32 ^= 0xffffffffU;
    old.hit = false;
    require(score_of(tt, key) == 101, "mutating a local snapshot changed table");
    tt.store(old, key, 202, -202, move_for(202), 20, BoundExact, false);
    require(score_of(tt, key) == 202, "local snapshot mutation changed private destination");
    require(old.entry.score == -123 && !old.hit, "store mutated caller snapshot");

    // Admission must use the CURRENT selected slot, not the old entry snapshot.
    const auto stale_contents = tt.probe(key);
    put(tt, key, 303, 30, move_for(303));
    tt.store(stale_contents, key, 404, -404, Move::none(), 1, BoundUpper, false);
    auto current = tt.probe(key);
    require(current.entry.score == 303 && current.entry.depth == 30 &&
            current.entry.move == move_for(303), "store admitted shallow payload using stale snapshot");
    tt.store(stale_contents, key, 404, -404, move_for(404), 1, BoundUpper, false);
    current = tt.probe(key);
    require(current.entry.score == 303 && current.entry.move == move_for(404),
            "rejected shallow payload did not preserve baseline independent move update");
    require(stale_contents.entry.score == 202, "intervening overwrite mutated snapshot");
}

void test_delayed_store_keeps_probe_destination() {
    TranspositionTable tt(1);
    const auto x = collision_key(tt, 0), y = collision_key(tt, 1);
    const auto before_x = tt.probe(x); // Empty slot0 is frozen in this handle.
    require(!before_x.hit, "empty table unexpectedly hit");
    put(tt, y, 111); // Independent probe also chooses empty slot0.
    tt.store(before_x, x, 222, -222, move_for(222), 8, BoundExact, false);
    require(!tt.probe(y).hit && score_of(tt, x) == 222,
            "delayed miss store reselected another slot or rejected ordinary overwrite");
    require(!before_x.entry.occupied(), "old empty snapshot changed after intervening store");
}

void test_replacement_ties_age_and_late_changes() {
    TranspositionTable tt(1);
    std::array<std::uint64_t, 6> keys{};
    for (unsigned i = 0; i < keys.size(); ++i) keys[i] = collision_key(tt, i);
    for (unsigned i = 0; i < 4; ++i) put(tt, keys[i], 100 + static_cast<int>(i), 8);
    // A later matching key must be found even if an earlier slot is empty.
    tt.store(tt.probe(keys[0]), keys[0], 0, 0, Move::none(), 30, forge::BoundNone, false);
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
    tt.store(delayed, keys[5], 203, -203, Move::none(), 8, BoundExact, false);
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
    const auto key = collision_key(tt, 0), same_cluster = collision_key(tt, 1);
    const auto elsewhere = std::numeric_limits<std::uint64_t>::max();
    put(tt, key, 101);
    const auto valid = tt.probe(key);
    tt.store(forge::TTProbe{}, key, 999, -999, Move::none(), 8, BoundExact, false);
    tt.store(other.probe(key), key, 999, -999, Move::none(), 8, BoundExact, false);
    tt.store(valid, same_cluster, 999, -999, Move::none(), 8, BoundExact, false);
    tt.store(valid, elsewhere, 999, -999, Move::none(), 8, BoundExact, false);
    require(score_of(tt, key) == 101 && !tt.probe(same_cluster).hit && !tt.probe(elsewhere).hit,
            "default/foreign/key-mismatched handle changed table");

    tt.new_search();
    tt.store(valid, key, 999, -999, Move::none(), 8, BoundExact, false);
    require(score_of(tt, key) == 101, "new_search did not invalidate old handle");
    put(tt, key, 202);
    auto before_clear = tt.probe(key);
    tt.clear();
    tt.store(before_clear, key, 999, -999, Move::none(), 8, BoundExact, false);
    require(!tt.probe(key).hit && before_clear.entry.score == 202,
            "clear did not invalidate handle/preserve local snapshot");
    put(tt, key, 303);
    const auto before_resize = tt.probe(key);
    tt.resize(2);
    tt.store(before_resize, key, 999, -999, Move::none(), 8, BoundExact, false);
    require(!tt.probe(key).hit && before_resize.entry.score == 303, "resize did not invalidate handle");
    put(tt, key, 404);
    const auto before_shrink = tt.probe(key);
    tt.resize(1);
    tt.store(before_shrink, key, 999, -999, Move::none(), 8, BoundExact, false);
    require(!tt.probe(key).hit, "shrinking table left stale handle usable");
    put(tt, key, 505);
    require(score_of(tt, key) == 505, "fresh handle failed after lifecycle transitions");
}

void test_resize_allocation_failure_preserves_table() {
    static_assert(alignof(forge::TTCluster) > __STDCPP_DEFAULT_NEW_ALIGNMENT__,
                  "fault injector requires over-aligned TTCluster array allocation");
    TranspositionTable tt(1);
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
    tt.store(before, key, 202, -202, Move::none(), 8, BoundExact, false);
    require(score_of(tt, key) == 202, "failed resize invalidated still-live old handle");
}

void test_hashfull_current_generation_and_wrap() {
    TranspositionTable tt(1);
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

void test_concurrent_correlated_snapshots_and_hashfull() {
    TranspositionTable tt(1);
    const std::array<std::uint64_t, 2> keys{collision_key(tt, 0), collision_key(tt, 1)};
    auto publish = [&](int value, unsigned bucket) {
        const auto probe = tt.probe(keys[bucket]);
        tt.store(probe, keys[bucket], value, -value, move_for(value), 1 + value % 64,
                 BoundExact, (value & 1) != 0);
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
    auto reader = [&] {
        gate();
        for (int i = 0; i < Iterations; ++i) {
            const auto probe = tt.probe(keys[static_cast<unsigned>(i & 1)]);
            const auto& e = probe.entry;
            const int value = e.score;
            if (!probe.hit || value < 1 || value > 2 * Iterations || e.eval != -value ||
                e.depth != 1 + value % 64 || e.move != move_for(value) ||
                e.pv() != ((value & 1) != 0) || e.bound() != BoundExact || e.generation() != 0)
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
    require(errors.load(std::memory_order_relaxed) == 0, "concurrent probe observed a torn tuple");
}
} // namespace

int main() {
    try {
        test_snapshot_and_current_slot_admission();
        test_delayed_store_keeps_probe_destination();
        test_replacement_ties_age_and_late_changes();
        test_invalid_handles_and_lifecycle();
        test_resize_allocation_failure_preserves_table();
        test_hashfull_current_generation_and_wrap();
        test_concurrent_correlated_snapshots_and_hashfull();
        std::cout << "All7 TT coherence/regression groups passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
