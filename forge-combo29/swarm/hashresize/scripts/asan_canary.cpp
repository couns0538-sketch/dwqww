// Positive control for the ASan detector in exp_asan.py.
//
// The ASan suite is only admissible if the harness reports a diagnostic WHEN
// ONE EXISTS.  This binary is a minimal UCI-shaped program that answers
// `uci`/`isready` and then overflows a heap buffer when it sees
// `setoption name Hash`.  Driving it through the same Engine class and the
// same stderr capture as the engine proves the detector fires on a real
// AddressSanitizer report rather than merely on a missing binary.
//
// Build (matched to the engine's sanitizer flags):
//   g++ -O1 -g -fsanitize=address,undefined -o asan_canary asan_canary.cpp
#include <cstdio>
#include <iostream>
#include <string>

struct TTCluster {
    volatile char bytes[64];
};

int main() {
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line == "uci") {
            std::printf("id name asan canary\nuciok\n");
            std::fflush(stdout);
        } else if (line == "isready") {
            std::printf("readyok\n");
            std::fflush(stdout);
        } else if (line.rfind("setoption name Hash", 0) == 0) {
            TTCluster* clusters = new TTCluster[2];
            for (int i = 0; i < 4; ++i) {
                for (int j = 0; j < 64; ++j) clusters[i].bytes[j] = static_cast<char>(i + j);
            }
            volatile char sink = clusters[3].bytes[63];
            std::printf("info string canary survived %d\n", sink);
            std::fflush(stdout);
            delete[] clusters;
        } else if (line == "quit") {
            return 0;
        }
    }
    return 0;
}
