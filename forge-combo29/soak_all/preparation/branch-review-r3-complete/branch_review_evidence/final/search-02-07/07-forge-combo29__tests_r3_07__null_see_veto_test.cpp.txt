#include "forge/search.hpp"

#include <iostream>
#include <string>
#include <string_view>

namespace {

int failures = 0;

void expect(bool condition, std::string_view message) {
    if (condition) return;
    std::cerr << "fail: " << message << '\n';
    ++failures;
}

struct Rng {
    std::uint64_t state;
    std::uint64_t next() {
        std::uint64_t x = state;
        x ^= x << 7;
        x ^= x >> 9;
        x ^= x << 8;
        state = x;
        return x;
    }
};

int enemy_exchange(forge::Board& board, std::string_view uci) {
    forge::NullUndo undo;
    board.make_null_move(undo);
    int score = 999999;
    bool found = false;
    const forge::MoveList moves = board.pseudo_legal_moves(true);
    for (const forge::Move& move : moves) {
        if (forge::Board::move_to_uci(move) != uci) continue;
        found = board.is_legal(move);
        score = board.static_exchange(move);
        break;
    }
    board.unmake_null_move(undo);
    if (!found) return 999999;
    return score;
}

void expect_threat(const char* fen, bool threat, const char* label) {
    forge::Board board;
    std::string error;
    expect(board.set_fen(fen, &error), label);
    expect(!board.in_check(forge::White) && !board.in_check(forge::Black), label);
    const std::string before = board.fen();
    const bool got = forge::null_see_veto_threat(board);
    expect(board.fen() == before, label);
    expect(got == threat, label);
    if (got != threat) std::cerr << "  fen " << fen << " threat " << got << '\n';
}

void expect_exchange(const char* fen, const char* uci, bool loses, const char* label) {
    forge::Board board;
    expect(board.set_fen(fen), label);
    const int score = enemy_exchange(board, uci);
    expect(score != 999999, label);
    expect(loses ? score < 0 : score >= 0, label);
    if ((loses && score >= 0) || (!loses && score < 0) || score == 999999) {
        std::cerr << "  " << label << " see " << score << " move " << uci << '\n';
    }
}

void check_positions() {
    expect(!forge::tune::NullSeeVeto, "option starts off");
    expect_threat(std::string(forge::Board::StandardStartFen).c_str(), false, "start has no lesser capture");
    expect_threat("4k3/8/8/8/1n6/8/Q7/4K3 w - - 0 1", true, "knight takes a loose queen");
    expect_exchange("4k3/8/8/8/1n6/8/Q7/4K3 w - - 0 1", "b4a2", false, "loose queen exchange wins");
    expect_threat("4k3/8/8/3q4/8/8/8/4K2Q w - - 0 1", false, "queen takes queen is not cheaper");
    expect_threat("4k3/8/8/8/8/1b6/P7/4K3 w - - 0 1", false, "bishop takes a pawn is not dearer");
    expect_threat("k7/8/8/8/2B5/n7/8/7K w - - 0 1", false, "knight takes bishop is the same price");
    expect_threat("8/2Q5/4k3/3n4/2B5/8/8/K7 w - - 0 1", false, "pinned knight capture is illegal");
    expect_threat("8/2k5/8/2n5/4R3/3P4/8/4K3 w - - 0 1", true, "defended rook still loses to the knight");
    expect_exchange("8/2k5/8/2n5/4R3/3P4/8/4K3 w - - 0 1", "c5e4", false, "pawn defence does not save the rook");
    expect_threat("R7/4k3/1n6/8/8/8/8/4K3 w - - 0 1", true, "loose rook on the last rank");
    expect_exchange("R7/4k3/1n6/8/8/8/8/4K3 w - - 0 1", "b6a8", false, "loose rook exchange wins");
    expect_threat("R7/1P2k3/1n6/8/8/8/8/4K3 w - - 0 1", false, "promoting pawn makes the rook safe");
    expect_exchange("R7/1P2k3/1n6/8/8/8/8/4K3 w - - 0 1", "b6a8", true, "promoting recapture loses for the knight");
    expect_threat("4k3/8/8/p7/1Q6/8/8/4K3 w - - 0 1", true, "pawn takes a loose queen");
    expect_exchange("4k3/8/8/p7/1Q6/8/8/4K3 w - - 0 1", "a5b4", false, "pawn takes queen wins the exchange");
    expect_threat("4k3/8/8/Q7/8/8/r7/7K w - - 0 1", true, "rook takes a loose queen");
    expect_exchange("4k3/8/8/Q7/8/8/r7/7K w - - 0 1", "a2a5", false, "rook takes queen wins the exchange");
    expect_threat("4k3/8/8/7K/q7/8/8/R7 w - - 0 1", false, "queen takes a rook is not cheaper");
    expect_threat("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", false, "en passant is not a cheaper capture");
}

void check_searches() {
    forge::tune::NullSeeVeto = true;
    forge::Searcher searcher(16, 1);
    Rng rng{0x5ee0d011ULL};
    int done = 0;
    while (done < 200) {
        forge::Board board;
        expect(board.set_fen(forge::Board::StandardStartFen), "start fen");
        searcher.clear();
        for (int ply = 0; ply < 24 && done < 200; ++ply) {
            const forge::MoveList legal = board.legal_moves();
            if (legal.empty()) break;
            forge::SearchLimits limits;
            limits.depth = 10;
            const forge::SearchInfo info = searcher.search(
                board, limits, false, forge::Searcher::TTAccess::Exclusive);
            bool listed = false;
            for (const forge::Move& move : legal) {
                if (move == info.best_move) listed = true;
            }
            if (!listed || info.best_move.is_none() || !board.is_legal(info.best_move)) {
                std::cerr << "fail: illegal move " << forge::Board::move_to_uci(info.best_move)
                          << " fen " << board.fen() << " search " << done << '\n';
                ++failures;
                return;
            }
            forge::Board line = board;
            for (const forge::Move& pv_move : info.pv) {
                bool pv_listed = false;
                const forge::MoveList pv_legal = line.legal_moves();
                for (const forge::Move& candidate : pv_legal) {
                    if (candidate == pv_move) pv_listed = true;
                }
                if (!pv_listed || !line.is_legal(pv_move)) {
                    std::cerr << "fail: illegal pv move " << forge::Board::move_to_uci(pv_move)
                              << " fen " << line.fen() << " search " << done << '\n';
                    ++failures;
                    return;
                }
                forge::Undo pv_undo;
                if (!line.make_move(pv_move, pv_undo)) {
                    std::cerr << "fail: pv move rejected " << forge::Board::move_to_uci(pv_move)
                              << " search " << done << '\n';
                    ++failures;
                    return;
                }
            }
            ++done;
            if (done % 40 == 0) std::cout << "searches " << done << '\n';
            const forge::Move played = legal[static_cast<std::size_t>(rng.next() % legal.size())];
            forge::Undo undo;
            if (!board.make_move(played, undo)) {
                std::cerr << "fail: could not play " << forge::Board::move_to_uci(played) << '\n';
                ++failures;
                return;
            }
        }
    }
    std::cout << "searches " << done << " legal\n";
}

}  // namespace

int main() {
    check_positions();
    if (failures != 0) {
        std::cerr << failures << " position failures\n";
        return 1;
    }
    std::cout << "positions ok\n";
    check_searches();
    if (failures != 0) {
        std::cerr << failures << " search failures\n";
        return 1;
    }
    std::cout << "NullSeeVeto tests passed\n";
    return 0;
}
