// Is LmrSignedCorrection capable of any effect at all?
// correction = clamp(..., -CorrectionLimit, CorrectionLimit) = [-8192, 8192]
// static_eval = raw + correction / CorrectionGrain      (CorrectionGrain = 256)
// correction_cp = static_eval - raw_eval = correction/256 in [-32, 32]
// delta = correction_cp / 64   (integer division)
#include <cstdio>
constexpr int CorrectionLimit = 32 * 256;
constexpr int CorrectionGrain = 256;
int apply(int r, int correction_cp) {
    int delta = correction_cp / 64;
    if (delta > 1) delta = 1;
    if (delta < -1) delta = -1;
    const int adjusted = r - delta;
    return adjusted > 0 ? adjusted : 0;
}
int main() {
    int nonzero_delta = 0, changed = 0, total = 0;
    for (int correction = -CorrectionLimit; correction <= CorrectionLimit; ++correction) {
        const int correction_cp = correction / CorrectionGrain;
        const int delta = correction_cp / 64;
        if (delta != 0) ++nonzero_delta;
        for (int r = 0; r <= 30; ++r) {
            ++total;
            if (apply(r, correction_cp) != r) ++changed;
        }
    }
    std::printf("correction range [-%d, %d]\n", CorrectionLimit, CorrectionLimit);
    std::printf("correction_cp range [%d, %d]\n", -CorrectionLimit/CorrectionGrain, CorrectionLimit/CorrectionGrain);
    std::printf("values of correction giving a NONZERO delta: %d\n", nonzero_delta);
    std::printf("(reduction, correction) pairs where the reduction CHANGES: %d of %d\n", changed, total);
    return 0;
}
