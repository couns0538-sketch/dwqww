// In-process checks for the release engine. Nothing here is a UCI session:
// perft, make/unmake, classic NNUE incremental updates against a full refresh,
// mirrored evaluation, and mate/draw search. Positions that claim a mate are
// accepted only when the brute-force oracle in this file agrees.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstring>
#include <iostream>
#include <random>
#include <string>
#include <string_view>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static int eval(Worker& worker, const Board& board, SearchStack* ss) {
        return worker.static_evaluate(board, ss);
    }
    static void record(Worker& worker, SearchStack* ss, const Board& board, const Move& move) {
        worker.record_move(ss, board, move);
    }
    static void record_null(Worker& worker, SearchStack* ss) { worker.record_null_move(ss); }
};
} // namespace forge

namespace {

int g_checks = 0;
int g_failures = 0;

void expect(bool condition, const std::string& what) {
    ++g_checks;
    if (!condition) {
        ++g_failures;
        std::cout << "FAIL " << what << '\n';
    }
}

[[nodiscard]] bool contains_move(const forge::MoveList& moves, const forge::Move& move) {
    return std::any_of(moves.begin(), moves.end(), [&](const forge::Move& legal) { return legal == move; });
}

[[nodiscard]] std::string move_text(const forge::Move& move) {
    return move.is_none() ? "0000" : forge::Board::move_to_uci(move);
}

// Minimum plies for the side to move to force checkmate, or -1 if none within max_ply.
// max_ply is 1 (mate in one move) or 3 (mate in two moves). Wider searches are not used.
[[nodiscard]] int forced_mate_plies(forge::Board& board, int max_ply) {
    if (max_ply < 1) return -1;
    const forge::MoveList legal = board.legal_moves();
    if (legal.empty()) return -1;
    int best = -1;
    for (const forge::Move move : legal) {
        forge::Undo undo;
        (void)board.make_move(move, undo);
        int plies = -1;
        if (board.in_check() && !board.has_legal_move()) {
            plies = 1;
        } else if (board.has_legal_move() && max_ply >= 3) {
            const forge::MoveList replies = board.legal_moves();
            int slowest = 0;
            bool every = true;
            for (const forge::Move reply : replies) {
                forge::Undo reply_undo;
                (void)board.make_move(reply, reply_undo);
                const int sub = forced_mate_plies(board, max_ply - 2);
                (void)board.unmake_move(reply, reply_undo);
                if (sub < 0) {
                    every = false;
                    break;
                }
                slowest = std::max(slowest, sub);
            }
            if (every && !replies.empty()) plies = slowest + 2;
        }
        (void)board.unmake_move(move, undo);
        if (plies > 0 && (best < 0 || plies < best)) best = plies;
        if (best == 1) return 1;
    }
    return best;
}

[[nodiscard]] bool move_forces_mate(forge::Board board, const forge::Move& move, int plies) {
    forge::Undo undo;
    (void)board.make_move(move, undo);
    if (plies == 1) return board.in_check() && !board.has_legal_move();
    if (!board.has_legal_move()) return false;
    const forge::MoveList replies = board.legal_moves();
    for (const forge::Move reply : replies) {
        forge::Undo reply_undo;
        (void)board.make_move(reply, reply_undo);
        const int sub = forced_mate_plies(board, plies - 2);
        (void)board.unmake_move(reply, reply_undo);
        if (sub < 0 || sub + 2 != plies) return false;
    }
    return !replies.empty();
}

[[nodiscard]] std::vector<int> feature_list(forge::Color perspective, const forge::Board& board) {
    std::vector<int> features;
    for (int square = 0; square < 64; ++square) {
        const forge::Piece piece = board.piece_at(square);
        if (piece == forge::Empty) continue;
        features.push_back(forge::nnue::feature_index(perspective, piece, square));
    }
    std::sort(features.begin(), features.end());
    return features;
}

// Color-swap plus a vertical mirror. The side that was to move is the same army,
// so a symmetric evaluation of the side to move must be unchanged.
[[nodiscard]] std::string mirror_fen(const forge::Board& board) {
    static constexpr char kLetters[] = " PNBRQKpnbrqk";
    std::string fen;
    for (int rank = 7; rank >= 0; --rank) {
        if (rank != 7) fen += '/';
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const forge::Piece piece = board.piece_at(forge::make_square(file, 7 - rank));
            if (piece == forge::Empty) {
                ++empty;
                continue;
            }
            if (empty != 0) {
                fen += static_cast<char>('0' + empty);
                empty = 0;
            }
            const char letter = kLetters[static_cast<int>(piece)];
            fen += forge::color_of(piece) == forge::White
                ? static_cast<char>(std::tolower(static_cast<unsigned char>(letter)))
                : static_cast<char>(std::toupper(static_cast<unsigned char>(letter)));
        }
        if (empty != 0) fen += static_cast<char>('0' + empty);
    }
    fen += board.side_to_move() == forge::White ? " b " : " w ";
    const unsigned rights = board.castling_rights();
    unsigned mirrored = 0;
    if ((rights & 1U) != 0U) mirrored |= 4U;
    if ((rights & 2U) != 0U) mirrored |= 8U;
    if ((rights & 4U) != 0U) mirrored |= 1U;
    if ((rights & 8U) != 0U) mirrored |= 2U;
    std::string castle;
    if ((mirrored & 1U) != 0U) castle += 'K';
    if ((mirrored & 2U) != 0U) castle += 'Q';
    if ((mirrored & 4U) != 0U) castle += 'k';
    if ((mirrored & 8U) != 0U) castle += 'q';
    if (castle.empty()) castle = "-";
    fen += castle;
    fen += ' ';
    if (board.ep_square() < 0) {
        fen += '-';
    } else {
        const int square = forge::flip_square(board.ep_square());
        fen += static_cast<char>('a' + forge::file_of(square));
        fen += static_cast<char>('1' + forge::rank_of(square));
    }
    fen += ' ';
    fen += std::to_string(board.halfmove_clock());
    fen += " 1";
    return fen;
}

