// Search module: R5A effective-settings echo and option-combination warning (forge/r5a_options.hpp).
// Compiled as part of src/search.cpp (included exactly once, last, so every search function keeps its
// placement). Cold code: the UCI thread calls it once per go or setoption, never inside a search.

namespace forge::r5a {

namespace {

std::vector<int> capture_tune_defaults() {
    std::vector<int> values;
    for (const tune::Parameter& parameter : tune::parameters()) values.push_back(*parameter.value);
    return values;
}

void add(std::string& out, std::string_view name, std::string_view value) {
    if (!out.empty()) out += ' ';
    out += name;
    out += '=';
    out += value;
}

void add_flag(std::string& out, std::string_view name, bool value, bool default_value) {
    if (value != default_value) add(out, name, value ? "true" : "false");
}

void add_int(std::string& out, std::string_view name, int value, int default_value) {
    if (value != default_value) add(out, name, std::to_string(value));
}

} // namespace

const std::vector<int>& tune_defaults() {
    static const std::vector<int> values = capture_tune_defaults();
    return values;
}

namespace {
// Forces the capture during this translation unit's dynamic initialisation (before main). The tunables are
// constant-initialised, so it reads their compiled-in values.
[[maybe_unused]] const bool TuneDefaultsCaptured = !tune_defaults().empty();
} // namespace

std::string active_search_options() {
    std::string out;
    add_flag(out, "SmpExactNodes", options::smp_exact_nodes, false);
    add_flag(out, "SmpBestThread", options::smp_best_thread, false);
    add_flag(out, "LocklessTT", options::lockless_tt, false);
    add_flag(out, "SmpHelpersPastDepth", options::smp_helpers_past_depth, false);
    add_flag(out, "SmpV2", fb2::requested.smp_v2, false);
    add_flag(out, "TmSoftHardClamp", fb2::requested.tm_soft_hard_clamp, false);
    add_int(out, "SyzygyProbeDepth", options::syzygy_probe_depth, 1);
    add_flag(out, "Syzygy50MoveRule", options::syzygy_50_move_rule, true);
    add_int(out, "CorrHistPlus", options::corr_hist_plus, 0);
    add_int(out, "HardDeadline", options::hard_deadline_ms, 0);
    add_int(out, "NNUEKingBuckets", options::nnue_king_buckets, 0);
    add_int(out, "NNUEOutputBuckets", options::nnue_output_buckets, 0);
    add_int(out, "NNUEThreats", options::nnue_threats, 0);
    add_int(out, "NNUEPawnPairs", options::nnue_pawn_pairs, 0);
    add_int(out, "PureNnue", options::pure_nnue ? 1 : 0, 0);
    add_int(out, "CorrMargins", options::corr_margins, 0);
    add_int(out, "CorrExt", options::corr_ext, 0);
    add_flag(out, "CuckooRep", options::cuckoo_rep, false);
    add_flag(out, "MaterialKeyTable", options::material_key_table, false);
    add_int(out, "NetScale", net_scale::percent, net_scale::Default);
    add_int(out, "HistRework", search_options::hist_rework, 0);
    add_flag(out, "IntendedThreefold", options::intended_threefold, false);
    const fb2::Options effective = fb2::effective(fb2::requested, options::corr_hist_plus, options::corr_ext);
    if (fb2::requested.corr_hist_v2) {
        add(out, "CorrHistV2", effective.corr_hist_v2 ? "true" : "true(dropped)");
    }
    add_flag(out, "LmrTableV2", fb2::requested.lmr_table_v2, false);
    add_flag(out, "TtPruneV2", fb2::requested.tt_prune_v2, false);
    if (fb2::requested.singular_v2) {
        add(out, "SingularV2", effective.singular_v2 ? "1" : "1(dropped)");
    }
    add_flag(out, "UseNNUE", nnue::enabled, true);
    const std::vector<tune::Parameter>& parameters = tune::parameters();
    const std::vector<int>& defaults = tune_defaults();
    for (std::size_t i = 0; i < parameters.size() && i < defaults.size(); ++i) {
        add_int(out, parameters[i].name, *parameters[i].value, defaults[i]);
    }
    return out;
}

std::string combination_warning(std::string_view bundle) {
    if (options::corr_margins == 0 || !fb2::requested.tt_prune_v2) return {};
    std::string text = "warning: CorrMargins=" + std::to_string(options::corr_margins) + " with TtPruneV2=true";
    if (!bundle.empty() && bundle != "OFF") {
        text += " (BundlePreset ";
        text += bundle;
        text += ')';
    }
    text += ": both move the reverse-futility and futility margins of the CorrMargins search instance;"
            " never gated together (allowed, not refused)";
    return text;
}

} // namespace forge::r5a
