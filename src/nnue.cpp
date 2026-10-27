#include "forge/nnue.hpp"
#include "forge/nnue_v2.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <memory>
#include <sstream>
#include <vector>

// The output layer uses SSE min/max/mul/add directly: compilers may not turn a
// float clamp into min/max instructions without -ffast-math, which left the
// AVX2 builds with slow scalar code. SSE2 is part of every x86-64 target.
#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)
#include <xmmintrin.h>
#define FORGE_NNUE_SSE 1
#else
#define FORGE_NNUE_SSE 0
#endif

#if defined(__AVX2__)
#include <immintrin.h>
#endif

#if __has_include("nnue_weights.inc")
#include "nnue_weights.inc"
#define FORGE_HAS_NNUE 1
#else
#define FORGE_HAS_NNUE 0
#endif
// Include files written before residual training existed carry no flag and
// hold stand-alone networks.
#ifndef FORGE_NNUE_RESIDUAL
#define FORGE_NNUE_RESIDUAL 0
#endif
#if FORGE_HAS_NNUE
static_assert(sizeof(NnueW1) / sizeof(NnueW1[0]) == static_cast<std::size_t>(forge::nnue::InputCount) * forge::nnue::HiddenSize,
              "nnue_weights.inc was trained for a different FORGE_NNUE_HIDDEN");
static_assert(sizeof(NnueB1) / sizeof(NnueB1[0]) == static_cast<std::size_t>(forge::nnue::HiddenSize), "nnue_weights.inc b1 size");
static_assert(sizeof(NnueW2) / sizeof(NnueW2[0]) == 2 * static_cast<std::size_t>(forge::nnue::HiddenSize), "nnue_weights.inc w2 size");
#endif

