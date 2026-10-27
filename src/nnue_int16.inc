// NnueInt16: integer inference for Forge's own quantized network (OFF by default).
// Ported from Sol's NnueInt16 (b425207a: 764db5f3, 07410241) onto the AL1 lock;
// see opus_round1/sol_SA2/IDEA_SOURCE.md. Included within forge::nnue.
//
// Number format (the include file's own): w1, b1, w2, b2 are int16 multiples of
// 1/4096. Accumulators are int32 (not int16): A = b1 + sum w1 over the active
// features. Activation a = clamp(A, 0, 4096) (= the float clamp to [0, 1]);
// square q = (a*a + 1024) / 2048 in [0, 8192] (scale 8192); output
// T = sum q*w2 (scale 2^25, summed in int64), logit = T / 2^25 + b2 / 4096,
// centipawns = logit * 400 / 2.25, clamped and truncated toward zero.
namespace int16_detail {

constexpr std::int32_t ActivationScale = 4096;
constexpr std::int64_t SquaredScale = 8192;

struct alignas(64) IntegerWeights {
    alignas(64) std::array<std::int16_t, static_cast<std::size_t>(InputCount) * HiddenSize> w1{};
    alignas(64) std::array<std::int16_t, HiddenSize> b1{};
    alignas(64) std::array<std::int16_t, 2 * HiddenSize> w2{};
    alignas(64) std::array<std::int16_t, 2 * HiddenSize> packed_w2{};
    double bias = 0.0;
    bool representable = false;

    IntegerWeights() {
#if FORGE_HAS_NNUE
        if (WeightScale != 4096.0F || OutputScale != 4096.0F || HiddenSize % 16 != 0) return;
        std::int64_t largest_column = 0;
        std::int64_t largest_lane = 0;
        for (int h = 0; h < HiddenSize; ++h) {
            std::int64_t lane = std::abs(static_cast<std::int64_t>(NnueB1[h]));
            for (int f = 0; f < InputCount; ++f) {
                const std::int64_t magnitude = std::abs(static_cast<std::int64_t>(NnueW1[static_cast<std::size_t>(f) * HiddenSize + h]));
                lane += magnitude;
                largest_column = std::max(largest_column, magnitude);
            }
            largest_lane = std::max(largest_lane, lane);
        }
        // Require exact float-grid accumulator equivalence (every value and every
        // intermediate of a four-change dirty update below 2^24 units), which
        // also keeps the int32 accumulators at least 128x below overflow. Any
        // int16 network passes the int32 part: 773 * 32767 < 2^31.
        const std::int64_t intermediate = largest_lane + 4 * largest_column;
        if (intermediate >= (std::int64_t{1} << 24) ||
            intermediate > std::numeric_limits<std::int32_t>::max()) return;
        // Each 16-unit group contributes four products per int32 lane, at most
        // 4 * 8192 * 32768 = 2^30 for any int16 w2; the total is summed in int64
        // and must stay exact when converted to double.
        const std::int64_t total_bound = static_cast<std::int64_t>(2) * HiddenSize * SquaredScale * 32768;
        if (total_bound > (std::int64_t{1} << 53)) return;
        std::copy(std::begin(NnueW1), std::end(NnueW1), w1.begin());
        std::copy(std::begin(NnueB1), std::end(NnueB1), b1.begin());
        std::copy(std::begin(NnueW2), std::end(NnueW2), w2.begin());
        // AVX2 packus_epi32 interleaves its 128-bit halves in this order.
        constexpr std::array<int, 16> PackedOrder{0, 1, 2, 3, 8, 9, 10, 11, 4, 5, 6, 7, 12, 13, 14, 15};
        for (int side = 0; side < 2; ++side)
            for (int group = 0; group < HiddenSize; group += 16)
                for (int i = 0; i < 16; ++i)
                    packed_w2[static_cast<std::size_t>(side * HiddenSize + group + i)] =
                        w2[static_cast<std::size_t>(side * HiddenSize + group + PackedOrder[static_cast<std::size_t>(i)])];
        bias = static_cast<double>(NnueB2) / 4096.0;
        representable = true;
#endif
    }
};

const IntegerWeights& weights() {
    static const IntegerWeights instance;
    return instance;
}

// Written by set_int16() (the UCI thread, between searches), read by refresh()
// in every search thread: atomic, so a mid-search setoption is not a data race.
std::atomic<bool> selected{false};

const std::int16_t* column(const IntegerWeights& w, Color perspective, const PieceChange& change) {
    return w.w1.data() + static_cast<std::size_t>(feature_index(perspective, change.piece, change.square)) * HiddenSize;
}

void refresh_integer(const Board& board, Accumulator& accumulator) {
    const IntegerWeights& w = weights();
    for (const Color perspective : {White, Black}) {
        auto& lanes = accumulator.integer_values[static_cast<std::size_t>(perspective)];
        for (int h = 0; h < HiddenSize; ++h) lanes[static_cast<std::size_t>(h)] = w.b1[static_cast<std::size_t>(h)];
        Bitboard occupied = board.occupied();
        while (occupied != 0) {
            const int square = pop_lsb(occupied);
            const std::size_t offset = static_cast<std::size_t>(feature_index(perspective, board.piece_at(square), square)) * HiddenSize;
            for (int h = 0; h < HiddenSize; ++h) lanes[static_cast<std::size_t>(h)] += w.w1[offset + static_cast<std::size_t>(h)];
        }
    }
    accumulator.integer = true;
    accumulator.valid = true;
}

void update_integer(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty) {
    const IntegerWeights& w = weights();
    for (const Color perspective : {White, Black}) {
        const auto& source = parent.integer_values[static_cast<std::size_t>(perspective)];
        auto& destination = child.integer_values[static_cast<std::size_t>(perspective)];
        std::array<const std::int16_t*, 4> columns{};
        for (int i = 0; i < dirty.count; ++i) columns[static_cast<std::size_t>(i)] = column(w, perspective, dirty.changes[static_cast<std::size_t>(i)]);
#if defined(__AVX2__)
        for (int h = 0; h < HiddenSize; h += 8) {
            __m256i value = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(source.data() + h));
            for (int i = 0; i < dirty.count; ++i) {
                const std::size_t k = static_cast<std::size_t>(i);
                const __m256i change = _mm256_cvtepi16_epi32(_mm_loadu_si128(reinterpret_cast<const __m128i*>(columns[k] + h)));
                value = dirty.changes[k].add ? _mm256_add_epi32(value, change) : _mm256_sub_epi32(value, change);
            }
            _mm256_storeu_si256(reinterpret_cast<__m256i*>(destination.data() + h), value);
        }
#else
        for (int h = 0; h < HiddenSize; ++h) {
            std::int32_t value = source[static_cast<std::size_t>(h)];
            for (int i = 0; i < dirty.count; ++i) {
                const std::size_t k = static_cast<std::size_t>(i);
                value += dirty.changes[k].add ? columns[k][h] : -static_cast<std::int32_t>(columns[k][h]);
            }
            destination[static_cast<std::size_t>(h)] = value;
        }
#endif
    }
    child.integer = true;
    child.valid = true;
}

