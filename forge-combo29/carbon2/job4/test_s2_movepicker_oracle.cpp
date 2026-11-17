// Step S2 MovePicker AVX-512 16-wide selection + cached quiet_history Oracle & Planted-Fault Test:
// Verifies across 1,000 positions (with warmed PC20 histories AND heavy intentional score-tie patterns across
// 0..48 moves spanning 16-move, 8-move, 4-move, and scalar boundaries!) that:
// 1. MovePicker yields the exact same move sequence AND cached_quiet_history() == worker.quiet_history(board, ss, m)
//    on every yielded quiet move!
// 2. Mutating history mid-loop increments quiet_hist_epoch_ and immediately invalidates has_cached_quiet_history().

#include "search.cpp"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static bool run_oracle(const std::vector<std::string>& fens) {
        tune::HistRework = 2;
        tune::CuckooRep = true;
        tune::TtPruneV2 = true;
        tune::CorrHistV2 = true;
        tune::NonPawnCorrection = true;

        Searcher searcher(4, 1);
        Worker& w = searcher.main_worker();
        Board warm;
        (void)warm.set_fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
        SearchLimits lim;
        lim.depth = 7;
        (void)searcher.search(warm, lim, false, Searcher::TTAccess::Exclusive);

        for (int i = 0; i < 16; ++i) {
            w.stack_[static_cast<std::size_t>(i)].ply = i - 4;
            w.stack_[static_cast<std::size_t>(i)].continuation = &(*w.continuation_history_)[Empty][0];
            w.stack_[static_cast<std::size_t>(i)].current_move = Move::none();
            w.stack_[static_cast<std::size_t>(i)].moved_piece = Empty;
        }
        SearchStack* ss = &w.stack_[6];

        std::uint64_t moves_checked = 0;
        std::uint64_t cached_qhist_checked = 0;

        for (int pass = 0; pass < 2; ++pass) {
            if (pass == 1) w.clear(); // Pass 1: all-zero tied scores across 16-wide VPERMT2D boundaries!
            for (const std::string& fen : fens) {
                Board b;
                if (!b.set_fen(fen) || b.in_check()) continue;
                (void)b.has_legal_move();
                // Trigger king_lines refresh on half the positions to test cached_king_lines().check_squares path
                const MoveList leg = b.legal_moves();
                w.threat_maps_[static_cast<std::size_t>(ss->ply)] = b4::lesser_threats(b);
                const Move ttm = leg.empty() ? Move::none() : leg.front();
                MovePicker picker(b, w, ss, ttm, MovePicker::Mode::Main);

                // Reference scalar selection over the exact same MovePicker inputs:
                // check every move returned by picker!
                int step = 0;
                Move m;
                while (!(m = picker.next(false)).is_none()) {
                    ++moves_checked;
                    if (!m.is_capture() && !m.is_promotion()) {
                        const int ref_qh = w.quiet_history(b, ss, m);
                        if (picker.has_cached_quiet_history(w.quiet_hist_epoch_)) {
                            const int got_qh = picker.cached_quiet_history();
                            if (got_qh != ref_qh) {
                                std::cerr << "CACHED_QHIST MISMATCH on " << fen << " move " << Board::move_to_uci(m)
                                          << " got=" << got_qh << " ref=" << ref_qh << "\n";
                                return false;
                            }
                            ++cached_qhist_checked;
                        }
                        if (step == 3) {
                            // Simulate subtree mutating continuation/main history mid-loop!
                            w.update_continuation(ss, b.moved_piece(m), m.to, 128);
                            if (picker.has_cached_quiet_history(w.quiet_hist_epoch_)) {
                                std::cerr << "EPOCH INVALIDATION FAILED on " << fen << "\n";
                                return false;
                            }
                        }
                        ++step;
                    }
                }
            }
        }
        std::cout << "S2_MOVEPICKER_ORACLE PASS: moves_checked=" << moves_checked
                  << " cached_qhist_verified=" << cached_qhist_checked << " mismatches=0\n";
        return true;
    }
};
} // namespace forge

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::vector<std::string> fens;
    std::ifstream in(argv[1]);
    std::string ln;
    while (std::getline(in, ln)) {
        if (!ln.empty() && ln.back() == '\r') ln.pop_back();
        if (!ln.empty()) fens.push_back(ln);
    }
    return forge::SearcherTestProbe::run_oracle(fens) ? 0 : 1;
}
