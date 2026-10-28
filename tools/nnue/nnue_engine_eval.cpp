// nnue_engine_eval (O4): the engine's own static evaluation of positions, with v2-network options applied
// the way the UCI layer applies them, next to the network alone and the hand-crafted evaluation (HCE).
//   nnue_engine_eval <in.fen> <out.tsv> [NNUEFile=<net.fnn2>] [NNUEKingBuckets=<n>] [PureNnue=0|1]
//                    [UseNNUE=true|false]
// Options are applied in the order given; an unusable v2 request is reported like the engine's fail-loud
// rule (`ERROR NNUE v2: ...`, exit status 2). Per position (one FEN per line, CRLF accepted):
//   engine   Worker::static_evaluate at the root of a real search stack (a depth-1 search sets the stack up,
//            as tests/nnue_v2_tests.cpp does), i.e. the evaluation the search uses (before correction history)
//   network  the active v2 net alone on a from-scratch accumulator (forge/nnue_v2.hpp evaluate), or "-" when no
//            v2 net is active
//   hce      Evaluator::evaluate_uncached (side to move)
// Prints how many positions have engine == network (a stand-alone net with PureNnue 1) and
// engine == clamp(hce + network) (a residual net). Exit status 0 when every position matches the rule that
// belongs to the active net (stand-alone: engine == network; residual: engine == clamp(hce + network)).
// With tools/nnue/v2_parity.py (PyTorch network == C++ network, bit for bit) this closes the chain
// PyTorch == engine evaluation for PureNnue.
//
//   nnue_engine_eval --walk <plies> <seed> [options as above]
// Evaluation-cost benchmark: a deterministic random make/unmake walk (the move choices depend only on the seed
// and the positions, so every option set replays the identical walk) that evaluates every new ply through
// Worker::static_evaluate (lazy incremental accumulators, as in search). Prints the evaluations, a checksum of
// the values and the time per evaluation; comparing two option sets on the same walk isolates their cost
// difference (e.g. the lock net + HCE vs the same weights flagged stand-alone with PureNnue = the HCE's cost).
#include "forge/nnue_v2.hpp"
#include "forge/search.hpp"
#include "forge/search_options.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static SearchStack* root(Worker& w) { return &w.stack_[4]; }
    static int eval(Worker& w, const Board& b, SearchStack* ss) { return w.static_evaluate(b, ss); }
    static void move(Worker& w, SearchStack* ss, const Board& b, Move m) { w.record_move(ss, b, m); (ss + 1)->ply = ss->ply + 1; }
};
} // namespace forge

using namespace forge;
namespace v2 = forge::nnue::v2;

