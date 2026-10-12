#include "forge/board.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

namespace forge {

struct SearcherTestProbe {
    static int quiescence(Searcher& searcher, Board& board, int ply = 0, bool null_branch = false) {
        return searcher.quiescence(board, ply, -32000, 32000, null_branch);
    }

    static int quiescence_window(Searcher& searcher, Board& board, int alpha, int beta,
                                 int ply = 0, bool null_branch = false) {
        return searcher.quiescence(board, ply, alpha, beta, null_branch);
    }

    static int alpha_beta(Searcher& searcher, Board& board, int depth, int alpha, int beta,
                          int ply = 0) {
        return searcher.alpha_beta(board, depth, ply, alpha, beta);
    }

    static int alpha_beta_without_null(Searcher& searcher, Board& board, int depth,
                                       int alpha, int beta, int ply = 1) {
        return searcher.alpha_beta(board, depth, ply, alpha, beta, false, false);
    }
    static std::uint64_t null_tries(const Searcher& searcher) { return searcher.null_tries_; }
    static std::uint64_t null_cutoffs(const Searcher& searcher) { return searcher.null_cutoffs_; }
    static std::uint64_t reverse_futility_cutoffs(const Searcher& searcher) {
        return searcher.reverse_futility_cutoffs_;
    }
    static std::uint64_t nodes(const Searcher& searcher) { return searcher.nodes_; }
    static void reset_nodes(Searcher& searcher) { searcher.nodes_ = 0; searcher.aborted_ = false; }
    static std::uint64_t time_limit_ms(const Searcher& searcher) { return searcher.time_limit_ms_; }
    static std::uint64_t soft_limit_ms(const Searcher& searcher) { return searcher.soft_limit_ms_; }
    static bool node_limit_specified(const Searcher& searcher) { return searcher.node_limit_specified_; }
    static std::uint64_t time_check_mask(const Searcher& searcher) { return searcher.time_check_mask_; }
    static std::size_t occupied_tt(const Searcher& searcher) {
        return static_cast<std::size_t>(std::count_if(
            searcher.table_.begin(), searcher.table_.end(),
            [](const Searcher::TTEntry& entry) { return Searcher::tt_depth(entry) >= 0; }));
    }
    static bool has_tt_entry(const Searcher& searcher, const Board& board) {
        const std::uint64_t key = Searcher::tt_key(board);
        const Searcher::TTEntry& entry = searcher.table_[searcher.tt_index(key)];
        return entry.key == key && Searcher::tt_depth(entry) >= 0;
    }
    static std::array<std::uint64_t, 6> root_tt_state(const Searcher& searcher, const Board& board) {
        const Searcher::TTEntry& entry = searcher.table_[searcher.tt_index(Searcher::tt_key(board))];
        return {entry.key, entry.move.from, entry.move.to, entry.move.promotion,
                static_cast<std::uint64_t>(static_cast<int>(entry.score) + 32768), entry.meta};
    }
};

} // namespace forge

namespace {

int failures = 0;

void check(bool condition, std::string_view message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        ++failures;
    }
}

void check_perft(std::string_view fen, int depth, std::uint64_t expected, std::string_view label) {
    forge::Board board;
    check(board.set_fen(fen), "parse perft FEN");
    const auto actual = board.perft(depth);
    if (actual != expected) {
        std::cerr << "FAIL: " << label << " expected " << expected << " got " << actual << '\n';
        ++failures;
    }
}

void play(forge::Board& board, std::string_view text) {
    const auto move = board.parse_uci(text);
    check(move.has_value(), "move should parse as legal");
    if (move.has_value()) {
        forge::Undo undo;
        (void)board.make_move(*move, undo);
    }
}

void check_piece_bitboards(const forge::Board& board, std::string_view label) {
    std::array<std::uint64_t, 13> rebuilt{};
    for (int square = 0; square < 64; ++square) {
        const forge::Piece piece = board.piece_at(square);
        if (piece != forge::Empty) rebuilt[static_cast<std::size_t>(piece)] |= 1ULL << square;
    }
    for (int piece = forge::WP; piece <= forge::BK; ++piece) {
        if (board.pieces(static_cast<forge::Piece>(piece)) != rebuilt[static_cast<std::size_t>(piece)]) {
            std::cerr << "FAIL: " << label << " piece bitboard mismatch for " << piece << '\n';
            ++failures;
        }
    }
}


void check_occupancy(const forge::Board& board, std::string_view label) {
    const std::uint64_t white = board.pieces(forge::WP) | board.pieces(forge::WN) |
                                board.pieces(forge::WB) | board.pieces(forge::WR) |
                                board.pieces(forge::WQ) | board.pieces(forge::WK);
    const std::uint64_t black = board.pieces(forge::BP) | board.pieces(forge::BN) |
                                board.pieces(forge::BB) | board.pieces(forge::BR) |
                                board.pieces(forge::BQ) | board.pieces(forge::BK);
    if (board.occupied(forge::White) != white || board.occupied(forge::Black) != black) {
        std::cerr << "FAIL: " << label << " occupancy mismatch\n";
        ++failures;
    }
}

