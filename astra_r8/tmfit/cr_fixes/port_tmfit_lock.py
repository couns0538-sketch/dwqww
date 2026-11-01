#!/usr/bin/env python3
"""CR port of astra-r8-tmfit (41699d07) onto the crew lock source d4f4312 (FD3A5190).
Checks every anchor (exactly once) before writing anything. Usage: port_tmfit_lock.py <lock-tree> <tmfit.hpp> <tmfit_tests.cpp>"""
import pathlib, sys
root = pathlib.Path(sys.argv[1]); hdr = pathlib.Path(sys.argv[2]).read_text(); tst = pathlib.Path(sys.argv[3]).read_text()
E = []  # (file, old, new)
def e(f, old, new): E.append((f, old, new))
e("CMakeLists.txt",
 'option(FORGE_EXPOSE_TUNABLES "Advertise search tuning constants as UCI options (development builds)" OFF)\n',
 'option(FORGE_EXPOSE_TUNABLES "Advertise search tuning constants as UCI options (development builds)" OFF)\n'
 'option(FORGE_TM_LOG "Emit completed root iterations for time-model fitting" OFF)\n')
e("CMakeLists.txt",
 'target_compile_features(forge_core PUBLIC cxx_std_20)\n',
 'target_compile_features(forge_core PUBLIC cxx_std_20)\nif(FORGE_TM_LOG)\n    target_compile_definitions(forge_core PUBLIC FORGE_TM_LOG=1)\nendif()\n')
e("CMakeLists.txt",
 'add_executable(forge_bench bench/benchmark.cpp)\n',
 'add_executable(forge_tmfit_tests tests/tmfit_tests.cpp)\ntarget_include_directories(forge_tmfit_tests PRIVATE src)\n'
 'target_link_libraries(forge_tmfit_tests PRIVATE forge_core Threads::Threads)\n\nadd_executable(forge_bench bench/benchmark.cpp)\n')
e("CMakeLists.txt",
 'add_test(NAME forge_rule50_tests COMMAND forge_rule50_tests)\n',
 'add_test(NAME forge_rule50_tests COMMAND forge_rule50_tests)\nadd_test(NAME forge_tmfit_tests COMMAND forge_tmfit_tests)\n')
e("include/forge/search.hpp",
 'extern int TmMinFactorPercent;    // lower bound of the combined soft-limit factor (x0.01)\n',
 'extern int TmMinFactorPercent;    // lower bound of the combined soft-limit factor (x0.01)\n'
 '// Fitted model coefficients Q12 and probability-to-multiplier mapping permille (UCI TmFitModel).\n'
 'extern int TmFitBias, TmFitDepth, TmFitChanged, TmFitEffort, TmFitScore, TmFitDelta, TmFitElapsed;\n'
 'extern int TmFitA, TmFitB, TmFitLo, TmFitHi;\n')
e("include/forge/search.hpp",
 '} // namespace tune\n',
 '} // namespace tune\n\n// UCI TmFitModel (spin 0-1, default 0). Changes only the clock-managed soft\n'
 '// budget. The main worker snapshots it once per search; written only while no search runs.\n'
 'namespace options {\nextern bool tm_fit_model;\n} // namespace options\n')
e("src/search.cpp",
 '#include "forge/uci_output.hpp"\n',
 '#include "forge/uci_output.hpp"\n#include "search/tmfit.hpp"\n')
e("src/search.cpp",
 'int TmMinFactorPercent = 45;\n',
 'int TmMinFactorPercent = 45;\n// UNPROVEN: Q12 logistic fit from 52,012 logged iterations; see astra_r8/tmfit.\n'
 'int TmFitBias = -3201;\nint TmFitDepth = -5127;\nint TmFitChanged = 6120;\nint TmFitEffort = -3440;\n'
 'int TmFitScore = -1537;\nint TmFitDelta = -167;\nint TmFitElapsed = 1284;\nint TmFitA = 742;\nint TmFitB = 3000;\n'
 'int TmFitLo = 650;\nint TmFitHi = 1750;\n')
