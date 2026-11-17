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
            const char* expected_replies[] = {"e8e7", "e8f7", "e8d8", "e8f8"};
            bool seen[4] = {};
            int extra = 0;
            std::ostringstream listed;
            listed << "double-check legal:";
            for (const forge::Move reply : legal) {
                const std::string uci = forge::Board::move_to_uci(reply);
                listed << ' ' << uci;
                bool known = false;
                for (int i = 0; i < 4; ++i) {
                    if (uci == expected_replies[i]) {
                        seen[i] = true;
                        known = true;
                    }
                }
                if (!known) ++extra;
            }
            std::cout << listed.str() << std::endl;
            const bool exact = extra == 0 && seen[0] && seen[1] && seen[2] && seen[3] && legal.size() == 4;
            check(exact, "double check replies are exactly e8e7 e8f7 e8d8 e8f8");
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

// Positions the first pass did not stand on their own: queenside castling,
// a file pin on en passant, a null move, a pure discovered check, and a
// capture or pawn move that resets a clock of 99.
void further_edges() {
    auto roundtrip = [](forge::Board& board, const forge::Move& move, std::string_view name) {
        warm(board);
        const forge::Board before = board;
        forge::Undo undo;
        (void)board.make_move(move, undo);
        std::string diff;
        const bool keys = forge::BoardStateProbe::incremental_matches(board, &diff);
        check(keys, std::string("key after ") + std::string(name) + (keys ? "" : " mismatch " + diff));
        board.unmake_move(move, undo);
        same_board(board, before, std::string("STATE unmake ") + std::string(name));
    };

    {
        forge::Board board = load("3r4/2k5/8/8/8/8/8/R3K2R w Q - 0 1");
        check(!board.in_check() && board.square_attacked(3, forge::Black), "queenside through: d1 attacked, king safe");
        check(!uci_legal(board, "e1c1"), "cannot castle queenside through check");
        forge::Move crafted{};
        crafted.from = 4;
        crafted.to = 2;
        crafted.flags = forge::QueenCastle;
        check(!board.is_pseudo_legal(crafted), "crafted queenside castle through check is not pseudo-legal");
    }
    {
        forge::Board board = load("2r5/1k6/8/8/8/8/8/R3K2R w Q - 0 1");
        check(!board.in_check() && board.square_attacked(2, forge::Black) && !board.square_attacked(3, forge::Black),
              "queenside into: c1 attacked, d1 safe");
        check(!uci_legal(board, "e1c1"), "cannot castle queenside into check");
    }
    {
        forge::Board board = load("4r3/2k5/8/8/8/8/8/R3K2R w Q - 0 1");
        check(board.in_check(), "queenside out: king is in check");
        check(!uci_legal(board, "e1c1"), "cannot castle queenside out of check");
    }
    {
        forge::Board board = load("r7/2k5/8/8/8/8/8/R3K2R w Q - 0 1");
        check(board.square_attacked(0, forge::Black), "a1 rook is attacked");
        check(!board.square_attacked(2, forge::Black) && !board.square_attacked(3, forge::Black) && !board.in_check(),
              "queenside king path c1-d1 is safe");
        const std::optional<forge::Move> castle = board.parse_uci("e1c1");
        check(castle.has_value(), "queenside castle with the rook attacked is legal");
        if (castle) {
            warm(board);
            const forge::Board before = board;
            forge::Undo undo;
            (void)board.make_move(*castle, undo);
            check(board.piece_at(2) == forge::WK && board.piece_at(3) == forge::WR, "O-O-O lands king c1 rook d1");
            check(board.piece_at(0) == forge::Empty && board.piece_at(4) == forge::Empty, "O-O-O vacates a1 and e1");
            std::string diff;
            const bool keys = forge::BoardStateProbe::incremental_matches(board, &diff);
            check(keys, std::string("key after O-O-O rook attacked") + (keys ? "" : " mismatch " + diff));
            board.unmake_move(*castle, undo);
            same_board(board, before, "STATE unmake O-O-O rook attacked");
        }
    }
    {
        forge::Board board = load("1r6/2k5/8/8/8/8/8/R3K2R w Q - 0 1");
        check(board.square_attacked(1, forge::Black), "b1 is attacked");
        check(!board.square_attacked(2, forge::Black) && !board.square_attacked(3, forge::Black), "c1 and d1 are safe");
        const std::optional<forge::Move> castle = board.parse_uci("e1c1");
        check(castle.has_value() && board.is_pseudo_legal(*castle) && board.is_legal(*castle),
              "queenside castle is legal when only b1 is attacked");
        if (castle) roundtrip(board, *castle, "O-O-O b1 attacked");
    }
    {
        forge::Board through = load("r3k2r/8/8/8/8/8/5R2/4K3 b k - 0 1");
        check(!through.in_check() && through.square_attacked(61, forge::White), "black kingside through: f8 attacked");
        check(!uci_legal(through, "e8g8"), "black cannot castle through check");
        forge::Board into = load("r3k2r/8/8/8/8/8/6R1/4K3 b k - 0 1");
        check(into.square_attacked(62, forge::White) && !into.square_attacked(61, forge::White), "black kingside into: g8 attacked");
        check(!uci_legal(into, "e8g8"), "black cannot castle into check");
        forge::Board out = load("r3k2r/8/8/8/8/8/4R3/4K3 b k - 0 1");
        check(out.in_check() && !uci_legal(out, "e8g8"), "black cannot castle out of check");
        forge::Board rook = load("r3k2r/8/8/8/8/8/7R/4K3 b k - 0 1");
        check(rook.square_attacked(63, forge::White) && uci_legal(rook, "e8g8"), "black castle with h8 rook attacked is legal");
        forge::Board queen = load("r3k3/8/8/8/8/8/8/1R2K3 b q - 0 1");
        check(queen.square_attacked(57, forge::White) && uci_legal(queen, "e8c8"),
              "black queenside castle is legal when only b8 is attacked");
    }
    {
        forge::Board illegal = load("3r4/8/8/3Pp3/8/8/8/3K3k w - e6 0 1");
        check(illegal.ep_square() == 44, "file-pin ep square is e6");
        check(uci_pseudo(illegal, "d5e6"), "file-pin ep d5e6 is pseudo-legal");
        check(!uci_legal(illegal, "d5e6"), "file-pin ep d5e6 is illegal");
        forge::Board legal = load("r7/8/8/3Pp3/8/8/8/3K3k w - e6 0 1");
        const std::optional<forge::Move> ep = legal.parse_uci("d5e6");
        check(ep.has_value(), "ep d5e6 is legal when the king is not on the opened file");
        if (ep) roundtrip(legal, *ep, "legal ep d5e6");
        forge::Board black = load("4k3/8/8/8/3Pp3/8/8/4R2K b - d3 0 1");
        check(uci_pseudo(black, "e4d3") && !uci_legal(black, "e4d3"), "black ep e4d3 is illegal when it opens the e-file");
    }
    {
        forge::Board board = load("4r3/8/8/8/8/8/4N3/4K2k w - - 0 1");
        check(uci_pseudo(board, "e2d4") && !uci_legal(board, "e2d4"), "pinned knight e2d4 is illegal");
        check(uci_pseudo(board, "e2c3") && !uci_legal(board, "e2c3"), "pinned knight e2c3 is illegal");
        bool knight_moved = false;
        for (const forge::Move move : board.legal_moves(false)) {
            const std::string uci = forge::Board::move_to_uci(move);
            if (uci.size() >= 2 && uci[0] == 'e' && uci[1] == '2') knight_moved = true;
        }
        check(!knight_moved, "pinned knight has no legal move");
    }
    {
        forge::Board board = load("4k3/8/8/8/8/8/4N3/4RK2 w - - 0 1");
        const std::optional<forge::Move> move = board.parse_uci("e2d4");
        check(move.has_value() && board.gives_check(*move), "e2d4 is a pure discovered check");
        if (move) {
            forge::Undo undo;
            (void)board.make_move(*move, undo);
            const int checkers = forge::popcount(board.checkers());
            check(board.in_check() && checkers == 1 && (board.checkers() & board.pieces(forge::WR)) != 0 &&
                      (board.checkers() & board.pieces(forge::WN)) == 0,
                  "discovered check is the rook alone");
            board.unmake_move(*move, undo);
        }
    }
    {
        forge::Board board = load("3k4/8/8/8/8/8/8/R3K3 w Q - 0 1");
        const std::optional<forge::Move> castle = board.parse_uci("e1c1");
        check(castle.has_value() && board.gives_check(*castle), "O-O-O gives check along the d-file");
        if (castle) {
            forge::Undo undo;
            (void)board.make_move(*castle, undo);
            check(board.in_check() && (board.checkers() & board.pieces(forge::WR)) != 0, "rook on d1 is the checker");
            check(forge::BoardStateProbe::incremental_matches(board, nullptr), "key after checking castle");
            board.unmake_move(*castle, undo);
        }
    }
    {
        forge::Board board = load("r7/8/8/3Pp3/8/8/8/3K3k w - e6 0 1");
        warm(board);
        const forge::Board before = board;
        forge::NullUndo undo;
        board.make_null_move(undo);
        check(board.side_to_move() == forge::Black, "null move passes the turn");
        check(board.ep_square() < 0, "null move clears en passant");
        check(board.halfmove_clock() == 1, "null move increments the half-move clock");
        check(forge::BoardStateProbe::incremental_matches(board, nullptr), "key after null move matches a recompute");
        board.unmake_null_move(undo);
        same_board(board, before, "STATE after null-move unmake");
    }
    {
        forge::Board board = load("4k3/8/8/8/8/8/8/4K2R w - - 0 1");
        check(play(board, "h1h2") && play(board, "e8d8") && play(board, "h2h1") && play(board, "d8e8"),
              "cycle once before the null-move chain");
        forge::Searcher searcher(16, 1);
        const std::size_t root = board.history_size() - 1;
        forge::SearcherTestProbe::set_root_history(searcher.main_worker(), root);
        check(!forge::SearcherTestProbe::is_draw(searcher.main_worker(), board, 1), "twofold before the null moves is not a draw");
        forge::NullUndo first;
        forge::NullUndo second;
        board.make_null_move(first);
        board.make_null_move(second);
        check(board.side_to_move() == forge::White, "two null moves restore the side to move");
        forge::SearcherTestProbe::set_root_history(searcher.main_worker(), root);
        check(!forge::SearcherTestProbe::is_draw(searcher.main_worker(), board, 1),
              "a null move breaks the repetition chain the search uses");
        board.unmake_null_move(second);
        board.unmake_null_move(first);
        check(!board.is_repetition(), "unmaking the null moves restores twofold, not threefold");
    }
    {
        forge::Board board = load("8/8/8/8/8/7k/P7/4K3 w - - 99 1");
        const std::optional<forge::Move> push = board.parse_uci("a2a3");
        const std::optional<forge::Move> quiet = board.parse_uci("e1e2");
        check(push.has_value() && quiet.has_value(), "clock 99 has a pawn push and a quiet king move");
        if (push && quiet) {
            forge::Searcher searcher(16, 1);
            forge::Undo undo;
            (void)board.make_move(*push, undo);
            check(board.halfmove_clock() == 0, "a pawn move resets the half-move clock");
            forge::SearcherTestProbe::set_root_history(searcher.main_worker(), board.history_size() - 1);
            check(!forge::SearcherTestProbe::is_draw(searcher.main_worker(), board, 1), "the position after the pawn move is not a 50-move draw");
            check(forge::BoardStateProbe::incremental_matches(board, nullptr), "key after the pawn reset");
            board.unmake_move(*push, undo);
            (void)board.make_move(*quiet, undo);
            check(board.halfmove_clock() == 100, "a quiet move from 99 lands on 100");
            forge::SearcherTestProbe::set_root_history(searcher.main_worker(), board.history_size() - 1);
            check(forge::SearcherTestProbe::is_draw(searcher.main_worker(), board, 1), "the quiet reply at 100 is a draw");
            board.unmake_move(*quiet, undo);
            const std::optional<forge::Move> twice = board.parse_uci("a2a4");
            check(twice.has_value(), "a2a4 double push is legal");
            if (twice) {
                (void)board.make_move(*twice, undo);
                check(board.ep_square() == 16, "double push sets ep a3 even with no capturer");
                check(board.halfmove_clock() == 0, "double push resets the clock");
                check(forge::BoardStateProbe::incremental_matches(board, nullptr), "dead ep square is not hashed");
                std::string fen = board.fen();
                check(fen.find(" a3 ") != std::string::npos, "fen still records the dead ep square");
                board.unmake_move(*twice, undo);
            }
        }
    }
    {
        forge::Board board = load("n7/8/8/8/8/7k/8/R3K3 w - - 99 1");
        const std::optional<forge::Move> capture = board.parse_uci("a1a8");
        check(capture.has_value() && capture->is_capture(), "a1a8 captures the knight at clock 99");
        if (capture) {
            forge::Undo undo;
            (void)board.make_move(*capture, undo);
            check(board.halfmove_clock() == 0 && board.piece_at(56) == forge::WR, "capture resets the clock and leaves the rook");
            forge::Searcher searcher(16, 1);
            searcher.clear();
            const forge::SearchInfo info = search_depth(searcher, board, 2);
            std::cout << "DRAW capture-resets-99 " << search_text(info) << std::endl;
            check(!adjudicated_draw(info) && info.score != 0, "a capture on ply 99 is not a 50-move draw");
        }
    }
}

