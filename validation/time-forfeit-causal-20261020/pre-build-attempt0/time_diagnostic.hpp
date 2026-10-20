#pragma once
// Diagnostic-only Linux instrumentation. Never included in a production checkout.
#include <atomic>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <fcntl.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

namespace forge::time_diagnostic {
inline std::atomic<unsigned long long> next_search{0};
inline std::atomic<unsigned long long> next_event{0};
inline thread_local unsigned long long search_id = 0;
inline thread_local long long previous_write_wall_ns = 0;
inline thread_local long long previous_write_thread_cpu_ns = 0;
inline thread_local long long previous_write_process_cpu_ns = 0;
inline thread_local unsigned long long previous_event_id = 0;
inline long long clock_ns(clockid_t kind) {
    timespec ts{};
    if (::clock_gettime(kind, &ts) != 0) std::abort();
    return static_cast<long long>(ts.tv_sec) * 1000000000LL + ts.tv_nsec;
}
inline int log_fd() {
    static const int fd = [] {
        const char* path = std::getenv("FORGE_TIME_DIAGNOSTIC_PATH");
        if (path == nullptr || *path == '\0') std::abort();
        const int value = ::open(path, O_WRONLY | O_CREAT | O_EXCL | O_APPEND | O_CLOEXEC, 0600);
        if (value < 0) std::abort();
        return value;
    }();
    return fd;
}
inline bool poll_enabled() {
    static const auto target = [] {
        const char* text = std::getenv("FORGE_TIME_DIAGNOSTIC_POLL_SEARCH");
        if (text == nullptr) std::abort();
        char* end = nullptr;
        const auto value = std::strtoull(text, &end, 10);
        if (end == text || *end != '\0' || value == 0) std::abort();
        return value;
    }();
    return search_id == target;
}
inline void enter_search(unsigned long long id) { search_id = id; }
inline void event(const char* tag, unsigned long long nodes = 0,
                  long long origin_ns = 0, long long budget_ms = 0, long long detail = 0) {
    const int saved_errno = errno;
    const int fd = log_fd();
    const auto wall = clock_ns(CLOCK_MONOTONIC);
    const auto thread_cpu = clock_ns(CLOCK_THREAD_CPUTIME_ID);
    const auto process_cpu = clock_ns(CLOCK_PROCESS_CPUTIME_ID);
    const auto id = next_event.fetch_add(1, std::memory_order_relaxed) + 1;
    char buffer[768];
    const int length = std::snprintf(buffer, sizeof(buffer),
        "{\"event\":\"%s\",\"id\":%llu,\"search\":%llu,\"pid\":%ld,\"tid\":%ld,"
        "\"wall_ns\":%lld,\"thread_cpu_ns\":%lld,\"process_cpu_ns\":%lld,"
        "\"nodes\":%llu,\"origin_ns\":%lld,\"budget_ms\":%lld,\"detail\":%lld,"
        "\"previous_event_id\":%llu,\"previous_write_wall_ns\":%lld,"
        "\"previous_write_thread_cpu_ns\":%lld,\"previous_write_process_cpu_ns\":%lld}\n",
        tag, id, search_id, static_cast<long>(::getpid()), static_cast<long>(::syscall(SYS_gettid)),
        wall, thread_cpu, process_cpu, nodes, origin_ns, budget_ms, detail,
        previous_event_id, previous_write_wall_ns, previous_write_thread_cpu_ns,
        previous_write_process_cpu_ns);
    if (length <= 0 || static_cast<unsigned>(length) >= sizeof(buffer)) std::abort();
    // One append write keeps a complete event atomic across UCI/main worker threads.
    ssize_t result;
    do { result = ::write(fd, buffer, static_cast<std::size_t>(length)); } while (result < 0 && errno == EINTR);
    if (result != length) std::abort(); // Never silently drop or truncate telemetry.
    previous_event_id = id;
    previous_write_thread_cpu_ns = clock_ns(CLOCK_THREAD_CPUTIME_ID) - thread_cpu;
    previous_write_process_cpu_ns = clock_ns(CLOCK_PROCESS_CPUTIME_ID) - process_cpu;
    previous_write_wall_ns = clock_ns(CLOCK_MONOTONIC) - wall;
    errno = saved_errno;
}
inline unsigned long long begin_go(long long receipt_ns) {
    search_id = next_search.fetch_add(1, std::memory_order_relaxed) + 1;
    event("go_receipt", 0, receipt_ns);
    return search_id;
}
} // namespace forge::time_diagnostic
