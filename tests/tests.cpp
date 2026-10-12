#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

namespace forge {

struct SearcherTestProbe {
    static std::uint64_t null_tries(Searcher& searcher) { return searcher.main_worker().null_tries_; }
    static std::uint64_t null_cutoffs(Searcher& searcher) { return searcher.main_worker().null_cutoffs_; }
    static TranspositionTable& tt(Searcher& searcher) { return searcher.transposition_table(); }
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
    check(board.fen() == fen, "perft leaves the position unchanged");
}

void play(forge::Board& board, std::string_view text) {
    const auto move = board.parse_uci(text);
    check(move.has_value(), "move should parse as legal");
    if (move.has_value()) {
        forge::Undo undo;
        (void)board.make_move(*move, undo);
    }
}

std::string mirror_fen(std::string_view fen) {
    // Swap colours and flip ranks so the evaluation must negate exactly.
    std::vector<std::string> fields;
    std::string current;
    for (const char c : fen) {
        if (c == ' ') { fields.push_back(current); current.clear(); } else current += c;
    }
    fields.push_back(current);
    std::vector<std::string> ranks;
    current.clear();
    for (const char c : fields[0]) {
        if (c == '/') { ranks.push_back(current); current.clear(); } else current += c;
    }
    ranks.push_back(current);
    std::string placement;
    for (auto it = ranks.rbegin(); it != ranks.rend(); ++it) {
        for (char c : *it) {
            if (std::isalpha(static_cast<unsigned char>(c))) {
                c = std::islower(static_cast<unsigned char>(c)) ? static_cast<char>(std::toupper(static_cast<unsigned char>(c)))
                                                                : static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
            }
            placement += c;
        }
        if (it + 1 != ranks.rend()) placement += '/';
    }
    std::string castling;
    for (const char c : fields[2]) {
        if (c == '-') castling += c;
        else castling += std::islower(static_cast<unsigned char>(c)) ? static_cast<char>(std::toupper(static_cast<unsigned char>(c)))
                                                                     : static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    std::string ep = fields[3];
    if (ep != "-") ep[1] = ep[1] == '3' ? '6' : '3';
    return placement + ' ' + (fields[1] == "w" ? "b" : "w") + ' ' + castling + ' ' + ep + ' ' + fields[4] + ' ' + fields[5];
}

void check_board_consistency(const forge::Board& board, std::string_view label) {
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
    const std::uint64_t white = board.pieces(forge::WP) | board.pieces(forge::WN) | board.pieces(forge::WB) |
                                board.pieces(forge::WR) | board.pieces(forge::WQ) | board.pieces(forge::WK);
    const std::uint64_t black = board.pieces(forge::BP) | board.pieces(forge::BN) | board.pieces(forge::BB) |
                                board.pieces(forge::BR) | board.pieces(forge::BQ) | board.pieces(forge::BK);
    check(board.occupied(forge::White) == white && board.occupied(forge::Black) == black, "occupancy matches pieces");
    forge::Board rebuilt_board;
    check(rebuilt_board.set_fen(board.fen()), "FEN round trip parses");
    check(rebuilt_board.key() == board.key(), "incremental key matches recomputation");
    check(rebuilt_board.pawn_key() == board.pawn_key(), "incremental pawn key matches recomputation");
    check(rebuilt_board.checkers() == board.checkers(), "incremental checkers match recomputation");
    check(rebuilt_board.in_check(board.side_to_move()) == board.in_check(), "check status is consistent");
}

struct TacticalCase {
    std::string_view label;
    std::string_view fen;
    int depth;
    std::string_view best_move;
    int minimum_score;
    std::string_view alternative_move = "";
};

void check_tactical_case(const TacticalCase& item) {
    forge::Board board;
    check(board.set_fen(item.fen), "tactical FEN parses");
    forge::Searcher searcher(8);
    forge::SearchLimits limits;
    limits.depth = item.depth;
    const forge::SearchInfo result = searcher.search(board, limits);
    const std::string best = forge::Board::move_to_uci(result.best_move);
    if (best != item.best_move && (item.alternative_move.empty() || best != item.alternative_move)) {
        std::cerr << "FAIL: " << item.label << " expected " << item.best_move << " got " << best << '\n';
        ++failures;
    }
    if (result.score < item.minimum_score) {
        std::cerr << "FAIL: " << item.label << " score " << result.score << " below " << item.minimum_score << '\n';
        ++failures;
    }
}

void test_fen_validation() {
    forge::Board board;
    const std::string unchanged = board.fen();
    check(unchanged == forge::Board::StandardStartFen, "start FEN round trip");
    check(!board.set_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1 trailing"), "FEN rejects trailing fields");
    check(board.fen() == unchanged, "rejected FEN leaves the board unchanged");
    check(!board.set_fen("4k3/8/8/8/8/8/8/P3K3 w - - 0 1"), "FEN rejects a pawn on the promotion rank");
    check(!board.set_fen("8/8/8/8/8/8/4k3/4K3 w - - 0 1"), "FEN rejects adjacent kings");
    check(!board.set_fen("4k3/8/8/8/8/8/4R3/4K3 w - - 0 1"), "FEN rejects a previous move that left its king in check");
    check(board.fen() == unchanged, "rejected in-check FEN leaves the board unchanged");
    check(board.set_fen("4k3/4r3/8/8/8/8/8/4K3 w - - 0 1"), "FEN allows the side to move to be in check");
    check(board.in_check(), "incremental checkers detect the FEN check");
    check(!board.set_fen("4k3/8/8/8/8/8/8/4K3 w K - 0 1"), "FEN rejects castling rights without a rook");
    check(!board.set_fen("4k3/8/8/8/8/8/8/4K3 w - e6 0 1"), "FEN rejects an inconsistent en-passant target");
    check(!board.set_fen("4k3/8/3N4/3p4/8/8/8/4K3 w - d6 0 1"), "FEN rejects an occupied en-passant target");
    check(!board.set_fen("4k3/8/8/8/P7/PPPPPPPP/8/4K3 w - - 0 1"), "FEN rejects more than eight pawns for one side");
    check(!board.set_fen("4k3/8/8/8/8/QQ6/PPPPPPPP/4K3 w - - 0 1"), "FEN rejects promoted material without a missing pawn");
    check(board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 65535 65535"), "saturated counters parse");
    play(board, "g8f6");
    check(board.fen().ends_with(" 65535 65535"), "move counters saturate without wrapping");
}

void test_move_generation() {
    forge::Board board;
    check(board.legal_moves().size() == 20, "start position has 20 moves");
    check(board.perft(0) == 1 && board.perft(-1) == 1, "non-positive perft depths terminate at the leaf");
    check_perft(forge::Board::StandardStartFen, 4, 197281, "start perft 4");
    check_perft("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 3, 97862, "kiwipete perft 3");
    check_perft("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 4, 43238, "perft position 3 depth 4");
    check_perft("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 3, 9467, "perft position 4 depth 3");
    check_perft("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 3, 62379, "perft position 5 depth 3");
    check_perft("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 3, 89890, "perft position 6 depth 3");

    check(board.set_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1"), "promotion FEN parses");
    check(board.parse_uci("a7a8q").has_value() && board.parse_uci("a7a8n").has_value(), "promotions are legal");
    check(board.legal_moves(true).size() == 1, "captures-only generation keeps only the queen promotion");
    check(board.set_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"), "en-passant FEN parses");
    check(board.parse_uci("e5d6").has_value(), "en-passant is legal");
    check(board.set_fen("k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"), "pinned en-passant FEN parses");
    check(!board.parse_uci("e5d6").has_value(), "en-passant exposing the king is illegal");

    forge::Board twin;
    check(board.set_fen("4k3/8/8/8/P7/8/8/4K3 b - a3 0 1") && twin.set_fen("4k3/8/8/8/P7/8/8/4K3 b - - 0 1"),
          "non-capturable ep FENs parse");
    check(board.key() == twin.key(), "non-capturable ep target is not hashed");
    check(board.set_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1") && twin.set_fen("4k3/8/8/3pP3/8/8/8/4K3 w - - 0 1"),
          "capturable ep FENs parse");
    check(board.key() != twin.key(), "capturable ep target is hashed");

    // Pseudo-legality must agree with generation, including for garbage moves.
    std::uint64_t random_state = 0x6a09e667f3bcc909ULL;
    for (int game = 0; game < 12; ++game) {
        check(board.set_fen(forge::Board::StandardStartFen), "random walk reset");
        for (int ply = 0; ply < 160; ++ply) {
            const forge::MoveList pseudo = board.pseudo_legal_moves();
            const forge::MoveList legal = board.legal_moves();
            for (const forge::Move move : pseudo) {
                check(board.is_pseudo_legal(move), "generated moves are pseudo-legal");
            }
            for (int probe = 0; probe < 8; ++probe) {
                random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
                const forge::Move garbage{static_cast<std::uint8_t>(random_state % 64),
                                          static_cast<std::uint8_t>((random_state >> 8) % 64),
                                          static_cast<std::uint8_t>((random_state >> 16) % 7),
                                          static_cast<std::uint8_t>((random_state >> 24) % 64)};
                const bool generated = std::find(pseudo.begin(), pseudo.end(), garbage) != pseudo.end();
                check(board.is_pseudo_legal(garbage) == generated, "is_pseudo_legal agrees with generation");
            }
            if (legal.empty()) break;
            random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
            const forge::Move move = legal[static_cast<std::size_t>(random_state % legal.size())];
            const bool predicted_check = board.gives_check(move);
            const std::string before = board.fen();
            forge::Undo undo;
            (void)board.make_move(move, undo);
            check(board.in_check() == predicted_check, "gives_check predicts the resulting check status");
            check_board_consistency(board, "random walk");
            forge::Board copy = board;
            copy.unmake_move(move, undo);
            check(copy.fen() == before && copy.key() == undo.key, "unmake restores the previous position");
            if (board.halfmove_clock() >= 100 || board.is_repetition()) break;
        }
    }
}

void test_repetition_and_null_moves() {
    forge::Board board;
    for (int cycle = 0; cycle < 2; ++cycle) {
        play(board, "g1f3"); play(board, "g8f6"); play(board, "f3g1"); play(board, "f6g8");
    }
    check(board.is_repetition(), "threefold repetition tracked");
    check(board.set_fen(forge::Board::StandardStartFen), "reset for search repetition");
    const std::size_t root = board.history_size() - 1;
    play(board, "g1f3"); play(board, "g8f6"); play(board, "f3g1"); play(board, "f6g8");
    check(!board.is_repetition(), "a single repetition is not a game-level threefold");
    check(board.is_repetition(root), "a repetition of a search position counts as a draw in search");
    check(board.set_fen(board.fen()), "rebuilt position parses");
    check(!board.is_repetition(board.history_size() - 1), "fresh history has no repetition");

    check(board.set_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 99 1"), "null-move FEN parses");
    const std::string before = board.fen();
    const std::uint64_t key = board.key();
    forge::NullUndo null_undo;
    board.make_null_move(null_undo);
    forge::Board rebuilt;
    check(rebuilt.set_fen(board.fen()), "null position parses");
    check(board.key() == rebuilt.key(), "null move key matches recomputation");
    board.unmake_null_move(null_undo);
    check(board.fen() == before && board.key() == key, "null move restores position and key");
}

void test_static_exchange() {
    forge::Board board;
    check(board.set_fen("4k3/8/8/3r4/8/8/8/3QK3 w - - 0 1"), "SEE free-rook FEN parses");
    auto move = board.parse_uci("d1d5");
    check(move.has_value() && board.static_exchange(*move) == 500, "SEE values an undefended rook capture");
    check(board.see_ge(*move, 500) && !board.see_ge(*move, 501), "see_ge brackets the exact gain");
    check(board.set_fen("3qk3/8/8/3p4/8/8/8/3QK3 w - - 0 1"), "SEE defended-pawn FEN parses");
    move = board.parse_uci("d1d5");
    check(move.has_value() && board.static_exchange(*move) == -800, "SEE detects a poisoned pawn capture");
    check(board.set_fen("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"), "SEE Nxe5 FEN parses");
    move = board.parse_uci("f3e5");
    check(move.has_value() && board.static_exchange(*move) == -200, "SEE sees the knight recapture");
    check(board.set_fen("4k3/8/8/8/8/8/4p3/3RK3 b - - 0 1"), "SEE promotion FEN parses");
    move = board.parse_uci("e2d1q");
    check(move.has_value() && board.static_exchange(*move) == 400, "SEE includes promotion gains and the king recapture");
    check(board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"), "SEE quiet FEN parses");
    move = board.parse_uci("e2e4");
    check(move.has_value() && board.static_exchange(*move) == 0, "quiet moves to safe squares have zero exchange value");
    check(board.set_fen("4k3/8/8/4p3/8/8/8/3NK3 w - - 0 1"), "SEE hanging knight FEN parses");
    move = board.parse_uci("d1f2");
    check(move.has_value() && board.see_ge(*move, 0), "knight to an unattacked square is not losing");
    check(board.set_fen("4k3/8/8/8/4p3/8/8/2N1K3 w - - 0 1"), "SEE attacked square FEN parses");
    move = board.parse_uci("c1d3");
    check(move.has_value() && !board.see_ge(*move, 0) && board.static_exchange(*move) == -300,
          "quiet move into a pawn attack loses the piece");
}

void test_evaluation() {
    forge::Board board;
    check(forge::Searcher::evaluate(board) > 0 && forge::Searcher::evaluate(board) < 40,
          "start position evaluation is a small tempo bonus");
    const std::array<std::string_view, 5> fens{
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    };
    forge::Board mirror;
    for (const std::string_view fen : fens) {
        check(board.set_fen(fen), "evaluation FEN parses");
        check(mirror.set_fen(mirror_fen(fen)), "mirrored evaluation FEN parses");
        if (forge::Searcher::evaluate(board) != forge::Searcher::evaluate(mirror)) {
            std::cerr << "FAIL: evaluation is not colour symmetric for " << fen << '\n';
            ++failures;
        }
    }
    check(board.set_fen("6k1/8/8/8/8/8/8/Q3K3 w - - 0 1"), "material evaluation FEN parses");
    check(forge::Searcher::evaluate(board) > 500, "queen advantage evaluates decisively");
    check(board.set_fen("7k/8/4P3/8/8/8/8/4K3 w - - 0 1"), "advanced passer FEN parses");
    const int advanced = forge::Searcher::evaluate(board);
    check(board.set_fen("7k/8/8/8/8/8/4P3/4K3 w - - 0 1"), "home passer FEN parses");
    check(advanced > forge::Searcher::evaluate(board), "advanced passed pawn gains value");
    check(board.set_fen("4k3/8/8/8/8/8/8/2B1K3 w - - 0 1"), "lone bishop FEN parses");
    check(forge::Searcher::evaluate(board) < 60, "a lone minor piece is scaled down to a draw");
    check(board.set_fen("4k3/8/8/8/8/8/8/3QK3 w - - 0 1"), "lone queen FEN parses");
    check(forge::Searcher::evaluate(board) > 500, "a lone queen still wins");
}

void test_search() {
    constexpr std::array<TacticalCase, 8> cases{{
        {"white back-rank mate", "6k1/5ppp/8/8/8/8/8/4R1K1 w - - 0 1", 3, "e1e8", forge::MateValue - 1},
        {"smothered knight mate", "6rk/6pp/7N/8/8/8/8/6K1 w - - 0 1", 3, "h6f7", forge::MateValue - 1},
        {"queen sacrifice mate", "r6k/6pp/4Q2N/8/8/8/8/6K1 w - - 0 1", 8, "e6g8", forge::MateInMaxPly, "h6f7"},
        {"royal fork", "3q4/6k1/8/8/5N2/8/8/6K1 w - - 0 1", 6, "f4e6", -50},
        {"promotion mate", "k7/2P5/1K6/8/8/8/8/8 w - - 0 1", 3, "c7c8q", forge::MateValue - 1},
        {"black back-rank mate", "4r1k1/8/8/8/8/8/5PPP/6K1 b - - 0 1", 3, "e8e1", forge::MateValue - 1},
        {"scholar's mate", "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", 4, "h5f7", forge::MateValue - 1},
        {"WAC 001", "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1", 12, "g3g6", forge::MateValue - 3},
    }};
    for (const TacticalCase& item : cases) check_tactical_case(item);

    forge::Board board;
    forge::SearchLimits limits;
    limits.depth = 8;
    forge::Searcher searcher(8);
    check(board.set_fen("8/8/8/3k4/8/4K3/4P3/8 w - - 0 1"), "pawn-only FEN parses");
    (void)searcher.search(board, limits);
    check(forge::SearcherTestProbe::null_tries(searcher) == 0, "null pruning is disabled in pawn-only endings");
    check(board.set_fen(forge::Board::StandardStartFen), "start FEN parses");
    searcher.clear();
    (void)searcher.search(board, limits);
    check(forge::SearcherTestProbe::null_tries(searcher) > 0 && forge::SearcherTestProbe::null_cutoffs(searcher) > 0,
          "null pruning is active with non-pawn material");

    // searchmoves restrictions.
    forge::SearchLimits restricted;
    restricted.depth = 4;
    restricted.search_moves_specified = true;
    restricted.search_moves.push_back(*board.parse_uci("a2a3"));
    forge::SearchInfo info = searcher.search(board, restricted);
    check(forge::Board::move_to_uci(info.best_move) == "a2a3", "searchmoves restricts the root move");
    check(!info.restricted_root_empty, "non-empty restriction is not flagged as empty");
    restricted.search_moves.clear();
    restricted.search_moves.push_back(forge::Move{0, 56, 0, 0});
    info = searcher.search(board, restricted);
    check(info.restricted_root_empty && info.best_move.is_none(), "empty restriction yields a no-result flag");

    // Terminal roots.
    check(board.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"), "mated root parses");
    info = searcher.search(board, limits);
    check(info.best_move.is_none() && info.score == -forge::MateValue, "mated root reports mate 0");
    check(board.set_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"), "stalemated root parses");
    info = searcher.search(board, limits);
    check(info.best_move.is_none() && info.score == 0, "stalemated root reports a draw");
    check(board.set_fen("7k/8/8/8/8/8/8/KR6 w - - 100 1"), "rule-50 root parses");
    info = searcher.search(board, limits);
    check(!info.best_move.is_none() && info.score == 0, "rule-50 root is drawn but still moves");

    // Explicit zero node budget returns immediately with a legal move.
    check(board.set_fen(forge::Board::StandardStartFen), "start FEN parses again");
    forge::SearchLimits zero_nodes;
    zero_nodes.nodes_specified = true;
    zero_nodes.nodes = 0;
    info = searcher.search(board, zero_nodes);
    check(!info.best_move.is_none() && info.nodes == 0, "zero node budget returns a legal move without searching");

    // Node limits are honoured closely.
    forge::SearchLimits node_limited;
    node_limited.nodes_specified = true;
    node_limited.nodes = 5000;
    info = searcher.search(board, node_limited);
    check(info.nodes <= 5100 && info.nodes >= 4000, "node limit bounds the search");
    check(!info.best_move.is_none(), "node-limited search returns a move");

    // Mate scores come back correctly through the transposition table.
    check(board.set_fen("r4q1k/p2bR1rp/2p2Q1N/5p2/5p2/2P5/PP3PPP/R5K1 w - - 0 1"), "WAC 008 parses");
    forge::SearchLimits mate_limits;
    mate_limits.depth = 14;
    forge::Searcher mate_searcher(16);
    info = mate_searcher.search(board, mate_limits);
    check(forge::Board::move_to_uci(info.best_move) == "e7f7", "WAC 008 finds Rxf7");
    check(info.score > 300, "WAC 008 is recognised as winning");
}

void test_threads() {
    forge::Board board;
    forge::Searcher searcher(16, 4);
    check(searcher.threads() == 4, "searcher reports its thread count");
    forge::SearchLimits limits;
    limits.depth = 12;
    forge::SearchInfo info = searcher.search(board, limits);
    check(!info.best_move.is_none() && info.depth == 12, "multi-threaded search completes the requested depth");
    check(info.nodes > 0, "multi-threaded search reports nodes");
    // A second search must not be blocked by the helper shutdown of the first.
    info = searcher.search(board, limits);
    check(info.depth == 12, "helper shutdown does not leave the stop flag raised");
    check(board.set_fen("6k1/5ppp/8/8/8/8/8/4R1K1 w - - 0 1"), "threaded mate FEN parses");
    limits.depth = 6;
    info = searcher.search(board, limits);
    check(forge::Board::move_to_uci(info.best_move) == "e1e8" && info.score == forge::MateValue - 1,
          "multi-threaded search finds the mate");
    searcher.set_threads(1);
    check(searcher.threads() == 1, "thread count can be reduced");
    info = searcher.search(board, limits);
    check(forge::Board::move_to_uci(info.best_move) == "e1e8", "single-threaded search still works after resizing");
}

void test_nnue() {
    if (!forge::nnue::available()) return;
    // Incremental accumulator updates must agree with a full refresh along
    // random games, including castling, promotions and en passant.
    forge::Board board;
    std::uint64_t random_state = 0x243f6a8885a308d3ULL;
    int mismatches = 0;
    for (int game = 0; game < 6; ++game) {
        check(board.set_fen(forge::Board::StandardStartFen), "nnue walk reset");
        forge::nnue::Accumulator incremental;
        forge::nnue::refresh(board, incremental);
        for (int ply = 0; ply < 160; ++ply) {
            const forge::MoveList legal = board.legal_moves();
            if (legal.empty()) break;
            random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
            const forge::Move move = legal[static_cast<std::size_t>(random_state % legal.size())];
            const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
            forge::Undo undo;
            (void)board.make_move(move, undo);
            forge::nnue::Accumulator next;
            forge::nnue::update(incremental, next, dirty);
            forge::nnue::Accumulator fresh;
            forge::nnue::refresh(board, fresh);
            if (forge::nnue::evaluate(board, next) != forge::nnue::evaluate(board, fresh)) ++mismatches;
            incremental = next;
            if (board.halfmove_clock() >= 100 || board.is_repetition()) break;
        }
    }
    check(mismatches == 0, "incremental NNUE accumulators match full refreshes");
    check(board.set_fen("6k1/8/8/8/8/8/8/Q3K3 w - - 0 1"), "nnue material FEN parses");
    forge::nnue::Accumulator acc;
    forge::nnue::refresh(board, acc);
    check(forge::nnue::evaluate(board, acc) > 300, "NNUE sees a decisive material advantage");
    check(board.set_fen("q3k3/8/8/8/8/8/8/6K1 b - - 0 1"), "nnue mirrored FEN parses");
    forge::nnue::refresh(board, acc);
    check(forge::nnue::evaluate(board, acc) > 300, "NNUE evaluates from the side to move's perspective");
}

void test_transposition_table() {
    forge::TranspositionTable tt(1);
    bool hit = true;
    forge::TTEntry* entry = tt.probe(0x123456789abcdefULL, hit);
    check(!hit && entry != nullptr, "empty table misses");
    tt.store(entry, 0x123456789abcdefULL, 123, 45, forge::Move{12, 28, 0, 0}, 7, forge::BoundExact, true);
    entry = tt.probe(0x123456789abcdefULL, hit);
    check(hit && entry->score == 123 && entry->eval == 45 && entry->depth == 7 && entry->bound() == forge::BoundExact &&
              entry->pv() && entry->move == forge::Move{12, 28, 0, 0},
          "stored entry is retrieved intact");
    tt.store(entry, 0x123456789abcdefULL, 50, 45, forge::Move::none(), 2, forge::BoundUpper, false);
    entry = tt.probe(0x123456789abcdefULL, hit);
    check(hit && entry->depth == 7 && entry->move == forge::Move{12, 28, 0, 0},
          "a much shallower bound does not overwrite a deep exact entry in the same search");
    tt.clear();
    entry = tt.probe(0x123456789abcdefULL, hit);
    check(!hit, "clear empties the table");
}

} // namespace

int main() {
    test_fen_validation();
    test_move_generation();
    test_repetition_and_null_moves();
    test_static_exchange();
    test_evaluation();
    test_transposition_table();
    test_search();
    test_threads();
    test_nnue();
    if (failures == 0) {
        std::cout << "All tests passed\n";
        return 0;
    }
    std::cerr << failures << " test failure(s)\n";
    return 1;
}
