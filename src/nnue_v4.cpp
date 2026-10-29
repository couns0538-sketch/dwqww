// NNUE v4 (R5C): loader, scalar reference and AVX2 kernel. Format and arithmetic: opus_r5/r5c/FNN4_FORMAT.md.
#include "forge/nnue_v4.hpp"

#include "forge/nnue.hpp"

#include <algorithm>
#include <bit>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <limits>
#include <memory>
#include <sstream>

#if defined(__AVX2__)
#include <immintrin.h>
#endif

static_assert(std::endian::native == std::endian::little, "the FNN4 reader assumes a little-endian host");

namespace forge::nnue_v4 {

bool requested = false;
bool active = false;

namespace {

std::unique_ptr<Net> g_net;

constexpr char Magic[8] = {'F', 'O', 'R', 'G', 'E', 'N', 'N', '4'};
constexpr int MaxHidden = 1024;
constexpr int MaxL2 = 64;
constexpr std::int64_t MaxBiasOut = std::int64_t{1} << 40;

std::uint32_t u32_at(const unsigned char* p) {
    std::uint32_t v;
    std::memcpy(&v, p, sizeof v);
    return v;
}

std::int32_t i32_at(const unsigned char* p) {
    std::int32_t v;
    std::memcpy(&v, p, sizeof v);
    return v;
}

struct Header {
    int hidden = 0, king_buckets = 0, output_buckets = 0, l2 = 0, eval_scale = 0;
    std::uint32_t flags = 0;
};

// Every header field; `error` names the first bad one.
bool check_header(const unsigned char* h, Header& out, std::string& error) {
    if (std::memcmp(h, Magic, sizeof Magic) != 0) return error = "not an FNN4 file (magic)", false;
    if (u32_at(h + 8) != 1) return error = "unsupported version " + std::to_string(u32_at(h + 8)), false;
    if (u32_at(h + 12) != HeaderBytes) return error = "header_bytes " + std::to_string(u32_at(h + 12)), false;
    if (u32_at(h + 16) != Inputs) return error = "inputs " + std::to_string(u32_at(h + 16)), false;
    const std::uint32_t hidden = u32_at(h + 20), kb = u32_at(h + 24), ob = u32_at(h + 28), l2 = u32_at(h + 32);
    if (hidden < 64 || hidden > MaxHidden || hidden % 64 != 0) return error = "hidden " + std::to_string(hidden), false;
    if (kb < 1 || kb > 32) return error = "king_buckets " + std::to_string(kb), false;
    if (ob < 1 || ob > 16) return error = "output_buckets " + std::to_string(ob), false;
    if (l2 < 1 || l2 > MaxL2) return error = "l2 " + std::to_string(l2), false;
    const std::uint32_t flags = u32_at(h + 36);
    if ((flags & ~(FlagResidual | FlagMirror)) != 0) return error = "unknown flags " + std::to_string(flags), false;
    const std::int32_t scale = i32_at(h + 40);
    if (scale < 1 || scale > 10000) return error = "eval_scale " + std::to_string(scale), false;
    if (u32_at(h + 44) != QA || u32_at(h + 48) != SShift || u32_at(h + 52) != QW || u32_at(h + 56) != QO)
        return error = "quantisation constants differ from qa 255, s_shift 6, qw 1024, qo 256", false;
    for (int i = 0; i < 64; ++i)
        if (h[60 + i] >= kb) return error = "king_map[" + std::to_string(i) + "] out of range", false;
    for (int i = 0; i < 33; ++i)
        if (h[124 + i] >= ob) return error = "output_map[" + std::to_string(i) + "] out of range", false;
    for (int i = 157; i < HeaderBytes; ++i)
        if (h[i] != 0) return error = "reserved header byte " + std::to_string(i) + " is not 0", false;
    out = {static_cast<int>(hidden), static_cast<int>(kb), static_cast<int>(ob), static_cast<int>(l2), scale, flags};
    return true;
}

template <typename T>
const unsigned char* read_array(const unsigned char* p, std::vector<T>& v, std::size_t count) {
    v.resize(count);
    std::memcpy(v.data(), p, count * sizeof(T));
    return p + count * sizeof(T);
}

} // namespace

std::uint64_t fnv1a64(const unsigned char* data, std::size_t size) {
    std::uint64_t h = 0xcbf29ce484222325ULL;
    for (std::size_t i = 0; i < size; ++i) {
        h ^= data[i];
        h *= 0x100000001b3ULL;
    }
    return h;
}

std::uint64_t file_size_for(int hidden, int king_buckets, int output_buckets, int l2) {
    if (hidden < 64 || hidden > MaxHidden || hidden % 64 != 0 || king_buckets < 1 || king_buckets > 32 || output_buckets < 1 ||
        output_buckets > 16 || l2 < 1 || l2 > MaxL2)
        return 0;
    const std::uint64_t h = static_cast<std::uint64_t>(hidden), kb = static_cast<std::uint64_t>(king_buckets),
                        ob = static_cast<std::uint64_t>(output_buckets), n = static_cast<std::uint64_t>(l2);
    return HeaderBytes + 2 * kb * Inputs * h + 2 * h + 4 * n * h + 4 * n + 2 * ob * n + 8 * ob + 8;
}

bool parse(const std::vector<unsigned char>& bytes, Net& out, std::string& error) {
    if (bytes.size() < static_cast<std::size_t>(HeaderBytes)) return error = "file shorter than the header", false;
    Header hd;
    if (!check_header(bytes.data(), hd, error)) return false;
    const std::uint64_t expected = file_size_for(hd.hidden, hd.king_buckets, hd.output_buckets, hd.l2);
    if (bytes.size() != expected)
        return error = "file size " + std::to_string(bytes.size()) + ", the header needs " + std::to_string(expected), false;
    std::uint64_t stored;
    std::memcpy(&stored, bytes.data() + bytes.size() - 8, sizeof stored);
    const std::uint64_t computed = fnv1a64(bytes.data(), bytes.size() - 8);
    if (stored != computed) return error = "checksum mismatch", false;

    Net net;
    net.hidden = hd.hidden;
    net.king_buckets = hd.king_buckets;
    net.output_buckets = hd.output_buckets;
    net.l2 = hd.l2;
    net.flags = hd.flags;
    net.eval_scale = hd.eval_scale;
    std::memcpy(net.king_map.data(), bytes.data() + 60, 64);
    std::memcpy(net.output_map.data(), bytes.data() + 124, 33);
    const std::size_t H = static_cast<std::size_t>(hd.hidden), L2 = static_cast<std::size_t>(hd.l2);
    const unsigned char* p = bytes.data() + HeaderBytes;
    p = read_array(p, net.w1, static_cast<std::size_t>(hd.king_buckets) * Inputs * H);
    p = read_array(p, net.b1, H);
    p = read_array(p, net.l2w, L2 * 2 * H);
    p = read_array(p, net.l2b, L2);
    p = read_array(p, net.l2o, static_cast<std::size_t>(hd.output_buckets) * L2);
    p = read_array(p, net.b_out, static_cast<std::size_t>(hd.output_buckets));
    net.checksum = stored;

    // Overflow bounds of FNN4_FORMAT.md: int16 accumulators for 32 pieces, int32 layer-2 sums in any order.
    int max_w1 = 0, max_b1 = 0;
    for (const std::int16_t w : net.w1) max_w1 = std::max(max_w1, std::abs(static_cast<int>(w)));
    for (const std::int16_t b : net.b1) max_b1 = std::max(max_b1, std::abs(static_cast<int>(b)));
    if (max_b1 + 32 * max_w1 > 32767)
        return error = "accumulator bound: max|b1| " + std::to_string(max_b1) + " + 32 * max|w1| " + std::to_string(max_w1) +
                       " > 32767", false;
    for (std::size_t j = 0; j < L2; ++j) {
        std::int64_t abs_sum = 0;
        for (std::size_t i = 0; i < 2 * H; ++i) abs_sum += std::abs(static_cast<int>(net.l2w[j * 2 * H + i]));
        const std::int64_t bound = std::abs(static_cast<std::int64_t>(net.l2b[j])) + std::int64_t{SMax} * abs_sum;
        if (bound > std::numeric_limits<std::int32_t>::max())
            return error = "layer-2 bound of unit " + std::to_string(j) + ": " + std::to_string(bound) + " > 2^31 - 1", false;
    }
    for (const std::int64_t b : net.b_out)
        if (b > MaxBiasOut || b < -MaxBiasOut) return error = "b_out out of range", false;
    out = std::move(net);
    return true;
}

bool load(const std::string& path, std::string& error) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return error = "cannot open " + path, false;
    unsigned char header[HeaderBytes];
    if (!in.read(reinterpret_cast<char*>(header), HeaderBytes)) return error = "file shorter than the header", false;
    Header hd;
    if (!check_header(header, hd, error)) return false;
    // The exact size is known from the header: check it before reading any weight.
    in.seekg(0, std::ios::end);
    const std::uint64_t size = static_cast<std::uint64_t>(in.tellg());
    const std::uint64_t expected = file_size_for(hd.hidden, hd.king_buckets, hd.output_buckets, hd.l2);
    if (size != expected) return error = "file size " + std::to_string(size) + ", the header needs " + std::to_string(expected), false;
    std::vector<unsigned char> bytes(static_cast<std::size_t>(size));
    in.seekg(0, std::ios::beg);
    if (!in.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(size))) return error = "read error", false;
    auto net = std::make_unique<Net>();
    if (!parse(bytes, *net, error)) return false;
    g_net = std::move(net);
    refresh_active();
    return true;
}

