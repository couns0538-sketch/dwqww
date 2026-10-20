// Independent actual-library API checks. Link with --wrap=pthread_mutex_lock.
// No private access, production changes, sleep-based assertions, or concurrent lifecycle mutation.
#include "forge/search.hpp"
#include <array>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <pthread.h>
#include <streambuf>
#include <stdexcept>
#include <string>
#include <thread>

namespace {
thread_local unsigned role = 0; // Probe1, store2, hashfull4, owner8.
thread_local unsigned owner_locks = 0;
std::atomic<bool> proof_phase{false};
std::atomic<unsigned> attempted{0}, busy{0}, completed{0};
std::atomic<bool> paused{false}, resume_owner{false};
std::atomic<unsigned> inject_owner_lock_call{0};
std::atomic<bool> injected_lock_failure{false};
forge::TTProbe seed;
constexpr std::uint64_t Target = 21;

[[noreturn]] void fail(const char* reason) {
    std::cerr << "FAIL " << reason << '\n';
    std::_Exit(3); // A failed synchronization check must not hang joining blocked test threads.
}
void require(bool condition, const char* reason) { if (!condition) fail(reason); }
template<class Predicate> void await(Predicate condition, const char* reason) {
    const auto end = std::chrono::steady_clock::now() + std::chrono::seconds(20);
    while (!condition()) {
        if (std::chrono::steady_clock::now() >= end) fail(reason);
        std::this_thread::yield();
    }
}
forge::Move move_for(int value) {
    return forge::Move{static_cast<std::uint8_t>(value % 64),
                       static_cast<std::uint8_t>((value % 64 + 1) % 64), 0, 0};
}
void put(forge::TranspositionTable& tt, std::uint64_t key, int value,
         int depth = 255, forge::Bound bound = forge::BoundExact) {
    const auto probe = tt.probe(key);
    tt.store(probe, key, value, -value, move_for(value), depth, bound,
             (value & 1) != 0, static_cast<std::uint16_t>(value % 101));
}
void tuple(const forge::TTProbe& probe) {
    if (!probe.hit) return; // Another legal replacement may evict the diagnostic key in SMP.
    const int value = probe.entry.score;
    require(value == 303 || value == 707, "foreign probe published an unexpected diagnostic payload");
    require(probe.entry.eval == -value && probe.entry.depth == 255 &&
            probe.entry.move == move_for(value) && probe.entry.bound() == forge::BoundExact &&
            probe.entry.pv() == ((value & 1) != 0) && probe.entry.rule50_clock == value % 101,
            "foreign probe observed a torn diagnostic tuple");
}
void owner_semantics(forge::TranspositionTable& tt) {
#if defined(__SIZEOF_INT128__)
    // Small distinct keys share cluster0 with multiply-high indexing.
    for (std::uint64_t key = 1; key <= 4; ++key) put(tt, key, 100 + static_cast<int>(key));
    const auto delayed = tt.probe(Target);
    put(tt, 22, 202);
    tt.store(delayed, Target, 303, -303, move_for(303), 255, forge::BoundExact,
             true, static_cast<std::uint16_t>(303 % 101));
    require(!tt.probe(22).hit && tt.probe(Target).entry.score == 303,
            "delayed store reselected its probe-time slot");
    auto snapshot = tt.probe(Target);
    snapshot.entry.score = -99;
    snapshot.hit = false;
    require(tt.probe(Target).entry.score == 303, "snapshot mutation escaped into live storage");
    tt.store(snapshot, Target, 404, -404, forge::Move::none(), 1, forge::BoundUpper, false, 99);
    const auto current = tt.probe(Target);
    require(current.entry.score == 303 && current.entry.eval == -303 &&
            current.entry.rule50_clock == 303 % 101 && current.entry.move == move_for(303),
            "shallow admission used stale snapshot or changed score context");
    tt.store(forge::TTProbe{}, Target, 999, 999, forge::Move::none(), 255,
             forge::BoundExact, false, 0);
    require(tt.probe(Target).entry.score == 303, "default opaque handle was accepted");
#else
    fail("this independent collision fixture requires the audited multiply-high indexing build");
#endif
}

class PauseBuffer final : public std::streambuf {
    forge::Searcher& searcher_;
    bool did_pause_ = false;
    bool semantics_;
public:
    unsigned acquired_before_pause = 0;
    PauseBuffer(forge::Searcher& searcher, bool semantics) : searcher_(searcher), semantics_(semantics) {}
private:
    void inspect_and_pause() {
        if (role != 8 || did_pause_) return;
        did_pause_ = true;
        auto& tt = searcher_.transposition_table();
        if (semantics_) owner_semantics(tt);
        put(tt, Target, 303);
        seed = tt.probe(Target); // Current search epoch, copied before publishing paused.
        require(seed.hit, "owner could not seed the actual search table");
        acquired_before_pause = owner_locks;
        proof_phase.store(true, std::memory_order_release);
        paused.store(true, std::memory_order_release);
        await([] { return resume_owner.load(std::memory_order_acquire); }, "owner release deadline");
    }
    std::streamsize xsputn(const char*, std::streamsize size) override {
        inspect_and_pause();
        return size;
    }
    int_type overflow(int_type ch) override { inspect_and_pause(); return traits_type::not_eof(ch); }
    int sync() override { return 0; }
};

void run_paused(forge::Searcher& searcher, forge::Searcher::TTAccess policy,
                bool expect_exclusive, const char* name) {
    searcher.reset_stop();
    attempted = 0; busy = 0; completed = 0; paused = false; resume_owner = false;
    proof_phase = false;
    PauseBuffer capture(searcher, searcher.threads() == 1);
    auto* const previous = std::cout.rdbuf(&capture);
    forge::Board board;
    forge::SearchLimits limits;
    limits.depth = 64;
    limits.infinite = true;
    forge::SearchInfo answer;
    std::thread owner([&] {
        role = 8;
        owner_locks = 0;
        answer = policy == forge::Searcher::TTAccess::Shared
            ? searcher.search(board, limits, true) // Exercise the omitted/default policy argument.
            : searcher.search(board, limits, true, policy);
        role = 0;
    });
    await([] { return paused.load(std::memory_order_acquire); }, "real search did not reach first info callback");
    std::array<std::thread, 3> diagnostics;
    diagnostics[0] = std::thread([&] {
        role = 1;
        tuple(searcher.transposition_table().probe(Target));
        completed.fetch_or(1, std::memory_order_release);
    });
    diagnostics[1] = std::thread([&] {
        role = 2;
        searcher.transposition_table().store(seed, Target, 707, -707, move_for(707), 255,
                                             forge::BoundExact, true, 707 % 101);
        completed.fetch_or(2, std::memory_order_release);
    });
    diagnostics[2] = std::thread([&] {
        role = 4;
        const int value = searcher.hashfull_permille();
        require(value >= 0 && value <= 1000, "foreign hashfull outside valid range");
        completed.fetch_or(4, std::memory_order_release);
    });
    if (expect_exclusive) {
        await([] { return busy.load(std::memory_order_acquire) == 7; },
              "foreign methods did not all encounter an actually contended lock");
        require(completed.load(std::memory_order_acquire) == 0,
                "foreign entry operation completed while owner lease was paused");
    } else {
        await([] { return completed.load(std::memory_order_acquire) == 7; },
              "default/SMP access unexpectedly blocked for the whole search");
    }
    // This is an actual external stop of an infinite search. No lifecycle call
    // occurs until both search and every foreign accessor have joined.
    searcher.stop();
    proof_phase.store(false, std::memory_order_release);
    resume_owner.store(true, std::memory_order_release);
    owner.join();
    for (auto& diagnostic : diagnostics) diagnostic.join();
    std::cout.rdbuf(previous);
    require(completed.load() == 7, "a diagnostic did not finish after search returned");
    require(answer.nodes > 0 && answer.depth >= 1 &&
            board.parse_uci(forge::Board::move_to_uci(answer.best_move)).has_value(),
            "externally stopped search did not return a legal completed iteration");
    if (searcher.threads() == 1) {
        const auto final = searcher.transposition_table().probe(Target);
        require(final.hit && final.entry.score == 707, "foreign store did not publish after lease release");
        tuple(final);
    }
    const auto stale = searcher.transposition_table().probe(Target);
    searcher.resize_hash(2);
    searcher.transposition_table().store(stale, Target, 999, 999, forge::Move::none(), 255,
                                         forge::BoundExact, false, 0);
    require(!searcher.transposition_table().probe(Target).hit,
            "post-return resize left an old opaque handle usable");
    searcher.clear_hash();
    searcher.clear();
    std::cout << "PASS " << name << " owner_lock_calls=" << capture.acquired_before_pause
              << " actual_foreign_busy_bits=" << busy.load() << '\n';
}

void test_nested_other_table() {
    forge::Searcher outer(1, 1), inner(1, 1);
    class NestedBuffer final : public std::streambuf {
        forge::Searcher& outer_;
        forge::Searcher& inner_;
        bool entered_ = false;
        void once() {
            if (entered_) return;
            entered_ = true;
            forge::SearchLimits zero;
            zero.nodes_specified = true;
            zero.nodes = 0;
            const auto info = inner_.search(forge::Board{}, zero, false,
                                            forge::Searcher::TTAccess::Exclusive);
            require(info.nodes == 0, "nested other-table zero-node search changed behavior");
            // If inner destruction loses the outer TLS owner, this real public
            // operation waits on our own still-held outer gate and hits deadline.
            put(outer_.transposition_table(), Target, 303);
            tuple(outer_.transposition_table().probe(Target));
            outer_.stop();
        }
        std::streamsize xsputn(const char*, std::streamsize size) override { once(); return size; }
        int_type overflow(int_type ch) override { once(); return traits_type::not_eof(ch); }
        int sync() override { return 0; }
    public:
        NestedBuffer(forge::Searcher& outer, forge::Searcher& inner) : outer_(outer), inner_(inner) {}
    } capture(outer, inner);
    auto* const previous = std::cout.rdbuf(&capture);
    forge::SearchLimits limits;
    limits.depth = 64;
    limits.infinite = true;
    const auto result = outer.search(forge::Board{}, limits, true, forge::Searcher::TTAccess::Exclusive);
    std::cout.rdbuf(previous);
    require(result.nodes > 0, "outer search failed around a nested other-table lease");
    std::atomic<bool> done{false};
    std::thread foreign([&] {
        put(outer.transposition_table(), Target, 303);
        put(inner.transposition_table(), Target, 303);
        done.store(true, std::memory_order_release);
    });
    await([&] { return done.load(std::memory_order_acquire); }, "nested lease left gate or request active");
    foreign.join();
    std::cout << "PASS nested-other-table-owner-restoration\n";
}

void test_exception_unwind() {
    forge::Searcher searcher(1, 1);
    class ThrowBuffer final : public std::streambuf {
        std::streamsize xsputn(const char*, std::streamsize) override { throw std::runtime_error("injected stream failure"); }
        int_type overflow(int_type) override { throw std::runtime_error("injected stream failure"); }
    } capture;
    const auto previous_mask = std::cout.exceptions();
    auto* const previous = std::cout.rdbuf(&capture);
    std::cout.exceptions(std::ios::badbit | std::ios::failbit);
    bool caught = false;
    try {
        forge::SearchLimits limits;
        limits.depth = 2;
        (void)searcher.search(forge::Board{}, limits, true, forge::Searcher::TTAccess::Exclusive);
    } catch (const std::exception&) {
        caught = true;
    }
    std::cout.exceptions(std::ios::goodbit);
    std::cout.rdbuf(previous);
    std::cout.clear();
    std::cout.exceptions(previous_mask);
    require(caught, "stream failure did not unwind an actual exclusive search");
    std::atomic<bool> done{false};
    std::thread foreign([&] {
        put(searcher.transposition_table(), Target, 303);
        tuple(searcher.transposition_table().probe(Target));
        done.store(true, std::memory_order_release);
    });
    await([&] { return done.load(std::memory_order_acquire); }, "exception unwind left gate or request active");
    foreign.join();
    searcher.resize_hash(2);
    searcher.clear();
    std::cout << "PASS actual-search-exception-unwind\n";
}

void test_partial_drain_exception() {
    forge::Searcher searcher(1, 1);
    forge::SearchLimits zero;
    zero.nodes_specified = true;
    zero.nodes = 0;
    role = 8;
    owner_locks = 0;
    injected_lock_failure = false;
    inject_owner_lock_call = 300;
    bool caught = false;
    try {
        (void)searcher.search(forge::Board{}, zero, false, forge::Searcher::TTAccess::Exclusive);
    } catch (const std::exception&) {
        caught = true;
    }
    inject_owner_lock_call = 0;
    role = 0;
    require(caught && injected_lock_failure.load() && owner_locks == 300,
            "partial-drain lock fault did not exercise the actual lease constructor");
    std::atomic<bool> done{false};
    std::thread foreign([&] {
        put(searcher.transposition_table(), Target, 303);
        tuple(searcher.transposition_table().probe(Target));
        const int full = searcher.hashfull_permille();
        require(full >= 0 && full <= 1000, "hashfull failed after partial drain unwind");
        done.store(true, std::memory_order_release);
    });
    await([&] { return done.load(std::memory_order_acquire); }, "partial drain left exclusive request active");
    foreign.join();
    const auto next = searcher.search(forge::Board{}, zero, false, forge::Searcher::TTAccess::Exclusive);
    require(next.nodes == 0 && !next.best_move.is_none(), "partial drain left gate locked or TLS stale");
    searcher.resize_hash(2);
    std::cout << "PASS partial-drain-constructor-exception\n";
}
}