[[nodiscard]] float max_abs_diff(const forge::nnue::Accumulator& left, const forge::nnue::Accumulator& right) {
    float worst = 0.0F;
    for (int color = 0; color < 2; ++color) {
        for (int hidden = 0; hidden < forge::nnue::HiddenSize; ++hidden) {
            const float delta = std::fabs(left.values[static_cast<std::size_t>(color)][static_cast<std::size_t>(hidden)] -
                                           right.values[static_cast<std::size_t>(color)][static_cast<std::size_t>(hidden)]);
            worst = std::max(worst, delta);
        }
    }
    return worst;
}

struct NnueStats {
    int plies = 0;
    int king_moves = 0;
    int castles = 0;
    int en_passants = 0;
    int promotions = 0;
    int captures = 0;
    int quiets = 0;
    int nulls = 0;
    int dirty[5] = {};
    int large_gaps = 0;
    int eval_gaps = 0;
    int worker_gaps = 0;
    float max_gap = 0.0F;
    int max_worker_cp = 0;
    std::string first_large;
};

void note_move(NnueStats& stats, const forge::Board& board, const forge::Move& move) {
    const forge::Piece moved = board.piece_at(move.from);
    if (forge::piece_type(moved) == forge::King) ++stats.king_moves;
    if (move.is_castle()) ++stats.castles;
    if ((move.flags & forge::EnPassant) != 0U) ++stats.en_passants;
    if (move.is_promotion()) ++stats.promotions;
    if (move.is_capture()) ++stats.captures;
    else ++stats.quiets;
}

// One ply of the classic (king-independent) network: incremental update versus a full refresh.
void check_incremental(forge::Board& board, const forge::nnue::Accumulator& parent, const forge::Move& move,
                       forge::Searcher& searcher, std::vector<forge::SearchStack>& stack, int ply, NnueStats& stats) {
    const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
    expect(dirty.count >= 0 && dirty.count <= 4, "dirty count is 0..4");
    if (dirty.count >= 0 && dirty.count <= 4) ++stats.dirty[dirty.count];
    note_move(stats, board, move);
    forge::nnue::Accumulator child;
    forge::nnue::update(parent, child, dirty);
    forge::Undo undo;
    (void)board.make_move(move, undo);
    forge::nnue::Accumulator fresh;
    forge::nnue::refresh(board, fresh);
    const float gap = max_abs_diff(child, fresh);
    stats.max_gap = std::max(stats.max_gap, gap);
    const int network_child = forge::nnue::evaluate(board, child);
    const int network_fresh = forge::nnue::evaluate(board, fresh);
    if (gap > 0.01F) {
        ++stats.large_gaps;
        if (stats.first_large.empty()) {
            stats.first_large = board.fen() + " move " + move_text(move) + " gap " + std::to_string(gap);
        }
    }
    if (network_child != network_fresh) ++stats.eval_gaps;
    ++stats.plies;

    if (ply + 1 < static_cast<int>(stack.size())) {
        forge::SearcherTestProbe::record(searcher.main_worker(), &stack[static_cast<std::size_t>(ply)], board, move);
        // record_move reads the board before the move. The move is already made, so compare the
        // worker only when the caller recorded first. This helper is used after the move for the
        // accumulator check; the worker chain is driven by check_chain.
    }
    (void)board.unmake_move(move, undo);
    (void)searcher;
    (void)stack;
    (void)ply;
}