namespace forge::nnue {

bool enabled = true;

namespace {

struct Weights {
    std::unique_ptr<float[]> w1;   // [InputCount][HiddenSize]
    alignas(32) std::array<float, HiddenSize> b1{};
    alignas(32) std::array<float, 2 * HiddenSize> w2{};
    float b2 = 0.0F;
};

const Weights& weights() {
    static const Weights instance = [] {
        Weights w;
        w.w1 = std::make_unique<float[]>(static_cast<std::size_t>(InputCount) * HiddenSize);
#if FORGE_HAS_NNUE
        for (std::size_t i = 0; i < static_cast<std::size_t>(InputCount) * HiddenSize; ++i) {
            w.w1[i] = static_cast<float>(NnueW1[i]) / WeightScale;
        }
        for (std::size_t i = 0; i < HiddenSize; ++i) w.b1[i] = static_cast<float>(NnueB1[i]) / WeightScale;
        for (std::size_t i = 0; i < 2 * HiddenSize; ++i) w.w2[i] = static_cast<float>(NnueW2[i]) / OutputScale;
        w.b2 = static_cast<float>(NnueB2) / OutputScale;
#endif
        return w;
    }();
    return instance;
}

inline void add_feature(std::array<float, HiddenSize>& acc, const float* column) {
    for (int h = 0; h < HiddenSize; ++h) acc[static_cast<std::size_t>(h)] += column[h];
}

inline void sub_feature(std::array<float, HiddenSize>& acc, const float* column) {
    for (int h = 0; h < HiddenSize; ++h) acc[static_cast<std::size_t>(h)] -= column[h];
}

} // namespace

bool available() { return FORGE_HAS_NNUE != 0; }

bool residual() { return FORGE_HAS_NNUE != 0 && FORGE_NNUE_RESIDUAL != 0; }

void refresh(const Board& board, Accumulator& accumulator) {
    const Weights& w = weights();
    for (const Color perspective : {White, Black}) {
        auto& acc = accumulator.values[static_cast<std::size_t>(perspective)];
        acc = w.b1;
        Bitboard occupied = board.occupied();
        while (occupied != 0) {
            const int square = pop_lsb(occupied);
            const int index = feature_index(perspective, board.piece_at(square), square);
            add_feature(acc, w.w1.get() + static_cast<std::size_t>(index) * HiddenSize);
        }
    }
    accumulator.valid = true;
}

void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty) {
    const Weights& w = weights();
    // Quiet moves (including noncapturing promotions) remove one feature and
    // add one. Keep each lane's subtraction-then-addition order while avoiding
    // a full copy and two separate read/write passes over the child.
    if (dirty.count == 2 && !dirty.changes[0].add && dirty.changes[1].add) {
        for (const Color perspective : {White, Black}) {
            const auto& source = parent.values[static_cast<std::size_t>(perspective)];
            auto& destination = child.values[static_cast<std::size_t>(perspective)];
            const PieceChange& removed = dirty.changes[0];
            const PieceChange& added = dirty.changes[1];
            const float* removed_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, removed.piece, removed.square)) * HiddenSize;
            const float* added_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, added.piece, added.square)) * HiddenSize;
            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                destination[index] = (source[index] - removed_column[index]) + added_column[index];
            }
        }
        child.valid = true;
        return;
    }
    // Captures remove the mover and captured piece before adding the mover
    // (or promoted piece). Preserve both intermediate subtractions per lane.
    if (dirty.count == 3 && !dirty.changes[0].add && !dirty.changes[1].add && dirty.changes[2].add) {
        for (const Color perspective : {White, Black}) {
            const auto& source = parent.values[static_cast<std::size_t>(perspective)];
            auto& destination = child.values[static_cast<std::size_t>(perspective)];
            const PieceChange& removed0 = dirty.changes[0];
            const PieceChange& removed1 = dirty.changes[1];
            const PieceChange& added = dirty.changes[2];
            const float* removed0_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, removed0.piece, removed0.square)) * HiddenSize;
            const float* removed1_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, removed1.piece, removed1.square)) * HiddenSize;
            const float* added_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, added.piece, added.square)) * HiddenSize;
            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                destination[index] = ((source[index] - removed0_column[index]) - removed1_column[index]) + added_column[index];
            }
        }
        child.valid = true;
        return;
    }
    for (const Color perspective : {White, Black}) {
        auto& acc = child.values[static_cast<std::size_t>(perspective)];
        acc = parent.values[static_cast<std::size_t>(perspective)];
        for (int i = 0; i < dirty.count; ++i) {
            const PieceChange& change = dirty.changes[static_cast<std::size_t>(i)];
            const int index = feature_index(perspective, change.piece, change.square);
            const float* column = w.w1.get() + static_cast<std::size_t>(index) * HiddenSize;
            if (change.add) add_feature(acc, column);
            else sub_feature(acc, column);
        }
    }
    child.valid = true;
}

