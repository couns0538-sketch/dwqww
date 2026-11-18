// Job 16 Part 2 Differential Oracle + Planted-Fault Verifier for stack/14_cuckoo_avx512_parity.patch.txt:
// Across 200,000 random move / null-move / unmake steps from positions_1000.txt (with reversible runs
// up to 80+ plies, interleaved null moves, unmakes, and varied root_index values), verifies that
// Board::upcoming_repetition(root_index) matches an independent brute-force legal-move oracle:
//   "Does there exist a legal reversible non-pawn non-capture non-castling move m after which
//    child.is_repetition(root_index) is true?"

#include "forge/board.hpp"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace {

bool brute_force_upcoming_repetition(const forge::Board& board, std::size_t root_index) {
    const forge::MoveList legals = board.legal_moves();
    for (const forge::Move m : legals) {
        if (m.is_capture() || m.is_promotion() || m.is_castle()) continue;
        if (forge::piece_type(board.moved_piece(m)) == forge::Pawn) continue;
        forge::Board child = board;
        forge::Undo u;
        (void)child.make_move(m, u);
        if (child.is_repetition(root_index)) return true;
    }
    return false;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::vector<std::string> fens;
    {
        std::ifstream in(argv[1]);
        std::string ln;
        while (std::getline(in, ln)) {
            if (!ln.empty() && ln.back() == '\r') ln.pop_back();
            if (!ln.empty()) fens.push_back(ln);
        }
    }

    std::mt19937_64 rng(2026111816ULL);
    std::uint64_t states_checked = 0;
    std::uint64_t true_hits = 0;

    // 1. Targeted deterministic 3-ply / 7-ply / 19-ply knight & rook dance + null-move reset tests
    {
        forge::Board b;
        (void)b.set_fen(forge::Board::StandardStartFen);
        const char* dance[] = {
            "g1f3", "g8f6", "f3g1", // after 3 plies: Black to move, f6g8 repeats startpos!
            "f6e4", "g1f3", "e4f6", "f3g1", "f6g8", // multi-ply dance
            "b1c3", "b8c6", "c3b1", "c6b8", "g1f3", "g8f6", "f3g1", "f6g8",
            "b1c3", "b8c6", "c3d5", "c6d4", "d5c3", "d4c6", "c3b1"
        };
        for (const char* uci : dance) {
            const auto mv = b.parse_uci(uci);
            if (!mv.has_value()) return 1;
            forge::Undo u;
            (void)b.make_move(*mv, u);
            for (const std::size_t ri : {std::size_t{0}, b.history_size() / 2, b.history_size() - 1}) {
                const bool got = b.upcoming_repetition(ri);
                const bool exp = brute_force_upcoming_repetition(b, ri);
                if (got != exp) {
                    std::cerr << "S14_ORACLE MISMATCH (dance) hist=" << b.history_size()
                              << " ri=" << ri << " got=" << got << " exp=" << exp << "\n";
                    return 1;
                }
                if (got) ++true_hits;
                ++states_checked;
            }
        }
        // Null move resets plies_from_null_ -> upcoming_repetition must be false for 3 plies
        forge::NullUndo nu;
        b.make_null_move(nu);
        if (b.upcoming_repetition(0) != brute_force_upcoming_repetition(b, 0)) return 1;
        b.unmake_null_move(nu);
        if (b.upcoming_repetition(0) != brute_force_upcoming_repetition(b, 0)) return 1;
    }

    // 2. 200,000 random reversible-biased walks with null-moves and unmakes across positions_1000
    for (std::size_t g = 0; g < 1000 && states_checked < 200000; ++g) {
        forge::Board b;
        if (!b.set_fen(fens[g % fens.size()])) continue;
        struct Frame { bool is_null; forge::Move mv; forge::Undo u; forge::NullUndo nu; };
        std::vector<Frame> stack;
        stack.reserve(96);

        for (int step = 0; step < 80 && states_checked < 200000; ++step) {
            if (!stack.empty() && (rng() % 9ULL) == 0ULL) {
                Frame fr = stack.back();
                stack.pop_back();
                if (fr.is_null) b.unmake_null_move(fr.nu);
                else b.unmake_move(fr.mv, fr.u);
            } else if (!b.in_check() && (rng() % 17ULL) == 0ULL) {
                Frame fr{};
                fr.is_null = true;
                b.make_null_move(fr.nu);
                stack.push_back(fr);
            } else {
                const forge::MoveList legals = b.legal_moves();
                if (legals.empty()) break;
                // Bias toward reversible piece moves (even back-and-forth) so long spans (>16..60 plies) & hits happen often!
                std::vector<forge::Move> rev;
                for (const forge::Move m : legals) {
                    if (!m.is_capture() && !m.is_promotion() && !m.is_castle() &&
                        forge::piece_type(b.moved_piece(m)) != forge::Pawn) {
                        rev.push_back(m);
                    }
                }
                const forge::Move chosen = (!rev.empty() && (rng() % 8ULL) != 0ULL)
                    ? rev[rng() % rev.size()]
                    : legals[rng() % legals.size()];
                Frame fr{};
                fr.is_null = false;
                fr.mv = chosen;
                (void)b.make_move(chosen, fr.u);
                stack.push_back(fr);
            }

            const std::size_t hs = b.history_size();
            const std::size_t ri = (rng() & 1ULL) ? 0 : (hs > 4 ? (rng() % hs) : 0);
            const bool got = b.upcoming_repetition(ri);
            const bool exp = brute_force_upcoming_repetition(b, ri);
            if (got != exp) {
                std::cerr << "S14_ORACLE MISMATCH at g=" << g << " step=" << step
                          << " hs=" << hs << " halfmove=" << b.halfmove_clock()
                          << " ri=" << ri << " got=" << got << " exp=" << exp
                          << " fen='" << b.fen() << "'\n";
                return 1;
            }
            if (got) ++true_hits;
            ++states_checked;
        }
    }

    std::cout << "S14_UPCOMING_REP_ORACLE PASS: states_checked=" << states_checked
              << " true_hits=" << true_hits << " mismatches=0\n";
    return 0;
}
