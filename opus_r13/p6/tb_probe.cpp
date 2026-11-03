// R13 P6 (own code): WDL / DTZ of every FEN through the ported Syzygy prober (forge::syzygy, src/syzygy.inc included
// by src/search.cpp of the port), for the comparison with an independent prober (check_tb.py).
// Build against the port tree, e.g.
//   g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -march=x86-64-v3 -static -Iinclude \
//       tb_probe.cpp src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp -o tb_probe.exe
// usage: tb_probe <tables dir> <fens.txt>  -> per FEN: "<wdl> <dtz> <dtz_rounded>" or "NA" where a probe fails
#include "forge/board.hpp"
#include "forge/syzygy.hpp"

#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: tb_probe <tables dir> <fens.txt>\n";
        return 2;
    }
    const forge::syzygy::LoadSummary summary = forge::syzygy::load(argv[1]);
    std::cerr << "loaded " << summary.wdl_tables << " WDL, " << summary.dtz_tables << " DTZ, up to " << summary.max_pieces
              << " pieces, rejected " << summary.rejected << "\n";
    if (summary.wdl_tables == 0) return 2;
    std::ifstream in(argv[2]);
    if (!in) {
        std::cerr << "cannot open " << argv[2] << "\n";
        return 2;
    }
    long probed = 0;
    std::string fen;
    long line = 0;
    while (std::getline(in, fen)) {
        ++line;
        if (!fen.empty() && fen.back() == '\r') fen.pop_back();
        if (fen.empty()) continue;
        forge::Board board;
        std::string error;
        if (!board.set_fen(fen, &error)) {
            std::cerr << "line " << line << ": bad FEN (" << error << ")\n";
            return 1;
        }
        ++probed;
        int wdl = 0;
        int dtz = 0;
        bool rounded = false;
        const bool ok_wdl = forge::syzygy::probe_wdl(board, wdl);
        const bool ok_dtz = forge::syzygy::probe_dtz(board, dtz, rounded);
        if (!ok_wdl || !ok_dtz) {
            std::cout << "NA\n";
            continue;
        }
        std::cout << wdl << ' ' << dtz << ' ' << (rounded ? 1 : 0) << '\n';
    }
    if (probed == 0) {
        std::cerr << "no FENs in " << argv[2] << "\n";
        return 2;
    }
    return 0;
}
