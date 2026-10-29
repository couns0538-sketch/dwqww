// R5A option echo and conflict guards (opus_r5/r5a/REPORT.md M2; forge/r5a_options.hpp).
// Part A (library): forge::r5a::active_search_options() is "" at the defaults, names each non-default option as
//   Name=value in UCI spelling and listing order, follows the tunables, and is "" again after a reset;
//   combination_warning() fires only for CorrMargins with TtPruneV2 and names the preset.
// Part B (UCI, argv[1] = forge executable, scripted stdin): no new output at the defaults; exactly one
//   `info string active: ...` line per go once an option is set, none after it is reset; CorrHistPlus 1/2/4/6 and
//   CorrHistV2 refuse each other in both orders (the value stays unchanged, shown by the echo); CorrMargins with a
//   BundlePreset (all four set TtPruneV2) prints the warning but is not refused.
// Writes its engine transcripts (r5a_opt_*.in / .out / .err) into the working directory and leaves them there.
// usage: forge_r5a_options_tests <forge executable>
#include "forge/corr_margins.hpp"
#include "forge/fb2.hpp"
#include "forge/hist_rework.hpp"
#include "forge/net_scale.hpp"
#include "forge/nnue.hpp"
#include "forge/r5a_options.hpp"
#include "forge/search_options.hpp"
#include "forge/search_tune.hpp"

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <functional>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

int failures = 0;

void report(bool ok, const std::string& what) {
    std::cout << (ok ? "PASS " : "FAIL ") << what << '\n';
    if (!ok) ++failures;
}

int* tunable(const char* name) {
    for (const forge::tune::Parameter& p : forge::tune::parameters()) {
        if (std::string(p.name) == name) return p.value;
    }
    return nullptr;
}

// One option change: `set` applies it, `reset` restores the default, `expected` is the whole echo while it is on.
struct Case {
    std::string name;
    std::function<void()> set;
    std::function<void()> reset;
    std::string expected;
};