// static_evaluate at ply 0 still reads the previous stack entry. The search keeps
// a sentinel there; these tests do the same, otherwise the "fresh" comparison
// updates from whatever happens to sit in memory before the stack object.
[[nodiscard]] int fresh_worker_eval(forge::Searcher& searcher, const forge::Board& board) {
    forge::SearchStack pair[2];
    pair[1].ply = 0;
    return forge::SearcherTestProbe::eval(searcher.main_worker(), board, &pair[1]);
}

void check_chain(forge::Board board, const std::vector<std::string>& moves, forge::Searcher& searcher, NnueStats& stats) {
    // stack[0] is the sentinel. The root entry is stack[1].
    std::vector<forge::SearchStack> stack(moves.size() + 3);
    forge::SearchStack* root = &stack[1];
    root->ply = 0;
    const int root_eval = forge::SearcherTestProbe::eval(searcher.main_worker(), board, root);
    expect(root_eval == fresh_worker_eval(searcher, board),
           "root worker eval matches a second refresh on " + board.fen());

    forge::nnue::Accumulator running = root->accumulator;
    for (std::size_t i = 0; i < moves.size(); ++i) {
        const auto parsed = board.parse_uci(moves[i]);
        expect(parsed.has_value(), "chain move " + moves[i] + " from " + board.fen());
        if (!parsed) return;
        const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, *parsed);
        if (dirty.count >= 0 && dirty.count <= 4) ++stats.dirty[dirty.count];
        note_move(stats, board, *parsed);
        forge::SearcherTestProbe::record(searcher.main_worker(), &stack[i + 1], board, *parsed);
        forge::nnue::Accumulator next;
        forge::nnue::update(running, next, dirty);
        forge::Undo undo;
        expect(board.make_move(*parsed, undo), "make " + moves[i]);
        forge::nnue::Accumulator refreshed;
        forge::nnue::refresh(board, refreshed);
        const float gap = max_abs_diff(next, refreshed);
        stats.max_gap = std::max(stats.max_gap, gap);
        if (gap > 0.01F) {
            ++stats.large_gaps;
            if (stats.first_large.empty()) stats.first_large = board.fen() + " after " + moves[i];
        }
        if (forge::nnue::evaluate(board, next) != forge::nnue::evaluate(board, refreshed)) ++stats.eval_gaps;
        stack[i + 2].ply = static_cast<int>(i + 1);
        const int chained = forge::SearcherTestProbe::eval(searcher.main_worker(), board, &stack[i + 2]);
        const int full = fresh_worker_eval(searcher, board);
        const int cp = std::abs(chained - full);
        stats.max_worker_cp = std::max(stats.max_worker_cp, cp);
        if (cp != 0) ++stats.worker_gaps;
        running = next;
        ++stats.plies;
        (void)undo;
    }
}

void check_all_moves(const std::string& fen, forge::Searcher& searcher, NnueStats& stats) {
    forge::Board board;
    expect(board.set_fen(fen), "set fen " + fen);
    forge::nnue::Accumulator parent;
    forge::nnue::refresh(board, parent);
    const forge::MoveList legal = board.legal_moves();
    std::vector<forge::SearchStack> unused(2);
    for (const forge::Move move : legal) {
        check_incremental(board, parent, move, searcher, unused, 0, stats);
    }
}