void unload() {
    g_net.reset();
    refresh_active();
}

const Net* loaded() { return g_net.get(); }

std::string describe(const Net& net) {
    std::ostringstream s;
    s << "H" << net.hidden << " KB" << net.king_buckets << " OB" << net.output_buckets << " L2 " << net.l2
      << (net.mirror() ? " mirrored" : "") << (net.residual() ? " residual" : " standalone") << " eval_scale "
      << net.eval_scale << " checksum " << std::hex << net.checksum << std::dec << ", kernel "
      << kernel_name(best_kernel());
    return s.str();
}

void refresh_active() { active = requested && g_net != nullptr && nnue::enabled; }

bool kernel_available(Kernel kernel) {
#if defined(__AVX2__)
    return kernel == Kernel::Scalar || kernel == Kernel::Avx2;
#else
    return kernel == Kernel::Scalar;
#endif
}

Kernel best_kernel() { return kernel_available(Kernel::Avx2) ? Kernel::Avx2 : Kernel::Scalar; }

const char* kernel_name(Kernel kernel) { return kernel == Kernel::Avx2 ? "avx2" : "scalar"; }

namespace {

struct KingKey {
    int bucket;
    int flip;
};

KingKey king_key(const Net& net, Color perspective, int king_square) {
    const int kr = perspective == White ? king_square : king_square ^ 56;
    return {net.king_map[static_cast<std::size_t>(kr)], (net.mirror() && (kr & 7) >= 4) ? 7 : 0};
}

int feature(Color perspective, KingKey key, Piece piece, int square) {
    const int rel = color_of(piece) == perspective ? 0 : 1;
    const int r = (perspective == White ? square : square ^ 56) ^ key.flip;
    return key.bucket * Inputs + (rel * 6 + piece_type(piece) - 1) * 64 + r;
}

// The active feature columns of one perspective.
int columns_of(const Net& net, const Board& board, Color perspective, const std::int16_t** columns) {
    const KingKey key = king_key(net, perspective, board.king_square(perspective));
    int count = 0;
    Bitboard occupied = board.occupied();
    while (occupied != 0) {
        const int square = pop_lsb(occupied);
        columns[count++] = net.w1.data() + static_cast<std::size_t>(feature(perspective, key, board.piece_at(square), square)) *
                                               static_cast<std::size_t>(net.hidden);
    }
    return count;
}

int finish(const Net& net, const std::int32_t* z, int ob) {
    std::int64_t out = net.b_out[static_cast<std::size_t>(ob)];
    const std::int16_t* o = net.l2o.data() + static_cast<std::size_t>(ob) * static_cast<std::size_t>(net.l2);
    for (int j = 0; j < net.l2; ++j) {
        const std::int64_t h = std::clamp<std::int64_t>(z[j], 0, One);
        out += h * o[j];
    }
    const std::int64_t cp = out * net.eval_scale / (One * QO);
    return static_cast<int>(std::clamp<std::int64_t>(cp, -30000, 30000));
}

int output_bucket(const Net& net, const Board& board) {
    return net.output_map[static_cast<std::size_t>(std::min(popcount(board.occupied()), 32))];
}

int evaluate_scalar(const Net& net, const Board& board) {
    const int H = net.hidden;
    std::int16_t acc[2][MaxHidden];
    const std::int16_t* columns[32];
    const Color us = board.side_to_move();
    for (int side = 0; side < 2; ++side) {
        const Color perspective = side == 0 ? us : opposite(us);
        const int count = columns_of(net, board, perspective, columns);
        for (int h = 0; h < H; ++h) {
            int a = net.b1[static_cast<std::size_t>(h)];
            for (int c = 0; c < count; ++c) a += columns[c][h];
            acc[side][h] = static_cast<std::int16_t>(a);
        }
    }
    std::int32_t s[2 * MaxHidden];
    for (int side = 0; side < 2; ++side)
        for (int h = 0; h < H; ++h) {
            const int c = std::clamp<int>(acc[side][h], 0, QA);
            s[side * H + h] = (c * c) >> SShift;
        }
    std::int32_t z[MaxL2];
    for (int j = 0; j < net.l2; ++j) {
        std::int32_t sum = net.l2b[static_cast<std::size_t>(j)];
        const std::int16_t* w = net.l2w.data() + static_cast<std::size_t>(j) * 2 * static_cast<std::size_t>(H);
        for (int i = 0; i < 2 * H; ++i) sum += s[i] * w[i];
        z[j] = sum;
    }
    return finish(net, z, output_bucket(net, board));
}

#if defined(__AVX2__)
int evaluate_avx2(const Net& net, const Board& board) {
    const int H = net.hidden;
    alignas(32) std::int16_t s[2 * MaxHidden];
    const std::int16_t* columns[32];
    const Color us = board.side_to_move();
    const __m256i zero = _mm256_setzero_si256();
    const __m256i qa = _mm256_set1_epi16(QA);
    for (int side = 0; side < 2; ++side) {
        const Color perspective = side == 0 ? us : opposite(us);
        const int count = columns_of(net, board, perspective, columns);
        for (int h = 0; h < H; h += 64) {
            // Four vectors of 16 lanes stay in registers while every column is added (int16, no overflow).
            __m256i a0 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(net.b1.data() + h));
            __m256i a1 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(net.b1.data() + h + 16));
            __m256i a2 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(net.b1.data() + h + 32));
            __m256i a3 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(net.b1.data() + h + 48));
            for (int c = 0; c < count; ++c) {
                const std::int16_t* col = columns[c] + h;
                a0 = _mm256_add_epi16(a0, _mm256_loadu_si256(reinterpret_cast<const __m256i*>(col)));
                a1 = _mm256_add_epi16(a1, _mm256_loadu_si256(reinterpret_cast<const __m256i*>(col + 16)));
                a2 = _mm256_add_epi16(a2, _mm256_loadu_si256(reinterpret_cast<const __m256i*>(col + 32)));
                a3 = _mm256_add_epi16(a3, _mm256_loadu_si256(reinterpret_cast<const __m256i*>(col + 48)));
            }
            // SCReLU input: clamp to [0, 255], square (exact in 16 unsigned bits), shift right by 6.
            const __m256i v[4] = {a0, a1, a2, a3};
            for (int k = 0; k < 4; ++k) {
                const __m256i c = _mm256_min_epi16(_mm256_max_epi16(v[k], zero), qa);
                _mm256_store_si256(reinterpret_cast<__m256i*>(s + side * H + h + 16 * k),
                                   _mm256_srli_epi16(_mm256_mullo_epi16(c, c), SShift));
            }
        }
    }
    std::int32_t z[MaxL2];
    for (int j = 0; j < net.l2; ++j) {
        const std::int16_t* w = net.l2w.data() + static_cast<std::size_t>(j) * 2 * static_cast<std::size_t>(H);
        __m256i sum = _mm256_setzero_si256();
        for (int i = 0; i < 2 * H; i += 16) {
            const __m256i x = _mm256_load_si256(reinterpret_cast<const __m256i*>(s + i));
            const __m256i y = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(w + i));
            sum = _mm256_add_epi32(sum, _mm256_madd_epi16(x, y));
        }
        alignas(32) std::int32_t lanes[8];
        _mm256_store_si256(reinterpret_cast<__m256i*>(lanes), sum);
        std::int32_t total = net.l2b[static_cast<std::size_t>(j)];
        for (const std::int32_t lane : lanes) total += lane;
        z[j] = total;
    }
    return finish(net, z, output_bucket(net, board));
}
#endif

} // namespace

int evaluate_with(const Net& net, const Board& board, Kernel kernel) {
#if defined(__AVX2__)
    if (kernel == Kernel::Avx2) return evaluate_avx2(net, board);
#endif
    (void)kernel;
    return evaluate_scalar(net, board);
}

int evaluate(const Net& net, const Board& board) { return evaluate_with(net, board, best_kernel()); }

} // namespace forge::nnue_v4