void part_a() {
    using namespace forge;
    report(r5a::active_search_options().empty(), "A defaults: active_search_options() is empty (got '" +
                                                     r5a::active_search_options() + "')");
    const std::vector<tune::Parameter>& parameters = tune::parameters();
    bool same = r5a::tune_defaults().size() == parameters.size();
    for (std::size_t i = 0; same && i < parameters.size(); ++i) same = r5a::tune_defaults()[i] == *parameters[i].value;
    report(same, "A tune_defaults() has one compiled-in value per tunable (" + std::to_string(parameters.size()) + ")");

    int* rfp = tunable("RfpMargin");
    int* corr_rfp = tunable("CorrRfpPct");
    report(rfp != nullptr && corr_rfp != nullptr, "A tunables RfpMargin and CorrRfpPct exist");
    const int rfp_default = rfp ? *rfp : 0;
    const int corr_rfp_default = corr_rfp ? *corr_rfp : 0;

    const std::vector<Case> cases = {
        {"CorrMargins", [] { options::corr_margins = 1; }, [] { options::corr_margins = 0; }, "CorrMargins=1"},
        {"CorrExt", [] { options::corr_ext = 1; }, [] { options::corr_ext = 0; }, "CorrExt=1"},
        {"CorrHistPlus 2", [] { options::corr_hist_plus = 2; }, [] { options::corr_hist_plus = 0; }, "CorrHistPlus=2"},
        {"CorrHistPlus 4", [] { options::corr_hist_plus = 4; }, [] { options::corr_hist_plus = 0; }, "CorrHistPlus=4"},
        {"CorrHistPlus 6", [] { options::corr_hist_plus = 6; }, [] { options::corr_hist_plus = 0; }, "CorrHistPlus=6"},
        {"NetScale 99", [] { net_scale::percent = 99; }, [] { net_scale::percent = net_scale::Default; }, "NetScale=99"},
        {"HistRework 1", [] { search_options::hist_rework = 1; }, [] { search_options::hist_rework = 0; }, "HistRework=1"},
        {"HistRework 3", [] { search_options::hist_rework = 3; }, [] { search_options::hist_rework = 0; }, "HistRework=3"},
        {"CuckooRep", [] { options::cuckoo_rep = true; }, [] { options::cuckoo_rep = false; }, "CuckooRep=true"},
        {"CorrHistV2", [] { fb2::requested.corr_hist_v2 = true; }, [] { fb2::requested.corr_hist_v2 = false; },
         "CorrHistV2=true"},
        {"LmrTableV2", [] { fb2::requested.lmr_table_v2 = true; }, [] { fb2::requested.lmr_table_v2 = false; },
         "LmrTableV2=true"},
        {"TtPruneV2", [] { fb2::requested.tt_prune_v2 = true; }, [] { fb2::requested.tt_prune_v2 = false; },
         "TtPruneV2=true"},
        {"IntendedThreefold", [] { options::intended_threefold = true; }, [] { options::intended_threefold = false; },
         "IntendedThreefold=true"},
        {"MaterialKeyTable", [] { options::material_key_table = true; }, [] { options::material_key_table = false; },
         "MaterialKeyTable=true"},
        {"LocklessTT", [] { options::lockless_tt = true; }, [] { options::lockless_tt = false; }, "LocklessTT=true"},
        {"SmpExactNodes", [] { options::smp_exact_nodes = true; }, [] { options::smp_exact_nodes = false; },
         "SmpExactNodes=true"},
        {"Syzygy50MoveRule", [] { options::syzygy_50_move_rule = false; }, [] { options::syzygy_50_move_rule = true; },
         "Syzygy50MoveRule=false"},
        {"SyzygyProbeDepth", [] { options::syzygy_probe_depth = 3; }, [] { options::syzygy_probe_depth = 1; },
         "SyzygyProbeDepth=3"},
        {"HardDeadline", [] { options::hard_deadline_ms = 10; }, [] { options::hard_deadline_ms = 0; }, "HardDeadline=10"},
        {"UseNNUE", [] { nnue::enabled = false; }, [] { nnue::enabled = true; }, "UseNNUE=false"},
        {"RfpMargin (advertised tunable)", [rfp] { if (rfp) *rfp = 80; }, [rfp, rfp_default] { if (rfp) *rfp = rfp_default; },
         "RfpMargin=80"},
        {"CorrRfpPct (unlisted tunable)", [corr_rfp] { if (corr_rfp) *corr_rfp = 60; },
         [corr_rfp, corr_rfp_default] { if (corr_rfp) *corr_rfp = corr_rfp_default; }, "CorrRfpPct=60"},
    };
    for (const Case& c : cases) {
        c.set();
        const std::string on = r5a::active_search_options();
        c.reset();
        const std::string off = r5a::active_search_options();
        report(on == c.expected && off.empty(), "A " + c.name + ": '" + on + "' then '" + off + "' after the reset");
    }

    // Listing order and the dropped CorrHistV2 request (only reachable without the UCI guard).
    options::corr_margins = 1;
    fb2::requested.tt_prune_v2 = true;
    net_scale::percent = 99;
    report(r5a::active_search_options() == "CorrMargins=1 NetScale=99 TtPruneV2=true",
           "A order: '" + r5a::active_search_options() + "'");
    options::corr_margins = 0;
    fb2::requested.tt_prune_v2 = false;
    net_scale::percent = net_scale::Default;
    options::corr_hist_plus = 2;
    fb2::requested.corr_hist_v2 = true;
    report(r5a::active_search_options() == "CorrHistPlus=2 CorrHistV2=true(dropped)",
           "A CorrHistV2 with CorrHistPlus (no UCI guard): '" + r5a::active_search_options() + "'");
    options::corr_hist_plus = 0;
    fb2::requested.corr_hist_v2 = false;

    // A preset and its reset.
    fb2::apply_bundle(fb2::Bundle::B1);
    report(r5a::active_search_options() == "CorrHistPlus=1 CuckooRep=true HistRework=2 TtPruneV2=true",
           "A BundlePreset B1: '" + r5a::active_search_options() + "'");
    fb2::apply_bundle(fb2::Bundle::Off);
    report(r5a::active_search_options().empty(), "A BundlePreset OFF: empty again");

    // Combination warning.
    report(r5a::combination_warning("OFF").empty(), "A warning: none at the defaults");
    options::corr_margins = 1;
    report(r5a::combination_warning("OFF").empty(), "A warning: none for CorrMargins alone");
    options::corr_margins = 0;
    fb2::requested.tt_prune_v2 = true;
    report(r5a::combination_warning("B2").empty(), "A warning: none for TtPruneV2 alone");
    options::corr_margins = 1;
    const std::string w_preset = r5a::combination_warning("B2");
    const std::string w_alone = r5a::combination_warning("OFF");
    report(w_preset.rfind("warning: CorrMargins=1 with TtPruneV2=true (BundlePreset B2):", 0) == 0,
           "A warning with a preset: '" + w_preset + "'");
    report(w_alone.rfind("warning: CorrMargins=1 with TtPruneV2=true:", 0) == 0 &&
               w_alone.find("BundlePreset") == std::string::npos,
           "A warning without a preset: '" + w_alone + "'");
    options::corr_margins = 0;
    fb2::requested.tt_prune_v2 = false;
    report(r5a::active_search_options().empty(), "A end: every option back at its default");
}

