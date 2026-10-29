// Synthetic compile-only fixture. Uses the supplied copied header, not engine execution.
// IDEA_SOURCE: source-grounded preset ownership and named option construction.
#include "forge/fb2.hpp"

using forge::fb2::Bundle;
constexpr auto n1 = forge::fb2::bundle_settings(Bundle::N1);
static_assert(n1.corr_hist_plus == 4, "N1 must select CorrHistPlus=4");
static_assert(n1.hist_rework == 0 && !n1.cuckoo_rep, "N1 must not enable unrelated preset fields");
static_assert(!n1.fb2.corr_hist_v2 && !n1.fb2.lmr_table_v2 && !n1.fb2.tt_prune_v2,
              "N1 must not enable the older FB2 features");
static_assert(n1.fb2.singular_v2, "N1 must enable SingularV2");
static_assert(!n1.fb2.smp_v2, "N1 must not enable SmpV2");
static_assert(!n1.fb2.tm_soft_hard_clamp, "N1 must not enable TmSoftHardClamp");

constexpr bool ordinary_presets_leave_new_flags_off() {
    for (const auto preset : {Bundle::Off, Bundle::B1, Bundle::B2, Bundle::B3, Bundle::B4}) {
        const auto s = forge::fb2::bundle_settings(preset);
        if (s.fb2.singular_v2 || s.fb2.smp_v2 || s.fb2.tm_soft_hard_clamp) return false;
    }
    return true;
}
static_assert(ordinary_presets_leave_new_flags_off(), "OFF/B1-B4 must leave all three new flags false");
