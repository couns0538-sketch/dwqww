// Isolated model of Forge 6.4's UCI thread-admission time accounting.
// NOT an engine build, UCI regression, or evidence of an Elo improvement.
#include <chrono>
#include <cstdint>
#include <iostream>
#include <thread>

using Clock = std::chrono::steady_clock;
static std::int64_t ms(Clock::time_point start) {
    return std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - start).count();
}

int main() {
    const auto go_received = Clock::now();
    // Simulate the UCI consumer being delayed before its search worker begins.
    // No real engine or CPU saturation is involved.
    std::this_thread::sleep_for(std::chrono::milliseconds(440));
    const auto old_worker_origin = Clock::now();
    const auto recovered_origin = go_received;
    constexpr std::int64_t frozen_hard_budget_ms = 351;
    const std::int64_t old_elapsed_ms = ms(old_worker_origin);
    const std::int64_t recovered_elapsed_ms = ms(recovered_origin);
    std::cout << "budget_ms=" << frozen_hard_budget_ms
              << " old_elapsed_ms=" << old_elapsed_ms
              << " go_origin_elapsed_ms=" << recovered_elapsed_ms << '\n';
    if (old_elapsed_ms >= frozen_hard_budget_ms) return 1;
    if (recovered_elapsed_ms < frozen_hard_budget_ms) return 2;
    // The default direct-search origin is created at entry, not inherited
    // from a prior search; this preserves non-UCI callers' old behavior.
    const Clock::time_point unspecified{};
    const auto direct_origin = (unspecified == Clock::time_point{}) ? Clock::now() : unspecified;
    if (ms(direct_origin) > 50) return 3;
    std::cout << "PASS: UCI go-origin exposes admission delay; direct caller remains local\n";
    return 0;
}
