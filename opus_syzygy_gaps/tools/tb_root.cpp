// tb_root.cpp - white-box view of the root tablebase path (own test tool, not part of the engine).
// Reads lines "<six-field FEN>[ moves a b c]" from a file and writes, per line, tab separated:
//   line number, status, displayed score (or "-"), search_cardinality after prepare_root, used_dtz,
//   kept moves (space separated, "-" if the root was not restricted),
//   ranks ("uci:rank:value:rounded" per legal move), interior WDL probe of the root ("-" if it fails),
//   probe_wdl_with_counter ("-" if undecided or failing), root DTZ + rounded ("-" if failing).
// usage: tb_root <tables dir> <fens file> [rule50 0|1] [Name=Value ...]
// Build: plain_build.ps1 -Units bitboard,board,book,eval,eval_params,nnue,search -MoreSources tb_root.cpp
#include "forge/board.hpp"
#include "forge/search.hpp"
#include "forge/syzygy.hpp"

#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using forge::Board;
using forge::Move;
using forge::Undo;

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: tb_root <tables dir> <fens file> [rule50 0|1]\n";
        return 2;
    }
    const auto summary = forge::syzygy::load(argv[1]);
    std::cerr << "loaded " << summary.wdl_tables << " WDL, " << summary.dtz_tables << " DTZ, rejected " << summary.rejected
              << ", max " << summary.max_pieces << "\n";
    forge::options::syzygy_50_move_rule = argc < 4 || std::string(argv[3]) != "0";
    for (int i = 4; i < argc; ++i) {
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
    }
    std::ifstream in(argv[2]);
    if (!in) {
        std::cerr << "cannot open " << argv[2] << "\n";
        return 2;
    }
    std::string line;
    int number = 0;
    int bad = 0;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        ++number;
        std::string fen = line;
        std::string moves;
        const std::size_t cut = line.find(" moves ");
        if (cut != std::string::npos) {
            fen = line.substr(0, cut);
            moves = line.substr(cut + 7);
        }
        Board board;
        if (!board.set_fen(fen)) {
            std::cout << number << "\tBADFEN\n";
            ++bad;
            continue;
        }
        std::stringstream ms(moves);
        std::string uci;
        bool ok = true;
        while (ms >> uci) {
            const auto parsed = board.parse_uci(uci);
            if (!parsed) {
                ok = false;
                break;
            }
            Undo undo;
            (void)board.make_move(*parsed, undo);
        }
        if (!ok) {
            std::cout << number << "\tBADMOVE\n";
            ++bad;
            continue;
        }
        forge::SearchLimits limits;
        forge::syzygy::prepare_root(board, limits);
        const int display = forge::syzygy::root_display.load();
        std::ostringstream out;
        out << number << "\tok\t";
        if (display != 0) out << forge::syzygy::display_score(0);
        else out << '-';
        out << '\t' << forge::syzygy::search_cardinality.load() << '\t';
        Board copy = board;
        std::vector<forge::syzygy::RootRank> ranks;
        bool used_dtz = false;
        const bool ranked = forge::syzygy::rank_root_moves(copy, forge::options::syzygy_50_move_rule, ranks, used_dtz);
        out << (ranked ? (used_dtz ? 1 : 0) : -1) << '\t';
        if (limits.search_moves_specified) {
            bool first = true;
            for (const Move& m : limits.search_moves) {
                out << (first ? "" : " ") << Board::move_to_uci(m);
                first = false;
            }
        } else {
            out << '-';
        }
        out << '\t';
        bool first = true;
        for (const auto& r : ranks) {
            out << (first ? "" : " ") << Board::move_to_uci(r.move) << ':' << r.rank << ':' << r.value << ':' << (r.rounded ? 1 : 0);
            first = false;
        }
        if (first) out << '-';
        int wdl = 0;
        Board p1 = board;
        out << '\t';
        if (forge::syzygy::probe_wdl(p1, wdl)) out << wdl;
        else out << '-';
        out << '\t';
        Board p2 = board;
        if (forge::syzygy::probe_wdl_with_counter(p2, wdl)) out << wdl;
        else out << '-';
        out << '\t';
        Board p3 = board;
        int dtz = 0;
        bool rounded = false;
        if (forge::syzygy::probe_dtz(p3, dtz, rounded)) out << dtz << ':' << (rounded ? 1 : 0);
        else out << '-';
        std::cout << out.str() << '\n';
    }
    std::cerr << "lines " << number << " bad " << bad << "\n";
    return bad == 0 ? 0 : 1;
}
