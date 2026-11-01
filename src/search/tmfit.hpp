#pragma once
// Original Forge time-model inference. UNPROVEN: coefficients are fitted offline.
// No allocation, floating-point sigmoid, search-state mutation, or hard-cap extension.
#include <algorithm>
#include <array>
#include <cstdint>

namespace forge::tmfit {
using Features = std::array<int, 7>;
struct Model {
    std::array<int, 7> beta{}; // Q12, order: bias/depth/change/effort/score/delta/elapsed
    int a = 1000, b = 0, lo = 500, hi = 1500; // multiplier permille
};

// Saturating ratio in Q10 (cap must be a positive multiple of 1024), including
// UINT64_MAX inputs without multiplication overflow.
inline int ratio_q10(std::uint64_t numerator, std::uint64_t denominator, int cap) {
    if (!denominator) return 0;
    const auto whole = numerator / denominator;
    if (whole >= static_cast<std::uint64_t>(cap / 1024)) return cap;
    auto remainder = numerator % denominator;
    int fraction = 0;
    for (int bit = 0; bit < 10; ++bit) {
        fraction *= 2;
        if (remainder >= denominator - remainder) {
            remainder -= denominator - remainder;
            ++fraction;
        } else {
            remainder *= 2;
        }
    }
    return std::min(cap, static_cast<int>(whole) * 1024 + fraction);
}

inline Features features(int depth, bool changed, std::uint64_t best_nodes, std::uint64_t nodes,
                         int score, int delta, std::int64_t elapsed, std::int64_t soft) {
    return {1024, std::clamp(depth, 0, 64) * 64, changed ? 1024 : 0,
            ratio_q10(best_nodes, nodes, 1024),
            std::clamp(score, -2000, 2000) * 1024 / 1000,
            std::clamp(delta, -1000, 1000) * 1024 / 1000,
            ratio_q10(static_cast<std::uint64_t>(std::max<std::int64_t>(0, elapsed)),
                      static_cast<std::uint64_t>(std::max<std::int64_t>(1, soft)), 4096)};
}

// round(1024 / (1 + exp(-x))) for x=-8,-8+1/16,...,8.
// Mathematical lookup values, generated independently; no engine's tuned constants.
inline constexpr std::array<int, 257> Sigmoid = {
    0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2,
    3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 6, 6, 6,
    7, 7, 8, 8, 9, 9, 10, 11, 11, 12, 13, 14, 14, 15, 16, 17,
    18, 20, 21, 22, 24, 25, 27, 28, 30, 32, 34, 36, 38, 41, 43, 46,
    49, 52, 55, 58, 62, 65, 69, 73, 78, 82, 87, 92, 98, 103, 109, 116,
    122, 129, 136, 144, 152, 160, 168, 177, 187, 197, 207, 217, 228, 239, 251, 263,
    275, 288, 301, 315, 329, 343, 357, 372, 387, 402, 417, 433, 448, 464, 480, 496,
    512, 528, 544, 560, 576, 591, 607, 622, 637, 652, 667, 681, 695, 709, 723, 736,
    749, 761, 773, 785, 796, 807, 817, 827, 837, 847, 856, 864, 872, 880, 888, 895,
    902, 908, 915, 921, 926, 932, 937, 942, 946, 951, 955, 959, 962, 966, 969, 972,
    975, 978, 981, 983, 986, 988, 990, 992, 994, 996, 997, 999, 1000, 1002, 1003, 1004,
    1006, 1007, 1008, 1009, 1010, 1010, 1011, 1012, 1013, 1013, 1014, 1015, 1015, 1016, 1016, 1017,
    1017, 1018, 1018, 1018, 1019, 1019, 1019, 1020, 1020, 1020, 1020, 1021, 1021, 1021, 1021, 1021,
    1021, 1022, 1022, 1022, 1022, 1022, 1022, 1022, 1022, 1023, 1023, 1023, 1023, 1023, 1023, 1023,
    1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1024, 1024, 1024, 1024, 1024, 1024,
    1024
};
inline int sigmoid_q10(std::int64_t logit_q12) {
    const auto bounded = std::clamp<std::int64_t>(logit_q12, -32768, 32768);
    return Sigmoid[static_cast<std::size_t>((bounded + 32768 + 128) / 256)];
}
inline int predict_q10(const Model& model, const Features& x) {
    std::int64_t dot = 0;
    for (std::size_t i = 0; i < x.size(); ++i)
        dot += static_cast<std::int64_t>(model.beta[i]) * x[i];
    return sigmoid_q10(dot / 1024); // C++ truncation toward zero, mirrored by the fitter.
}
inline int multiplier_permille(const Model& model, int probability_q10) {
    const int lo = std::clamp(model.lo, 100, 3000);
    const int hi = std::max(lo, std::clamp(model.hi, 100, 3000));
    const std::int64_t raw = static_cast<std::int64_t>(model.a)
        + static_cast<std::int64_t>(model.b) * std::clamp(probability_q10, 0, 1024) / 1024;
    return static_cast<int>(std::clamp<std::int64_t>(raw, lo, hi));
}
inline std::int64_t soft_target_ms(std::int64_t soft, double legacy_factor, int multiplier,
                                   std::int64_t hard) {
    // The legacy factor remains unchanged; all fitted inference and mapping above are integer.
    // Compare before converting to avoid integer overflow even with extreme UCI clock values.
    const double target = static_cast<double>(soft) * legacy_factor * multiplier / 1000.0;
    if (target >= static_cast<double>(hard)) return hard;
    return std::max<std::int64_t>(1, static_cast<std::int64_t>(target));
}
} // namespace forge::tmfit
