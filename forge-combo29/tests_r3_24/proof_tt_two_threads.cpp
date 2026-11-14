// Two-thread form of audit finding 8.
// Thread A probes key_a and holds that probe. Thread B fills the probed slot
// with another key, then stores a depth-14 exact score for key_a in a later
// slot. Thread A then stores a depth-2 upper bound through the original probe.
// Probe must still return the depth-14 score. Threads >= 2 search this way:
// both workers take the striped lock (the exclusive lease is only taken for
// one worker).

#include "forge/search.hpp"

#include <atomic>
#include <cstdint>
#include <iostream>
#include <thread>

namespace {

const std::uint64_t key_a = 0x4242424211111111ULL;
const std::uint64_t key_other = 0x4242424222222222ULL;

bool visible(const forge::TTProbe& probe, int depth, int score) {
    return probe.hit && static_cast<int>(probe.entry.depth) == depth && probe.entry.score == score &&
           probe.entry.bound() == forge::BoundExact;
}

int fail(const char* what) {
    std::cerr << "FAIL " << what << "\n";
    return 1;
}

// One ordered interleaving. Returns 0 when the deep score stays visible.
int interleave_once(forge::TranspositionTable& tt) {
    tt.clear();
    std::atomic<int> phase{0};

    std::thread late([&] {
        const forge::TTProbe p_shallow = tt.probe(key_a);
        if (p_shallow.hit) {
            phase.store(-1, std::memory_order_release);
            return;
        }
        phase.store(1, std::memory_order_release);
        for (;;) {
            const int step = phase.load(std::memory_order_acquire);
            if (step == 2 || step < 0) break;
            std::this_thread::yield();
        }
        if (phase.load(std::memory_order_acquire) != 2) return;
        tt.store(p_shallow, key_a, -50, 100, forge::Move{8, 16, 0, 0}, 2, forge::BoundUpper, false, 0);
        phase.store(3, std::memory_order_release);
    });

    std::thread writer([&] {
        for (;;) {
            const int step = phase.load(std::memory_order_acquire);
            if (step == 1 || step < 0) break;
            std::this_thread::yield();
        }
        if (phase.load(std::memory_order_acquire) != 1) return;
        const forge::TTProbe p_other = tt.probe(key_other);
        tt.store(p_other, key_other, 15, 15, forge::Move{12, 28, 0, 0}, 3, forge::BoundExact, false, 0);
        const forge::TTProbe p_deep = tt.probe(key_a);
        if (p_deep.hit) {
            phase.store(-2, std::memory_order_release);
            return;
        }
        tt.store(p_deep, key_a, 777, 100, forge::Move{6, 21, 0, 0}, 14, forge::BoundExact, true, 0);
        if (!visible(tt.probe(key_a), 14, 777)) {
            phase.store(-3, std::memory_order_release);
            return;
        }
        phase.store(2, std::memory_order_release);
    });

    late.join();
    writer.join();

    const int step = phase.load(std::memory_order_acquire);
    if (step != 3) {
        std::cerr << "FAIL interleaving stopped at phase " << step << "\n";
        return 1;
    }
    const forge::TTProbe after = tt.probe(key_a);
    if (!visible(after, 14, 777) || !after.entry.pv()) {
        return fail("two-thread shallow store hid the deeper score");
    }
    if (after.entry.move.from != 6 || after.entry.move.to != 21) {
        return fail("two-thread shallow store replaced the deeper move");
    }
    if (!visible(tt.probe(key_other), 3, 15)) return fail("two-thread store dropped the colliding key");
    return 0;
}

// Thread A holds a miss. Thread B writes the colliding key and a shallow
// key_a. Thread A then stores the depth-14 exact score through the old probe.
int interleave_deep_late(forge::TranspositionTable& tt) {
    tt.clear();
    std::atomic<int> phase{0};

    std::thread late([&] {
        const forge::TTProbe p_deep = tt.probe(key_a);
        if (p_deep.hit) {
            phase.store(-1, std::memory_order_release);
            return;
        }
        phase.store(1, std::memory_order_release);
        for (;;) {
            const int step = phase.load(std::memory_order_acquire);
            if (step == 2 || step < 0) break;
            std::this_thread::yield();
        }
        if (phase.load(std::memory_order_acquire) != 2) return;
        tt.store(p_deep, key_a, 777, 100, forge::Move{6, 21, 0, 0}, 14, forge::BoundExact, true, 0);
        phase.store(3, std::memory_order_release);
    });

    std::thread writer([&] {
        for (;;) {
            const int step = phase.load(std::memory_order_acquire);
            if (step == 1 || step < 0) break;
            std::this_thread::yield();
        }
        if (phase.load(std::memory_order_acquire) != 1) return;
        const forge::TTProbe p_other = tt.probe(key_other);
        tt.store(p_other, key_other, 15, 15, forge::Move{12, 28, 0, 0}, 3, forge::BoundExact, false, 0);
        const forge::TTProbe p_shallow = tt.probe(key_a);
        if (p_shallow.hit) {
            phase.store(-2, std::memory_order_release);
            return;
        }
        tt.store(p_shallow, key_a, -50, 40, forge::Move{8, 16, 0, 0}, 2, forge::BoundUpper, false, 0);
        phase.store(2, std::memory_order_release);
    });

    late.join();
    writer.join();
    if (phase.load(std::memory_order_acquire) != 3) {
        std::cerr << "FAIL deep-late phase " << phase.load(std::memory_order_acquire) << "\n";
        return 1;
    }
    const forge::TTProbe after = tt.probe(key_a);
    if (!visible(after, 14, 777) || after.entry.move.from != 6 || after.entry.move.to != 21 ||
        after.entry.eval != 100 || !after.entry.pv()) {
        return fail("two-thread deeper store did not replace the shallow entry");
    }
    if (!visible(tt.probe(key_other), 3, 15)) return fail("two-thread deeper store dropped the colliding key");
    return 0;
}

// Both threads keep probing and storing with no extra barrier, then stop.
// A sanitizer build is what makes a torn cluster entry visible.
int hammer(forge::TranspositionTable& tt) {
    tt.clear();
    constexpr int kRounds = 20000;
    std::thread upper([&] {
        for (int i = 0; i < kRounds; ++i) {
            const forge::TTProbe probe = tt.probe(key_a);
            tt.store(probe, key_a, -50, 100, forge::Move{8, 16, 0, 0}, 2, forge::BoundUpper, false, 0);
        }
    });
    std::thread exact([&] {
        for (int i = 0; i < kRounds; ++i) {
            const forge::TTProbe other = tt.probe(key_other);
            tt.store(other, key_other, 15, 15, forge::Move{12, 28, 0, 0}, 3, forge::BoundExact, false, 0);
            const forge::TTProbe deep = tt.probe(key_a);
            tt.store(deep, key_a, 777, 100, forge::Move{6, 21, 0, 0}, 14, forge::BoundExact, true, 0);
        }
    });
    upper.join();
    exact.join();
    const forge::TTProbe after = tt.probe(key_a);
    if (!after.hit) return fail("hammer left key_a empty");
    if (after.entry.score != 777 && after.entry.score != -50) {
        std::cerr << "FAIL hammer score " << after.entry.score << "\n";
        return 1;
    }
    return 0;
}

int search_two_workers(forge::Searcher::TTAccess access) {
    forge::Searcher searcher(16, 2);
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) return fail("startpos");
    forge::SearchLimits limits;
    limits.depth = 4;
    searcher.reset_stop();
    const forge::SearchInfo info = searcher.search(board, limits, false, access);
    if (info.nodes == 0) return fail("two-worker search reported no nodes");
    if (info.best_move.is_none()) return fail("two-worker search returned no move");
    for (const forge::Move move : board.legal_moves()) {
        if (move == info.best_move) {
            std::cout << "two-worker depth 4 nodes=" << info.nodes
                      << " access=" << (access == forge::Searcher::TTAccess::Shared ? "shared" : "exclusive")
                      << "\n";
            return 0;
        }
    }
    return fail("two-worker best move is illegal");
}

}  // namespace

