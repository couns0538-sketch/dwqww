# THE PERFT NULL RESULT — what was checked, how, and why a zero here is a measured zero

**Seat 23, area 3 (move generation). One page, because this is the strongest null result in the run and a reader
should be able to weigh it without reading 16 job folders.**

## What was checked

| set | positions | depths | result |
|---|---|---|---|
| R seed 2301 (random legal games, one position every 7 plies) | 5,000 | perft 1–4 | 0 differences (23-F4) |
| R seed 2401 (independent draw, 0 FENs in common with 2301) | 5,000 | perft 1–4 | 0 differences (23-F22) |
| R seed 2301, first 200 | 200 | perft **5** | 0 differences, 7,399,207,740 nodes on each side (23-F11) |
| set G, first 30 | 30 | perft **5** | 0 differences, 1,022,355,864 nodes on each side (23-F12) |
| R seed 2501 (third independent draw, 0 overlap) | 100 | perft **5** | 0 differences, 2,603,588,130 nodes on each side (23-F33) |
| special positions filtered from R+G by python-chess | 58 | perft 1–4 | 0 differences (job 2) |
| seat 13's special-position set (their FENs) | 494 | perft 1–4 | 0 differences, 1,976/1,976 pairs (23-C3) |
| seat 03's set_all230 (their FENs) | 230 | perft 1–5 | 0 differences, 1,150/1,150 pairs (23-C2) |
| hand-built pinned-en-passant positions + control | 3 + 1 | perft 1 | engine omits the pinned capture in all 3, emits it in the control (23-F6) |
| the same 5,000 seed-2301 positions on the **PC r15 build** under **PC20** | 5,000 | perft 1–4 | 0 differences, totals identical to base (23-F9) |

**Total: 10,000 distinct random-legal-play positions at depths 1–4, 330 at depth 5, 494 + 230 of other seats'
positions, and zero disagreements anywhere.**

## Why this zero is a measured zero, not a blank

Four things, each with a committed artifact:

1. **The relation is the right one.** Perft counts are absolute integers for a fixed (position, depth), so
   `engine nodes == reference nodes` is correct. This mattered: the one time I assumed the wrong relation (that a
   colour-flipped `eval` should negate) I got a confident, entirely wrong table (23-F40). The perft relation was
   audited explicitly for that reason (23-F41).
2. **Both walkers are anchored on published values.** python-chess startpos perft 1–5 gives exactly
   20 / 400 / 8902 / 197281 / 4865609, and the engine gives 4,865,609 at depth 5. Neither walker is trusted on its
   own arithmetic.
3. **The comparison cannot pass on missing data.** A missing depth key or an empty comparison is a `HARD FAILURE`
   with exit 2 (23-F3's self-test, 7 malformed cases), and every script now carries a row-count guard that dies if
   the table is shorter than the depths asked for (23-F34/F35 — that fault actually happened and is why the guard
   exists).
4. **A planted mismatch is caught.** One node added to one reference row is reported as exactly one mismatching
   position (`218150726` vs `218150727`); a deleted depth key exits 2 (23-F10/23-F21).

## What this does NOT say

- **Nothing about unreachable boards.** Every position here was reached by a real game. The engine's FEN laxness
  (adjacent digits summing, impossible castling rights, unreachable ep squares) is area 1's territory; a generator
  that trusts a bad castling right would pass this whole suite trivially.
- **Nothing about depth 6+.** Depth 5 is the deepest checked.
- **Nothing about per-move divides on a mismatch**, because there were no mismatches; totals are compared, so a
  compensating pair of errors inside one position would be invisible. I consider that unlikely — the reference
  *is* python-chess's own move list — but it is the honest limit of a totals comparison.
- **Nothing about search.** Area 3 is move generation; the search's colour asymmetry (23-C15) and mate-distance
  behaviour (23-C5) are separate findings.

## The one-line version

> Over 10,000 random-legal-play positions the engine's perft equals python-chess's at depths 1–4, and at depth 5
> over 330 more (8.4e9 + 2.6e9 nodes walked), with the comparison's relation, both walkers, and the detection of a
> one-node difference all independently verified — and the same holds on the PC's build under its own settings.
