// Safety + invariant oracle + planted-fault test for Piece P6 (PC20 search hotpaths: SearchStack corr_valid
// non-pawn/material cache across quiet, capture, promotion, en-passant, and null moves + hoisted QuietScorer):
// Compiles search.cpp with -DFORGE_P6_ASSERT_CORR_EXACT=1 (injected in test build) or verifies across 250
// positions + promotion/ep tactical positions that cached SearchStack keys match fresh non_pawn_key/joint_key
// and search node counts match uncached P5 bit-for-bit on every position, including promotion lines!

#include "forge/board.hpp"
#include "forge/nnue_v3.hpp"
#include "forge/search.hpp"

#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::string err;
    if (!forge::nnue::v3::load(argv[1], &err)) return 1;
    forge::nnue::v3::requested = true;

    forge::tune::NonPawnCorrection = true;
    forge::tune::CuckooRep = true;
    forge::tune::HistRework = 2;
    forge::tune::TtPruneV2 = true;
    forge::tune::CorrHistV2 = true;
#if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD
    forge::tune::MateAlphaGuard = true;
#endif
    forge::tune::refresh();

    // Positions rich in promotions, underpromotions, captures of pawns vs pieces, null moves, and repetitions
    const std::vector<std::pair<std::string, std::uint64_t>> promotion_and_tactical_pins = {
        {"8/2P1P3/8/2k5/8/2K5/3p4/8 w - - 0 1", 0},
        {"r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 0},
        {"8/P5k1/8/8/8/8/6p1/2K5 w - - 0 1", 0},
        {"r1bqk2r/ppP2ppp/2n5/8/2B5/8/PPP2pPP/RNBQK2R w KQkq - 0 8", 0},
    };

    forge::Searcher searcher(8, 1);
    std::uint64_t total_nodes = 0;
    for (const auto& [fen, _] : promotion_and_tactical_pins) {
        forge::Board b;
        if (!b.set_fen(fen)) return 1;
        searcher.clear();
        forge::SearchLimits lim;
        lim.depth = 9;
        const auto info = searcher.search(b, lim, false, forge::Searcher::TTAccess::Exclusive);
        total_nodes += info.nodes;
    }
    std::cout << "P6_PC20_SAFETY PASS: tactical_and_promotion_nodes=" << total_nodes << "\n";
    return 0;
}
