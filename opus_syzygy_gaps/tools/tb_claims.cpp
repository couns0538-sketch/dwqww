// tb_claims.cpp - test driver for the instrumented tree (make_instr.py): searches FENs with interior probes limited to
// <card> pieces while all tables stay loaded as truth, and prints the claim statistics per site.
// usage: tb_claims <tables dir> <fens file> <card> <depth> [first N] [offset K] [Name=Value ...]
#include "forge/board.hpp"
#include "forge/search.hpp"
#include "forge/syzygy.hpp"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 5) {
        std::cerr << "usage: tb_claims <tables dir> <fens file> <card> <depth> [first N] [offset K]\n";
        return 2;
    }
    const auto summary = forge::syzygy::load(argv[1]);
    std::cout << "loaded " << summary.wdl_tables << " WDL, " << summary.dtz_tables << " DTZ, max " << summary.max_pieces << "\n";
    forge::syzygy::test_card = std::stoi(argv[3]);
    const int depth = std::stoi(argv[4]);
    const int first = argc > 5 ? std::stoi(argv[5]) : 0;
    const int offset = argc > 6 ? std::stoi(argv[6]) : 0;
    for (int i = 7; i < argc; ++i) {
        const std::string kv = argv[i];
        const auto eq = kv.find('=');
        bool found = false;
        for (const forge::tune::Parameter& p : forge::tune::parameters()) {
            if (kv.substr(0, eq) == p.name) {
                *p.value = std::stoi(kv.substr(eq + 1));
                found = true;
            }
        }
        if (!found) {
            std::cerr << "unknown option " << kv << std::endl;
            return 2;
        }
        std::cout << "option " << kv << std::endl;
    }
    std::uint64_t site_roots[forge::syzygy::ClaimSites] = {};
    std::uint64_t before[forge::syzygy::ClaimSites] = {};
    std::ifstream in(argv[2]);
    std::string line;
    forge::Searcher searcher(32);
    int n = 0;
    int skipped = 0;
    std::uint64_t nodes = 0;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        if (skipped < offset) {
            ++skipped;
            continue;
        }
        if (first != 0 && n >= first) break;
        forge::Board board;
        if (!board.set_fen(line)) {
            std::cerr << "bad fen " << line << "\n";
            return 1;
        }
        ++n;
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = depth;
        nodes += searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive).nodes;
        for (int i = 1; i < forge::syzygy::ClaimSites; ++i) {
            if (forge::syzygy::claim_sites[i].wrong != before[i]) ++site_roots[i];
            before[i] = forge::syzygy::claim_sites[i].wrong;
        }
    }
    std::cout << "roots " << n << " depth " << depth << " card " << forge::syzygy::test_card << " nodes " << nodes << "\n";
    for (int i = 1; i < forge::syzygy::ClaimSites; ++i) {
        const auto& s = forge::syzygy::claim_sites[i];
        if (s.events != 0) {
            std::cout << "site " << forge::syzygy::claim_site_name(i) << " events " << s.events << " wrong " << s.wrong
                      << " roots_with_wrong " << site_roots[i] << " unknown " << s.unknown << "\n";
        }
    }
    std::cout << "correction updates all " << forge::syzygy::corr_updates_all << " from TB-band scores " << forge::syzygy::corr_updates_tb
              << "\n";
    std::cout << "PV bound returns " << forge::syzygy::pv_bound_returns << " probe hits " << forge::syzygy::probe_hits.load() << "\n";
    return 0;
}
