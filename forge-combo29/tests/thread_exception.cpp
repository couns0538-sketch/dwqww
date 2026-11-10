// Linux-only exceptional-resource-failure reproduction. No production hooks.
// Static libstdc++ is required so --wrap sees std::thread's pthread_create.
#include "forge/search.hpp"
#include <cerrno>
#include <csignal>
#include <iostream>
#include <pthread.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <system_error>
#include <unistd.h>
#ifndef FORGE_FIX_SMP_EXCEPTIONS
#define FORGE_FIX_SMP_EXCEPTIONS 0
#endif
namespace {
int fail_creation = 0;
int creation_count = 0;
int join_count = 0;
int run_child(int fail_at) {
    forge::nnue::enabled = false;
    forge::Board board;
    forge::Searcher searcher(1, 3);
    forge::SearchLimits limits;
    limits.depth = 1;
    fail_creation = fail_at;
    creation_count = 0;
    join_count = 0;
    try {
        (void)searcher.search(board, limits);
    } catch (const std::system_error& error) {
        std::cerr << "CAUGHT system_error fail_at=" << fail_at
                  << " creates=" << creation_count << " joins=" << join_count << " code=" << error.code().value() << '\n';
        return creation_count == fail_at && join_count == fail_at - 1 && error.code().value() == EAGAIN ? 42 : 43;
    } catch (...) {
        return 44;
    }
    std::cerr << "RETURNED normally fail_at=" << fail_at << " creates=" << creation_count << '\n';
    return fail_at == 0 && creation_count == 2 && join_count == 2 ? 0 : 45;
}
int observe(int fail_at) {
    std::cout.flush();
    std::cerr.flush();
    const pid_t child = fork();
    if (child < 0) { perror("fork"); return -1; }
    if (child == 0) {
        const rlimit no_core{0, 0};
        (void)setrlimit(RLIMIT_CORE, &no_core);
        _exit(run_child(fail_at));
    }
    int status = 0;
    if (waitpid(child, &status, 0) != child) { perror("waitpid"); return -1; }
    if (WIFSIGNALED(status)) {
        std::cout << "OBSERVED fail_at=" << fail_at << " signal=" << WTERMSIG(status) << '\n';
        return -WTERMSIG(status);
    }
    if (!WIFEXITED(status)) return -99;
    std::cout << "OBSERVED fail_at=" << fail_at << " exit=" << WEXITSTATUS(status) << '\n';
    return WEXITSTATUS(status);
}
}
extern "C" int __real_pthread_create(pthread_t*, const pthread_attr_t*, void* (*)(void*), void*);
extern "C" int __wrap_pthread_create(pthread_t* thread, const pthread_attr_t* attr,
                                     void* (*function)(void*), void* argument) {
    ++creation_count;
    if (fail_creation != 0 && creation_count == fail_creation) {
        std::cerr << "INJECT pthread_create EAGAIN call=" << creation_count << '\n';
        return EAGAIN;
    }
    return __real_pthread_create(thread, attr, function, argument);
}
extern "C" int __real_pthread_join(pthread_t, void**);
extern "C" int __wrap_pthread_join(pthread_t thread, void** result) {
    const int rc = __real_pthread_join(thread, result);
    if (rc == 0) ++join_count;
    return rc;
}
int main() {
    const int control = observe(0);
    const int first = observe(1);
    const int second = observe(2);
    const int expected_second = FORGE_FIX_SMP_EXCEPTIONS ? 42 : -SIGABRT;
    if (control != 0 || first != 42 || second != expected_second) {
        std::cerr << "FAIL unexpected outcome for configured exception-safety switch\n";
        return 1;
    }
    if (FORGE_FIX_SMP_EXCEPTIONS)
        std::cout << "PASS second-helper creation exception is catchable after cleanup\n";
    else
        std::cout << "REPRODUCED second-helper creation exception terminates process with SIGABRT (6)\n";
}
