// v2_eval_o30.cpp - Opus 30-h job parity harness (own code): prints the v2 network output in centipawns of every FEN
// in a file through the engine's own loader (forge::nnue::v2::load), full refresh and output kernel, and, with
// --walk, plays the FEN list's games move by move checking the cached refresh and the incremental update against a
// full refresh at every ply (exact float equality of both perspectives).
// Build against the ported lock tree (opus_30h/a/v2port.patch), e.g.:
//   g++ -std=c++20 -O2 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -march=x86-64-v3 -Iinclude \
//       v2_eval_o30.cpp src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp -o v2_eval_avx2
//   (-march=x86-64-v2 for the SSE output path, -DFORGE_NNUE_V2_SCALAR=1 for the scalar one)
// usage: v2_eval_o30 <net.nnue2> <fens.txt>            -> one line per FEN: the network cp, or ERR
//        v2_eval_o30 --walk <net.nnue2> <seed> <games> <plies>   -> random legal games; prints a summary, exit 1 on mismatch
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/nnue_v2.hpp"

#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <random>
#include <string>

namespace {

bool same(const forge::nnue::Accumulator& a, const forge::nnue::Accumulator& b) {
    return std::memcmp(a.values.data(), b.values.data(), sizeof(a.values)) == 0;
}

int walk(const forge::nnue::v2::Net& net, std::uint64_t seed, int games, int plies) {
    std::mt19937_64 rng(seed);
    std::uint64_t checked = 0;
    std::uint64_t king_key_changes = 0;
    std::uint64_t mismatches = 0;
    forge::nnue::v2::RefreshCache& cache = forge::nnue::v2::make_cache(net, 0);
    auto inc = std::make_unique<forge::nnue::Accumulator>();
    auto full = std::make_unique<forge::nnue::Accumulator>();
    auto cached = std::make_unique<forge::nnue::Accumulator>();
    for (int g = 0; g < games; ++g) {
        forge::Board board;
        (void)board.set_fen(forge::Board::StandardStartFen);
        for (const forge::Color c : {forge::White, forge::Black}) {
            forge::nnue::v2::refresh(net, board, c, inc->values[static_cast<std::size_t>(c)].data());
        }
        for (int p = 0; p < plies; ++p) {
            const forge::MoveList moves = board.legal_moves();
            if (moves.size() == 0) break;
            const forge::Move move = moves[static_cast<std::size_t>(rng() % moves.size())];
            const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
            std::array<forge::nnue::v2::KingKey, 2> before{
                forge::nnue::v2::king_key(net, forge::White, board.king_square(forge::White)),
                forge::nnue::v2::king_key(net, forge::Black, board.king_square(forge::Black))};
            auto parent = std::make_unique<forge::nnue::Accumulator>(*inc);
            forge::Undo undo;
            if (!board.make_move(move, undo)) return 3;
            for (const forge::Color c : {forge::White, forge::Black}) {
                const std::size_t i = static_cast<std::size_t>(c);
                const forge::nnue::v2::KingKey now = forge::nnue::v2::king_key(net, c, board.king_square(c));
                if (!(now == before[i])) {
                    ++king_key_changes;
                    forge::nnue::v2::refresh_cached(net, cache, forge::nnue::v2::pieces_of(board), board.king_square(c), c,
                                                    inc->values[i].data());
                } else {
                    forge::nnue::v2::update(net, c, now, parent->values[i].data(), inc->values[i].data(), dirty);
                }
                forge::nnue::v2::refresh(net, board, c, full->values[i].data());
                forge::nnue::v2::refresh_cached(net, cache, forge::nnue::v2::pieces_of(board), board.king_square(c), c,
                                                cached->values[i].data());
            }
            ++checked;
            if (!same(*inc, *full) || !same(*cached, *full)) {
                if (++mismatches <= 5) std::cerr << "MISMATCH game " << g << " ply " << p << " fen " << board.fen() << "\n";
            }
        }
    }
    std::cout << "walk: games " << games << " plies checked " << checked << " king-key changes " << king_key_changes
              << " mismatches " << mismatches << "\n";
    return mismatches == 0 && checked > 0 ? 0 : 1;
}

} // namespace

int main(int argc, char** argv) {
    const bool walking = argc == 6 && std::string(argv[1]) == "--walk";
    if (!walking && argc != 3) {
        std::cerr << "usage: v2_eval_o30 <net.nnue2> <fens.txt> | --walk <net.nnue2> <seed> <games> <plies>\n";
        return 2;
    }
    std::string error;
    if (!forge::nnue::v2::load(argv[walking ? 2 : 1], &error)) {
        std::cerr << "load failed: " << error << "\n";
        return 2;
    }
    const forge::nnue::v2::Net& net = *forge::nnue::v2::loaded();
    std::cerr << forge::nnue::v2::summary(net) << "\n";
    if (walking) return walk(net, std::stoull(argv[3]), std::stoi(argv[4]), std::stoi(argv[5]));
    std::ifstream in(argv[2]);
    std::string fen;
    auto accumulator = std::make_unique<forge::nnue::Accumulator>();
    while (std::getline(in, fen)) {
        if (!fen.empty() && fen.back() == '\r') fen.pop_back();
        if (fen.empty()) continue;
        forge::Board board;
        if (!board.set_fen(fen)) {
            std::cout << "ERR\n";
            continue;
        }
        forge::nnue::v2::refresh(net, board, forge::White, accumulator->values[0].data());
        forge::nnue::v2::refresh(net, board, forge::Black, accumulator->values[1].data());
        std::cout << forge::nnue::v2::evaluate(net, board, *accumulator) << "\n";
    }
    return 0;
}
