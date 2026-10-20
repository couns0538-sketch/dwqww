// Linux/GNU-linker audit helper. Link actual engine objects with
// -Wl,--wrap=pthread_mutex_lock -Wl,--wrap=pthread_mutex_unlock.
// Counts are deterministic operation evidence, never timing measurements.
#include <atomic>
#include <cstdio>
#include <cstdint>
#include <pthread.h>

namespace {
std::atomic<std::uint64_t> acquired{0};
std::atomic<std::uint64_t> released{0};
std::atomic<std::uint64_t> errors{0};
}

extern "C" int __real_pthread_mutex_lock(pthread_mutex_t*);
extern "C" int __real_pthread_mutex_unlock(pthread_mutex_t*);

extern "C" int __wrap_pthread_mutex_lock(pthread_mutex_t* mutex) {
    const int result = __real_pthread_mutex_lock(mutex);
    (result == 0 ? acquired : errors).fetch_add(1, std::memory_order_relaxed);
    return result;
}

extern "C" int __wrap_pthread_mutex_unlock(pthread_mutex_t* mutex) {
    const int result = __real_pthread_mutex_unlock(mutex);
    (result == 0 ? released : errors).fetch_add(1, std::memory_order_relaxed);
    return result;
}

__attribute__((destructor)) static void report_mutex_counts() {
    std::fprintf(stderr, "FORGE_MUTEX_COUNTS acquired=%llu released=%llu errors=%llu\n",
        static_cast<unsigned long long>(acquired.load(std::memory_order_relaxed)),
        static_cast<unsigned long long>(released.load(std::memory_order_relaxed)),
        static_cast<unsigned long long>(errors.load(std::memory_order_relaxed)));
}
