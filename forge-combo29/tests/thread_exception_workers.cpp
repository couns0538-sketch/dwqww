// Inject one allocation failure inside the main/helper Worker::search call.
// Run only with FORGE_FIX_SMP_EXCEPTIONS=1. No production hooks.
#include "forge/search.hpp"
#include <cstdlib>
#include <iostream>
#include <new>
#include <pthread.h>
namespace {
thread_local bool fail_next = false;
int mode = 0, creates = 0, joins = 0;
struct Start { void* (*function)(void*); void* argument; };
void* helper_start(void* opaque) {
    const Start start = *static_cast<Start*>(opaque);
    delete static_cast<Start*>(opaque);
    fail_next = true;
    return start.function(start.argument);
}
}
void* operator new(std::size_t size) {
    if (fail_next) { fail_next = false; throw std::bad_alloc(); }
    if (void* p = std::malloc(size ? size : 1)) return p;
    throw std::bad_alloc();
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
extern "C" int __real_pthread_create(pthread_t*, const pthread_attr_t*, void* (*)(void*), void*);
extern "C" int __real_pthread_join(pthread_t, void**);
extern "C" int __wrap_pthread_create(pthread_t* thread, const pthread_attr_t* attr,
                                      void* (*function)(void*), void* argument) {
    ++creates;
    if (mode == 2 && creates == 1) {
        auto* start = new Start{function, argument};
        const int rc = __real_pthread_create(thread, attr, helper_start, start);
        if (rc != 0) delete start;
        return rc;
    }
    const int rc = __real_pthread_create(thread, attr, function, argument);
    if (mode == 1 && creates == 2 && rc == 0) fail_next = true;
    return rc;
}
extern "C" int __wrap_pthread_join(pthread_t thread, void** result) {
    const int rc = __real_pthread_join(thread, result);
    if (rc == 0) ++joins;
    return rc;
}
int main(int argc, char**) {
    forge::nnue::enabled = false;
    forge::Board board;
    forge::Searcher searcher(1, 3);
    forge::SearchLimits limits;
    limits.depth = 1;
    mode = argc == 1 ? 1 : 2;
    try { (void)searcher.search(board, limits); }
    catch (const std::bad_alloc&) {
        if (joins != 2) return 2;
        std::cout << "PASS " << (mode == 1 ? "main" : "helper") << " allocation exception propagated after " << joins << " joins\n";
        mode = 0;
        (void)searcher.search(board, limits);
        if (searcher.main_worker().nodes() == 0) return 3;
        (void)searcher.search(board, limits);
        if (searcher.main_worker().nodes() == 0) return 4;
        std::cout << "PASS consecutive searches reusable without reset_stop\n";
        return 0;
    }
    std::cerr << "FAIL expected allocation exception\n";
    return 1;
}
