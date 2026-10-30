#include "forge/nnue_halfka.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <fstream>
#include <memory>
#include <sstream>

#if defined(__AVX2__)
#include <immintrin.h>
#endif

namespace forge::halfka {
namespace {

struct Stack {
    std::vector<std::int32_t> b1, b2;
    std::int32_t b3 = 0;
    std::vector<std::int8_t> w1, w2, w3;  // row-major [output][padded input]
};

struct Net {
    int l1 = 0, l2 = 0, l3 = 0;
    int in1 = 0, in2 = 0, in3 = 0;  // input widths padded to 32 as stored in the file
    std::uint32_t hash = 0;
    std::string path, text;
    std::vector<std::int16_t> ft_bias;
    std::vector<std::int8_t> ft_weight;  // NumFeatures rows of l1 values
    std::vector<Stack> stacks;
};

// Read-only while a search runs: only `setoption` (which stops the search first) replaces it.
std::unique_ptr<Net> g_net;
bool g_force_scalar = false;

// Oriented own-king square (files e-h after the horizontal mirror) -> king bucket 0..31.
constexpr std::array<int, 64> KingBucket = {
    -1, -1, -1, -1, 31, 30, 29, 28,
    -1, -1, -1, -1, 27, 26, 25, 24,
    -1, -1, -1, -1, 23, 22, 21, 20,
    -1, -1, -1, -1, 19, 18, 17, 16,
    -1, -1, -1, -1, 15, 14, 13, 12,
    -1, -1, -1, -1, 11, 10, 9, 8,
    -1, -1, -1, -1, 7, 6, 5, 4,
    -1, -1, -1, -1, 3, 2, 1, 0,
};

// Black sees the board flipped vertically; a king on files a-d mirrors the board horizontally.
constexpr int orient(Color perspective, int square, int king_square) {
    return square ^ (perspective == Black ? 56 : 0) ^ ((king_square & 7) < 4 ? 7 : 0);
}

int pad32(int n) { return (n + 31) / 32 * 32; }

std::uint32_t fc_hash(int l1, int l2, int l3) {
    std::uint32_t prev = 0xEC42E90DU ^ static_cast<std::uint32_t>(l1 * 2);
    for (const int out : {l2, l3, 1}) {
        std::uint32_t h = 0xCC03DAE4U + static_cast<std::uint32_t>(out);
        h ^= prev >> 1;
        h ^= prev << 31;
        if (out != 1) h += 0x538D24C7U;
        prev = h;
    }
    return prev;
}

std::uint64_t file_size_for(std::uint64_t header, int l1, int l2, int l3) {
    const std::uint64_t ft = 4 + 2ULL * l1 + static_cast<std::uint64_t>(NumFeatures) * l1;
    const std::uint64_t stack = 4 + (4ULL * l2 + static_cast<std::uint64_t>(l2) * pad32(l1)) +
                                (4ULL * l3 + static_cast<std::uint64_t>(l3) * pad32(2 * l2)) + (4 + pad32(2 * l2 + 2 * l3));
    return header + ft + NumStacks * stack;
}

class Reader {
public:
    explicit Reader(const std::vector<std::uint8_t>& data) : d_(data) {}
    bool u32(std::uint32_t& v) { return raw(&v, 4); }
    template <typename T> bool array(std::vector<T>& out, std::size_t n) {
        out.resize(n);
        return raw(out.data(), n * sizeof(T));
    }
    bool raw(void* dst, std::size_t n) {
        if (n > d_.size() - pos_) return false;
        std::memcpy(dst, d_.data() + pos_, n);
        pos_ += n;
        return true;
    }
    bool skip(std::size_t n) {
        if (n > d_.size() - pos_) return false;
        pos_ += n;
        return true;
    }
    [[nodiscard]] std::size_t pos() const { return pos_; }

private:
    const std::vector<std::uint8_t>& d_;
    std::size_t pos_ = 0;
};

bool fail(std::string& error, const std::string& why) {
    error = why;
    return false;
}

// ---------------------------------------------------------------- kernels
void row_add(std::int16_t* acc, const std::int8_t* w, int n) {
#if defined(__AVX2__)
    if (!g_force_scalar) {
        for (int j = 0; j < n; j += 16) {
            const __m256i a = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(acc + j));
            const __m256i b = _mm256_cvtepi8_epi16(_mm_loadu_si128(reinterpret_cast<const __m128i*>(w + j)));
            _mm256_storeu_si256(reinterpret_cast<__m256i*>(acc + j), _mm256_add_epi16(a, b));
        }
        return;
    }
#endif
    for (int j = 0; j < n; ++j) acc[j] = static_cast<std::int16_t>(acc[j] + w[j]);
}

void row_sub(std::int16_t* acc, const std::int8_t* w, int n) {
#if defined(__AVX2__)
    if (!g_force_scalar) {
        for (int j = 0; j < n; j += 16) {
            const __m256i a = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(acc + j));
            const __m256i b = _mm256_cvtepi8_epi16(_mm_loadu_si128(reinterpret_cast<const __m128i*>(w + j)));
            _mm256_storeu_si256(reinterpret_cast<__m256i*>(acc + j), _mm256_sub_epi16(a, b));
        }
        return;
    }
#endif
    for (int j = 0; j < n; ++j) acc[j] = static_cast<std::int16_t>(acc[j] - w[j]);
}

