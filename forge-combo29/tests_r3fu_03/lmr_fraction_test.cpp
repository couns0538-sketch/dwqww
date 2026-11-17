#include "forge/search.hpp"

#include <iostream>

namespace {

int fail(const char* why, int got, int expect) {
    std::cerr << "fail: " << why << " got " << got << " expected " << expect << '\n';
    return 1;
}

} // namespace

int main() {
    using forge::apply_lmr_signed_correction;
    struct Case {
        int reduction;
        int correction_cp;
        int expect;
        const char* why;
    };
    const Case cases[] = {
        {4, 0, 4, "zero correction is unchanged"},
        {3, 63, 3, "63cp rounds toward zero"},
        {3, -63, 3, "-63cp rounds toward zero"},
        {3, 64, 2, "64cp subtracts one ply"},
        {3, -64, 4, "-64cp adds one ply"},
        {3, 127, 2, "127cp is still one ply toward zero"},
        {3, -127, 4, "-127cp is still one ply toward zero"},
        {6, 128, 5, "128cp is one ply, not two"},
        {6, -128, 7, "-128cp is one ply, not two"},
        {6, 10000, 5, "positive correction is capped at one ply"},
        {6, -10000, 7, "negative correction is capped at one ply"},
        {0, 64, 0, "never below zero"},
        {1, 64, 0, "one ply less from 1 lands on zero"},
        {0, -64, 1, "one ply more from zero is allowed"},
        {-3, -64, 0, "a negative base plus one ply stays at zero"},
        {2, -1, 2, "a negative fraction below 64cp is zero"},
    };
    for (const Case& item : cases) {
        const int got = apply_lmr_signed_correction(item.reduction, item.correction_cp);
        if (got != item.expect) return fail(item.why, got, item.expect);
        if (got < 0) return fail("negative reduction", got, item.expect);
    }
    if (forge::tune::LmrSignedCorrection) {
        std::cerr << "fail: option must default off\n";
        return 1;
    }
    std::cout << "r3fu fraction ok\n";
    return 0;
}