// M5: the advertised CorrMarginsScale / CorrExtTripleCorr spins and the scaled CorrMargins formulas.
void part_a_m5() {
    using namespace forge;
    bool listed = true;
    for (const std::string_view name : tune::R5aAdvertisedParameters) listed &= tunable(std::string(name).c_str()) != nullptr;
    report(listed && tune::R5aAdvertisedParameters.size() == 2, "A5 R5aAdvertisedParameters name 2 existing tunables");
    report(tune::CorrMarginsScale == 100 && tune::CorrExtTripleCorr == 48,
           "A5 defaults: CorrMarginsScale 100, CorrExtTripleCorr 48 (the O8 constant)");
    // Scale 100 == the O5 formulas bit for bit (old expressions written out here).
    bool same = true;
    for (int c = 0; c <= 400 && same; ++c) {
        for (const int depth : {1, 3, 6, 8}) {
            for (const bool improving : {false, true}) {
                same &= corr_margins::rfp_margin(depth, improving, c) ==
                        tune::RfpMargin * depth - tune::RfpImproving * improving + c * tune::CorrRfpPct / 100;
            }
            same &= corr_margins::futility_margin(depth, c) ==
                    tune::FutilityBase + tune::FutilityMultiplier * depth + c * tune::CorrFutilityPct / 100;
            same &= corr_margins::null_move_threshold(37, depth, c) ==
                    37 - tune::NullMoveMarginDepth * depth + tune::NullMoveMarginBase + c * tune::CorrNullMovePct / 100;
        }
        for (int r = -2; r <= 30; ++r) {
            const int old = r <= 0 ? r : r - std::min(r, r * c * tune::CorrLmrPct / 6400);
            same &= corr_margins::lmr_reduction(r, c) == old;
        }
    }
    report(same, "A5 scale 100: rfp / futility / null-move / LMR equal the O5 formulas for |correction| 0..400");
    // Scale 0 removes every correction term; scale 200 doubles it (exact floor).
    tune::CorrMarginsScale = 0;
    bool zero = true;
    for (int c = 0; c <= 400; c += 7) {
        zero &= corr_margins::rfp_margin(5, true, c) == tune::RfpMargin * 5 - tune::RfpImproving &&
                corr_margins::futility_margin(4, c) == tune::FutilityBase + tune::FutilityMultiplier * 4 &&
                corr_margins::lmr_reduction(9, c) == 9;
    }
    report(zero, "A5 scale 0: margins and LMR are the AL1 s198 values at every |correction|");
    tune::CorrMarginsScale = 200;
    bool twice = true;
    for (int c = 0; c <= 400; c += 7) twice &= corr_margins::scaled_term(c, tune::CorrFutilityPct) == c * tune::CorrFutilityPct / 50;
    report(twice, "A5 scale 200: the futility correction term is c * pct / 50");
    tune::CorrMarginsScale = 400;
    tune::CorrLmrPct = 400;
    const int big = corr_margins::lmr_reduction(30, 1000);
    report(big == 0, "A5 limits (r 30, |correction| 1000, pct 400, scale 400): no overflow, relief capped at r (got " +
                         std::to_string(big) + ")");
    tune::CorrLmrPct = 25;
    tune::CorrMarginsScale = 100;
    report(r5a::active_search_options().empty(), "A5 end: every tunable back at its default");
}

// ---- Part B: the real engine with scripted stdin
std::string read_file(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    std::ostringstream s;
    s << in.rdbuf();
    return s.str();
}

