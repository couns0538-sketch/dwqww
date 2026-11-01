// Numeric safety and independent sigmoid reference for the time-only model.
#include "search/tmfit.hpp"
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>

int main() {
    using namespace forge::tmfit;
    int failures = 0;
    auto check = [&](bool ok, const char* what) {
        if (!ok) { ++failures; std::cerr << "FAIL " << what << '\n'; }
    };
    check(ratio_q10(1, 2, 4096) == 512, "fraction scale");
    check(ratio_q10(UINT64_MAX - 1, UINT64_MAX, 4096) == 1023, "fraction overflow");
    check(ratio_q10(UINT64_MAX, 1, 4096) == 4096, "ratio saturation");
    check(ratio_q10(0, 0, 4096) == 0, "zero denominator");
    const auto f = features(16, true, 1, 2, -1500, -500, 100, 200);
    check(f == Features{1024, 1024, 1024, 512, -1536, -512, 512}, "feature units and signed truncation");
    const auto extreme = features(1000, false, UINT64_MAX, 1, INT32_MIN, INT32_MAX, INT64_MAX, 1);
    check(extreme == Features{1024, 4096, 0, 1024, -2048, 1024, 4096}, "feature clamps");
    int last = -1;
    for (int z = -32768; z <= 32768; ++z) {
        const int p = sigmoid_q10(z);
        check(p >= last && p >= 0 && p <= 1024, "sigmoid bounds and monotonicity");
        // Nearest grid spacing is 1/16; worst derivative is 1/4.
        check(std::abs(p / 1024.0 - 1.0 / (1.0 + std::exp(-z / 4096.0))) < 0.0084,
              "sigmoid independent numeric accuracy");
        last = p;
    }
    Model model{};
    check(predict_q10(model, f) == 512, "zero logit probability");
    model.beta[0] = 4096;
    check(predict_q10(model, f) == 749, "positive logit units");
    model.beta[0] = -4096;
    check(predict_q10(model, f) == 275, "negative logit units");
    model.beta[0] = -128;
    model.beta[1] = -1;
    check(predict_q10(model, Features{1024,1,0,0,0,0,0}) == 512, "signed dot truncates toward zero");
    model.beta.fill(131072);
    check(predict_q10(model, Features{1024,4096,1024,1024,2048,1024,4096}) == 1024,
          "dot product wide accumulation");
    model.a = INT32_MAX;
    model.b = INT32_MAX;
    model.lo = 500;
    model.hi = 1500;
    check(multiplier_permille(model, 1024) == 1500, "absurd mapping clamps");
    model.lo = 2000;
    model.hi = 1000;
    check(multiplier_permille(model, 0) == 2000, "crossed bounds safe");
    check(soft_target_ms(100, 1.5, 2000, 200) == 200, "hard cap");
    check(soft_target_ms(100, 1.5, 500, 200) == 75, "scales before hard cap");
    check(soft_target_ms(INT64_MAX, 10.0, 3000, INT64_MAX) == INT64_MAX, "target overflow cap");
    check(soft_target_ms(1, 0.01, 100, 50) == 1, "positive minimum");
    std::cout << "tmfit numeric tests " << (failures ? "FAIL" : "PASS") << '\n';
    return failures ? 1 : 0;
}