extern "C" int __real_pthread_mutex_lock(pthread_mutex_t* mutex);
extern "C" int __wrap_pthread_mutex_lock(pthread_mutex_t* mutex) {
    if (role == 8) {
        ++owner_locks;
        if (inject_owner_lock_call.load(std::memory_order_relaxed) == owner_locks) {
            injected_lock_failure.store(true, std::memory_order_relaxed);
            return EAGAIN; // Actual std::mutex::lock throws; do not acquire the failed drain stripe.
        }
    }
    if ((role & 7U) != 0 && proof_phase.load(std::memory_order_acquire)) {
        attempted.fetch_or(role, std::memory_order_release);
        const int attempt = pthread_mutex_trylock(mutex);
        if (attempt == EBUSY) busy.fetch_or(role, std::memory_order_release);
        else if (attempt == 0) pthread_mutex_unlock(mutex);
        else fail("diagnostic trylock returned an unexpected error");
    }
    return __real_pthread_mutex_lock(mutex);
}

int main() {
    forge::Searcher searcher(1, 1);
    run_paused(searcher, forge::Searcher::TTAccess::Shared, false, "default-shared1");
    searcher.set_threads(4);
    run_paused(searcher, forge::Searcher::TTAccess::Exclusive, false, "exclusive-request-smp4-fallback");
    searcher.set_threads(1);
    run_paused(searcher, forge::Searcher::TTAccess::Exclusive, true, "exclusive1-after-1to4to1");
    searcher.reset_stop();
    forge::SearchLimits zero;
    zero.nodes_specified = true;
    zero.nodes = 0;
    const auto answer = searcher.search(forge::Board{}, zero, false, forge::Searcher::TTAccess::Exclusive);
    require(answer.nodes == 0 && !answer.best_move.is_none(), "zero-node lease exit changed behavior");
    searcher.resize_hash(1);
    put(searcher.transposition_table(), Target, 303);
    tuple(searcher.transposition_table().probe(Target));
    std::cout << "PASS post-return-default-api-and-zero-node-cleanup\n";
    test_nested_other_table();
    test_exception_unwind();
    test_partial_drain_exception();
}
