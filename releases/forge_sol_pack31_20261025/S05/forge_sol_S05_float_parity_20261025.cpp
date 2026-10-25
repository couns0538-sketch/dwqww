// Float-API adaptation of the earlier standalone incremental/fresh test idea.
// No optional inference backend or engine configuration is changed by this driver.
#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

namespace {
using forge::Board;
using forge::Move;
using Accumulator = forge::nnue::Accumulator;
static_assert(forge::nnue::HiddenSize == 256, "S05 qualification requires H256");

struct Counts {
    std::uint64_t positions = 0, transitions = 0, parent_checks = 0, alias_checks = 0;
    std::uint64_t castles = 0, en_passant = 0, promotions = 0, nulls = 0;
    std::uint64_t lane_mismatches = 0, score_mismatches = 0, state_mismatches = 0;
} counts;

void require(bool ok, const char* message) {
    if (!ok) throw std::runtime_error(message);
}

bool same(const Accumulator& a, const Accumulator& b) {
    if (a.valid != b.valid) return false;
    for (std::size_t side = 0; side < a.values.size(); ++side)
        for (std::size_t h = 0; h < a.values[side].size(); ++h)
            if (!std::isfinite(a.values[side][h]) || !std::isfinite(b.values[side][h]) ||
                std::bit_cast<std::uint32_t>(a.values[side][h]) !=
                    std::bit_cast<std::uint32_t>(b.values[side][h])) return false;
    return true;
}

void compare_fresh(const Board& board, const Accumulator& incremental) {
    Accumulator fresh;
    forge::nnue::refresh(board, fresh);
    require(fresh.valid && incremental.valid, "invalid accumulator");
    if (!same(incremental, fresh)) ++counts.lane_mismatches;
    if (forge::nnue::evaluate(board, incremental) != forge::nnue::evaluate(board, fresh))
        ++counts.score_mismatches;
    ++counts.positions;
}

Accumulator updated(const Accumulator& parent, const forge::nnue::DirtyPieces& dirty) {
    const Accumulator saved = parent;
    Accumulator child;
    forge::nnue::update(parent, child, dirty);
    ++counts.parent_checks;
    if (!same(parent, saved)) ++counts.state_mismatches;
    Accumulator alias = parent;
    forge::nnue::update(alias, alias, dirty);
    ++counts.alias_checks;
    if (!same(child, alias)) ++counts.lane_mismatches;
    require(child.valid && alias.valid, "update did not mark accumulator valid");
    return child;
}

void move_once(Board& board, Accumulator& current, Move move, forge::Undo& undo) {
    const auto dirty = forge::nnue::dirty_pieces(board, move);
    auto child = updated(current, dirty);
    require(board.make_move(move, undo), "legal move rejected");
    compare_fresh(board, child);
    current = child;
    ++counts.transitions;
    counts.castles += move.is_castle();
    counts.en_passant += (move.flags & forge::EnPassant) != 0U;
    counts.promotions += move.is_promotion();
}

void null_once(Board& board, const Accumulator& current) {
    const auto child = updated(current, forge::nnue::DirtyPieces{});
    forge::NullUndo undo;
    board.make_null_move(undo);
    compare_fresh(board, child);
    board.unmake_null_move(undo);
    compare_fresh(board, current);
    ++counts.nulls;
}

constexpr std::array<const char*, 10> fixtures{
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
    "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
    "4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1",
    "1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
    "4k3/7P/8/8/8/8/p7/1R2K3 b - - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
};

void print_summary(const char* status) {
    std::cout << "{\"status\":\"" << status << "\",\"positions\":" << counts.positions
        << ",\"transitions\":" << counts.transitions << ",\"parent_checks\":" << counts.parent_checks
        << ",\"alias_checks\":" << counts.alias_checks << ",\"castles\":" << counts.castles
        << ",\"en_passant\":" << counts.en_passant << ",\"promotions\":" << counts.promotions
        << ",\"nulls\":" << counts.nulls << ",\"lane_mismatches\":" << counts.lane_mismatches
        << ",\"score_mismatches\":" << counts.score_mismatches
        << ",\"state_mismatches\":" << counts.state_mismatches << "}\n";
}
} // namespace

int main(int argc, char** argv) {
    try {
        require(argc <= 2, "usage: float_parity [walk_positions]");
        std::uint64_t target = 20000;
        if (argc == 2) {
            const std::string argument(argv[1]);
            require(!argument.empty() && argument.find_first_not_of("0123456789") == std::string::npos,
                    "positions must be a positive decimal integer");
            std::size_t consumed = 0;
            target = std::stoull(argument, &consumed);
            require(consumed == argument.size() && target != 0, "positions must be positive");
        }
        require(forge::nnue::available(), "no compiled NNUE network");
        Board board;
        for (const char* fen : fixtures) {
            require(board.set_fen(fen), "fixture rejected");
            Accumulator root;
            forge::nnue::refresh(board, root);
            compare_fresh(board, root);
            for (Move move : board.legal_moves()) {
                auto current = root;
                forge::Undo undo;
                move_once(board, current, move, undo);
                board.unmake_move(move, undo);
                compare_fresh(board, root);
            }
            if (!board.in_check()) null_once(board, root);
        }

        std::mt19937_64 random(20261025);
        Accumulator current;
        std::uint64_t reset = 0;
        int ply = 0;
        auto restart = [&] {
            require(board.set_fen(fixtures[static_cast<std::size_t>(reset++ % fixtures.size())]), "walk fixture rejected");
            forge::nnue::refresh(board, current);
            ply = 0;
        };
        restart();
        for (std::uint64_t position = 0; position < target; ++position) {
            auto legal = board.legal_moves();
            if (legal.empty() || ply == 160) {
                restart();
                legal = board.legal_moves();
            }
            require(!legal.empty(), "walk fixture has no legal move");
            forge::Undo undo;
            move_once(board, current, legal[static_cast<std::size_t>(random() % legal.size())], undo);
            ++ply;
            if (position % 43 == 0 && !board.in_check()) null_once(board, current);
        }
        require(counts.castles && counts.en_passant && counts.promotions && counts.nulls, "special-move coverage missing");
        const bool pass = counts.lane_mismatches == 0 && counts.score_mismatches == 0 && counts.state_mismatches == 0;
        print_summary(pass ? "PASS" : "FAIL");
        return pass ? 0 : 1;
    } catch (const std::exception& error) {
        print_summary("FAIL");
        std::cerr << error.what() << '\n';
        return 1;
    }
}