void check_tt_rule50_context() {
    constexpr std::string_view normal_fen = "7k/8/8/8/8/8/8/KR6 w - - 0 1";
    constexpr std::string_view clock98_fen = "7k/8/8/8/8/8/8/KR6 w - - 98 1";
    constexpr std::string_view clock99_fen = "7k/8/8/8/8/8/8/KR6 w - - 99 1";
    constexpr std::string_view clock100_fen = "7k/8/8/8/8/8/8/KR6 w - - 100 1";

    forge::Board normal, clock98, clock99, clock100;
    check(normal.set_fen(normal_fen), "TT rule-50 normal FEN parses");
    check(clock98.set_fen(clock98_fen), "TT rule-50 clock-98 FEN parses");
    check(clock99.set_fen(clock99_fen), "TT rule-50 clock-99 FEN parses");
    check(clock100.set_fen(clock100_fen), "TT rule-50 clock-100 FEN parses");

    forge::SearchLimits depth2; depth2.depth = 2;
    forge::SearchLimits depth4; depth4.depth = 4;
    forge::Searcher tt_searcher(4);

    tt_searcher.clear_hash();
    check(tt_searcher.search(clock98, depth2).score == 0, "cold clock-98 search is a rule-50 draw");

    tt_searcher.clear_hash();
    check(tt_searcher.search(normal, depth4).score > 0, "ordinary rook ending is positive before rule-50 boundary");
    check(tt_searcher.search(clock98, depth2).score == 0, "clock-98 ignores incompatible warmed TT scores");

    tt_searcher.clear_hash();
    check(tt_searcher.search(clock98, depth2).score == 0, "cleared clock-98 remains a draw");

    tt_searcher.clear_hash();
    check(tt_searcher.search(clock98, depth2).score == 0, "reverse-order clock-98 warmup starts drawn");
    (void)tt_searcher.search(normal, depth4);
    check(tt_searcher.search(clock98, depth2).score == 0, "reverse-order warmup does not leak ordinary TT scores");

    tt_searcher.clear_hash();
    (void)tt_searcher.search(normal, depth4);
    check(tt_searcher.search(clock99, depth2).score == 0, "clock-99 ignores incompatible warmed TT scores");

    tt_searcher.clear_hash();
    check(tt_searcher.search(clock99, depth2).score == 0, "cold clock-99 search is a rule-50 draw");

    tt_searcher.clear_hash();
    (void)tt_searcher.search(normal, depth4);
    check(tt_searcher.search(clock100, depth2).score == 0, "clock-100 root draw precedes TT reuse");

    forge::Board mate100;
    check(mate100.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 100 1"), "TT rule-50 checkmate FEN parses");
    tt_searcher.clear_hash();
    check(forge::SearcherTestProbe::alpha_beta(tt_searcher, mate100, 2, -32000, 32000) < -29000,
          "checkmate still precedes rule-50 with TT enabled");

    forge::Board qnormal, q99;
    check(qnormal.set_fen("r6k/8/8/8/8/8/8/KR6 w - - 0 1"), "qsearch TT normal FEN parses");
    check(q99.set_fen("r6k/8/8/8/8/8/8/KR6 w - - 99 1"), "qsearch TT clock-99 FEN parses");
    forge::Searcher qsearcher(4);
    qsearcher.clear_hash();
    check(forge::SearcherTestProbe::quiescence(qsearcher, q99) == 0, "cold qsearch clock-99 check is drawn");
    qsearcher.clear_hash();
    const int qnormal_score = forge::SearcherTestProbe::quiescence(qsearcher, qnormal);
    check(qnormal_score != 0, "ordinary checked qsearch fixture is non-draw");
    check(forge::SearcherTestProbe::quiescence(qsearcher, q99) == 0, "qsearch ignores incompatible warmed TT score");

    qsearcher.clear_hash();
    const int null_score = forge::SearcherTestProbe::quiescence(qsearcher, q99, 0, true);
    check(null_score != 0, "synthetic-null qsearch suppresses rule-50 draw");
    check(forge::SearcherTestProbe::quiescence(qsearcher, q99) == 0, "synthetic-null TT score does not leak into normal qsearch");
    qsearcher.clear_hash();
    check(forge::SearcherTestProbe::quiescence(qsearcher, q99) == 0, "normal qsearch stores rule-50-aware context");
    check(forge::SearcherTestProbe::quiescence(qsearcher, q99, 0, true) == null_score, "normal TT context does not leak into synthetic-null qsearch");

    forge::Board pawn_reset;
    check(pawn_reset.set_fen("7k/8/8/8/8/8/P7/K7 w - - 99 1"), "pawn-reset FEN parses");
    const auto pawn_move = pawn_reset.parse_uci("a2a3");
    check(pawn_move.has_value(), "pawn-reset move is legal");
    if (pawn_move) {
        forge::Undo undo; (void)pawn_reset.make_move(*pawn_move, undo);
        check(pawn_reset.halfmove_clock() == 0, "pawn move resets rule-50 clock to zero");
        pawn_reset.unmake_move(*pawn_move, undo);
    }

    forge::Board capture_reset;
    check(capture_reset.set_fen("7k/8/8/8/8/8/r7/KR6 w - - 99 1"), "capture-reset FEN parses");
    const auto capture = capture_reset.parse_uci("a1a2");
    check(capture.has_value(), "capture-reset move is legal");
    if (capture) {
        forge::Undo undo; (void)capture_reset.make_move(*capture, undo);
        check(capture_reset.halfmove_clock() == 0, "capture resets rule-50 clock to zero");
        capture_reset.unmake_move(*capture, undo);
    }
}

void check_incremental_keys(std::string_view fen, std::string_view label) {
    forge::Board board;
    check(board.set_fen(fen), "incremental-key FEN parses");
    const std::string original_fen = board.fen();
    const std::uint64_t original_key = board.key();
    const std::uint64_t original_pawn_key = board.pawn_key();
    for (const forge::Move move : board.legal_moves()) {
        forge::Undo undo;
        (void)board.make_move(move, undo);
        check_piece_bitboards(board, label);
        check_occupancy(board, label);
        forge::Board rebuilt;
        check(rebuilt.set_fen(board.fen()), "incremental-key child FEN parses");
        if (board.key() != rebuilt.key()) {
            std::cerr << "FAIL: " << label << " key mismatch after " << forge::Board::move_to_uci(move) << '\n';
            ++failures;
        }
        check(board.pawn_key() == rebuilt.pawn_key(), "incremental pawn key matches reconstruction");
        board.unmake_move(move, undo);
        check_piece_bitboards(board, label);
        check_occupancy(board, label);
        check(board.fen() == original_fen && board.key() == original_key &&
                  board.pawn_key() == original_pawn_key,
              "incremental-key unmake restores state");
    }
}

// Slow, legal-move-based target-square exchange oracle for small fixtures.
// Like SEE, either side may decline the exchange; this is not a full chess search.
constexpr std::array<int, 7> ExchangeValue{0, 100, 320, 330, 500, 900, 20000};

int capture_gain(const forge::Board& board, const forge::Move& move) {
    const int victim = (move.flags & forge::EnPassant) != 0U ? 1
        : forge::piece_type(board.piece_at(move.to));
    const int promotion = (move.flags & forge::Promotion) != 0U
        ? ExchangeValue[move.promotion] - ExchangeValue[1] : 0;
    return ExchangeValue[static_cast<std::size_t>(victim)] + promotion;
}

int legal_recaptures(forge::Board& board, int target, int remaining = 30) {
    if (remaining == 0) return 0;
    int best = 0;
    for (const forge::Move move : board.legal_moves(true)) {
        if (move.to != target || !move.is_capture()) continue;
        const int gain = capture_gain(board, move);
        forge::Undo undo;
        (void)board.make_move(move, undo);
        const int score = gain - legal_recaptures(board, target, remaining - 1);
        board.unmake_move(move, undo);
        best = std::max(best, score);
    }
    return best;
}

void check_legal_see() {
    struct Case { std::string_view fen; std::string_view move; int expected; };
    const std::array<Case, 13> cases{{
        {"4k3/4n3/8/3p4/8/8/8/K2QR3 w - - 0 1", "d1d5", 100},
        {"k2qr3/8/8/8/3P4/8/4N3/4K3 b - - 0 1", "d8d4", 100},
        {"4k3/4b3/3p4/8/8/8/8/K2QR3 w - - 0 1", "d1d6", 100},
        {"4k3/4p3/3p4/8/8/8/8/K2QR3 w - - 0 1", "d1d6", 100},
        {"4k3/8/8/3pr3/8/8/8/K2QR3 w - - 0 1", "d1d5", 100},
        {"4k3/8/8/3pq3/8/8/K7/3QR3 w - - 0 1", "d1d5", 100},
        {"4k3/4r3/Q3p3/8/8/8/8/K3R3 w - - 0 1", "a6e6", -300},
        {"4k3/4n3/2b5/3p4/8/8/8/K2QR3 w - - 0 1", "d1d5", -800},
        {"8/8/4k3/Q2r4/8/8/8/K2R4 w - - 0 1", "a5d5", 500},
        {"4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2", "e5d6", 100},
        {"r6k/1P6/8/8/8/8/8/7K w - - 0 1", "b7a8q", 1300},
        {"r6k/1P6/8/8/8/8/8/7K w - - 0 1", "b7a8n", 720},
        {"1q2k3/4n3/8/3r4/8/8/8/K2QR3 w - - 0 1", "d1d5", 500}
    }};
    for (const Case& item : cases) {
        forge::Board board;
        check(board.set_fen(item.fen), "legal SEE fixture parses");
        const auto move = board.parse_uci(item.move);
        check(move.has_value(), "legal SEE fixture move is legal");
        if (!move) continue;
        const auto fen = board.fen();
        const auto key = board.key();
        const auto pawn_key = board.pawn_key();
        const auto history = board.key_history();
        const int actual = board.static_exchange(*move);
        if (actual != item.expected) {
            std::cerr << "FAIL: legal SEE " << item.fen << " " << item.move
                      << " expected " << item.expected << " got " << actual << '\n';
            ++failures;
        }
        check(board.fen() == fen && board.key() == key && board.pawn_key() == pawn_key &&
                  board.key_history() == history, "SEE leaves original board state untouched");
        check_piece_bitboards(board, "legal SEE");
        check_occupancy(board, "legal SEE");
        const int gain = capture_gain(board, *move);
        forge::Undo undo;
        (void)board.make_move(*move, undo);
        check(actual == gain - legal_recaptures(board, move->to), "SEE matches legal target-exchange oracle");
    }
    for (const std::string_view fen : {cases[0].fen, cases[1].fen}) {
        forge::Board board;
        check(board.set_fen(fen), "pinned recapture qsearch fixture parses");
        const std::string original = board.fen();
        forge::Searcher searcher(4);
        const int stand_pat = forge::Searcher::evaluate(board);
        const int result = forge::SearcherTestProbe::quiescence(searcher, board);
        check(result > stand_pat + 100, "qsearch does not prune the profitable capture of a pinned defender's pawn");
        check(board.fen() == original, "king-safe SEE qsearch restores board");
    }
    forge::Board material_case;
    check(material_case.set_fen(cases[12].fen), "material-changing pin fixture parses");
    forge::Searcher material_searcher(4);
    check(forge::Searcher::evaluate(material_case) < 0 &&
              forge::SearcherTestProbe::quiescence(material_searcher, material_case) > 0,
          "qsearch recognizes the free rook behind an illegal pinned recapture");
}

struct TacticalCase {
    std::string_view label;
    std::string_view fen;
    int depth;
    std::string_view first_move;
    std::string_view second_move;
    int minimum_score;
    std::uint64_t maximum_nodes;
};

void check_tactical_case(const TacticalCase& item) {
    forge::Board board;
    check(board.set_fen(item.fen), "tactical FEN parses");
    forge::Searcher searcher(4);
    forge::SearchLimits limits;
    limits.depth = item.depth;
    const forge::SearchInfo result = searcher.search(board, limits);
    const std::string best = forge::Board::move_to_uci(result.best_move);
    if (best != item.first_move && (item.second_move.empty() || best != item.second_move)) {
        std::cerr << "FAIL: " << item.label << " expected " << item.first_move << " got " << best << '\n';
        ++failures;
    }
    check(result.depth == item.depth, "tactical search completes requested depth");
    if (result.score < item.minimum_score) {
        std::cerr << "FAIL: " << item.label << " score " << result.score
                  << " below " << item.minimum_score << '\n';
        ++failures;
    }
    check(result.nodes <= item.maximum_nodes, "tactical search stays within node ceiling");
}

} // namespace