enum class FenKind { Reject, ClampHalf, ClampFull };

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
        {"4k3/8/8/8/8/8/8/4K3 w - - 1000000 1", "half-move 1000000", FenKind::ClampHalf},
        {"4k3/8/8/8/8/8/8/4K3 w - - 0 1000000", "full-move 1000000", FenKind::ClampFull},
        {"4k3/8/8/8/8/8/8/4K3 w - - 9223372036854775807 1", "half-move LLONG_MAX", FenKind::ClampHalf},
        {"4k3/8/8/8/8/8/8/4K3 w - - 0 9223372036854775807", "full-move LLONG_MAX", FenKind::ClampFull},
        {"4k3/8/8/8/8/8/8/4K3 w - - 999999999999999999999 1", "half-move overflows long long", FenKind::Reject},
        {"4k3/8/8/8/8/8/8/4K3 w - - 0 999999999999999999999", "full-move overflows long long", FenKind::Reject},
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
            case FenKind::ClampHalf:
            case FenKind::ClampFull:
                check(false, std::string("FEN ") + std::to_string(index) + " rejected a clock that must be clamped");
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
        case FenKind::ClampHalf:
            check(trial.halfmove_clock() == 65535 && trial.fullmove_number() == 1,
                  std::string("FEN ") + std::to_string(index) + " clamps the half-move clock to 65535");
            break;
        case FenKind::ClampFull:
            check(trial.halfmove_clock() == 0 && trial.fullmove_number() == 65535,
                  std::string("FEN ") + std::to_string(index) + " clamps the full-move number to 65535");
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

