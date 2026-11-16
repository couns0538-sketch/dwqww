# REPORT — seat 07, job 41: settling position 155 (seat 03 vs seat 02)

## What was asked / the answer / how sure

**Asked:** (cycle work) two seats disagree about one position. Seat 03 (S-F16/S-F17) calls it a live
PC defect; seat 02 (S-C7/S-C8) says the move is correct and the mate is real. Nobody had reconciled
them with an instrument that compares the two claims.

**Answer:** **the symptom seat 03 reported is real, their explanation is imprecise, and seat 02's
defence is wrong on the merits.** The engine plays the move whose mate is **6 plies later** than the
best alternative. It is not "playing a move it scored as a loss" — all four moves are losses — and
"the PV replays to a verified mate" is true but does not make the choice good, because a shorter mate
was available.

**How sure:** high. python-chess replays the engine's own PV for each of white's four legal moves, and
the mate distances are exact and internally consistent.

## The position and why every move loses

    fen: 1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183

White is a **bare king on c6** against rook + bishop + knight. There is no drawing resource; all four
legal moves lose. So the question is never "does white survive" but "which death is slowest".

## Measured (PC r15 under PC20, Threads 1, Hash 16, depth 20, each move via `searchmoves`)

| white move | engine score | PV replayed by python-chess | plies to mate |
|---|---|---|---|
| `c6d6` | mate −8 | checkmate | **16** |
| `c6d7` | mate −8 | checkmate | **16** |
| `c6c5` | mate −8 | checkmate | **16** |
| **`c6c7`** (the engine's free choice) | mate −11 | checkmate | **22** |

The engine's free search chose `c6c7` and reported `mate −10` with a 20-ply PV that replays to
checkmate in exactly 20 plies.

**So:** `c6c7` is the **worst** of the four by six plies, and the engine's own per-move scores agree
with that ranking (−11 against −8). It is not a scoring failure — the engine knows `c6c7` is worse —
it is a **root choice** that picks the worse-scored move.

## Where each seat was right and wrong

| claim | verdict |
|---|---|
| seat 03: "the engine plays a move it has itself scored as a forced loss" | **Right that the move is bad; wrong about why.** All four moves are scored as forced losses, and correctly so. The defect is choosing the *slowest* loss, not scoring a loss. |
| seat 03: "the PC build does this, the base build does not" | consistent with their S-F11/S-F14 attribution to the bare-king rules; I did not re-test the base build here |
| seat 02: "does NOT reproduce a lone-king wrong-move defect" | **wrong on the merits.** Their check verified that `c6c7`'s PV really mates — which it does — but never compared it against `c6d6`'s 16 plies. A true mate is not a good move when a faster loss exists. |
| seat 02: "free choice is CORRECT" | **does not hold.** mate in 22 vs mate in 16. |

## The convention note

For a score **against** the side to move, the PV mate distance came out as **`2|N|` exactly** on all
four moves (mate −8 → 16 plies, mate −11 → 22 plies), not the `2N−1` I reached for first. Because the
offset is systematic across all four, it is a convention difference in how this engine counts, not an
error in any single case — and it does not affect the relative comparison that decides the question.

## Findings

**07-C40** in FINDINGS.md.

## Suspicions, not proven

- That the wrong choice is caused by the bare-king rules rather than by something generic in root move
  selection. Seat 03's S-F11/S-F14 attribute it to `FORGE_FIX_BARE_KING_LMR_CAP` and the
  `ONE_THREAD` combination, which my job38 scan found no evidence for *on a different sample*; here on
  a stripped bare-king ending I see the symptom, so their attribution remains the best available and I
  did not improve on it.
- Whether a deeper search fixes it. Seat 03's S-F19 reports it holds to depth 22; I did not go beyond
  depth 20 for all four moves (cost).

## What I did NOT do

- Did not re-run the base build on this position (seat 03 and seat 02 both did, and they disagree
  about what it means, not about what it answers).
- Did not test whether a patch to the bare-king cap changes the choice.

## What I am NOT sure about

- Whether the free search's `mate −10` versus `searchmoves c6c7`'s `mate −11` is a depth/aspiration
  difference or a genuine inconsistency in how restricted and unrestricted roots score the same move.
  It is one ply of mate distance in a lost position and I did not chase it.

## Times

See job41/stamps.txt.
