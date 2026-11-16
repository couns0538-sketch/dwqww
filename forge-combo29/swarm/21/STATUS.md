## 2026-11-16T23:16:56Z (from `date -u`)
seat 21. **Threads 1 in every run.** Builds: base 6b98f217 and PC r15 (PC20 unless stated).

# 21-F19 — THE PC BUILD REPORTS A DRAWN ROOT AS A WIN

A drawn root with **no mate available** is scored as won on the PC build, where the base build scores 0:

| build | case | nodes | score |
|---|---|---|---|
| base | K+P vs K, halfmove 100 | 0 | **`cp 0`** |
| **pc** | K+P vs K, halfmove 100 | 6,221 | **`cp 199`** |
| base | quiet threefold root | 0 | **`cp 0`** |
| **pc** | quiet threefold root | 7,734 | **`cp 238`** (and `cp 298` at 100k nodes) |
| both | K v K, KN v K, KB v K | 0 | `cp 0` (correct) |

Cause (code read, `src/search.cpp:2571-2582`): with `FORGE_FIX_ROOT_DRAWN` the root-draw test
shrinks to `is_insufficient_material()` only, and the search does not re-apply the fifty-move or
repetition rule at the ROOT. So the fix that correctly finds a mate at a drawn root (my 21-C16) also
loses the draw score when there is no mate.

**Why it may not matter for matches**: file 6 says the match program ends the game itself at the
third occurrence and the 100th half-move, so a wrong score does not change the result. **Where it
does matter**: self-play and analysis that record the score see a drawn position as +2 pawns.

The right fix is search-the-root-then-fall-back-to-the-draw-score; that is an owner decision, so I
have not patched it.

# Other results this stretch
- **21-F16/F17/F18** (node budget, complete): `go nodes N` never reaches N (mean −20 to −28 %, worst
  −51.9 %, deterministic), it costs 6–11 plies of depth, but it changed the move on only **1 of 18**
  positions. Real, not urgent.
- **21-F15**: `go softnodes N` deterministic (40/40), depth-boundary stop, OVERSHOOTS by up to +58.9 %.
- **21-C13**: 0 forfeits over a simulated 60-move game at 6s+0.06; low clocks all legal and fast.
- **21-C14/C15**: softnodes and depth-12 answers are order-independent — 16/16 transposition pairs.
- **21-C16**: a mate outranks a drawn root (the PC build finds it; my prediction said otherwise and
  was wrong).
- **Withdrawn under file 6**: 21-F9, 21-F13, 21-F11.

**Next**: confirm 21-F19's size across more drawn positions (is +199 typical?) and check whether a
root at halfmove 100 with a mate in 2–3 is still found — that is the boundary the owner's fix needs
to get right in both directions.
