// Test-only linker wrappers. No production hooks or external fault process.
#include "forge/search.hpp"
#include <atomic>
#include <cstdlib>
#include <cstring>
#include <new>
#include <pthread.h>
#include <stdexcept>
#include <unistd.h>

namespace {
std::atomic<bool> injected{false};
std::atomic<int> creates{0};
thread_local bool fail_next = false;
thread_local const char* failure_name = "allocation";
bool mode_is(const char* expected) {
    const char* mode = std::getenv("FORGE_TEST_EXCEPTION");
    return mode && std::strcmp(mode, expected) == 0;
}
void mark(const char* name) {
    const char prefix[] = "test injection: ";
    (void)::write(2, prefix, sizeof(prefix) - 1);
    (void)::write(2, name, std::strlen(name));
    (void)::write(2, "\n", 1);
}
struct Start { void* (*function)(void*); void* argument; };
void* helper_start(void* opaque) {
    const auto start = *static_cast<Start*>(opaque);
    delete static_cast<Start*>(opaque);
    failure_name = "helper allocation";
    fail_next = true;
    return start.function(start.argument);
}
}
void* operator new(std::size_t size) {
    if (fail_next) { fail_next = false; mark(failure_name); throw std::bad_alloc(); }
    if (void* p = std::malloc(size ? size : 1)) return p;
    throw std::bad_alloc();
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
extern "C" int __real_pthread_create(pthread_t*, const pthread_attr_t*, void* (*)(void*), void*);
extern "C" int __wrap_pthread_create(pthread_t* thread, const pthread_attr_t* attr,
                                      void* (*function)(void*), void* argument) {
    const int count = ++creates;
    // #1 is the actual UCI worker; #2/#3 are its two Searcher helpers.
    if (mode_is("helper") && count == 2 && !injected.exchange(true)) {
        auto* start = new Start{function, argument};
        const int result = __real_pthread_create(thread, attr, helper_start, start);
        if (result != 0) delete start;
        return result;
    }
    const int result = __real_pthread_create(thread, attr, function, argument);
    if (mode_is("main") && count == 3 && result == 0 && !injected.exchange(true)) {
        failure_name = "main allocation";
        fail_next = true;
    }
    return result;
}
extern "C" forge::SearchInfo real_search(forge::Searcher*, forge::Board,
    const forge::SearchLimits&, bool, forge::Searcher::TTAccess)
    asm("__real__ZN5forge8Searcher6searchENS_5BoardERKNS_12SearchLimitsEbNS0_8TTAccessE");
extern "C" forge::SearchInfo wrapped_search(forge::Searcher*, forge::Board,
    const forge::SearchLimits&, bool, forge::Searcher::TTAccess)
    asm("__wrap__ZN5forge8Searcher6searchENS_5BoardERKNS_12SearchLimitsEbNS0_8TTAccessE");
extern "C" forge::SearchInfo wrapped_search(forge::Searcher* searcher, forge::Board board,
    const forge::SearchLimits& limits, bool emit, forge::Searcher::TTAccess access) {
    const bool direct = emit ? (mode_is("search") || mode_is("unknown"))
                             : (mode_is("bench") || mode_is("bench_unknown") || mode_is("bench_alloc"));
    if (direct && !injected.exchange(true)) {
        if (mode_is("bench_alloc")) {
            failure_name = "bench allocation";
            fail_next = true;
        } else {
            mark(emit ? "search facade" : "bench facade");
            if (mode_is("unknown") || mode_is("bench_unknown")) throw 7;
            throw std::runtime_error("injected search failure");
        }
    }
    return real_search(searcher, std::move(board), limits, emit, access);
}