std::string run_engine(const std::string& engine, const std::string& name, const std::string& script) {
    const std::string in = "r5a_opt_" + name + ".in";
    const std::string out = "r5a_opt_" + name + ".out";
    const std::string err = "r5a_opt_" + name + ".err";
    {
        std::ofstream f(in, std::ios::binary);
        f << script;
    }
    std::string command = "\"" + engine + "\" < \"" + in + "\" > \"" + out + "\" 2> \"" + err + "\"";
#if defined(_WIN32)
    command = "\"" + command + "\"";   // cmd.exe /c strips one pair of outer quotes
#endif
    std::fflush(nullptr);
    const int status = std::system(command.c_str());
    if (status != 0) std::cout << "  [" << name << "] exit status " << status << '\n';
    return read_file(out);
}

std::vector<std::string> lines_with(const std::string& text, const std::string& prefix) {
    std::vector<std::string> found;
    std::istringstream lines(text);
    for (std::string line; std::getline(lines, line);) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.rfind(prefix, 0) == 0) found.push_back(line);
    }
    return found;
}

std::string joined(const std::vector<std::string>& lines) {
    std::string s;
    for (const std::string& l : lines) s += (s.empty() ? "" : " | ") + l;
    return s.empty() ? "(none)" : s;
}

const std::string Head = "uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\n";
const std::string Go = "isready\nposition startpos\ngo depth 2\nisready\n";
std::string set(const std::string& name, const std::string& value) {
    return "setoption name " + name + " value " + value + "\n";
}

