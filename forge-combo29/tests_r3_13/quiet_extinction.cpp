#include "forge/board.hpp"
#include "forge/search.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>

namespace {

std::uint64_t mix(std::uint64_t value) {
    value ^= value >> 30;
    value *= 0xBF58476D1CE4E5B9ULL;
    value ^= value >> 27;
    value *= 0x94D049BB133111EBULL;
    value ^= value >> 31;
    return value;
}

bool listed(const forge::MoveList& legal, forge::Move move) {
    for (const forge::Move candidate : legal) {
        if (candidate == move) return true;
    }
    return false;
}

// Same eight positions the engine's bench command searches, in the same order.
std::uint64_t bench_nodes(int depth) {
    constexpr std::array<std::string_view, 8> fens{
        forge::Board::StandardStartFen,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    };
    forge::Searcher searcher(16, 1);
    std::uint64_t total = 0;
    for (const std::string_view fen : fens) {
        forge::Board board;
        if (!board.set_fen(fen)) return 0;
        forge::SearchLimits limits;
        limits.depth = depth;
        searcher.clear();
        total += searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive).nodes;
    }
    return total;
}

forge::Board walked(std::uint64_t salt, int plies) {
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) return board;
    std::uint64_t state = mix(salt);
    for (int ply = 0; ply < plies; ++ply) {
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty()) break;
        state = mix(state + static_cast<std::uint64_t>(ply) + 9U);
        const forge::Move chosen = legal[static_cast<std::size_t>(state % legal.size())];
        forge::Undo undo;
        if (!board.make_move(chosen, undo)) break;
    }
    return board;
}

} // namespace

int main() {
    if (forge::tune::QuietExtinction) {
        std::cerr << "QuietExtinction default is not false\n";
        return 1;
    }
    forge::Board perft_board;
    if (!perft_board.set_fen(forge::Board::StandardStartFen)) {
        std::cerr << "start fen rejected\n";
        return 1;
    }
    const std::uint64_t perft5 = perft_board.perft(5);
    const std::uint64_t bench11 = bench_nodes(11);
    const std::uint64_t bench13_off = bench_nodes(13);
    forge::tune::QuietExtinction = true;
    const std::uint64_t bench13_on = bench_nodes(13);
    std::cout << "perft5 " << perft5 << " bench11 " << bench11 << " bench13_off " << bench13_off
              << " bench13_on " << bench13_on << '\n';
    if (perft5 != 4865609 || bench11 != 312866 || bench13_off != 862329 || bench13_on == 0 ||
        bench13_on == bench13_off) {
        std::cerr << "pin mismatch\n";
        return 1;
    }
    forge::Searcher searcher(16, 1);
    int searched = 0;
    int illegal = 0;
    std::uint64_t nodes = 0;

    auto check = [&](forge::Board board, int index) {
        const forge::MoveList legal = board.legal_moves();
        const bool ruled_draw = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                                    board.is_insufficient_material());
        forge::SearchLimits limits;
        limits.depth = 10;
        searcher.clear();
        const forge::SearchInfo info = searcher.search(
            board, limits, false, forge::Searcher::TTAccess::Exclusive);
        ++searched;
        nodes += info.nodes;
        bool ok = info.depth == 10;
        if (legal.empty()) ok = ok && info.best_move.is_none();
        else {
            ok = ok && listed(legal, info.best_move);
            forge::Undo undo;
            ok = ok && board.make_move(info.best_move, undo);
            if (!ruled_draw) ok = ok && info.nodes > 0;
        }
        if (!ok) {
            ++illegal;
            std::cerr << "illegal index " << index << " move " << forge::Board::move_to_uci(info.best_move)
                      << " legal " << legal.size() << " depth " << info.depth << " nodes " << info.nodes << '\n';
        }
    };

    for (int i = 0; i < 197; ++i) {
        check(walked(0x51A7ULL * static_cast<std::uint64_t>(i + 3), 1 + (i % 23)), i);
    }

    forge::Board king_pawn;
    forge::Board checked;
    forge::Board start;
    if (!king_pawn.set_fen("4k3/8/8/3p4/3P4/8/8/4K3 w - - 0 1") ||
        !checked.set_fen("4k3/8/8/8/8/8/8/4QK2 b - - 0 1") ||
        !start.set_fen(forge::Board::StandardStartFen)) {
        std::cerr << "setup fen rejected\n";
        return 1;
    }
    if (king_pawn.has_non_pawn_material(forge::White) || king_pawn.has_non_pawn_material(forge::Black) ||
        !checked.in_check() || !start.has_non_pawn_material(forge::White)) {
        std::cerr << "setup position does not match the case it is meant to cover\n";
        return 1;
    }
    check(king_pawn, 197);
    check(checked, 198);
    check(start, 199);

    forge::tune::QuietExtinction = false;
    const std::uint64_t bench13_restored = bench_nodes(13);
    std::cout << "searches " << searched << " illegal " << illegal << " nodes " << nodes
              << " bench13_restored " << bench13_restored << '\n';
    return searched == 200 && illegal == 0 && nodes > 0 && bench13_restored == 862329 ? 0 : 1;
}
