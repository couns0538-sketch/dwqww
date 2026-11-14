#pragma once

#include "forge/board.hpp"

#include <algorithm>
#include <bit>
#include <cstdint>
#include <vector>

// KrkTablebase below is copied verbatim from tests_t12/krk_mate_test.cpp,
// introduced by commit 0ca7c0e00126fb58fa2bf03a1f69d7632b8b9619.
// Source blob: 329cad9acfee7e0a88e118911d14298818234244.
// Only its enclosing namespace differs. This is an independent retrograde
// algorithm, but it shares Forge board/move/attack primitives. It is not an
// external tablebase and does not model repetition or the fifty-move rule.
namespace soak {

// Exact retrograde tablebase for White King + White Rook vs Black King.
// State index: ((wk * 64 + wr) * 64 + bk) * 2 + stm, where stm = 0 (White), 1 (Black).
class KrkTablebase {
public:
    static constexpr std::size_t TotalStates = 64U * 64U * 64U * 2U;

    KrkTablebase() : dtm_(TotalStates, -1), legal_(TotalStates, 0) {
        forge::attacks::init();
        build();
    }

    [[nodiscard]] int dtm(int wk, int wr, int bk, int stm) const {
        return dtm_[index(wk, wr, bk, stm)];
    }

    [[nodiscard]] bool is_legal_state(int wk, int wr, int bk, int stm) const {
        return legal_[index(wk, wr, bk, stm)] != 0;
    }

    // Evaluates a White-to-move KRK move from (wk, wr, bk).
    // Returns exact distance-to-mate in plies from the root (>= 1) if the move
    // forces mate, or -1 if the move allows a draw (stalemate or rook loss).
    [[nodiscard]] int move_mate_plies(const forge::Board& root, const forge::Move& move) const {
        if (move.is_none() || !root.is_legal(move)) return -1;
        forge::Board next = root;
        forge::Undo undo;
        if (!next.make_move(move, undo)) return -1;
        if (!next.has_legal_move()) {
            return next.in_check() ? 1 : -1;
        }
        if (next.is_insufficient_material()) return -1;
        const forge::Bitboard wr_bb = next.pieces(forge::White, forge::Rook);
        if (wr_bb == 0) return -1;
        const int wk = next.king_square(forge::White);
        const int bk = next.king_square(forge::Black);
        const int wr = forge::lsb(wr_bb);
        const int child_dtm = dtm(wk, wr, bk, 1);
        if (child_dtm < 0) return -1;
        return 1 + child_dtm;
    }

private:
    std::vector<std::int16_t> dtm_;
    std::vector<std::uint8_t> legal_;

    [[nodiscard]] static constexpr std::size_t index(int wk, int wr, int bk, int stm) {
        return ((static_cast<std::size_t>(wk) * 64U + static_cast<std::size_t>(wr)) * 64U +
                static_cast<std::size_t>(bk)) * 2U + static_cast<std::size_t>(stm);
    }

    [[nodiscard]] static bool rook_attacks_bk(int wk, int wr, int bk) {
        return (forge::attacks::rook(wr, forge::square_bb(wk)) & forge::square_bb(bk)) != 0;
    }

