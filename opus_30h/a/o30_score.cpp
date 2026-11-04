// o30_score.cpp - Opus 30-h job holdout scorer (own code), built against the ported lock tree (opus_30h/a/v2port.patch).
// The crew's S31 holdout metric, computed with the engine's own v2 code: for every FPOS row,
//   net logit  = nnue::v2::output() of the v2 file (float32, the engine's arithmetic; no centipawn truncation)
//   pred       = sigmoid(net logit + hce * K / 400)   (residual net)  |  sigmoid(net logit)  (stand-alone net)
//              = sigmoid(hce * K / 400)                (no net: the hand-crafted evaluation alone)
//   teacher    = sigmoid(clamp(score * K / 400, -40, 40)),  stm_result from the meta byte
//   target(b)  = b * teacher + (1 - b) * stm_result,  MSE per blend b in {1.0, 0.6, 0.8}, K = 2.25.
// hce comes from the .hce file (what the lock net was trained with); --check-hce also recomputes the lock's own
// hand-crafted evaluation (Evaluator::evaluate_uncached on the FEN rebuilt from the row: no castling / ep, clocks 0 1)
// and counts rows where the two differ.
// Rows with |score| >= --mate-cut (default 30000) are skipped and counted (Astra R13's mate-row definition).
// usage: o30_score [--net <file.nnue2>] --pos <file.pos> --hce <file.hce> [--stride N] [--check-hce] [--mate-cut V]
//        [--dump <new file>]   (per-row b0.6 squared errors, float64, -1 = skipped row; for paired comparisons)
// Output: one JSON line.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/nnue_v2.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

namespace {

constexpr double K = 2.25;
const char* const PieceChars = ".PNBRQKpnbrqk";

bool read_all(const std::string& path, std::vector<unsigned char>& out) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;
    f.seekg(0, std::ios::end);
    const auto n = static_cast<std::size_t>(f.tellg());
    f.seekg(0, std::ios::beg);
    out.resize(n);
    f.read(reinterpret_cast<char*>(out.data()), static_cast<std::streamsize>(n));
    return static_cast<bool>(f);
}

std::string row_fen(const unsigned char* board, int stm) {
    std::string fen;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const int sq = rank * 8 + file;
            const int code = (sq & 1) != 0 ? board[sq / 2] >> 4 : board[sq / 2] & 15;
            if (code == 0) { ++empty; continue; }
            if (empty != 0) { fen += static_cast<char>('0' + empty); empty = 0; }
            fen += PieceChars[code];
        }
        if (empty != 0) fen += static_cast<char>('0' + empty);
        if (rank != 0) fen += '/';
    }
    fen += stm == 0 ? " w - - 0 1" : " b - - 0 1";
    return fen;
}

double sigmoid(double x) { return 1.0 / (1.0 + std::exp(-x)); }

std::string json_escape(const std::string& in) {
    std::string out;
    for (const char c : in) {
        if (c == '\\' || c == '"') out += '\\';
        out += c;
    }
    return out;
}

} // namespace