// Two workers share the transposition table. The result is the main worker's.
// Helpers are joined before search returns. This only checks that a second
// thread runs, returns, and does not play an illegal move. Node counts are
// not printed: the helper races the table, so the count is not a signature.
void multi_thread() {
    std::cout << "MULTI-THREAD" << std::endl;
    forge::Searcher searcher(16, 2);
    check(searcher.threads() == 2, "searcher keeps two workers");

    forge::Board mate = load("k7/8/1QK5/8/8/8/8/8 w - - 0 1");
    searcher.clear();
    const forge::SearchInfo mate_info = search_depth(searcher, mate, 2);
    const std::string mate_uci = forge::Board::move_to_uci(mate_info.best_move);
    std::cout << "THREADS mate depth2 score=" << mate_info.score << " best=" << mate_uci << std::endl;
    check(mate.is_legal(mate_info.best_move), "two-thread mate search returns a legal move");
    check(mate_uci == "b6b7" && forge::is_mate_score(mate_info.score), "two threads still find the mate in one");

    forge::Board start = load(forge::Board::StandardStartFen);
    searcher.clear();
    const forge::SearchInfo start_info = search_depth(searcher, start, 3);
    const std::string start_uci = forge::Board::move_to_uci(start_info.best_move);
    std::cout << "THREADS start depth3 score=" << start_info.score << " best=" << start_uci << std::endl;
    check(start_info.nodes > 0, "two-thread start search visits nodes");
    check(start.is_legal(start_info.best_move), "two-thread start search returns a legal move");
}

} // namespace

int main() {
    std::cout << "t17 rules suite" << std::endl;
    perft_and_state();
    special_moves();
    further_edges();
    draw_rules();
    multi_thread();
    malformed_fens();
    std::cout << "RESULT " << (g_fails == 0 ? "PASS" : "FAIL") << " fails=" << g_fails << std::endl;
    return g_fails == 0 ? 0 : 1;
}
