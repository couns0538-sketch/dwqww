#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {

int failures = 0;

void expect(bool ok, const std::string& name) {
    if (ok) {
        std::cout << "ok " << name << '\n';
        return;
    }
    std::cout << "FAIL " << name << '\n';
    ++failures;
}

std::vector<unsigned char> read_file(const std::string& path) {
    std::ifstream input(path, std::ios::binary);
    input.seekg(0, std::ios::end);
    const auto length = input.tellg();
    input.seekg(0);
    std::vector<unsigned char> bytes(static_cast<std::size_t>(length));
    if (length > 0) input.read(reinterpret_cast<char*>(bytes.data()), length);
    return bytes;
}

void write_file(const std::string& path, const std::vector<unsigned char>& bytes) {
    std::ofstream output(path, std::ios::binary);
    output.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
}

int evaluate_fen(const char* fen) {
    forge::Board board;
    if (!board.set_fen(fen)) return 999999;
    forge::nnue::Accumulator accumulator;
    forge::nnue::refresh(board, accumulator);
    return forge::nnue::evaluate(board, accumulator);
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: nnue_file_test <lock-net>\n";
        return 2;
    }
    const std::string net_path = argv[1];
    const char* start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    const char* kiwipete = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    const int start_builtin = evaluate_fen(start);
    const int kiwi_builtin = evaluate_fen(kiwipete);

    std::string error;
    const bool loaded = forge::nnue::load_file(net_path, error);
    expect(loaded && error.empty(), "load converted net");
    expect(evaluate_fen(start) == start_builtin, "startpos eval matches built-in net");
    expect(evaluate_fen(kiwipete) == kiwi_builtin, "kiwipete eval matches built-in net");

    std::vector<unsigned char> bytes = read_file(net_path);
    expect(bytes.size() > 16 && bytes.size() >= 8, "converted file is non-empty");

    auto shifted = bytes;
    const std::uint16_t bias = std::uint16_t(shifted[shifted.size() - 2]) |
                               (std::uint16_t(shifted[shifted.size() - 1]) << 8);
    const std::uint16_t bumped = static_cast<std::uint16_t>(bias + 2000);
    shifted[shifted.size() - 2] = static_cast<unsigned char>(bumped);
    shifted[shifted.size() - 1] = static_cast<unsigned char>(bumped >> 8);
    const std::string shifted_path = net_path + ".shifted";
    write_file(shifted_path, shifted);
    expect(forge::nnue::load_file(shifted_path, error), "load shifted bias");
    const bool changed = evaluate_fen(start) != start_builtin || evaluate_fen(kiwipete) != kiwi_builtin;
    expect(changed, "shifted bias changes an evaluation");

    expect(forge::nnue::load_file("", error) && error.empty(), "empty path restores built-in net");
    expect(evaluate_fen(start) == start_builtin && evaluate_fen(kiwipete) == kiwi_builtin,
           "restored eval matches built-in net");

    auto magic = bytes;
    magic[0] = 'X';
    write_file(net_path + ".magic", magic);
    expect(!forge::nnue::load_file(net_path + ".magic", error) && error == "nnue: bad magic",
           "bad magic keeps the current net");
    expect(evaluate_fen(start) == start_builtin, "eval unchanged after bad magic");

    auto version = bytes;
    version[8] = 2;
    write_file(net_path + ".version", version);
    expect(!forge::nnue::load_file(net_path + ".version", error) && error == "nnue: unsupported version",
           "wrong version keeps the current net");

    auto hidden = bytes;
    hidden[12] = 128;
    hidden[13] = 0;
    write_file(net_path + ".hidden", hidden);
    expect(!forge::nnue::load_file(net_path + ".hidden", error) && error == "nnue: wrong size",
           "wrong hidden size keeps the current net");

    auto truncated = bytes;
    truncated.pop_back();
    write_file(net_path + ".short", truncated);
    expect(!forge::nnue::load_file(net_path + ".short", error) && error == "nnue: wrong size",
           "truncated file keeps the current net");

    auto extra = bytes;
    extra.push_back(0);
    write_file(net_path + ".extra", extra);
    expect(!forge::nnue::load_file(net_path + ".extra", error) && error == "nnue: wrong size",
           "oversized file keeps the current net");

    expect(!forge::nnue::load_file(net_path + ".missing", error) && error == "nnue: cannot open file",
           "missing file keeps the current net");
    expect(evaluate_fen(start) == start_builtin && evaluate_fen(kiwipete) == kiwi_builtin,
           "eval unchanged after rejected files");

    if (failures != 0) {
        std::cout << failures << " failed\n";
        return 1;
    }
    std::cout << "PASS\n";
    return 0;
}
