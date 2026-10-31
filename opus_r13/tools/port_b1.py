#!/usr/bin/env python3
"""port_b1.py - R13 P1 item 1: the rest of the B1 bundle port onto the lock tree (run once, on the scratch repo).

Precondition (done by hand before this script, see opus_r13/p1/b1/README.md):
  fresh lock copy (fresh_lock.sh) + `patch -p1 -F0` of A1 a8b63aae (HistRework) and C6 2cb0babd (Board cuckoo table)
  src/include hunks + include/forge/correction_plus.hpp copied from forge-bundle-int b7c17722 (unchanged; this script
  only drops its forge/history.hpp include, which the lock tree does not have).
This script adds, as in forge-bundle-int b7c17722 (BUNDLES.md preset B1 = CorrHistPlus 1, HistRework 2, CuckooRep true,
TtPruneV2 true): CorrHistPlus (Opus C2: options, tunables, the cold twins of corrected_eval / update_correction, incl. the
R3 HistRework x CorrHistPlus combination), the CuckooRep search instance (Opus C6 147395c4 + 4d14f3cf: a template
instance instead of R3's macro instances; same wrappers), TtPruneV2 (FB2-J3: RFP worsening, cut-node IIR, TT-move
pruning rules; per-search snapshot like bundle-int's fb2_), UCI CorrHistPlus / CuckooRep / TtPruneV2 / BundlePreset (OFF, B1).
Every anchor must match exactly once (asserted). Files are read and written as LF bytes.
usage: python -I -B port_b1.py <scratch repo> <corrplus body file>
"""
import re
import sys

root, body_file = sys.argv[1], sys.argv[2]


def load(rel):
    with open(f'{root}/{rel}', 'rb') as fh:
        return fh.read().decode()


def save(rel, text):
    assert '\r' not in text
    with open(f'{root}/{rel}', 'wb') as fh:
        fh.write(text.encode())


def rep(text, old, new, count=1):
    n = text.count(old)
    assert n == count, f'anchor found {n}x (want {count}): {old[:90]!r}'
    return text.replace(old, new)


# ---- include/forge/correction_plus.hpp: drop the R3-only include ----
cp = load('include/forge/correction_plus.hpp')
cp = rep(cp, '#include "forge/history.hpp"\n',
         '// R13 lock port: included from forge/search.hpp after CorrectionSize / CorrectionGrain / CorrectionLimit\n'
         '// (the R3 stack has them in forge/history.hpp).\n')
save('include/forge/correction_plus.hpp', cp)

# ---- include/forge/search.hpp ----
h = load('include/forge/search.hpp')
h = rep(h, 'using CorrectionHistory = std::array<std::array<std::int32_t, CorrectionSize>, 2>;\n',
        'using CorrectionHistory = std::array<std::array<std::int32_t, CorrectionSize>, 2>;\n'
        '} // namespace forge\n'
        '\n'
        '// CorrHistPlus (R13 B1 port of Opus C2 as in forge-bundle-int b7c17722): forge/correction_plus.hpp uses\n'
        '// CorrectionSize / CorrectionGrain / CorrectionLimit above, so it is included here.\n'
        '#include "forge/correction_plus.hpp"\n'
        '\n'
        'namespace forge {\n'
        '\n'
        '// Runtime search options of the B1 bundle (R13 port of forge-bundle-int b7c17722). All default OFF; with all\n'
        '// of them OFF the search is the AL1 s198 search. Written only while no search runs (the UCI loop stops it first).\n'
        'namespace options {\n'
        '// UCI CorrHistPlus (spin 0-7, default 0): extra correction-history keys, a bitmask of\n'
        '// forge::corrplus::{Continuation = 1, MinorPiece = 2, NonPawn = 4} (forge/correction_plus.hpp).\n'
        'extern std::uint8_t corr_hist_plus;\n'
        '// UCI CuckooRep (check, default false): upcoming-repetition draw bound in search (Board::upcoming_repetition).\n'
        'extern bool cuckoo_rep;\n'
        '// UCI TtPruneV2 (check, default false): FB2-J3 TT-move pruning rules; each search reads it once (tt_prune_v2_).\n'
        'extern bool tt_prune_v2;\n'
        '} // namespace options\n')
