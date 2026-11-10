// Linux regression harness. --wrap holds helpers before Worker::search until
// Searcher joins them; no scheduler timing, sleeps or production hooks needed.
#include "forge/search.hpp"

#include <condition_variable>
#include <cstdlib>
#include <iostream>
#include <mutex>
#include <pthread.h>
#include <streambuf>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static std::vector<Worker*> workers(Worker& main) { return *main.all_workers_; }
    static void permit_tail_work(Worker& worker) {
        worker.shared_.stop.store(false, std::memory_order_relaxed);
    }
    static void seed_nodes(Worker& worker, std::uint64_t nodes) {
        worker.nodes_.store(nodes, std::memory_order_relaxed);
    }
};
}

namespace {
std::mutex gate_mutex;
std::condition_variable gate_cv;
bool hold_helpers = false;
bool release_helpers = false;
int gated_creates = 0;
forge::Worker* tail_worker = nullptr;
struct Start { void* (*function)(void*); void* argument; };
void* gated_start(void* argument) {
    const Start start = *static_cast<Start*>(argument);
    delete static_cast<Start*>(argument);
    {
        std::unique_lock<std::mutex> lock(gate_mutex);
        gate_cv.wait(lock, [] { return release_helpers; });
    }
    return start.function(start.argument);
}

class CaptureWorkers final : public std::streambuf {
public:
    explicit CaptureWorkers(forge::Worker& main) : main_(main) {}
    std::vector<forge::Worker*> workers;
private:
    void capture() {
        if (workers.empty()) workers = forge::SearcherTestProbe::workers(main_);
    }
    std::streamsize xsputn(const char*, std::streamsize n) override { capture(); return n; }
    int overflow(int c) override { capture(); return traits_type::not_eof(c); }
    forge::Worker& main_;
};
}

extern "C" int __real_pthread_create(pthread_t*, const pthread_attr_t*, void* (*)(void*), void*);
extern "C" int __real_pthread_join(pthread_t, void**);
extern "C" int __wrap_pthread_create(pthread_t* thread, const pthread_attr_t* attr,
                                      void* (*function)(void*), void* argument) {
    if (!hold_helpers) return __real_pthread_create(thread, attr, function, argument);
    ++gated_creates;
    auto* start = new Start{function, argument};
    const int result = __real_pthread_create(thread, attr, gated_start, start);
    if (result != 0) delete start;
    return result;
}
extern "C" int __wrap_pthread_join(pthread_t thread, void** result) {
    if (hold_helpers) {
        // Model real late work after the result snapshot by letting the held
        // helper complete a depth-one search before this join returns.
        if (tail_worker) forge::SearcherTestProbe::permit_tail_work(*tail_worker);
        { const std::lock_guard<std::mutex> lock(gate_mutex); release_helpers = true; }
        gate_cv.notify_all();
    }
    return __real_pthread_join(thread, result);
}

int main() {
    const bool test_tail = std::getenv("SMP_NODES_FINAL") != nullptr;
    forge::nnue::enabled = false;
    forge::Searcher searcher(1, 2);
    forge::SearchLimits warmup;
    warmup.depth = 1;
    CaptureWorkers capture(searcher.main_worker());
    auto* old = std::cout.rdbuf(&capture);
    (void)searcher.search(forge::Board{}, warmup, true);
    std::cout.rdbuf(old);
    if (capture.workers.size() != 2) return 2;
    forge::SearcherTestProbe::seed_nodes(*capture.workers[1], test_tail ? 0 : 1000000);
    if (test_tail) tail_worker = capture.workers[1];
    hold_helpers = true;
    forge::SearchLimits limits;
    limits.depth = test_tail ? 1 : 8;
    limits.nodes = test_tail ? 0 : 100;
    limits.nodes_specified = !test_tail;
    const auto result = searcher.search(forge::Board{}, limits);
    hold_helpers = false;
    const auto main_nodes = searcher.main_worker().nodes();
    if (gated_creates != 1) {
        std::cerr << "FAIL pthread wrapping inactive (link static libstdc++)\n";
        return 2;
    }
    if (test_tail) {
        std::uint64_t total = 0;
        for (const auto* worker : capture.workers) total += worker->nodes();
        if (total <= main_nodes || result.nodes != total) {
            std::cerr << "FAIL post-join accounting: main=" << main_nodes
                      << " returned=" << result.nodes << " final=" << total << '\n';
            return 1;
        }
        std::cout << "PASS post-join accounting: returned=" << result.nodes << '\n';
        return 0;
    }
    if (main_nodes != 100 || result.nodes != 100) {
        std::cerr << "FAIL stale helper counter: main=" << main_nodes
                  << " returned=" << result.nodes << " expected=100\n";
        return 1;
    }
    std::cout << "PASS stale helper counter reset before launch\n";
}
