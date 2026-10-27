// nnue_v2_tool: helper for the v2 export parity check (tools/nnue/v2_parity.py).
//   nnue_v2_tool positions <out.fen> <count> <seed>
//       Diverse legal positions from random games (capture-biased so that every piece count from 32
//       down to 2 occurs; kings wander, so king buckets and mirroring are covered). Deterministic.
//   nnue_v2_tool eval <net.fnn2> <in.fen> <out_prefix>
//       Loads the v2 net with the engine's loader and, per position, computes the accumulators from
//       scratch with the engine's kernels (forge/nnue_v2.hpp) and the evaluation. Writes
//       <out_prefix>.tsv (index, side to move, king bucket/flip per perspective, piece count, raw output
//       float bits, centipawns) and <out_prefix>.acc (float32 [N][2][HiddenSize], White then Black
//       perspective). Also checks the refresh cache against the from-scratch refresh on every position.
#include "forge/nnue_v2.hpp"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <set>
#include <string>
#include <vector>

using namespace forge;
namespace v2 = forge::nnue::v2;

namespace {

struct Rng {
    std::uint64_t s;
    std::uint64_t next() {
        s ^= s >> 12U; s ^= s << 25U; s ^= s >> 27U;
        return s * 2685821657736338717ULL;
    }
    int below(int n) { return static_cast<int>(next() % static_cast<std::uint64_t>(n)); }
};

int positions(const std::string& out_path, int count, std::uint64_t seed) {
    const std::vector<std::string> starts = {
        std::string(Board::StandardStartFen),
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    };
    Rng rng{seed};
    std::set<std::string> seen;
    std::vector<std::string> fens;
    // Even coverage of the piece counts 2..32: at most `quota` positions per count (relaxed if the
    // random games cannot fill a count).
    const int quota = (count + 30) / 31;
    std::vector<int> per_count(33, 0);
    for (long game = 0; static_cast<int>(fens.size()) < count; ++game) {
        const bool relaxed = game > 200000;
        Board board;
        (void)board.set_fen(starts[static_cast<std::size_t>(rng.below(static_cast<int>(starts.size())))]);
        const int capture_bias = 20 + rng.below(50);   // percent
        const int keep = 4 + rng.below(10);            // percent of plies recorded
        // Games continue in bare-king endings, so kings also visit every square.
        for (int ply = 0; ply < 600 && static_cast<int>(fens.size()) < count; ++ply) {
            const MoveList moves = board.legal_moves();
            if (moves.empty()) break;
            std::vector<Move> captures;
            for (const Move& m : moves) if (m.is_capture()) captures.push_back(m);
            const Move move = !captures.empty() && rng.below(100) < capture_bias
                ? captures[static_cast<std::size_t>(rng.below(static_cast<int>(captures.size())))]
                : moves[static_cast<std::size_t>(rng.below(static_cast<int>(moves.size())))];
            Undo undo;
            (void)board.make_move(move, undo);
            const int pieces = popcount(board.occupied());
            if (rng.below(100) < keep && (relaxed || per_count[static_cast<std::size_t>(pieces)] < quota)) {
                const std::string fen = board.fen();
                if (seen.insert(fen).second) {
                    fens.push_back(fen);
                    ++per_count[static_cast<std::size_t>(pieces)];
                }
            }
        }
    }
    std::ofstream out(out_path, std::ios::binary);   // LF line ends on every platform
    for (const std::string& fen : fens) out << fen << '\n';
    std::cout << "wrote " << fens.size() << " positions to " << out_path << '\n';
    return 0;
}

int eval(const std::string& net_path, const std::string& fen_path, const std::string& prefix) {
    std::string error;
    if (!v2::load(net_path, &error)) {
        std::cerr << "cannot load " << net_path << ": " << error << '\n';
        return 2;
    }
    const v2::Net& net = *v2::loaded();
    v2::RefreshCache& cache = v2::cache(net, 0);
    std::ifstream in(fen_path);
    std::ofstream tsv(prefix + ".tsv", std::ios::binary);
    std::ofstream acc(prefix + ".acc", std::ios::binary);
    tsv << "index\tstm\twhite_bucket\twhite_flip\tblack_bucket\tblack_flip\tpieces\tout_bits\tcp\n";
    std::string line;
    int index = 0;
    int cache_mismatch = 0;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();   // CRLF input
        if (line.empty()) continue;
        Board board;
        if (!board.set_fen(line, &error)) {
            std::cerr << "bad FEN line " << index << ": " << error << '\n';
            return 2;
        }
        nnue::Accumulator a;
        v2::refresh(net, board, White, a.values[White].data());
        v2::refresh(net, board, Black, a.values[Black].data());
        nnue::Accumulator c;
        const v2::Pieces pieces = v2::pieces_of(board);
        v2::refresh_cached(net, cache, pieces, board.king_square(White), White, c.values[White].data());
        v2::refresh_cached(net, cache, pieces, board.king_square(Black), Black, c.values[Black].data());
        if (std::memcmp(a.values.data(), c.values.data(), sizeof(a.values)) != 0) ++cache_mismatch;
        const float out = v2::output(net, board, a);
        std::uint32_t bits = 0;
        std::memcpy(&bits, &out, sizeof(bits));
        const v2::KingKey wk = v2::king_key(net, White, board.king_square(White));
        const v2::KingKey bk = v2::king_key(net, Black, board.king_square(Black));
        char hex[16];
        std::snprintf(hex, sizeof(hex), "%08x", static_cast<unsigned>(bits));
        tsv << index << '\t' << (board.side_to_move() == White ? 0 : 1) << '\t' << wk.bucket << '\t' << wk.flip << '\t'
            << bk.bucket << '\t' << bk.flip << '\t' << popcount(board.occupied()) << '\t' << hex << '\t'
            << v2::evaluate(net, board, a) << '\n';
        acc.write(reinterpret_cast<const char*>(a.values.data()), static_cast<std::streamsize>(sizeof(a.values)));
        ++index;
    }
    std::cout << "evaluated " << index << " positions with " << net_path << " (king buckets " << net.king_buckets
              << (net.mirror ? ", mirrored" : "") << "); refresh cache vs from-scratch mismatches: " << cache_mismatch << '\n';
    return cache_mismatch == 0 ? 0 : 1;
}

} // namespace

int main(int argc, char** argv) {
    const std::string mode = argc > 1 ? argv[1] : "";
    if (mode == "positions" && argc == 5) return positions(argv[2], std::stoi(argv[3]), std::stoull(argv[4]));
    if (mode == "eval" && argc == 5) return eval(argv[2], argv[3], argv[4]);
    std::cerr << "usage: nnue_v2_tool positions <out.fen> <count> <seed>\n"
                 "       nnue_v2_tool eval <net.fnn2> <in.fen> <out_prefix>\n";
    return 2;
}