int main(int argc, char** argv) {
    std::string net_path, pos_path, hce_path;
    std::size_t stride = 1;
    bool check_hce = false;
    int mate_cut = 30000;
    std::string dump_path;
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto next = [&]() -> std::string { if (i + 1 >= argc) { std::cerr << "missing value for " << a << "\n"; std::exit(2); } return argv[++i]; };
        if (a == "--net") net_path = next();
        else if (a == "--pos") pos_path = next();
        else if (a == "--hce") hce_path = next();
        else if (a == "--stride") stride = static_cast<std::size_t>(std::stoul(next()));
        else if (a == "--check-hce") check_hce = true;
        else if (a == "--mate-cut") mate_cut = std::stoi(next());
        else if (a == "--dump") dump_path = next();
        else { std::cerr << "unknown argument " << a << "\n"; return 2; }
    }
    if (pos_path.empty() || hce_path.empty() || stride == 0) {
        std::cerr << "usage: o30_score [--net f.nnue2] --pos f.pos --hce f.hce [--stride N] [--check-hce] [--mate-cut V]\n";
        return 2;
    }
    const forge::nnue::v2::Net* net = nullptr;
    if (!net_path.empty()) {
        std::string error;
        if (!forge::nnue::v2::load(net_path, &error)) { std::cerr << "load failed: " << error << "\n"; return 2; }
        net = forge::nnue::v2::loaded();
    }
    std::vector<unsigned char> pos, hce;
    if (!read_all(pos_path, pos) || !read_all(hce_path, hce)) { std::cerr << "cannot read inputs\n"; return 2; }
    if (pos.size() < 16 || std::string(pos.begin(), pos.begin() + 4) != "FPOS") { std::cerr << "bad FPOS\n"; return 2; }
    if (hce.size() < 16 || std::string(hce.begin(), hce.begin() + 4) != "FHCE") { std::cerr << "bad FHCE\n"; return 2; }
    std::uint64_t n = 0, nh = 0;
    for (int b = 7; b >= 0; --b) { n = (n << 8U) | pos[8 + b]; nh = (nh << 8U) | hce[8 + b]; }
    if (n != nh || pos.size() != 16 + 35 * n || hce.size() != 16 + 2 * n) { std::cerr << "row counts / sizes differ\n"; return 2; }
    const unsigned char* boards = pos.data() + 16;
    const unsigned char* scores = pos.data() + 16 + 32 * n;
    const unsigned char* metas = pos.data() + 16 + 34 * n;
    const unsigned char* hces = hce.data() + 16;
    const double blends[3] = {1.0, 0.6, 0.8};
    double sums[3] = {0, 0, 0};
    std::uint64_t used = 0, mates = 0, bad_fen = 0, hce_checked = 0, hce_diff = 0;
    auto acc = std::make_unique<forge::nnue::Accumulator>();
    // --dump: the b0.6 squared error of every row as float64, -1 for a skipped row (a fixed row order, so two dumps
    // of the same data compare row by row: o30_paired.py).
    std::vector<double> dump;
    if (!dump_path.empty()) dump.assign(static_cast<std::size_t>((n + stride - 1) / stride), -1.0);
    for (std::uint64_t r = 0; r < n; r += stride) {
        const auto score = static_cast<std::int16_t>(static_cast<std::uint16_t>(scores[2 * r] | (scores[2 * r + 1] << 8U)));
        const auto h = static_cast<std::int16_t>(static_cast<std::uint16_t>(hces[2 * r] | (hces[2 * r + 1] << 8U)));
        const int meta = metas[r];
        const int stm = meta & 1;
        const double white = (meta >> 1) * 0.5;
        const double stm_res = stm == 0 ? white : 1.0 - white;
        if (std::abs(static_cast<int>(score)) >= mate_cut) { ++mates; continue; }
        double logit = 0.0;
        if (net != nullptr || check_hce) {
            forge::Board board;
            if (!board.set_fen(row_fen(boards + 32 * r, stm))) { ++bad_fen; continue; }
            if (check_hce) {
                ++hce_checked;
                if (forge::Evaluator::evaluate_uncached(board) != h) ++hce_diff;
            }
            if (net != nullptr) {
                forge::nnue::v2::refresh(*net, board, forge::White, acc->values[0].data());
                forge::nnue::v2::refresh(*net, board, forge::Black, acc->values[1].data());
                logit = forge::nnue::v2::output(*net, board, *acc);
            }
        }
        if (net == nullptr || net->residual) logit += h * (K / 400.0);
        const double pred = sigmoid(logit);
        const double teacher = sigmoid(std::clamp(score * (K / 400.0), -40.0, 40.0));
        for (int b = 0; b < 3; ++b) {
            const double target = blends[b] * teacher + (1.0 - blends[b]) * stm_res;
            sums[b] += (pred - target) * (pred - target);
            if (b == 1 && !dump.empty()) dump[static_cast<std::size_t>(r / stride)] = (pred - target) * (pred - target);
        }
        ++used;
    }
    std::printf("{\"net\": \"%s\", \"pos\": \"%s\", \"rows\": %llu, \"used\": %llu, \"mate_rows_skipped\": %llu, "
                "\"bad_fen\": %llu, \"stride\": %llu, \"residual\": %s, \"mse_b1.0\": %.9f, \"mse_b0.6\": %.9f, \"mse_b0.8\": %.9f",
                json_escape(net_path).c_str(), json_escape(pos_path).c_str(), static_cast<unsigned long long>(n), static_cast<unsigned long long>(used),
                static_cast<unsigned long long>(mates), static_cast<unsigned long long>(bad_fen),
                static_cast<unsigned long long>(stride), net == nullptr ? "null" : (net->residual ? "true" : "false"),
                used ? sums[0] / used : 0.0, used ? sums[1] / used : 0.0, used ? sums[2] / used : 0.0);
    if (check_hce) std::printf(", \"hce_checked\": %llu, \"hce_differs\": %llu", static_cast<unsigned long long>(hce_checked),
                               static_cast<unsigned long long>(hce_diff));
    std::printf("}\n");
    if (!dump.empty()) {
        std::FILE* f = std::fopen(dump_path.c_str(), "wbx");
        if (f == nullptr) { std::cerr << "cannot create (or exists) " << dump_path << "\n"; return 2; }
        const bool ok = std::fwrite(dump.data(), sizeof(double), dump.size(), f) == dump.size();
        std::fclose(f);
        if (!ok) { std::cerr << "short write " << dump_path << "\n"; return 2; }
    }
    return 0;
}
