#include "forge/board.hpp"
#include "forge/search.hpp"

#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

#include <sys/wait.h>
#include <unistd.h>

namespace {

int g_failures = 0;

void expect(bool condition, const std::string& name) {
    if (condition) {
        std::cout << "PASS " << name << std::endl;
        return;
    }
    std::cout << "FAIL " << name << std::endl;
    ++g_failures;
}

std::size_t cluster_index(std::uint64_t key, std::size_t count) {
    using u128 = unsigned __int128;
    return static_cast<std::size_t>((static_cast<u128>(key) * static_cast<u128>(count)) >> 64U);
}

// Attack-table initialisation publishes its "done" flag before the tables exist.
// A thread that arrives during FORGE_INIT_PAUSE_MS must still see a real start position.
int test_init_race() {
    std::atomic<bool> leader_entered{false};
    std::atomic<int> bad{0};
    std::thread leader([&] {
        leader_entered.store(true, std::memory_order_release);
        forge::Board board;
        if (board.legal_moves().size() != 20) bad.fetch_add(1, std::memory_order_relaxed);
    });
    while (!leader_entered.load(std::memory_order_acquire)) std::this_thread::yield();
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    std::vector<std::thread> others;
    others.reserve(8);
    for (int i = 0; i < 8; ++i) {
        others.emplace_back([&] {
            forge::Board board;
            if (board.legal_moves().size() != 20) bad.fetch_add(1, std::memory_order_relaxed);
        });
    }
    leader.join();
    for (std::thread& thread : others) thread.join();
    const int observed = bad.load(std::memory_order_relaxed);
    std::cout << "init_race bad_boards " << observed << std::endl;
    expect(observed == 0, "concurrent Board construction sees 20 start moves");
    return g_failures == 0 ? 0 : 1;
}

int test_tt_replacement_race() {
    forge::TranspositionTable table(1);
    table.clear();
    table.new_search();
    const std::size_t count = table.cluster_count();
    std::vector<std::uint64_t> keys;
    std::vector<int> tally(count, 0);
    std::size_t hot = 0;
    for (std::uint64_t key = 1; key < 400000ULL && keys.size() < 6; ++key) {
        const std::size_t index = cluster_index(key, count);
        const int seen = ++tally[index];
        if (seen == 1) hot = index;
        if (index == hot) keys.push_back(key);
    }
    // The scan above only keeps keys after `hot` is chosen. Restart so the six
    // keys are exactly the first six that land in one cluster.
    keys.clear();
    std::size_t target = static_cast<std::size_t>(-1);
    for (std::uint64_t key = 1; key < 400000ULL && keys.size() < 6; ++key) {
        const std::size_t index = cluster_index(key, count);
        if (target == static_cast<std::size_t>(-1)) target = index;
        if (index == target) keys.push_back(key);
    }
    expect(keys.size() == 6, "found six keys in one transposition cluster");
    if (keys.size() != 6) return 1;

    for (std::size_t i = 0; i < 4; ++i) {
        const forge::TTProbe probe = table.probe(keys[i]);
        table.store(probe, keys[i], 10, 10, forge::Move::none(), 10, forge::BoundLower, false, 0);
    }
    for (std::size_t i = 0; i < 4; ++i) {
        const forge::TTProbe probe = table.probe(keys[i]);
        expect(probe.hit && probe.entry.depth == 10, "cluster slot filled at depth 10");
    }

    std::atomic<int> phase{0};
    forge::TTProbe stale{};
    std::thread replacer([&] {
        const forge::TTProbe probe = table.probe(keys[4]);
        stale = probe;
        phase.store(1, std::memory_order_release);
        while (phase.load(std::memory_order_acquire) < 2) std::this_thread::yield();
        table.store(stale, keys[4], 1, 1, forge::Move::none(), 1, forge::BoundLower, false, 0);
    });
    std::thread writer([&] {
        while (phase.load(std::memory_order_acquire) < 1) std::this_thread::yield();
        const forge::TTProbe probe = table.probe(keys[5]);
        table.store(probe, keys[5], 40, 40, forge::Move::none(), 40, forge::BoundExact, true, 0);
        phase.store(2, std::memory_order_release);
    });
    replacer.join();
    writer.join();

    const forge::TTProbe kept = table.probe(keys[5]);
    std::cout << "tt_race hit " << kept.hit << " depth " << static_cast<int>(kept.entry.depth)
              << " key32 " << kept.entry.key32 << std::endl;
    expect(kept.hit && kept.entry.depth == 40,
           "shallower concurrent store does not overwrite a deeper different key");
    return g_failures == 0 ? 0 : 1;
}

void raise_stop(forge::Searcher& searcher) { searcher.stop(); }

int test_stop_not_cleared() {
    forge::Board board;
    forge::Searcher searcher(8, 2);
    forge::ConcurrencyTestAccess::set_after_main(searcher, raise_stop);
    forge::SearchLimits limits;
    limits.depth = 2;
    const forge::SearchInfo info = searcher.search(board, limits, false);
    const bool stopped = forge::ConcurrencyTestAccess::stop_flag(searcher);
    std::cout << "stop_flag_after_search " << stopped << " best "
              << (info.best_move.is_none() ? "none" : forge::Board::move_to_uci(info.best_move)) << std::endl;
    expect(stopped, "stop published during helper wind-down stays set");
    expect(!info.best_move.is_none(), "wind-down stop still returns the completed move");
    return g_failures == 0 ? 0 : 1;
}

int test_node_total_includes_helpers() {
    forge::Board board;
    forge::Searcher searcher(16, 4);
    forge::SearchLimits limits;
    limits.depth = 5;
    const forge::SearchInfo info = searcher.search(board, limits, false);
    const std::uint64_t published = forge::ConcurrencyTestAccess::published_nodes(searcher);
    std::cout << "nodes_result " << info.nodes << " nodes_published " << published << std::endl;
    expect(info.nodes == published, "reported nodes include every worker after join");
    expect(published > 0, "multi-thread search counts nodes");
    return g_failures == 0 ? 0 : 1;
}

int test_ponder_waits_for_hit() {
    forge::Board board;
    forge::Searcher searcher(8, 1);
    forge::SearchLimits limits;
    limits.ponder = true;
    limits.movetime_ms = 1;
    limits.depth = 32;
    std::atomic<bool> done{false};
    std::thread worker([&] {
        (void)searcher.search(board, limits, false);
        done.store(true, std::memory_order_release);
    });
    std::this_thread::sleep_for(std::chrono::milliseconds(80));
    const bool still_pondering = !done.load(std::memory_order_acquire);
    searcher.ponderhit();
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(3);
    while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    const bool finished = done.load(std::memory_order_acquire);
    if (finished) worker.join();
    else {
        searcher.stop();
        worker.join();
    }
    expect(still_pondering, "movetime does not expire before ponderhit");
    expect(finished, "ponderhit starts the clock and the search returns");
    return g_failures == 0 ? 0 : 1;
}

int test_stop_interrupts_search() {
    forge::Board board;
    forge::Searcher searcher(8, 2);
    forge::SearchLimits limits;
    limits.depth = 32;
    limits.movetime_ms = 5000;
    std::atomic<bool> done{false};
    std::thread worker([&] {
        (void)searcher.search(board, limits, false);
        done.store(true, std::memory_order_release);
    });
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    searcher.stop();
    const auto started = std::chrono::steady_clock::now();
    const auto deadline = started + std::chrono::seconds(2);
    while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    const auto elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                                std::chrono::steady_clock::now() - started)
                                .count();
    const bool finished = done.load(std::memory_order_acquire);
    if (finished) worker.join();
    else worker.detach();
    std::cout << "stop_latency_ms " << elapsed_ms << std::endl;
    expect(finished && elapsed_ms < 2000, "shared stop flag ends a multi-thread search");
    return g_failures == 0 ? 0 : 1;
}

