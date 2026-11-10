// Test-only access to runtime HCE helpers. Standard/dependency headers are
// loaded first; no production testing hook or search implementation is linked.
#include "forge/board.hpp"
#include <cstdint>
#include <vector>
#define private public
#include "forge/eval.hpp"
#undef private
#include "forge/nnue.hpp"
#include <bit>
#include <cstdlib>
#include <iostream>
#include <random>
#include <string>

namespace {
using namespace forge;
struct State {
    nnue::Accumulator accumulator;
    Evaluator::RuntimePsqt psqt;
};
struct Step { Move move; Undo undo; State parent; std::string fen; };
std::uint64_t checked = 0, transitions = 0, captures = 0, en_passant = 0;
std::uint64_t promotions = 0, castles = 0, nulls = 0, unmakes = 0;
std::array<std::uint64_t, 4> castle_types{}, promotion_types{};
Evaluator evaluator;
std::string context;

[[noreturn]] void fail(const Board& board, const std::string& message) {
    std::cerr << "FAIL: " << message << " context=" << context << " fen=" << board.fen() << '\n';
    std::exit(1);
}

State refresh(const Board& board) {
    State state;
    nnue::refresh(board, state.accumulator);
    state.psqt = Evaluator::refresh_runtime_psqt(board);
    return state;
}

State increment(const State& parent, const nnue::DirtyPieces& dirty) {
    State child;
    nnue::update(parent.accumulator, child.accumulator, dirty);
    Evaluator::update_runtime_psqt(parent.psqt, child.psqt, dirty);
    return child;
}

void check(const Board& board, const State& state) {
    const State fresh = refresh(board);
    if (!state.accumulator.valid) fail(board, "Invalid incremental accumulator");
    for (std::size_t p = 0; p < 2; ++p) {
        for (std::size_t h = 0; h < nnue::HiddenSize; ++h) {
            if (std::bit_cast<std::uint32_t>(state.accumulator.values[p][h]) !=
                std::bit_cast<std::uint32_t>(fresh.accumulator.values[p][h])) {
                fail(board, "Accumulator bits differ perspective=" + std::to_string(p) +
                     " lane=" + std::to_string(h));
            }
        }
    }
    if (state.psqt.valid != fresh.psqt.valid || state.psqt.phase != fresh.psqt.phase ||
        (state.psqt.valid && state.psqt.score != fresh.psqt.score)) fail(board, "Runtime PSQT differs");
    const int oracle = Evaluator::evaluate_uncached(board);
    const int runtime = evaluator.evaluate_runtime(board, state.psqt);
    const int cached = evaluator.evaluate(board);
    if (runtime != oracle || cached != oracle) fail(board, "HCE runtime/cached differs from uncached oracle");
    if (nnue::evaluate(board, state.accumulator) != nnue::evaluate(board, fresh.accumulator))
        fail(board, "NNUE output differs");
    ++checked;
}

void count(const Board& parent, const Move& move) {
    ++transitions;
    if (move.is_capture()) ++captures;
    if ((move.flags & EnPassant) != 0) ++en_passant;
    if (move.is_promotion()) {
        ++promotions;
        ++promotion_types[static_cast<std::size_t>(move.promotion - Knight)];
    }
    if (move.is_castle()) {
        ++castles;
        ++castle_types[2 * static_cast<std::size_t>(parent.side_to_move()) +
                       ((move.flags & KingCastle) != 0 ? 0U : 1U)];
    }
}

void probe_move(Board& board, const State& parent, const Move& move) {
    const std::string before = board.fen();
    context = "branch " + Board::move_to_uci(move);
    const auto dirty = nnue::dirty_pieces(board, move);
    const State child = increment(parent, dirty);
    count(board, move);
    Undo undo;
    if (!board.make_move(move, undo)) fail(board, "Legal generated move rejected");
    check(board, child);
    board.unmake_move(move, undo);
    ++unmakes;
    if (board.fen() != before) fail(board, "Unmake changed parent FEN");
    check(board, parent);
}

void probe_null(Board& board, const State& parent) {
    // Match the elementary search null-move prerequisites, not a chess move.
    if (board.in_check() || !board.has_non_pawn_material(board.side_to_move())) return;
    const std::string before = board.fen();
    context = "null";
    const State child = increment(parent, nnue::DirtyPieces{});
    NullUndo undo;
    board.make_null_move(undo);
    ++nulls;
    check(board, child);
    // Exercise real successors below the null position as search does.
    const auto moves = board.legal_moves();
    if (!moves.empty()) probe_move(board, child, moves.front());
    board.unmake_null_move(undo);
    ++unmakes;
    if (board.fen() != before) fail(board, "Null unmake changed parent FEN");
    check(board, parent);
}
} // namespace

int main(int argc, char** argv) {
    const std::uint32_t seed = argc > 1 ? static_cast<std::uint32_t>(std::stoul(argv[1])) : 0xE7A12026U;
    std::mt19937 rng(seed);
    if (!nnue::available() || !nnue::residual() || nnue::HiddenSize != 256) {
        std::cerr << "Requires shipped residual256 network\n";
        return 1;
    }
    const char* fixtures[] = {
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
        "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
        "4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1",
        "1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/p7/1R2K3 b - - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    };
    for (const char* fen : fixtures) {
        Board board;
        if (!board.set_fen(fen)) fail(board, "Invalid targeted fixture");
        State state = refresh(board);
        check(board, state);
        for (const Move& move : board.legal_moves()) probe_move(board, state, move);
        probe_null(board, state);
    }
    for (int game = 0; game < 32; ++game) {
        Board board;
        if (game % 4 != 0 && !board.set_fen(fixtures[(game - 1) % 7])) fail(board, "Invalid playout fixture");
        State state = refresh(board);
        std::vector<Step> path;
        for (int ply = 0; ply < 256; ++ply) {
            context = "game=" + std::to_string(game) + " ply=" + std::to_string(ply);
            check(board, state);
            const auto moves = board.legal_moves();
            if (moves.empty()) break;
            if (ply % 16 == 0) {
                for (const Move& move : moves) probe_move(board, state, move);
                probe_null(board, state);
            }
            const Move move = moves[rng() % moves.size()];
            Step step{move, {}, state, board.fen()};
            const auto dirty = nnue::dirty_pieces(board, move);
            count(board, move);
            if (!board.make_move(move, step.undo)) fail(board, "Playout legal move rejected");
            state = increment(state, dirty);
            path.push_back(step);
            check(board, state);
        }
        // Restore the entire stack one ply at a time, not just the last move.
        while (!path.empty()) {
            const Step& step = path.back();
            board.unmake_move(step.move, step.undo);
            ++unmakes;
            state = step.parent;
            if (board.fen() != step.fen) fail(board, "Full unwind changed parent FEN");
            check(board, state);
            path.pop_back();
        }
    }
    if (captures == 0 || en_passant < 2 || promotions == 0 || nulls == 0)
        fail(Board{}, "Missing special-move coverage");
    for (auto n : castle_types) if (n == 0) fail(Board{}, "Missing castling direction");
    for (auto n : promotion_types) if (n == 0) fail(Board{}, "Missing promotion type");
    std::cout << "{\"passed\":true,\"seed\":" << seed << ",\"checks\":" << checked
              << ",\"transitions\":" << transitions << ",\"captures\":" << captures
              << ",\"en_passant\":" << en_passant << ",\"promotions\":" << promotions
              << ",\"castles\":" << castles << ",\"nulls\":" << nulls
              << ",\"unmakes\":" << unmakes << "}\n";
}
