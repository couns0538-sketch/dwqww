#include "forge/nnue_v3.hpp"

#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <new>
#include <sstream>

#if defined(__AVX2__)
#include <immintrin.h>
#define FORGE_NNUE_V3_AVX2 1
#else
#define FORGE_NNUE_V3_AVX2 0
#endif

namespace forge::nnue::v3 {

bool requested = false;

namespace {

std::unique_ptr<Net> g_net;
std::string g_problem;
std::uint64_t g_generation = 0;

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

std::size_t cache_index(const Net& net, Color perspective, KingKey key) {
    return (static_cast<std::size_t>(perspective) * static_cast<std::size_t>(net.king_buckets) + key.bucket) * 2 +
           (key.flip != 0 ? 1 : 0);
}

inline void add_column_scalar(std::int16_t* acc, const std::int16_t* col, int hidden) {
    for (int h = 0; h < hidden; ++h) acc[h] = static_cast<std::int16_t>(acc[h] + col[h]);
}

inline void sub_column_scalar(std::int16_t* acc, const std::int16_t* col, int hidden) {
    for (int h = 0; h < hidden; ++h) acc[h] = static_cast<std::int16_t>(acc[h] - col[h]);
}

#if FORGE_NNUE_V3_AVX2
inline void add_column(std::int16_t* acc, const std::int16_t* col, int hidden) {
    for (int h = 0; h < hidden; h += 16) {
        _mm256_store_si256(reinterpret_cast<__m256i*>(acc + h),
                           _mm256_add_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(acc + h)),
                                            _mm256_load_si256(reinterpret_cast<const __m256i*>(col + h))));
    }
}

inline void sub_column(std::int16_t* acc, const std::int16_t* col, int hidden) {
    for (int h = 0; h < hidden; h += 16) {
        _mm256_store_si256(reinterpret_cast<__m256i*>(acc + h),
                           _mm256_sub_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(acc + h)),
                                            _mm256_load_si256(reinterpret_cast<const __m256i*>(col + h))));
    }
}
#else
inline void add_column(std::int16_t* acc, const std::int16_t* col, int hidden) { add_column_scalar(acc, col, hidden); }
inline void sub_column(std::int16_t* acc, const std::int16_t* col, int hidden) { sub_column_scalar(acc, col, hidden); }
#endif

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

const char* kernel_name() { return FORGE_NNUE_V3_AVX2 ? "avx2" : "scalar"; }

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
    net->generation = ++g_generation;
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
        << " max|w1| " << net.max_abs_w1 << " max|b1| " << net.max_abs_b1 << " max|w2| " << net.max_abs_w2
        << " kernel " << kernel_name();
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

Pieces pieces_of(const Board& board) {
    Pieces pieces{};
    for (int piece = WP; piece <= BK; ++piece) pieces[static_cast<std::size_t>(piece)] = board.pieces(static_cast<Piece>(piece));
    return pieces;
}

// ---- scalar reference path ----

void refresh_perspective(const Net& net, const Board& board, Color perspective, Accumulator& accumulator) {
    const int hidden = net.hidden;
    auto& acc = accumulator.values[static_cast<std::size_t>(perspective)];
    const int king_square = board.king_square(perspective);
    const KingKey key = king_key(net, perspective, king_square);
    accumulator.keys[static_cast<std::size_t>(perspective)] = key;
    accumulator.king_sq[static_cast<std::size_t>(perspective)] = static_cast<std::uint8_t>(king_square);
    const std::int16_t* b1 = net.b1.data();
    for (int h = 0; h < hidden; ++h) acc[static_cast<std::size_t>(h)] = b1[h];
    Bitboard occupied = board.occupied();
    while (occupied != 0) {
        const int square = pop_lsb(occupied);
        add_column_scalar(acc.data(), column(net, feature_index(key, perspective, board.piece_at(square), square)), hidden);
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

int evaluate_reference(const Net& net, const Board& board) {
    auto accumulator = std::make_unique<Accumulator>();
    refresh(net, board, *accumulator);
    const Color us = board.side_to_move();
    const int bucket = output_bucket(net, board);
    return finish(net, output_sum_scalar(net, accumulator->values[static_cast<std::size_t>(us)].data(),
                                         accumulator->values[static_cast<std::size_t>(opposite(us))].data(), bucket), bucket);
}

// ---- fast path ----

std::int64_t output_sum(const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket) {
#if FORGE_NNUE_V3_AVX2
    const int hidden = net.hidden;
    const std::int16_t* w2 = net.w2.data() + static_cast<std::size_t>(bucket) * 2 * static_cast<std::size_t>(hidden);
    const __m256i zero = _mm256_setzero_si256();
    const __m256i qa = _mm256_set1_epi16(static_cast<short>(QA));
    // Two int32 accumulators: each lane sums hidden / 8 exact terms of at most 255^2 * 127,
    // below 2^31 for every hidden size up to 1024 (bounds checked by the loader).
    __m256i sum0 = zero;
    __m256i sum1 = zero;
    for (int h = 0; h < hidden; h += 16) {
        const __m256i a = _mm256_min_epi16(_mm256_max_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(ours + h)), zero), qa);
        const __m256i b = _mm256_min_epi16(_mm256_max_epi16(_mm256_load_si256(reinterpret_cast<const __m256i*>(theirs + h)), zero), qa);
        const __m256i wa = _mm256_load_si256(reinterpret_cast<const __m256i*>(w2 + h));
        const __m256i wb = _mm256_load_si256(reinterpret_cast<const __m256i*>(w2 + hidden + h));
        sum0 = _mm256_add_epi32(sum0, _mm256_madd_epi16(_mm256_mullo_epi16(a, wa), a));
        sum1 = _mm256_add_epi32(sum1, _mm256_madd_epi16(_mm256_mullo_epi16(b, wb), b));
    }
    alignas(32) std::int32_t lanes[16];
    _mm256_store_si256(reinterpret_cast<__m256i*>(lanes), sum0);
    _mm256_store_si256(reinterpret_cast<__m256i*>(lanes + 8), sum1);
    std::int64_t sum = 0;
    for (const std::int32_t lane : lanes) sum += lane;
    return sum;
#else
    return output_sum_scalar(net, ours, theirs, bucket);
#endif
}

