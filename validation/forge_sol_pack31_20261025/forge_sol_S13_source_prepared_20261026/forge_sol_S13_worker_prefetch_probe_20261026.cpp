// Diagnostic only: count the actual search source's prefetch requests.
// Hardware prefetch is replaced only in this driver; production is unchanged.
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <memory>
#include <mutex>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/uci_output.hpp"

#ifndef FORGE_S13_TT_CHILD_PREFETCH
#error "Compile this diagnostic against the S13 candidate with its build switch ON"
#endif
#ifndef FORGE_S13_NATIVE_SEARCH_CPP
#error "Pass the exact candidate src/search.cpp path as a quoted include macro"
#endif

namespace s13_probe {
std::uint64_t requests = 0;
void record(const void* address) {
    if (address == nullptr) throw std::runtime_error("null TT prefetch address");
    ++requests;
}
}

// Dependencies were included above, so this intercepts Forge's one TT method.
#define __builtin_prefetch(address, ...) ::s13_probe::record(address)
#include FORGE_S13_NATIVE_SEARCH_CPP
#undef __builtin_prefetch

namespace forge {
struct SearcherTestProbe {
    static std::uint64_t null_tries(const Worker& worker) { return worker.null_tries_; }
};
}

namespace {
struct Capture {
    std::ostringstream text;
    std::streambuf* previous;
    Capture() : previous(std::cout.rdbuf(text.rdbuf())) {}
    ~Capture() { std::cout.rdbuf(previous); }
    Capture(const Capture&) = delete;
    Capture& operator=(const Capture&) = delete;
};

struct Run {
    forge::SearchInfo info;
    std::uint64_t prefetches;
    std::uint64_t null_tries;
};

void require(bool okay, const char* reason) {
    if (!okay) throw std::runtime_error(reason);
}

Run run(const std::string& fen, bool enabled) {
    forge::Board board;
    require(board.set_fen(fen), "invalid test FEN");
    forge::Searcher searcher(16, 1);
    searcher.set_s13_tt_child_prefetch(enabled);
    forge::SearchLimits limits;
    limits.depth = 10;
    Run result;
    {
        Capture output;
        s13_probe::requests = 0;
        result.info = searcher.search(board, limits, false);
        result.prefetches = s13_probe::requests;
        result.null_tries = forge::SearcherTestProbe::null_tries(searcher.main_worker());
        // A second search of the same facade must not repeat the active line.
        limits.depth = 1;
        (void)searcher.search(board, limits, false);
        require(output.text.str() == (enabled ? "info string TtChildPrefetch active\n" : ""),
                "OFF output or once-per-facade active marker mismatch");
    }
    return result;
}

bool same(const forge::SearchInfo& a, const forge::SearchInfo& b) {
    return a.best_move == b.best_move && a.ponder_move == b.ponder_move &&
           a.score == b.score && a.depth == b.depth && a.seldepth == b.seldepth &&
           a.nodes == b.nodes && a.pv == b.pv &&
           a.restricted_root_empty == b.restricted_root_empty;
}
}

int main() {
    try {
        const std::array<std::string, 4> fens{
            std::string(forge::Board::StandardStartFen),
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
            "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        };
        std::uint64_t total_null = 0;
        std::uint64_t total_probcut = 0;
        for (std::size_t i = 0; i < fens.size(); ++i) {
            const auto off = run(fens[i], false);
            const auto on = run(fens[i], true);
            require(same(off.info, on.info), "actual search result/node/PV parity mismatch");
            require(off.null_tries == on.null_tries, "null search path changed");
            require(on.prefetches >= off.prefetches + on.null_tries,
                    "missing new null-child requests or divergent prefetch accounting");
            const auto probcut = on.prefetches - off.prefetches - on.null_tries;
            total_null += on.null_tries;
            total_probcut += probcut;
            std::cout << "case=" << i << " nodes=" << on.info.nodes
                      << " off_prefetch=" << off.prefetches
                      << " on_prefetch=" << on.prefetches
                      << " null_child=" << on.null_tries
                      << " probcut_child_derived=" << probcut << '\n';
        }
        require(total_null > 0, "registered corpus did not cover null child path");
        require(total_probcut > 0, "registered corpus did not cover ProbCut child path");
        std::cout << "S13 actual-source diagnostic PASS; no speed or strength conclusion\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "S13 actual-source diagnostic FAIL: " << error.what() << '\n';
        return 1;
    }
}