int run_case(const std::string& mode) {
    g_failures = 0;
    if (mode == "init") {
        if (setenv("FORGE_INIT_PAUSE_MS", "80", 1) != 0) return 1;
        return test_init_race();
    }
    if (mode == "tt") return test_tt_replacement_race();
    if (mode == "stop-flag") return test_stop_not_cleared();
    if (mode == "nodes") return test_node_total_includes_helpers();
    if (mode == "ponder") return test_ponder_waits_for_hit();
    if (mode == "stop-latency") return test_stop_interrupts_search();
    std::cerr << "unknown case " << mode << std::endl;
    return 2;
}

int run_child(const char* mode) {
    const pid_t pid = fork();
    if (pid < 0) {
        std::cout << "FAIL " << mode << " fork" << std::endl;
        return 1;
    }
    if (pid == 0) {
        if (setenv("FORGE_CONCURRENCY_CASE", mode, 1) != 0) _exit(127);
        const std::string self = "/proc/self/exe";
        execl(self.c_str(), "forge_concurrency_tests", static_cast<char*>(nullptr));
        _exit(127);
    }
    int status = 0;
    if (waitpid(pid, &status, 0) < 0) {
        std::cout << "FAIL " << mode << " wait" << std::endl;
        return 1;
    }
    if (WIFSIGNALED(status)) {
        std::cout << "FAIL " << mode << " signal " << WTERMSIG(status) << std::endl;
        return 1;
    }
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        std::cout << "FAIL " << mode << " exit " << (WIFEXITED(status) ? WEXITSTATUS(status) : status) << std::endl;
        return 1;
    }
    std::cout << "PASS case " << mode << std::endl;
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    if (const char* mode = std::getenv("FORGE_CONCURRENCY_CASE")) {
        return run_case(mode);
    }
    if (argc == 2) return run_case(argv[1]);

    int failures = 0;
    for (const char* mode : {"init", "tt", "stop-flag", "nodes", "ponder", "stop-latency"}) {
        failures += run_child(mode);
    }
    std::cout << (failures == 0 ? "ALL PASS" : "ALL FAIL") << " failures " << failures << std::endl;
    return failures == 0 ? 0 : 1;
}