// out[j] = clamp(a[j], 0, 255) * clamp(a[j + half], 0, 255) >> 9 for j < half (values 0..127)
void pairwise(const std::int16_t* a, std::uint8_t* out, int half) {
#if defined(__AVX2__)
    if (!g_force_scalar) {
        const __m256i zero = _mm256_setzero_si256(), top = _mm256_set1_epi16(255);
        for (int j = 0; j < half; j += 32) {
            auto clampv = [&](const std::int16_t* p) {
                return _mm256_min_epi16(_mm256_max_epi16(_mm256_loadu_si256(reinterpret_cast<const __m256i*>(p)), zero), top);
            };
            const __m256i x = _mm256_srli_epi16(_mm256_mullo_epi16(clampv(a + j), clampv(a + half + j)), 9);
            const __m256i y = _mm256_srli_epi16(_mm256_mullo_epi16(clampv(a + j + 16), clampv(a + half + j + 16)), 9);
            _mm256_storeu_si256(reinterpret_cast<__m256i*>(out + j), _mm256_permute4x64_epi64(_mm256_packus_epi16(x, y), 0xD8));
        }
        return;
    }
#endif
    for (int j = 0; j < half; ++j) {
        const int x = std::clamp<int>(a[j], 0, 255), y = std::clamp<int>(a[j + half], 0, 255);
        out[j] = static_cast<std::uint8_t>((x * y) >> 9);
    }
}

// sum_i w[i] * x[i] over n inputs (n a multiple of 32; x values 0..127, w int8)
std::int32_t dot(const std::int8_t* w, const std::uint8_t* x, int n) {
#if defined(__AVX2__)
    if (!g_force_scalar) {
        __m256i acc = _mm256_setzero_si256();
        const __m256i ones = _mm256_set1_epi16(1);
        for (int i = 0; i < n; i += 32) {
            const __m256i xv = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(x + i));
            const __m256i wv = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(w + i));
            // x <= 127 and |w| <= 128: each pair sum stays inside int16, so maddubs does not saturate
            acc = _mm256_add_epi32(acc, _mm256_madd_epi16(_mm256_maddubs_epi16(xv, wv), ones));
        }
        const __m128i s = _mm_add_epi32(_mm256_castsi256_si128(acc), _mm256_extracti128_si256(acc, 1));
        const __m128i s2 = _mm_add_epi32(s, _mm_shuffle_epi32(s, 0x4E));
        return _mm_cvtsi128_si32(_mm_add_epi32(s2, _mm_shuffle_epi32(s2, 0xB1)));
    }
