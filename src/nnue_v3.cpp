#include "forge/nnue_v3.hpp"

#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <new>
#include <sstream>

namespace forge::nnue::v3 {

bool requested = false;

namespace {

std::unique_ptr<Net> g_net;
std::string g_problem;

std::uint32_t read_u32(const std::uint8_t* p) {
    return static_cast<std::uint32_t>(p[0]) | (static_cast<std::uint32_t>(p[1]) << 8U) |
           (static_cast<std::uint32_t>(p[2]) << 16U) | (static_cast<std::uint32_t>(p[3]) << 24U);
}

std::int32_t read_i32(const std::uint8_t* p) { return static_cast<std::int32_t>(read_u32(p)); }

std::int16_t read_i16(const std::uint8_t* p) {
    return static_cast<std::int16_t>(static_cast<std::uint16_t>(p[0]) | static_cast<std::uint16_t>(static_cast<std::uint16_t>(p[1]) << 8U));
}

std::uint64_t read_u64(const std::uint8_t* p) {
    return static_cast<std::uint64_t>(read_u32(p)) | (static_cast<std::uint64_t>(read_u32(p + 4)) << 32U);
}

bool fail(std::string* error, const std::string& text) {
    if (error != nullptr) *error = text;
    return false;
}

} // namespace

AlignedInt16::~AlignedInt16() { release(); }

void AlignedInt16::allocate(std::size_t count) {
    release();
    data_ = static_cast<std::int16_t*>(::operator new(count * sizeof(std::int16_t), std::align_val_t{64}));
    size_ = count;
    std::fill(data_, data_ + count, static_cast<std::int16_t>(0));
}

void AlignedInt16::release() {
    if (data_ != nullptr) ::operator delete(data_, std::align_val_t{64});
    data_ = nullptr;
    size_ = 0;
}

std::uint64_t fnv1a64(const std::uint8_t* data, std::size_t size, std::uint64_t hash) {
    for (std::size_t i = 0; i < size; ++i) {
        hash ^= static_cast<std::uint64_t>(data[i]);
        hash *= 1099511628211ULL;
    }
    return hash;
}

std::size_t file_size_for(int hidden, int king_buckets, int output_buckets) {
    const std::size_t h = static_cast<std::size_t>(hidden);
    return static_cast<std::size_t>(HeaderBytes) +
           2 * static_cast<std::size_t>(king_buckets) * static_cast<std::size_t>(InputsPerBucket) * h +   // w1
           2 * h +                                                                                          // b1
           2 * static_cast<std::size_t>(output_buckets) * 2 * h +                                           // w2
           4 * static_cast<std::size_t>(output_buckets) +                                                   // b2
           8;                                                                                               // checksum
}

bool load(const std::string& path, std::string* error) {
    // No silent fallback: whatever happens below, a failed load leaves nothing loaded.
    g_net.reset();
    std::ifstream in(path, std::ios::binary);
    if (!in) return fail(error, "cannot open " + path);
    std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    if (bytes.size() < static_cast<std::size_t>(HeaderBytes) + 8) return fail(error, path + ": file too small for a v3 header");
    const std::uint8_t* h = bytes.data();
    if (std::memcmp(h, "FORGENN3", 8) != 0) return fail(error, path + ": bad magic (expected FORGENN3)");
    if (read_u32(h + 8) != 3U) return fail(error, path + ": unsupported version " + std::to_string(read_u32(h + 8)));
    if (read_u32(h + 12) != static_cast<std::uint32_t>(HeaderBytes)) return fail(error, path + ": header_bytes must be 192");
    if (read_u32(h + 16) != static_cast<std::uint32_t>(InputsPerBucket)) return fail(error, path + ": inputs must be 768");
    const std::uint32_t hidden = read_u32(h + 20);
    const std::uint32_t king_buckets = read_u32(h + 24);
    const std::uint32_t output_buckets = read_u32(h + 28);
    const std::uint32_t flags = read_u32(h + 32);
    const std::int32_t qa = read_i32(h + 36);
    const std::int32_t qb = read_i32(h + 40);
    const std::int32_t eval_scale = read_i32(h + 44);
    if (hidden < static_cast<std::uint32_t>(MinHidden) || hidden > static_cast<std::uint32_t>(MaxHidden) || hidden % 32U != 0U) {
        return fail(error, path + ": hidden must be a multiple of 32 in 32..1024, got " + std::to_string(hidden));
    }
    if (king_buckets < 1U || king_buckets > static_cast<std::uint32_t>(MaxKingBuckets)) {
        return fail(error, path + ": king_buckets must be 1..32, got " + std::to_string(king_buckets));
    }
    if (output_buckets < 1U || output_buckets > static_cast<std::uint32_t>(MaxOutputBuckets)) {
        return fail(error, path + ": output_buckets must be 1..16, got " + std::to_string(output_buckets));
    }
    if ((flags & ~(FlagResidual | FlagMirror)) != 0U) return fail(error, path + ": unknown flag bits");
    if (qa != QA || qb != QB) return fail(error, path + ": quantisation must be qa 255 / qb 64");
    if (eval_scale < 1 || eval_scale > MaxEvalScale) return fail(error, path + ": eval_scale must be 1..10000");
    for (int i = 145; i < HeaderBytes; ++i) {
        if (h[i] != 0) return fail(error, path + ": reserved header bytes must be zero");
    }
    const std::size_t expected = file_size_for(static_cast<int>(hidden), static_cast<int>(king_buckets), static_cast<int>(output_buckets));
    if (bytes.size() != expected) {
        return fail(error, path + ": file size " + std::to_string(bytes.size()) + " != expected " + std::to_string(expected));
    }
    const std::uint64_t stored = read_u64(bytes.data() + bytes.size() - 8);
    const std::uint64_t computed = fnv1a64(bytes.data(), bytes.size() - 8);
    if (stored != computed) return fail(error, path + ": checksum mismatch");

    auto net = std::make_unique<Net>();
    net->path = path;
    net->hidden = static_cast<int>(hidden);
    net->king_buckets = static_cast<int>(king_buckets);
    net->output_buckets = static_cast<int>(output_buckets);
    net->eval_scale = eval_scale;
    net->residual = (flags & FlagResidual) != 0U;
    net->mirror = (flags & FlagMirror) != 0U;
    net->checksum = stored;
    for (int i = 0; i < 64; ++i) {
        net->king_map[static_cast<std::size_t>(i)] = h[48 + i];
        if (h[48 + i] >= king_buckets) return fail(error, path + ": king_bucket_map entry out of range");
    }
    for (int i = 0; i < 33; ++i) {
        net->output_map[static_cast<std::size_t>(i)] = h[112 + i];
        if (h[112 + i] >= output_buckets) return fail(error, path + ": output_bucket_map entry out of range");
    }
    const std::size_t hs = static_cast<std::size_t>(net->hidden);
    const std::size_t w1_count = static_cast<std::size_t>(net->king_buckets) * static_cast<std::size_t>(InputsPerBucket) * hs;
    const std::size_t w2_count = static_cast<std::size_t>(net->output_buckets) * 2 * hs;
    net->w1.allocate(w1_count);
    net->b1.allocate(hs);
    net->w2.allocate(w2_count);
    net->b2.assign(static_cast<std::size_t>(net->output_buckets), 0);
    const std::uint8_t* p = h + HeaderBytes;
    int max_w1 = 0;
    for (std::size_t i = 0; i < w1_count; ++i, p += 2) {
        const std::int16_t v = read_i16(p);
        net->w1.data()[i] = v;
        max_w1 = std::max(max_w1, std::abs(static_cast<int>(v)));
    }
    int max_b1 = 0;
    for (std::size_t i = 0; i < hs; ++i, p += 2) {
        const std::int16_t v = read_i16(p);
        net->b1.data()[i] = v;
        max_b1 = std::max(max_b1, std::abs(static_cast<int>(v)));
    }
    int max_w2 = 0;
    for (std::size_t i = 0; i < w2_count; ++i, p += 2) {
        const std::int16_t v = read_i16(p);
        net->w2.data()[i] = v;
        max_w2 = std::max(max_w2, std::abs(static_cast<int>(v)));
    }
    for (std::size_t i = 0; i < static_cast<std::size_t>(net->output_buckets); ++i, p += 4) net->b2[i] = read_i32(p);
    net->max_abs_w1 = max_w1;
    net->max_abs_b1 = max_b1;
    net->max_abs_w2 = max_w2;
    if (max_w2 > MaxW2) return fail(error, path + ": |w2| must be <= 127, got " + std::to_string(max_w2));
    if (max_b1 + MaxPieces * max_w1 > 32767) {
        return fail(error, path + ": accumulator range: max|b1| + 32 * max|w1| = " + std::to_string(max_b1 + MaxPieces * max_w1) + " > 32767");
    }
    g_net = std::move(net);
    return true;
}

void unload() { g_net.reset(); }

const Net* loaded() { return g_net.get(); }

std::string describe(const Net& net) {
    std::ostringstream out;
    out << "v3 " << net.path << " hidden " << net.hidden << " king_buckets " << net.king_buckets
        << (net.mirror ? " mirrored" : "") << " output_buckets " << net.output_buckets
        << (net.residual ? " residual" : " standalone") << " eval_scale " << net.eval_scale
        << " checksum " << std::hex << net.checksum << std::dec
        << " max|w1| " << net.max_abs_w1 << " max|b1| " << net.max_abs_b1 << " max|w2| " << net.max_abs_w2;
    return out.str();
}

std::string problem() {
    if (!requested) return {};
    if (loaded() == nullptr) {
        if (!g_problem.empty()) return g_problem;
        return "NNUEArch is on but no v3 network is loaded (set NNUEArchFile)";
    }
    return {};
}

void set_problem(const std::string& text) { g_problem = text; }

KingKey king_key(const Net& net, Color perspective, int king_square) {
    const int kr = perspective == White ? king_square : king_square ^ 56;
    KingKey key;
    key.bucket = net.king_map[static_cast<std::size_t>(kr)];
    key.flip = (net.mirror && (kr & 7) >= 4) ? 7 : 0;
    return key;
}

int feature_index(KingKey key, Color perspective, Piece piece, int square) {
    const int relative_color = color_of(piece) == perspective ? 0 : 1;
    const int type = piece_type(piece) - 1;
    const int relative_square = (perspective == White ? square : square ^ 56) ^ static_cast<int>(key.flip);
    return static_cast<int>(key.bucket) * InputsPerBucket + (relative_color * 6 + type) * 64 + relative_square;
}

int output_bucket(const Net& net, const Board& board) {
    const int pieces = std::min(popcount(board.occupied()), MaxPieces);
    return net.output_map[static_cast<std::size_t>(pieces)];
}

void refresh_perspective(const Net& net, const Board& board, Color perspective, Accumulator& accumulator) {
    const int hidden = net.hidden;
    auto& acc = accumulator.values[static_cast<std::size_t>(perspective)];
    const KingKey key = king_key(net, perspective, board.king_square(perspective));
    accumulator.keys[static_cast<std::size_t>(perspective)] = key;
    const std::int16_t* b1 = net.b1.data();
    for (int h = 0; h < hidden; ++h) acc[static_cast<std::size_t>(h)] = b1[h];
    Bitboard occupied = board.occupied();
    while (occupied != 0) {
        const int square = pop_lsb(occupied);
        const std::int16_t* col = column(net, feature_index(key, perspective, board.piece_at(square), square));
        for (int h = 0; h < hidden; ++h) {
            acc[static_cast<std::size_t>(h)] = static_cast<std::int16_t>(acc[static_cast<std::size_t>(h)] + col[h]);
        }
    }
}

void refresh(const Net& net, const Board& board, Accumulator& accumulator) {
    refresh_perspective(net, board, White, accumulator);
    refresh_perspective(net, board, Black, accumulator);
    accumulator.valid = true;
}

std::int64_t output_sum_scalar(const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket) {
    const int hidden = net.hidden;
    const std::int16_t* w2 = net.w2.data() + static_cast<std::size_t>(bucket) * 2 * static_cast<std::size_t>(hidden);
    std::int64_t sum = 0;
    for (int h = 0; h < hidden; ++h) {
        const int a = std::clamp(static_cast<int>(ours[h]), 0, QA);
        sum += static_cast<std::int64_t>(a * a * static_cast<int>(w2[h]));
    }
    for (int h = 0; h < hidden; ++h) {
        const int b = std::clamp(static_cast<int>(theirs[h]), 0, QA);
        sum += static_cast<std::int64_t>(b * b * static_cast<int>(w2[hidden + h]));
    }
    return sum;
}

int finish(const Net& net, std::int64_t sum, int bucket) {
    const std::int64_t out = sum / QA + static_cast<std::int64_t>(net.b2[static_cast<std::size_t>(bucket)]);
    const std::int64_t centipawns = out * static_cast<std::int64_t>(net.eval_scale) / static_cast<std::int64_t>(QA * QB);
    return static_cast<int>(std::clamp<std::int64_t>(centipawns, -30000, 30000));
}

int evaluate(const Net& net, const Board& board, const Accumulator& accumulator) {
    const Color us = board.side_to_move();
    const int bucket = output_bucket(net, board);
    const std::int64_t sum = output_sum_scalar(net, accumulator.values[static_cast<std::size_t>(us)].data(),
                                               accumulator.values[static_cast<std::size_t>(opposite(us))].data(), bucket);
    return finish(net, sum, bucket);
}

int evaluate_reference(const Net& net, const Board& board) {
    auto accumulator = std::make_unique<Accumulator>();
    refresh(net, board, *accumulator);
    return evaluate(net, board, *accumulator);
}

} // namespace forge::nnue::v3
