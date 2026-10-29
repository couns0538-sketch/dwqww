// Astra R2 B3: focused regression of the bundle's existing v2 loader preflight.
// IDEA_SOURCE: Forge's documented FORGENN2 format and existing loader tests.
// No engine code or network format change; no third-party engine implementation.
#include "forge/nnue_v2.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
namespace nnue = forge::nnue;
namespace v2 = forge::nnue::v2;
namespace {
using Header = std::array<unsigned char, v2::HeaderBytes>;
int checks = 0;
int failures = 0;
void check(bool okay, const std::string& label) {
    ++checks;
    if (!okay) ++failures;
    std::cout << (okay ? "PASS " : "FAIL ") << label << '\n';
}
void put32(Header& h, std::size_t offset, std::uint32_t value) {
    for (std::size_t i = 0; i < 4; ++i) h[offset + i] = static_cast<unsigned char>(value >> (8U * i));
}
Header header() {
    Header h{};
    constexpr std::array<unsigned char, 8> magic{'F', 'O', 'R', 'G', 'E', 'N', 'N', '2'};
    std::copy(magic.begin(), magic.end(), h.begin());
    put32(h, 8, 2); put32(h, 12, v2::HeaderBytes); put32(h, 16, 0);
    put32(h, 20, nnue::InputCount); put32(h, 24, nnue::HiddenSize);
    put32(h, 28, 1); put32(h, 32, 1); put32(h, 36, 1); // residual, one input/output bucket
    put32(h, 40, std::bit_cast<std::uint32_t>(nnue::WeightScale));
    put32(h, 44, std::bit_cast<std::uint32_t>(nnue::OutputScale));
    put32(h, 48, std::bit_cast<std::uint32_t>(nnue::SigmoidK));
    // Both maps and reserved bytes are zero: the sole bucket is selected everywhere.
    return h;
}
fs::path new_run_directory(const fs::path& root) {
    fs::create_directories(root);
    const auto stamp = std::chrono::steady_clock::now().time_since_epoch().count();
    for (unsigned attempt = 0; attempt < 1000; ++attempt) {
        const auto path = root / ("run_" + std::to_string(stamp) + "_" + std::to_string(attempt));
        if (fs::create_directory(path)) return path;
    }
    throw std::runtime_error("could not create a new fixture directory");
}
void sparse_file(const fs::path& path, const Header& h, std::uint64_t size) {
    std::ofstream out(path, std::ios::binary);
    if (!out) throw std::runtime_error("cannot create " + path.string());
    const auto prefix = static_cast<std::streamsize>(std::min<std::uint64_t>(size, h.size()));
    out.write(reinterpret_cast<const char*>(h.data()), prefix);
    if (size > h.size()) {
        out.seekp(static_cast<std::streamoff>(size - 1U));
        out.put('\0');
    }
    out.close();
    if (!out || fs::file_size(path) != size) throw std::runtime_error("fixture write failed: " + path.string());
}
void valid_zero_net(const fs::path& path, const Header& h) {
    // Stream the documented i16 payload using one small zero block. This fixture is a valid
    // loader positive control, never a playing/training network and never used by a search.
    std::ofstream out(path, std::ios::binary);
    std::uint64_t hash = 0xcbf29ce484222325ULL;
    const auto write = [&](const unsigned char* bytes, std::size_t count) {
        out.write(reinterpret_cast<const char*>(bytes), static_cast<std::streamsize>(count));
        for (std::size_t i = 0; i < count; ++i) { hash ^= bytes[i]; hash *= 0x100000001b3ULL; }
    };
    write(h.data(), h.size());
    std::array<unsigned char, 4096> zeros{};
    auto remaining = v2::file_bytes(1, 1) - h.size() - 8U;
    while (remaining != 0U) {
        const auto chunk = static_cast<std::size_t>(std::min<std::uint64_t>(remaining, zeros.size()));
        write(zeros.data(), chunk);
        remaining -= chunk;
    }
    for (unsigned shift = 0; shift < 64; shift += 8) out.put(static_cast<char>(hash >> shift));
    out.close();
    if (!out || fs::file_size(path) != v2::file_bytes(1, 1)) throw std::runtime_error("valid fixture write failed");
}
struct Case {
    const char* name;
    Header bytes;
    std::uint64_t size;
    const char* error_phrase;
    std::uint64_t bytes_read;
};
}