std::size_t cluster_index(std::uint64_t key, std::size_t count) {
    using u128 = unsigned __int128;
    return static_cast<std::size_t>((static_cast<u128>(key) * static_cast<u128>(count)) >> 64);
}

int main() {
    forge::TranspositionTable tt(1);
    if (cluster_index(key_a, tt.cluster_count()) != cluster_index(key_other, tt.cluster_count())) {
        return fail("keys do not share a cluster; the shadow case is not reached");
    }
    if (hammer(tt) != 0) return 1;
    std::cout << "PASS hammer\n";
    constexpr int kRepeats = 100;
    for (int i = 0; i < kRepeats; ++i) {
        if (interleave_once(tt) != 0) {
            std::cerr << "FAIL at repeat " << i << "\n";
            return 1;
        }
    }
    const forge::TTProbe kept = tt.probe(key_a);
    std::cout << "PASS two-thread interleaving x" << kRepeats
              << " kept move " << static_cast<int>(kept.entry.move.from)
              << "->" << static_cast<int>(kept.entry.move.to) << "\n";
    for (int i = 0; i < kRepeats; ++i) {
        if (interleave_deep_late(tt) != 0) {
            std::cerr << "FAIL deep-late at repeat " << i << "\n";
            return 1;
        }
    }
    std::cout << "PASS two-thread deeper store x" << kRepeats << "\n";
    if (search_two_workers(forge::Searcher::TTAccess::Shared) != 0) return 1;
    if (search_two_workers(forge::Searcher::TTAccess::Exclusive) != 0) return 1;
    std::cout << "PASS two-worker search\n";
    return 0;
}
