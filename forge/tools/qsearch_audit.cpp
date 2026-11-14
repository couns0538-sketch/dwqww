// Differential audit of Searcher::quiescence. Not part of the engine.
// Compares the engine with the capture/promotion qsearch contract:
//   - in check: every legal evasion, no stand-pat
//   - stalemate: draw
//   - tactical moves are searched
//   - stand-pat is used only when a non-tactical legal move exists
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

namespace forge {

struct SearcherTestProbe {
    static int quiescence(Searcher& searcher, Board& board, int alpha = -32000, int beta = 32000) {
        return searcher.quiescence(board, 0, alpha, beta, false);
    }
    static void reset(Searcher& searcher) {
        searcher.clear_hash();
        searcher.nodes_ = 0;
        searcher.aborted_ = false;
        searcher.seldepth_ = 0;
    }
    static std::uint64_t nodes(const Searcher& searcher) { return searcher.nodes_; }
};

} // namespace forge

namespace {

constexpr int MateScore = 30000;
constexpr int Infinity = 32000;

bool is_tactical(const forge::Move& move) {
    return move.is_capture() || (move.flags & forge::Promotion) != 0U;
}

struct Shape {
    bool checked = false;
    bool quiet = false;
    bool tactical = false;
    int legal = 0;
    int tactical_count = 0;
};

Shape classify(forge::Board& board) {
    Shape shape;
    shape.checked = board.in_check(board.side_to_move());
    const auto moves = board.legal_moves();
    shape.legal = static_cast<int>(moves.size());
    for (const forge::Move move : moves) {
        if (is_tactical(move)) {
            shape.tactical = true;
            ++shape.tactical_count;
        } else {
            shape.quiet = true;
        }
    }
    return shape;
}

int engine_score(forge::Searcher& searcher, forge::Board& board, int alpha = -Infinity, int beta = Infinity) {
    return forge::SearcherTestProbe::quiescence(searcher, board, alpha, beta);
}

// Independent contract search. Stand-pat applies only when a quiet legal move exists.
int contract(forge::Board& board, int alpha, int beta, int ply, std::uint64_t& nodes, std::uint64_t cap) {
    if (++nodes > cap) return 1000000;
    if (ply >= 127) return forge::Searcher::evaluate(board);
    const bool checked = board.in_check(board.side_to_move());
    if (board.is_repetition() || board.halfmove_clock() >= 100) {
        if (!checked || board.has_legal_move()) return 0;
        return -MateScore + ply;
    }
    if (board.is_insufficient_material()) return 0;
    alpha = std::max(alpha, -MateScore + ply);
    beta = std::min(beta, MateScore - ply - 1);
    if (alpha >= beta) return alpha;

    const auto moves = board.legal_moves();
    if (moves.empty()) return checked ? -MateScore + ply : 0;

    std::vector<forge::Move> tactical;
    bool quiet = false;
    tactical.reserve(moves.size());
    for (const forge::Move move : moves) {
        if (is_tactical(move)) tactical.push_back(move);
        else quiet = true;
    }

    if (!checked && quiet) {
        const int stand_pat = forge::Searcher::evaluate(board);
        if (stand_pat >= beta) return beta;
        alpha = std::max(alpha, stand_pat);
        if (tactical.empty()) return alpha;
    }

    const std::vector<forge::Move> searched = checked
        ? std::vector<forge::Move>(moves.begin(), moves.end())
        : tactical;
    for (const forge::Move move : searched) {
        forge::Undo undo;
        (void)board.make_move(move, undo);
        const int score = -contract(board, -beta, -alpha, ply + 1, nodes, cap);
        board.unmake_move(move, undo);
        if (score == -1000000 || score == 1000000) return 1000000;
        if (score >= beta) return beta;
        alpha = std::max(alpha, score);
    }
    return alpha;
}

int best_listed_reply(forge::Searcher& searcher, forge::Board& board, const Shape& shape) {
    const auto moves = board.legal_moves();
    int best = -40000;
    bool any = false;
    for (const forge::Move move : moves) {
        if (!shape.checked && !is_tactical(move)) continue;
        forge::Undo undo;
        (void)board.make_move(move, undo);
        const int score = -engine_score(searcher, board);
        board.unmake_move(move, undo);
        best = std::max(best, score);
        any = true;
    }
    if (!any) {
        if (shape.checked) return -MateScore;
        if (shape.quiet) return forge::Searcher::evaluate(board);
        return 0;
    }
    if (!shape.checked && shape.quiet) best = std::max(best, forge::Searcher::evaluate(board));
    return best;
}

struct Mismatch {
    std::string fen;
    std::string kind;
    int engine = 0;
    int contract_score = 0;
    int listed = 0;
    int stand_pat = 0;
    Shape shape;
};

std::string kind_of(const Shape& shape, int engine, int contract_score) {
    if (!shape.checked && shape.legal == 0 && engine != 0) return "stalemate";
    if (shape.checked && shape.legal == 0 && engine != -MateScore) return "checkmate-score";
    if (shape.checked && engine < -MateScore + 128 && contract_score > -MateScore + 128) return "false-mate";
    if (shape.checked && engine > contract_score) return "inflated-evasion";
    if (shape.checked && engine < contract_score) return "dropped-evasion";
    if (!shape.checked && !shape.quiet && shape.tactical && engine > contract_score) return "forced-tactical-stand-pat";
    if (!shape.checked && shape.quiet && engine < contract_score) return "pruned-tactical";
    if (!shape.checked && !shape.quiet && shape.legal == 0) return "stalemate";
    return "other";
}

void consider(forge::Searcher& searcher, forge::Board& board, std::vector<Mismatch>& out,
              int& compared, int& contract_caps) {
    const std::string fen = board.fen();
    const std::string original = fen;
    const Shape shape = classify(board);
    const int stand_pat = forge::Searcher::evaluate(board);
    const int engine = engine_score(searcher, board);
    if (board.fen() != original) {
        out.push_back(Mismatch{fen, "board-not-restored", engine, engine, engine, stand_pat, shape});
        return;
    }
    const int listed = best_listed_reply(searcher, board, shape);
    std::uint64_t nodes = 0;
    const int agreed = contract(board, -Infinity, Infinity, 0, nodes, 200000);
    ++compared;
    if (agreed == 1000000) {
        ++contract_caps;
        std::cerr << "CAP " << fen << '\n';
        return;
    }
    if (board.fen() != original) {
        out.push_back(Mismatch{fen, "contract-board-not-restored", engine, agreed, listed, stand_pat, shape});
        return;
    }
    if (engine != agreed) {
        Mismatch mismatch{fen, kind_of(shape, engine, agreed), engine, agreed, listed, stand_pat, shape};
        out.push_back(std::move(mismatch));
    }
}

void audit_fen(forge::Searcher& searcher, std::string_view fen, std::vector<Mismatch>& out,
               int& compared, int& contract_caps, int& rejected) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        ++rejected;
        std::cerr << "REJECT " << fen << '\n';
        return;
    }
    consider(searcher, board, out, compared, contract_caps);
}

