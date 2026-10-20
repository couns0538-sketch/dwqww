#include <array>
#include <cstdio>
#include <mutex>

int main() {
    std::fputs("entered-main\n", stderr);
    std::array<std::mutex, 1024> stripes;
    std::mutex gate;
    const std::lock_guard<std::mutex> lease(gate);
    for (auto& stripe : stripes) {
        const std::lock_guard<std::mutex> drain(stripe);
    }
    std::puts("one-gate-drained1024-default-tsan-smoke-completed");
}