int evaluate(const Board& board, const Accumulator& accumulator) {
    const Weights& w = weights();
    const Color us = board.side_to_move();
    const auto& ours = accumulator.values[static_cast<std::size_t>(us)];
    const auto& theirs = accumulator.values[static_cast<std::size_t>(opposite(us))];
    // Sixteen independent partial sums (lane j takes the hidden units with
    // index % 16 == j, in increasing order) and then one ordered sum: the
    // association is fixed by the source, so every target (SSE, AVX2, AVX-512,
    // the scalar fallback) produces bit-identical results without -ffast-math.
    constexpr int Lanes = 16;
    static_assert(HiddenSize % Lanes == 0, "HiddenSize must be a multiple of the lane count");
    alignas(64) float lanes[Lanes];
#if defined(__AVX2__)
    const __m256 zero = _mm256_setzero_ps();
    const __m256 one = _mm256_set1_ps(1.0F);
    __m256 sums[2] = {zero, zero};
    for (int h = 0; h < HiddenSize; h += Lanes) {
        for (int k = 0; k < 2; ++k) {
            const std::size_t base = static_cast<std::size_t>(h + 8 * k);
            const __m256 a = _mm256_min_ps(_mm256_max_ps(_mm256_load_ps(ours.data() + base), zero), one);
            const __m256 b = _mm256_min_ps(_mm256_max_ps(_mm256_load_ps(theirs.data() + base), zero), one);
            const __m256 term = _mm256_add_ps(_mm256_mul_ps(_mm256_mul_ps(a, a), _mm256_load_ps(w.w2.data() + base)),
                                            _mm256_mul_ps(_mm256_mul_ps(b, b), _mm256_load_ps(w.w2.data() + HiddenSize + base)));
            sums[k] = _mm256_add_ps(sums[k], term);
        }
    }
    for (int k = 0; k < 2; ++k) _mm256_store_ps(lanes + 8 * k, sums[k]);
#elif FORGE_NNUE_SSE
    const __m128 zero = _mm_setzero_ps();
    const __m128 one = _mm_set1_ps(1.0F);
    __m128 sums[4] = {zero, zero, zero, zero};
    for (int h = 0; h < HiddenSize; h += Lanes) {
        for (int k = 0; k < 4; ++k) {
            const std::size_t base = static_cast<std::size_t>(h + 4 * k);
            const __m128 a = _mm_min_ps(_mm_max_ps(_mm_load_ps(ours.data() + base), zero), one);
            const __m128 b = _mm_min_ps(_mm_max_ps(_mm_load_ps(theirs.data() + base), zero), one);
            const __m128 term = _mm_add_ps(_mm_mul_ps(_mm_mul_ps(a, a), _mm_load_ps(w.w2.data() + base)),
                                           _mm_mul_ps(_mm_mul_ps(b, b), _mm_load_ps(w.w2.data() + HiddenSize + base)));
            sums[k] = _mm_add_ps(sums[k], term);
        }
    }
    for (int k = 0; k < 4; ++k) _mm_store_ps(lanes + 4 * k, sums[k]);
#else
    for (float& lane : lanes) lane = 0.0F;
    for (int h = 0; h < HiddenSize; h += Lanes) {
        for (int j = 0; j < Lanes; ++j) {
            const std::size_t index = static_cast<std::size_t>(h + j);
            const float a = std::min(std::max(ours[index], 0.0F), 1.0F);
            const float b = std::min(std::max(theirs[index], 0.0F), 1.0F);
            lanes[j] += a * a * w.w2[index] + b * b * w.w2[static_cast<std::size_t>(HiddenSize) + index];
        }
    }
#endif
    float out = w.b2;
    for (int j = 0; j < Lanes; ++j) out += lanes[j];
    const float centipawns = out * 400.0F / SigmoidK;
    return static_cast<int>(std::clamp(centipawns, -30000.0F, 30000.0F));
}

DirtyPieces dirty_pieces(const Board& board, const Move& move) {
    DirtyPieces dirty;
    const Color us = board.side_to_move();
    const Piece moved = board.piece_at(move.from);
    const Piece captured = board.captured_piece(move);
    dirty.remove(moved, move.from);
    if (captured != Empty) {
        const int captured_square = (move.flags & EnPassant) != 0U ? move.to - pawn_push_delta(us) : move.to;
        dirty.remove(captured, captured_square);
    }
    dirty.add(move.is_promotion() ? make_piece(us, move.promotion) : moved, move.to);
    if (move.is_castle()) {
        const bool king_side = (move.flags & KingCastle) != 0U;
        const int rook_from = us == White ? (king_side ? 7 : 0) : (king_side ? 63 : 56);
        const int rook_to = us == White ? (king_side ? 5 : 3) : (king_side ? 61 : 59);
        dirty.remove(make_piece(us, Rook), rook_from);
        dirty.add(make_piece(us, Rook), rook_to);
    }
    return dirty;
}

} // namespace forge::nnue

