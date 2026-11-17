#include "softnodes-preparation/uci_process.hpp"
#include <iostream>

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    constexpr const char* fen = "8/8/2n2r2/3qN1k1/8/8/8/K7 w - - 90 141";
    try {
        UciProcess engine(argv[1], 1, 15000);
        const auto result = engine.search(fen, 9, 30000, true);
        const auto shutdown = engine.finish(250);
        std::cout << "FEN " << fen << '\n' << engine.transcript();
        const bool passed = result.depth == 9 && result.score_kind == "mate"
            && result.score == -5 && result.nodes == 2566746
            && result.score_bound.empty() && engine.stderr_output().empty()
            && !result.move.empty() && result.move != "0000"
            && shutdown.reaped && shutdown.exit_code == 0
            && shutdown.signal == 0 && !shutdown.timed_out
            && shutdown.error.empty();
        std::cout << "EXPECTED depth=9 score=mate:-5 nodes=2566746\n"
                  << "RESULT depth=" << result.depth << " score=" << result.score_kind
                  << ':' << result.score << " nodes=" << result.nodes
                  << " move=" << result.move << " bound=" << result.score_bound
                  << " stderr_bytes=" << engine.stderr_output().size()
                  << " passed=" << passed << '\n';
        return passed ? 0 : 1;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
