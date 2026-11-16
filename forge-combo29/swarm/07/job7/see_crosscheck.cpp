// see_crosscheck.cpp -- compares Board::see_ge(move, t) with an independent, slow,
// obviously-correct SEE implemented here from the definition, over random legal play.
//
// The independent implementation:
//   * simulates the capture on a local copy,
//   * repeatedly finds the least valuable attacker of the destination square for the side
//     to recapture, using the engine's own attack tables on the simulated occupancy,
//   * runs the standard swap algorithm from the back of the exchange list,
//   * handles en passant (the victim stands on a different square) and promotions.
// It deliberately does NOT reuse Board::see_ge or its helpers.
//
// For every legal move and a set of thresholds t in {-1, 0, 1, 50, 100, 900}, the engine's
// boolean see_ge(move, t) must equal (reference_see >= t).
#include "forge/board.hpp"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>

using namespace forge;

namespace {

// The engine's SEE prices a king at 0 (see include/forge/eval.hpp:32 SeePieceValue and the
// comment at src/search.cpp:157 "the SEE table stores king as 0"). Match that convention,
// otherwise every line where a king can recapture differs for a reason that is a documented
// engine choice, not a fault.
constexpr std::array<int, 7> Val{0, 100, 300, 300, 500, 900, 0};

struct Sim {
    std::array<Piece, 64> sq{};
    Bitboard occ = 0;
    Bitboard side_bits[2] = {0, 0};

    static Sim from(const Board& b) {
        Sim s;
        for (int i = 0; i < 64; ++i) s.sq[static_cast<std::size_t>(i)] = b.piece_at(i);
        s.occ = b.occupied();
        s.side_bits[0] = b.occupied(White);
        s.side_bits[1] = b.occupied(Black);
        return s;
    }
    void erase(int s) {
        const Piece p = sq[static_cast<std::size_t>(s)];
        if (p == Empty) return;
        sq[static_cast<std::size_t>(s)] = Empty;
        occ &= ~square_bb(s);
        side_bits[static_cast<std::size_t>(color_of(p))] &= ~square_bb(s);
    }
    void place(int s, Piece p) {
        erase(s);
        sq[static_cast<std::size_t>(s)] = p;
        occ |= square_bb(s);
        side_bits[static_cast<std::size_t>(color_of(p))] |= square_bb(s);
    }
    [[nodiscard]] Bitboard side(Color c) const { return side_bits[static_cast<std::size_t>(c)]; }
    [[nodiscard]] Bitboard type(Color c, PieceType t) const {
        Bitboard r = 0;
        for (int i = 0; i < 64; ++i) {
            const Piece p = sq[static_cast<std::size_t>(i)];
            if (p != Empty && color_of(p) == c && piece_type(p) == t) r |= square_bb(i);
        }
        return r;
    }
};

// All pieces of `by` that attack square `to` on the simulated board, ignoring pins.
Bitboard attackers(const Sim& s, Color by, int to) {
    Bitboard r = 0;
    r |= attacks::pawn(opposite(by), to) & s.type(by, Pawn);
    r |= attacks::knight(to) & s.type(by, Knight);
    r |= attacks::king(to) & s.type(by, King);
    const Bitboard diag = (s.type(by, Bishop) | s.type(by, Queen));
    const Bitboard orth = (s.type(by, Rook) | s.type(by, Queen));
    r |= attacks::bishop(to, s.occ) & diag;
    r |= attacks::rook(to, s.occ) & orth;
    return r & s.side(by);
}

int cheapest_valuer(const Sim& s, Color by, int to, int& from_square) {
    int best = 1000000;
    from_square = -1;
    Bitboard a = attackers(s, by, to);
    while (a != 0) {
        const int from = pop_lsb(a);
        const int v = Val[static_cast<std::size_t>(piece_type(s.sq[static_cast<std::size_t>(from)]))];
        if (v < best) { best = v; from_square = from; }
    }
    return best;
}

// Returns true when the static exchange for `move` gains at least `threshold`.
bool reference_see_ge(const Board& board, Move move, int threshold) {
    const Color us = board.side_to_move();
    Sim s = Sim::from(board);
    const int from = move.from;
    const int to = move.to;
    const bool ep = (move.flags & EnPassant) != 0U;
    const int victim_square = ep ? to - pawn_push_delta(us) : to;
    const Piece moving = s.sq[static_cast<std::size_t>(from)];
    const Piece victim = s.sq[static_cast<std::size_t>(victim_square)];

    // Gain list: gain[0] = value of the first victim (+ promotion delta).
    std::vector<int> gain;
    gain.push_back(Val[static_cast<std::size_t>(piece_type(victim))]);
    if (move.is_promotion()) {
        gain[0] += Val[move.promotion] - Val[Pawn];
    }

    s.erase(victim_square);
    s.erase(from);
    s.place(to, move.is_promotion() ? make_piece(us, move.promotion) : moving);

    // Swap-list algorithm. gain[i] must be the value the side to move at step i-1 stands to
    // lose if the exchange stops after its own capture, which requires carrying the value of
    // the piece currently standing on `to` -- not merely the cheapest attacker's value. My
    // first version used `v - gain.back()` and was wrong: it reported b2b4 here as a losing
    // capture when White wins a knight for a pawn (settled independently with python-chess).
    Color stm = opposite(us);
    int standing_value = Val[static_cast<std::size_t>(
        piece_type(move.is_promotion() ? make_piece(us, move.promotion) : moving))];
    while (true) {
        int next_from = -1;
        const int v = cheapest_valuer(s, stm, to, next_from);
        if (next_from < 0) break;
        // The side now to move captures the piece standing on `to`, whose value is
        // standing_value: gain = standing_value - (what it may lose next).
        gain.push_back(standing_value - gain.back());
        standing_value = v;
        s.erase(next_from);
        PieceType standing = Pawn;
        for (int t = Pawn; t <= King; ++t) {
            if (Val[static_cast<std::size_t>(t)] == v) { standing = static_cast<PieceType>(t); break; }
        }
        s.place(to, make_piece(stm, standing));
        stm = opposite(stm);
    }

    // Standard back-propagation.
    for (int i = static_cast<int>(gain.size()) - 1; i > 0; --i) {
        gain[static_cast<std::size_t>(i - 1)] =
            -std::max(-gain[static_cast<std::size_t>(i - 1)],
                      gain[static_cast<std::size_t>(i)]);
    }
    return gain[0] >= threshold;
}

}  // namespace

