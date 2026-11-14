// DrawJitter checks for repetition and fifty-move leaves.
// Build beside the engine sources (not via CMakeLists). One thread, 16 MB hash.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>

namespace forge {

struct SearcherTestProbe {
    static void set_nodes(Worker& worker, std::uint64_t nodes) { worker.local_nodes_ = nodes; }
    static int leaf(const Worker& worker, const Board& board) { return worker.draw_leaf_score(board); }
};

} // namespace forge

namespace {

int g_fails = 0;

void expect(bool ok, std::string_view name) {
    std::cout << (ok ? "PASS " : "FAIL ") << name << std::endl;
    if (!ok) ++g_fails;
}

forge::Board board_from(std::string_view fen) {
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cout << "FAIL fen " << fen << " " << error << std::endl;
        ++g_fails;
    }
    return board;
}

forge::SearchInfo search_at(const forge::Board& board, int depth) {
    forge::Searcher searcher(16);
    forge::SearchLimits limits;
    limits.depth = depth;
    return searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
}

bool move_is_legal(const forge::Board& board, forge::Move move) {
    const forge::MoveList legal = board.legal_moves();
    if (move.is_none()) return legal.empty();
    for (const forge::Move candidate : legal) {
        if (candidate == move) return true;
    }
    return false;
}

void check_formula() {
    forge::Searcher searcher(16);
    forge::Worker& worker = searcher.main_worker();
    const forge::Board fifty = board_from("8/8/8/4k3/8/4K3/8/4R3 w - - 100 1");
    const forge::Board quiet = board_from("8/8/8/4k3/8/4K3/8/4R3 w - - 10 1");
    const forge::Board bare = board_from("8/8/8/4k3/8/4K3/8/8 w - - 10 1");

    forge::DrawJitter = 0;
    forge::SearcherTestProbe::set_nodes(worker, 3);
    expect(forge::SearcherTestProbe::leaf(worker, fifty) == 0, "span 0 fifty leaf is 0");

    forge::DrawJitter = 8;
    bool walked = true;
    int previous = 0;
    for (std::uint64_t nodes = 0; nodes < 24; ++nodes) {
        forge::SearcherTestProbe::set_nodes(worker, nodes);
        const int score = forge::SearcherTestProbe::leaf(worker, fifty);
        const int width = 8 * 2 + 1;
        const int expected = static_cast<int>(nodes % static_cast<std::uint64_t>(width)) - 8;
        if (score != expected || score < -8 || score > 8) walked = false;
        if (nodes == 1 && score == previous) walked = false;
        if (forge::SearcherTestProbe::leaf(worker, quiet) != 0) walked = false;
        if (forge::SearcherTestProbe::leaf(worker, bare) != 0) walked = false;
        previous = score;
    }
    expect(walked, "fifty leaf walks the node count inside +/-8");
    expect(forge::SearcherTestProbe::leaf(worker, quiet) == 0, "quiet leaf stays 0");
    expect(forge::SearcherTestProbe::leaf(worker, bare) == 0, "insufficient leaf stays 0");
}

bool play_uci(forge::Board& board, std::string_view text) {
    const std::optional<forge::Move> move = board.parse_uci(text);
    if (!move.has_value()) return false;
    forge::Undo undo;
    return board.make_move(*move, undo);
}

void check_repetition() {
    forge::Board board = board_from("8/8/8/4k3/8/4K3/8/4R3 w - - 0 1");
    static constexpr std::string_view moves[] = {
        "e1a1", "e5e6", "a1e1", "e6e5", "e1a1", "e5e6", "a1e1", "e6e5",
    };
    bool played = true;
    for (const std::string_view text : moves) played = played && play_uci(board, text);
    expect(played && board.is_repetition(), "shuffling the rook reaches threefold");
    forge::DrawJitter = 0;
    const forge::SearchInfo off = search_at(board, 2);
    forge::DrawJitter = 8;
    const forge::SearchInfo on = search_at(board, 2);
    expect(off.score == 0, "threefold root is 0 when DrawJitter is 0");
    expect(on.score == -8, "threefold root uses the zero-node leaf score");
    expect(move_is_legal(board, on.best_move), "threefold best move is legal");
}