bool king_adjacent(int a, int b) {
    const int df = std::abs((a & 7) - (b & 7));
    const int dr = std::abs((a >> 3) - (b >> 3));
    return df <= 1 && dr <= 1;
}

std::string fen_from_squares(const std::array<char, 64>& squares, char side) {
    std::string fen;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const char piece = squares[static_cast<std::size_t>(rank * 8 + file)];
            if (piece == 0) {
                ++empty;
                continue;
            }
            if (empty != 0) {
                fen += static_cast<char>('0' + empty);
                empty = 0;
            }
            fen += piece;
        }
        if (empty != 0) fen += static_cast<char>('0' + empty);
        if (rank != 0) fen += '/';
    }
    fen += ' ';
    fen += side;
    fen += " - - 0 1";
    return fen;
}

} // namespace

int main() {
    forge::Searcher searcher(1);
    std::vector<Mismatch> mismatches;
    int compared = 0;
    int contract_caps = 0;
    int rejected = 0;

    const std::array<std::pair<const char*, const char*>, 12> named{{
        {"mate-black", "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"},
        {"stalemate-black", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"},
        {"favorable-stalemate", "5k1K/7P/8/8/8/8/8/8 w - - 0 1"},
        {"evasion-not-mate", "4r2k/8/8/8/8/8/8/4K3 w - - 0 1"},
        {"winning-rook-capture", "4k3/8/8/2q5/8/8/8/2R1K3 w - - 0 1"},
        {"ep-available", "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2"},
        {"losing-back-rank", "7k/8/8/8/8/7K/p7/1rR5 w - - 0 1"},
        {"quiet-mate-in-one", "k7/8/1K6/8/8/8/8/6Q1 w - - 0 1"},
        {"forced-promo-w", "8/P7/8/8/8/8/6q1/K1k5 w - - 0 1"},
        {"forced-promo-b", "5K1k/1Q6/8/8/8/8/7p/8 b - - 0 1"},
        {"forced-bishop-w", "8/8/8/8/8/1k6/1p6/BK6 w - - 0 1"},
        {"forced-bishop-b", "6kb/6P1/6K1/8/8/8/8/8 b - - 0 1"},
    }};
    std::cout << "named\n";
    for (const auto& [label, fen] : named) {
        const std::size_t before = mismatches.size();
        audit_fen(searcher, fen, mismatches, compared, contract_caps, rejected);
        forge::Board board;
        if (!board.set_fen(fen)) continue;
        const int stand = forge::Searcher::evaluate(board);
        const int engine = engine_score(searcher, board);
        const Shape shape = classify(board);
        std::cout << label << " engine=" << engine << " stand=" << stand
                  << " legal=" << shape.legal << " quiet=" << shape.quiet
                  << " tactical=" << shape.tactical << " check=" << shape.checked;
        if (mismatches.size() > before) std::cout << " MISMATCH " << mismatches.back().kind
                                                   << " contract=" << mismatches.back().contract_score
                                                   << " listed=" << mismatches.back().listed;
        std::cout << '\n';
    }

    std::cout << "structured\n";
    int structured_seen = 0;
    for (int wk = 0; wk < 64; ++wk) {
        for (int bk = 0; bk < 64; ++bk) {
            if (wk == bk || king_adjacent(wk, bk)) continue;
            for (int pawn = 0; pawn < 8; ++pawn) {
                const int from = 6 * 8 + pawn; // white pawn on the seventh rank
                if (from == wk || from == bk) continue;
                std::array<char, 64> squares{};
                squares[static_cast<std::size_t>(wk)] = 'K';
                squares[static_cast<std::size_t>(bk)] = 'k';
                squares[static_cast<std::size_t>(from)] = 'P';
                forge::Board board;
                if (!board.set_fen(fen_from_squares(squares, 'w'))) continue;
                const Shape shape = classify(board);
                const bool interesting = shape.checked || shape.legal == 0 ||
                                         (shape.tactical && !shape.quiet);
                if (!interesting) continue;
                ++structured_seen;
                consider(searcher, board, mismatches, compared, contract_caps);
            }
            for (int knight = 0; knight < 64; ++knight) {
                if (knight == wk || knight == bk) continue;
                for (int victim = 0; victim < 64; ++victim) {
                    if (victim == wk || victim == bk || victim == knight) continue;
                    // Keep this exhaustive subset: rim knights only, pawn victims only.
                    if ((knight & 7) != 0 && (knight & 7) != 7 && (knight >> 3) != 0 && (knight >> 3) != 7) continue;
                    std::array<char, 64> squares{};
                    squares[static_cast<std::size_t>(wk)] = 'K';
                    squares[static_cast<std::size_t>(bk)] = 'k';
                    squares[static_cast<std::size_t>(knight)] = 'N';
                    squares[static_cast<std::size_t>(victim)] = 'p';
                    forge::Board board;
                    if (!board.set_fen(fen_from_squares(squares, 'w'))) continue;
                    const Shape shape = classify(board);
                    const bool interesting = shape.checked || shape.legal == 0 ||
                                             (shape.tactical && !shape.quiet) ||
                                             (shape.quiet && shape.tactical && ((knight * 17 + victim) % 23 == 0));
                    if (!interesting) continue;
                    ++structured_seen;
                    consider(searcher, board, mismatches, compared, contract_caps);
                }
            }
        }
    }
    std::cout << "structured_seen=" << structured_seen << " compared=" << compared
              << " mismatches=" << mismatches.size() << " caps=" << contract_caps << '\n';

    std::cout << "walk\n";
    int walk_seen = 0;
    for (int game = 0; game < 30; ++game) {
        forge::Board board;
        std::uint64_t random_state = 0x9e3779b97f4a7c15ULL + static_cast<std::uint64_t>(game) * 0x10001U;
        for (int ply = 0; ply < 24; ++ply) {
            const Shape shape = classify(board);
            const bool interesting = shape.checked || shape.legal == 0 ||
                                     (shape.tactical && !shape.quiet) || (ply % 4 == 0);
            if (interesting) {
                ++walk_seen;
                consider(searcher, board, mismatches, compared, contract_caps);
            }
            const auto moves = board.legal_moves();
            if (moves.empty()) break;
            random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
            forge::Undo undo;
            (void)board.make_move(moves[static_cast<std::size_t>(random_state % moves.size())], undo);
        }
    }
    std::cout << "walk_seen=" << walk_seen << " compared=" << compared
              << " mismatches=" << mismatches.size() << '\n';

    std::cout << "summary kind counts\n";
    std::array<std::pair<const char*, int>, 8> kinds{{
        {"forced-tactical-stand-pat", 0},
        {"pruned-tactical", 0},
        {"dropped-evasion", 0},
        {"inflated-evasion", 0},
        {"false-mate", 0},
        {"stalemate", 0},
        {"checkmate-score", 0},
        {"other", 0},
    }};
    for (const Mismatch& mismatch : mismatches) {
        bool known = false;
        for (auto& kind : kinds) {
            if (mismatch.kind == kind.first) {
                ++kind.second;
                known = true;
            }
        }
        if (!known) std::cout << "unclassified " << mismatch.kind << '\n';
    }
    for (const auto& kind : kinds) std::cout << kind.first << '=' << kind.second << '\n';

    std::cout << "examples\n";
    int shown = 0;
    for (const Mismatch& mismatch : mismatches) {
        if (shown >= 12) break;
        std::cout << mismatch.kind << " engine=" << mismatch.engine
                  << " contract=" << mismatch.contract_score
                  << " listed=" << mismatch.listed
                  << " stand=" << mismatch.stand_pat
                  << " legal=" << mismatch.shape.legal
                  << " tactical=" << mismatch.shape.tactical_count
                  << " quiet=" << mismatch.shape.quiet
                  << " check=" << mismatch.shape.checked
                  << " fen=" << mismatch.fen << '\n';
        ++shown;
    }

    if (!mismatches.empty()) {
        const Mismatch& sample = mismatches.front();
        forge::Board board;
        if (board.set_fen(sample.fen)) {
            std::cout << "windows for " << sample.fen << '\n';
            const int windows[][2] = {{-Infinity, Infinity}, {sample.contract_score, sample.contract_score + 1},
                                      {sample.stand_pat, sample.stand_pat + 1}, {-1, 0}, {0, 1}};
            for (const auto& window : windows) {
                const int alpha = window[0];
                const int beta = window[1];
                if (alpha >= beta) continue;
                const int got = engine_score(searcher, board, alpha, beta);
                std::uint64_t nodes = 0;
                const int expect = contract(board, alpha, beta, 0, nodes, 200000);
                std::cout << "  [" << alpha << ',' << beta << ") engine=" << got
                          << " contract=" << expect << '\n';
            }
            std::cout << "legal moves:";
            for (const forge::Move move : board.legal_moves()) {
                std::cout << ' ' << forge::Board::move_to_uci(move)
                          << (is_tactical(move) ? "*" : "");
            }
            std::cout << '\n';
        }
    }

    std::cout << "compared=" << compared << " rejected=" << rejected
              << " caps=" << contract_caps << " mismatches=" << mismatches.size() << '\n';
    return mismatches.empty() ? 0 : 1;
}
