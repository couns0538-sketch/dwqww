// Environment-only TSan probe; not a Forge engine or a chess experiment.
#include <atomic>
#include <thread>
#include <iostream>
int main() {
    std::atomic<int> counter{0};
    std::thread a([&]{for(int i=0;i<10000;++i) counter.fetch_add(1,std::memory_order_relaxed);});
    std::thread b([&]{for(int i=0;i<10000;++i) counter.fetch_add(1,std::memory_order_relaxed);});
    a.join(); b.join();
    std::cout << counter.load() << '\n';
    return counter.load()==20000 ? 0 : 1;
}
