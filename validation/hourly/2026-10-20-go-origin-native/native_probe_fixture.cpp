// An intentionally small UCI-like fixture to verify the admission-delay probe.
// This is NOT Forge and must never be counted as an engine test.
#include <chrono>
#include <iostream>
#include <mutex>
#include <string>
#include <thread>
using Clock = std::chrono::steady_clock;
int main() {
    std::mutex output;
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line == "uci") { std::cout << "id name clock-probe-fixture\nuciok\n" << std::flush; continue; }
        if (line == "isready") { std::cout << "readyok\n" << std::flush; continue; }
        if (line.rfind("go ", 0) == 0) {
            const auto go_received = Clock::now();
            const bool timed = line.find("movetime") != std::string::npos;
            std::thread worker([&output, go_received, timed] {
                const auto origin =
#ifdef BAD_GO_ORIGIN_ALL
                  go_received;
#elif defined(FIX_GO_ORIGIN)
                  timed ? go_received : Clock::now();
#else
                  Clock::now();
#endif
                std::this_thread::sleep_for(std::chrono::milliseconds(12));
                const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now()-origin).count();
                std::lock_guard<std::mutex> guard(output);
                std::cout << "info depth 1 score cp 0 nodes 20 time " << elapsed << " pv e2e4\n"
                             "bestmove e2e4\n" << std::flush;
            });
            worker.join();
        }
        if (line == "quit") break;
    }
}
