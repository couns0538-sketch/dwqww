"""R5D diagnosis 3 (scratch only): watch every node of the mating tree. For a watched key the driver gives the
side that wins (+1: side to move mates, -1: side to move is mated) and the plies needed; a store that contradicts it
at that depth or more is logged with worker, iteration, ply, depth, window, bound and path."""
from pathlib import Path

root = Path("F:/opus_scratch/r5/r5d/diag_src")
search_cpp = root / "src/search.cpp"
s = search_cpp.read_bytes().decode()
old = "std::mutex mutex; std::string stores; }\n"
assert s.count(old) == 1
s = s.replace(old, "std::mutex mutex; std::string stores; std::uint64_t keys[16]; int sign[16]; int need[16]; "
                   "const char* name[16]; int count = 0; std::uint64_t seq = 0; }\n")
search_cpp.write_bytes(s.encode())

ab = root / "src/search/alphabeta.inc"
a = ab.read_bytes().decode()
anchor = '''    if (r5d_diag::on && board.key() == r5d_diag::key && depth >= 3 && best_score < beta + 100000 &&'''
assert a.count(anchor) == 1
a = a.replace(anchor, '''    for (int r5d_i = 0; r5d_diag::on && r5d_i < r5d_diag::count; ++r5d_i) {
        if (board.key() != r5d_diag::keys[r5d_i] || depth < r5d_diag::need[r5d_i]) continue;
        const bool wrong = r5d_diag::sign[r5d_i] > 0
            ? (best_score < MateInMaxPly && (bound == BoundUpper || bound == BoundExact))
            : (best_score > -MateInMaxPly && (bound == BoundLower || bound == BoundExact));
        if (!wrong) continue;
        char r5d_buf[320];
        const std::lock_guard<std::mutex> lock(r5d_diag::mutex);
        std::snprintf(r5d_buf, sizeof r5d_buf, "  BAD#%llu %s worker %d iter %d ply %d depth %d window %d,%d best %d move %s bound %d cut %d excl %d path",
                      static_cast<unsigned long long>(++r5d_diag::seq), r5d_diag::name[r5d_i], id_, root_depth_, ply, depth,
                      alpha, beta, best_score, Board::move_to_uci(best_move).c_str(), static_cast<int>(bound),
                      cut_node ? 1 : 0, excluded.is_none() ? 0 : 1);
        std::string line = r5d_buf;
        for (int k = ply; k >= 1; --k) line += " " + Board::move_to_uci((ss - k)->current_move);
        r5d_diag::stores += line + "\\n";
    }
    if (false && r5d_diag::on && board.key() == r5d_diag::key && depth >= 3 && best_score < beta + 100000 &&''')
ab.write_bytes(a.encode())
print("instrumented 3")