#endif
    std::int32_t sum = 0;
    for (int i = 0; i < n; ++i) sum += static_cast<std::int32_t>(w[i]) * x[i];
    return sum;
}

std::uint8_t lin(std::int32_t s, int shift) { return static_cast<std::uint8_t>(std::clamp(s >> shift, 0, 127)); }
// floor(s^2 / 2^shift + 1e-5) clamped to 127: the trainer's fake quantization of the squared activation (the 1e-5
// moves values within 2^shift * 1e-5 below an integer up, hence + add)
std::uint8_t sqr(std::int32_t s, int shift, std::int64_t add) {
    const std::int64_t q = (static_cast<std::int64_t>(s) * s + add) >> shift;
    return static_cast<std::uint8_t>(std::min<std::int64_t>(q, 127));
}

} // namespace

bool load(const std::string& path, std::string& error) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return fail(error, "cannot open " + path);
    std::vector<std::uint8_t> data((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    Reader r(data);
    std::uint32_t version = 0, net_hash = 0, desc_len = 0, ft_hash = 0;
    if (!r.u32(version) || !r.u32(net_hash) || !r.u32(desc_len)) return fail(error, "file too short for a .nnue header");
    if (version != FileVersion) {
        std::ostringstream s;
        s << "not a supported .nnue version (0x" << std::hex << version << ", expected 0x" << FileVersion << ")";
        return fail(error, s.str());
    }
    if (desc_len > (1U << 20) || !r.skip(desc_len)) return fail(error, "bad description length");
    const std::uint64_t header = r.pos();
    if (!r.u32(ft_hash)) return fail(error, "file ends before the feature transformer");
    const std::uint32_t l1x2 = ft_hash ^ FeatureHash;
    const int l1 = static_cast<int>(l1x2 / 2);
    if (l1x2 % 2 != 0 || l1 < 64 || l1 > MaxL1 || l1 % 64 != 0) {
        std::ostringstream s;
        s << "feature transformer hash 0x" << std::hex << ft_hash << " is not K32H3^ with L1 a multiple of 64 up to "
          << std::dec << MaxL1 << " (other feature sets such as Full_Threats are not supported)";
        return fail(error, s.str());
    }
    int l2 = 0, l3 = 0, matches = 0;
    for (int a = 2; a <= MaxL2; a += 2)
        for (int b = 2; b <= MaxL3; b += 2)
            if ((fc_hash(l1, a, b) ^ FeatureHash ^ l1x2) == net_hash && file_size_for(header, l1, a, b) == data.size()) {
                l2 = a;
                l3 = b;
                ++matches;
            }
    if (matches != 1) {
        std::ostringstream s;
        s << "no unique layer shape for L1 " << l1 << " matches the network hash 0x" << std::hex << net_hash << std::dec
          << " and the file size " << data.size() << " (truncated or a different architecture)";
        return fail(error, s.str());
    }
    auto net = std::make_unique<Net>();
    net->l1 = l1;
    net->l2 = l2;
    net->l3 = l3;
    net->in1 = pad32(l1);
    net->in2 = pad32(2 * l2);
    net->in3 = pad32(2 * l2 + 2 * l3);
    net->hash = net_hash;
    net->path = path;
    if (!r.array(net->ft_bias, static_cast<std::size_t>(l1)) ||
        !r.array(net->ft_weight, static_cast<std::size_t>(NumFeatures) * l1))
        return fail(error, "file ends inside the feature transformer");
    const std::uint32_t fc = fc_hash(l1, l2, l3);
    net->stacks.resize(NumStacks);
    for (Stack& st : net->stacks) {
        std::uint32_t h = 0;
        if (!r.u32(h) || h != fc) return fail(error, "layer stack hash mismatch");
        std::vector<std::int32_t> b3;
        if (!r.array(st.b1, static_cast<std::size_t>(l2)) || !r.array(st.w1, static_cast<std::size_t>(l2) * net->in1) ||
            !r.array(st.b2, static_cast<std::size_t>(l3)) || !r.array(st.w2, static_cast<std::size_t>(l3) * net->in2) ||
            !r.array(b3, 1) || !r.array(st.w3, static_cast<std::size_t>(net->in3)))
            return fail(error, "file ends inside a layer stack");
        st.b3 = b3[0];
    }
    if (r.pos() != data.size()) return fail(error, "trailing bytes after the last layer stack");
    // int16 accumulators must not overflow: bias + 32 active features x the largest weight of each output
    std::vector<int> wmax(static_cast<std::size_t>(l1), 0);
    for (std::size_t i = 0; i < net->ft_weight.size(); ++i) {
        int& m = wmax[i % static_cast<std::size_t>(l1)];
        m = std::max(m, std::abs(static_cast<int>(net->ft_weight[i])));
    }
    for (int j = 0; j < l1; ++j)
        if (std::abs(static_cast<int>(net->ft_bias[static_cast<std::size_t>(j)])) + 32 * wmax[static_cast<std::size_t>(j)] > 32767)
            return fail(error, "feature transformer output " + std::to_string(j) + " could overflow an int16 accumulator");
    std::ostringstream s;
    s << path << ": K32H3^ " << l1 << "x" << l2 << "x" << l3 << ", 32 layer stacks, hash 0x" << std::hex << net_hash;
    net->text = s.str();
    g_net = std::move(net);
    return true;
}

void unload() { g_net.reset(); }
bool active() { return g_net != nullptr; }
int l1() { return g_net ? g_net->l1 : 0; }
std::string description() { return g_net ? g_net->text : std::string("none"); }
void set_force_scalar(bool on) { g_force_scalar = on; }
bool simd_compiled() {
#if defined(__AVX2__)
    return true;
#else
    return false;
#endif
}

int feature_bucket(const Board& board, Color perspective) {
    const Color them = perspective == White ? Black : White;
    int state = 0;
    if (board.pieces(them, Queen) != 0) state = 2;
    else if ((board.pieces(Rook) | board.pieces(Queen)) != 0) state = 1;
    const int ksq = board.king_square(perspective);
    return state * NumKingBuckets + KingBucket[static_cast<std::size_t>(orient(perspective, ksq, ksq))];
}

int feature_index(Color perspective, Piece piece, int square, int king_square, int bucket) {
    const int plane = std::min((piece_type(piece) - 1) * 2 + (color_of(piece) != perspective ? 1 : 0), 10);
    return orient(perspective, square, king_square) + plane * 64 + bucket * PlanesPerBucket;
}

int stack_index(const Board& board) {
    const Color us = board.side_to_move(), them = us == White ? Black : White;
    return (popcount(board.occupied()) - 1) / 4 * 4 + (board.pieces(us, Queen) != 0 ? 2 : 0) +
           (board.pieces(them, Queen) != 0 ? 1 : 0);
}

void refresh(const Board& board, Color perspective, std::int16_t* out) {
    const Net& n = *g_net;
    std::copy(n.ft_bias.begin(), n.ft_bias.end(), out);
    const int ksq = board.king_square(perspective), bucket = feature_bucket(board, perspective);
    for (Bitboard bb = board.occupied(); bb != 0; bb &= bb - 1) {
        const int sq = lsb(bb);
        const int f = feature_index(perspective, board.piece_at(sq), sq, ksq, bucket);
        row_add(out, n.ft_weight.data() + static_cast<std::size_t>(f) * n.l1, n.l1);
    }
}

void apply(const std::int16_t* parent, std::int16_t* child, Color perspective, int king_square, int bucket,
           const nnue::DirtyPieces& dirty) {
    const Net& n = *g_net;
    if (child != parent) std::memcpy(child, parent, sizeof(std::int16_t) * static_cast<std::size_t>(n.l1));
    for (int c = 0; c < dirty.count; ++c) {
        const nnue::PieceChange& pc = dirty.changes[static_cast<std::size_t>(c)];
        const std::int8_t* w = n.ft_weight.data() +
                               static_cast<std::size_t>(feature_index(perspective, pc.piece, pc.square, king_square, bucket)) * n.l1;
        if (pc.add) row_add(child, w, n.l1);
        else row_sub(child, w, n.l1);
    }
}

std::int64_t evaluate_raw(const Board& board, const std::int16_t* white, const std::int16_t* black) {
    const Net& n = *g_net;
    const Stack& st = n.stacks[static_cast<std::size_t>(stack_index(board))];
    const bool white_to_move = board.side_to_move() == White;
    alignas(64) std::array<std::uint8_t, MaxL1> ft{};
    const int half = n.l1 / 2;
    pairwise(white_to_move ? white : black, ft.data(), half);
    pairwise(white_to_move ? black : white, ft.data() + half, half);
    std::array<std::int32_t, MaxL2> s1{};
    alignas(64) std::array<std::uint8_t, 2 * MaxL2 + 2 * MaxL3 + 32> x{};  // [sq1, lin1, sq2, lin2], zero padding
    for (int k = 0; k < n.l2; ++k) {
        s1[static_cast<std::size_t>(k)] = st.b1[static_cast<std::size_t>(k)] +
                                          dot(st.w1.data() + static_cast<std::size_t>(k) * n.in1, ft.data(), n.in1);
        x[static_cast<std::size_t>(k)] = sqr(s1[static_cast<std::size_t>(k)], 21, 20);
        x[static_cast<std::size_t>(n.l2 + k)] = lin(s1[static_cast<std::size_t>(k)], 7);
    }
    alignas(64) std::array<std::uint8_t, 2 * MaxL3 + 32> x3{};
    for (int k = 0; k < n.l3; ++k) {
        const std::int32_t s2 = st.b2[static_cast<std::size_t>(k)] + dot(st.w2.data() + static_cast<std::size_t>(k) * n.in2, x.data(), n.in2);
        x3[static_cast<std::size_t>(k)] = sqr(s2, 19, 5);
        x3[static_cast<std::size_t>(n.l3 + k)] = lin(s2, 6);
    }
    // the output layer reads [sq1, lin1, sq2, lin2]: copy the second block right behind the first
    std::copy(x3.begin(), x3.begin() + 2 * n.l3, x.begin() + 2 * n.l2);
    std::fill(x.begin() + 2 * n.l2 + 2 * n.l3, x.begin() + n.in3, std::uint8_t{0});
    const std::int64_t s3 = st.b3 + dot(st.w3.data(), x.data(), n.in3);
    const std::int64_t total = s3 + s1[static_cast<std::size_t>(n.l2 - 2)] - s1[static_cast<std::size_t>(n.l2 - 1)];
    return total * 2 * 9600 / 32768;  // the trainer's output value (truncated toward zero)
}

int evaluate(const Board& board, const std::int16_t* white, const std::int16_t* black) {
    return static_cast<int>(evaluate_raw(board, white, black) / 16);
}

std::int64_t evaluate_fresh_raw(const Board& board) {
    std::vector<std::int16_t> w(static_cast<std::size_t>(l1())), b(static_cast<std::size_t>(l1()));
    refresh(board, White, w.data());
    refresh(board, Black, b.data());
    return evaluate_raw(board, w.data(), b.data());
}

void AccumulatorStack::ensure(int entries) {
    const int want = forge::halfka::l1();  // the net's L1 (the member l1() is this stack's current width)
    if (entries > 1024) entries = 1024;
    if (want != l1_ || entries != entries_) {
        l1_ = want;
        entries_ = entries;
        stride_ = static_cast<std::size_t>(want);
        data_.assign(static_cast<std::size_t>(entries) * 2 * stride_, 0);
    }
    invalidate_all();
}

void AccumulatorStack::invalidate_all() {
    for (auto& v : valid)
        for (bool& b : v) b = false;
}

} // namespace forge::halfka
