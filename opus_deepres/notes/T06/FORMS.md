# T06 - eval post-processing forms per engine (own words; no code, no tuned constants)

Legend: M = material on the board, c = halfmove (rule50) clock, v = static eval (side to move), r = a search score.
GPL / AGPL rows come from commit titles, commit messages, PR text and test logs only (never source). MIT rows may come
from source (read at the named commit, described in own words).

## Forge lock FD3A5190 (own source, read-only)
- HCE `scale_factor()` (src/eval.cpp:346-371): drawishness scale on the HCE endgame term only - no pawns for the strong
  side with at most a minor ahead, opposite-coloured bishops (with/without other pieces, by strong-side pawn count),
  and a few-pawns scale; then the HCE tapers mg/eg by phase (eval.cpp:455-459).
- Residual net (src/search.cpp:616-620): final = clamp(HCE_runtime + network); the net output is NOT scaled by
  material, by the HCE scale factor, by the clock or by anything else. Both parts exist separately at that line.
- Draw score: exactly 0 at every draw return (search.cpp:692-700, 780, 893). rule50 only drives the draw at 100 and
  the TT-cutoff guard (search.hpp:75-85).

## Forge E3 candidate (own, e3_evalpost_al1; OFF-default options, gated vs the lock, rows UE3* of TRIED_GATES)
Order: raw static eval (TT keeps raw) -> optimism -> material scale -> rule50 damp -> clamp -> correction history.
- EvalMatScale s (0..50 = 0..0.5): multiply by 1 + s(2M - M0)/M0, M = total MG material of both sides, M0 = start
  total. Centred at M0/2: factor 1 at half material, amplifies above, damps below. One-sided range (s >= 0).
- EvalOptimism K (0..150): o = K r/(|r| + 120) from the previous iteration's root score (depth >= 4, 0 for mates),
  +o for the root side, -o for the other, weighted by M/M0. Symmetric, no complexity term.
- EvalRule50Damp D (0..60): v -= v D min(c,100)/10000 (linear from clock 0).
- DrawJitter (0/1): draw score = (nodes & 2) - 1. Not gated.

## Stockfish (GPL-3.0, ideas only; commit titles + fishtest logs, official-stockfish/Stockfish)
PENDING