int main() {
    check_tt_rule50_context();

    check_legal_see();
    forge::Board board;
    const std::string start(board.fen());
    check(start == forge::Board::StandardStartFen, "start FEN round trip");
    forge::Board invalid_board;
    const std::string unchanged_invalid_board = invalid_board.fen();
    check(!invalid_board.set_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1 trailing"),
          "FEN rejects trailing fields");
    check(invalid_board.fen() == unchanged_invalid_board,
          "rejected trailing FEN leaves the board unchanged");
    check(!invalid_board.set_fen("4k3/8/8/8/8/8/8/P3K3 w - - 0 1"),
          "FEN rejects a pawn on the promotion rank");
    check(!invalid_board.set_fen("8/8/8/8/8/8/4k3/4K3 w - - 0 1"),
          "FEN rejects adjacent kings");
    check(!invalid_board.set_fen("4k3/8/8/8/8/8/4R3/4K3 w - - 0 1"),
          "FEN rejects a previous move that left its king in check");
    check(invalid_board.set_fen("4k3/4r3/8/8/8/8/8/4K3 w - - 0 1"),
          "FEN allows the side to move to be in check");
    check(!invalid_board.set_fen("4k3/8/8/8/8/8/8/4K3 w K - 0 1"),
          "FEN rejects castling rights without a rook");
    check(!invalid_board.set_fen("4k3/8/8/8/8/8/8/4K3 w - e6 0 1"),
          "FEN rejects an inconsistent en-passant target");
    check(!invalid_board.set_fen("4k3/8/3N4/3p4/8/8/8/4K3 w - d6 0 1"),
          "FEN rejects an occupied en-passant target");
    check(!invalid_board.set_fen("4k3/3N4/8/3p4/8/8/8/4K3 w - d6 0 1"),
          "FEN rejects an occupied double-push origin");
    check(!invalid_board.set_fen("4k3/8/8/8/P7/PPPPPPPP/8/4K3 w - - 0 1"),
          "FEN rejects more than eight pawns for one side");
    check(!invalid_board.set_fen("4k3/8/8/8/8/QQ6/PPPPPPPP/4K3 w - - 0 1"),
          "FEN rejects promoted material without a missing pawn");
    forge::Board see_board;
    check(see_board.set_fen("4k3/8/8/3r4/8/8/8/3QK3 w - - 0 1"), "SEE free-rook FEN parses");
    const auto free_rook = see_board.parse_uci("d1d5");
    check(free_rook.has_value() && see_board.static_exchange(*free_rook) == 500,
          "SEE values an undefended rook capture");
    check(see_board.set_fen("3qk3/8/8/3p4/8/8/8/3QK3 w - - 0 1"), "SEE defended-pawn FEN parses");
    const auto poisoned_pawn = see_board.parse_uci("d1d5");
    check(poisoned_pawn.has_value() && see_board.static_exchange(*poisoned_pawn) == -800,
          "SEE detects a poisoned pawn capture");
    check(see_board.set_fen("7k/8/8/8/8/7K/p7/1rR5 w - - 0 1"),
          "SEE promotion-recapture FEN parses");
    const auto promotion_recapture = see_board.parse_uci("c1b1");
    check(promotion_recapture.has_value() && see_board.static_exchange(*promotion_recapture) == -800,
          "SEE includes material gained by a promotion recapture");
    if (promotion_recapture.has_value()) {
        forge::Searcher qsearcher(4);
        check(forge::SearcherTestProbe::quiescence(qsearcher, see_board) ==
                  forge::Searcher::evaluate(see_board),
              "quiescence preserves the score for a losing back-rank capture");
        check(see_board.fen() == "7k/8/8/8/8/7K/p7/1rR5 w - - 0 1",
              "losing promotion-recapture qsearch restores board");
    }
    check(see_board.set_fen("1Rr5/P7/7k/8/8/8/8/7K b - - 0 1"),
          "SEE mirrored promotion-recapture FEN parses");
    const auto mirrored_promotion_recapture = see_board.parse_uci("c8b8");
    check(mirrored_promotion_recapture.has_value() &&
              see_board.static_exchange(*mirrored_promotion_recapture) == -800,
          "SEE includes material gained by a mirrored promotion recapture");
    if (mirrored_promotion_recapture.has_value()) {
        forge::Searcher qsearcher(4);
        check(forge::SearcherTestProbe::quiescence(qsearcher, see_board) ==
                  forge::Searcher::evaluate(see_board),
              "quiescence handles mirrored losing back-rank captures");
        check(see_board.fen() == "1Rr5/P7/7k/8/8/8/8/7K b - - 0 1",
              "mirrored losing promotion-recapture qsearch restores board");
    }
    forge::Board qsee_board;
    check(qsee_board.set_fen("rnbq1b1r/1p3ppp/p1p1k2n/3pp1B1/6PP/N2P1P1B/PPP1P3/R2QK1NR w KQ - 2 8"),
          "negative-SEE qsearch regression FEN parses");
    {
        const std::string original = qsee_board.fen();
        forge::Searcher qsearcher(4);
        // Bxd8 wins the queen; the equal bishop-for-knight reply Bxa3 (SEE -10)
        // must survive quiescence pruning so the win is not overstated.
        const int qscore = forge::SearcherTestProbe::quiescence(qsearcher, qsee_board);
        check(qscore > 600 && qscore < 800,
              "qsearch keeps a near-equal exchange that bounds the won material");
        check(qsee_board.fen() == original,
              "negative-SEE qsearch regression restores board");
    }
    {
        forge::Searcher searcher(4);
        forge::SearchLimits limits;
        limits.depth = 1;
        const forge::SearchInfo result = searcher.search(qsee_board, limits);
        check(result.score > 600 && result.score < 800,
              "depth-1 public search inherits the quiescence score");
        check(forge::Board::move_to_uci(result.best_move) == "g5d8",
              "depth-1 public search preserves the tactical best move");
    }
    forge::Board qsee_child;
    check(qsee_child.set_fen("rnbB1b1r/1p3ppp/p1p1k2n/3pp3/6PP/N2P1P1B/PPP1P3/R2QK1NR b KQ - 0 8"),
          "negative-SEE child regression FEN parses");
    const auto qsee_reply = qsee_child.parse_uci("f8a3");
    check(qsee_reply.has_value() && qsee_child.static_exchange(*qsee_reply) == -10,
          "negative-SEE tactical reply remains correctly classified by material SEE");

    forge::Board qdelta_board;
    check(qdelta_board.set_fen("r1b1k2r/Nppp1pp1/n6n/4p2p/Pb2P2q/5RP1/2PP1P1P/2BQKBNR b Kkq - 2 10"),
          "hard-delta qsearch regression FEN parses");
    {
        const std::string original = qdelta_board.fen();
        forge::Searcher qsearcher(4);
        check(forge::Searcher::evaluate(qdelta_board) == 46,
              "hard-delta qsearch regression keeps the expected static evaluation");
        check(forge::SearcherTestProbe::quiescence_window(qsearcher, qdelta_board, 296, 297) == 297,
              "qsearch does not prune a pawn capture that refutes the zero-window bound");
        check(qdelta_board.fen() == original,
              "hard-delta qsearch regression restores board");
        const auto delta_reply = qdelta_board.parse_uci("h4e4");
        check(delta_reply.has_value() && qdelta_board.static_exchange(*delta_reply) == 100,
              "hard-delta causal queen capture remains a favorable material exchange");
    }

    check(board.legal_moves().size() == 20, "start position has 20 moves");
    check(board.perft(0) == 1 && board.perft(-1) == 1,
          "non-positive perft depths terminate at the current leaf");
    check(forge::Searcher::evaluate(board) == 10, "start evaluation is tempo only");

    forge::Board evaluation_board;
    check(evaluation_board.set_fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
          "complex evaluation regression FEN parses");
    check(forge::Searcher::evaluate(evaluation_board) == 30,
          "complex evaluation regression preserves exact tapered score");
    check(evaluation_board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"),
          "side-to-move evaluation FEN parses");
    check(forge::Searcher::evaluate(evaluation_board) == 10, "tempo bonus follows side to move");
    check(evaluation_board.set_fen("6k1/8/8/8/8/8/8/Q3K3 w - - 0 1"), "material evaluation FEN parses");
    check(forge::Searcher::evaluate(evaluation_board) > 800, "queen advantage evaluates decisively");
    check(evaluation_board.set_fen("7k/8/4P3/8/8/8/8/4K3 w - - 0 1"), "advanced passer FEN parses");
    const int advanced_passer = forge::Searcher::evaluate(evaluation_board);
    check(evaluation_board.set_fen("7k/8/8/8/8/8/4P3/4K3 w - - 0 1"), "home passer FEN parses");
    check(advanced_passer > forge::Searcher::evaluate(evaluation_board), "advanced passed pawn gains value");
    check(evaluation_board.set_fen("7k/8/8/8/3K4/8/8/8 w - - 0 1"), "central king FEN parses");
    const int central_king = forge::Searcher::evaluate(evaluation_board);
    check(evaluation_board.set_fen("7k/8/8/8/8/8/8/K7 w - - 0 1"), "corner king FEN parses");
    check(central_king > forge::Searcher::evaluate(evaluation_board), "endgame king centralization gains value");

    const auto e2e4 = board.parse_uci("e2e4");
    check(e2e4.has_value(), "e2e4 parses");
    if (e2e4.has_value()) {
        forge::Undo undo;
        (void)board.make_move(*e2e4, undo);
        board.unmake_move(*e2e4, undo);
        check(board.fen() == start, "make/unmake restores FEN");
    }
    check(board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 65535 65535"),
          "saturated-counter FEN parses");
    const std::string saturated_fen = board.fen();
    const auto saturated_move = board.parse_uci("g8f6");
    check(saturated_move.has_value(), "saturated-counter quiet move parses");
    if (saturated_move.has_value()) {
        forge::Undo undo;
        (void)board.make_move(*saturated_move, undo);
        check(board.fen().ends_with(" 65535 65535"), "move counters saturate without wrapping");
        board.unmake_move(*saturated_move, undo);
        check(board.fen() == saturated_fen, "unmake restores saturated counters exactly");
    }
    check(board.set_fen(forge::Board::StandardStartFen), "reset after saturated-counter test");

    check_perft(forge::Board::StandardStartFen, 4, 197281, "start perft 4");
    check_perft("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
                3, 97862, "kiwipete perft 3");
    check_perft("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 4, 43238, "perft position 3 depth 4");
    check_perft("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
                3, 9467, "perft position 4 depth 3");
    check_perft("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
                3, 62379, "perft position 5 depth 3");

    check(board.set_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1"), "promotion FEN parses");
    check(board.parse_uci("a7a8q").has_value(), "queen promotion legal");
    check(board.parse_uci("a7a8n").has_value(), "knight promotion legal");

    check(board.set_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"), "en-passant FEN parses");
    check(board.parse_uci("e5d6").has_value(), "en-passant legal");

    forge::Board key_comparison;
    check(board.set_fen("4k3/8/8/8/P7/8/8/4K3 b - a3 0 1"), "non-capturable ep FEN parses");
    check(key_comparison.set_fen("4k3/8/8/8/P7/8/8/4K3 b - - 0 1"), "matching no-ep FEN parses");
    check(board.key() == key_comparison.key(), "non-capturable ep target is not hashed");

    check(board.set_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"), "capturable ep key FEN parses");
    check(key_comparison.set_fen("4k3/8/8/3pP3/8/8/8/4K3 w - - 0 1"), "matching capturable no-ep FEN parses");
    check(board.key() != key_comparison.key(), "capturable ep target is hashed");

    check(board.set_fen("k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"), "pinned ep key FEN parses");
    check(key_comparison.set_fen("k3r3/8/8/3pP3/8/8/8/4K3 w - - 0 1"), "matching pinned no-ep FEN parses");
    check(board.key() == key_comparison.key(), "king-pinned ep target is not hashed");

    check(board.set_fen(forge::Board::StandardStartFen), "reset start FEN");
    for (int cycle = 0; cycle < 2; ++cycle) {
        play(board, "g1f3"); play(board, "g8f6"); play(board, "f3g1"); play(board, "f6g8");
    }
    check(board.is_repetition(), "threefold repetition tracked");

    check(board.set_fen(forge::Board::StandardStartFen), "reset for ep repetition test");
    play(board, "a2a4");
    for (int cycle = 0; cycle < 2; ++cycle) {
        play(board, "g8f6"); play(board, "g1f3"); play(board, "f6g8"); play(board, "f3g1");
    }
    check(board.is_repetition(), "non-capturable ep target does not hide threefold repetition");

    forge::Board repeated_context;
    check(repeated_context.set_fen("6nk/8/8/8/8/8/8/1Q2K1N1 w - - 0 1"),
          "repetition TT fixture parses");
    for (const auto move : {"g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1"}) {
        play(repeated_context, move);
    }
    forge::Board fresh_context;
    check(fresh_context.set_fen(repeated_context.fen()), "repetition TT fresh twin parses");
    check(fresh_context.key() == repeated_context.key() &&
              fresh_context.halfmove_clock() == repeated_context.halfmove_clock(),
          "repetition TT fixture shares ordinary key and rule-50 context");
    check(fresh_context.transposition_history_key() != repeated_context.transposition_history_key(),
          "TT identity distinguishes known reversible histories");

    forge::Searcher history_warm(1);
    forge::Searcher history_cold(1);
    const int fresh_history_score = forge::SearcherTestProbe::alpha_beta(
        history_warm, fresh_context, 1, -32000, 32000, 1);
    const int warm_repetition_score = forge::SearcherTestProbe::alpha_beta(
        history_warm, repeated_context, 1, -32000, 32000, 1);
    const int cold_repetition_score = forge::SearcherTestProbe::alpha_beta(
        history_cold, repeated_context, 1, -32000, 32000, 1);
    check(fresh_history_score < -500, "fresh history fixture is losing without a repetition claim");
    check(warm_repetition_score == 0 && cold_repetition_score == 0,
          "warm TT cannot override an available repetition draw from another history");

    forge::Board zeroed_history;
    check(zeroed_history.set_fen(forge::Board::StandardStartFen), "history reset fixture parses");
    for (const auto move : {"g1f3", "g8f6", "f3g1", "f6g8", "e2e4"}) {
        play(zeroed_history, move);
    }
    forge::Board rebuilt_history;
    check(rebuilt_history.set_fen(zeroed_history.fen()), "zeroing-move twin parses");
    check(zeroed_history.transposition_history_key() == rebuilt_history.transposition_history_key(),
          "pawn move resets obsolete repetition context");

    forge::Board castling_reset;
    check(castling_reset.set_fen("4k2r/8/8/8/8/8/8/R3K2R w KQk - 0 1"),
          "castling-right reset fixture parses");
    play(castling_reset, "h1h2");
    forge::Board castling_rebuilt;
    check(castling_rebuilt.set_fen(castling_reset.fen()), "castling-right reset twin parses");
    check(castling_reset.transposition_history_key() == castling_rebuilt.transposition_history_key(),
          "castling-right loss resets obsolete repetition context");

    const std::uint64_t before_history_key = zeroed_history.transposition_history_key();
    const auto history_moves = zeroed_history.legal_moves();
    check(!history_moves.empty(), "history make/unmake fixture has a legal move");
    if (!history_moves.empty()) {
        forge::Undo history_undo;
        (void)zeroed_history.make_move(history_moves.front(), history_undo);
        zeroed_history.unmake_move(history_moves.front(), history_undo);
        check(zeroed_history.transposition_history_key() == before_history_key,
              "make/unmake restores repetition TT context exactly");
    }

    check_incremental_keys(forge::Board::StandardStartFen, "ordinary move");
    check_incremental_keys("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "castling move");
    check_incremental_keys("4k3/P7/8/8/8/8/8/4K3 w - - 0 1", "promotion move");
    check_incremental_keys("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "en-passant move");

    check(board.set_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 99 1"), "null-move EP FEN parses");
    const std::string before_null_fen = board.fen();
    const std::uint64_t before_null_key = board.key();
    const std::size_t before_null_history = board.key_history().size();
    forge::NullUndo first_null;
    forge::NullUndo second_null;
    board.make_null_move(first_null);
    check(board.halfmove_clock() == 99, "null move preserves rule-50 clock");
    check(board.key_history().size() == before_null_history, "null move does not enter repetition history");
    forge::Board rebuilt_null;
    check(rebuilt_null.set_fen(board.fen()), "null position FEN parses");
    check(board.key() == rebuilt_null.key(), "null position key matches full recomputation");
    board.make_null_move(second_null);
    board.unmake_null_move(second_null);
    board.unmake_null_move(first_null);
    check(board.fen() == before_null_fen && board.key() == before_null_key,
          "double null move restores FEN and key");
    check(board.key_history().size() == before_null_history, "double null restores repetition history");

    std::uint64_t random_state = 0x6a09e667f3bcc909ULL;
    for (int game = 0; game < 8; ++game) {
        check(board.set_fen(forge::Board::StandardStartFen), "incremental-key walk reset");
        for (int ply = 0; ply < 160; ++ply) {
            const auto moves = board.legal_moves();
            if (moves.empty()) break;
            random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
            const forge::Move move = moves[static_cast<std::size_t>(random_state % moves.size())];
            forge::Undo undo;
            (void)board.make_move(move, undo);
            check_piece_bitboards(board, "deterministic walk");
            check_occupancy(board, "deterministic walk");
            forge::Board rebuilt;
            check(rebuilt.set_fen(board.fen()), "incremental-key walk FEN parses");
        check(board.key() == rebuilt.key(), "incremental key matches full recomputation during walk");
        check(board.pawn_key() == rebuilt.pawn_key(), "incremental pawn key matches reconstruction during walk");
        }
    }

    constexpr std::array<TacticalCase, 7> TacticalCases{{
        {"white back-rank mate", "6k1/5ppp/8/8/8/8/8/4R1K1 w - - 0 1", 3, "e1e8", "", 29000, 1000},
        {"smothered knight mate", "6rk/6pp/7N/8/8/8/8/6K1 w - - 0 1", 3, "h6f7", "", 29000, 500},
        {"queen sacrifice mate", "r6k/6pp/4Q2N/8/8/8/8/6K1 w - - 0 1", 4, "e6g8", "", 29000, 10000},
        {"royal fork", "3q4/6k1/8/8/5N2/8/8/6K1 w - - 0 1", 3, "f4e6", "", 0, 1500},
        {"discovered double attack", "3q3k/6N1/8/8/8/8/1B6/6K1 w - - 0 1", 3, "g7e6", "", 500, 2000},
        {"promotion mate", "k7/2P5/1K6/8/8/8/8/8 w - - 0 1", 3, "c7c8q", "c7c8r", 29000, 500},
        {"black back-rank mate", "4r1k1/8/8/8/8/8/5PPP/6K1 b - - 0 1", 3, "e8e1", "", 29000, 1000},
    }};
    for (const TacticalCase& item : TacticalCases) check_tactical_case(item);

    forge::SearchLimits null_limits;
    null_limits.depth = 8;
    forge::Searcher null_searcher(4);
    check(board.set_fen("8/8/8/3k4/8/4K3/4P3/8 w - - 0 1"), "pawn-only null guard FEN parses");
    (void)null_searcher.search(board, null_limits);
    check(forge::SearcherTestProbe::null_tries(null_searcher) == 0,
          "null pruning is disabled in pawn-only endings");
    check(board.set_fen(forge::Board::StandardStartFen), "null activity start FEN parses");
    (void)null_searcher.search(board, null_limits);
    check(forge::SearcherTestProbe::null_tries(null_searcher) > 0,
          "null pruning activates with non-pawn material");
    check(forge::SearcherTestProbe::null_cutoffs(null_searcher) > 0,
          "null pruning produces verified cutoffs");

    // The search prunes speculatively (reverse futility, null move, late-move
    // reductions, futility and late-move pruning). The properties below hold
    // regardless of pruning: forced mates are found, draws are never turned
    // into wins, and searches are deterministic.
    struct MateCase {
        std::string_view label;
        std::string_view fen;
        int depth;
        std::string_view first_move;
    };
    constexpr std::array<MateCase, 4> MateCases{{
        {"Morphy opera mate in two", "4kb1r/p2n1ppp/4q3/4p1B1/4P3/1Q6/PPP2PPP/2KR4 w k - 1 17", 5, "b3b8"},
        {"Reti-Tartakower mate in three", "rnb1kb1r/pp3ppp/2p5/4q3/4n3/3Q4/PPPB1PPP/2KR1BNR w kq - 0 1", 7, "d3d8"},
        {"back-rank mate in one with pruning depth", "6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1", 6, "d1d8"},
        {"scholar's mate at depth six", "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", 6, "h5f7"},
    }};
    for (const MateCase& item : MateCases) {
        forge::Board mate_board;
        check(mate_board.set_fen(item.fen), "mate property FEN parses");
        forge::Searcher mate_searcher(8);
        forge::SearchLimits mate_limits;
        mate_limits.depth = item.depth;
        const forge::SearchInfo mate_info = mate_searcher.search(mate_board, mate_limits);
        if (forge::Board::move_to_uci(mate_info.best_move) != item.first_move) {
            std::cerr << "FAIL: " << item.label << " expected " << item.first_move << " got "
                      << forge::Board::move_to_uci(mate_info.best_move) << '\n';
            ++failures;
        }
        check(mate_info.score > 29000, "pruned search still proves the forced mate");
        check(mate_board.fen() == item.fen, "mate property search restores the board");
    }

    // Whole-node pruning must never manufacture a bound in a stalemate: the
    // favorable-looking side has only pawns, so no move-free cutoff applies.
    forge::Board pruned_stalemate;
    check(pruned_stalemate.set_fen("5k1K/7P/8/8/8/8/8/8 w - - 0 1"), "pruned stalemate FEN parses");
    for (int depth = 1; depth <= 6; ++depth) {
        forge::Searcher stalemate_searcher(4);
        check(forge::SearcherTestProbe::alpha_beta(stalemate_searcher, pruned_stalemate, depth, 0, 1, 1) == 0,
              "zero-window stalemate stays drawn at every pruning depth");
        check(forge::SearcherTestProbe::alpha_beta(stalemate_searcher, pruned_stalemate, depth, -1, 0, 1) == 0,
              "zero-window stalemate never fails low below the draw score");
    }

    // Reverse futility and null-move pruning are disabled in pawn endings.
    forge::Board pawn_ending;
    check(pawn_ending.set_fen("8/5k2/8/3K4/3P4/8/8/8 w - - 0 1"), "pawn ending FEN parses");
    forge::Searcher pawn_ending_searcher(4);
    forge::SearchLimits pawn_ending_limits;
    pawn_ending_limits.depth = 8;
    (void)pawn_ending_searcher.search(pawn_ending, pawn_ending_limits);
    check(forge::SearcherTestProbe::reverse_futility_cutoffs(pawn_ending_searcher) == 0 &&
              forge::SearcherTestProbe::null_tries(pawn_ending_searcher) == 0,
          "pawn endings use neither reverse futility nor null-move pruning");

    // Reverse futility is active with non-pawn material and never returns
    // anything but the beta bound from a zero-window node.
    forge::Board rfp_board;
    check(rfp_board.set_fen("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 3"),
          "reverse futility activity FEN parses");
    forge::Searcher rfp_searcher(4);
    forge::SearchLimits rfp_limits;
    rfp_limits.depth = 7;
    const forge::SearchInfo rfp_result = rfp_searcher.search(rfp_board, rfp_limits);
    check(forge::SearcherTestProbe::reverse_futility_cutoffs(rfp_searcher) > 0,
          "reverse futility pruning activates in a middlegame search");
    check(rfp_result.depth == 7 && std::abs(rfp_result.score) < 300,
          "pruned middlegame search returns a sane score at the requested depth");

    // Identical searches are deterministic: same nodes, score and move.
    forge::Board determinism_board;
    check(determinism_board.set_fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
          "determinism FEN parses");
    forge::SearchLimits determinism_limits;
    determinism_limits.depth = 7;
    forge::Searcher determinism_first(8);
    forge::Searcher determinism_second(8);
    const forge::SearchInfo determinism_a = determinism_first.search(determinism_board, determinism_limits);
    const forge::SearchInfo determinism_b = determinism_second.search(determinism_board, determinism_limits);
    check(determinism_a.nodes == determinism_b.nodes && determinism_a.score == determinism_b.score &&
              forge::Board::move_to_uci(determinism_a.best_move) ==
                  forge::Board::move_to_uci(determinism_b.best_move),
          "fresh searchers reproduce the same node count, score and best move");
    check(determinism_a.pv.size() >= 4 && determinism_a.seldepth >= determinism_a.depth,
          "pruned search reports a usable principal variation and selective depth");

    check(board.set_fen("2rqNN2/4k3/ppp2pB1/3p4/PPPp1Prb/n3P2b/K7/4Q3 b - - 0 34"),
          "searchmoves tactical regression FEN parses");
    const auto null_a3b5 = board.parse_uci("a3b5");
    const auto null_g4g3 = board.parse_uci("g4g3");
    check(null_a3b5.has_value() && null_g4g3.has_value(),
          "searchmoves tactical regression moves parse");
    if (null_a3b5.has_value() && null_g4g3.has_value()) {
        forge::SearchLimits restricted_tactical_limits;
        restricted_tactical_limits.depth = 6;
        restricted_tactical_limits.search_moves_specified = true;
        restricted_tactical_limits.search_moves = {*null_a3b5, *null_g4g3};
        forge::Searcher restricted_tactical_searcher(4);
        const forge::SearchInfo restricted_tactical =
            restricted_tactical_searcher.search(board, restricted_tactical_limits);
        const std::string restricted_best = forge::Board::move_to_uci(restricted_tactical.best_move);
        check(restricted_best == "g4g3" || restricted_best == "a3b5",
              "restricted root search chooses one of the permitted moves");
        check(restricted_tactical.score > 1000,
              "restricted root search recognizes the decisive advantage");
    }
    forge::SearchLimits overhead_limits;
    overhead_limits.movetime_ms = 100;
    overhead_limits.move_overhead_ms = 25;
    overhead_limits.nodes = 1;
    (void)null_searcher.search(board, overhead_limits);
    check(forge::SearcherTestProbe::time_limit_ms(null_searcher) == 75,
          "configured move overhead is reserved from movetime");
    check(forge::SearcherTestProbe::soft_limit_ms(null_searcher) == 75,
          "a fixed movetime has no earlier soft limit");
    check(forge::SearcherTestProbe::time_check_mask(null_searcher) == 31,
          "short searches use a responsive clock-check interval");
    forge::SearchLimits clock_limits;
    clock_limits.time_ms = 30000;
    clock_limits.increment_ms = 0;
    clock_limits.moves_to_go = 30;
    clock_limits.move_overhead_ms = 0;
    clock_limits.nodes = 1;
    (void)null_searcher.search(board, clock_limits);
    check(forge::SearcherTestProbe::time_limit_ms(null_searcher) == 1000 &&
              forge::SearcherTestProbe::soft_limit_ms(null_searcher) == 500,
          "a game clock stops starting iterations at half of the hard budget");
    forge::SearchLimits zero_movetime_limits;
    zero_movetime_limits.movetime_ms = 0;
    zero_movetime_limits.nodes = 1;
    (void)null_searcher.search(board, zero_movetime_limits);
    check(forge::SearcherTestProbe::time_limit_ms(null_searcher) == 1,
          "explicit zero movetime is a bounded one-millisecond search, not an absent limit");
    forge::SearchLimits zero_clock_limits;
    zero_clock_limits.time_ms = 0;
    zero_clock_limits.nodes = 1;
    (void)null_searcher.search(board, zero_clock_limits);
    check(forge::SearcherTestProbe::time_limit_ms(null_searcher) == 1,
          "explicit zero side clock is a bounded one-millisecond search, not an absent limit");
    forge::SearchLimits absent_clock_limits;
    absent_clock_limits.nodes = 1;
    (void)null_searcher.search(board, absent_clock_limits);
    check(forge::SearcherTestProbe::time_limit_ms(null_searcher) == 0,
          "absent clock and movetime fields remain unbounded");
    forge::SearchLimits zero_node_limits;
    zero_node_limits.nodes = 0;
    zero_node_limits.nodes_specified = true;
    const forge::SearchInfo zero_node_result = null_searcher.search(board, zero_node_limits);
    check(forge::SearcherTestProbe::node_limit_specified(null_searcher),
          "explicit zero node limit remains distinguishable from an absent node limit");
    check(zero_node_result.nodes == 0 && zero_node_result.depth == 0,
          "explicit zero node limit stops before visiting a search node");
    forge::SearchLimits absent_node_limits;
    absent_node_limits.depth = 1;
    const forge::SearchInfo absent_node_result = null_searcher.search(board, absent_node_limits);
    check(!forge::SearcherTestProbe::node_limit_specified(null_searcher),
          "absent node limit remains unbounded");
    check(absent_node_result.depth == 1 && absent_node_result.nodes > 0,
          "absent node limit still permits a normal finite-depth search");
    forge::SearchLimits legacy_positive_node_limits;
    legacy_positive_node_limits.depth = 3;
    legacy_positive_node_limits.nodes = 1;
    const forge::SearchInfo legacy_positive_node_result =
        null_searcher.search(board, legacy_positive_node_limits);
    check(forge::SearcherTestProbe::node_limit_specified(null_searcher) &&
              legacy_positive_node_result.nodes == 1,
          "positive direct-API node limits remain effective without the explicit flag");
    forge::SearchLimits extreme_clock_limits;
    extreme_clock_limits.nodes = 1;
    extreme_clock_limits.time_ms = std::numeric_limits<int>::max();
    extreme_clock_limits.increment_ms = std::numeric_limits<int>::max();
    (void)null_searcher.search(board, extreme_clock_limits);
    check(forge::SearcherTestProbe::time_limit_ms(null_searcher) == 1073741813ULL,
          "clock-budget arithmetic is overflow-safe at maximum integer limits");
    check(forge::SearcherTestProbe::occupied_tt(null_searcher) > 0, "search populates the hash table");
    null_searcher.clear_hash();
    check(forge::SearcherTestProbe::occupied_tt(null_searcher) == 0, "clear hash empties the hash table");

    forge::Searcher qtt_searcher(4);
    check(board.set_fen("4k3/8/8/8/8/8/4q3/4R1K1 w - - 0 1"), "quiescence TT FEN parses");
    const int first_qscore = forge::SearcherTestProbe::quiescence(qtt_searcher, board);
    const std::uint64_t first_qnodes = forge::SearcherTestProbe::nodes(qtt_searcher);
    forge::SearcherTestProbe::reset_nodes(qtt_searcher);
    const int second_qscore = forge::SearcherTestProbe::quiescence(qtt_searcher, board);
    const std::uint64_t second_qnodes = forge::SearcherTestProbe::nodes(qtt_searcher);
    check(first_qscore == second_qscore, "quiescence TT preserves the cached score");
    check(first_qnodes > second_qnodes && second_qnodes == 1,
          "quiescence TT exact hit avoids re-searching the capture tree");

    check(board.set_fen("8/8/8/3k4/8/4K3/8/8 w - - 0 1"), "bare-kings FEN parses");
    check(board.is_insufficient_material(), "bare kings are insufficient material");
    forge::Searcher draw_searcher(4);
    forge::SearchLimits draw_limits;
    draw_limits.depth = 4;
    const auto bare_kings_result = draw_searcher.search(board, draw_limits);
    check(bare_kings_result.score == 0,
          "search adjudicates insufficient material as a draw");
    check(bare_kings_result.depth == 4,
          "completed insufficient-material root reports its completed depth");
    check(bare_kings_result.best_move.from != bare_kings_result.best_move.to,
          "insufficient-material root preserves a legal fallback move for UCI compatibility");
    check(bare_kings_result.nodes == 4,
          "each terminal root visit consumes one node per completed iteration");
    check(board.set_fen("8/8/8/3k4/8/4K3/2B5/8 w - - 0 1"), "single-bishop FEN parses");
    check(board.is_insufficient_material(), "king and bishop versus king is insufficient material");
    check(board.set_fen("8/8/8/3k1b2/8/4K3/2B5/8 w - - 0 1"), "same-color bishops FEN parses");
    check(board.is_insufficient_material(), "same-color bishop ending is insufficient material");
    check(board.set_fen("8/8/8/3k4/8/4K3/2BN4/8 w - - 0 1"), "bishop-knight FEN parses");
    check(!board.is_insufficient_material(), "bishop and knight retain mating material");

    check(board.set_fen("7k/5Q2/7K/8/8/8/8/8 w - - 0 1"), "mate test FEN parses");
    forge::Searcher searcher(4);
    forge::SearchLimits limits;
    limits.depth = 3;
    const forge::SearchInfo result = searcher.search(board, limits);
    check(result.best_move.from != result.best_move.to, "search finds a move");
    check(result.score > 29000, "search recognizes forced mate");
    check(result.seldepth > 0 && result.seldepth < 128, "search reports selective depth");
    check(searcher.hashfull_permille() >= 0 && searcher.hashfull_permille() <= 1000,
          "hashfull telemetry stays in permille range");
    forge::SearchLimits mate_limits;
    mate_limits.mate_moves = 1;
    const forge::SearchInfo mate_result = searcher.search(board, mate_limits);
    check(mate_result.depth == 1 && mate_result.score > 29000,
          "mate limit stops after proving mate in one");

    check(board.set_fen(forge::Board::StandardStartFen), "searchmoves start FEN parses");
    forge::Searcher exact_budget_searcher(4);
    forge::SearchLimits one_ply_limits;
    one_ply_limits.depth = 1;
    const auto one_ply = exact_budget_searcher.search(board, one_ply_limits);
    forge::SearchLimits exact_budget_limits;
    exact_budget_limits.depth = 3;
    exact_budget_limits.nodes = one_ply.nodes;
    forge::Searcher cold_exact_budget_searcher(4);
    const auto exact_budget = cold_exact_budget_searcher.search(board, exact_budget_limits);
    check(exact_budget.depth == 1 && exact_budget.nodes == one_ply.nodes,
          "an iteration completed exactly at the node limit is retained");
    forge::SearchLimits restricted_limits;
    restricted_limits.depth = 3;
    restricted_limits.search_moves_specified = true;
    const auto forced_root = board.parse_uci("e2e4");
    check(forced_root.has_value(), "searchmoves root move parses");
    if (forced_root.has_value()) restricted_limits.search_moves.push_back(*forced_root);
    const forge::SearchInfo restricted = searcher.search(board, restricted_limits);
    check(forge::Board::move_to_uci(restricted.best_move) == "e2e4",
          "searchmoves restricts the root result");
    check(restricted.depth == 3 && !restricted.pv.empty() &&
              forge::Board::move_to_uci(restricted.pv.front()) == "e2e4",
          "searchmoves retains completed depth and principal variation without a root TT bound");
    forge::SearchLimits interrupted_restricted_limits = restricted_limits;
    interrupted_restricted_limits.nodes = 1;
    forge::Searcher interrupted_restricted_searcher(4);
    const forge::SearchInfo interrupted_restricted =
        interrupted_restricted_searcher.search(board, interrupted_restricted_limits);
    check(forge::Board::move_to_uci(interrupted_restricted.best_move) == "e2e4",
          "interrupted searchmoves returns an allowed legal fallback move");
    forge::SearchLimits empty_root_limits;
    empty_root_limits.depth = 3;
    empty_root_limits.search_moves_specified = true;
    const forge::SearchInfo empty_root = searcher.search(board, empty_root_limits);
    check(empty_root.best_move.from == empty_root.best_move.to,
          "empty searchmoves restriction does not fall back to an unrestricted move");
    check(empty_root.restricted_root_empty && empty_root.score == 0 && empty_root.pv.empty(),
          "empty searchmoves is a non-mate no-result, not a terminal chess position");
    forge::Searcher cold_empty_searcher(4);
    check(forge::SearcherTestProbe::occupied_tt(cold_empty_searcher) == 0,
          "cold restricted-root fixture starts with an empty transposition table");
    forge::Board original_start_board = board;
    const forge::SearchInfo cold_empty = cold_empty_searcher.search(board, empty_root_limits);
    check(cold_empty.restricted_root_empty && cold_empty.score == 0 && cold_empty.pv.empty() &&
              forge::SearcherTestProbe::occupied_tt(cold_empty_searcher) == 0,
          "cold restricted-empty root never publishes a TT entry or a false mate");
    check(board.fen() == original_start_board.fen() && board.key() == original_start_board.key() &&
              board.transposition_history_key() == original_start_board.transposition_history_key() &&
              board.halfmove_clock() == original_start_board.halfmove_clock() &&
              board.legal_moves().size() == original_start_board.legal_moves().size(),
          "restricted-empty search preserves FEN, key, reversible history, clock, and legal moves");

    forge::Searcher warm_empty_searcher(4);
    forge::SearchLimits warm_root_limits;
    warm_root_limits.depth = 3;
    const forge::SearchInfo warm_before = warm_empty_searcher.search(board, warm_root_limits);
    check(forge::SearcherTestProbe::has_tt_entry(warm_empty_searcher, board),
          "unrestricted search seeds the root TT for warm-empty test");
    const auto root_tt_before = forge::SearcherTestProbe::root_tt_state(warm_empty_searcher, board);
    const forge::SearchInfo warm_empty = warm_empty_searcher.search(board, empty_root_limits);
    check(warm_empty.restricted_root_empty && warm_empty.score == 0 && warm_empty.pv.empty() &&
              warm_empty.best_move.from == warm_empty.best_move.to,
          "warm unrestricted root TT never turns an empty restriction into a move or mate");
    check(forge::SearcherTestProbe::root_tt_state(warm_empty_searcher, board) == root_tt_before,
          "restricted-empty root does not overwrite a prior unrestricted root TT entry");
    const forge::SearchInfo warm_after = warm_empty_searcher.search(board, warm_root_limits);
    check(warm_after.score == warm_before.score &&
              forge::Board::move_to_uci(warm_after.best_move) ==
                  forge::Board::move_to_uci(warm_before.best_move),
          "unrestricted root remains stable after a restricted-empty search");

    forge::SearchLimits terminal_restricted_limits = empty_root_limits;
    forge::Board restricted_in_check;
    check(restricted_in_check.set_fen("4r2k/8/8/8/8/8/8/4K3 w - - 0 1"),
          "restricted-empty in-check nonmate FEN parses");
    check(restricted_in_check.in_check(forge::White) && restricted_in_check.has_legal_move(),
          "restricted-empty in-check position has genuine legal evasions");
    forge::Board in_check_snapshot = restricted_in_check;
    const forge::SearchInfo in_check_empty =
        warm_empty_searcher.search(restricted_in_check, terminal_restricted_limits);
    check(in_check_empty.restricted_root_empty && in_check_empty.score == 0 &&
              in_check_empty.best_move.from == in_check_empty.best_move.to &&
              in_check_empty.pv.empty(),
          "empty in-check restriction is a no-result, never a false mate");
    check(restricted_in_check.fen() == in_check_snapshot.fen() &&
              restricted_in_check.key() == in_check_snapshot.key() &&
              restricted_in_check.transposition_history_key() == in_check_snapshot.transposition_history_key() &&
              restricted_in_check.halfmove_clock() == in_check_snapshot.halfmove_clock() &&
              restricted_in_check.legal_moves().size() == in_check_snapshot.legal_moves().size(),
          "restricted in-check search restores the exact board and legal-move count");

    forge::Board restricted_terminal;
    check(restricted_terminal.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"),
          "restricted genuine checkmate FEN parses");
    const forge::SearchInfo restricted_mate =
        warm_empty_searcher.search(restricted_terminal, terminal_restricted_limits);
    check(!restricted_mate.restricted_root_empty && restricted_mate.score < -29000 &&
              restricted_mate.best_move.from == restricted_mate.best_move.to &&
              restricted_mate.pv.empty(),
          "genuine checkmate remains mate even with a root restriction");
    check(restricted_terminal.set_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
          "restricted genuine stalemate FEN parses");
    const forge::SearchInfo restricted_stalemate =
        warm_empty_searcher.search(restricted_terminal, terminal_restricted_limits);
    check(!restricted_stalemate.restricted_root_empty && restricted_stalemate.score == 0 &&
              restricted_stalemate.best_move.from == restricted_stalemate.best_move.to &&
              restricted_stalemate.pv.empty(),
          "genuine stalemate remains a draw with a root restriction");

    forge::Board restricted_child;
    check(restricted_child.set_fen("rnbqkbnr/pppp1ppp/8/4p3/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 2"),
          "searchmoves TT contamination child FEN parses");
    forge::SearchLimits restricted_tt_limits;
    restricted_tt_limits.depth = 2;
    restricted_tt_limits.search_moves_specified = true;
    const auto restricted_tt_move = restricted_child.parse_uci("a2a3");
    check(restricted_tt_move.has_value(), "searchmoves TT contamination move parses");
    if (restricted_tt_move.has_value()) restricted_tt_limits.search_moves.push_back(*restricted_tt_move);
    forge::Searcher restricted_tt_searcher(4);
    const forge::SearchInfo restricted_tt_result =
        restricted_tt_searcher.search(restricted_child, restricted_tt_limits);
    check(forge::Board::move_to_uci(restricted_tt_result.best_move) == "a2a3" &&
              restricted_tt_result.depth == 2,
          "restricted root search completes normally");
    check(!forge::SearcherTestProbe::has_tt_entry(restricted_tt_searcher, restricted_child),
          "restricted root does not publish a TT score/bound for the restricted move set");

    forge::Board unrestricted_parent;
    check(unrestricted_parent.set_fen("rnbqkbnr/pppp1ppp/4p3/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 7 1"),
          "searchmoves TT contamination parent FEN parses");
    forge::SearchLimits parent_limits;
    parent_limits.depth = 3;
    const forge::SearchInfo warmed_parent = restricted_tt_searcher.search(unrestricted_parent, parent_limits);
    forge::Searcher fresh_parent_searcher(4);
    const forge::SearchInfo fresh_parent = fresh_parent_searcher.search(unrestricted_parent, parent_limits);
    check(warmed_parent.score == fresh_parent.score &&
              forge::Board::move_to_uci(warmed_parent.best_move) == forge::Board::move_to_uci(fresh_parent.best_move),
          "restricted root search does not contaminate a later unrestricted transposition");

    forge::Searcher unrestricted_root_searcher(4);
    forge::SearchLimits unrestricted_child_limits;
    unrestricted_child_limits.depth = 2;
    (void)unrestricted_root_searcher.search(restricted_child, unrestricted_child_limits);
    check(forge::SearcherTestProbe::has_tt_entry(unrestricted_root_searcher, restricted_child),
          "ordinary unrestricted roots still publish TT entries");

    forge::SearchLimits pv_limits;
    pv_limits.depth = 5;
    const forge::SearchInfo cold_pv = searcher.search(board, pv_limits);
    const forge::SearchInfo warm_pv = searcher.search(board, pv_limits);
    check(cold_pv.pv.size() == 5 && warm_pv.pv.size() == 5,
          "cold and warm hash searches report a complete principal variation");

    check(board.set_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"), "stalemate FEN parses");
    check(!board.in_check(forge::Black), "stalemate side is not in check");
    check(!board.has_legal_move(), "stalemate has no legal move");
    check(forge::SearcherTestProbe::quiescence(searcher, board) == 0,
          "quiescence scores quiet stalemate as draw");

    check(board.set_fen("5k1K/7P/8/8/8/8/8/8 w - - 0 1"), "favorable stalemate FEN parses");
    check(forge::Searcher::evaluate(board) > 0, "favorable stalemate has positive static evaluation");
    check(forge::SearcherTestProbe::quiescence(searcher, board) == 0,
          "quiescence scores favorable quiet stalemate as draw");
    const std::string favorable_stalemate_fen = board.fen();
    forge::Searcher favorable_stalemate_window_searcher(4);
    check(forge::SearcherTestProbe::quiescence_window(
              favorable_stalemate_window_searcher, board, 0, 388) == 0,
          "favorable stalemate does not promote positive stand-pat inside the qsearch window");
    check(board.fen() == favorable_stalemate_fen,
          "favorable-stalemate qsearch window regression restores the board");
    forge::Searcher rfp_stalemate_searcher(4);
    check(forge::SearcherTestProbe::alpha_beta(rfp_stalemate_searcher, board, 1, 0, 1) == 0,
          "reverse-futility precheck preserves zero-window stalemate draw");

    check(board.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"), "checkmate horizon FEN parses");
    check(board.in_check(forge::Black), "checkmate side is in check");
    check(forge::SearcherTestProbe::quiescence(searcher, board) < -29000,
          "quiescence scores horizon checkmate as mate");

    check(board.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 100 1"), "rule-50 checkmate FEN parses");
    check(forge::SearcherTestProbe::quiescence(searcher, board) < -29000,
          "checkmate takes precedence over rule-50 draw");

    forge::Searcher terminal_result_searcher(4);
    forge::SearchLimits terminal_result_limits;
    terminal_result_limits.depth = 3;
    check(board.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"),
          "terminal SearchInfo checkmate FEN parses");
    const forge::SearchInfo terminal_mate =
        terminal_result_searcher.search(board, terminal_result_limits);
    check(terminal_mate.score < -29000,
          "terminal SearchInfo commits the completed checkmate score");
    check(terminal_mate.depth == 3,
          "terminal SearchInfo commits the completed checkmate depth");
    check(terminal_mate.best_move.from == terminal_mate.best_move.to && terminal_mate.pv.empty(),
          "terminal checkmate reports no legal best move or PV");

    check(board.set_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
          "terminal SearchInfo stalemate FEN parses");
    const forge::SearchInfo terminal_stalemate =
        terminal_result_searcher.search(board, terminal_result_limits);
    check(terminal_stalemate.score == 0 && terminal_stalemate.depth == 3,
          "terminal SearchInfo commits completed stalemate score and depth");
    check(terminal_stalemate.best_move.from == terminal_stalemate.best_move.to &&
              terminal_stalemate.pv.empty(),
          "terminal stalemate reports no legal best move or PV");

    check(board.set_fen("7k/4Q3/6K1/8/8/8/8/8 w - - 0 1"), "stalemate parent FEN parses");
    const std::string parent_fen = board.fen();
    const std::uint64_t parent_key = board.key();
    check(board.has_legal_move(), "stalemate parent has a legal move");
    check(board.fen() == parent_fen && board.key() == parent_key,
          "legal-move probe preserves board state");
    const auto stalemating_move = board.parse_uci("e7f7");
    check(stalemating_move.has_value(), "stalemating parent move is legal");
    if (stalemating_move.has_value()) {
        forge::Undo undo;
        (void)board.make_move(*stalemating_move, undo);
        const int parent_score = -forge::SearcherTestProbe::quiescence(searcher, board, 1);
        board.unmake_move(*stalemating_move, undo);
        check(parent_score == 0, "parent sees horizon stalemate as draw");
    }

    if (failures != 0) {
        std::cerr << failures << " test(s) failed\n";
        return 1;
    }
    std::cout << "All tests passed\n";
    return 0;
}
