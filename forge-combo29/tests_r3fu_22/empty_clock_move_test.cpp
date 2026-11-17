// Empty-clock move choice: hash move if it is legal, otherwise one ply and
// at most 2000 nodes, otherwise the first legal move. Also reuses one
// Searcher at Threads 2 then 4 and asks for an empty-clock move from a
// mated, a stalemated, and a drawn root.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>
#include <string>

namespace {

int failures = 0;

void fail(const std::string& message) {
    ++failures;
    std::cerr << "FAIL " << message << '\n';
}

[[nodiscard]] bool is_legal(const forge::Board& board, forge::Move move) {
    if (move.is_none()) return false;
    for (const forge::Move candidate : board.legal_moves()) {
        if (candidate == move) return true;
    }
    return false;
}

[[nodiscard]] forge::Move first_legal(const forge::Board& board) {
    const forge::MoveList moves = board.legal_moves();
    return moves.empty() ? forge::Move::none() : moves.front();
}

void expect_depth1(const char* label, const char* fen) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        fail(std::string(label) + " fen");
        return;
    }
    forge::Searcher reference(16, 1);
    forge::SearchLimits depth;
    depth.depth = 1;
    const forge::SearchInfo full = reference.search(board, depth, false);

    forge::Searcher searcher(16, 1);
    forge::SearchLimits empty;
    empty.time_ms = 0;
    empty.move_overhead_ms = 10;
    const forge::SearchInfo info = searcher.search(board, empty, false);
    if (info.nodes > 2000 || info.depth != 1 || info.best_move != full.best_move || !is_legal(board, info.best_move) ||
        info.nodes != full.nodes) {
        fail(std::string(label) + " nodes " + std::to_string(info.nodes) + " depth " + std::to_string(info.depth) +
             " move " + forge::Board::move_to_uci(info.best_move) + " full " +
             forge::Board::move_to_uci(full.best_move) + " full_nodes " + std::to_string(full.nodes));
        return;
    }
    std::cout << "PASS " << label << " depth 1 nodes " << info.nodes << " move "
              << forge::Board::move_to_uci(info.best_move) << '\n';
}

void expect_hash(const char* label, const char* fen) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        fail(std::string(label) + " fen");
        return;
    }
    forge::Searcher searcher(16, 1);
    forge::SearchLimits depth;
    depth.depth = 6;
    const forge::SearchInfo full = searcher.search(board, depth, false);
    forge::SearchLimits empty;
    empty.time_ms = 0;
    empty.move_overhead_ms = 10;
    const forge::SearchInfo info = searcher.search(board, empty, false);
    if (info.nodes != 0 || info.depth != 0 || info.best_move != full.best_move || !is_legal(board, info.best_move)) {
        fail(std::string(label) + " hash nodes " + std::to_string(info.nodes) + " move " +
             forge::Board::move_to_uci(info.best_move) + " wanted " + forge::Board::move_to_uci(full.best_move));
        return;
    }
    std::cout << "PASS " << label << " hash move " << forge::Board::move_to_uci(info.best_move) << '\n';
}

void expect_unfinished(const char* label, const char* fen) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        fail(std::string(label) + " fen");
        return;
    }
    forge::Searcher searcher(16, 1);
    forge::SearchLimits empty;
    empty.time_ms = 0;
    empty.move_overhead_ms = 10;
    empty.nodes = 1;
    empty.nodes_specified = true;
    const forge::SearchInfo info = searcher.search(board, empty, false);
    const forge::Move first = first_legal(board);
    if (info.depth != 0 || info.nodes > 1 || info.best_move != first) {
        fail(std::string(label) + " unfinished nodes " + std::to_string(info.nodes) + " depth " +
             std::to_string(info.depth) + " move " + forge::Board::move_to_uci(info.best_move));
        return;
    }
    std::cout << "PASS " << label << " unfinished first " << forge::Board::move_to_uci(info.best_move) << '\n';
}

void expect_terminal(forge::Searcher& searcher, const char* label, const char* fen, bool drawn) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        fail(std::string(label) + " fen");
        return;
    }
    const bool mate = board.in_check() && !board.has_legal_move();
    const bool stalemate = !board.in_check() && !board.has_legal_move();
    const bool draw = board.has_legal_move() && (board.halfmove_clock() >= 100 || board.is_insufficient_material());
    if (drawn) {
        if (!draw) fail(std::string(label) + " is not a drawn root");
    } else if (label[0] == 'm') {
        if (!mate) fail(std::string(label) + " is not mate");
    } else if (!stalemate) {
        fail(std::string(label) + " is not stalemate");
    }
    forge::SearchLimits empty;
    empty.time_ms = 0;
    empty.move_overhead_ms = 10;
    const forge::SearchInfo info = searcher.search(board, empty, false);
    if (info.nodes != 0) {
        fail(std::string(label) + " nodes " + std::to_string(info.nodes));
        return;
    }
    if (drawn) {
        if (!is_legal(board, info.best_move)) {
            fail(std::string(label) + " illegal " + forge::Board::move_to_uci(info.best_move));
            return;
        }
    } else if (!info.best_move.is_none()) {
        fail(std::string(label) + " produced " + forge::Board::move_to_uci(info.best_move));
        return;
    }
    std::cout << "PASS " << label << " nodes " << info.nodes << '\n';
}

} // namespace

int main() {
    constexpr const char* start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    constexpr const char* kiwi = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    expect_depth1("start", start);
    expect_depth1("kiwi", kiwi);
    expect_hash("start", start);
    expect_hash("kiwi", kiwi);
    expect_unfinished("start", start);
    expect_unfinished("kiwi", kiwi);

    forge::Searcher searcher(16, 1);
    searcher.set_threads(2);
    {
        forge::Board board;
        if (!board.set_fen(start)) fail("start fen");
        forge::SearchLimits depth;
        depth.depth = 3;
        (void)searcher.search(board, depth, false);
    }
    searcher.set_threads(4);
    {
        forge::Board board;
        if (!board.set_fen(start)) fail("start fen");
        forge::SearchLimits depth;
        depth.depth = 3;
        (void)searcher.search(board, depth, false);
    }
    expect_terminal(searcher, "mate", "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1", false);
    expect_terminal(searcher, "stalemate", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", false);
    expect_terminal(searcher, "draw", "8/8/8/4k3/8/8/4K3/R7 w - - 100 1", true);

    if (failures != 0) {
        std::cerr << failures << " empty-clock failures\n";
        return 1;
    }
    std::cout << "PASS empty clock move\n";
    return 0;
}
