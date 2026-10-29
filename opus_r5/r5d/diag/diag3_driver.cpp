// R5D diagnosis 3 driver (scratch only): KRK mate tree watch; prints the contradicting stores of failing runs.
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdlib>
#include <iostream>
#include <memory>
#include <mutex>
#include <sstream>
#include <string>

namespace r5d_diag {
extern std::uint64_t key; extern std::string log; extern bool on; extern std::mutex mutex; extern std::string stores;
extern std::uint64_t keys[16]; extern int sign[16]; extern int need[16]; extern const char* name[16]; extern int count;
extern std::uint64_t seq; extern bool all_stores;
}

int main(int argc, char** argv) {
    const int runs = argc > 1 ? std::atoi(argv[1]) : 600;
    const int threads = argc > 2 ? std::atoi(argv[2]) : 2;
    const int want = argc > 3 ? std::atoi(argv[3]) : 2;
    const int max_lines = argc > 4 ? std::atoi(argv[4]) : 12;
    forge::Board root;
    (void)root.set_fen("4R3/8/8/k2K4/8/8/8/8 w - - 0 1");
    // Mating tree: 1.Kc5 Ka6 2.Re7 Ka5 3.Ra7#  and  1.Kc5 Ka4 2.Re3 Ka5 3.Ra3#.
    static const char* lines[] = {"d5c5", "d5c5 a5a6", "d5c5 a5a6 e8e7", "d5c5 a5a6 e8e7 a6a5",
                                  "d5c5 a5a4", "d5c5 a5a4 e8e3", "d5c5 a5a4 e8e3 a4a5"};
    static std::string names[7];
    for (int i = 0; i < 7; ++i) {
        forge::Board b = root;
        std::istringstream in(lines[i]);
        std::string m;
        int plies = 0;
        while (in >> m) {
            forge::Undo u;
            (void)b.make_move(*b.parse_uci(m), u);
            ++plies;
        }
        names[i] = std::string("[") + lines[i] + "]";
        r5d_diag::keys[i] = b.key();
        r5d_diag::name[i] = names[i].c_str();
        // Side to move after an odd number of plies is Black (the mated side).
        r5d_diag::sign[i] = plies % 2 == 1 ? -1 : 1;
        r5d_diag::need[i] = 5 - plies;  // plies left to the mate
    }
    r5d_diag::count = 7;
    r5d_diag::all_stores = argc > 5;
    const bool print_pass = argc > 6;
    r5d_diag::on = true;
    int failures = 0, passes_with_bad = 0;
    for (int r = 0; r < runs && failures < want; ++r) {
        r5d_diag::stores.clear();
        r5d_diag::seq = 0;
        forge::Searcher searcher(16, threads);
        forge::SearchLimits limits;
        limits.depth = 14;
        const forge::SearchInfo info = searcher.search(root, limits);
        const bool fail = info.score < forge::MateInMaxPly;
        if (!fail && print_pass) { std::cout << "PASS run " << r << '\n' << r5d_diag::stores; return 0; }
        if (!fail) {
            if (!r5d_diag::stores.empty()) ++passes_with_bad;
            continue;
        }
        ++failures;
        std::cout << "FAIL run " << r << " score " << info.score << " move " << forge::Board::move_to_uci(info.best_move) << '\n';
        std::istringstream all(r5d_diag::stores);
        std::string line;
        for (int n = 0; n < max_lines && std::getline(all, line); ++n) std::cout << line << '\n';
    }
    std::cout << "failures " << failures << ", passing runs that also had contradicting stores " << passes_with_bad << '\n';
    return 0;
}