h = rep(h, 'extern int FailLowContinuationBonus; // x0.01 of the history bonus given to the parent move on fail low (0 = off)\n',
        'extern int FailLowContinuationBonus; // x0.01 of the history bonus given to the parent move on fail low (0 = off)\n'
        '// CorrHistPlus (UCI option, default 0 = off): read weights of the extra correction keys (x0.01).\n'
        'extern int CorrContWeight;        // bit 1: continuation correction (previous two moves)\n'
        'extern int CorrMinorWeight;       // bit 2: minor-piece correction\n'
        'extern int CorrNonPawnWeight;     // bit 4: each side\'s non-pawn correction\n')
h = rep(h, '    std::array<hist_rework::LesserThreats, MaxPly + 8> threat_maps_{};\n',
        '    std::array<hist_rework::LesserThreats, MaxPly + 8> threat_maps_{};\n'
        '    // CorrHistPlus tables (forge/correction_plus.hpp), owned by this worker: null until the option is on and the\n'
        '    // first update allocates them; freed by Worker::clear(). TtPruneV2: this search\'s snapshot of the option.\n'
        '    std::unique_ptr<corrplus::Tables> correction_plus_;\n'
        '    bool tt_prune_v2_ = false;\n')
h = rep(h, '    int search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);\n'
           '    int qsearch(Board& board, SearchStack* ss, int alpha, int beta);\n',
        '    // Two search instances: Cuckoo = false is the lock search; Cuckoo = true is the UCI CuckooRep instance, whose\n'
        '    // child calls go through the upcoming-repetition bound (search_cuckoo / qsearch_cuckoo), as the R3 stack\'s\n'
        '    // CuckooRep instances do. search_child / qsearch_child are the child calls of an instance.\n'
        '    template <bool Cuckoo> int search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);\n'
        '    template <bool Cuckoo> int qsearch(Board& board, SearchStack* ss, int alpha, int beta);\n'
        '    template <bool Cuckoo> int search_child(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);\n'
        '    template <bool Cuckoo> int qsearch_child(Board& board, SearchStack* ss, int alpha, int beta);\n'
        '    int search_cuckoo(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);\n'
        '    int qsearch_cuckoo(Board& board, SearchStack* ss, int alpha, int beta);\n')
h = rep(h, '    void update_correction(const Board& board, int depth, int best_score, int static_eval);\n',
        '    void update_correction(const Board& board, int depth, int best_score, int static_eval);\n'
        '    // CorrHistPlus (src/search.cpp). corrected_eval and update_correction jump to their cold twins only when\n'
        '    // forge::options::corr_hist_plus != 0; the helpers are always inlined so that corrected_eval_plus stays a leaf.\n'
        '    [[gnu::cold]] [[nodiscard]] int corrected_eval_plus(const Board& board, int raw_eval) const;\n'
        '    [[gnu::cold]] void update_correction_plus(const Board& board, int depth, int best_score, int static_eval);\n'
        '    [[gnu::always_inline]] [[nodiscard]] inline int correction_plus(const Board& board) const;\n'
        '    [[gnu::always_inline]] [[nodiscard]] inline const SearchStack* correction_frame(const Board& board) const;\n'
        '    [[gnu::always_inline]] [[nodiscard]] inline std::size_t continuation_correction_index(const Board& board) const;\n')
save('include/forge/search.hpp', h)

# ---- src/search.cpp ----
s = load('src/search.cpp')
s = rep(s, '#include <limits>\n#include <optional>\n', '#include <limits>\n#include <new>\n#include <optional>\n')
s = rep(s, '} // namespace search_options\n',
        '} // namespace search_options\n'
        '\n'
        '// B1 bundle options (R13 port of forge-bundle-int b7c17722; forge/search.hpp), all OFF.\n'
        'namespace options {\n'
        'std::uint8_t corr_hist_plus = 0;\n'
        'bool cuckoo_rep = false;\n'
        'bool tt_prune_v2 = false;\n'
        '} // namespace options\n')
s = rep(s, 'int FailLowContinuationBonus = 0;\n',
        'int FailLowContinuationBonus = 0;\nint CorrContWeight = 100;\nint CorrMinorWeight = 100;\nint CorrNonPawnWeight = 100;\n')
s = rep(s, '        {"CaptureFutilityDepth", &CaptureFutilityDepth, 0, 15},  {"FailLowContinuationBonus", &FailLowContinuationBonus, 0, 300},\n',
        '        {"CaptureFutilityDepth", &CaptureFutilityDepth, 0, 15},  {"FailLowContinuationBonus", &FailLowContinuationBonus, 0, 300},\n'
        '        {"CorrContWeight", &CorrContWeight, 0, 300},          {"CorrMinorWeight", &CorrMinorWeight, 0, 300},\n'
        '        {"CorrNonPawnWeight", &CorrNonPawnWeight, 0, 300},\n')
