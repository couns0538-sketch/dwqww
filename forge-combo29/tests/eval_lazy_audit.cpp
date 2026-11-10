#include "forge/search.hpp"
#include <algorithm>
#include <bit>
#include <cstdlib>
#include <iostream>
#include <random>
#include <string>

namespace forge {
// Existing friendship provides access without modifying production code.
struct SearcherTestProbe {
    static SearchStack* reset(Worker& worker) {
        for (std::size_t i = 0; i < worker.stack_.size(); ++i) {
            worker.stack_[i] = SearchStack{};
            worker.stack_[i].ply = static_cast<int>(i) - 4;
        }
        return worker.stack_.data() + 4;
    }
    static int evaluate(Worker& worker, const Board& board, SearchStack* ss) {
        return worker.static_evaluate(board, ss);
    }
    static void move(Worker& worker, const Board& board, SearchStack* ss, Move move) {
        worker.record_move(ss, board, move);
    }
    static void null(Worker& worker, SearchStack* ss) { worker.record_null_move(ss); }
};
}

namespace {
using namespace forge;
std::uint64_t evaluations = 0, records = 0, nulls = 0, restores = 0;
std::uint64_t no_ancestor = 0, cache_hits = 0, castles = 0, ep = 0, promotions = 0;
std::array<std::uint64_t, MaxPly + 1> distances{};
std::array<unsigned, 4> castle_directions{}, promotion_types{};
std::string context;

[[noreturn]] void fail(const Board& board, const std::string& reason) {
    std::cerr << "FAIL: " << reason << " " << context << " fen=" << board.fen() << '\n';
    std::exit(1);
}

void check(Worker& worker, const Board& board, SearchStack* ss) {
    if (nnue::enabled) {
        if (ss->accumulator.valid) ++cache_hits;
        else {
            int distance = 1;
            while (distance <= ss->ply && !(ss - distance)->accumulator.valid) ++distance;
            if (distance > ss->ply) ++no_ancestor;
            else ++distances[static_cast<std::size_t>(distance)];
        }
    }
    int expected = Evaluator::evaluate_uncached(board);
    nnue::Accumulator fresh;
    if (nnue::enabled) {
        nnue::refresh(board, fresh);
        expected = std::clamp(expected + nnue::evaluate(board, fresh), -MateInMaxPly + 1, MateInMaxPly - 1);
    }
    const int actual = SearcherTestProbe::evaluate(worker, board, ss);
    if (actual != expected) fail(board, "Worker static evaluation mismatch ply=" + std::to_string(ss->ply));
    if (nnue::enabled) {
        if (!ss->accumulator.valid || !ss->runtime_psqt.valid) fail(board, "Worker left invalid state");
        for (std::size_t p = 0; p < 2; ++p)
            for (std::size_t h = 0; h < nnue::HiddenSize; ++h)
                if (std::bit_cast<std::uint32_t>(ss->accumulator.values[p][h]) !=
                    std::bit_cast<std::uint32_t>(fresh.values[p][h]))
                    fail(board, "Worker accumulator bits mismatch ply=" + std::to_string(ss->ply));
    }
    ++evaluations;
}

struct Step {
    Move move{};
    Undo undo{};
    NullUndo null_undo{};
    bool is_null = false;
    std::string fen;
};

void push(Worker& worker, Board& board, SearchStack* root, std::vector<Step>& path, Move move) {
    Step step;
    step.move = move;
    step.fen = board.fen();
    SearcherTestProbe::move(worker, board, root + path.size(), move);
    ++records;
    if (move.is_castle()) {
        ++castles;
        ++castle_directions[2 * static_cast<std::size_t>(board.side_to_move()) +
                            ((move.flags & KingCastle) != 0 ? 0U : 1U)];
    }
    if (move.is_promotion()) { ++promotions; ++promotion_types[move.promotion - Knight]; }
    if ((move.flags & EnPassant) != 0) ++ep;
    if (!board.make_move(move, step.undo)) fail(board, "Legal move rejected");
    path.push_back(step);
}

void push_null(Worker& worker, Board& board, SearchStack* root, std::vector<Step>& path) {
    Step step;
    step.is_null = true;
    step.fen = board.fen();
    SearcherTestProbe::null(worker, root + path.size());
    board.make_null_move(step.null_undo);
    path.push_back(step);
    ++nulls;
}

void pop(Board& board, std::vector<Step>& path) {
    const Step& step = path.back();
    if (step.is_null) board.unmake_null_move(step.null_undo);
    else board.unmake_move(step.move, step.undo);
    if (board.fen() != step.fen) fail(board, "Unmake changed parent");
    path.pop_back();
    ++restores;
}

void extend(Worker& worker, Board& board, SearchStack* root, std::vector<Step>& path,
            std::mt19937& rng, int target, int stride) {
    while (static_cast<int>(path.size()) < target) {
        const auto legal = board.legal_moves();
        if (legal.empty()) break;
        if (path.size() % 17 == 8 && !board.in_check() && board.has_non_pawn_material(board.side_to_move()))
            push_null(worker, board, root, path);
        else push(worker, board, root, path, legal[rng() % legal.size()]);
        if (static_cast<int>(path.size()) % stride == 0) check(worker, board, root + path.size());
    }
    check(worker, board, root + path.size());
}
} // namespace