void part_b(const std::string& engine) {
    const std::string Active = "info string active: ";
    {
        const std::string out = run_engine(engine, "defaults", Head + Go + Go + "quit\n");
        report(lines_with(out, Active).empty() && lines_with(out, "info string warning").empty() &&
                   lines_with(out, "bestmove").size() == 2,
               "B defaults: no active / warning line, 2 bestmoves (" + joined(lines_with(out, "info string")) + ")");
    }
    {
        const std::string out = run_engine(engine, "corrmargins_on_off",
                                           Head + set("CorrMargins", "1") + Go + Go + set("CorrMargins", "0") + Go + "quit\n");
        const auto active = lines_with(out, Active);
        report(active.size() == 2 && active[0] == Active + "CorrMargins=1" && active[1] == active[0],
               "B CorrMargins 1: one active line per go, none after the reset (" + joined(active) + ")");
    }
    for (const std::string value : {"1", "2", "4", "6"}) {
        const std::string out = run_engine(engine, "v2_then_plus" + value,
                                           Head + set("CorrHistV2", "true") + set("CorrHistPlus", value) + Go + "quit\n");
        const auto refused = lines_with(out, "info string CorrHistPlus refused");
        const auto active = lines_with(out, Active);
        report(refused.size() == 1 && active.size() == 1 && active[0] == Active + "CorrHistV2=true",
               "B CorrHistV2 then CorrHistPlus " + value + ": refused, value unchanged (" + joined(refused) + " / " +
                   joined(active) + ")");
    }
    for (const std::string value : {"2", "4", "6"}) {
        const std::string out = run_engine(engine, "plus" + value + "_then_v2",
                                           Head + set("CorrHistPlus", value) + set("CorrHistV2", "true") + Go + "quit\n");
        const auto refused = lines_with(out, "info string CorrHistV2 refused");
        const auto active = lines_with(out, Active);
        report(refused.size() == 1 && active.size() == 1 && active[0] == Active + "CorrHistPlus=" + value,
               "B CorrHistPlus " + value + " then CorrHistV2: refused, value unchanged (" + joined(refused) + " / " +
                   joined(active) + ")");
    }
    {
        const std::string out = run_engine(engine, "preset_then_cm", Head + set("BundlePreset", "B1") + set("CorrMargins", "1") + Go + "quit\n");
        const auto warnings = lines_with(out, "info string warning: CorrMargins=1 with TtPruneV2=true (BundlePreset B1):");
        const auto active = lines_with(out, Active);
        report(warnings.size() == 1 && active.size() == 1 &&
                   active[0] == Active + "CorrHistPlus=1 CorrMargins=1 CuckooRep=true HistRework=2 TtPruneV2=true",
               "B BundlePreset B1 then CorrMargins 1: one warning, not refused (" + joined(warnings) + " / " + joined(active) + ")");
    }
    {
        const std::string out = run_engine(engine, "cm_then_preset", Head + set("CorrMargins", "1") + set("BundlePreset", "B2") + Go + "quit\n");
        const auto warnings = lines_with(out, "info string warning: CorrMargins=1 with TtPruneV2=true (BundlePreset B2):");
        const auto preset = lines_with(out, "info string BundlePreset B2:");
        report(warnings.size() == 1 && preset.size() == 1 && out.find(preset[0]) < out.find(warnings[0]),
               "B CorrMargins 1 then BundlePreset B2: preset line, then one warning (" + joined(warnings) + ")");
    }
    {
        const std::string out = run_engine(engine, "cm_preset_off",
                                           Head + set("CorrMargins", "1") + set("BundlePreset", "B3") + set("BundlePreset", "OFF") + Go + "quit\n");
        const auto warnings = lines_with(out, "info string warning");
        const auto active = lines_with(out, Active);
        report(warnings.size() == 1 && active.size() == 1 && active[0] == Active + "CorrMargins=1",
               "B BundlePreset OFF clears the combination: one warning (B3) only, echo CorrMargins=1 (" + joined(active) + ")");
    }
    {
        const std::string out = run_engine(engine, "ttprune_alone_cm", Head + set("TtPruneV2", "true") + set("CorrMargins", "1") + Go + "quit\n");
        const auto warnings = lines_with(out, "info string warning: CorrMargins=1 with TtPruneV2=true:");
        report(warnings.size() == 1, "B TtPruneV2 on its own then CorrMargins 1: one warning without a preset name (" +
                                         joined(warnings) + ")");
    }
    {
        const std::string out = run_engine(engine, "netscale_tunable",
                                           Head + set("NetScale", "99") + set("RfpMargin", "80") + Go + set("NetScale", "100") +
                                               set("RfpMargin", "72") + Go + "quit\n");
        const auto active = lines_with(out, Active);
        report(active.size() == 1 && active[0] == Active + "NetScale=99 RfpMargin=80",
               "B NetScale 99 + RfpMargin 80, then both reset: one echo (" + joined(active) + ")");
    }
    {
        // M5: both spins advertised once, after the R3-4 block, with the current defaults; a set value is echoed.
        const std::string out = run_engine(engine, "m5_spins",
                                           Head + "isready\n" + set("CorrMarginsScale", "150") + set("CorrExtTripleCorr", "32") +
                                               Go + set("CorrMarginsScale", "100") + set("CorrExtTripleCorr", "48") + Go + "quit\n");
        const auto scale = lines_with(out, "option name CorrMarginsScale ");
        const auto triple = lines_with(out, "option name CorrExtTripleCorr ");
        const auto active = lines_with(out, Active);
        const bool order = out.find("option name AspirationDelta ") < out.find("option name CorrMarginsScale ") &&
                           out.find("option name CorrMarginsScale ") < out.find("option name CorrExtTripleCorr ");
        report(scale.size() == 1 && scale[0] == "option name CorrMarginsScale type spin default 100 min 0 max 400" &&
                   triple.size() == 1 && triple[0] == "option name CorrExtTripleCorr type spin default 48 min 0 max 256" && order,
               "B M5: CorrMarginsScale (100, 0-400) and CorrExtTripleCorr (48, 0-256) advertised once after AspirationDelta (" +
                   joined(scale) + " / " + joined(triple) + ")");
        report(active.size() == 1 && active[0] == Active + "CorrExtTripleCorr=32 CorrMarginsScale=150",
               "B M5: set values echoed in tunable order, nothing after the reset (" + joined(active) + ")");
    }
}

} // namespace

int main(int argc, char** argv) {
    part_a();
    part_a_m5();
    if (argc >= 2) {
        std::string engine = argv[1];
#if defined(_WIN32)
        for (char& c : engine) if (c == '/') c = '\\';
#endif
        part_b(engine);
    } else {
        std::cout << "SKIP part B (no engine path given)\n";
    }
    std::cout << (failures == 0 ? "ALL OK" : "FAILURES: " + std::to_string(failures)) << '\n';
    return failures == 0 ? 0 : 1;
}
