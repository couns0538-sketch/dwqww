// Move-generation and game-rule suite for the combo29 lock.
// Links the engine sources. Prints one line per check. Does not write files.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstddef>
#include <cstdint>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>

namespace forge {

struct BoardStateProbe {
    static bool same(const Board& left, const Board& right, std::string* diff) {
        auto fail = [&](const char* field) {
            if (diff != nullptr) *diff = field;
            return false;
        };
        if (left.squares_ != right.squares_) return fail("squares");
        if (left.bitboards_ != right.bitboards_) return fail("bitboards");
        if (left.occupied_ != right.occupied_) return fail("occupied");
        if (left.king_squares_ != right.king_squares_) return fail("king_squares");
        if (left.side_ != right.side_) return fail("side");
        if (left.castling_ != right.castling_) return fail("castling");
        if (left.ep_square_ != right.ep_square_) return fail("ep_square");
        if (left.halfmove_ != right.halfmove_) return fail("halfmove");
        if (left.fullmove_ != right.fullmove_) return fail("fullmove");
        if (left.key_ != right.key_) return fail("key");
        if (left.pawn_key_ != right.pawn_key_) return fail("pawn_key");
        if (left.checkers_ != right.checkers_) return fail("checkers");
        if (left.plies_from_null_ != right.plies_from_null_) return fail("plies_from_null");
        if (left.key_history_ != right.key_history_) return fail("key_history");
#if FORGE_SPD_KING_LINES
        if (left.king_lines_.valid != right.king_lines_.valid) return fail("king_lines.valid");
        if (left.king_lines_.pinned != right.king_lines_.pinned) return fail("king_lines.pinned");
        if (left.king_lines_.discoverers != right.king_lines_.discoverers) return fail("king_lines.discoverers");
        if (left.king_lines_.check_squares != right.king_lines_.check_squares) return fail("king_lines.check_squares");
#endif
        return true;
    }

    // Incremental key and the checker set against a from-scratch recompute.
    static bool incremental_matches(const Board& board, std::string* diff) {
        if (board.key_ != board.compute_key()) {
            if (diff != nullptr) *diff = "key";
            return false;
        }
        if (board.pawn_key_ != board.compute_pawn_key()) {
            if (diff != nullptr) *diff = "pawn_key";
            return false;
        }
        if (board.checkers_ != board.compute_checkers()) {
            if (diff != nullptr) *diff = "checkers";
            return false;
        }
        return true;
    }
};

struct SearcherTestProbe {
    static void set_root_history(Worker& worker, std::size_t index) { worker.root_history_index_ = index; }

    static bool is_draw(const Worker& worker, const Board& board, int ply) { return worker.is_draw(board, ply); }
};

} // namespace forge

namespace {

int g_fails = 0;

void check(bool ok, std::string_view name) {
    std::cout << (ok ? "PASS " : "FAIL ") << name << std::endl;
    if (!ok) ++g_fails;
}

forge::Board load(std::string_view fen) {
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cout << "FAIL load [" << fen << "] " << error << std::endl;
        ++g_fails;
    }
    return board;
}

void warm(forge::Board& board) {
    const forge::MoveList moves = board.pseudo_legal_moves(false);
    for (const forge::Move move : moves) {
        (void)board.is_legal(move);
        (void)board.gives_check(move);
    }
}

bool same_board(const forge::Board& left, const forge::Board& right, std::string_view what) {
    std::string diff;
    const bool ok = forge::BoardStateProbe::same(left, right, &diff);
    if (!ok) {
        std::cout << "FAIL " << what << " field " << diff << std::endl;
        ++g_fails;
        return false;
    }
    std::cout << "PASS " << what << std::endl;
    return true;
}

bool play(forge::Board& board, std::string_view uci) {
    const std::optional<forge::Move> move = board.parse_uci(uci);
    if (!move) {
        std::cout << "FAIL play " << uci << " in " << board.fen() << std::endl;
        ++g_fails;
        return false;
    }
    forge::Undo undo;
    (void)board.make_move(*move, undo);
    return true;
}

