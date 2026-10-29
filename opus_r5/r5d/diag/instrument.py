"""R5D diagnosis only (scratch copy, never committed): log the main thread's TT probe and result at one node."""
from pathlib import Path

root = Path("F:/opus_scratch/r5/r5d/diag_src")
search_cpp = root / "src/search.cpp"
s = search_cpp.read_bytes().decode()
anchor = '#include "forge/uci_output.hpp"\n'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '#include <cstdio>\n#include <string>\nnamespace r5d_diag { std::uint64_t key = 0; std::string log; bool on = false; }\n')
search_cpp.write_bytes(s.encode())

ab = root / "src/search/alphabeta.inc"
a = ab.read_bytes().decode()
probe_anchor = "    ss->tt_pv = pv_node || (tt_hit && tte.pv());\n"
assert a.count(probe_anchor) == 1
a = a.replace(probe_anchor, probe_anchor + '''    const bool r5d_watch = r5d_diag::on && is_main() && board.key() == r5d_diag::key;
    if (r5d_watch) {
        char r5d_buf[256];
        std::snprintf(r5d_buf, sizeof r5d_buf, "  [iter %d ply %d depth %d window %d,%d] tt_hit %d tt_score %d bound %d tt_depth %d\\n",
                      root_depth_, ply, depth, alpha, beta, tt_hit ? 1 : 0, tt_score, static_cast<int>(tt_bound), tt_depth);
        r5d_diag::log += r5d_buf;
    }
''')
cut_anchor = '''         (tt_bound == BoundUpper && tt_score <= alpha))) {
        return tt_score;'''
assert a.count(cut_anchor) == 1
a = a.replace(cut_anchor, '''         (tt_bound == BoundUpper && tt_score <= alpha))) {
        if (r5d_watch) r5d_diag::log += "    -> TT cutoff\\n";
        return tt_score;''')
end_anchor = '''    return best_score;
}
'''
assert a.count(end_anchor) == 1
a = a.replace(end_anchor, '''    if (r5d_watch) {
        char r5d_buf[160];
        std::snprintf(r5d_buf, sizeof r5d_buf, "    -> searched: best %d move %s bound %d\\n", best_score,
                      Board::move_to_uci(best_move).c_str(), static_cast<int>(bound));
        r5d_diag::log += r5d_buf;
    }
    return best_score;
}
''')
ab.write_bytes(a.encode())
print("instrumented")
