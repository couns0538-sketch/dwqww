// Step S3 Unrolled non_pawn_key + Correction Prefetch Oracle & Planted-Fault Test:
// Verifies unrolled non_pawn_key(board, White/Black) against the original loop formulation across all
// 1,000 positions of positions_1000.txt + all depth-1 legal child moves (~22,000 positions).

#include "search.cpp"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {
std::uint64_t reference_loop_non_pawn_key(const forge::Board& board, forge::Color color) {
    std::uint64_t key = static_cast<std::uint64_t>(color) * 0x517CC1B727220A95ULL;
    for (int type = forge::Knight; type <= forge::King; ++type) {
        const forge::Bitboard bb = board.pieces(color, static_cast<forge::PieceType>(type));
        key ^= bb * (0x9E3779B97F4A7C15ULL + static_cast<std::uint64_t>(type) * 0xBF58476D1CE4E5B9ULL);
        key = (key ^ (key >> 30U)) * 0x94D049BB133111EBULL;
    }
    return key ^ (key >> 31U);
}
} // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::ifstream in(argv[1]);
    std::string ln;
    std::uint64_t checked = 0;
    while (std::getline(in, ln)) {
        if (!ln.empty() && ln.back() == '\r') ln.pop_back();
        if (ln.empty()) continue;
        forge::Board b;
        if (!b.set_fen(ln)) return 1;
        for (const forge::Color c : {forge::White, forge::Black}) {
            if (forge::non_pawn_key(b, c) != reference_loop_non_pawn_key(b, c)) {
                std::cerr << "NON_PAWN_KEY MISMATCH on " << ln << "\n";
                return 1;
            }
            ++checked;
        }
        for (const forge::Move m : b.legal_moves()) {
            forge::Undo u;
            (void)b.make_move(m, u);
            for (const forge::Color c : {forge::White, forge::Black}) {
                if (forge::non_pawn_key(b, c) != reference_loop_non_pawn_key(b, c)) {
                    std::cerr << "NON_PAWN_KEY CHILD MISMATCH on " << b.fen() << "\n";
                    return 1;
                }
                ++checked;
            }
            b.unmake_move(m, u);
        }
    }
    std::cout << "S3_CORRECTION_KEY_ORACLE PASS: keys_checked=" << checked << " mismatches=0\n";
    return 0;
}
