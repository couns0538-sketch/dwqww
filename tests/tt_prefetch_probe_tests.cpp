// Job S13 (TT prefetch at every key change; 64-byte TT bucket), after Sol's
// forge_sol_S13_worker_prefetch_probe_20261026.cpp. Counts the TT prefetch
// requests of the ACTUAL src/search.cpp: this file includes it with
// __builtin_prefetch redirected to a counter (only TranspositionTable::prefetch
// in forge/search.hpp uses it; no other forge_core source includes that
// header), so the production sources are unchanged. The link must not pull
// the core archive's own search.cpp object: it would clash with these
// definitions, so a successful link shows that it was not used.
//
// Every build:  a TT bucket is one 64-byte line (sizeof 64, alignof 64, and
//               every prefetched bucket address is a multiple of 64), and the
//               existing prefetch sites (main search and quiescence make) are hit.
// Build with FORGE_S13_TT_CHILD_PREFETCH (UCI TtChildPrefetch): OFF and ON
//               searches of 4 positions to depth 10 return the same move,
//               ponder move, score, depth, seldepth, nodes and PV and the same
//               null-move attempts; ON issues at least one extra request per
//               null move (null child) and, summed over the positions, also
//               ProbCut child requests; `info string TtChildPrefetch active`
//               is printed once per Searcher and never when OFF.
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

namespace s13_probe {
std::uint64_t requests = 0;
std::uint64_t misaligned = 0;
void record(const void* address) {
    if (address == nullptr) throw std::runtime_error("null TT prefetch address");
    if (reinterpret_cast<std::uintptr_t>(address) % 64U != 0U) ++misaligned;
    ++requests;
}
} // namespace s13_probe

// Everything search.cpp needs was included above, so the redirection reaches
// only the TT prefetch of forge/search.hpp (first included by search.cpp).
#define __builtin_prefetch(address, ...) ::s13_probe::record(address)
#include "../src/search.cpp"
#undef __builtin_prefetch

namespace forge {
struct SearcherTestProbe {
    static std::uint64_t null_tries(const Worker& worker) { return worker.null_tries_; }
};
} // namespace forge

namespace {

int failures = 0;
int checks = 0;

void check(bool okay, const std::string& name) {
    ++checks;
    if (!okay) ++failures;
    std::cout << (okay ? "PASS " : "FAIL ") << name << '\n';
}

static_assert(sizeof(forge::TTCluster) == 64, "a TT bucket is 64 bytes");
static_assert(alignof(forge::TTCluster) == 64, "a TT bucket starts on a 64-byte line");

struct Run {
    forge::SearchInfo info;
    std::uint64_t prefetches = 0;
    std::uint64_t null_tries = 0;
    std::string output;
};

// Redirect std::cout for the searches (the ON marker is printed there).
struct Capture {
    std::ostringstream text;
    std::streambuf* previous;
    Capture() : previous(std::cout.rdbuf(text.rdbuf())) {}
    ~Capture() { std::cout.rdbuf(previous); }
    Capture(const Capture&) = delete;
    Capture& operator=(const Capture&) = delete;
};

Run run(const std::string& fen, bool enabled) {
    forge::Board board;
    if (!board.set_fen(fen)) throw std::runtime_error("invalid test FEN");
    forge::Searcher searcher(16, 1);
#ifdef FORGE_S13_TT_CHILD_PREFETCH
    searcher.set_s13_tt_child_prefetch(enabled);
#else
    if (enabled) throw std::logic_error("ON run needs FORGE_S13_TT_CHILD_PREFETCH");
#endif
    forge::SearchLimits limits;
    limits.depth = 10;
    Run result;
    {
        Capture output;
        s13_probe::requests = 0;
        result.info = searcher.search(board, limits, false);
        result.prefetches = s13_probe::requests;
        result.null_tries = forge::SearcherTestProbe::null_tries(searcher.main_worker());
        // A second search of the same Searcher must not repeat the active line.
        limits.depth = 1;
        (void)searcher.search(board, limits, false);
        result.output = output.text.str();
    }
    return result;
}

bool same(const forge::SearchInfo& a, const forge::SearchInfo& b) {
    return a.best_move == b.best_move && a.ponder_move == b.ponder_move && a.score == b.score && a.depth == b.depth &&
           a.seldepth == b.seldepth && a.nodes == b.nodes && a.pv == b.pv &&
           a.restricted_root_empty == b.restricted_root_empty;
}

} // namespace

