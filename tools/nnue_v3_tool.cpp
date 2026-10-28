// NNUE v3 command-line tool (job FB1).
//   forge_nnue_v3_tool info <net>
//   forge_nnue_v3_tool eval <net> <fen file>      one line per FEN: cp bucket kb_w flip_w kb_b flip_b
//   forge_nnue_v3_tool sum  <net> <fen file>      one line per FEN: raw int64 output sum (before b2/scaling)
// cp is the network output alone (side to move, centipawns) computed with the fast path (cache refresh +
// compiled kernel); every position is also evaluated with the scalar reference and a difference is reported
// on stderr as MISMATCH (the exit status is then 3). The residual flag is reported by `info`.
#include "forge/board.hpp"
#include "forge/nnue_v3.hpp"
#include "forge/search.hpp"

#include <fstream>
#include <iostream>
#include <memory>
#include <string>

namespace {

int usage() {
    std::cerr << "usage: forge_nnue_v3_tool info <net> | eval <net> <fen file> | sum <net> <fen file>\n";
    return 2;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) return usage();
    const std::string command = argv[1];
    std::string error;
    if (!forge::nnue::v3::load(argv[2], &error)) {
        std::cerr << "ERROR NNUE v3: " << error << '\n';
        return 1;
    }
    const forge::nnue::v3::Net& net = *forge::nnue::v3::loaded();
    if (command == "info") {
        std::cout << forge::nnue::v3::describe(net) << '\n';
        return 0;
    }
    if ((command != "eval" && command != "sum") || argc < 4) return usage();
    std::ifstream in(argv[3]);
    if (!in) {
        std::cerr << "cannot open " << argv[3] << '\n';
        return 1;
    }
    auto state = std::make_unique<forge::nnue::v3::WorkerState>();
    forge::nnue::v3::prepare(net, *state, 8);
    std::string line;
    forge::Board board;
    int count = 0;
    int mismatches = 0;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        if (line.empty()) continue;
        if (!board.set_fen(line)) {
            std::cout << "BADFEN\n";
            continue;
        }
        const forge::nnue::v3::KingKey white = forge::nnue::v3::king_key(net, forge::White, board.king_square(forge::White));
        const forge::nnue::v3::KingKey black = forge::nnue::v3::king_key(net, forge::Black, board.king_square(forge::Black));
        const int bucket = forge::nnue::v3::output_bucket(net, board);
        forge::nnue::v3::Accumulator& accumulator = state->stack[4];
        forge::nnue::v3::refresh_cached(net, state->cache, board, accumulator);
        const forge::Color us = board.side_to_move();
        const std::int16_t* ours = accumulator.values[static_cast<std::size_t>(us)].data();
        const std::int16_t* theirs = accumulator.values[static_cast<std::size_t>(forge::opposite(us))].data();
        if (command == "eval") {
            const int fast = forge::nnue::v3::evaluate(net, board, accumulator);
            const int reference = forge::nnue::v3::evaluate_reference(net, board);
            if (fast != reference) {
                ++mismatches;
                std::cerr << "MISMATCH fast " << fast << " reference " << reference << " at " << line << '\n';
            }
            std::cout << fast << ' ' << bucket << ' '
                      << static_cast<int>(white.bucket) << ' ' << static_cast<int>(white.flip) << ' '
                      << static_cast<int>(black.bucket) << ' ' << static_cast<int>(black.flip) << '\n';
        } else {
            const std::int64_t fast = forge::nnue::v3::output_sum(net, ours, theirs, bucket);
            const std::int64_t reference = forge::nnue::v3::output_sum_scalar(net, ours, theirs, bucket);
            if (fast != reference) {
                ++mismatches;
                std::cerr << "MISMATCH sum fast " << fast << " reference " << reference << " at " << line << '\n';
            }
            std::cout << fast << '\n';
        }
        ++count;
    }
    std::cerr << count << " positions, kernel " << forge::nnue::v3::kernel_name() << ", fast-vs-reference mismatches " << mismatches
              << ", cache refreshes " << state->cache.refreshes << " columns " << state->cache.columns << '\n';
    return mismatches == 0 ? 0 : 3;
}