// ---------------------------------------------------------------------------
// v2 networks (forge/nnue_v2.hpp): loading and selection, all cold.
// This translation unit is linked before search.cpp; the functions above keep
// their code and addresses because nothing here is placed in .text (cold
// functions go to .text.unlikely, which the PE linker puts after every
// object's .text) and nothing here calls the local helpers above.
namespace forge::nnue::v2 {

// Constant-initialised: no dynamic initialisation or exit-time code.
const Net* active_net = nullptr;

namespace {

Net* loaded_net = nullptr;   // owned; deleted by load() / unload()
std::uint64_t last_bytes_read = 0;   // bytes of its file the last load() read

constexpr std::uint32_t FlagResidual = 1U;
constexpr std::uint32_t FlagMirror = 2U;
constexpr char Magic[8] = {'F', 'O', 'R', 'G', 'E', 'N', 'N', '2'};

[[gnu::cold]] std::uint32_t read_u32(const unsigned char* bytes, std::size_t offset) {
    return static_cast<std::uint32_t>(bytes[offset]) | static_cast<std::uint32_t>(bytes[offset + 1]) << 8U |
           static_cast<std::uint32_t>(bytes[offset + 2]) << 16U | static_cast<std::uint32_t>(bytes[offset + 3]) << 24U;
}

[[gnu::cold]] float read_f32(const unsigned char* bytes, std::size_t offset) {
    const std::uint32_t bits = read_u32(bytes, offset);
    float value = 0.0F;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

[[gnu::cold]] std::int16_t read_i16(const unsigned char* bytes, std::size_t offset) {
    return static_cast<std::int16_t>(static_cast<std::uint16_t>(bytes[offset] | (bytes[offset + 1] << 8U)));
}

[[gnu::cold]] std::uint64_t fnv1a64(const unsigned char* data, std::size_t size) {
    std::uint64_t hash = 0xcbf29ce484222325ULL;
    for (std::size_t i = 0; i < size; ++i) {
        hash ^= data[i];
        hash *= 0x100000001b3ULL;
    }
    return hash;
}

[[gnu::cold]] bool fail(std::string* error, const std::string& text) {
    if (error != nullptr) *error = text;
    return false;
}

} // namespace

[[gnu::cold]] std::uint64_t file_bytes(int king_buckets, int output_buckets, std::uint32_t feature_set) {
    const std::uint64_t w1 = static_cast<std::uint64_t>(king_buckets) * InputCount * HiddenSize;
    const std::uint64_t wt = (feature_set & FeatureSetThreats) != 0U ? static_cast<std::uint64_t>(ThreatFeatures) * HiddenSize : 0U;
    const std::uint64_t w2 = static_cast<std::uint64_t>(output_buckets) * 2U * HiddenSize;
    return static_cast<std::uint64_t>(HeaderBytes) + 2U * (w1 + wt + HiddenSize + w2 + static_cast<std::uint64_t>(output_buckets)) + 8U;
}

[[gnu::cold]] std::uint64_t last_load_bytes_read() { return last_bytes_read; }

[[gnu::cold]] bool load(const std::string& path, std::string* error) {
    // Whatever happens below, the previously loaded net is gone: after a failed load no net is
    // loaded, so the engine cannot evaluate with a net other than the one last requested.
    unload();
    last_bytes_read = 0;
    std::ifstream file(path, std::ios::binary);
    if (!file) return fail(error, "cannot open " + path);
    // The file size comes first (seek to the end): nothing is allocated or read before the size is
    // known to be the one the header implies.
    file.seekg(0, std::ios::end);
    const std::streamoff end = file.tellg();
    if (!file || end < 0) return fail(error, "cannot determine the size of " + path);
    const auto size = static_cast<std::uint64_t>(end);
    const std::uint64_t largest = file_bytes(MaxKingBuckets, MaxOutputBuckets, FeatureSetThreats);
    if (size < static_cast<std::uint64_t>(HeaderBytes) + 8U) {
        return fail(error, "file too short for a v2 net (" + std::to_string(size) + " bytes)");
    }
    if (size > largest) {
        return fail(error, "file too large for a v2 net (" + std::to_string(size) + " bytes; the largest valid v2 file has " +
                               std::to_string(largest) + ")");
    }
    std::array<unsigned char, HeaderBytes> header{};
    file.seekg(0, std::ios::beg);
    file.read(reinterpret_cast<char*>(header.data()), HeaderBytes);
    if (!file) return fail(error, "cannot read the header of " + path);
    last_bytes_read = HeaderBytes;
    const unsigned char* bytes = header.data();
    if (std::memcmp(bytes, Magic, sizeof(Magic)) != 0) return fail(error, "bad magic (not a FORGENN2 file)");
    if (read_u32(bytes, 8) != 2U) return fail(error, "unsupported version " + std::to_string(read_u32(bytes, 8)));
    if (read_u32(bytes, 12) != static_cast<std::uint32_t>(HeaderBytes)) return fail(error, "unexpected header size");
    const std::uint32_t feature_set = read_u32(bytes, 16);
    if ((feature_set & ~FeatureSetThreats) != 0U) return fail(error, "unsupported feature set " + std::to_string(feature_set));
    if (read_u32(bytes, 20) != static_cast<std::uint32_t>(InputCount)) return fail(error, "inputs per bucket must be 768");
    if (read_u32(bytes, 24) != static_cast<std::uint32_t>(HiddenSize)) {
        return fail(error, "hidden size " + std::to_string(read_u32(bytes, 24)) + " != engine hidden size " +
                               std::to_string(HiddenSize) + " (FORGE_NNUE_HIDDEN)");
    }
    const std::uint32_t king_buckets = read_u32(bytes, 28);
    const std::uint32_t output_buckets = read_u32(bytes, 32);
    const std::uint32_t flags = read_u32(bytes, 36);
    if (king_buckets < 1U || king_buckets > static_cast<std::uint32_t>(MaxKingBuckets)) return fail(error, "king buckets out of range 1-32");
    if (output_buckets < 1U || output_buckets > static_cast<std::uint32_t>(MaxOutputBuckets)) {
        return fail(error, "output buckets " + std::to_string(output_buckets) + " not supported (max " +
                               std::to_string(MaxOutputBuckets) + ")");
    }
    if ((flags & ~(FlagResidual | FlagMirror)) != 0U) return fail(error, "unknown flag bits");
    if (read_f32(bytes, 40) != WeightScale || read_f32(bytes, 44) != OutputScale || read_f32(bytes, 48) != SigmoidK) {
        return fail(error, "quantisation scales / sigmoid K differ from the engine's (4096, 4096, 2.25)");
    }
    for (std::size_t i = 0; i < 64; ++i) {
        if (bytes[52 + i] >= king_buckets) return fail(error, "king bucket map entry out of range");
    }
    for (std::size_t i = 0; i < 33; ++i) {
        if (bytes[116 + i] >= output_buckets) return fail(error, "output bucket map entry out of range");
    }
    for (std::size_t i = 149; i < static_cast<std::size_t>(HeaderBytes); ++i) {
        if (bytes[i] != 0U) return fail(error, "reserved header bytes are not zero");
    }
    const bool threats = (feature_set & FeatureSetThreats) != 0U;
    const std::size_t w1_count = static_cast<std::size_t>(king_buckets) * InputCount * HiddenSize;
    const std::size_t wt_count = threats ? static_cast<std::size_t>(ThreatFeatures) * HiddenSize : 0U;
    const std::size_t w2_count = static_cast<std::size_t>(output_buckets) * 2U * HiddenSize;
    const std::uint64_t expected = file_bytes(static_cast<int>(king_buckets), static_cast<int>(output_buckets), feature_set);
    if (size != expected) {
        return fail(error, "file size " + std::to_string(size) + " bytes does not match the " + std::to_string(expected) +
                               " bytes implied by its header (" + std::to_string(king_buckets) + " king buckets, " +
                               std::to_string(output_buckets) + " output buckets, hidden " + std::to_string(HiddenSize) +
                               (threats ? ", threat inputs" : "") + "); the weights were not read");
    }
    // Only now are the weight blocks allocated and read.
    std::vector<unsigned char> all(static_cast<std::size_t>(expected));
    std::copy(header.begin(), header.end(), all.begin());
    file.read(reinterpret_cast<char*>(all.data() + HeaderBytes), static_cast<std::streamsize>(expected - HeaderBytes));
    if (!file) return fail(error, "cannot read the weights of " + path);
    last_bytes_read = expected;
    bytes = all.data();
    std::uint64_t stored = 0;
    for (std::size_t i = 8; i-- > 0;) stored = (stored << 8U) | bytes[all.size() - 8U + i];
    const std::uint64_t checksum = fnv1a64(bytes, all.size() - 8U);
    if (stored != checksum) return fail(error, "checksum mismatch (file damaged)");

    auto net = std::make_unique<Net>();
    net->path = path;
    net->king_buckets = static_cast<int>(king_buckets);
    net->output_buckets = static_cast<int>(output_buckets);
    net->mirror = (flags & FlagMirror) != 0U;
    net->residual = (flags & FlagResidual) != 0U;
    net->threats = threats;
    net->checksum = checksum;
    std::copy(bytes + 52, bytes + 116, net->king_map.begin());
    std::copy(bytes + 116, bytes + 149, net->output_map.begin());
    net->w1.allocate(w1_count);
    if (threats) net->wt.allocate(wt_count);
    net->b1.allocate(HiddenSize);
    net->w2.allocate(w2_count);
    net->b2.assign(output_buckets, 0.0F);
    std::size_t offset = static_cast<std::size_t>(HeaderBytes);
    // Same de-quantisation as the compiled-in network (weights(): int / scale).
    for (std::size_t i = 0; i < w1_count; ++i, offset += 2) net->w1.data()[i] = static_cast<float>(read_i16(bytes, offset)) / WeightScale;
    for (std::size_t i = 0; i < wt_count; ++i, offset += 2) net->wt.data()[i] = static_cast<float>(read_i16(bytes, offset)) / WeightScale;
    for (std::size_t i = 0; i < HiddenSize; ++i, offset += 2) net->b1.data()[i] = static_cast<float>(read_i16(bytes, offset)) / WeightScale;
    for (std::size_t i = 0; i < w2_count; ++i, offset += 2) net->w2.data()[i] = static_cast<float>(read_i16(bytes, offset)) / OutputScale;
    for (std::size_t i = 0; i < output_buckets; ++i, offset += 2) net->b2[i] = static_cast<float>(read_i16(bytes, offset)) / OutputScale;

    loaded_net = net.release();
    return true;
}

[[gnu::cold]] void unload() {
    if (active_net == loaded_net) active_net = nullptr;
    delete loaded_net;
    loaded_net = nullptr;
}

[[gnu::cold]] const Net* loaded() { return loaded_net; }

[[gnu::cold]] std::string summary(const Net& net) {
    std::ostringstream out;
    out << net.path << " king buckets " << net.king_buckets << " output buckets " << net.output_buckets << " hidden "
        << HiddenSize << (net.mirror ? " mirrored" : " unmirrored") << (net.residual ? " residual" : " stand-alone")
        << (net.threats ? " threat inputs" : "") << " fnv1a " << std::hex << std::setw(16) << std::setfill('0') << net.checksum;
    return out.str();
}

[[gnu::cold]] const Net* select(int king_buckets, std::string* message) {
    active_net = nullptr;
    std::string text;
    if (king_buckets <= 0) {
        text = "off (NNUEKingBuckets 0): compiled-in network";
    } else if (loaded_net == nullptr) {
        text = "NNUEKingBuckets " + std::to_string(king_buckets) + " needs a v2 net (NNUEFile)";
    } else if (loaded_net->king_buckets != king_buckets) {
        text = "NNUEKingBuckets " + std::to_string(king_buckets) + " does not match the loaded net (" +
               std::to_string(loaded_net->king_buckets) + " king buckets)";
    } else {
        active_net = loaded_net;
        text = "active: " + summary(*loaded_net);
    }
    if (message != nullptr) *message = text;
    return active_net;
}

[[gnu::cold]] Description describe(const Net& net) {
    Description d;
    d.path = net.path;
    d.king_buckets = net.king_buckets;
    d.output_buckets = net.output_buckets;
    d.mirror = net.mirror;
    d.residual = net.residual;
    d.threats = net.threats;
    d.checksum = net.checksum;
    return d;
}

[[gnu::cold]] RefreshCache& make_cache(const Net& net, int worker_id) {
    std::unique_ptr<RefreshCache>& slot = net.caches[static_cast<std::size_t>(std::clamp(worker_id, 0, MaxWorkers - 1))];
    if (slot == nullptr) {
        auto cache = std::make_unique<RefreshCache>();
        cache->entries.resize(static_cast<std::size_t>(2 * net.king_buckets * 2));
        for (RefreshCache::Entry& entry : cache->entries) {
            std::copy(net.b1.data(), net.b1.data() + HiddenSize, entry.values.begin());
            entry.pieces.fill(0);
        }
        slot = std::move(cache);
    }
    return *slot;
}

} // namespace forge::nnue::v2
