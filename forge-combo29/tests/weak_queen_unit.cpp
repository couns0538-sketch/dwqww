// Catches queen-as-attacker, ignored occupancy blockers, wrong slider type,
// wrong color, and any changed HCE value or trace coefficient.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/eval_params.hpp"
#include <array>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <random>
#include <string>

namespace forge {
int weak_queen_oracle_uncached(const Board&);
int weak_queen_oracle_cached(const Board&);
int weak_queen_oracle_traced(const Board&, EvalTrace&);
}
using namespace forge;

namespace {
std::uint64_t boards = 0, queens = 0, weak = 0, algebra = 0, fixtures = 0;
Evaluator evaluator;
void require(bool ok, const std::string& message) {
    if (!ok) { std::cerr << "FAIL: " << message << '\n'; std::exit(1); }
}
Bitboard old_mask(Bitboard diagonal, Bitboard straight, Bitboard bishops,
                  Bitboard rooks, Bitboard enemy_queens) {
    return ((diagonal & (bishops | enemy_queens)) |
            (straight & (rooks | enemy_queens))) & ~enemy_queens;
}
Bitboard new_mask(Bitboard diagonal, Bitboard straight, Bitboard bishops, Bitboard rooks) {
    return (diagonal & bishops) | (straight & rooks);
}
void check_algebra() {
    // Exhaust every possible single-bit assignment. Checking a bit proves the
    // whole identity because these expressions use only bitwise operations.
    for (unsigned bits = 0; bits < 32; ++bits) {
        const Bitboard d = (bits >> 0) & 1, s = (bits >> 1) & 1;
        const Bitboard b = (bits >> 2) & 1, r = (bits >> 3) & 1, q = (bits >> 4) & 1;
        if ((b & q) || (r & q) || (b & r)) continue;
        require(old_mask(d, s, b, r, q) == new_mask(d, s, b, r), "Single-bit identity");
        ++algebra;
    }
    require(algebra == 16, "Truth table coverage");
    // A deliberately invalid overlap proves disjointness is a real precondition.
    require(old_mask(1, 0, 1, 0, 1) != new_mask(1, 0, 1, 0), "Overlap counterexample");
    std::mt19937_64 rng(20261110);
    for (int i = 0; i < 100000; ++i) {
        const Bitboard q = rng(), b = rng() & ~q, r = rng() & ~(q | b);
        const Bitboard d = rng(), s = rng();
        require(old_mask(d, s, b, r, q) == new_mask(d, s, b, r), "64-bit identity");
        ++algebra;
    }
}
int weak_count(const Board& board) {
    int coefficient = 0;
    Bitboard used = 0;
    for (Color c : {White, Black}) for (int t = Pawn; t <= King; ++t) {
        const Bitboard bits = board.pieces(c, static_cast<PieceType>(t));
        require(!(used & bits), "Valid Board has overlapping piece bitboards");
        used |= bits;
    }
    require(used == board.occupied(), "Occupancy equals piece union");
    for (Color c : {White, Black}) {
        const Color enemy = opposite(c);
        Bitboard own = board.pieces(c, Queen);
        while (own) {
            const int sq = pop_lsb(own);
            const Bitboard d = attacks::bishop(sq, board.occupied());
            const Bitboard s = attacks::rook(sq, board.occupied());
            const Bitboard old = old_mask(d, s, board.pieces(enemy, Bishop),
                                         board.pieces(enemy, Rook), board.pieces(enemy, Queen));
            const Bitboard candidate = new_mask(d, s, board.pieces(enemy, Bishop), board.pieces(enemy, Rook));
            require(old == candidate, "Board predicate identity: " + board.fen());
            ++queens;
            if (old) { ++weak; coefficient += c == White ? 1 : -1; }
        }
    }
    return coefficient;
}
void check(const Board& board) {
    const int coefficient = weak_count(board);
    const int oracle = weak_queen_oracle_uncached(board);
    require(Evaluator::evaluate_uncached(board) == oracle, "Uncached HCE: " + board.fen());
    require(evaluator.evaluate(board) == oracle, "Cached HCE: " + board.fen());
    require(evaluator.evaluate(board) == oracle, "Repeat cache hit: " + board.fen());
    require(weak_queen_oracle_cached(board) == oracle, "Oracle cached HCE");
    EvalTrace actual, expected;
    const int a = evaluate_traced(board, actual);
    const int b = weak_queen_oracle_traced(board, expected);
    require(a == b && actual.coefficients == expected.coefficients && actual.phase == expected.phase &&
            actual.scale == expected.scale && actual.side_to_move == expected.side_to_move &&
            actual.white_eval == expected.white_eval, "Full HCE trace: " + board.fen());
    require(actual.coefficients[params::WeakQueen] == coefficient, "WeakQueen coefficient");
    require(a == (board.side_to_move() == White ? oracle : -oracle), "Trace perspective");
    ++boards;
}
std::string fen(const std::array<char, 64>& squares, Color side) {
    std::string text;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const char p = squares[rank * 8 + file];
            if (!p) ++empty;
            else { if (empty) text += char('0' + empty); empty = 0; text += p; }
        }
        if (empty) text += char('0' + empty);
        if (rank) text += '/';
    }
    return text + (side == White ? " w - - 0 1" : " b - - 0 1");
}
void adversarial() {
    constexpr int queen_sq = 27; // d4, with every tested endpoint two squares away.
    constexpr int directions[8] = {-9, -8, -7, -1, 1, 7, 8, 9};
    for (Color color : {White, Black}) for (int delta : directions)
        for (char target : {'b', 'r', 'q'}) for (char blocker : std::string(".PNBRQpnbrq")) {
            std::array<char, 64> squares{};
            squares[0] = 'K'; squares[56] = 'k'; squares[queen_sq] = 'Q';
            squares[queen_sq + 2 * delta] = target;
            if (blocker != '.') squares[queen_sq + delta] = blocker;
            if (color == Black) for (char& p : squares) if (p)
                p = std::islower(static_cast<unsigned char>(p)) ? std::toupper(p) : std::tolower(p);
            Board board;
            std::string position = fen(squares, color);
            std::string error;
            bool parsed = board.set_fen(position, &error);
            int king = 56;
            // Keep the far enemy king outside the tested two-square ray
            // segment, and respect Board's side-that-moved check validation.
            for (int alternate : {7, 57, 6, 48, 15, 62, 55}) {
                if (parsed) break;
                squares[alternate] = squares[king]; squares[king] = 0;
                king = alternate;
                position = fen(squares, color);
                parsed = board.set_fen(position, &error);
            }
            require(parsed, "Adversarial FEN parse: " + position + " " + error);
            const bool diagonal = delta == -9 || delta == -7 || delta == 7 || delta == 9;
            // Nearest enemy b/r blocker is itself an attacker of matching type.
            // Any other blocker (including either queen) hides the far slider.
            const char visible = blocker == '.' ? target : blocker;
            const bool want = diagonal ? visible == 'b' : visible == 'r';
            const Bitboard mask = new_mask(attacks::bishop(queen_sq, board.occupied()),
                attacks::rook(queen_sq, board.occupied()), board.pieces(opposite(color), Bishop),
                board.pieces(opposite(color), Rook));
            require(bool(mask) == want, "Literal blocker/type expectation: " + board.fen());
            check(board);
            ++fixtures;
        }
}
} // namespace