void check_search_scores() {
    const forge::Board fifty = board_from("8/8/8/4k3/8/4K3/8/4R3 w - - 100 1");
    const forge::Board almost = board_from("8/8/8/4k3/8/4K3/8/4R3 w - - 99 1");
    const forge::Board mate = board_from("7k/8/6K1/8/8/8/8/R7 w - - 0 1");
    const forge::Board mate_late = board_from("7k/8/6K1/8/8/8/8/R7 w - - 99 1");
    const forge::Board mated = board_from("k5R1/8/1K6/8/8/8/8/8 b - - 100 1");
    const forge::Board stale = board_from("k7/2Q5/1K6/8/8/8/8/8 b - - 0 1");
    const forge::Board stale_late = board_from("k7/2Q5/1K6/8/8/8/8/8 b - - 100 1");
    const forge::Board bare = board_from("8/8/8/4k3/8/4K3/8/8 w - - 40 1");

    forge::DrawJitter = 0;
    const forge::SearchInfo fifty_off = search_at(fifty, 3);
    const forge::SearchInfo almost_off = search_at(almost, 2);
    const forge::SearchInfo mate_off = search_at(mate, 3);
    const forge::SearchInfo mate_late_off = search_at(mate_late, 3);
    const forge::SearchInfo mated_off = search_at(mated, 2);
    const forge::SearchInfo stale_off = search_at(stale, 2);
    expect(fifty_off.score == 0, "fifty root is 0 when DrawJitter is 0");
    expect(almost_off.score == 0, "move into fifty is 0 when DrawJitter is 0");
    expect(forge::is_mate_score(mate_off.score) && mate_off.score > 0, "mate in one with DrawJitter 0");
    expect(mated_off.score == -forge::MateValue, "checkmate on half-move 100 with DrawJitter 0");
    expect(stale_off.score == 0, "stalemate is 0 when DrawJitter is 0");

    forge::DrawJitter = 8;
    const forge::SearchInfo fifty_on = search_at(fifty, 3);
    const forge::SearchInfo almost_on = search_at(almost, 2);
    const forge::SearchInfo mate_on = search_at(mate, 3);
    const forge::SearchInfo mate_late_on = search_at(mate_late, 3);
    const forge::SearchInfo mated_on = search_at(mated, 2);
    const forge::SearchInfo stale_on = search_at(stale, 2);
    const forge::SearchInfo stale_late_on = search_at(stale_late, 2);
    const forge::SearchInfo bare_on = search_at(bare, 3);
    expect(fifty_on.score == -8, "fifty root uses the zero-node leaf score");
    expect(almost_on.score != 0 && almost_on.score >= -8 && almost_on.score <= 8,
           "in-tree fifty score is a few centipawns and not 0");
    expect(mate_on.score == mate_off.score && forge::is_mate_score(mate_on.score), "mate score unchanged");
    expect(mate_late_on.score == mate_late_off.score && forge::is_mate_score(mate_late_on.score),
           "mate that reaches half-move 100 stays a mate");
    expect(mated_on.score == -forge::MateValue, "side to move is mated on half-move 100");
    expect(stale_on.score == 0, "plain stalemate stays 0");
    expect(stale_late_on.score >= -8 && stale_late_on.score <= 8 && stale_late_on.score != 0,
           "stalemate on half-move 100 is a fifty-move leaf");
    expect(bare_on.score == 0, "insufficient material stays 0");
    expect(move_is_legal(mate, mate_on.best_move), "mate best move is legal");
    expect(move_is_legal(fifty, fifty_on.best_move), "fifty best move is legal");
}

forge::Board played_position(int index) {
    static constexpr std::string_view roots[] = {
        forge::Board::StandardStartFen,
        "8/8/8/4k3/8/4K3/8/4R3 w - - 0 1",
        "4k3/8/8/8/8/8/3Q4/4K3 w - - 0 1",
        "8/2k5/8/2K5/8/8/2R5/8 w - - 0 1",
    };
    forge::Board board = board_from(roots[static_cast<std::size_t>(index) % 4]);
    std::uint32_t mix = 0xC0FFEEU ^ static_cast<std::uint32_t>(index) * 0x45D9F3BU;
    const int steps = 4 + (index % 9);
    for (int step = 0; step < steps; ++step) {
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty()) break;
        mix ^= mix << 13;
        mix ^= mix >> 17;
        mix ^= mix << 5;
        const forge::Move move = legal[mix % legal.size()];
        forge::Undo undo;
        if (!board.make_move(move, undo)) break;
    }
    if (board.legal_moves().empty()) board = board_from(forge::Board::StandardStartFen);
    return board;
}

void check_many_searches() {
    forge::DrawJitter = 8;
    forge::Searcher searcher(16);
    expect(searcher.threads() == 1, "one thread and 16 MB hash");
    int illegal = 0;
    for (int index = 0; index < 200; ++index) {
        const forge::Board board = played_position(index);
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = 10;
        const forge::SearchInfo info = searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
        if (!move_is_legal(board, info.best_move)) {
            ++illegal;
            if (illegal <= 5) {
                std::cout << "FAIL illegal search " << index << " move " << forge::Board::move_to_uci(info.best_move)
                          << " fen " << board.fen() << std::endl;
            }
        }
        if ((index + 1) % 20 == 0) {
            std::cout << "info searches " << (index + 1) << " illegal " << illegal << std::endl;
        }
    }
    expect(illegal == 0, "200 depth-10 searches with DrawJitter 8 returned legal moves");
}

} // namespace

int main() {
    check_formula();
    check_search_scores();
    check_repetition();
    check_many_searches();
    forge::DrawJitter = 0;
    std::cout << (g_fails == 0 ? "OK" : "FAILED") << " fails " << g_fails << std::endl;
    return g_fails == 0 ? 0 : 1;
}
