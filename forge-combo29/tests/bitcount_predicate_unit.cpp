// Catches single-support-as-double, missing empty/singleton handling, color
// mixups, exactly-two instead of at-least-two bishops, and any HCE/trace drift.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/eval_params.hpp"
#include <array>
#include <bit>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <random>
#include <string>

namespace forge {
int bitcount_predicate_oracle_uncached(const Board&);
int bitcount_predicate_oracle_cached(const Board&);
int bitcount_predicate_oracle_traced(const Board&, EvalTrace&);
}
using namespace forge;
namespace {
std::uint64_t algebra = 0, boards = 0, bishop_cases = 0, pawn_cases = 0;
Evaluator evaluator;
void require(bool ok, const std::string& why) {
    if (!ok) { std::cerr << "FAIL: " << why << '\n'; std::exit(1); }
}
void truth(Bitboard bits, bool many, bool one) {
    require(more_than_one(bits) == many, "At-least-two truth case");
    require((bits != 0 && !more_than_one(bits)) == one, "Exactly-one truth case");
    ++algebra;
}
void algebra_cases() {
    truth(0, false, false);
    truth(~Bitboard{0}, true, false);
    for (int i = 0; i < 64; ++i) {
        truth(square_bb(i), false, true);
        truth(~square_bb(i), true, false);
        for (int j = i + 1; j < 64; ++j) truth(square_bb(i) | square_bb(j), true, false);
    }
    std::mt19937_64 random(0xb17c0a1720261110ULL);
    for (int i = 0; i < 100000; ++i) {
        const Bitboard bits = random();
        const int count = std::popcount(bits);
        truth(bits, count >= 2, count == 1);
    }
    require(algebra == 102146, "Algebra case coverage");
}
std::string fen(const std::array<char, 64>& squares, Color side) {
    std::string text;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const char p = squares[8 * rank + file];
            if (!p) ++empty;
            else { if (empty) text += char('0' + empty); empty = 0; text += p; }
        }
        if (empty) text += char('0' + empty);
        if (rank) text += '/';
    }
    return text + (side == White ? " w - - 0 1" : " b - - 0 1");
}
Board position(std::array<char, 64> squares, Color side) {
    // Keep both kings off all tested piece squares. FEN validation also checks
    // the side-that-moved king, so generated evaluation fixtures remain valid.
    Board board;
    for (int w : {4, 0, 7, 3, 1, 6}) for (int b : {60, 56, 63, 59, 57, 62}) {
        if (squares[w] || squares[b]) continue;
        squares[w] = 'K'; squares[b] = 'k';
        const std::string text = fen(squares, side);
        squares[w] = 0; squares[b] = 0;
        if (board.set_fen(text)) return board;
    }
    require(false, "No valid king placement: " + fen(squares, side));
    return board;
}
EvalTrace check(const Board& board) {
    const int expected = bitcount_predicate_oracle_uncached(board);
    require(Evaluator::evaluate_uncached(board) == expected, "Uncached HCE: " + board.fen());
    require(evaluator.evaluate(board) == expected, "Cached HCE: " + board.fen());
    require(evaluator.evaluate(board) == expected, "Repeated cache hit: " + board.fen());
    require(bitcount_predicate_oracle_cached(board) == expected, "Oracle cache");
    EvalTrace actual, oracle;
    const int a = evaluate_traced(board, actual);
    const int b = bitcount_predicate_oracle_traced(board, oracle);
    require(a == b && actual.coefficients == oracle.coefficients && actual.phase == oracle.phase &&
        actual.scale == oracle.scale && actual.side_to_move == oracle.side_to_move &&
        actual.white_eval == oracle.white_eval, "Complete trace: " + board.fen());
    require(a == (board.side_to_move() == White ? expected : -expected), "Trace perspective");
    ++boards;
    return actual;
}
void bishop_fixtures() {
    // Includes zero, singleton, same-/opposite-color pairs, and promoted triples.
    // The second arrangement puts all three bishops on one square color.
    for (const auto& spots : {std::array<int, 6>{18, 21, 26, 42, 45, 34},
                              std::array<int, 6>{18, 20, 22, 42, 44, 46}})
        for (unsigned white = 0; white < 8; ++white) for (unsigned black = 0; black < 8; ++black)
            for (Color side : {White, Black}) {
                std::array<char, 64> squares{};
                squares[8] = 'P'; squares[55] = 'p';
                for (int i = 0; i < 3; ++i) {
                    if (white & (1U << i)) squares[spots[i]] = 'B';
                    if (black & (1U << i)) squares[spots[i + 3]] = 'b';
                }
                const Board board = position(squares, side);
                const auto trace = check(board);
                const int want = (std::popcount(white) >= 2 ? 1 : 0) - (std::popcount(black) >= 2 ? 1 : 0);
                require(trace.coefficients[params::BishopPair] == want, "Literal BishopPair coefficient");
                ++bishop_cases;
            }
}
void pawn_fixtures() {
    for (Color color : {White, Black}) for (int rank = 2; rank <= 6; ++rank)
        for (int file = 0; file < 8; ++file) for (unsigned supports = 0; supports < 4; ++supports)
            for (bool phalanx : {false, true}) for (Color side : {White, Black}) {
                const int r = color == White ? rank : 7 - rank;
                const int behind = color == White ? r - 1 : r + 1;
                if ((file == 0 && (supports & 1)) || (file == 7 && (supports & 2))) continue;
                std::array<char, 64> squares{};
                const char piece = color == White ? 'P' : 'p';
                squares[8 * r + file] = piece;
                if (supports & 1) squares[8 * behind + file - 1] = piece;
                if (supports & 2) squares[8 * behind + file + 1] = piece;
                if (phalanx) squares[8 * r + (file == 7 ? file - 1 : file + 1)] = piece;
                const Board board = position(squares, side);
                const auto trace = check(board);
                const int want = supports == 3 ? (color == White ? 1 : -1) : 0;
                require(trace.coefficients[params::PawnDoubleSupport] == want, "Literal PawnDoubleSupport coefficient");
                ++pawn_cases;
            }
}
} // namespace
int main(int argc, char** argv) {
    algebra_cases();
    bishop_fixtures();
    pawn_fixtures();
    if (argc > 1) {
        std::ifstream input(argv[1]);
        require(bool(input), "Open saved fixtures");
        std::string text;
        int count = 0;
        while (std::getline(input, text)) {
            Board board;
            require(board.set_fen(text), "Saved fixture parse");
            check(board); ++count;
        }
        require(count == 128, "128 saved fixtures");
    }
    for (unsigned seed : {20261110U, 3886096422U, 305419896U}) {
        std::mt19937 random(seed);
        Board board;
        for (unsigned ply = 0; ply < 4096; ++ply) {
            check(board);
            const auto moves = board.legal_moves();
            if (moves.empty() || ply % 256 == 255) {
                require(board.set_fen(Board::StandardStartFen), "Legal walk restart");
                evaluator.clear();
            } else {
                const Move move = moves[random() % moves.size()];
                Undo undo;
                require(board.make_move(move, undo), "Legal move");
                check(board);
                board.unmake_move(move, undo);
                check(board);
                require(board.make_move(move, undo), "Replay move");
            }
        }
    }
    require(bishop_cases == 256 && pawn_cases == 1120, "Fixture coverage");
    std::cout << "{\"passed\":true,\"algebra_cases\":" << algebra << ",\"bishop_fixtures\":" << bishop_cases
              << ",\"pawn_fixtures\":" << pawn_cases << ",\"boards\":" << boards << "}\n";
}