// ABANDONED as an oracle (kept for the record): this reference disagreed with the engine on
// exf5 in "2b1kbn1/2r3p1/p1Pp1q2/5p2/2BpPP2/1P2Q2r/P1R4P/RNB1K3 w Q - 2 29". python-chess
// settles that case the engine's way: after exf5 Black's only legal captures are h3e3 and
// d4e3, so nothing recaptures on f5, and see_ge(exf5, 100)=true is right. The reference's
// attacker list was wrong (it invented a queen recapture), so ITS disagreements are not
// evidence about the engine. No finding is drawn from this program.
int main(int argc, char** argv) {
    const int games = argc > 1 ? std::atoi(argv[1]) : 60;
    const unsigned seed = argc > 2 ? static_cast<unsigned>(std::atoi(argv[2])) : 701u;
    std::mt19937_64 rng(seed);
    constexpr std::array<int, 6> thresholds{-1, 0, 1, 50, 100, 900};

    std::uint64_t compared = 0, mismatches = 0;
    std::string first;
    for (int game = 0; game < games; ++game) {
        Board board;
        for (int ply = 0; ply < 200; ++ply) {
            const auto moves = board.legal_moves();
            if (moves.size() == 0) break;
            for (const Move move : moves) {
                // SEE of a NON-capture is not defined by the exchange algorithm alone (the
                // engine and my reference legitimately differ there), so this cross-check
                // covers captures only and says so in its own output.
                if (!move.is_capture()) continue;
                for (const int t : thresholds) {
                    const bool engine = board.see_ge(move, t);
                    const bool ref = reference_see_ge(board, move, t);
                    ++compared;
                    if (engine != ref) {
                        ++mismatches;
                        if (first.empty()) {
                            first = "fen " + board.fen() + " move " + Board::move_to_uci(move) +
                                    " threshold " + std::to_string(t) +
                                    " engine " + (engine ? "true" : "false") +
                                    " reference " + (ref ? "true" : "false");
                        }
                    }
                }
            }
            const Move pick = moves[static_cast<std::size_t>(rng() % moves.size())];
            Undo undo;
            (void)board.make_move(pick, undo);
        }
    }
    std::printf("games %d seed %u (CAPTURES ONLY, all thresholds)\n", games, seed);
    std::printf("see_ge comparisons %llu  mismatches %llu\n",
                static_cast<unsigned long long>(compared),
                static_cast<unsigned long long>(mismatches));
    if (compared == 0) {
        std::printf("FAIL nothing compared: this run proves nothing\n");
        return 2;
    }
    if (mismatches != 0) {
        std::printf("FIRST MISMATCH %s\n", first.c_str());
        return 1;
    }
    std::printf("OK engine see_ge agreed with the reference at every threshold\n");
    return 0;
}
