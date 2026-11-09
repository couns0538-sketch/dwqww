// zz_scan.cpp - own test tool: finds mutual zugzwangs by random sampling with the engine's reader (candidates are confirmed later by the oracle).
// Z: S to move, S has a non-pawn piece, not in check, S does not win; with the other side to move, the other side loses.
// usage: zz_scan <tables dir> <materials: all | list separated by commas> <samples> <seed> <max found>   -> FENs on stdout, counts on stderr
#include "forge/board.hpp"
#include "forge/search.hpp"
#include "forge/syzygy.hpp"

#include <filesystem>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <vector>

namespace {

std::string fen_of(const char* board, bool white_to_move) {
    std::string out;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const char c = board[rank * 8 + file];
            if (c == 0) {
                ++empty;
                continue;
            }
            if (empty != 0) {
                out += static_cast<char>('0' + empty);
                empty = 0;
            }
            out += c;
        }
        if (empty != 0) out += static_cast<char>('0' + empty);
        if (rank != 0) out += '/';
    }
    out += white_to_move ? " w - - 0 1" : " b - - 0 1";
    return out;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 6) {
        std::cerr << "usage: zz_scan <tables dir> <materials> <samples> <seed> <max found>\n";
        return 2;
    }
    const auto summary = forge::syzygy::load(argv[1]);
    std::cerr << "loaded " << summary.wdl_tables << " WDL\n";
    std::vector<std::string> materials;
    if (std::string(argv[2]) == "all") {
        for (const auto& e : std::filesystem::directory_iterator(argv[1])) {
            if (e.path().extension() == ".rtbw") materials.push_back(e.path().stem().string());
        }
    } else {
        std::stringstream ss(argv[2]);
        std::string m;
        while (std::getline(ss, m, ',')) materials.push_back(m);
    }
    const long long samples = std::stoll(argv[3]);
    std::mt19937_64 rng(std::stoull(argv[4]));
    const long long max_found = std::stoll(argv[5]);
    long long legal = 0;
    long long found = 0;
    for (long long n = 0; n < samples && found < max_found; ++n) {
        const std::string& material = materials[rng() % materials.size()];
        char board[64] = {};
        bool ok = true;
        bool white = true;
        bool have_white_piece = false;
        bool have_black_piece = false;
        for (const char c0 : material) {
            if (c0 == 'v') {
                white = false;
                continue;
            }
            int s = 0;
            for (int tries = 0;; ++tries) {
                s = static_cast<int>(rng() % 64);
                if (board[s] == 0 && !(c0 == 'P' && (s / 8 == 0 || s / 8 == 7))) break;
                if (tries > 200) {
                    ok = false;
                    break;
                }
            }
            if (!ok) break;
            board[s] = white ? c0 : static_cast<char>(c0 + 32);
            if (c0 != 'K' && c0 != 'P') (white ? have_white_piece : have_black_piece) = true;
        }
        if (!ok) continue;
        const bool stm_white = (rng() & 1) != 0;
        if (!(stm_white ? have_white_piece : have_black_piece)) continue;
        forge::Board a;
        forge::Board b;
        if (!a.set_fen(fen_of(board, stm_white)) || !b.set_fen(fen_of(board, !stm_white))) continue;
        if (a.in_check() || b.in_check() || !a.has_legal_move() || !b.has_legal_move()) continue;
        ++legal;
        int w1 = 0;
        int w2 = 0;
        if (!forge::syzygy::probe_wdl(b, w2) || w2 != -2) continue;
        if (!forge::syzygy::probe_wdl(a, w1) || w1 > 0) continue;
        std::cout << fen_of(board, stm_white) << '\t' << w1 << '\t' << w2 << '\n';
        ++found;
    }
    std::cerr << "samples " << samples << " legal " << legal << " found " << found << "\n";
    return 0;
}
