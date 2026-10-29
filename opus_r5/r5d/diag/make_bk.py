"""R5D candidate fix BK (scratch only): mating mode against a bare king - no shallow quiet-move pruning and no LMR at a
node whose side NOT to move has only its king."""
import subprocess
from pathlib import Path

WT = "D:/grok-pc-data/dwqww/.claude/worktrees/opus-r5d-matefix"
root = Path("F:/opus_scratch/r5/r5d/exp_bk")
root.mkdir(parents=True, exist_ok=True)
archive = subprocess.run(["git", "-C", WT, "-c", "core.autocrlf=false", "archive", "HEAD", "src", "include"],
                         check=True, capture_output=True).stdout
subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
p = root / "src/search/alphabeta.inc"
s = p.read_bytes().decode()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


rep("    const bool has_material = board.has_non_pawn_material(board.side_to_move());\n",
    "    const bool has_material = board.has_non_pawn_material(board.side_to_move());\n"
    "    // R5D: against a bare king every quiet move may be the mating one (quiet zugzwang moves such as Re7 in KRK):\n"
    "    // no move-count / futility / history / SEE pruning of quiet moves and no late-move reduction there.\n"
    "    const bool bare_king_opponent = popcount(board.occupied(opposite(board.side_to_move()))) == 1;\n")
rep("        if (!root_node && best_score > -MateInMaxPly && has_material) {\n",
    "        if (!root_node && best_score > -MateInMaxPly && has_material && !bare_king_opponent) {\n")
rep("        if (depth >= 2 && move_count > 1 + (root_node ? 1 : 0) && (quiet || !ss->tt_pv || move_count > 4)) {\n",
    "        if (depth >= 2 && move_count > 1 + (root_node ? 1 : 0) && !bare_king_opponent && (quiet || !ss->tt_pv || move_count > 4)) {\n")
p.write_bytes(s.encode())
print("prepared exp_bk")
