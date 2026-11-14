// Fixed-seed random playouts. Compares the engine static evaluation of the
// lock net (256) with the zero-widened net (512) on every position.

#include "wide_eval.hpp"

#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <random>
#include <string>
#include <unordered_set>

namespace {

constexpr std::uint32_t kSeed = 20261110u;
constexpr int kPositions = 100000;
constexpr int kPlyCap = 400;

int static_eval(int classical, int network, bool residual) {
    if (!residual) return network;
    return std::clamp(classical + network, -forge::MateInMaxPly + 1, forge::MateInMaxPly - 1);
}

void mix(std::uint64_t& hash, int value) {
    hash ^= static_cast<std::uint64_t>(static_cast<std::uint32_t>(value));
    hash *= 1099511628211ull;
}

bool terminal(const forge::Board& board, int ply) {
    if (ply >= kPlyCap) return true;
    if (board.halfmove_clock() >= 100) return true;
    if (board.is_insufficient_material()) return true;
    if (board.is_repetition()) return true;
    return board.legal_moves().empty();
}

} // namespace

int main() {
    static_assert(forge::nnue::HiddenSize == 256, "lock side must be the 256 net");

    const bool residual_256 = forge::nnue::residual();
    const bool residual_512 = forge::t19::residual_512();
    forge::Board board;
    std::mt19937 rng(kSeed);
    std::unordered_set<std::uint64_t> seen;
    std::uint64_t hash_256 = 14695981039346656037ull;
    std::uint64_t hash_512 = 14695981039346656037ull;
    int ply = 0;
    int resets = 0;
    int make_failures = 0;
    int static_differ = 0;
    int network_differ = 0;
    long long static_max_abs = 0;
    long long network_max_abs = 0;
    int worst_256 = 0;
    int worst_512 = 0;
    int worst_network_256 = 0;
    int worst_network_512 = 0;
    std::string worst_fen = "-";
    int start_256 = 0;
    int start_512 = 0;
    bool saw_start = false;

    for (int n = 0; n < kPositions; ++n) {
        forge::nnue::Accumulator accumulator;
        forge::nnue::refresh(board, accumulator);
        const int network_256 = forge::nnue::evaluate(board, accumulator);
        const int network_512 = forge::t19::network_eval_512(board);
        const int classical = forge::Evaluator::evaluate_uncached(board);
        const int eval_256 = static_eval(classical, network_256, residual_256);
        const int eval_512 = static_eval(classical, network_512, residual_512);
        if (!saw_start) {
            start_256 = eval_256;
            start_512 = eval_512;
            saw_start = true;
        }
        mix(hash_256, eval_256);
        mix(hash_512, eval_512);
        seen.insert(board.key());

        const long long network_gap = static_cast<long long>(network_512) - static_cast<long long>(network_256);
        const long long network_abs = network_gap < 0 ? -network_gap : network_gap;
        if (network_abs != 0) {
            ++network_differ;
            if (network_abs > network_max_abs) {
                network_max_abs = network_abs;
                worst_network_256 = network_256;
                worst_network_512 = network_512;
            }
        }
        const long long gap = static_cast<long long>(eval_512) - static_cast<long long>(eval_256);
        const long long abs_gap = gap < 0 ? -gap : gap;
        if (abs_gap != 0) {
            ++static_differ;
            if (abs_gap > static_max_abs) {
                static_max_abs = abs_gap;
                worst_256 = eval_256;
                worst_512 = eval_512;
                worst_fen = board.fen();
            }
        }

        if (terminal(board, ply)) {
            if (!board.set_fen(forge::Board::StandardStartFen)) {
                std::cerr << "eval_parity: cannot reset to the start position\n";
                return 1;
            }
            ply = 0;
            ++resets;
            continue;
        }
        const forge::MoveList moves = board.legal_moves();
        const forge::Move move = moves[static_cast<std::size_t>(rng() % moves.size())];
        forge::Undo undo;
        if (!board.make_move(move, undo)) {
            ++make_failures;
            if (!board.set_fen(forge::Board::StandardStartFen)) return 1;
            ply = 0;
            ++resets;
            continue;
        }
        ++ply;
    }

    std::cout << "seed " << kSeed << '\n'
              << "positions " << kPositions << '\n'
              << "unique " << seen.size() << '\n'
              << "resets " << resets << '\n'
              << "make_failures " << make_failures << '\n'
              << "residual_256 " << (residual_256 ? 1 : 0) << '\n'
              << "residual_512 " << (residual_512 ? 1 : 0) << '\n'
              << "start_static_256 " << start_256 << '\n'
              << "start_static_512 " << start_512 << '\n'
              << "static_equal " << (kPositions - static_differ) << '\n'
              << "static_differ " << static_differ << '\n'
              << "static_max_abs_diff " << static_max_abs << '\n'
              << "worst_fen " << worst_fen << '\n'
              << "worst_static_256 " << worst_256 << '\n'
              << "worst_static_512 " << worst_512 << '\n'
              << "network_differ " << network_differ << '\n'
              << "network_max_abs_diff " << network_max_abs << '\n'
              << "worst_network_256 " << worst_network_256 << '\n'
              << "worst_network_512 " << worst_network_512 << '\n'
              << "hash_static_256 " << hash_256 << '\n'
              << "hash_static_512 " << hash_512 << '\n';
    if (!residual_256 || !residual_512 || make_failures != 0 || static_differ != 0 || network_differ != 0) return 1;
    return 0;
}
