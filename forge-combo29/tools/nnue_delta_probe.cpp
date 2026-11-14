// Compare the incremental NNUE update with a full refresh.
// Search records dirty_pieces before make_move and applies them later. Castling
// changes four features, a capture or en passant three, and a quiet move two.
// A null move changes no pieces, so the refreshed accumulator must be identical.

#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <cstdint>
#include <cstring>
#include <iostream>
#include <random>
#include <string>
#include <string_view>
#include <vector>

namespace {

int g_fails = 0;
float g_max_abs = 0.0F;
int g_moves = 0;
int g_eval_mismatch = 0;
int g_castle = 0;
int g_ep = 0;
int g_promo = 0;
int g_nulls = 0;

float max_abs_diff(const forge::nnue::Accumulator& left, const forge::nnue::Accumulator& right) {
    float worst = 0.0F;
    for (std::size_t side = 0; side < left.values.size(); ++side) {
        for (int unit = 0; unit < forge::nnue::HiddenSize; ++unit) {
            const float delta = left.values[side][static_cast<std::size_t>(unit)] -
                                right.values[side][static_cast<std::size_t>(unit)];
            const float abs_delta = delta < 0.0F ? -delta : delta;
            if (abs_delta > worst) worst = abs_delta;
        }
    }
    return worst;
}

void note_abs(float value) {
    if (value > g_max_abs) g_max_abs = value;
}

void check_move(forge::Board& board, const forge::nnue::Accumulator& parent, forge::Move move, std::string_view label) {
    const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
    if (dirty.count < 2 || dirty.count > 4) {
        std::cout << "FAIL dirty count " << dirty.count << " " << forge::Board::move_to_uci(move) << " " << label
                  << '\n';
        ++g_fails;
    }
    forge::nnue::Accumulator incremental;
    forge::nnue::update(parent, incremental, dirty);
    const int parent_eval = forge::nnue::evaluate(board, parent);
    if (move.is_castle()) ++g_castle;
    if ((move.flags & forge::EnPassant) != 0U) ++g_ep;
    if (move.is_promotion()) ++g_promo;
    forge::Undo undo;
    (void)board.make_move(move, undo);
    forge::nnue::Accumulator fresh;
    forge::nnue::refresh(board, fresh);
    const float worst = max_abs_diff(incremental, fresh);
    note_abs(worst);
    const int child_eval = forge::nnue::evaluate(board, fresh);
    const int incremental_eval = forge::nnue::evaluate(board, incremental);
    ++g_moves;
    if (incremental_eval != child_eval) {
        std::cout << "FAIL eval " << forge::Board::move_to_uci(move) << " incremental " << incremental_eval
                  << " refresh " << child_eval << " abs " << worst << " " << label << '\n';
        ++g_fails;
        ++g_eval_mismatch;
    }
    board.unmake_move(move, undo);
    forge::nnue::Accumulator restored;
    forge::nnue::refresh(board, restored);
    if (std::memcmp(parent.values.data(), restored.values.data(), sizeof(parent.values)) != 0) {
        std::cout << "FAIL unmake refresh " << forge::Board::move_to_uci(move) << " " << label << '\n';
        ++g_fails;
    }
    const int restored_eval = forge::nnue::evaluate(board, restored);
    if (restored_eval != parent_eval) {
        std::cout << "FAIL unmake eval " << forge::Board::move_to_uci(move) << " " << label << '\n';
        ++g_fails;
    }
}

void check_null(forge::Board& board, std::string_view label) {
    if (board.in_check()) return;
    ++g_nulls;
    forge::nnue::Accumulator before;
    forge::nnue::refresh(board, before);
    forge::NullUndo undo;
    board.make_null_move(undo);
    forge::nnue::Accumulator after;
    forge::nnue::refresh(board, after);
    if (std::memcmp(before.values.data(), after.values.data(), sizeof(before.values)) != 0) {
        std::cout << "FAIL null refresh " << label << '\n';
        ++g_fails;
    }
    board.unmake_null_move(undo);
    forge::nnue::Accumulator restored;
    forge::nnue::refresh(board, restored);
    if (std::memcmp(before.values.data(), restored.values.data(), sizeof(before.values)) != 0) {
        std::cout << "FAIL null unmake " << label << '\n';
        ++g_fails;
    }
}

void check_position(const std::string& fen) {
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cout << "FAIL fen " << error << " " << fen << '\n';
        ++g_fails;
        return;
    }
    forge::nnue::Accumulator root;
    forge::nnue::refresh(board, root);
    const forge::MoveList legal = board.legal_moves();
    for (const forge::Move move : legal) check_move(board, root, move, fen);
    check_null(board, fen);
}

void walk(const std::string& fen, int plies, std::uint32_t seed) {
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cout << "FAIL walk fen " << error << '\n';
        ++g_fails;
        return;
    }
    std::mt19937 rng(seed);
    for (int ply = 0; ply < plies; ++ply) {
        forge::nnue::Accumulator parent;
        forge::nnue::refresh(board, parent);
        if (!board.in_check() && (rng() % 7U) == 0U) {
            check_null(board, "walk");
            forge::NullUndo undo;
            board.make_null_move(undo);
            continue;
        }
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty()) break;
        const forge::Move move = legal[static_cast<std::size_t>(rng() % legal.size())];
        check_move(board, parent, move, "walk");
        forge::Undo undo;
        (void)board.make_move(move, undo);
    }
}

} // namespace

int main() {
    if (!forge::nnue::available()) {
        std::cout << "FAIL network unavailable\n";
        return 1;
    }
    const std::vector<std::string> positions = {
        std::string(forge::Board::StandardStartFen),
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",
        "8/8/8/3pP3/8/8/4K3/k7 w - d6 0 1",
        "8/8/8/k2pP2R/8/8/8/4K3 w - d6 0 1",
        "8/8/8/8/2pPp3/8/8/k3K3 b - d3 0 1",
        "8/8/8/4k3/3Pp3/8/8/4K3 b - d3 0 1",
        "8/1k6/8/1Pp5/8/8/8/4K3 w - c6 0 1",
        "r3k2r/1P6/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "8/P7/8/8/8/8/8/k3K3 w - - 0 1",
        "7k/4P3/8/8/8/8/8/4K3 w - - 0 1",
        "3nk3/4P3/8/8/8/8/8/4R1K1 w - - 0 1",
        "3k4/8/8/8/8/8/8/R3K2R w KQ - 0 1",
        "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1",
    };
    for (const std::string& fen : positions) check_position(fen);
    walk(std::string(forge::Board::StandardStartFen), 80, 0x82b6a11dU);
    walk("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 60, 0x4f3e91c2U);
    walk("n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1", 40, 0x20261113U);
    std::cout << "moves " << g_moves << " castle " << g_castle << " ep " << g_ep << " promo " << g_promo
              << " null " << g_nulls << " fails " << g_fails << " eval_mismatch " << g_eval_mismatch
              << " max_abs " << g_max_abs << '\n';
    return g_fails == 0 ? 0 : 1;
}
