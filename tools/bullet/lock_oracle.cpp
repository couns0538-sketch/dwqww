// Standalone evaluation oracle linked with byte-identical pinned AL1 engine sources.
// usage: lock_oracle <fens.txt> <cp.txt> [--accumulators FILE] [--hce FILE]
// Optional accumulator stream: white then black, HiddenSize float32 values each,
// per position in file order. The qualification manifest records host byte order.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"

#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 3 || argc % 2 == 0) {
        std::cerr << "usage: lock_oracle <fens.txt> <cp.txt> [--accumulators FILE] [--hce FILE]\n";
        return 2;
    }
    if (!forge::nnue::available()) {
        std::cerr << "no compiled-in network\n";
        return 2;
    }
    std::string accum_path;
    std::string hce_path;
    bool write_accum = false;
    bool write_hce = false;
    for (int i = 3; i < argc; i += 2) {
        const std::string option = argv[i];
        if (option == "--accumulators" && !write_accum) {
            write_accum = true;
            accum_path = argv[i + 1];
        } else if (option == "--hce" && !write_hce) {
            write_hce = true;
            hce_path = argv[i + 1];
        } else {
            std::cerr << "unknown or repeated option: " << option << '\n';
            return 2;
        }
    }
    // Validate the complete namespace before creating anything. Canonicalization
    // covers lexical aliases and symlinked parents; equivalent covers hardlinks.
    namespace fs = std::filesystem;
    try {
        std::vector<fs::path> paths{fs::weakly_canonical(argv[1])};
        std::vector<std::string> outputs{argv[2]};
        if (write_accum) outputs.push_back(accum_path);
        if (write_hce) outputs.push_back(hce_path);
        for (const auto& output : outputs) {
            const fs::path target = fs::weakly_canonical(output);
            for (const auto& other : paths) {
                if (target == other || (fs::exists(target) && fs::exists(other) && fs::equivalent(target, other))) {
                    std::cerr << "input/output paths alias\n";
                    return 2;
                }
            }
            if (fs::exists(fs::symlink_status(output))) {
                std::cerr << "refusing to overwrite existing output: " << output << '\n';
                return 2;
            }
            paths.push_back(target);
        }
    } catch (const fs::filesystem_error& error) {
        std::cerr << "path validation failed: " << error.what() << '\n';
        return 2;
    }
    std::ifstream fens(argv[1]);
    if (!fens) {
        std::cerr << "failed to open input\n";
        return 2;
    }
    using File = std::unique_ptr<std::FILE, decltype(&std::fclose)>;
    // The x flag protects existing files even if one appears after preflight.
    File cp(std::fopen(argv[2], "wbx"), &std::fclose);
    File accum(write_accum ? std::fopen(accum_path.c_str(), "wbx") : nullptr, &std::fclose);
    File hce(write_hce ? std::fopen(hce_path.c_str(), "wbx") : nullptr, &std::fclose);
    if (!cp || (write_accum && !accum) || (write_hce && !hce)) {
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
        std::fprintf(cp.get(), "%d\n", forge::nnue::evaluate(board, accumulator));
        if (write_hce) std::fprintf(hce.get(), "%d\n", evaluator.evaluate_uncached(board));
        if (write_accum) {
            for (const auto& perspective : accumulator.values) {
                std::fwrite(perspective.data(), sizeof(float), perspective.size(), accum.get());
            }
        }
        ++positions;
    }
    bool writes_ok = std::fflush(cp.get()) == 0 && std::ferror(cp.get()) == 0;
    if (write_accum) writes_ok = (std::fflush(accum.get()) == 0 && std::ferror(accum.get()) == 0) && writes_ok;
    if (write_hce) writes_ok = (std::fflush(hce.get()) == 0 && std::ferror(hce.get()) == 0) && writes_ok;
    if (!fens.eof() || !writes_ok || positions == 0) {
        std::cerr << "input/output error or empty corpus\n";
        return 1;
    }
    std::cout << "positions " << positions << " hidden " << forge::nnue::HiddenSize
              << " residual " << forge::nnue::residual() << '\n';
    return 0;
}
