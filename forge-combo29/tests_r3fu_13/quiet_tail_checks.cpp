#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>
#include <string>

namespace {

int fails = 0;

void expect(bool ok, const std::string& name) {
    std::cout << (ok ? "PASS " : "FAIL ") << name << "\n";
    if (!ok) ++fails;
}

forge::SearchInfo search_fen(forge::Searcher& searcher, const std::string& fen, int depth) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        forge::SearchInfo empty;
        empty.score = 0;
        return empty;
    }
    forge::SearchLimits limits;
    limits.depth = depth;
    searcher.clear();
    return searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
}

bool only_quiet_check_mate(forge::Board& board, const std::string& uci) {
    const auto expected = board.parse_uci(uci);
    if (!expected || expected->is_capture() || expected->is_promotion() || !board.gives_check(*expected)) return false;
    int mates = 0;
    bool expected_mates = false;
    for (const forge::Move shot : board.legal_moves()) {
        forge::Undo undo;
        if (!board.make_move(shot, undo)) continue;
        const bool mate = board.in_check() && board.legal_moves().empty();
        board.unmake_move(shot, undo);
        if (!mate) continue;
        ++mates;
        if (shot == *expected) expected_mates = true;
    }
    return expected_mates && mates == 1;
}

} // namespace

int main() {
    forge::tune::QuietExtinction = true;
    forge::Searcher searcher(16, 1);

    // After Qg6 and ...a6, the only mate is the quiet check Qh7.
    // Two earlier quiet checks in that node are not mate; the tail must keep Qh7.
    {
        forge::Board board;
        expect(board.set_fen("2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"), "setup fen");
        forge::Undo u1;
        forge::Undo u2;
        const auto setup = board.parse_uci("g3g6");
        expect(setup.has_value() && board.make_move(*setup, u1), "play g3g6");
        const auto reply = board.parse_uci("a7a6");
        expect(reply.has_value() && board.make_move(*reply, u2), "play a7a6");
        expect(only_quiet_check_mate(board, "g6h7"), "g6h7 is the only mate and it is a quiet check");
        const std::string fen = board.fen();
        const forge::SearchInfo info = search_fen(searcher, fen, 4);
        expect(forge::Board::move_to_uci(info.best_move) == "g6h7" && info.score > 30000,
               "option on finds the only quiet check g6h7");
        std::cout << "quiet_check move " << forge::Board::move_to_uci(info.best_move) << " score " << info.score << "\n";
    }

    // Mate in 2. The mating shot Qh7 is a quiet check that sits behind other quiets.
    {
        const std::string fen = "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1";
        const forge::SearchInfo info = search_fen(searcher, fen, 10);
        const bool move_ok = forge::Board::move_to_uci(info.best_move) == "g3g6" && info.score > 30000;
        expect(move_ok, "option on finds quiet mate line g3g6");
        bool pv_has_quiet_mate = false;
        for (const forge::Move move : info.pv) {
            if (forge::Board::move_to_uci(move) == "g6h7") pv_has_quiet_mate = true;
        }
        expect(pv_has_quiet_mate, "pv contains quiet mating check g6h7");
        forge::Board board;
        expect(board.set_fen(fen), "mate fen");
        forge::Undo u1;
        forge::Undo u2;
        const auto setup = board.parse_uci("g3g6");
        expect(setup.has_value() && board.make_move(*setup, u1), "mate prefix g3g6");
        const auto reply = board.parse_uci("c6e5");
        expect(reply.has_value() && board.make_move(*reply, u2), "mate prefix c6e5");
        expect(only_quiet_check_mate(board, "g6h7"), "g6h7 is the only quiet checking mate after c6e5");
        std::cout << "quiet_mate move " << forge::Board::move_to_uci(info.best_move) << " score " << info.score << " pv";
        for (const forge::Move move : info.pv) std::cout << " " << forge::Board::move_to_uci(move);
        std::cout << "\n";
    }

    std::cout << "fails " << fails << "\n";
    return fails == 0 ? 0 : 1;
}
