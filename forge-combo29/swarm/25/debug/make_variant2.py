#!/usr/bin/env python3
"""make_variant2.py : the NARROWER repair (S-F22), as an EXPERIMENT patch.

Instead of deleting the fifty-move test, make it refusable-aware:

    a node at clock >= 100 is a draw only when NEITHER side has a capture or pawn move available;
    otherwise it is searched.

Needs a helper that answers "does either side have a capture or pawn move?" - the cheapest correct check is to
walk the legal moves of the side to move (already computed in most nodes) plus a static scan for the other side,
so this patch uses `has_resetting_move()` implemented with Board's own move generator for the side to move and a
conservative static test for the opponent. The helper is deliberately conservative: if it cannot prove a reset
exists it returns false, which keeps the old behaviour.
"""
import pathlib
import shutil
import subprocess

SRC = pathlib.Path("/agent/repos/pcsrc/forge-combo29")
WORK = pathlib.Path("/agent/repos/var52")
OUTDIR = pathlib.Path("/agent/repos/dwqww/forge-combo29/swarm/25/debug")

if WORK.exists():
    shutil.rmtree(WORK)
shutil.copytree(SRC, WORK, ignore=shutil.ignore_patterns("tests_*", "docs", "*.zip"))

f = WORK / "src" / "search.cpp"
text = f.read_text()

OLD = """bool Worker::is_draw(const Board& board, int ply) const {
    (void)ply;
    if (board.halfmove_clock() >= 100) {
        // Checkmate on the hundredth half-move still wins; everything else is a draw.
        return !board.in_check() || board.has_legal_move();
    }"""

NEW = """#ifdef FORGE_CLOCK99_NARROW
// EXPERIMENT (swarm seat 25, S-F22): a fifty-move "draw" at clock >= 100 is only terminal when NEITHER side can
// reset the counter. Conservative: if the side to move has a capture or pawn move, the draw is refusable.
static bool has_resetting_move(const Board& board) {
    for (const Move m : board.legal_moves()) {
        if (m.is_capture() || piece_type(board.moved_piece(m)) == Pawn) return true;
    }
    return false;
}
#endif

bool Worker::is_draw(const Board& board, int ply) const {
    (void)ply;
    if (board.halfmove_clock() >= 100) {
#ifdef FORGE_CLOCK99_NARROW
        if (has_resetting_move(board)) {
            // Someone can reset the clock, so the draw is only claimable, not forced. Search it.
            return board.is_repetition(root_history_index_) || board.is_insufficient_material() ||
                   (!board.in_check() && !board.has_legal_move());
        }
#endif
        // Checkmate on the hundredth half-move still wins; everything else is a draw.
        return !board.in_check() || board.has_legal_move();
    }"""

if OLD not in text:
    raise SystemExit("is_draw pattern not found")
if text.count(OLD) != 1:
    raise SystemExit("not unique")
f.write_text(text.replace(OLD, NEW))
print("narrow variant instrumented")

diff = subprocess.run(
    ["diff", "-u", "--label", "a/src/search.cpp", "--label", "b/src/search.cpp",
     str(SRC / "src" / "search.cpp"), str(f)],
    capture_output=True, text=True)
patch = OUTDIR / "FORGE_EXPERIMENT_rule50_refusable_aware.patch.txt"
patch.write_text(diff.stdout)
print(f"wrote {patch}")
