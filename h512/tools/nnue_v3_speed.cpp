// NNUE v3 speed probe (cloud CPU, 2026-11-13). Not a strength test.
// Times the operations a search evaluation actually does and prints a checksum of the
// centipawn outputs so a faster kernel can be checked for bit-exact results.
//
//   nnue_v3_speed <net.fnn3> [timed plies, default 200000]
#include "forge/board.hpp"
#include "forge/nnue_v3.hpp"

#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace {

double ns_per(std::chrono::steady_clock::duration d, long n) {
    return std::chrono::duration<double, std::nano>(d).count() / static_cast<double>(n);
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: nnue_v3_speed <net.fnn3> [timed plies]\n";
        return 2;
    }
    std::string error;
    if (!forge::nnue::v3::load(argv[1], &error)) {
        std::cerr << "ERROR " << error << '\n';
        return 1;
    }
    const forge::nnue::v3::Net& net = *forge::nnue::v3::loaded();
    const long timed = argc > 2 ? std::stol(argv[2]) : 200000L;
    double timer_ns = 0;
    {
        constexpr long n = 200000;
        const auto t0 = std::chrono::steady_clock::now();
        auto sink = t0;
        for (long i = 0; i < n; ++i) {
            sink += std::chrono::steady_clock::now() - std::chrono::steady_clock::now();
        }
        timer_ns = ns_per(std::chrono::steady_clock::now() - t0, n);
        if (sink.time_since_epoch().count() == 1) std::cout << "unreachable\n";
        std::cout << "timer_pair_ns " << timer_ns << '\n';
    }
    std::cout << "net hidden " << net.hidden << " king_buckets " << net.king_buckets
              << (net.mirror ? " mirrored" : "") << " output_buckets " << net.output_buckets
              << " kernel " << forge::nnue::v3::kernel_name() << " checksum " << std::hex << net.checksum << std::dec
              << '\n';

    // ---- output kernel only, on one refreshed start position ----
    {
        forge::Board board;
        auto acc = std::make_unique<forge::nnue::v3::Accumulator>();
        forge::nnue::v3::refresh(net, board, *acc);
        const int bucket = forge::nnue::v3::output_bucket(net, board);
        const std::int16_t* ours = acc->values[static_cast<std::size_t>(board.side_to_move())].data();
        const std::int16_t* theirs = acc->values[static_cast<std::size_t>(forge::opposite(board.side_to_move()))].data();
        const long reps = 200000;
        const std::int64_t once = forge::nnue::v3::output_sum(net, ours, theirs, bucket);
        const auto t0 = std::chrono::steady_clock::now();
        std::int64_t sink = 0;
        for (long i = 0; i < reps; ++i) sink += forge::nnue::v3::output_sum(net, ours, theirs, bucket);
        const auto t1 = std::chrono::steady_clock::now();
        std::cout << "output_sum_ns " << ns_per(t1 - t0, reps) << " sum " << once << " sink " << sink << '\n';
    }

    // ---- search-shaped walk: incremental make_valid + evaluate ----
    {
        constexpr int StackSize = 136;   // MaxPly + 8, without pulling the search translation unit in
        constexpr int MaxIndex = 4 + 80;
        forge::nnue::v3::WorkerState state;
        forge::nnue::v3::prepare(net, state, StackSize);
        std::vector<forge::nnue::DirtyPieces> dirty(static_cast<std::size_t>(StackSize));
        const auto dirty_of = [&](int k) -> const forge::nnue::DirtyPieces& { return dirty[static_cast<std::size_t>(k)]; };
        const std::string_view starts[] = {
            forge::Board::StandardStartFen,
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
            "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
            "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
            "2r2rk1/1bqnbpp1/1p1ppn1p/pP6/N1P1P3/P2B1N2/1B2QPPP/R2R2K1 b - - 0 16",
        };
        std::mt19937 rng(20261113);
        std::uniform_real_distribution<double> coin(0.0, 1.0);
        auto run = [&](long plies, bool time_it) {
            long done = 0;
            long evals = 0;
            long quiet = 0;
            long captures = 0;
            long kings = 0;
            std::int64_t checksum = 0;
            std::chrono::steady_clock::duration eval_time{};
            while (done < plies) {
                forge::Board board;
                if (!board.set_fen(starts[rng() % (sizeof(starts) / sizeof(starts[0]))])) return std::int64_t{-1};
                state.invalidate();
                int index = 4;
                std::vector<forge::Move> moves;
                std::vector<forge::Undo> undos;
                int game = 0;
                while (game < 80 && done < plies) {
                    if (index > 4 && (coin(rng) < 0.25 || index >= MaxIndex)) {
                        board.unmake_move(moves.back(), undos.back());
                        moves.pop_back();
                        undos.pop_back();
                        --index;
                        continue;
                    }
                    forge::MoveList legal = board.legal_moves();
                    if (legal.empty()) break;
                    forge::Move move = legal.begin()[static_cast<std::ptrdiff_t>(rng() % legal.size())];
                    const forge::nnue::DirtyPieces d = forge::nnue::dirty_pieces(board, move);
                    if (d.count == 2) ++quiet;
                    else if (d.count == 3) ++captures;
                    if (forge::piece_type(board.piece_at(move.from)) == forge::King) ++kings;
                    dirty[static_cast<std::size_t>(index + 1)] = d;
                    forge::Undo undo;
                    if (!board.make_move(move, undo)) break;
                    moves.push_back(move);
                    undos.push_back(undo);
                    ++index;
                    state.stack[static_cast<std::size_t>(index)].valid = false;
                    ++game;
                    ++done;
                    if ((done & 1) == 0) {
                        const auto t0 = std::chrono::steady_clock::now();
                        forge::nnue::v3::make_valid(net, state, index, board, dirty_of);
                        checksum += forge::nnue::v3::evaluate(net, board, state.stack[static_cast<std::size_t>(index)]);
                        eval_time += std::chrono::steady_clock::now() - t0;
                        ++evals;
                    }
                }
            }
            if (time_it) {
                std::cout << "walk_plies " << done << " evals " << evals << " quiet " << quiet << " captures " << captures
                          << " king_moves " << kings << " eval_only_ns " << ns_per(eval_time, evals) << " checksum " << checksum
                          << " refreshes " << state.cache.refreshes << " columns " << state.cache.columns << '\n';
            }
            return checksum;
        };
        (void)run(timed / 10, false);   // warmup, also fills the refresh cache the way a search does
        const auto warm_columns = state.cache.columns;
        const std::int64_t checksum = run(timed, true);
        std::cout << "warmup_columns " << warm_columns << " timed_checksum " << checksum << '\n';
    }

    // ---- cold king-bucket refresh: two positions that share a white king square and little else ----
    {
        forge::nnue::v3::WorkerState state;
        forge::nnue::v3::prepare(net, state, 8);
        forge::Board a;
        forge::Board b;
        (void)a.set_fen("r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8");
        (void)b.set_fen("6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1");
        const long reps = 1000000;   // ~0.2-1 s; shorter runs were scheduler noise on this VM
        std::int64_t checksum = 0;
        const auto t0 = std::chrono::steady_clock::now();
        for (long i = 0; i < reps; ++i) {
            forge::Board& board = (i & 1) == 0 ? a : b;
            forge::nnue::v3::Accumulator& acc = state.stack[4];
            acc.valid = false;
            forge::nnue::v3::refresh_cached(net, state.cache, board, acc);
            checksum += forge::nnue::v3::evaluate(net, board, acc);
        }
        const auto t1 = std::chrono::steady_clock::now();
        std::cout << "cold_refresh_ns " << ns_per(t1 - t0, reps) << " checksum " << checksum
                  << " refreshes " << state.cache.refreshes << " columns " << state.cache.columns << '\n';
    }
    return 0;
}