int main(int argc, char** argv) {
    const std::uint32_t seed = argc > 1 ? static_cast<std::uint32_t>(std::stoul(argv[1])) : 20261110;
    std::mt19937 rng(seed);
    if (!nnue::available() || !nnue::residual() || nnue::HiddenSize != 256) return 2;
    const char* fixtures[] = {
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
        "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
        "4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1",
        "1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/p7/1R2K3 b - - 0 1"
    };
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    for (bool use_nnue : {false, true}) {
        nnue::enabled = use_nnue;
        for (bool root_valid : {false, true}) {
            for (int stride : {1, 2, 7, 31, 96}) {
                for (const char* fen : fixtures) {
                    Board board;
                    if (!board.set_fen(fen)) fail(board, "Invalid fixture");
                    auto* root = SearcherTestProbe::reset(*worker);
                    context = "seed=" + std::to_string(seed) + " nnue=" + std::to_string(use_nnue) +
                              " root_valid=" + std::to_string(root_valid) + " stride=" + std::to_string(stride);
                    if (root_valid) check(*worker, board, root);
                    std::vector<Step> path;
                    extend(*worker, board, root, path, rng, 96, stride);
                    while (!path.empty()) {
                        pop(board, path);
                        // Re-evaluate selected restored ancestors, then reuse
                        // their child slots for sibling subtrees of deferred moves.
                        if (path.size() % 8 == 0) {
                            check(*worker, board, root + path.size());
                            const auto legal = board.legal_moves();
                            if (!legal.empty()) {
                                const auto depth = path.size();
                                push(*worker, board, root, path, legal[rng() % legal.size()]);
                                extend(*worker, board, root, path, rng, static_cast<int>(depth) + 5, 96);
                                while (path.size() > depth) pop(board, path);
                                check(*worker, board, root + path.size());
                            }
                        }
                    }
                    // Explore every root move so all promotion choices, EP,
                    // and castling wings are exercised, not left to chance.
                    for (const Move& move : board.legal_moves()) {
                        root = SearcherTestProbe::reset(*worker);
                        if (root_valid) check(*worker, board, root);
                        push(*worker, board, root, path, move);
                        extend(*worker, board, root, path, rng, 9, 96);
                        while (!path.empty()) pop(board, path);
                        check(*worker, board, root);
                    }
                }
            }
        }
    }
    for (auto n : castle_directions) if (n == 0) fail(Board{}, "Missing castling direction");
    for (auto n : promotion_types) if (n == 0) fail(Board{}, "Missing promotion type");
    for (int distance : {1, 2, 7, 31, 96})
        if (distances[distance] == 0) fail(Board{}, "Missing requested ancestor distance");
    if (no_ancestor == 0 || cache_hits == 0 || nulls == 0 || ep == 0) fail(Board{}, "Missing traversal coverage");
    std::cout << "{\"passed\":true,\"seed\":" << seed << ",\"evaluations\":" << evaluations
              << ",\"records\":" << records << ",\"nulls\":" << nulls << ",\"restores\":" << restores
              << ",\"no_ancestor\":" << no_ancestor << ",\"cache_hits\":" << cache_hits
              << ",\"castles\":" << castles << ",\"en_passant\":" << ep
              << ",\"promotions\":" << promotions << ",\"ancestor_distances\":{";
    bool first = true;
    for (int i = 1; i <= MaxPly; ++i) if (distances[i] != 0) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << '\"' << i << "\":" << distances[i];
    }
    std::cout << "}}\n";
}
