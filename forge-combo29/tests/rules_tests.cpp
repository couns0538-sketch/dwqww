// Movegen, repetition, terminal-position and draw-rule checks. These do not
// depend on the network: failures here are illegal moves or wrong results.
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>
#include <string>
#include <string_view>
#include <vector>

namespace {

int failures = 0;

void check(bool okay, const std::string& message) {
    if (!okay) {
        ++failures;
        std::cerr << "FAIL: " << message << '\n';
    }
}

forge::Board board_from(std::string_view fen) {
    forge::Board board;
    std::string error;
    const bool parsed = board.set_fen(fen, &error);
    check(parsed, std::string(fen) + " parses: " + error);
    return board;
}

void check_perft(std::string_view fen, const std::vector<std::uint64_t>& counts) {
    forge::Board board = board_from(fen);
    for (int depth = 1; depth <= static_cast<int>(counts.size()); ++depth) {
        const auto nodes = board.perft(depth);
        check(nodes == counts[static_cast<std::size_t>(depth - 1)],
              std::string(fen) + " perft " + std::to_string(depth) + " got " + std::to_string(nodes) +
                  " expected " + std::to_string(counts[static_cast<std::size_t>(depth - 1)]));
    }
}

void check_make_unmake(std::string_view fen, int depth) {
    forge::Board board = board_from(fen);
    const auto saved_fen = board.fen();
    const auto saved_key = board.key();
    auto walk = [&](auto&& self, int remaining) -> void {
        const auto here = board.fen();
        const auto key = board.key();
        if (remaining == 0) return;
        const auto moves = board.legal_moves();
        for (const forge::Move move : moves) {
            forge::Undo undo;
            if (!board.make_move(move, undo)) {
                check(false, "legal move rejected: " + forge::Board::move_to_uci(move));
                return;
            }
            self(self, remaining - 1);
            board.unmake_move(move, undo);
            check(board.fen() == here && board.key() == key,
                  "unmake restored " + forge::Board::move_to_uci(move) + " from " + std::string(fen));
        }
    };
    walk(walk, depth);
    check(board.fen() == saved_fen && board.key() == saved_key, "make/unmake walk restored " + std::string(fen));
}

void play(forge::Board& board, const char* uci) {
    const auto move = board.parse_uci(uci);
    check(move.has_value(), std::string("legal ") + uci);
    if (!move) return;
    forge::Undo undo;
    check(board.make_move(*move, undo), std::string("make ") + uci);
}

void check_repetition() {
    forge::Board board = board_from(forge::Board::StandardStartFen);
    play(board, "g1f3");
    play(board, "b8c6");
    play(board, "f3g1");
    play(board, "c6b8");
    check(!board.is_repetition(), "twofold is not a game draw");
    check(!board.is_repetition(board.history_size() - 1), "a fresh root at the second occurrence is not a draw");
    check(board.is_repetition(0), "repeating the root position is a search draw");
    play(board, "g1f3");
    play(board, "b8c6");
    play(board, "f3g1");
    play(board, "c6b8");
    check(board.is_repetition(), "threefold is a game draw");
}

void check_ep_and_castle() {
    // En passant opens the rank between the white king and the black rook.
    forge::Board pinned = board_from("8/8/8/K2pP2r/8/8/8/4k3 w - d6 0 1");
    bool saw_ep = false;
    for (const forge::Move move : pinned.pseudo_legal_moves()) {
        if ((move.flags & forge::EnPassant) == 0U) continue;
        saw_ep = true;
        check(!pinned.is_legal(move), "en passant that discovers check is illegal");
        check(!pinned.parse_uci("e5d6").has_value(), "UCI parser rejects the pinned en passant");
    }
    check(saw_ep, "pinned en passant is generated as pseudo-legal");

    forge::Board open = board_from("8/8/8/K2pP3/8/8/8/4k3 w - d6 0 1");
    const auto ep = open.parse_uci("e5d6");
    check(ep.has_value() && (ep->flags & forge::EnPassant) != 0U, "unpinned en passant is legal");

    forge::Board castle = board_from("4k3/8/8/8/8/8/5r2/R3K2R w KQ - 0 1");
    check(!castle.parse_uci("e1g1").has_value(), "cannot castle through check");
    check(castle.parse_uci("e1c1").has_value(), "queenside castle is legal");
}

void check_move_oracle(std::string_view fen) {
    forge::Board board = board_from(fen);
    const std::string saved = board.fen();
    const std::uint64_t key = board.key();
    check(key == board.compute_key(), "set_fen key matches a full recompute");
    if (!board.in_check()) {
        forge::NullUndo null_undo;
        board.make_null_move(null_undo);
        check(board.key() == board.compute_key(), "null-move key matches a full recompute");
        board.unmake_null_move(null_undo);
        check(board.key() == key && board.fen() == saved, "null-move unmake restored the position");
    }
    for (const forge::Move move : board.pseudo_legal_moves()) {
        const bool checks = board.gives_check(move);
        const bool legal = board.is_legal(move);
        forge::Undo undo;
        (void)board.make_move(move, undo);
        check(board.key() == board.compute_key() && board.pawn_key() == board.compute_pawn_key(),
              "incremental keys match a full recompute");
        const bool opponent_in_check = board.in_check();
        const forge::Color mover = forge::opposite(board.side_to_move());
        const bool exposed = board.square_attacked(board.king_square(mover), board.side_to_move());
        board.unmake_move(move, undo);
        check(board.fen() == saved && board.key() == key, "oracle unmake restored the position");
        check(checks == opponent_in_check, "gives_check matches the position after the move");
        if (!move.is_castle()) {
            check(legal == !exposed, "is_legal matches king safety");
        }
    }
}

void check_search_rules() {
    using namespace forge;
    auto search_fen = [](std::string_view fen, int depth, int threads) {
        Board board = board_from(fen);
        SearchLimits limits;
        limits.depth = depth;
        Searcher searcher(16, threads);
        return searcher.search(board, limits);
    };

    const SearchInfo stalemate = search_fen("k7/2Q5/1K6/8/8/8/8/8 b - - 0 1", 2, 1);
    check(stalemate.score == 0 && stalemate.best_move.is_none(), "stalemate scores 0 and has no move");

    const SearchInfo mated = search_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 100 40", 2, 1);
    check(mated.score == -MateValue && mated.best_move.is_none(), "checkmate still loses when the 50-move clock is 100");

    const SearchInfo clock100 = search_fen("8/8/4k3/8/8/3K1R2/8/8 w - - 100 80", 2, 1);
    check(clock100.score == 0 && clock100.nodes == 0 && !clock100.best_move.is_none(),
          "50-move clock 100 is a draw without searching");
    check(board_from("8/8/4k3/8/8/3K1R2/8/8 w - - 100 80").is_legal(clock100.best_move),
          "50-move draw still returns a legal move");

    const SearchInfo clock99 = search_fen("8/8/4k3/8/8/3K1R2/8/8 w - - 99 80", 2, 1);
    check(clock99.score == 0 && clock99.nodes > 0, "clock 99 is searched and drawn by the move that reaches 100");

    const SearchInfo bare = search_fen("8/8/4k3/8/8/3K4/8/8 w - - 0 1", 2, 1);
    check(bare.score == 0 && bare.nodes == 0, "king versus king is a draw without searching");

    const SearchInfo mate99 = search_fen("6k1/4Q3/6K1/8/8/8/8/8 w - - 99 40", 3, 1);
    check(is_mate_score(mate99.score) && mate99.score > 0, "mate in one still wins when the clock is 99");

    const SearchInfo promote = search_fen("7k/4P3/6K1/8/8/8/8/8 w - - 0 1", 3, 1);
    check(is_mate_score(promote.score) && promote.score > 0, "promotion mate is a positive mate score");
    check(promote.best_move.is_promotion() && promote.best_move.promotion == Queen,
          "promotion mate is a queen promotion");

    const SearchInfo mate = search_fen("6k1/4Q3/6K1/8/8/8/8/8 w - - 0 1", 3, 1);
    check(is_mate_score(mate.score) && mate.score > 0, "mate in one is a positive mate score");
    Board after = board_from("6k1/4Q3/6K1/8/8/8/8/8 w - - 0 1");
    check(after.is_legal(mate.best_move), "mating move is legal");
    if (after.is_legal(mate.best_move)) {
        Undo undo;
        (void)after.make_move(mate.best_move, undo);
        check(after.in_check() && after.legal_moves().empty(), "mating move checkmates");
    }

    // KRK mate in 3. With the network on, two fresh searches used to report
    // e8e4 and a centipawn score or a mate in 10. See search.cpp.
    {
        Board krk = board_from("4R3/8/8/k2K4/8/8/8/8 w - - 0 1");
        const auto key = krk.parse_uci("d5c5");
        check(key.has_value(), "KRK key move parses");
        if (key.has_value()) {
            SearchLimits limits;
            limits.depth = 14;
            Searcher searcher(16, 2);
            int misses = 0;
            for (int run = 0; run < 200; ++run) {
                searcher.clear();
                const SearchInfo info = searcher.search(krk, limits);
                const int mate_moves = (MateValue - info.score + 1) / 2;
                const bool short_mate = is_mate_score(info.score) && info.score > 0 && mate_moves <= 3;
                if (!short_mate || info.best_move != *key) ++misses;
            }
            check(misses == 0, "two threads keep the KRK mate in 3");
        }
    }

    // One thread, no clear() between roots. History left by the first search
    // used to make the second miss mate in 3 and play the rook sideways.
    {
        Board krk = board_from("4R3/8/8/k2K4/8/8/8/8 w - - 0 1");
        const auto key = krk.parse_uci("d5c5");
        check(key.has_value(), "warm KRK key move parses");
        if (key.has_value()) {
            Searcher searcher(16, 1);
            const char* poisons[] = {
                "8/8/8/8/3k4/8/3K4/3Q4 w - - 0 1",
                "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
                "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
            };
            for (const char* fen : poisons) {
                SearchLimits poison_limits;
                poison_limits.depth = 9;
                (void)searcher.search(board_from(fen), poison_limits);
                SearchLimits limits;
                limits.depth = 10;
                const SearchInfo info = searcher.search(krk, limits);
                const int mate_moves = (MateValue - info.score + 1) / 2;
                const bool short_mate = is_mate_score(info.score) && info.score > 0 && mate_moves <= 3;
                check(short_mate && info.best_move == *key,
                      std::string("warm one-thread KRK mate in 3 after ") + fen);
            }
            SearchLimits shallow;
            shallow.depth = 3;
            (void)searcher.search(krk, shallow);
            SearchLimits limits;
            limits.depth = 10;
            const SearchInfo info = searcher.search(krk, limits);
            const int mate_moves = (MateValue - info.score + 1) / 2;
            const bool short_mate = is_mate_score(info.score) && info.score > 0 && mate_moves <= 3;
            check(short_mate && info.best_move == *key, "warm one-thread KRK mate in 3 after a shallow search of itself");
        }
    }

    const SearchInfo mate_threads = search_fen("6k1/4Q3/6K1/8/8/8/8/8 w - - 0 1", 3, 2);
    check(is_mate_score(mate_threads.score) && mate_threads.score > 0, "two threads still report mate in one");
    Board threaded = board_from("6k1/4Q3/6K1/8/8/8/8/8 w - - 0 1");
    check(threaded.is_legal(mate_threads.best_move), "two-thread mate move is legal");

    // Qg6 is legal and leaves Black with no move and no check. The score is
    // the quiescence result of that quiet move, so a missed stalemate would
    // show up as a queen-advantage score.
    Board horizon = board_from("7k/5K2/8/6Q1/8/8/8/8 w - - 0 1");
    const auto quiet = horizon.parse_uci("g5g6");
    check(quiet.has_value(), "g5g6 is legal in the horizon fixture");
    if (quiet.has_value()) {
        SearchLimits limits;
        limits.depth = 1;
        limits.search_moves_specified = true;
        limits.search_moves = {*quiet};
        Searcher searcher(16, 1);
        const SearchInfo info = searcher.search(horizon, limits);
        check(info.score == 0 && info.best_move == *quiet, "quiet move into stalemate scores 0");
    }

    auto nodes_zero = [](std::string_view fen) {
        Board board = board_from(fen);
        SearchLimits limits;
        limits.depth = 8;
        limits.nodes = 0;
        limits.nodes_specified = true;
        Searcher searcher(16, 1);
        return searcher.search(board, limits);
    };
    const SearchInfo zero_stalemate = nodes_zero("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1");
    check(zero_stalemate.depth == 0 && zero_stalemate.score == 0 && zero_stalemate.best_move.is_none(),
          "nodes 0 at stalemate does not report a searched depth");
    const SearchInfo zero_mate = nodes_zero("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1");
    check(zero_mate.depth == 0 && zero_mate.score == -MateValue && zero_mate.best_move.is_none(),
          "nodes 0 at checkmate keeps the mate score and reports no depth");
    Board start;
    (void)start.set_fen(Board::StandardStartFen);
    const auto e2e4 = start.parse_uci("e2e4");
    check(e2e4.has_value(), "e2e4 parses from the start position");
    if (e2e4.has_value()) {
        SearchLimits restricted;
        restricted.nodes = 0;
        restricted.nodes_specified = true;
        restricted.search_moves_specified = true;
        restricted.search_moves = {*e2e4};
        const SearchInfo zero_live = Searcher(16, 1).search(start, restricted);
        check(zero_live.depth == 0 && zero_live.best_move == *e2e4,
              "nodes 0 on a live root still returns the requested move");
    }
}

} // namespace

int main() {
    check_perft(forge::Board::StandardStartFen, {20, 400, 8902, 197281, 4865609});
    check_perft("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
                {48, 2039, 97862, 4085603});
    check_perft("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", {14, 191, 2812, 43238, 674624});
    check_perft("n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1", {24, 496, 9483, 182838});
    check_make_unmake("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 2);
    check_make_unmake("8/2p5/3p4/KP5r/1R3pPk/8/4P3/8 b - g3 0 1", 2);
    check_repetition();
    check_ep_and_castle();
    check_move_oracle(forge::Board::StandardStartFen);
    check_move_oracle("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
    check_move_oracle("8/2p5/3p4/KP5r/1R3pPk/8/4P3/8 b - g3 0 1");
    check_move_oracle("n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1");
    check_move_oracle("8/8/8/K2pP2r/8/8/8/4k3 w - d6 0 1");
    check_move_oracle("4k3/8/8/8/8/8/5r2/R3K2R w KQ - 0 1");
    check_move_oracle("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1");
    check_search_rules();
    std::cout << "rules failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