s = rep(s, '[[nodiscard]] std::uint64_t material_key(const Board& board) {\n',
        '// Always inlined: it also has a call site in the cold CorrHistPlus path.\n'
        '[[gnu::always_inline]] [[nodiscard]] inline std::uint64_t material_key(const Board& board) {\n')
s = rep(s, '    *material_correction_ = CorrectionHistory{};\n',
        '    *material_correction_ = CorrectionHistory{};\n'
        '    correction_plus_.reset();  // CorrHistPlus tables, reallocated (zeroed) by the next update\n')
s = rep(s, 'int Worker::corrected_eval(const Board& board, int raw_eval) const {\n',
        'int Worker::corrected_eval(const Board& board, int raw_eval) const {\n'
        '    // CorrHistPlus (default 0 = off): one predictable branch; the cold path\n'
        '    // computes this correction plus the extra keys (corrected_eval_plus below).\n'
        '    if (options::corr_hist_plus != 0) [[unlikely]] return corrected_eval_plus(board, raw_eval);\n')
s = rep(s, 'void Worker::update_correction(const Board& board, int depth, int best_score, int static_eval) {\n',
        'void Worker::update_correction(const Board& board, int depth, int best_score, int static_eval) {\n'
        '    // CorrHistPlus (default 0 = off): one predictable branch; the cold path\n'
        '    // performs this update plus the extra keys (update_correction_plus below).\n'
        '    if (options::corr_hist_plus != 0) [[unlikely]] return update_correction_plus(board, depth, best_score, static_eval);\n')
body = open(body_file, 'rb').read().decode().replace('\r\n', '\n')
anchor = '        entry = hist_rework::gravity(entry, diff * weight / 256, CorrectionLimit);\n    }\n}\n'
s = rep(s, anchor, anchor + '\n// ---- CorrHistPlus (R13 B1 port: forge-bundle-int b7c17722 src/search/correction_plus.inc, unchanged) ----\n'
        + body.rstrip('\n') + '\n// ---- end CorrHistPlus ----\n')
# CuckooRep: template instances + wrappers (before qsearch)
cuckoo = (
    '// CuckooRep (R13 B1 port of Opus C6 as in forge-bundle-int b7c17722 src/search/cuckoo.inc): the child calls of the\n'
    '// CuckooRep instance (search<true> / qsearch<true>) go through these upcoming-repetition draw bounds; the lock\n'
    '// instance (search<false> / qsearch<false>) calls itself. A repetition needs >= 3 reversible plies (may_repeat).\n'
    'namespace {\n'
    '[[nodiscard]] inline bool may_repeat(const Board& board) { return board.halfmove_clock() >= 3; }\n'
    '} // namespace\n'
    '\n'
    'template <bool Cuckoo>\n'
    'inline int Worker::search_child(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {\n'
    '    if constexpr (Cuckoo) return search_cuckoo(board, ss, depth, alpha, beta, cut_node);\n'
    '    else return search<false>(board, ss, depth, alpha, beta, cut_node);\n'
    '}\n'
    '\n'
    'template <bool Cuckoo>\n'
    'inline int Worker::qsearch_child(Board& board, SearchStack* ss, int alpha, int beta) {\n'
    '    if constexpr (Cuckoo) return qsearch_cuckoo(board, ss, alpha, beta);\n'
    '    else return qsearch<false>(board, ss, alpha, beta);\n'
    '}\n'
    '\n'
    'int Worker::search_cuckoo(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {\n'
    '    constexpr int DrawScore = 0;\n'
    '    if (depth > 0 && alpha < DrawScore && ss->ply != 0 && ss->excluded_move.is_none() && may_repeat(board) &&\n'
    '        board.upcoming_repetition(root_history_index_)) {\n'
    '        if (beta <= DrawScore) return DrawScore;\n'
    '        return std::max(search<true>(board, ss, depth, DrawScore, beta, cut_node), DrawScore);\n'
    '    }\n'
    '    return search<true>(board, ss, depth, alpha, beta, cut_node);\n'
    '}\n'
    '\n'
    'int Worker::qsearch_cuckoo(Board& board, SearchStack* ss, int alpha, int beta) {\n'
    '    constexpr int DrawScore = 0;\n'
    '    if (alpha < DrawScore && may_repeat(board) && board.upcoming_repetition(root_history_index_)) {\n'
    '        if (beta <= DrawScore) return DrawScore;\n'
    '        return std::max(qsearch<true>(board, ss, DrawScore, beta), DrawScore);\n'
    '    }\n'
    '    return qsearch<true>(board, ss, alpha, beta);\n'
    '}\n'
    '\n')
