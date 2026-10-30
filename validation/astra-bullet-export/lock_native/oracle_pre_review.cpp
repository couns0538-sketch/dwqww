// Standalone evaluation oracle linked with byte-identical pinned AL1 engine sources.
// usage: lock_oracle <fens.txt> <cp.txt> [--accumulators FILE] [--hce FILE]
// Optional accumulator stream: white then black, HiddenSize float32 values each,
// per position in file order. The qualification manifest records host byte order.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"

#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc < 3 || argc % 2 == 0) {
        std::cerr << "usage: lock_oracle <fens.txt> <cp.txt> [--accumulators FILE] [--hce FILE]\n";
        return 2;
    }
    if (!forge::nnue::available()) {
        std::cerr << "no compiled-in network\n";
        return 2;
    }
    std::ifstream fens(argv[1]);
    std::ofstream cp(argv[2], std::ios::binary);
    std::ofstream accum;
    std::ofstream hce;
    bool write_accum = false;
    bool write_hce = false;
    for (int i = 3; i < argc; i += 2) {
        const std::string option = argv[i];
        if (option == "--accumulators" && !write_accum) {
            write_accum = true;
            accum.open(argv[i + 1], std::ios::binary);
        } else if (option == "--hce" && !write_hce) {
            write_hce = true;
            hce.open(argv[i + 1], std::ios::binary);
        } else {
            std::cerr << "unknown or repeated option: " << option << '\n';
            return 2;
        }
    }
    if (!fens || !cp || (write_accum && !accum) || (write_hce && !hce)) {
        std::cerr << "failed to open input/output\n";
        return 2;
    }
    std::string line;
    std::size_t positions = 0;
    forge::Evaluator evaluator;
    while (std::getline(fens, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        const auto bar = line.find(" | ");
        if (bar != std::string::npos) line.resize(bar);
        forge::Board board;
        if (!board.set_fen(line)) {
            std::cerr << "invalid FEN at position " << positions + 1 << '\n';
            return 1;
        }
        forge::nnue::Accumulator accumulator;
        forge::nnue::refresh(board, accumulator);
        cp << forge::nnue::evaluate(board, accumulator) << '\n';
        if (write_hce) hce << evaluator.evaluate_uncached(board) << '\n';
        if (write_accum) {
            for (const auto& perspective : accumulator.values) {
                accum.write(reinterpret_cast<const char*>(perspective.data()),
                            static_cast<std::streamsize>(sizeof(float) * perspective.size()));
            }
        }
        ++positions;
    }
    cp.flush();
    if (write_accum) accum.flush();
    if (write_hce) hce.flush();
    if (!fens.eof() || !cp || (write_accum && !accum) || (write_hce && !hce) || positions == 0) {
        std::cerr << "input/output error or empty corpus\n";
        return 1;
    }
    std::cout << "positions " << positions << " hidden " << forge::nnue::HiddenSize
              << " residual " << forge::nnue::residual() << '\n';
    return 0;
}
