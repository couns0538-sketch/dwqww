## 2026-11-16T23:48:55Z (from `date -u`)
seat 21. **Threads 1 in every run.** PC build r15 under PC20 unless stated.

# The measurement the coordinator asked for: the position-155 class

**21-F21: 0 hit in 50 positions, on an EXACT metric.**
50 bare-king endings (R or Q vs K) with the halfmove counter at **95–99**, so the fifty-move draw is
only **1–5 half-moves** away. That window is what makes the metric exact rather than a play-out
opinion: a minimax over exactly those plies decides each move's true result, because a move that
fails to mate inside the window IS a draw and no deeper search can change that.

- positions where the side to move had a move that **saves the draw**: **50 of 50**
- **HITS (engine walked into a mate it could have avoided): 0**
- engine answer identical at `go depth 16` and `go nodes 20000`: 50 of 50

**21-C17: position 155 is not a member.** White (bare king vs R+B+N, counter 18) is mated in 16–24
plies by every one of its four legal moves, where the draw needs 82. All lose, so no alternative is
better. Seat 03's S-F16 self-contradiction is a SCORING artefact, not a lost draw.

**21-F20 (method, worth broadcasting):** a single engine-vs-engine play-out manufactures hits.
`8/8/8/8/8/1r1k2K1/8/8 b - - 92 60` — `d3e3` read as a WIN 3/3 by play-out, yet exhaustive minimax
shows **no move forces mate** in the 7 plies available, so every move draws. My own first scan
reported an apparent hit on exactly this; and an earlier version of my hit test had its polarity
INVERTED (it flagged the engine for choosing a drawing move). Both are recorded in the report.

**`DESIGN_drawn_root.md`**: the fix direction as a design note, not a patch — search the root, then
take the draw score unless the search finds a win for the side to move. One paragraph of trade-off:
it keeps the PC build's mate-at-a-drawn-root (21-C16) and removes its drawn-as-won score (21-F19),
at the cost of searching a root the base tree answered in zero nodes.

**Also live: 21-F19** — the PC build reports a drawn root with no mate as a win (`cp 199–298`) where
the base build says `cp 0`. Combined with 21-F21 this is a **scoring** problem, not a lost-draw
problem: nothing I measured shows the engine throwing a drawn game.

**Next**: extend the exact scan beyond the 1–5 half-move window (counter 85–94) with a bounded solver,
and run the design note's acceptance test as a spec so the owner can apply it directly.