namespace {

int walk_benchmark(Worker& worker, long plies, std::uint64_t seed) {
    const std::vector<std::string> starts = {
        std::string(Board::StandardStartFen),
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    };
    std::uint64_t s = seed | 1U;
    auto below = [&s](int n) {
        s ^= s >> 12U; s ^= s << 25U; s ^= s >> 27U;
        return static_cast<int>((s * 2685821657736338717ULL) % static_cast<std::uint64_t>(n));
    };
    const std::vector<Worker*> all{&worker};
    long done = 0, evals = 0;
    std::uint64_t checksum = 0;
    double seconds = 0.0;
    while (done < plies) {
        Board board;
        (void)board.set_fen(starts[static_cast<std::size_t>(below(static_cast<int>(starts.size())))]);
        SearchLimits limits;
        limits.depth = 1;
        (void)worker.search(board, limits, false, all);   // stack set-up, untimed
        SearchStack* root = SearcherTestProbe::root(worker);
        std::vector<std::pair<Move, Undo>> stack;
        const auto start = std::chrono::steady_clock::now();
        for (int t = 0; t < 400 && done < plies; ++t) {
            const int depth = static_cast<int>(stack.size());
            if (depth < 16 && (depth == 0 || below(100) < 60)) {
                const MoveList moves = board.legal_moves();
                if (moves.empty()) continue;
                const Move move = moves[static_cast<std::size_t>(below(static_cast<int>(moves.size())))];
                SearcherTestProbe::move(worker, root + depth, board, move);
                Undo undo;
                (void)board.make_move(move, undo);
                stack.emplace_back(move, undo);
                ++done;
                const int value = SearcherTestProbe::eval(worker, board, root + depth + 1);
                checksum = checksum * 1099511628211ULL + static_cast<std::uint64_t>(static_cast<std::int64_t>(value));
                ++evals;
            } else if (depth > 0) {
                board.unmake_move(stack.back().first, stack.back().second);
                stack.pop_back();
            }
        }
        seconds += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    }
    std::cout << "walk plies " << done << " evaluations " << evals << " value checksum " << std::hex << checksum << std::dec
              << " time_ms " << static_cast<long>(seconds * 1000.0) << " ns_per_eval " << static_cast<long>(seconds * 1e9 / static_cast<double>(evals))
              << " (walk incl. move generation and make/unmake)\n";
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: nnue_engine_eval <in.fen> <out.tsv> [NNUEFile=<net>] [NNUEKingBuckets=<n>] "
                     "[PureNnue=0|1] [UseNNUE=true|false]\n"
                     "       nnue_engine_eval --walk <plies> <seed> [options]\n";
        return 2;
    }
    const bool walk = std::string(argv[1]) == "--walk";
    if (walk && argc < 4) {
        std::cerr << "usage: nnue_engine_eval --walk <plies> <seed> [options]\n";
        return 2;
    }
    std::string file;
    std::string load_error;
    for (int i = walk ? 4 : 3; i < argc; ++i) {
        const std::string arg = argv[i];
        const std::size_t eq = arg.find('=');
        const std::string name = arg.substr(0, eq);
        const std::string value = eq == std::string::npos ? "" : arg.substr(eq + 1);
        if (name == "NNUEFile") {
            file = value == "<empty>" ? std::string() : value;
            load_error.clear();
            if (file.empty()) v2::unload();
            else if (!v2::load(file, &load_error) && load_error.empty()) load_error = "load failed";
        } else if (name == "NNUEKingBuckets") {
            options::nnue_king_buckets = std::clamp(std::stoi(value), 0, 32);
        } else if (name == "PureNnue" && (value == "1" || value == "0" || value == "true" || value == "false")) {
            options::pure_nnue = value == "1" || value == "true";
        } else if (name == "UseNNUE" && (value == "true" || value == "false")) {
            nnue::enabled = value == "true";
        } else {
            std::cerr << "unknown option " << arg << '\n';
            return 2;
        }
        std::string state;
        (void)options::apply_nnue_v2(&state);
    }
    std::string state;
    const bool active = options::apply_nnue_v2(&state);
    const std::string problem = options::nnue_v2_problem(file, load_error);
    if (!problem.empty()) {
        std::cout << "ERROR NNUE v2: " << problem << '\n';
        return 2;
    }
    std::cout << "NNUE v2: " << state << '\n';
    const v2::Net* net = v2::active();

    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    if (walk) return walk_benchmark(*worker, std::stol(argv[2]), std::stoull(argv[3]));
    const std::vector<Worker*> all{worker.get()};
    std::ifstream in(argv[1]);
    std::ofstream out(argv[2], std::ios::binary);   // LF line ends on every platform
    out << "index\tengine\tnetwork\thce\n";
    long count = 0, engine_is_network = 0, engine_is_residual = 0;
    std::string line;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        if (line.empty()) continue;
        Board board;
        std::string error;
        if (!board.set_fen(line, &error)) {
            std::cerr << "bad FEN line " << count << ": " << error << '\n';
            return 2;
        }
        SearchLimits limits;
        limits.depth = 1;
        (void)worker->search(board, limits, false, all);   // sets the search stack up as a real search does
        // Recompute the root through the engine's own path (refresh cache / compiled-in refresh) rather than
        // reusing the accumulator the search left there.
        SearchStack* root = SearcherTestProbe::root(*worker);
        root->accumulator.valid = false;
        root->runtime_psqt.valid = false;
        const int engine = SearcherTestProbe::eval(*worker, board, root);
        const int hce = Evaluator::evaluate_uncached(board);
        out << count << '\t' << engine << '\t';
        if (net != nullptr) {
            nnue::Accumulator acc;
            v2::refresh(*net, board, White, acc.values[White].data());
            v2::refresh(*net, board, Black, acc.values[Black].data());
            const int network = v2::evaluate(*net, board, acc);
            engine_is_network += engine == network ? 1 : 0;
            engine_is_residual += engine == std::clamp(hce + network, -MateInMaxPly + 1, MateInMaxPly - 1) ? 1 : 0;
            out << network;
        } else {
            out << '-';
        }
        out << '\t' << hce << '\n';
        ++count;
    }
    std::cout << "positions " << count << "  active v2 net: " << (active ? "yes" : "no");
    bool ok = count > 0;
    if (net != nullptr) {
        std::cout << (net->residual ? " (residual)" : " (stand-alone)") << "\n"
                  << "engine == network alone:          " << engine_is_network << "/" << count << "\n"
                  << "engine == clamp(hce + network):   " << engine_is_residual << "/" << count << "\n";
        ok = ok && (net->residual ? engine_is_residual : engine_is_network) == count;
    } else {
        std::cout << "\n";
    }
    std::cout << (ok ? "PASS" : "FAIL") << '\n';
    return ok ? 0 : 1;
}