#if !defined(__AVX2__)
// Rounded square of the clamped activation, scale 8192 (4096^2 / 2048).
inline std::int64_t squared_activation(std::int32_t value) {
    const std::int64_t a = std::clamp(value, std::int32_t{0}, ActivationScale);
    return (a * a + 1024) / 2048;
}
#endif

int evaluate_integer(const Board& board, const Accumulator& accumulator) {
    const IntegerWeights& w = weights();
    const auto& ours = accumulator.integer_values[static_cast<std::size_t>(board.side_to_move())];
    const auto& theirs = accumulator.integer_values[static_cast<std::size_t>(opposite(board.side_to_move()))];
    std::int64_t total = 0;
#if defined(__AVX2__)
    const __m256i top = _mm256_set1_epi16(ActivationScale);
    __m256i lower = _mm256_setzero_si256();
    __m256i upper = _mm256_setzero_si256();
    for (int h = 0; h < HiddenSize; h += 16) {
        // packus saturates to [0, 65535], min 4096 completes the clamp to
        // [0, 4096]; mulhrs((4a), (4a)) = (16a^2 + 2^14) >> 15 = (a^2 + 1024) >> 11.
        const auto activate = [&](const std::int32_t* input) {
            const __m256i first = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(input));
            const __m256i second = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(input + 8));
            const __m256i bounded = _mm256_min_epu16(_mm256_packus_epi32(first, second), top);
            const __m256i scaled = _mm256_slli_epi16(bounded, 2);
            return _mm256_mulhrs_epi16(scaled, scaled);
        };
        const __m256i a = _mm256_madd_epi16(activate(ours.data() + h), _mm256_loadu_si256(reinterpret_cast<const __m256i*>(w.packed_w2.data() + h)));
        const __m256i b = _mm256_madd_epi16(activate(theirs.data() + h), _mm256_loadu_si256(reinterpret_cast<const __m256i*>(w.packed_w2.data() + HiddenSize + h)));
        // At most four products of 8192 and an int16 per lane: <= 2^30.
        // Widen this group before any cross-group or horizontal addition.
        const __m256i group = _mm256_add_epi32(a, b);
        lower = _mm256_add_epi64(lower, _mm256_cvtepi32_epi64(_mm256_castsi256_si128(group)));
        upper = _mm256_add_epi64(upper, _mm256_cvtepi32_epi64(_mm256_extracti128_si256(group, 1)));
    }
    alignas(32) std::int64_t lanes[4];
    _mm256_store_si256(reinterpret_cast<__m256i*>(lanes), _mm256_add_epi64(lower, upper));
    for (const std::int64_t lane : lanes) total += lane;
#else
    for (int h = 0; h < HiddenSize; ++h) {
        total += squared_activation(ours[static_cast<std::size_t>(h)]) * w.w2[static_cast<std::size_t>(h)];
        total += squared_activation(theirs[static_cast<std::size_t>(h)]) * w.w2[static_cast<std::size_t>(HiddenSize + h)];
    }
#endif
    const double output = static_cast<double>(total) / 33554432.0 + w.bias;
    const double cp = output * 400.0 / static_cast<double>(SigmoidK);
    return static_cast<int>(std::clamp(cp, -30000.0, 30000.0));
}

} // namespace int16_detail

bool int16_available() { return int16_detail::weights().representable; }
bool int16_active() { return int16_detail::selected.load(std::memory_order_relaxed); }
bool set_int16(bool requested) {
    const bool active = requested && int16_available();
    int16_detail::selected.store(active, std::memory_order_relaxed);
    return active;
}