qdef = 'int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {\n'
s = rep(s, qdef, cuckoo + 'template <bool Cuckoo>\n' + qdef)
sdef = 'int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {\n'
s = rep(s, sdef, 'template <bool Cuckoo>\n' + sdef)
# child calls, region by region
qa = s.index('template <bool Cuckoo>\n' + qdef)
sa = s.index('template <bool Cuckoo>\n' + sdef)
se = s.index('SearchInfo Worker::search(Board board, const SearchLimits& limits')
assert qa < sa < se
qreg, sreg = s[qa:sa], s[sa:se]
qreg, nq = re.subn(r'(?<![A-Za-z_])qsearch\(board,', 'qsearch_child<Cuckoo>(board,', qreg)
assert nq == 1, nq
sreg, n1 = re.subn(r'(?<![A-Za-z_])qsearch\(board,', 'qsearch_child<Cuckoo>(board,', sreg)
sreg, n2 = re.subn(r'(?<![A-Za-z_])search\(board,', 'search_child<Cuckoo>(board,', sreg)
assert (n1, n2) == (3, 8), (n1, n2)
s = s[:qa] + qreg + sreg + s[se:]
s = rep(s, '            iteration_score = search(board, ss, depth, alpha, beta, false);\n',
        '            iteration_score = options::cuckoo_rep ? search_cuckoo(board, ss, depth, alpha, beta, false)\n'
        '                                                  : search<false>(board, ss, depth, alpha, beta, false);\n')
s = rep(s, '    root_history_index_ = board.history_size() - 1;\n',
        '    root_history_index_ = board.history_size() - 1;\n'
        '    tt_prune_v2_ = options::tt_prune_v2;  // FB2 TtPruneV2: one snapshot per search (bundle-int fb2_)\n')
# TtPruneV2 (FB2-J3 as in forge-bundle-int alphabeta.inc)
s = rep(s, '        // Reverse futility pruning.\n'
           '        if (depth <= tune::RfpDepth && eval - (tune::RfpMargin * depth - tune::RfpImproving * improving) >= beta &&\n'
           '            eval < MateInMaxPly) {\n',
        '        // Reverse futility pruning.\n'
        '        // FB2 TtPruneV2: the opponent\'s static eval fell on their move (opponent worsening): a third of a\n'
        '        // margin step cheaper fail high. 0 with the option off, so the condition is the AL1 s198 one.\n'
        '        const int rfp_worsening = tt_prune_v2_ && (ss - 1)->static_eval != ValueNone &&\n'
        '                                          ss->static_eval + (ss - 1)->static_eval > 2\n'
        '                                      ? tune::RfpMargin / 3 : 0;\n'
        '        if (depth <= tune::RfpDepth &&\n'
        '            eval - (tune::RfpMargin * depth - tune::RfpImproving * improving - rfp_worsening) >= beta &&\n'
        '            eval < MateInMaxPly) {\n')
s = rep(s, '    if (!in_check && depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;\n',
        '    if (!in_check && depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;\n'
        '    // FB2 TtPruneV2: a cut node whose TT move failed low before (upper bound) is unlikely to cut: reduce it too.\n'
        '    // (Exclusive with the IIR above: that one needs no TT move, this one a TT move.)\n'
        '    else if (tt_prune_v2_ && !in_check && depth >= tune::IirDepth + 2 && cut_node && !tt_move.is_none() &&\n'
        '             tt_bound == BoundUpper && !ss->tt_pv) --depth;\n')
