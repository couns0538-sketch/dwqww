#!/usr/bin/env python3
"""make_variant.py : builds the EXPERIMENT variant with the fifty-move test REMOVED from is_draw.

This is the A/B counterpart to the instrumentation patch. It changes exactly one thing:

    is_draw:  if (board.halfmove_clock() >= 100) { return !board.in_check() || board.has_legal_move(); }
    becomes: the whole branch is skipped when FORGE_CLOCK99_NORULE50 is defined.

Nothing else changes. The patch is emitted as a real `diff -u` of the single file, stays EXPERIMENT text, and is
never applied to the repository tree. Honesty pins are re-checked on the variant before any A/B number is used:
if bench 11/13/16 or perft 5 moved, the variant is not a controlled change and gets no numbers.
"""
import pathlib
import shutil
import subprocess

SRC = pathlib.Path("/agent/repos/pcsrc/forge-combo29")
WORK = pathlib.Path("/agent/repos/var50")
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
NEW = """bool Worker::is_draw(const Board& board, int ply) const {
    (void)ply;
#ifdef FORGE_CLOCK99_NORULE50
    // EXPERIMENT (swarm seat 25, S-F19): the fifty-move test is REMOVED here to measure the risk of doing
    // exactly that. A claimable draw is not terminality, so it should not short-circuit a node.
#else
    if (board.halfmove_clock() >= 100) {
        // Checkmate on the hundredth half-move still wins; everything else is a draw.
        return !board.in_check() || board.has_legal_move();
    }
#endif"""

if OLD not in text:
    raise SystemExit("is_draw pattern not found")
if text.count(OLD) != 1:
    raise SystemExit("is_draw pattern not unique")
text = text.replace(OLD, NEW)
f.write_text(text)
print("variant instrumented: fifty-move branch in is_draw is now behind FORGE_CLOCK99_NORULE50")

diff = subprocess.run(
    ["diff", "-u", "--label", "a/src/search.cpp", "--label", "b/src/search.cpp",
     str(SRC / "src" / "search.cpp"), str(f)],
    capture_output=True, text=True)
patch = OUTDIR / "FORGE_EXPERIMENT_remove_rule50_from_is_draw.patch.txt"
patch.write_text(diff.stdout)
print(f"wrote {patch}")
