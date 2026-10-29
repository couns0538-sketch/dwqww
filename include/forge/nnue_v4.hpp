#pragma once

// NNUE v4 (R5C): the v3 feature transformer (king-bucketed HalfKA, int16 accumulators, SCReLU) followed by the
// J7 second layer (L2 clipped-ReLU units, per-output-bucket linear output). File format and arithmetic:
// opus_r5/r5c/FNN4_FORMAT.md. Loaded at run time with UCI NNUEv4File and used only while UCI NNUEv4 is true and a
// file is loaded (forge::nnue_v4::active); otherwise nothing here runs and the default network evaluates.
//
// Exactness: every step is integer arithmetic whose partial sums are bounded by the loader (accumulators fit int16
// for 32 pieces, each layer-2 sum fits int32 in any order, the output is int64), so the scalar reference and the
// AVX2 kernel return the same value for every position. No floating point, no FMA.
//
// This version rebuilds both accumulators for every evaluation (no incremental updates): exact and simple, but
// much slower than the default network (see opus_r5/r5c/REPORT.md, NPS).

#include "forge/board.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace forge::nnue_v4 {

constexpr int QA = 255;
constexpr int SShift = 6;
constexpr int QW = 1024;
constexpr int QO = 256;
constexpr int Inputs = 768;
constexpr int HeaderBytes = 256;
constexpr std::int64_t One = std::int64_t{QA} * QA * QW >> SShift;  // 1,040,400: layer-2 value 1.0
constexpr int SMax = (QA * QA) >> SShift;                           // 1016: largest layer-2 input
constexpr std::uint32_t FlagResidual = 1;
constexpr std::uint32_t FlagMirror = 2;

struct Net {
    int hidden = 0;
    int king_buckets = 0;
    int output_buckets = 0;
    int l2 = 0;
    std::uint32_t flags = 0;
    int eval_scale = 0;
    std::array<std::uint8_t, 64> king_map{};
    std::array<std::uint8_t, 33> output_map{};
    std::vector<std::int16_t> w1;     // [king_buckets][768][hidden]
    std::vector<std::int16_t> b1;     // [hidden]
    std::vector<std::int16_t> l2w;    // [l2][2 * hidden]: side to move first, then the opponent
    std::vector<std::int32_t> l2b;    // [l2], unit 1/One
    std::vector<std::int16_t> l2o;    // [output_buckets][l2], unit 1/QO
    std::vector<std::int64_t> b_out;  // [output_buckets], unit 1/(One * QO)
    std::uint64_t checksum = 0;
    [[nodiscard]] bool residual() const { return (flags & FlagResidual) != 0; }
    [[nodiscard]] bool mirror() const { return (flags & FlagMirror) != 0; }
};

// FNV-1a 64 (offset basis 0xcbf29ce484222325, prime 0x100000001b3).
[[nodiscard]] std::uint64_t fnv1a64(const unsigned char* data, std::size_t size);
// Exact file size for a header (0 when the header fields are out of range).
[[nodiscard]] std::uint64_t file_size_for(int hidden, int king_buckets, int output_buckets, int l2);
// Parses a complete file image with the loader's rules (tests, tools).
[[nodiscard]] bool parse(const std::vector<unsigned char>& bytes, Net& out, std::string& error);
// Loads `path`: header and the exact file size are checked before any weight is read, then the checksum and the
// overflow bounds. On success the net replaces the loaded one; on failure the loaded net (or none) stays.
// Must not run while a search runs (the UCI layer only calls it between searches).
[[nodiscard]] bool load(const std::string& path, std::string& error);
void unload();
[[nodiscard]] const Net* loaded();
[[nodiscard]] std::string describe(const Net& net);

// UCI NNUEv4 (check, default false).
extern bool requested;
// requested && a net is loaded && UseNNUE: read by Worker::static_evaluate (one branch per evaluation).
extern bool active;
// Recomputes `active` after a change of requested, the loaded net or UseNNUE.
void refresh_active();

enum class Kernel { Scalar, Avx2 };
[[nodiscard]] bool kernel_available(Kernel kernel);
[[nodiscard]] Kernel best_kernel();
[[nodiscard]] const char* kernel_name(Kernel kernel);
// Network score in centipawns from the side to move's view, clamped to +-30000 (the residual hand-crafted part
// is added by the search, not here).
[[nodiscard]] int evaluate_with(const Net& net, const Board& board, Kernel kernel);
[[nodiscard]] int evaluate(const Net& net, const Board& board);  // best kernel

} // namespace forge::nnue_v4