    void build() {
        for (int wk = 0; wk < 64; ++wk) {
            for (int wr = 0; wr < 64; ++wr) {
                if (wr == wk) continue;
                for (int bk = 0; bk < 64; ++bk) {
                    if (bk == wk || bk == wr) continue;
                    if (forge::square_distance(wk, bk) <= 1) continue;
                    const bool bk_checked = rook_attacks_bk(wk, wr, bk);
                    if (!bk_checked) {
                        legal_[index(wk, wr, bk, 0)] = 1;
                    }
                    legal_[index(wk, wr, bk, 1)] = 1;
                }
            }
        }

        // Terminal checkmates (stm == 1, in check, no legal king move or rook capture).
        for (int wk = 0; wk < 64; ++wk) {
            for (int wr = 0; wr < 64; ++wr) {
                for (int bk = 0; bk < 64; ++bk) {
                    const std::size_t idx = index(wk, wr, bk, 1);
                    if (!legal_[idx]) continue;
                    if (!rook_attacks_bk(wk, wr, bk)) continue;
                    bool has_escape = false;
                    forge::Bitboard moves = forge::attacks::king(bk);
                    while (moves != 0) {
                        const int nbk = forge::pop_lsb(moves);
                        if (forge::square_distance(wk, nbk) <= 1) continue;
                        if (nbk == wr) {
                            has_escape = true;
                            break;
                        }
                        if (!rook_attacks_bk(wk, wr, nbk)) {
                            has_escape = true;
                            break;
                        }
                    }
                    if (!has_escape) dtm_[idx] = 0;
                }
            }
        }

        for (int ply = 1; ply <= 64; ++ply) {
            bool changed = false;
            if ((ply & 1) == 1) {
                // White to move: wins in `ply` if any legal move reaches a Black state with dtm == ply - 1.
                for (int wk = 0; wk < 64; ++wk) {
                    for (int wr = 0; wr < 64; ++wr) {
                        for (int bk = 0; bk < 64; ++bk) {
                            const std::size_t idx = index(wk, wr, bk, 0);
                            if (!legal_[idx] || dtm_[idx] >= 0) continue;
                            bool found = false;
                            forge::Bitboard kmoves = forge::attacks::king(wk);
                            while (kmoves != 0) {
                                const int nwk = forge::pop_lsb(kmoves);
                                if (nwk == wr || forge::square_distance(nwk, bk) <= 1) continue;
                                if (dtm_[index(nwk, wr, bk, 1)] == ply - 1) {
                                    found = true;
                                    break;
                                }
                            }
                            if (!found) {
                                const forge::Bitboard occ = forge::square_bb(wk) | forge::square_bb(bk);
                                forge::Bitboard rmoves = forge::attacks::rook(wr, occ);
                                while (rmoves != 0) {
                                    const int nwr = forge::pop_lsb(rmoves);
                                    if (nwr == wk || nwr == bk) continue;
                                    if (dtm_[index(wk, nwr, bk, 1)] == ply - 1) {
                                        found = true;
                                        break;
                                    }
                                }
                            }
                            if (found) {
                                dtm_[idx] = static_cast<std::int16_t>(ply);
                                changed = true;
                            }
                        }
                    }
                }
            } else {
                // Black to move: loses in `ply` iff >= 1 legal move, cannot capture undefended rook,
                // and every legal move leads to a solved White state (max dtm == ply - 1).
                for (int wk = 0; wk < 64; ++wk) {
                    for (int wr = 0; wr < 64; ++wr) {
                        for (int bk = 0; bk < 64; ++bk) {
                            const std::size_t idx = index(wk, wr, bk, 1);
                            if (!legal_[idx] || dtm_[idx] >= 0) continue;
                            int legal_count = 0;
                            int worst = -1;
                            bool can_draw = false;
                            forge::Bitboard kmoves = forge::attacks::king(bk);
                            while (kmoves != 0) {
                                const int nbk = forge::pop_lsb(kmoves);
                                if (forge::square_distance(wk, nbk) <= 1) continue;
                                if (nbk == wr) {
                                    can_draw = true;
                                    break;
                                }
                                if (rook_attacks_bk(wk, wr, nbk)) continue;
                                ++legal_count;
                                const int child = dtm_[index(wk, wr, nbk, 0)];
                                if (child < 0) {
                                    can_draw = true;
                                    break;
                                }
                                worst = std::max(worst, child);
                            }
                            if (!can_draw && legal_count > 0 && worst == ply - 1) {
                                dtm_[idx] = static_cast<std::int16_t>(ply);
                                changed = true;
                            }
                        }
                    }
                }
            }
            if (!changed) break;
        }
    }
};

struct KrkRootAssessment {
    bool supported = false;
    bool legal = false;
    int dtm_plies = -1; // Exact game-theoretic DTM; -1 means draw if supported/legal.
};

struct KrkMoveAssessment {
    bool supported = false;
    bool root_legal = false;
    bool move_legal = false;
    int root_dtm_plies = -1;
    int move_dtm_plies = -1; // Includes the candidate move; -1 means draw if legal.
    bool loses_forced_mate = false;
};

// The supplied soak KRK roots have White K+R, Black K, White to move, a
// zero halfmove clock and no castling/en-passant. Other inputs are explicitly
// unsupported, including KQK/KBBK, Black attackers and Black-to-move roots.
// Callers use fresh positions: history-dependent repetition is not assessed.
class KrkOracle {
public:
    [[nodiscard]] KrkRootAssessment assess_root(const forge::Board& root) const {
        KrkRootAssessment result;
        const auto wk = root.pieces(forge::White, forge::King);
        const auto wr = root.pieces(forge::White, forge::Rook);
        const auto bk = root.pieces(forge::Black, forge::King);
        if (root.side_to_move() != forge::White || root.castling_rights() != 0 ||
            root.ep_square() != -1 || root.halfmove_clock() != 0 ||
            std::popcount(wk) != 1 || std::popcount(wr) != 1 || std::popcount(bk) != 1 ||
            root.occupied() != (wk | wr | bk)) return result;
        result.supported = true;
        result.legal = tablebase_.is_legal_state(forge::lsb(wk), forge::lsb(wr), forge::lsb(bk), 0);
        if (result.legal)
            result.dtm_plies = tablebase_.dtm(forge::lsb(wk), forge::lsb(wr), forge::lsb(bk), 0);
        return result;
    }

    [[nodiscard]] KrkMoveAssessment assess_move(const forge::Board& root,
                                                 const forge::Move& move) const {
        const auto assessment = assess_root(root);
        KrkMoveAssessment result;
        result.supported = assessment.supported;
        result.root_legal = assessment.legal;
        result.root_dtm_plies = assessment.dtm_plies;
        if (!result.supported || !result.root_legal || move.is_none() || !root.is_legal(move))
            return result;
        result.move_legal = true;
        result.move_dtm_plies = tablebase_.move_mate_plies(root, move);
        result.loses_forced_mate = result.root_dtm_plies > 0 && result.move_dtm_plies < 0;
        return result;
    }

private:
    KrkTablebase tablebase_;
};

} // namespace soak