int main() {
    try {
        const std::array<std::string, 4> fens{
            std::string(forge::Board::StandardStartFen),
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
            "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        };
#ifdef FORGE_S13_TT_CHILD_PREFETCH
        std::cout << "S13 TT prefetch probe (build switch FORGE_S13_TT_CHILD_PREFETCH on)\n";
#else
        std::cout << "S13 TT prefetch probe (default build: no TtChildPrefetch option)\n";
#endif
        std::uint64_t total_requests = 0;
        std::uint64_t total_null = 0;
        std::uint64_t total_probcut = 0;
        bool parity = true;
        bool null_children = true;
        bool quiet_off = true;
        bool marker_once = true;
        for (std::size_t i = 0; i < fens.size(); ++i) {
            const Run off = run(fens[i], false);
            total_requests += off.prefetches;
            quiet_off = quiet_off && off.output.empty();
#ifdef FORGE_S13_TT_CHILD_PREFETCH
            const Run on = run(fens[i], true);
            const bool equal = same(off.info, on.info) && off.null_tries == on.null_tries;
            parity = parity && equal;
            null_children = null_children && on.prefetches >= off.prefetches + on.null_tries;
            marker_once = marker_once && on.output == "info string TtChildPrefetch active\n";
            const std::uint64_t probcut = on.prefetches >= off.prefetches + on.null_tries
                                              ? on.prefetches - off.prefetches - on.null_tries : 0;
            total_null += on.null_tries;
            total_probcut += probcut;
            std::cout << "case " << i << " nodes " << off.info.nodes << '/' << on.info.nodes << " move "
                      << forge::Board::move_to_uci(off.info.best_move) << '/' << forge::Board::move_to_uci(on.info.best_move)
                      << " score " << off.info.score << '/' << on.info.score << " prefetch off " << off.prefetches
                      << " on " << on.prefetches << " null_child " << on.null_tries << " probcut_child_derived " << probcut
                      << (equal ? "" : " DIFFERENT") << '\n';
#else
            std::cout << "case " << i << " nodes " << off.info.nodes << " move " << forge::Board::move_to_uci(off.info.best_move)
                      << " score " << off.info.score << " prefetch " << off.prefetches << " null_tries " << off.null_tries << '\n';
#endif
        }
        std::cout << "prefetch requests with the option off: " << total_requests << ", misaligned bucket addresses: "
                  << s13_probe::misaligned << '\n';
        check(total_requests > 0, "existing TT prefetch sites are reached");
        check(s13_probe::misaligned == 0, "every prefetched TT bucket address is 64-byte aligned (one cache line)");
        check(quiet_off, "no TtChildPrefetch output with the option off");
#ifdef FORGE_S13_TT_CHILD_PREFETCH
        std::cout << "null-move children " << total_null << ", ProbCut children (derived) " << total_probcut << '\n';
        check(parity, "OFF and ON give the same move, ponder, score, depth, seldepth, nodes, PV and null-move attempts");
        check(null_children, "ON prefetches at least once per null-move child");
        check(total_null > 0, "positions exercise the null-move child path");
        check(total_probcut > 0, "positions exercise the ProbCut child path");
        check(marker_once, "ON prints 'info string TtChildPrefetch active' exactly once per Searcher");
#else
        (void)parity; (void)null_children; (void)marker_once; (void)total_null; (void)total_probcut;
#endif
    } catch (const std::exception& error) {
        std::cout << "FAIL exception: " << error.what() << '\n';
        ++failures;
    }
    std::cout << (failures == 0 ? "ALL PASS " : "FAILURES ") << failures << " of " << checks << " checks failed\n";
    return failures == 0 ? 0 : 1;
}