void check_mirror(const forge::Board& board, const std::string& tag, int& compared, int& skipped) {
    const std::string fen = mirror_fen(board);
    forge::Board mirrored;
    std::string error;
    if (!mirrored.set_fen(fen, &error)) {
        ++skipped;
        return;
    }
    ++compared;
    const int hce = forge::Evaluator::evaluate_uncached(board);
    const int hce_mirror = forge::Evaluator::evaluate_uncached(mirrored);
    expect(hce == hce_mirror, "HCE mirror " + tag + " " + std::to_string(hce) + " vs " + std::to_string(hce_mirror) +
                                  " fen " + board.fen() + " mirror " + fen);
    expect(feature_list(forge::White, board) == feature_list(forge::Black, mirrored),
           "white features match mirrored black features " + tag);
    expect(feature_list(forge::Black, board) == feature_list(forge::White, mirrored),
           "black features match mirrored white features " + tag);
    forge::nnue::Accumulator left;
    forge::nnue::Accumulator right;
    forge::nnue::refresh(board, left);
    forge::nnue::refresh(mirrored, right);
    const int network = forge::nnue::evaluate(board, left);
    const int network_mirror = forge::nnue::evaluate(mirrored, right);
    expect(network == network_mirror, "NNUE mirror " + tag + " " + std::to_string(network) + " vs " +
                                           std::to_string(network_mirror) + " fen " + board.fen());
}

