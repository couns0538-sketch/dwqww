#include "forge/board.hpp"
#include <thread>
#include <vector>
int main() {
    std::vector<std::thread> ts;
    for (int i = 0; i < 4; ++i)
        ts.emplace_back([] { forge::Board b; b.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"); });
    for (auto& t : ts) t.join();
    return 0;
}