e("src/search.cpp",
 '        {"TmFallingEvalPercent", &TmFallingEvalPercent, 0, 400}, {"TmMinFactorPercent", &TmMinFactorPercent, 10, 100},\n',
 '        {"TmFallingEvalPercent", &TmFallingEvalPercent, 0, 400}, {"TmMinFactorPercent", &TmMinFactorPercent, 10, 100},\n'
 '        {"TmFitBias", &TmFitBias, -131072, 131072},           {"TmFitDepth", &TmFitDepth, -131072, 131072},\n'
 '        {"TmFitChanged", &TmFitChanged, -131072, 131072},     {"TmFitEffort", &TmFitEffort, -131072, 131072},\n'
 '        {"TmFitScore", &TmFitScore, -131072, 131072},         {"TmFitDelta", &TmFitDelta, -131072, 131072},\n'
 '        {"TmFitElapsed", &TmFitElapsed, -131072, 131072},\n'
 '        {"TmFitA", &TmFitA, -1000000, 1000000},              {"TmFitB", &TmFitB, -1000000, 1000000},\n'
 '        {"TmFitLo", &TmFitLo, 100, 3000},                    {"TmFitHi", &TmFitHi, 100, 3000},\n')
e("src/search.cpp",
 '} // namespace tune\n\nnamespace {\n',
 '} // namespace tune\n\nnamespace options {\nbool tm_fit_model = false;\n} // namespace options\n\nnamespace {\n')
e("src/search.cpp",
 '        time_managed_ = true;\n    }\n    SearchInfo result;\n',
 '        time_managed_ = true;\n    }\n'
 '    const bool fit_enabled = options::tm_fit_model && is_main() && time_managed_;\n'
 '    const tmfit::Model fit_model = fit_enabled\n'
 '        ? tmfit::Model{{tune::TmFitBias, tune::TmFitDepth, tune::TmFitChanged, tune::TmFitEffort,\n'
 '                       tune::TmFitScore, tune::TmFitDelta, tune::TmFitElapsed},\n'
 '                      tune::TmFitA, tune::TmFitB, tune::TmFitLo, tune::TmFitHi}\n'
 '        : tmfit::Model{};\n    SearchInfo result;\n')
e("src/search.cpp",
 '        emit(depth, score, result.pv);\n\n        if (result.best_move == previous_best) ++stable_iterations;\n',
 '        emit(depth, score, result.pv);\n\n'
 '#ifdef FORGE_TM_LOG\n'
 '        // Training instrumentation is compiled out entirely in ordinary builds.\n'
 '        if (is_main() && emit_info) {\n'
 '            std::uint64_t best_nodes = 0;\n'
 '            const auto effort_end = root_effort_moves_.begin() + static_cast<std::ptrdiff_t>(root_effort_count_);\n'
 '            const auto best_effort = std::find(root_effort_moves_.begin(), effort_end, result.best_move);\n'
 '            if (best_effort != effort_end) {\n'
 '                best_nodes = root_move_nodes_[static_cast<std::size_t>(best_effort - root_effort_moves_.begin())];\n'
 '            }\n'
 '            const std::int64_t log_elapsed = elapsed_ms();\n'
 '            const std::lock_guard<std::mutex> output_lock(uci_output_mutex());\n'
 '            std::cout << "info string tm_log {\\"depth\\":" << depth\n'
 '                      << ",\\"best_move\\":\\"" << Board::move_to_uci(result.best_move) << \'\\"\'\n'
 '                      << ",\\"changed\\":" << (!previous_best.is_none() && result.best_move != previous_best ? 1 : 0)\n'
 '                      << ",\\"node_fraction\\":" << (local_nodes_ ? static_cast<double>(best_nodes) / static_cast<double>(local_nodes_) : 0.0)\n'
 '                      << ",\\"node_fraction_q10\\":" << tmfit::ratio_q10(best_nodes, local_nodes_, 1024)\n'
 '                      << ",\\"score_cp\\":" << score\n'
 '                      << ",\\"score_delta_cp\\":" << (previous_score == ValueNone ? 0 : score - previous_score)\n'
 '                      << ",\\"elapsed_ms\\":" << log_elapsed << ",\\"soft_ms\\":" << soft_limit_ms_\n'
 '                      << ",\\"hard_ms\\":" << hard_limit_ms_ << \'}\' << std::endl;\n'
 '        }\n'
 '#endif\n'
 '        const bool fit_changed = fit_enabled && !previous_best.is_none() && result.best_move != previous_best;\n'
 '        if (result.best_move == previous_best) ++stable_iterations;\n')
