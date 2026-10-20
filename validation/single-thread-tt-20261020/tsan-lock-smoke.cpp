#include <array>
#include <cstdio>
#include <mutex>

int main() {
    std::fputs("entered-main\n", stderr);
    std::array<std::mutex, 1024> mutexes;
    std::array<std::unique_lock<std::mutex>, 1024> locks;
    for (std::size_t i = 0; i < locks.size(); ++i) {
        locks[i] = std::unique_lock<std::mutex>(mutexes[i]);
        if (i == 63 || i == 64 || i == 1023)
            std::fprintf(stderr, "held=%zu\n", i + 1);
    }
    std::puts("all1024-held-default-tsan-smoke-completed");
}
