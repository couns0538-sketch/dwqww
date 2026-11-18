#include "forge/bitboard.hpp"
#include "forge/board.hpp"
#include <cassert>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    forge::attacks::init();
    std::vector<std::string> fens;
    std::ifstream in("/agent/repos/dwqww/forge-combo29/carbon2/positions_1000.txt");
    std::string line;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (!line.empty()) fens.push_back(line);
    }
    const char* extra_fens[] = {
        "4k3/4p3/8/2N5/8/8/8/4R1K1 w - - 0 1",
        "3rk3/3bp3/5Q2/8/8/8/8/4R1K1 w - - 0 1",
        "6k1/5p2/4n3/3B1Q2/8/8/8/6K1 w - - 0 1",
        "6k1/5p1p/5n2/3B3Q/8/8/8/6K1 w - - 0 1",
        "4k3/3p1p2/8/3Q4/8/8/8/R5K1 w - - 0 1",
        "4k3/8/8/3pP3/2p5/8/8/3R2K1 w - d6 0 1",
        "4k2r/2P1p3/3n4/5Q2/8/8/8/4R1K1 w k - 0 1",
        "4k3/3np3/8/5Q2/8/8/8/4R1K1 w - - 0 1"
    };
    for (const char* f : extra_fens) fens.emplace_back(f);

    constexpr int thresholds[7] = {-350, -100, -1, 0, 1, 100, 350};
    std::uint64_t hash = 14695981039346656037ULL;
    std::uint64_t calls = 0;
    std::uint64_t moves_total = 0;
    const bool dump_lines = (argc > 1 && std::string(argv[1]) == "--dump");
    for (std::size_t idx = 0; idx < fens.size(); ++idx) {
        forge::Board b;
        std::string err;
        const bool ok = b.set_fen(fens[idx], &err);
        if (!ok) {
            std::fprintf(stderr, "BAD FEN idx=%zu fen='%s' err='%s'\n", idx, fens[idx].c_str(), err.c_str());
            return 2;
        }
        const forge::MoveList ml = b.pseudo_legal_moves(false);
        moves_total += ml.size();
        for (std::size_t mi = 0; mi < ml.size(); ++mi) {
            const forge::Move m = ml[mi];
            int mask = 0;
            for (int ti = 0; ti < 7; ++ti) {
                const bool res = b.see_ge(m, thresholds[ti]);
                if (res) mask |= (1 << ti);
                hash ^= static_cast<std::uint64_t>(res ? 0x9e37 + ti : 0x1234 + ti);
                hash *= 1099511628211ULL;
                ++calls;
            }
            if (dump_lines) {
                std::printf("%zu|%s|%02x\n", idx, forge::Board::move_to_uci(m).c_str(), mask);
            }
        }
    }
    std::fprintf(stderr, "POSITIONS=%zu MOVES=%llu CALLS=%llu HASH=%016llx\n",
                 fens.size(), (unsigned long long)moves_total,
                 (unsigned long long)calls, (unsigned long long)hash);
    return 0;
}