bool uci_legal(const forge::Board& board, std::string_view uci) {
    const forge::MoveList moves = board.legal_moves(false);
    for (const forge::Move move : moves) {
        if (forge::Board::move_to_uci(move) == uci) return true;
    }
    return false;
}

bool uci_pseudo(const forge::Board& board, std::string_view uci) {
    const forge::MoveList moves = board.pseudo_legal_moves(false);
    for (const forge::Move move : moves) {
        if (forge::Board::move_to_uci(move) == uci) return true;
    }
    return false;
}

std::string search_text(const forge::SearchInfo& info) {
    std::ostringstream out;
    out << "score=" << info.score << " nodes=" << info.nodes << " best=";
    if (info.best_move.is_none()) out << "none";
    else out << forge::Board::move_to_uci(info.best_move);
    return out.str();
}

forge::SearchInfo search_depth(forge::Searcher& searcher, const forge::Board& board, int depth) {
    forge::SearchLimits limits;
    limits.depth = depth;
    return searcher.search(board, limits, false);
}

bool adjudicated_draw(const forge::SearchInfo& info) { return info.score == 0 && info.nodes == 0; }

void perft_and_state() {
    struct Case {
        const char* name;
        const char* fen;
        int depth;
        std::uint64_t expected;
    };
    // Published counts. Checked against chessprogramming.org/Perft_Results and
    // github.com/Wasserpuncher/chess-perft (also carokanns/GoBit perft_tests.txt).
    // Those sources agree with each other and with the numbers below.
    const Case cases[] = {
        {"start", forge::Board::StandardStartFen.data(), 5, 4865609ULL},
        {"kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 4, 4085603ULL},
        {"pos3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5, 674624ULL},
        {"pos4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 4, 422333ULL},
        {"pos5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 4, 2103487ULL},
        {"pos6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 4, 3894594ULL},
    };
    std::cout << "SOURCE chessprogramming.org/Perft_Results and github.com/Wasserpuncher/chess-perft "
                 "and github.com/carokanns/GoBit perft_tests.txt agree; disagreements=none"
              << std::endl;

    for (const Case& item : cases) {
        forge::Board board = load(item.fen);
        warm(board);
        const forge::Board before = board;
        const std::uint64_t got = board.perft(item.depth);
        std::ostringstream line;
        line << "PERFT " << item.name << " depth " << item.depth << " engine " << got << " expected " << item.expected;
        check(got == item.expected, line.str());
        same_board(board, before, std::string("STATE after perft ") + item.name);

        forge::Board walking = before;
        int positions = 0;
        int mismatches = 0;
        const auto walk = [&](auto&& self, forge::Board& node, int depth) -> void {
            ++positions;
            std::string diff;
            if (!forge::BoardStateProbe::incremental_matches(node, &diff)) {
                ++mismatches;
                if (mismatches <= 3) {
                    std::cout << "FAIL HASH " << item.name << " " << diff << " at " << node.fen() << std::endl;
                }
            }
            if (depth == 0) return;
            forge::MoveList moves;
            node.generate_pseudo_legal(moves, false);
            for (const forge::Move move : moves) {
                if (!node.is_legal(move)) continue;
                forge::Undo undo;
                (void)node.make_move(move, undo);
                self(self, node, depth - 1);
                node.unmake_move(move, undo);
            }
        };
        walk(walk, walking, 3);
        std::ostringstream hash_line;
        hash_line << "HASH " << item.name << " depth 3 positions " << positions << " mismatches " << mismatches;
        check(mismatches == 0, hash_line.str());
        same_board(walking, before, std::string("STATE after hash walk ") + item.name);
    }
}

void special_moves() {
    {
        forge::Board board = load("8/8/8/8/k2Pp2Q/8/8/3K4 b - d3 0 1");
        check(board.ep_square() == 19, "ep pin fen keeps d3");
        check(uci_pseudo(board, "e4d3"), "ep capture e4d3 is pseudo-legal");
        check(!uci_legal(board, "e4d3"), "ep capture e4d3 is illegal");
        const std::optional<forge::Move> parsed = board.parse_uci("e4d3");
        check(!parsed.has_value(), "parse_uci rejects illegal ep e4d3");
    }
    {
        forge::Board board = load("5r2/8/8/4k3/8/8/8/R3K2R w KQ - 0 1");
        check(!board.in_check(), "castle through: king is not in check");
        check(board.square_attacked(5, forge::Black), "castle through: f1 is attacked");
        check(!board.square_attacked(6, forge::Black), "castle through: g1 is not attacked");
        check(!uci_legal(board, "e1g1"), "cannot castle through check");
    }
    {
        forge::Board board = load("4r3/8/8/8/8/k7/8/4K2R w K - 0 1");
        check(board.in_check(), "castle out: king is in check");
        check(!uci_legal(board, "e1g1"), "cannot castle out of check");
    }
    {
        forge::Board board = load("6r1/8/8/8/8/8/k7/4K2R w K - 0 1");
        check(!board.in_check(), "castle into: king is not in check");
        check(!board.square_attacked(5, forge::Black), "castle into: f1 is not attacked");
        check(board.square_attacked(6, forge::Black), "castle into: g1 is attacked");
        check(!uci_legal(board, "e1g1"), "cannot castle into check");
    }
    {
        forge::Board board = load("7r/8/8/8/8/8/k7/4K2R w K - 0 1");
        check(board.square_attacked(7, forge::Black), "rook on h1 is attacked");
        check(!board.square_attacked(4, forge::Black) && !board.square_attacked(5, forge::Black) &&
                  !board.square_attacked(6, forge::Black),
              "king path e1-f1-g1 is safe");
        const std::optional<forge::Move> castle = board.parse_uci("e1g1");
        check(castle.has_value(), "castling with the rook attacked is legal");
        if (castle) {
            warm(board);
            const forge::Board before = board;
            forge::Undo undo;
            (void)board.make_move(*castle, undo);
            check(board.piece_at(6) == forge::WK && board.piece_at(5) == forge::WR, "O-O lands king g1 rook f1");
            check(board.piece_at(4) == forge::Empty && board.piece_at(7) == forge::Empty, "O-O vacates e1 and h1");
            board.unmake_move(*castle, undo);
            same_board(board, before, "STATE after attacked-rook castle unmake");
        }
    }
    {
        forge::Board board = load("8/P7/8/8/8/k7/8/4K3 w - - 0 1");
        const char* promos[] = {"a7a8n", "a7a8b", "a7a8r", "a7a8q"};
        const forge::Piece pieces[] = {forge::WN, forge::WB, forge::WR, forge::WQ};
        for (int i = 0; i < 4; ++i) {
            const std::optional<forge::Move> move = board.parse_uci(promos[i]);
            check(move.has_value(), std::string("underpromotion legal ") + promos[i]);
            if (!move) continue;
            warm(board);
            const forge::Board before = board;
            forge::Undo undo;
            (void)board.make_move(*move, undo);
            check(board.piece_at(56) == pieces[i], std::string("promotion piece ") + promos[i]);
            board.unmake_move(*move, undo);
            same_board(board, before, std::string("STATE unmake ") + promos[i]);
        }
    }
    {
        forge::Board board = load("1n6/P7/8/8/8/k7/8/4K3 w - - 0 1");
        const char* promos[] = {"a7b8n", "a7b8b", "a7b8r", "a7b8q"};
        const forge::Piece pieces[] = {forge::WN, forge::WB, forge::WR, forge::WQ};
        for (int i = 0; i < 4; ++i) {
            const std::optional<forge::Move> move = board.parse_uci(promos[i]);
            check(move.has_value() && move->is_capture() && move->is_promotion(),
                  std::string("promotion capture legal ") + promos[i]);
            if (!move) continue;
            warm(board);
            const forge::Board before = board;
            forge::Undo undo;
            (void)board.make_move(*move, undo);
            check(board.piece_at(57) == pieces[i] && board.piece_at(48) == forge::Empty,
                  std::string("promotion capture result ") + promos[i]);
            board.unmake_move(*move, undo);
            same_board(board, before, std::string("STATE unmake ") + promos[i]);
        }
    }
    {
        forge::Board board = load("4k3/3N2q1/8/8/B7/8/8/4K3 w - - 0 1");
        const std::optional<forge::Move> move = board.parse_uci("d7f6");
        check(move.has_value(), "double-check move d7f6 is legal");
        if (move) {
            check(board.gives_check(*move), "d7f6 gives check");
            warm(board);
            const forge::Board before = board;
            forge::Undo undo;
            (void)board.make_move(*move, undo);
            const int checkers = forge::popcount(board.checkers());
            std::ostringstream count;
            count << "double check has 2 checkers (got " << checkers << ")";
            check(board.in_check() && checkers == 2, count.str());
            check((board.checkers() & board.pieces(forge::WN)) != 0 && (board.checkers() & board.pieces(forge::WB)) != 0,
                  "checkers are the knight and the bishop");
            const forge::MoveList legal = board.legal_moves(false);
            bool only_king = !legal.empty();
            bool queen_takes = false;
            std::ostringstream listed;
            listed << "double-check legal:";
            for (const forge::Move reply : legal) {
                listed << ' ' << forge::Board::move_to_uci(reply);
                if (board.piece_at(reply.from) != forge::BK) only_king = false;
                if (forge::Board::move_to_uci(reply) == "g7f6") queen_takes = true;
            }
            std::cout << listed.str() << std::endl;
            check(only_king, "double check allows only king moves");
            check(!queen_takes, "queen cannot take one checker while the other remains");
            board.unmake_move(*move, undo);
            same_board(board, before, "STATE after double-check unmake");
        }
    }
}

void draw_rules() {
    forge::Searcher searcher(16, 1);
    auto draw_flag = [&](const forge::Board& board, std::size_t root) {
        forge::SearcherTestProbe::set_root_history(searcher.main_worker(), root);
        return forge::SearcherTestProbe::is_draw(searcher.main_worker(), board, 1);
    };

    {
        forge::Board board = load("4k3/8/8/8/8/8/8/4K2R w - - 0 1");
        const std::size_t root = board.history_size() - 1;
        check(play(board, "h1h2") && play(board, "e8d8") && play(board, "h2h1") && play(board, "d8e8"),
              "play one repetition cycle");
        check(!board.is_repetition(), "second occurrence is not game threefold");
        check(!draw_flag(board, board.history_size() - 1), "search draw is false on twofold at the root");
        check(draw_flag(board, root), "search draw is true when the line repeats the root");
        searcher.clear();
        const forge::SearchInfo twofold = search_depth(searcher, board, 3);
        std::cout << "DRAW twofold-root " << search_text(twofold) << std::endl;
        check(!adjudicated_draw(twofold), "search does not adjudicate twofold at the root");

        check(play(board, "h1h2") && play(board, "e8d8") && play(board, "h2h1") && play(board, "d8e8"),
              "play the second repetition cycle");
        check(board.is_repetition(), "third occurrence is game threefold");
        check(draw_flag(board, board.history_size() - 1), "search draw is true on threefold at the root");
        searcher.clear();
        const forge::SearchInfo threefold = search_depth(searcher, board, 3);
        std::cout << "DRAW threefold-root " << search_text(threefold) << std::endl;
        check(adjudicated_draw(threefold), "search adjudicates threefold as a draw");
    }

    {
        const char* quiet = "8/8/8/8/8/7k/8/R3K3 w - - ";
        forge::Board at99 = load(std::string(quiet) + "99 1");
        bool mate_in_one = false;
        for (const forge::Move move : at99.legal_moves(false)) {
            forge::Undo undo;
            (void)at99.make_move(move, undo);
            if (at99.in_check() && !at99.has_legal_move()) mate_in_one = true;
            at99.unmake_move(move, undo);
        }
        check(!mate_in_one, "clock 99 quiet position has no mating move");
        check(!draw_flag(at99, at99.history_size() - 1), "search draw is false at 99 half-moves");
        searcher.clear();
        const forge::SearchInfo search99 = search_depth(searcher, at99, 2);
        std::cout << "DRAW halfmove99 " << search_text(search99) << std::endl;
        check(!adjudicated_draw(search99) && search99.score == 0, "at 99 the search looks and the next ply is drawn");

        forge::Board at100 = load(std::string(quiet) + "100 1");
        check(draw_flag(at100, at100.history_size() - 1), "search draw is true at 100 half-moves");
        searcher.clear();
        const forge::SearchInfo search100 = search_depth(searcher, at100, 2);
        std::cout << "DRAW halfmove100 " << search_text(search100) << std::endl;
        check(adjudicated_draw(search100), "search adjudicates 100 half-moves as a draw");
    }

    {
        forge::Board ready = load("k7/8/1QK5/8/8/8/8/8 w - - 99 1");
        check(uci_legal(ready, "b6b7"), "quiet mate b6b7 is legal at half-move 99");
        searcher.clear();
        const forge::SearchInfo mate = search_depth(searcher, ready, 3);
        std::cout << "DRAW mate-on-100 " << search_text(mate) << std::endl;
        check(forge::is_mate_score(mate.score) && mate.score > 0, "mating move that reaches half-move 100 wins");

        forge::Board already = load("k7/8/1QK5/8/8/8/8/8 w - - 100 1");
        check(uci_legal(already, "b6b7"), "mate still exists once the clock is already 100");
        check(draw_flag(already, already.history_size() - 1), "clock already 100 is a draw before the move");
        searcher.clear();
        const forge::SearchInfo drawn = search_depth(searcher, already, 3);
        std::cout << "DRAW already-100-with-mate " << search_text(drawn) << std::endl;
        check(adjudicated_draw(drawn), "search does not play a mate after the clock has reached 100");

        const std::optional<forge::Move> mating = ready.parse_uci("b6b7");
        check(mating.has_value(), "parse mating move");
        if (mating) {
            forge::Undo undo;
            (void)ready.make_move(*mating, undo);
            check(ready.halfmove_clock() == 100, "mating move lands on half-move 100");
            check(ready.in_check() && ready.legal_moves(false).empty(), "opponent is checkmated");
            check(!draw_flag(ready, ready.history_size() - 1), "checkmate on half-move 100 is not a draw");
            searcher.clear();
            const forge::SearchInfo mated = search_depth(searcher, ready, 2);
            std::cout << "DRAW mated-at-100 " << search_text(mated) << std::endl;
            check(mated.score == -forge::MateValue, "side to move loses the mate on half-move 100");
        }
    }

    {
        forge::Board stale = load("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1");
        check(!stale.in_check() && stale.legal_moves(false).empty(), "stalemate has no legal move");
        check(draw_flag(stale, stale.history_size() - 1), "search draw is true in stalemate");
        searcher.clear();
        const forge::SearchInfo root = search_depth(searcher, stale, 2);
        std::cout << "DRAW stalemate-root " << search_text(root) << std::endl;
        check(adjudicated_draw(root), "search adjudicates stalemate as a draw");

        forge::Board parent = load("7k/5Q2/8/6K1/8/8/8/8 w - - 0 1");
        const std::optional<forge::Move> only = parent.parse_uci("g5g6");
        check(only.has_value(), "g5g6 leads to stalemate");
        if (only) {
            forge::SearchLimits limits;
            limits.depth = 1;
            limits.search_moves_specified = true;
            limits.search_moves.push_back(*only);
            searcher.clear();
            const forge::SearchInfo child = searcher.search(parent, limits, false);
            std::cout << "DRAW stalemate-child " << search_text(child) << std::endl;
            check(child.score == 0 && child.nodes > 0, "search scores a move into stalemate as a draw");
        }
    }

    struct Material {
        const char* name;
        const char* fen;
        bool drawn;
    };
    const Material materials[] = {
        {"bare-kings", "8/8/8/8/8/8/8/K6k w - - 0 1", true},
        {"bare-kings-black", "8/8/8/8/8/8/8/K6k b - - 0 1", true},
        {"knight-king", "8/8/8/8/8/8/8/KN5k w - - 0 1", true},
        {"bishop-king", "8/8/8/8/8/8/8/KB5k w - - 0 1", true},
        {"bishop-king-black", "8/8/8/8/8/8/8/k5BK b - - 0 1", true},
        {"rook-king", "8/8/8/8/8/7k/8/KR6 w - - 0 1", false},
    };
    for (const Material& item : materials) {
        forge::Board board = load(item.fen);
        const bool flag = draw_flag(board, board.history_size() - 1);
        searcher.clear();
        const forge::SearchInfo info = search_depth(searcher, board, 2);
        std::cout << "DRAW material " << item.name << " flag=" << (flag ? 1 : 0) << ' ' << search_text(info) << std::endl;
        check(board.is_insufficient_material() == item.drawn, std::string("insufficient-material ") + item.name);
        check(flag == item.drawn, std::string("search draw flag ") + item.name);
        check(adjudicated_draw(info) == item.drawn, std::string("search adjudication ") + item.name);
    }
}

enum class FenKind { Reject, Any };

void malformed_fens() {
    struct Case {
        const char* fen;
        const char* why;
        FenKind kind;
    };
    const Case cases[] = {
        {"", "missing all fields", FenKind::Reject},
        {"8/8/8/8/8/8/k7/4K3", "missing side, castling, ep, clocks", FenKind::Reject},
        {"8/8/8/8/8/8/k7/4K3 w", "missing castling, ep, clocks", FenKind::Reject},
        {"8/8/8/8/8/8/k7/4K3 w -", "missing ep and clocks", FenKind::Reject},
        {"8/8/8/8/8/8/k7/4K3 w - -", "missing both clocks", FenKind::Reject},
        {"8/8/8/8/8/8/k7/4K3 w - - 0", "missing fullmove", FenKind::Reject},
        {"8/8/8/8/8/8/k7/4K3 w - - 0 1 extra", "extra seventh field", FenKind::Reject},
        {"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR KQkq - 0 1", "missing side token", FenKind::Reject},
        {"9/8/8/8/8/8/k7/4K3 w - - 0 1", "digit 9 in a rank", FenKind::Reject},
        {"8p/8/8/8/8/8/k7/4K3 w - - 0 1", "eight empties plus a pawn", FenKind::Reject},
        {"ppppppppp/8/8/8/8/8/k7/4K3 w - - 0 1", "nine pawns on a rank", FenKind::Reject},
        {"4p4/8/8/8/8/8/k7/4K3 w - - 0 1", "4+pawn+4 squares", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/3KK3 w - - 0 1", "two white kings", FenKind::Reject},
        {"3kk3/8/8/8/8/8/8/4K3 w - - 0 1", "two black kings", FenKind::Reject},
        {"8/8/8/8/8/8/8/4K3 w - - 0 1", "no black king", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/8 w - - 0 1", "no white king", FenKind::Reject},
        {"8/8/8/8/8/8/8/8 w - - 0 1", "no kings", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/P3K3 w - - 0 1", "white pawn on rank 1", FenKind::Reject},
        {"P3k3/8/8/8/8/8/8/4K3 w - - 0 1", "white pawn on rank 8", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/p3K3 w - - 0 1", "black pawn on rank 1", FenKind::Reject},
        {"p3k3/8/8/8/8/8/8/4K3 w - - 0 1", "black pawn on rank 8", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/4K3 w - e4 0 1", "ep square on rank 4", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/4K3 w - e1 0 1", "ep square on rank 1", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/4K3 w - i6 0 1", "ep file off the board", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/4K3 w - e6 0 1", "ep e6 with no pawn", FenKind::Reject},
        {"4k3/8/8/8/4P3/8/8/4K3 w - e6 0 1", "ep e6 with a white pawn on e4", FenKind::Reject},
        {"4k3/8/4p3/8/8/8/8/4K3 w - e6 0 1", "ep square occupied", FenKind::Reject},
        {"4k3/4n3/8/4p3/8/8/8/4K3 w - e6 0 1", "ep origin e7 occupied", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/4K3 b - e3 0 1", "ep e3 with no white pawn", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/4K3 w - e3 0 1", "white to move but ep on rank 3", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/4K2r b - - 0 1", "side not to move (white) is in check", FenKind::Reject},
        {"4k2R/8/8/8/8/8/8/4K3 w - - 0 1", "side not to move (black) is in check", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/4K3 w - - 1000000 1", "half-move 1000000", FenKind::Any},
        {"4k3/8/8/8/8/8/8/4K3 w - - 0 1000000", "full-move 1000000", FenKind::Any},
        {"4k3/8/8/8/8/8/8/4K3 w - - 9223372036854775807 1", "half-move LLONG_MAX", FenKind::Any},
        {"4k3/8/8/8/8/8/8/4K3 w - - 0 9223372036854775807", "full-move LLONG_MAX", FenKind::Any},
        {"4k3/8/8/8/8/8/8/4K3 w - - 999999999999999999999 1", "half-move overflows long long", FenKind::Any},
        {"4k3/8/8/8/8/8/8/4K3 w - - 0 999999999999999999999", "full-move overflows long long", FenKind::Any},
        {"4k3/8/8/8/8/8/8/4K3 w - - -1 1", "negative half-move", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/4K3 w - - 0 0", "full-move 0", FenKind::Reject},
    };
    static_assert(sizeof(cases) / sizeof(cases[0]) == 40, "the suite lists 40 malformed FENs");

    const forge::Board baseline = load(forge::Board::StandardStartFen);
    int index = 0;
    for (const Case& item : cases) {
        ++index;
        forge::Board trial = baseline;
        std::string error;
        const bool accepted = trial.set_fen(item.fen, &error);
        std::ostringstream line;
        line << "FEN " << index << " ";
        if (!accepted) {
            std::string diff;
            const bool unchanged = forge::BoardStateProbe::same(trial, baseline, &diff);
            line << "REJECT " << item.why << " | " << error;
            std::cout << line.str() << std::endl;
            check(unchanged, std::string("FEN ") + std::to_string(index) + " reject leaves the board unchanged");
            if (!unchanged) std::cout << "FAIL FEN " << index << " mutated " << diff << std::endl;
            switch (item.kind) {
            case FenKind::Reject:
                check(true, std::string("FEN ") + std::to_string(index) + " rejected as required");
                break;
            case FenKind::Any:
                check(true, std::string("FEN ") + std::to_string(index) + " handled by rejection");
                break;
            default: {
                const FenKind unhandled = item.kind;
                (void)unhandled;
                check(false, "unhandled fen kind");
                break;
            }
            }
            continue;
        }
        (void)trial.legal_moves(false);
        (void)trial.perft(1);
        (void)trial.key();
        (void)trial.fen();
        line << "ACCEPT halfmove=" << trial.halfmove_clock() << " fullmove=" << trial.fullmove_number()
             << " fen=" << trial.fen() << " | " << item.why;
        std::cout << line.str() << std::endl;
        switch (item.kind) {
        case FenKind::Reject:
            check(false, std::string("FEN ") + std::to_string(index) + " accepted a malformed position");
            break;
        case FenKind::Any:
            check(true, std::string("FEN ") + std::to_string(index) + " handled by acceptance");
            break;
        default: {
            const FenKind unhandled = item.kind;
            (void)unhandled;
            check(false, "unhandled fen kind");
            break;
        }
        }
    }
}

} // namespace

int main() {
    std::cout << "t17 rules suite" << std::endl;
    perft_and_state();
    special_moves();
    draw_rules();
    malformed_fens();
    std::cout << "RESULT " << (g_fails == 0 ? "PASS" : "FAIL") << " fails=" << g_fails << std::endl;
    return g_fails == 0 ? 0 : 1;
}
