// Finding 6 proof, kept as the test. The position, the ply-2 mate seed
// MateInMaxPly + 1, and the depth-2 search are the audit case from
// audit/lock-source commit 302a08a2 (tests_audit/proof_mate_score_ply_underflow.cpp).
// score_from_tt used to turn that seed into 31871, which is no longer a mate score.
// This program fails if that collapsed value comes back. It also checks the mirrored
// loss at ply 1, and that a mate which still fits in the band is still a mate.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>

namespace {

forge::Board board_after_only_line() {
    forge::Board board;
    const bool ok = board.set_fen("kb6/p1p5/P1P4p/8/8/p1p3P1/P1P5/KB6 w - - 0 1");
    if (!ok) {
        std::cerr << "FAIL set_fen\n";
        return board;
    }
    forge::Undo first;
    forge::Undo second;
    const auto push = board.parse_uci("g3g4");
    const bool played_first = push.has_value() && board.make_move(*push, first);
    const auto reply = board.parse_uci("h6h5");
    const bool played_second = reply.has_value() && board.make_move(*reply, second);
    if (!played_first || !played_second) std::cerr << "FAIL make the only line\n";
    return board;
}

forge::Board board_after_first_move() {
    forge::Board board;
    const bool ok = board.set_fen("kb6/p1p5/P1P4p/8/8/p1p3P1/P1P5/KB6 w - - 0 1");
    if (!ok) std::cerr << "FAIL set_fen\n";
    forge::Undo undo;
    const auto push = board.parse_uci("g3g4");
    if (!push.has_value() || !board.make_move(*push, undo)) std::cerr << "FAIL make g3g4\n";
    return board;
}

forge::SearchInfo search_with_seed(forge::Searcher& searcher, const forge::Board& root,
                                   const forge::Board& seeded, int stored, int depth, bool emit) {
    searcher.clear();
    forge::TranspositionTable& tt = searcher.transposition_table();
    const forge::TTProbe probe = tt.probe(seeded.key());
    tt.store(probe, seeded.key(), stored, 0, forge::Move::none(), 10, forge::BoundExact, true,
             seeded.halfmove_clock());
    forge::SearchLimits limits;
    limits.depth = depth;
    return searcher.search(root, limits, emit);
}

}  // namespace

int main() {
    forge::Board root;
    if (!root.set_fen("kb6/p1p5/P1P4p/8/8/p1p3P1/P1P5/KB6 w - - 0 1")) {
        std::cerr << "FAIL root fen\n";
        return 1;
    }
    const forge::Board at_ply2 = board_after_only_line();
    forge::Searcher searcher(16, 1);

    const int underflow_mate = forge::MateInMaxPly + 1;
    std::cout << "Seeded ply-2 TT entry with score=" << underflow_mate
              << " (is_mate_score=" << forge::is_mate_score(underflow_mate) << ")\n";
    const forge::SearchInfo collapsed = search_with_seed(searcher, root, at_ply2, underflow_mate, 2, true);
    const int bogus_cp = underflow_mate - 2;
    std::cout << "Root search returned: score=" << collapsed.score
              << " is_mate_score=" << forge::is_mate_score(collapsed.score)
              << " best=" << forge::Board::move_to_uci(collapsed.best_move) << "\n";
    // 31871 is below MateInMaxPly, so the old bug reported it as centipawns.
    // Discarding the hit must leave an ordinary evaluation of this quiet position.
    if (forge::is_mate_score(collapsed.score) || collapsed.score == bogus_cp || collapsed.score > 1000 ||
        collapsed.score < -1000) {
        std::cerr << "FAIL mate crossed MateInMaxPly and came back as " << collapsed.score << "\n";
        return 1;
    }
    if (forge::Board::move_to_uci(collapsed.best_move) != "g3g4") {
        std::cerr << "FAIL expected the only legal root move\n";
        return 1;
    }

    // MateValue - 10 still fits after ply 2 is removed (31990 - 2 = 31988).
    // The same line must keep that as a mate, not drop every mate score.
    const int inside = forge::MateValue - 10;
    const int inside_at_ply2 = inside - 2;
    const forge::SearchInfo kept = search_with_seed(searcher, root, at_ply2, inside, 2, false);
    if (kept.score != inside_at_ply2 || !forge::is_mate_score(kept.score)) {
        std::cerr << "FAIL in-band mate score " << inside << " came back as " << kept.score << "\n";
        return 1;
    }

    // After g3g4, Black has no capture, so a depth-1 search is a stand-pat at ply 1.
    // A stored loss of -MateInMaxPly becomes -MateInMaxPly + 1 there. That used to
    // leave the mate band and return to White as the centipawn score +31871.
    const forge::Board at_ply1 = board_after_first_move();
    const int loss_underflow = -forge::MateInMaxPly;
    const forge::SearchInfo loss = search_with_seed(searcher, root, at_ply1, loss_underflow, 1, false);
    const int bogus_loss_cp = -loss_underflow - 1;
    if (forge::is_mate_score(loss.score) || loss.score == bogus_loss_cp || loss.score > 1000 || loss.score < -1000) {
        std::cerr << "FAIL losing mate crossed MateInMaxPly and came back as " << loss.score << "\n";
        return 1;
    }

    // -(MateValue - 10) + ply 1 is still a mate. One negation brings it to the root.
    const int loss_inside = -(forge::MateValue - 10);
    const int loss_at_root = -loss_inside - 1;
    const forge::SearchInfo loss_kept = search_with_seed(searcher, root, at_ply1, loss_inside, 1, false);
    if (loss_kept.score != loss_at_root || !forge::is_mate_score(loss_kept.score)) {
        std::cerr << "FAIL in-band loss score " << loss_inside << " came back as " << loss_kept.score << "\n";
        return 1;
    }

    std::cout << "PASS\n";
    return 0;
}