int evaluate(const Net& net, const Board& board, const Accumulator& accumulator) {
    const Color us = board.side_to_move();
    const int bucket = output_bucket(net, board);
    return finish(net, output_sum(net, accumulator.values[static_cast<std::size_t>(us)].data(),
                                  accumulator.values[static_cast<std::size_t>(opposite(us))].data(), bucket), bucket);
}

void prepare(const Net& net, WorkerState& state, int stack_size) {
    if (state.generation == net.generation && state.stack.size() == static_cast<std::size_t>(stack_size)) return;
    state.stack.assign(static_cast<std::size_t>(stack_size), Accumulator{});
    state.cache.entries.assign(static_cast<std::size_t>(2 * net.king_buckets * 2), RefreshCache::Entry{});
    for (RefreshCache::Entry& entry : state.cache.entries) {
        // An entry starts as the empty board: bias only, no pieces.
        std::copy_n(net.b1.data(), net.hidden, entry.values.data());
        entry.pieces.fill(0);
    }
    state.cache.generation = net.generation;
    state.cache.refreshes = 0;
    state.cache.columns = 0;
    state.generation = net.generation;
}

void apply_changes(const Net& net, const std::int16_t* source, std::int16_t* destination, KingKey key, Color perspective,
                   const DirtyPieces& dirty) {
    const int hidden = net.hidden;
    const std::int16_t* columns[4] = {nullptr, nullptr, nullptr, nullptr};
    bool adds[4] = {false, false, false, false};
    for (int i = 0; i < dirty.count; ++i) {
        const PieceChange& change = dirty.changes[static_cast<std::size_t>(i)];
        columns[i] = column(net, feature_index(key, perspective, change.piece, change.square));
        adds[i] = change.add;
    }
#if FORGE_NNUE_V3_AVX2
    for (int h = 0; h < hidden; h += 16) {
        __m256i v = _mm256_load_si256(reinterpret_cast<const __m256i*>(source + h));
        for (int i = 0; i < dirty.count; ++i) {
            const __m256i c = _mm256_load_si256(reinterpret_cast<const __m256i*>(columns[i] + h));
            v = adds[i] ? _mm256_add_epi16(v, c) : _mm256_sub_epi16(v, c);
        }
        _mm256_store_si256(reinterpret_cast<__m256i*>(destination + h), v);
    }
#else
    for (int h = 0; h < hidden; ++h) {
        int v = source[h];
        for (int i = 0; i < dirty.count; ++i) v += adds[i] ? columns[i][h] : -columns[i][h];
        destination[h] = static_cast<std::int16_t>(v);
    }
#endif
}

void refresh_from_pieces(const Net& net, RefreshCache& cache, const Pieces& pieces, Color perspective, int king_square,
                         std::int16_t* destination) {
    const KingKey key = king_key(net, perspective, king_square);
    RefreshCache::Entry& entry = cache.entries[cache_index(net, perspective, key)];
    const int hidden = net.hidden;
    ++cache.refreshes;
    for (int piece = WP; piece <= BK; ++piece) {
        const auto pi = static_cast<std::size_t>(piece);
        Bitboard removed = entry.pieces[pi] & ~pieces[pi];
        Bitboard added = pieces[pi] & ~entry.pieces[pi];
        while (removed != 0) {
            const int square = pop_lsb(removed);
            sub_column(entry.values.data(), column(net, feature_index(key, perspective, static_cast<Piece>(piece), square)), hidden);
            ++cache.columns;
        }
        while (added != 0) {
            const int square = pop_lsb(added);
            add_column(entry.values.data(), column(net, feature_index(key, perspective, static_cast<Piece>(piece), square)), hidden);
            ++cache.columns;
        }
        entry.pieces[pi] = pieces[pi];
    }
    std::copy_n(entry.values.data(), hidden, destination);
}

void refresh_cached(const Net& net, RefreshCache& cache, const Board& board, Accumulator& accumulator) {
    const Pieces pieces = pieces_of(board);
    for (const Color p : {White, Black}) {
        const auto pi = static_cast<std::size_t>(p);
        const int king_square = board.king_square(p);
        accumulator.king_sq[pi] = static_cast<std::uint8_t>(king_square);
        accumulator.keys[pi] = king_key(net, p, king_square);
        refresh_from_pieces(net, cache, pieces, p, king_square, accumulator.values[pi].data());
    }
    accumulator.valid = true;
}

} // namespace forge::nnue::v3