s = rep(s, '            const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));\n'
           '            if (quiet && !gives_check) {\n'
           '                if (!in_check && lmr_depth <= tune::FutilityDepth &&\n'
           '                    ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth <= alpha) {\n'
           '                    skip_quiets = true;\n'
           '                    continue;\n'
           '                }\n'
           '                if (lmr_depth <= tune::HistoryPruneDepth && history < -tune::HistoryPruneMultiplier * depth) continue;\n'
           '                if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) continue;\n'
           '            } else {\n',
        '            const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));\n'
        '            // FB2 TtPruneV2: the TT move is never pruned by futility / history / SEE (it carried a bound before);\n'
        '            // quiet futility needs a wider margin when improving; history pruning starts at 3/4 of the threshold when\n'
        '            // not improving.\n'
        '            const bool prunable = !tt_prune_v2_ || move != tt_move;\n'
        '            const int futility_improving = tt_prune_v2_ && improving ? tune::FutilityBase / 2 : 0;\n'
        '            const int history_prune_threshold = tt_prune_v2_ && !improving\n'
        '                                                    ? -tune::HistoryPruneMultiplier * depth * 3 / 4\n'
        '                                                    : -tune::HistoryPruneMultiplier * depth;\n'
        '            if (quiet && !gives_check && prunable) {\n'
        '                if (!in_check && lmr_depth <= tune::FutilityDepth &&\n'
        '                    ss->static_eval + tune::FutilityBase + futility_improving + tune::FutilityMultiplier * lmr_depth <= alpha) {\n'
        '                    skip_quiets = true;\n'
        '                    continue;\n'
        '                }\n'
        '                if (lmr_depth <= tune::HistoryPruneDepth && history < history_prune_threshold) continue;\n'
        '                if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) continue;\n'
        '            } else if (prunable) {\n')
save('src/search.cpp', s)

# ---- src/uci.cpp ----
u = load('src/uci.cpp')
u = rep(u, '            std::cout << "option name HistRework type spin default 0 min 0 max " << forge::hist_rework::MaxLevel << "\\n";\n',
        '            std::cout << "option name HistRework type spin default 0 min 0 max " << forge::hist_rework::MaxLevel << "\\n";\n'
        '            // B1 bundle options (R13 port of forge-bundle-int b7c17722); all default OFF.\n'
        '            std::cout << "option name CorrHistPlus type spin default 0 min 0 max 7\\n"\n'
        '                         "option name CuckooRep type check default false\\n"\n'
        '                         "option name TtPruneV2 type check default false\\n"\n'
        '                         "option name BundlePreset type combo default OFF var OFF var B1\\n";\n')
u = rep(u, '            } else if (name == "UseNNUE") {\n',
        '            } else if (name == "CorrHistPlus") {\n'
        '                int value = 0;\n'
        '                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);\n'
        '                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {\n'
        '                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
        '                    std::cout << "info string invalid value for option " << name << std::endl;\n'
        '                } else {\n'
        '                    forge::options::corr_hist_plus = static_cast<std::uint8_t>(std::clamp(value, 0, 7));\n'
        '                }\n'
        '            } else if (name == "CuckooRep" || name == "TtPruneV2") {\n'
        '                if (value_text != "true" && value_text != "false") {\n'
        '                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
        '                    std::cout << "info string invalid value for option " << name << std::endl;\n'
        '                } else if (name == "CuckooRep") {\n'
        '                    forge::options::cuckoo_rep = value_text == "true";\n'
        '                } else {\n'
        '                    forge::options::tt_prune_v2 = value_text == "true";\n'
        '                }\n'
        '            } else if (name == "BundlePreset") {\n'
        '                // forge-bundle-int presets; OFF and B1 are ported (B2-B4 need CorrHistV2 / LmrTableV2).\n'
        '                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
        '                if (value_text != "OFF" && value_text != "B1") {\n'
        '                    std::cout << "info string invalid value for option " << name << std::endl;\n'
        '                } else {\n'
        '                    const bool b1 = value_text == "B1";\n'
        '                    forge::options::corr_hist_plus = static_cast<std::uint8_t>(b1 ? 1 : 0);\n'
        '                    forge::search_options::hist_rework = b1 ? 2 : 0;\n'
        '                    forge::options::cuckoo_rep = b1;\n'
        '                    forge::options::tt_prune_v2 = b1;\n'
        '                    std::cout << "info string BundlePreset " << value_text << ": CorrHistPlus=" << (b1 ? 1 : 0)\n'
        '                              << " HistRework=" << (b1 ? 2 : 0) << " CuckooRep=" << (b1 ? "true" : "false")\n'
        '                              << " CorrHistV2=false LmrTableV2=false TtPruneV2=" << (b1 ? "true" : "false") << std::endl;\n'
        '                }\n'
        '            } else if (name == "UseNNUE") {\n')
save('src/uci.cpp', u)
print('port_b1: all anchors applied')
