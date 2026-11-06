"""mk_counters.py - add the box-test counters (FORGE_SPEC_COUNTERS, test build only) to a copy of a port's gate tree.

Own code, 2026-11-06 (leftover checks). usage: python -I -B mk_counters.py <cnl|tcn|ntc> <tree dir (copy of *_gate)>
Counters are plain globals (valid at Threads 1), incremented by search and never read by it; one
'info string spec_counters ...' line at process exit. Every anchor must match exactly the expected number of times.
"""
import sys
from pathlib import Path

HEAD = """#ifndef FORGE_SPEC_COUNTERS
#define FORGE_SPEC_COUNTERS 0
#endif
#if FORGE_SPEC_COUNTERS
// Box-test counters (test build only, never in a gate exe): search increments them and never reads them. Plain
// globals: valid for Threads 1. One line at process exit = the totals of everything the process searched.
namespace spec_counters {
"""

BLOCK = {
    'cnl': HEAD + """std::uint64_t lmr_all = 0, lmr_cut_nott = 0, applied = 0, clamped_all = 0, clamped_cut_nott = 0, research_all = 0,
              research_cut_nott = 0, boosts_all = 0, boosts_cut_nott = 0;
struct Printer {
    ~Printer() {
        std::cout << "info string spec_counters lmr_all " << lmr_all << " lmr_cut_nott " << lmr_cut_nott << " applied "
                  << applied << " clamped_all " << clamped_all << " clamped_cut_nott " << clamped_cut_nott
                  << " research_all " << research_all << " research_cut_nott " << research_cut_nott << " boosts_all "
                  << boosts_all << " boosts_cut_nott " << boosts_cut_nott << std::endl;
    }
} printer;
} // namespace spec_counters
#endif
""",
    'tcn': HEAD + """std::uint64_t eligible[4] = {}, cut[4] = {}, refused_high_noncut[4] = {}, refused_low_cut[4] = {};
struct Printer {
    ~Printer() {
        static const char* names[4] = {"d1-2", "d3-4", "d5-6", "d7+"};
        std::cout << "info string spec_counters";
        for (int b = 0; b < 4; ++b)
            std::cout << " " << names[b] << " eligible " << eligible[b] << " cut " << cut[b] << " refused_high_noncut "
                      << refused_high_noncut[b] << " refused_low_cut " << refused_low_cut[b];
        std::cout << std::endl;
    }
} printer;
} // namespace spec_counters
#endif
""",
    'ntc': HEAD + """std::uint64_t eligible = 0, blocked = 0, tt_capture_victim[8] = {}, blocked_victim[8] = {}, null_tries = 0,
              null_cutoffs = 0;
struct Printer {
    ~Printer() {
        std::cout << "info string spec_counters nmp_eligible " << eligible << " blocked " << blocked;
        for (int t = 1; t <= 5; ++t) std::cout << " ttcap_v" << t << " " << tt_capture_victim[t];
        for (int t = 1; t <= 5; ++t) std::cout << " blocked_v" << t << " " << blocked_victim[t];
        std::cout << " null_tries " << null_tries << " null_cutoffs " << null_cutoffs << std::endl;
    }
} printer;
} // namespace spec_counters
#define SPEC_INC(x) (++spec_counters::x)
#else
#define SPEC_INC(x) ((void)0)
#endif
""",
}

