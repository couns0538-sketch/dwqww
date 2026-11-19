#include <cstdint>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>
int main() {
    for (int j = 1; j <= 80; ++j) {
        std::mt19937_64 rng(2400000 + j);
        std::vector<int> ids(257);
        std::iota(ids.begin(), ids.end(), 0);
        for (int i = 0; i + 1 < (int)ids.size(); ++i) {
            std::swap(ids[i], ids[i + rng() % (ids.size() - i)]);
        }
        for (int i=0;i<8;++i) std::cout << ids[i] << ' ';
        std::cout << '\n';
    }
}
