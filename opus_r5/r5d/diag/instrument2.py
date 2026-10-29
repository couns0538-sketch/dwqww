"""R5D diagnosis 2 (scratch only): log every thread's suspicious store at the watched key (non-mate lower bound at
depth >= 3) with worker id, iteration, ply, depth, window and the path from the root."""
from pathlib import Path

root = Path("F:/opus_scratch/r5/r5d/diag_src")
search_cpp = root / "src/search.cpp"
s = search_cpp.read_bytes().decode()
old = "namespace r5d_diag { std::uint64_t key = 0; std::string log; bool on = false; }\n"
assert s.count(old) == 1
s = s.replace(old, "#include <mutex>\nnamespace r5d_diag { std::uint64_t key = 0; std::string log; bool on = false; "
                   "std::mutex mutex; std::string stores; }\n")
search_cpp.write_bytes(s.encode())

ab = root / "src/search/alphabeta.inc"
a = ab.read_bytes().decode()
anchor = '''    if (r5d_watch) {
        char r5d_buf[160];'''
assert a.count(anchor) == 1
a = a.replace(anchor, '''    if (r5d_diag::on && board.key() == r5d_diag::key && depth >= 3 && best_score < beta + 100000 &&
        !is_mate_score(best_score) && bound == BoundLower) {
        char r5d_buf[320];
        std::snprintf(r5d_buf, sizeof r5d_buf, "  STORE worker %d iter %d ply %d depth %d window %d,%d best %d move %s cut_node %d excluded %d path",
                      id_, root_depth_, ply, depth, alpha, beta, best_score, Board::move_to_uci(best_move).c_str(),
                      cut_node ? 1 : 0, excluded.is_none() ? 0 : 1);
        std::string line = r5d_buf;
        for (int k = ply; k >= 1; --k) line += " " + Board::move_to_uci((ss - k)->current_move);
        const std::lock_guard<std::mutex> lock(r5d_diag::mutex);
        r5d_diag::stores += line + "\\n";
    }
    if (r5d_watch) {
        char r5d_buf[160];''')
ab.write_bytes(a.encode())
print("instrumented 2")