void test_perft() {
    struct Case {
        const char* name;
        const char* fen;
        int depth;
        std::uint64_t nodes;
        const char* source;
    };
    // Counts from https://www.chessprogramming.org/Perft_Results (checked 2026-11-13 against that table).
    const Case cases[] = {
        {"startpos", forge::Board::StandardStartFen.data(), 5, 4865609ULL, "CPW perft startpos"},
        {"kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 4, 4085603ULL, "CPW perft position 2"},
        {"cpw3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5, 674624ULL, "CPW perft position 3"},
        {"cpw4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 4, 422333ULL, "CPW perft position 4"},
        {"cpw5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 3, 62379ULL, "CPW perft position 5"},
        {"cpw6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 3, 89890ULL, "CPW perft position 6"},
    };
    for (const Case& item : cases) {
        forge::Board board;
        expect(board.set_fen(item.fen), std::string("perft fen ") + item.name);
        const auto started = std::chrono::steady_clock::now();
        const std::uint64_t nodes = board.perft(item.depth);
        const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - started).count();
        expect(nodes == item.nodes, std::string(item.name) + " perft " + std::to_string(item.depth) + " got " +
                                         std::to_string(nodes) + " expected " + std::to_string(item.nodes) + " (" + item.source + ")");
        std::cout << "PERFT " << item.name << " d" << item.depth << " nodes " << nodes << " ms " << ms << '\n';
    }
}

void test_make_unmake() {
    forge::Board board;
    expect(board.set_fen(forge::Board::StandardStartFen), "startpos");
    std::mt19937 rng(20261113);
    std::vector<forge::Move> played;
    std::vector<forge::Undo> undos;
    std::vector<std::string> fens;
    std::vector<std::uint64_t> keys;
    for (int ply = 0; ply < 80; ++ply) {
        fens.push_back(board.fen());
        keys.push_back(board.key());
        forge::Board rebuilt;
        expect(rebuilt.set_fen(board.fen()), "rebuild fen");
        expect(rebuilt.key() == board.key(), "zobrist matches a fresh fen at ply " + std::to_string(ply));
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty()) break;
        std::uniform_int_distribution<int> pick(0, static_cast<int>(legal.size()) - 1);
        const forge::Move move = legal.begin()[pick(rng)];
        played.push_back(move);
        undos.emplace_back();
        expect(board.make_move(move, undos.back()), "make random");
    }
    for (int i = static_cast<int>(played.size()) - 1; i >= 0; --i) {
        (void)board.unmake_move(played[static_cast<std::size_t>(i)], undos[static_cast<std::size_t>(i)]);
        expect(board.fen() == fens[static_cast<std::size_t>(i)], "unmake restores fen");
        expect(board.key() == keys[static_cast<std::size_t>(i)], "unmake restores zobrist");
    }
}

void test_parse_uci() {
    forge::Board board;
    expect(board.set_fen("8/P7/8/8/8/8/8/K6k w - - 0 1"), "promotion fen");
    const auto upper = board.parse_uci("a7a8Q");
    const auto lower = board.parse_uci("a7a8q");
    const auto squares = board.parse_uci("A7A8q");
    expect(upper.has_value() && lower.has_value() && squares.has_value(), "uppercase promotion and squares parse");
    if (upper && lower) expect(*upper == *lower && upper->promotion == forge::Queen, "promotion piece is a queen");
    expect(!board.parse_uci("a7a8k").has_value(), "king promotion is rejected");
    expect(!board.parse_uci("a7a9").has_value(), "off-board move is rejected");
    forge::Board start;
    expect(start.set_fen(forge::Board::StandardStartFen), "start");
    expect(start.parse_uci("E2E4").has_value(), "E2E4 parses");
    expect(!start.parse_uci("e2e5").has_value(), "illegal e2e5 is rejected");
}

void test_nnue(forge::Searcher& searcher) {
    NnueStats stats;
    check_all_moves(std::string(forge::Board::StandardStartFen), searcher, stats);
    check_all_moves("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", searcher, stats);
    check_all_moves("rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2", searcher, stats);
    check_all_moves("8/P7/8/8/8/8/8/K6k w - - 0 1", searcher, stats);
    check_all_moves("n7/1P6/8/8/8/8/8/K6k w - - 0 1", searcher, stats);
    check_all_moves("8/8/8/3k4/8/8/8/3K4 w - - 0 1", searcher, stats);
    check_all_moves("8/8/8/3k4/8/8/8/3K4 b - - 0 1", searcher, stats);

    {
        forge::Board board;
        expect(board.set_fen(forge::Board::StandardStartFen), "chain start");
        check_chain(board, {"e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "e1g1", "f8e7", "d2d3", "e8g8"}, searcher, stats);
    }

    forge::Board random_board;
    expect(random_board.set_fen(forge::Board::StandardStartFen), "random start");
    std::mt19937 rng(20261113);
    std::vector<std::string> random_moves;
    for (int ply = 0; ply < 40 && random_board.has_legal_move(); ++ply) {
        const forge::MoveList legal = random_board.legal_moves();
        std::uniform_int_distribution<int> pick(0, static_cast<int>(legal.size()) - 1);
        const forge::Move move = legal.begin()[pick(rng)];
        random_moves.push_back(forge::Board::move_to_uci(move));
        forge::Undo undo;
        (void)random_board.make_move(move, undo);
    }
    forge::Board chain_start;
    expect(chain_start.set_fen(forge::Board::StandardStartFen), "chain restart");
    check_chain(chain_start, random_moves, searcher, stats);

    // Null move: no piece changes. The accumulator must stay on the refreshed value.
    {
        forge::Board board;
        expect(board.set_fen(forge::Board::StandardStartFen), "null start");
        expect(!board.in_check(), "startpos is not in check");
        std::vector<forge::SearchStack> stack(3);
        stack[1].ply = 0;
        stack[2].ply = 1;
        (void)forge::SearcherTestProbe::eval(searcher.main_worker(), board, &stack[1]);
        forge::SearcherTestProbe::record_null(searcher.main_worker(), &stack[1]);
        forge::nnue::DirtyPieces empty;
        forge::nnue::Accumulator child;
        forge::nnue::update(stack[1].accumulator, child, empty);
        forge::NullUndo undo;
        board.make_null_move(undo);
        forge::nnue::Accumulator fresh;
        forge::nnue::refresh(board, fresh);
        const float gap = max_abs_diff(child, fresh);
        stats.max_gap = std::max(stats.max_gap, gap);
        if (gap > 0.01F) ++stats.large_gaps;
        if (forge::nnue::evaluate(board, child) != forge::nnue::evaluate(board, fresh)) ++stats.eval_gaps;
        const int chained = forge::SearcherTestProbe::eval(searcher.main_worker(), board, &stack[2]);
        const int full = fresh_worker_eval(searcher, board);
        if (chained != full) ++stats.worker_gaps;
        stats.max_worker_cp = std::max(stats.max_worker_cp, std::abs(chained - full));
        ++stats.nulls;
        ++stats.dirty[0];
        ++stats.plies;
        board.unmake_null_move(undo);
    }

    expect(stats.king_moves > 0, "NNUE sample includes a king move");
    expect(stats.castles > 0, "NNUE sample includes castling");
    expect(stats.en_passants > 0, "NNUE sample includes en passant");
    expect(stats.promotions > 0, "NNUE sample includes a promotion");
    expect(stats.captures > 0 && stats.quiets > 0, "NNUE sample includes captures and quiet moves");
    expect(stats.nulls > 0, "NNUE sample includes a null move");
    expect(stats.dirty[2] > 0 && stats.dirty[3] > 0 && stats.dirty[4] > 0, "quiet, capture and castling dirty counts were hit");
    expect(stats.large_gaps == 0, "no incremental accumulator differs from refresh by more than 0.01 (" + stats.first_large + ")");
    expect(stats.eval_gaps == 0, "incremental and refreshed NNUE evaluations match (" + std::to_string(stats.eval_gaps) + " gaps)");
    expect(stats.worker_gaps == 0, "worker incremental eval matches a fresh refresh (" + std::to_string(stats.worker_gaps) +
                                        " gaps, max " + std::to_string(stats.max_worker_cp) + " cp)");
    std::cout << "NNUE plies " << stats.plies << " king " << stats.king_moves << " castle " << stats.castles
              << " ep " << stats.en_passants << " promo " << stats.promotions << " dirty2 " << stats.dirty[2]
              << " dirty3 " << stats.dirty[3] << " dirty4 " << stats.dirty[4] << " max_gap " << stats.max_gap
              << " eval_gaps " << stats.eval_gaps << " worker_gaps " << stats.worker_gaps << '\n';
}

void test_mirror() {
    int compared = 0;
    int skipped = 0;
    forge::Board start;
    expect(start.set_fen(forge::Board::StandardStartFen), "mirror start");
    const std::string once = mirror_fen(start);
    forge::Board mid;
    expect(mid.set_fen(once), "mirror of startpos is legal: " + once);
    const std::string twice = mirror_fen(mid);
    forge::Board back;
    expect(back.set_fen(twice), "mirror twice is legal");
    expect(back.fen().substr(0, back.fen().find(' ')) == start.fen().substr(0, start.fen().find(' ')),
           "mirroring twice restores the startpos placement");
    check_mirror(start, "startpos", compared, skipped);

    const char* fens[] = {
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "8/8/8/3k4/8/8/4P3/3K4 w - - 0 1",
        "8/8/8/3k4/8/8/4P3/3K4 b - - 0 1",
        "6k1/8/5QK1/8/8/8/8/8 w - - 0 1",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        "8/8/8/8/8/8/8/K6k w - - 0 1",
        "8/8/8/8/8/8/8/K6k b - - 0 1",
    };
    for (const char* fen : fens) {
        forge::Board board;
        expect(board.set_fen(fen), std::string("mirror fen ") + fen);
        check_mirror(board, fen, compared, skipped);
    }

    forge::Board walking;
    expect(walking.set_fen(forge::Board::StandardStartFen), "mirror walk");
    std::mt19937 rng(7);
    for (int ply = 0; ply < 24 && walking.has_legal_move(); ++ply) {
        check_mirror(walking, "walk " + std::to_string(ply), compared, skipped);
        const forge::MoveList legal = walking.legal_moves();
        std::uniform_int_distribution<int> pick(0, static_cast<int>(legal.size()) - 1);
        forge::Undo undo;
        (void)walking.make_move(legal.begin()[pick(rng)], undo);
    }
    expect(compared >= 8, "compared several mirrored positions (" + std::to_string(compared) + ")");
    std::cout << "MIRROR compared " << compared << " skipped " << skipped << '\n';
}

void test_endgames_and_tactics(forge::Searcher& searcher) {
    struct MateCase {
        const char* fen;
        int max_ply;
        const char* source;
    };
    const MateCase mates[] = {
        {"6k1/8/5QK1/8/8/8/8/8 w - - 0 1", 1, "constructed Qg6/Kg6 vs Kg8; oracle must agree"},
        {"6k1/8/5QK1/8/8/8/8/8 w - - 99 40", 1, "same mate with halfmove 99, before the 50-move draw"},
        {"7k/5P2/6K1/8/8/8/8/8 w - - 0 1", 1, "constructed promotion on f7, Kg6 vs Kh8"},
        {"k7/8/1K6/8/8/8/8/7R w - - 0 1", 1, "constructed Rh8 mate, Kb6 vs Ka8"},
    };
    for (const MateCase& item : mates) {
        forge::Board board;
        expect(board.set_fen(item.fen), std::string("mate fen ") + item.fen);
        forge::Board oracle_board = board;
        const int plies = forced_mate_plies(oracle_board, item.max_ply);
        expect(plies == item.max_ply, std::string(item.source) + " oracle plies " + std::to_string(plies));
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = item.max_ply;
        const forge::SearchInfo info = searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
        const bool winning = !info.best_move.is_none() && move_forces_mate(board, info.best_move, item.max_ply);
        expect(winning, std::string("search plays a fastest mate, got ") + move_text(info.best_move) + " score " +
                             std::to_string(info.score) + " in " + item.fen);
        expect(info.score > 30000, "mate score is positive in " + std::string(item.fen) + " score " + std::to_string(info.score));
        std::cout << "TACTIC mate ply " << plies << " move " << move_text(info.best_move) << " score " << info.score
                  << " source " << item.source << '\n';
    }

    // Halfmove 100 is already a draw, including when a mating move exists.
    {
        forge::Board board;
        const char* fen = "6k1/8/5QK1/8/8/8/8/8 w - - 100 40";
        expect(board.set_fen(fen), "50-move fen");
        expect(forced_mate_plies(board, 1) == 1, "the mating move still exists at halfmove 100");
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = 2;
        const forge::SearchInfo info = searcher.search(board, limits, false);
        expect(info.score == 0, "halfmove 100 is a draw even with a mate on the board, score " + std::to_string(info.score));
        expect(contains_move(board.legal_moves(), info.best_move), "draw still returns a legal move");
        std::cout << "ENDGAME fifty-move-with-mate score " << info.score << " move " << move_text(info.best_move) << '\n';
    }

    {
        forge::Board board;
        expect(board.set_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"), "stalemate fen");
        expect(board.legal_moves().empty() && !board.in_check(), "stalemate has no move and is not check");
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = 2;
        const forge::SearchInfo info = searcher.search(board, limits, false);
        expect(info.score == 0 && info.best_move.is_none(), "stalemate score 0 bestmove none, score " + std::to_string(info.score));
        std::cout << "ENDGAME stalemate score " << info.score << " move " << move_text(info.best_move) << '\n';
    }

    {
        forge::Board board;
        expect(board.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 100 40"), "mate beats 50-move");
        expect(board.in_check() && board.legal_moves().empty(), "black is checkmated");
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = 1;
        const forge::SearchInfo info = searcher.search(board, limits, false);
        expect(info.score < -30000, "checkmate outranks the 50-move rule, score " + std::to_string(info.score));
        expect(info.best_move.is_none(), "checkmate has no move");
        std::cout << "ENDGAME mate-on-100 score " << info.score << '\n';
    }

    struct DrawCase {
        const char* fen;
        bool insufficient;
        const char* name;
    };
    const DrawCase draws[] = {
        {"8/8/8/8/8/8/8/4K2k w - - 0 1", true, "KvK"},
        {"8/8/8/8/8/8/8/B3K2k w - - 0 1", true, "KBvK"},
        {"8/8/8/8/8/8/8/N3K2k w - - 0 1", true, "KNvK"},
        {"8/8/8/8/8/8/8/NN2K2k w - - 0 1", false, "KNNvK"},
        {"8/8/8/2b5/8/8/8/2B1K2k w - - 0 1", true, "same-color bishops"},
        {"8/8/8/3b4/8/8/8/2B1K2k w - - 0 1", false, "opposite-color bishops"},
    };
    for (const DrawCase& item : draws) {
        forge::Board board;
        expect(board.set_fen(item.fen), item.name);
        expect(board.is_insufficient_material() == item.insufficient,
               std::string(item.name) + " insufficient flag");
        if (item.insufficient) {
            searcher.clear();
            forge::SearchLimits limits;
            limits.depth = 3;
            const forge::SearchInfo info = searcher.search(board, limits, false);
            expect(info.score == 0, std::string(item.name) + " search score 0, got " + std::to_string(info.score));
            std::cout << "ENDGAME " << item.name << " score " << info.score << " move " << move_text(info.best_move) << '\n';
        }
    }

    {
        forge::Board board;
        expect(board.set_fen(forge::Board::StandardStartFen), "repetition start");
        const char* moves[] = {"g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"};
        for (const char* text : moves) {
            const auto move = board.parse_uci(text);
            expect(move.has_value(), std::string("repetition move ") + text);
            if (!move) break;
            forge::Undo undo;
            (void)board.make_move(*move, undo);
        }
        expect(board.is_repetition(), "threefold after the knight shuttle");
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = 3;
        const forge::SearchInfo info = searcher.search(board, limits, false);
        expect(info.score == 0, "threefold search score 0, got " + std::to_string(info.score));
        expect(contains_move(board.legal_moves(), info.best_move), "threefold still returns a legal move");
        std::cout << "ENDGAME repetition score " << info.score << " move " << move_text(info.best_move) << '\n';
    }

    {
        forge::Board board;
        expect(board.set_fen(forge::Board::StandardStartFen), "searchmoves start");
        forge::SearchLimits limits;
        limits.depth = 2;
        limits.search_moves_specified = true;
        limits.search_moves.push_back(forge::Move::none());
        searcher.clear();
        const forge::SearchInfo info = searcher.search(board, limits, false);
        expect(info.restricted_root_empty, "empty searchmoves is flagged");
        expect(contains_move(board.legal_moves(), info.best_move), "empty searchmoves returns a legal move " + move_text(info.best_move));
        const auto only = board.parse_uci("a2a4");
        expect(only.has_value(), "a2a4");
        limits.search_moves = {*only};
        searcher.clear();
        const forge::SearchInfo restricted = searcher.search(board, limits, false);
        expect(!restricted.restricted_root_empty && restricted.best_move == *only, "searchmoves a2a4 is kept");
    }

    {
        // Pawn ending recorded for inspection. No tablebase is linked into this build.
        forge::Board board;
        expect(board.set_fen("8/8/8/8/8/4k3/4P3/4K3 w - - 0 1"), "kpk");
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = 8;
        const forge::SearchInfo info = searcher.search(board, limits, false);
        expect(contains_move(board.legal_moves(), info.best_move), "kpk move is legal");
        std::cout << "ENDGAME kpk depth 8 score " << info.score << " move " << move_text(info.best_move)
                  << " nodes " << info.nodes << " (no tablebase in this tree)\n";
    }
}

void test_timing() {
    forge::Board board;
    expect(board.set_fen(forge::Board::StandardStartFen), "time start");
    volatile std::size_t sink = 0;
    const auto gen_started = std::chrono::steady_clock::now();
    for (int i = 0; i < 200000; ++i) {
        const forge::MoveList legal = board.legal_moves();
        sink += legal.size();
    }
    const auto gen_ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - gen_started).count();

    const forge::MoveList legal = board.legal_moves();
    const auto make_started = std::chrono::steady_clock::now();
    for (int i = 0; i < 50000; ++i) {
        for (const forge::Move move : legal) {
            forge::Undo undo;
            (void)board.make_move(move, undo);
            (void)board.unmake_move(move, undo);
        }
    }
    const auto make_ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - make_started).count();

    forge::nnue::Accumulator acc;
    forge::nnue::refresh(board, acc);
    const auto nnue_started = std::chrono::steady_clock::now();
    for (int i = 0; i < 20000; ++i) {
        for (const forge::Move move : legal) {
            const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
            forge::nnue::Accumulator child;
            forge::nnue::update(acc, child, dirty);
            sink += static_cast<std::size_t>(child.values[0][0]);
        }
    }
    const auto nnue_ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - nnue_started).count();
    std::cout << "TIME legal_gen_200k_ms " << gen_ms << " make_unmake_50k_ms " << make_ms
              << " nnue_update_ms " << nnue_ms << " sink " << sink << '\n';
}

} // namespace

int main() {
    std::cout << "engine_checks nnue " << (forge::nnue::available() ? "on" : "off")
              << " residual " << (forge::nnue::residual() ? "on" : "off") << '\n';
    test_perft();
    test_make_unmake();
    test_parse_uci();
    forge::Searcher searcher(16, 1);
    test_nnue(searcher);
    test_mirror();
    test_endgames_and_tactics(searcher);
    test_timing();
    std::cout << "engine_checks " << g_checks << " checks, " << g_failures << " failures\n";
    return g_failures == 0 ? 0 : 1;
}
