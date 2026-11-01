#!/usr/bin/env python3
"""port_syzygy.py - R13 P6: port Opus C1's own Syzygy prober (3fd235c8 + aa0b0a83, = opus-r3-stack / forge-bundle-int
final) onto the lock tree (git d4f4312), prober + SyzygyPath / SyzygyProbeDepth / Syzygy50MoveRule only (no
IntendedThreefold, no HardDeadline: one change per gate line).

Files copied unchanged from aa0b0a83 except one include: include/forge/syzygy.hpp (forge/search_types.hpp, an R3-stack
header, -> forge/search.hpp, where the lock keeps SearchLimits / MaxPly / MateInMaxPly), src/syzygy.inc (= search/syzygy.inc),
src/tablebase.inc (= search/tablebase.inc); both are included at the end of src/search.cpp as in R3 (cold code after the search).
Hooks translated from the O3-split files onto the lock's search.cpp / search.hpp / uci.cpp (same statements):
  options syzygy_probe_depth (1) / syzygy_50_move_rule (true); Worker::probe_tablebase declaration; the in-search probe after
  the TT cutoff; score_to_tt / score_from_tt keep TB-band distances while tables are loaded; the two root emits show the TB
  score; Searcher::search prepares the root (move filter); UCI options and handlers.
usage: python -I -B port_syzygy.py <fresh lock scratch repo> <dwqww repo>
"""
import subprocess
import sys

root, repo = sys.argv[1], sys.argv[2]
C1 = 'aa0b0a83'


def show(path):
    return subprocess.run(['git', '-C', repo, '-c', 'core.autocrlf=false', 'show', f'{C1}:{path}'],
                          check=True, capture_output=True).stdout.decode()


def write(rel, text):
    assert '\r' not in text
    open(f'{root}/{rel}', 'wb').write(text.encode())


def edit(rel, pairs):
    p = f'{root}/{rel}'
    s = open(p, 'rb').read().decode()
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, f'{rel}: anchor found {n}x: {old[:90]!r}'
        s = s.replace(old, new)
    open(p, 'wb').write(s.encode())


hpp = show('include/forge/syzygy.hpp')
assert hpp.count('#include "forge/search_types.hpp"\n') == 1
write('include/forge/syzygy.hpp', hpp.replace('#include "forge/search_types.hpp"\n',
                                              '#include "forge/search.hpp"  // R13 lock port: SearchLimits, MaxPly, MateInMaxPly\n'))
write('src/syzygy.inc', show('src/search/syzygy.inc'))
write('src/tablebase.inc', show('src/search/tablebase.inc'))

edit('include/forge/search.hpp', [
    ('struct TTProbe {', '// Syzygy options (R13 P6 port of Opus C1; UCI SyzygyProbeDepth / Syzygy50MoveRule, only active while UCI\n'
     '// SyzygyPath has loaded tables, forge/syzygy.hpp).\nnamespace options {\nextern int syzygy_probe_depth;\n'
     'extern bool syzygy_50_move_rule;\n} // namespace options\n\nstruct TTProbe {'),
    ('    [[nodiscard]] int static_evaluate(const Board& board, SearchStack* ss);\n',
     '    [[nodiscard]] int static_evaluate(const Board& board, SearchStack* ss);\n'
     '    // Syzygy WDL probe inside the search (src/tablebase.inc); only called while tables are loaded. Returns ValueNone\n'
     '    // to search on.\n'
     '    [[gnu::cold]] int probe_tablebase(Board& board, SearchStack* ss, int depth, int alpha, int beta,\n'
     '                                      const TTProbe& tt_probe);\n'),
])
edit('src/search.cpp', [
    ('#include "forge/search.hpp"\n', '#include "forge/search.hpp"\n#include "forge/syzygy.hpp"\n'),
    ('} // namespace tune\n', '} // namespace tune\n\nnamespace options {\nint syzygy_probe_depth = 1;\nbool syzygy_50_move_rule = true;\n} // namespace options\n'),
    ('    if (score >= MateInMaxPly) return score + ply;\n    if (score <= -MateInMaxPly) return score - ply;\n',
     '    // Mate scores, and tablebase scores while tables are loaded (the band just below the mate scores,\n'
     '    // forge/syzygy.hpp), are stored as the distance from the storing node; everything else unchanged.\n'
     '    if (score >= syzygy::TbWinInMaxPly) return score >= MateInMaxPly || syzygy::tb_scores ? score + ply : score;\n'
     '    if (score <= -syzygy::TbWinInMaxPly) return score <= -MateInMaxPly || syzygy::tb_scores ? score - ply : score;\n'),
    ('    if (score >= MateInMaxPly) return score - ply;\n    if (score <= -MateInMaxPly) return score + ply;\n',
     '    if (score >= syzygy::TbWinInMaxPly) return score >= MateInMaxPly || syzygy::tb_scores ? score - ply : score;\n'
     '    if (score <= -syzygy::TbWinInMaxPly) return score <= -MateInMaxPly || syzygy::tb_scores ? score + ply : score;\n'),
    ('        return tt_score;\n    }\n\n    // Static evaluation.\n',
     '        return tt_score;\n    }\n\n'
     '    // Tablebase probe (UCI SyzygyPath; cold path, src/tablebase.inc).\n'
     '    if (syzygy::search_cardinality.load(std::memory_order_relaxed) != 0) [[unlikely]] {\n'
     '        const int tb_score = probe_tablebase(board, ss, depth, alpha, beta, tt_probe);\n'
     '        if (tb_score != ValueNone) return tb_score;\n'
     '    }\n\n    // Static evaluation.\n'),
    ('                emit(depth, result.score, result.pv);\n',
     '                // A tablebase root (UCI SyzygyPath) reports the tablebase result.\n'
     '                emit(depth, syzygy::root_display.load(std::memory_order_relaxed) != 0 ? syzygy::display_score(result.score)\n'
     '                                                                                     : result.score, result.pv);\n'),
    ('        emit(depth, score, result.pv);\n',
     '        emit(depth, syzygy::root_display.load(std::memory_order_relaxed) != 0 ? syzygy::display_score(score) : score,\n'
     '             result.pv);\n'),
])
s = open(f'{root}/src/search.cpp', 'rb').read().decode()
end = '} // namespace forge\n'
assert s.endswith(end) or s.rstrip('\n').endswith('} // namespace forge'), 'search.cpp tail'
s = s.rstrip('\n') + '\n\n// Syzygy tablebases (R13 P6 port of Opus C1; all [[gnu::cold]], placed after the search code).\n' \
    '#include "tablebase.inc"   // search glue: in-search probe, root filter\n#include "syzygy.inc"      // table reader, WDL/DTZ probes, root ranking\n'
