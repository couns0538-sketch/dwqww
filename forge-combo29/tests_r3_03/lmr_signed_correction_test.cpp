#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

namespace {

int fail(const std::string& message) {
    std::cerr << "fail: " << message << '\n';
    return 1;
}

int check_formula() {
    using forge::apply_lmr_signed_correction;
    struct Case {
        int reduction;
        int correction_cp;
        int expect;
        const char* why;
    };
    const Case cases[] = {
        {4, 0, 4, "zero correction keeps the reduction"},
        {0, 0, 0, "zero stays zero"},
        {3, 63, 3, "under 64cp rounds toward zero and stays put"},
        {3, -63, 3, "under 64cp the other way stays put"},
        {3, 64, 2, "64cp better subtracts one ply"},
        {3, -64, 4, "64cp worse adds one ply"},
        {3, 1000, 2, "a large positive correction is limited to one ply"},
        {3, -1000, 4, "a large negative correction is limited to one ply"},
        {1, 64, 0, "subtracting one ply can land on zero"},
        {0, 64, 0, "the reduction never goes below zero"},
        {0, -64, 1, "a one-ply increase from zero is allowed"},
        {-2, 0, 0, "an already negative reduction is clamped to zero"},
        {-2, -64, 0, "one extra ply does not lift a -2 base above zero"},
    };
    for (const Case& item : cases) {
        const int got = apply_lmr_signed_correction(item.reduction, item.correction_cp);
        if (got != item.expect) {
            std::cerr << "formula " << item.why << ": got " << got << " expected " << item.expect << '\n';
            return 1;
        }
        if (got < 0) return fail("formula returned a negative reduction");
    }
    return 0;
}

std::uint64_t mix(std::uint64_t& state) {
    state = state * 0xD1B54A32D192ED03ULL + 0x9E3779B97F4A7C15ULL;
    return state;
}

bool collect_positions(std::vector<std::string>& fens) {
    forge::Board root;
    if (!root.set_fen(forge::Board::StandardStartFen)) return false;
    fens.push_back(std::string(forge::Board::StandardStartFen));
    std::uint64_t state = 0xC0FFEE5EEDULL;
    int attempts = 0;
    while (fens.size() < 200 && attempts < 20000) {
        ++attempts;
        forge::Board board = root;
        const int plies = static_cast<int>(6 + (mix(state) % 14ULL));
        bool walked = true;
        for (int ply = 0; ply < plies; ++ply) {
            const forge::MoveList legal = board.legal_moves();
            if (legal.empty()) {
                walked = false;
                break;
            }
            const forge::Move chosen = legal[static_cast<std::size_t>(mix(state) % legal.size())];
            forge::Undo undo;
            if (!board.make_move(chosen, undo)) {
                walked = false;
                break;
            }
        }
        if (!walked || board.legal_moves().empty()) continue;
        const std::string fen = board.fen();
        bool seen = false;
        for (const std::string& prior : fens) {
            if (prior == fen) {
                seen = true;
                break;
            }
        }
        if (!seen) fens.push_back(fen);
    }
    return fens.size() == 200;
}

bool move_is_legal(const forge::Board& board, forge::Move move) {
    if (move.is_none()) return false;
    const forge::MoveList legal = board.legal_moves();
    for (const forge::Move candidate : legal) {
        if (candidate == move) return board.is_pseudo_legal(move) && board.is_legal(move);
    }
    return false;
}

bool line_is_legal(forge::Board board, const std::vector<forge::Move>& line) {
    for (const forge::Move move : line) {
        if (!move_is_legal(board, move)) return false;
        forge::Undo undo;
        if (!board.make_move(move, undo)) return false;
    }
    return true;
}

} // namespace

int main() {
    if (forge::tune::LmrSignedCorrection) return fail("LmrSignedCorrection must default off");
    if (check_formula() != 0) return 1;

    std::vector<std::string> fens;
    if (!collect_positions(fens)) return fail("could not build 200 positions");

    forge::tune::LmrSignedCorrection = true;
    forge::Searcher searcher(16, 1);
    int legal_moves = 0;
    for (std::size_t index = 0; index < fens.size(); ++index) {
        forge::Board board;
        if (!board.set_fen(fens[index])) return fail("fen rejected: " + fens[index]);
        if (board.legal_moves().empty()) return fail("empty legal list: " + fens[index]);
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = 10;
        const forge::SearchInfo info = searcher.search(board, limits, false);
        if (info.depth != 10) {
            std::cerr << "depth " << info.depth << " on " << fens[index] << '\n';
            return 1;
        }
        if (!move_is_legal(board, info.best_move)) {
            std::cerr << "illegal " << forge::Board::move_to_uci(info.best_move) << " on " << fens[index] << '\n';
            return 1;
        }
        if (!info.pv.empty() && info.pv.front() != info.best_move) {
            std::cerr << "pv disagrees with best move on " << fens[index] << '\n';
            return 1;
        }
        if (!line_is_legal(board, info.pv)) {
            std::cerr << "illegal pv on " << fens[index] << '\n';
            return 1;
        }
        ++legal_moves;
        if ((index + 1) % 25 == 0) {
            std::cerr << "searches " << (index + 1) << " legal\n";
        }
    }
    if (legal_moves != 200) return fail("search count");
    std::cout << "formula ok\nsearches 200 depth 10 option on legal 200\n";
    return 0;
}
