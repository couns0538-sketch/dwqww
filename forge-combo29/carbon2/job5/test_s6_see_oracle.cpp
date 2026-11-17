// Step S6 Board::see_ge Unpinned-Pawn Recapture Fast-Exit Oracle & Planted-Fault Test:
// Mode --dump <fens> <out>: evaluates reference Board::see_ge(m, th) across all legal moves x 7 thresholds
// on all 1,000 positions + pinned-enemy-pawn edge FENs and writes a compact bit-exact trace.
// Mode --verify <fens> <ref_out>: evaluates variant Board::see_ge(m, th) on the exact same inputs and fails
// immediately on the first mismatch against <ref_out>.

#include "forge/board.hpp"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

static std::vector<std::string> load_fens(const char* path) {
    std::vector<std::string> fens;
    std::ifstream in(path);
    std::string ln;
    while (std::getline(in, ln)) {
        if (!ln.empty() && ln.back() == '\r') ln.pop_back();
        if (!ln.empty()) fens.push_back(ln);
    }
    // Critical edge cases: enemy pawn attacking `to` is pinned to enemy king (`snipers_them != 0`).
    fens.push_back("3k4/8/3p4/8/8/5N2/8/3R2K1 w - - 0 1");   // Nf3-e5: d6 pawn pinned by Rd1 -> see_ge(Ne5, 0) == true
    fens.push_back("6k1/8/4p3/8/1N6/8/B7/6K1 w - - 0 1");    // Nb4-d5: e6 pawn pinned by Ba2 -> see_ge(Nd5, 0) == true
    return fens;
}

int main(int argc, char** argv) {
    if (argc < 4) return 1;
    const std::string mode = argv[1];
    const auto fens = load_fens(argv[2]);
    const int thresholds[] = {-300, -100, -25, 0, 1, 100, 300};

    if (mode == "--dump") {
        std::ofstream out(argv[3]);
        std::string bits;
        for (const std::string& fen : fens) {
            forge::Board b;
            if (!b.set_fen(fen)) return 1;
            for (const forge::Move m : b.legal_moves()) {
                for (const int th : thresholds) {
                    bits.push_back(b.see_ge(m, th) ? '1' : '0');
                }
            }
        }
        out << bits << "\n";
        std::cout << "S6_SEE_REF_DUMP calls=" << bits.size() << "\n";
        return 0;
    }

    if (mode == "--verify") {
        std::ifstream in(argv[3]);
        std::string ref_bits;
        std::getline(in, ref_bits);
        std::size_t idx = 0;
        for (const std::string& fen : fens) {
            forge::Board b;
            if (!b.set_fen(fen)) return 1;
            for (const forge::Move m : b.legal_moves()) {
                for (const int th : thresholds) {
                    if (idx >= ref_bits.size()) return 1;
                    const bool got = b.see_ge(m, th);
                    const bool exp = (ref_bits[idx] == '1');
                    if (got != exp) {
                        std::cerr << "SEE_GE MISMATCH at call=" << idx << " fen='" << fen
                                  << "' move=" << forge::Board::move_to_uci(m)
                                  << " thresh=" << th << " got=" << got << " expected=" << exp << "\n";
                        return 1;
                    }
                    ++idx;
                }
            }
        }
        if (idx != ref_bits.size()) return 1;
        std::cout << "S6_SEE_ORACLE PASS: see_ge_calls_checked=" << idx << " mismatches=0\n";
        return 0;
    }
    return 1;
}