e("src/search.cpp",
 '            if (elapsed_ms() >= static_cast<std::int64_t>(static_cast<double>(soft_limit_ms_) * factor)) break;\n',
 '            if (fit_enabled) {\n'
 '                std::uint64_t best_nodes = 0;\n'
 '                const auto effort_end = root_effort_moves_.begin() + static_cast<std::ptrdiff_t>(root_effort_count_);\n'
 '                const auto best_effort = std::find(root_effort_moves_.begin(), effort_end, result.best_move);\n'
 '                if (best_effort != effort_end)\n'
 '                    best_nodes = root_move_nodes_[static_cast<std::size_t>(best_effort - root_effort_moves_.begin())];\n'
 '                const int score_delta = iteration_previous_score == ValueNone ? 0 : score - iteration_previous_score;\n'
 '                const auto x = tmfit::features(depth, fit_changed, best_nodes, local_nodes_, score,\n'
 '                                               score_delta, elapsed_ms(), soft_limit_ms_);\n'
 '                const int probability = tmfit::predict_q10(fit_model, x);\n'
 '                const int multiplier = tmfit::multiplier_permille(fit_model, probability);\n'
 '                const auto target = tmfit::soft_target_ms(soft_limit_ms_, factor, multiplier, hard_limit_ms_);\n'
 '                if (emit_info) {\n'
 '                    const std::lock_guard<std::mutex> output_lock(uci_output_mutex());\n'
 '                    std::cout << "info string tmfit {\\"depth\\":" << depth << ",\\"p_q10\\":" << probability\n'
 '                              << ",\\"multiplier_permille\\":" << multiplier << ",\\"soft_target_ms\\":" << target\n'
 '                              << ",\\"hard_ms\\":" << hard_limit_ms_ << ",\\"changed\\":" << (fit_changed ? 1 : 0)\n'
 '                              << ",\\"effort_q10\\":" << x[3] << ",\\"delta_cp\\":" << score_delta\n'
 '                              << \'}\' << std::endl;\n'
 '                }\n'
 '                if (elapsed_ms() >= target) break;\n'
 '            } else {\n'
 '                if (elapsed_ms() >= static_cast<std::int64_t>(static_cast<double>(soft_limit_ms_) * factor)) break;\n'
 '            }\n')
e("src/uci.cpp",
 '            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n',
 '            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n'
 '            std::cout << "option name TmFitModel type spin default 0 min 0 max 1\\n";\n')
e("src/uci.cpp",
 '            } else if (name == "Clear Hash") {\n',
 '            } else if (name == "TmFitModel") {\n'
 '                if (value_text == "0" || value_text == "1") {\n'
 '                    forge::options::tm_fit_model = value_text == "1";\n'
 '                } else {\n'
 '                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
 '                    std::cout << "info string invalid value for option TmFitModel" << std::endl;\n'
 '                }\n'
 '            } else if (name == "Clear Hash") {\n')
texts = {}
bad = []
for f, old, new in E:
    t = texts.setdefault(f, (root / f).read_text())
    n = t.count(old)
    if n != 1: bad.append(f"{f}: anchor count {n}: {old[:60]!r}")
for p in ("src/search/tmfit.hpp", "tests/tmfit_tests.cpp"):
    if (root / p).exists(): bad.append(f"{p} already exists")
if bad:
    print("ANCHOR CHECK FAILED, nothing written:\n" + "\n".join(bad)); sys.exit(1)
for f, old, new in E:
    texts[f] = texts[f].replace(old, new, 1)
for f, t in texts.items(): (root / f).write_text(t)
(root / "src/search").mkdir(exist_ok=True)
(root / "src/search/tmfit.hpp").write_text(hdr)
(root / "tests/tmfit_tests.cpp").write_text(tst)
print(f"ported: {len(E)} edits in {len(texts)} files + 2 new files")
