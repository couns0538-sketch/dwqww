#pragma once

#include <string>
#include <string_view>
#include <vector>

// R5A (opus_r5/r5a/REPORT.md): the effective-settings echo and the option-combination warning of the UCI layer.
// Both read the option globals; they are called by the UCI thread between searches (setoption and go stop and join
// any running search first), never by search code, and print nothing while every option is at its default.
namespace forge::r5a {

// The search options that differ from their defaults, as "Name=value" items in UCI spelling (checks as
// true / false), separated by single spaces: first the options in the order `uci` lists them, then every tunable
// whose value differs from its compiled-in default (forge::tune::parameters() order). "" when all are at their
// defaults. Covered: forge::options (forge/search_options.hpp), HistRework, NetScale, the FB2 requests
// (CorrHistV2, LmrTableV2, TtPruneV2), UseNNUE and the tunables; the UCI layer appends NNUEFile, SyzygyPath and the
// build-switch options. A CorrHistV2 request that the per-search snapshot drops (CorrHistPlus nonzero, see
// fb2::effective) is shown as "CorrHistV2=true(dropped)".
[[nodiscard]] std::string active_search_options();

// The compiled-in value of every tunable, in forge::tune::parameters() order. Captured during the static
// initialisation of the search translation unit, i.e. before main and before any setoption.
[[nodiscard]] const std::vector<int>& tune_defaults();

// One warning line (without the "info string " prefix) for an allowed option combination whose parts share a
// mechanism and were never gated together; "" when none applies. Today one case: CorrMargins with TtPruneV2 (set by
// every BundlePreset B1-B4) -- both move the reverse-futility and futility margins of the CorrMargins search
// instance. The combination is not refused. `bundle` is the BundlePreset that set TtPruneV2 ("OFF" or "" when it
// was set on its own); a preset name is included in the text.
[[nodiscard]] std::string combination_warning(std::string_view bundle);

} // namespace forge::r5a
