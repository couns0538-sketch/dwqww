#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

namespace {

int fail(const std::string& what) {
    std::cerr << "FAIL " << what << '\n';
    return 1;
}

int score_start() {
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) return -999999;
    forge::nnue::Accumulator accumulator;
    forge::nnue::refresh(board, accumulator);
    return forge::nnue::evaluate(board, accumulator);
}

std::vector<unsigned char> read_all(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    return std::vector<unsigned char>(std::istreambuf_iterator<char>(in), {});
}

bool write_all(const std::string& path, const std::vector<unsigned char>& bytes) {
    std::ofstream out(path, std::ios::binary);
    if (!out) return false;
    out.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    return static_cast<bool>(out);
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: nnue_file_test <lock.forgenet>\n";
        return 2;
    }
    const std::string good_path = argv[1];
    const int compiled = score_start();
    if (compiled == -999999) return fail("startpos fen");
    std::cout << "compiled " << compiled << '\n';

    std::string error;
    if (!forge::nnue::load_file(good_path, error)) return fail("load converted lock net: " + error);
    const int loaded = score_start();
    std::cout << "loaded " << loaded << '\n';
    if (loaded != compiled) return fail("converted net eval differs from compiled net");
    std::cout << "ok converted net matches compiled eval\n";

    auto changed = read_all(good_path);
    if (changed.size() < 18) return fail("converted file is too small");
    const std::size_t last = changed.size() - 2;
    int b2 = static_cast<int>(changed[last]) | (static_cast<int>(changed[last + 1]) << 8);
    if ((b2 & 0x8000) != 0) b2 -= 0x10000;
    b2 += 400;
    changed[last] = static_cast<unsigned char>(static_cast<unsigned>(b2));
    changed[last + 1] = static_cast<unsigned char>(static_cast<unsigned>(b2) >> 8);
    const std::string changed_path = "/tmp/forge-t7-b2.bin";
    if (!write_all(changed_path, changed)) return fail("write changed net");
    if (!forge::nnue::load_file(changed_path, error)) return fail("load changed net: " + error);
    const int changed_score = score_start();
    std::cout << "changed " << changed_score << '\n';
    if (changed_score == compiled) return fail("changed b2 left the eval unchanged");
    std::cout << "ok changed b2 changes eval\n";

    auto bad_magic = read_all(good_path);
    bad_magic[0] = 'X';
    if (!write_all("/tmp/forge-t7-bad-magic.bin", bad_magic)) return fail("write bad magic");
    error.clear();
    if (forge::nnue::load_file("/tmp/forge-t7-bad-magic.bin", error)) return fail("bad magic was accepted");
    if (error.find("magic") == std::string::npos) return fail("bad magic reason: " + error);
    if (score_start() != changed_score) return fail("bad magic replaced the current net");
    std::cout << "ok bad magic kept current net (" << error << ")\n";

    auto bad_version = read_all(good_path);
    bad_version[8] = 2;
    if (!write_all("/tmp/forge-t7-bad-version.bin", bad_version)) return fail("write bad version");
    error.clear();
    if (forge::nnue::load_file("/tmp/forge-t7-bad-version.bin", error)) return fail("bad version was accepted");
    if (error.find("version") == std::string::npos) return fail("bad version reason: " + error);
    if (score_start() != changed_score) return fail("bad version replaced the current net");
    std::cout << "ok bad version kept current net (" << error << ")\n";

    auto bad_hidden = read_all(good_path);
    bad_hidden[12] = 128;
    bad_hidden[13] = 0;
    if (!write_all("/tmp/forge-t7-bad-hidden.bin", bad_hidden)) return fail("write bad hidden");
    error.clear();
    if (forge::nnue::load_file("/tmp/forge-t7-bad-hidden.bin", error)) return fail("bad hidden was accepted");
    if (error.find("size") == std::string::npos) return fail("bad hidden reason: " + error);
    if (score_start() != changed_score) return fail("bad hidden replaced the current net");
    std::cout << "ok bad hidden kept current net (" << error << ")\n";

    auto short_file = read_all(good_path);
    short_file.pop_back();
    if (!write_all("/tmp/forge-t7-short.bin", short_file)) return fail("write short file");
    error.clear();
    if (forge::nnue::load_file("/tmp/forge-t7-short.bin", error)) return fail("short file was accepted");
    if (error.find("size") == std::string::npos) return fail("short file reason: " + error);
    if (score_start() != changed_score) return fail("short file replaced the current net");
    std::cout << "ok short file kept current net (" << error << ")\n";

    error.clear();
    if (forge::nnue::load_file("/tmp/forge-t7-missing.bin", error)) return fail("missing file was accepted");
    if (score_start() != changed_score) return fail("missing file replaced the current net");
    std::cout << "ok missing file kept current net (" << error << ")\n";

    forge::nnue::use_compiled();
    const int restored = score_start();
    std::cout << "restored " << restored << '\n';
    if (restored != compiled) return fail("use_compiled did not restore the compiled eval");
    std::cout << "ok use_compiled restores eval\n";
    std::cout << "all checks passed\n";
    return 0;
}