int main(int argc, char** argv) {
    check_algebra();
    adversarial();
    if (argc > 1) {
        std::ifstream input(argv[1]);
        require(bool(input), "Open FEN fixtures");
        std::string text;
        unsigned count = 0;
        while (std::getline(input, text)) {
            Board board;
            require(board.set_fen(text), "Saved fixture parse");
            check(board); ++count;
        }
        require(count == 128, "128 saved positions");
    }
    for (unsigned seed : {20261110U, 3886096422U, 305419896U}) {
        std::mt19937 rng(seed);
        Board board;
        for (unsigned ply = 0; ply < 4096; ++ply) {
            check(board);
            const auto moves = board.legal_moves();
            if (moves.empty() || ply % 256 == 255) {
                require(board.set_fen(Board::StandardStartFen), "Legal walk restart");
                evaluator.clear();
            } else {
                const Move move = moves[rng() % moves.size()];
                Undo undo;
                require(board.make_move(move, undo), "Generated legal move");
                check(board);
                board.unmake_move(move, undo);
                check(board);
                require(board.make_move(move, undo), "Replay generated move");
            }
        }
    }
    require(weak > 100 && queens > 1000 && fixtures == 528, "Coverage thresholds");
    std::cout << "{\"passed\":true,\"algebra_cases\":" << algebra << ",\"adversarial_boards\":" << fixtures
              << ",\"boards\":" << boards << ",\"queens\":" << queens << ",\"weak_queens\":" << weak << "}\n";
}
