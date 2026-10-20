#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <pthread.h>
#include <stdlib.h>
#include <time.h>

// Linux-only, diagnostic-only LD_PRELOAD shim. Never link into Forge.
typedef int (*create_fn)(pthread_t*, const pthread_attr_t*, void* (*)(void*), void*);
int pthread_create(pthread_t* thread, const pthread_attr_t* attr,
                   void* (*start)(void*), void* arg) {
    void* symbol = dlsym(RTLD_NEXT, "pthread_create");
    create_fn actual = NULL;
    _Static_assert(sizeof(actual) == sizeof(symbol), "function pointer width");
    __builtin_memcpy(&actual, &symbol, sizeof(actual));
    if (actual == NULL) return EAGAIN;
    const char* value = getenv("FORGE_TEST_CREATE_DELAY_MS");
    if (value != NULL) {
        char* end = NULL;
        const long delay = strtol(value, &end, 10);
        if (end != value && *end == '\0' && delay > 0 && delay <= 1000) {
            const struct timespec required = {delay / 1000L, (delay % 1000L) * 1000000L};
            struct timespec remaining = required;
            while (nanosleep(&remaining, &remaining) < 0 && errno == EINTR) {}
        }
    }
    return actual(thread, attr, start, arg);
}