int main(int argc, char** argv) {
    if (argc != 2) { std::cerr << "usage: forge_nnue_loader_preflight_tests <new-run-parent>\n"; return 2; }
    try {
        const fs::path dir = new_run_directory(argv[1]);
        const auto good_header = header();
        const auto valid_size = v2::file_bytes(1, 1);
        const auto largest = v2::file_bytes(v2::MaxKingBuckets, v2::MaxOutputBuckets,
                                           v2::FeatureSetThreats | v2::FeatureSetPawnPairs);
        const auto good_path = dir / "valid_zero_control.fnn2";
        valid_zero_net(good_path, good_header);
        auto bad_magic = good_header; bad_magic[0] = 'X';
        auto bad_version = good_header; put32(bad_version, 8, 3);
        auto bad_hidden = good_header; put32(bad_hidden, 24, nnue::HiddenSize + 1);
        const std::vector<Case> cases{
            {"empty", good_header, 0, "too short", 0},
            {"truncated_header", good_header, v2::HeaderBytes - 1U, "too short", 0},
            {"truncated_payload", good_header, valid_size - 1U, "does not match", v2::HeaderBytes},
            {"extra_payload_byte", good_header, valid_size + 1U, "does not match", v2::HeaderBytes},
            {"wrong_magic", bad_magic, valid_size, "bad magic", v2::HeaderBytes},
            {"wrong_version", bad_version, valid_size, "unsupported version", v2::HeaderBytes},
            {"wrong_hidden", bad_hidden, valid_size, "hidden size", v2::HeaderBytes},
            {"oversized_sparse", good_header, largest + 1U, "too large", 0},
        };
        std::cout << "fixtures " << dir << "\nvalid_bytes " << valid_size << "\nmax_valid_bytes " << largest << '\n';
        for (const auto& c : cases) {
            const fs::path path = dir / (std::string(c.name) + ".fnn2");
            sparse_file(path, c.bytes, c.size);
            std::string error;
            const bool primed = v2::load(good_path.string(), &error);
            check(primed && v2::loaded() != nullptr && v2::last_load_bytes_read() == valid_size,
                  std::string(c.name) + ": positive control loads and reads its complete payload");
            if (!primed) continue;
            check(v2::select(1, 0, &error) != nullptr, std::string(c.name) + ": positive control is active");
            error.clear();
            const bool accepted = v2::load(path.string(), &error);
            check(!accepted && error.find(c.error_phrase) != std::string::npos,
                  std::string(c.name) + ": clean rejection: " + error);
            check(v2::last_load_bytes_read() == c.bytes_read,
                  std::string(c.name) + ": bytes_read=" + std::to_string(v2::last_load_bytes_read()) +
                  " expected=" + std::to_string(c.bytes_read));
            check(v2::loaded() == nullptr && v2::active() == nullptr,
                  std::string(c.name) + ": no stale loaded or active net after failure");
        }
        check(!v2::load((dir / "empty.fnn2").string(), nullptr) && v2::last_load_bytes_read() == 0,
              "empty file also rejects cleanly without an error-output pointer");
        v2::unload();
        std::cout << "nnue loader preflight: checks=" << checks << " failures=" << failures << '\n';
    } catch (const std::exception& error) {
        v2::unload();
        std::cerr << "FAIL exception: " << error.what() << '\n';
        return 1;
    }
    return failures == 0 ? 0 : 1;
}
