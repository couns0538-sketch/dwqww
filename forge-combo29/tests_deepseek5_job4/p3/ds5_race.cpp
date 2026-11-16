#include <thread>
int shared = 0;
int main() {
    std::thread a([]{ for (int i = 0; i < 100000; ++i) shared = i; });
    std::thread b([]{ for (int i = 0; i < 100000; ++i) shared = i + 1; });
    a.join(); b.join();
    return shared > 0 ? 0 : 0;
}