open(f'{root}/src/search.cpp', 'wb').write(s.encode())
edit('src/search.cpp', [
    ('    SearchLimits worker_limits = limits;\n    worker_limits.start_time = origin;\n',
     '    SearchLimits worker_limits = limits;\n    worker_limits.start_time = origin;\n'
     '    // Tablebases (UCI SyzygyPath): in-search probing limit, root move filter.\n'
     '    if (syzygy::max_pieces() > 0) [[unlikely]] syzygy::prepare_root(board, worker_limits);\n'),
])
edit('src/uci.cpp', [
    ('#include "forge/search.hpp"\n', '#include "forge/search.hpp"\n#include "forge/syzygy.hpp"\n'),
    ('            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n',
     '            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n'
     '            // Syzygy (R13 P6 port of Opus C1): off while SyzygyPath is empty.\n'
     '            std::cout << "option name SyzygyPath type string default <empty>\\n"\n'
     '                         "option name SyzygyProbeDepth type spin default 1 min 1 max 10\\n"\n'
     '                         "option name Syzygy50MoveRule type check default true\\n";\n'),
    ('            } else if (name == "UseNNUE") {\n',
     '            } else if (name == "SyzygyPath") {\n'
     '                // Folders separated by \';\' (Windows) or \':\' (elsewhere); may contain spaces.\n'
     '                std::string rest;\n'
     '                std::getline(input, rest);\n'
     '                std::string path = value_text + rest;\n'
     '                while (!path.empty() && (path.back() == \' \' || path.back() == \'\\r\')) path.pop_back();\n'
     '                const forge::syzygy::LoadSummary summary = forge::syzygy::load(path);\n'
     '                // Stored tablebase scores are encoded by whether tables are loaded (forge/syzygy.hpp).\n'
     '                searcher.clear_hash();\n'
     '                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
     '                if (path.empty() || path == "<empty>") {\n'
     '                    std::cout << "info string Syzygy tablebases off" << std::endl;\n'
     '                } else {\n'
     '                    std::cout << "info string Syzygy: " << summary.wdl_tables << " WDL and " << summary.dtz_tables\n'
     '                              << " DTZ tables, up to " << summary.max_pieces << " pieces";\n'
     '                    if (summary.rejected > 0) std::cout << ", " << summary.rejected << " invalid files skipped";\n'
     '                    std::cout << std::endl;\n'
     '                }\n'
     '            } else if (name == "SyzygyProbeDepth") {\n'
     '                int value = 0;\n'
     '                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);\n'
     '                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {\n'
     '                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
     '                    std::cout << "info string invalid value for option " << name << std::endl;\n'
     '                } else {\n'
     '                    forge::options::syzygy_probe_depth = std::clamp(value, 1, 10);\n'
     '                }\n'
     '            } else if (name == "Syzygy50MoveRule") {\n'
     '                if (value_text == "true") forge::options::syzygy_50_move_rule = true;\n'
     '                else if (value_text == "false") forge::options::syzygy_50_move_rule = false;\n'
     '                else {\n'
     '                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
     '                    std::cout << "info string invalid value for option " << name << std::endl;\n'
     '                }\n'
     '            } else if (name == "UseNNUE") {\n'),
])
print('port_syzygy: files copied, all hooks and UCI options applied')