# (anchor, text, 'after' | 'before', expected count)
SITES = {
    'cnl': [
        ("            const int reduced_depth = std::clamp(new_depth - r, 1, new_depth);\n", """#if FORGE_SPEC_COUNTERS
            const bool spec_cnt = cut_node && tt_move.is_none();
            ++spec_counters::lmr_all;
            if (new_depth - r < 1) ++spec_counters::clamped_all;
            if (spec_cnt) {
                ++spec_counters::lmr_cut_nott;
                if (tune::CutNoTtLmr > 0) ++spec_counters::applied;
                if (new_depth - r < 1) ++spec_counters::clamped_cut_nott;
            }
#endif
""", 'after', 1),
        ("            full_depth_needed = score > alpha && reduced_depth < new_depth;\n", """#if FORGE_SPEC_COUNTERS
            if (full_depth_needed) { ++spec_counters::research_all; if (spec_cnt) ++spec_counters::research_cut_nott; }
#endif
""", 'after', 1),
        ("                update_continuation(ss, moved, move.to, history_bonus(depth) / 2);\n", """#if FORGE_SPEC_COUNTERS
                ++spec_counters::boosts_all;
                if (spec_cnt) ++spec_counters::boosts_cut_nott;
#endif
""", 'before', 1),
    ],
    'tcn': [
        ("A refused cutoff searches the node.\n", """#if FORGE_SPEC_COUNTERS
    if (!pv_node && excluded.is_none() && tt_hit && tt_score != ValueNone && tt_depth >= depth &&
        board.halfmove_clock() < 90 &&
        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||
         (tt_bound == BoundUpper && tt_score <= alpha))) {
        const int spec_b = depth <= 2 ? 0 : depth <= 4 ? 1 : depth <= 6 ? 2 : 3;
        const bool spec_ok = tune::TtCutNodeDepth == 0 || depth > tune::TtCutNodeDepth ||
                             (tune::TtCutNodeForm == 2 ? ((tt_score >= beta) == cut_node) : (tt_score < beta || cut_node));
        ++spec_counters::eligible[spec_b];
        if (spec_ok) ++spec_counters::cut[spec_b];
        else if (tt_score >= beta) ++spec_counters::refused_high_noncut[spec_b];
        else ++spec_counters::refused_low_cut[spec_b];
    }
#endif
""", 'after', 1),
    ],
    'ntc': [
        ("            return tune::NmpTtCaptureSee > 0 && board.see_ge(tt_move, tune::NmpTtCaptureSee);\n        };\n", """#if FORGE_SPEC_COUNTERS
        if (depth >= tune::NullMoveMinDepth && eval >= beta && ss->static_eval >= beta - 24 * depth + 180 &&
            ss->null_move_allowed && !(ss - 1)->current_move.is_none() &&
            board.has_non_pawn_material(board.side_to_move()) &&
            !(tt_hit && tt_bound == BoundUpper && tt_score < beta)) {
            ++spec_counters::eligible;
            const bool spec_real = tt_capture && board.is_pseudo_legal(tt_move);
            const int spec_vt = spec_real ? static_cast<int>(piece_type(board.captured_piece(tt_move))) & 7 : 0;
            if (spec_real) ++spec_counters::tt_capture_victim[spec_vt];
            if (nmp_tt_capture_block()) { ++spec_counters::blocked; ++spec_counters::blocked_victim[spec_vt]; }
        }
#endif
""", 'after', 1),
        ("++null_tries_;", "++null_tries_; SPEC_INC(null_tries);", 'replace', None),
        ("++null_cutoffs_;", "++null_cutoffs_; SPEC_INC(null_cutoffs);", 'replace', None),
    ],
}


def main() -> int:
    port, tree = sys.argv[1], Path(sys.argv[2])
    f = tree / 'src' / 'search.cpp'
    s = f.read_bytes().decode('utf-8')
    if '\r' in s:
        print('CR bytes in', f); return 2
    anchor = '} // namespace tune\n'
    if s.count(anchor) != 1:
        print('anchor count', s.count(anchor), repr(anchor)); return 2
    s = s.replace(anchor, anchor + '\n' + BLOCK[port], 1)
    for a, text, how, n in SITES[port]:
        c = s.count(a)
        if (n is not None and c != n) or c == 0:
            print('anchor count', c, 'expected', n, repr(a[:70])); return 2
        if how == 'after':
            s = s.replace(a, a + text, 1)
        elif how == 'before':
            s = s.replace(a, text + a, 1)
        else:
            s = s.replace(a, text)
        print(f'{port}: {how} x{c}: {a.strip()[:70]}')
    f.write_bytes(s.encode('utf-8'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
