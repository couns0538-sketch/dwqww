# T04U-01: Check extension moved into LMR (kept in the reduced search only)
Status: COMPLETE

## Source
- Clockwork PR [#281](https://github.com/official-clockwork/Clockwork/pull/281) "Move check extensions into LMR", merged
  2025-10-09, merge [305e45878f](https://github.com/official-clockwork/Clockwork/commit/305e45878f75f069f687d38f4eec7c6ced34b66a);
  body = two OpenBench blocks + bench line, 0 comments, 0 review comments: the PR states no mechanism. Test logs (the
  PR's pythonanywhere links now show a hosting placeholder): STC [ob.cwchess.org/test/702](https://ob.cwchess.org/test/702/),
  LTC [ob.cwchess.org/test/704](https://ob.cwchess.org/test/704/); both test dev sha 277b0cc44f vs base a0ceb385d6.

## Licence
AGPL-3.0 at 305e45878f (`tools/licence_at.py --row`, notes/T04U/licences.md): ideas only. Read: PR title, PR body,
both test pages (settings + result blocks). No source file, diff or compare link opened.

## Mechanism
Own design under the PR title. The lock gives a non-losing checking move one extra ply, and LMR also reduces checking
moves one ply less. Here the extra ply is taken out of the move's depth and given back as one more ply of reduction
relief, only for the moves the lock would have extended. With the lock's whole-ply LMR the reduced (scout) search of
such a move then runs at the same depth as today (new depth one lower, reduction one lower); what goes away is the
extra ply in every search that is not reduced: the first move and PV searches, noisy checks at ttpv nodes with
move_count <= 4 (no LMR there), and the full-depth re-search after a reduced fail-high. A check is still looked at
deeply in the cheap scout search, but no longer makes its whole verified subtree one ply deeper. Cost side: both
test pages show bench nodes 17,351,435 (base) -> 11,595,447 (dev), -33 %.

## Forge fit
HAS both parts. `bash tools/forge_has.sh 'gives_check'` -> `src/search.cpp:1112-1115`: extension = 1 when
gives_check, depth >= CheckExtensionDepth (2, `:48`, range 1-30 `:90`), not root, SEE >= 0 (picker stage or
see_ge); it sits in the `else` of the singular block (:1089-1111), so singular TT moves are untouched. `:1143`
`if (gives_check) r -= 1;`, `:1147` reduced depth clamp(new_depth - r, 1, new_depth). Change: store the `:1112`
condition in a bool; option on -> extension stays 0 for it and the LMR block takes one more ply off r for it. Only
difference in the reduced search: a reduction that is already <= 0 now ends one ply lower (clamp to the lower
new_depth). Checks that fail SEE keep today's handling. Neighbours: TRIED gate 59 CheckExtDepthCap=8 (pack option,
0 hits in the lock; -1.85 Elo / -4.12 nElo, 1,500 games, LLR -1.13, capped no decision) removed the extension above
depth 8 with nothing in return; this card keeps it in the reduced search at all depths (the new angle). Plain
removal: Caissa 607753e non-reg only (notes/T04F/TABLE.md row 23), Stormphrax 67 non-reg (notes/T04B/TABLE.md
row 66); a limit: RubiChess #457 +1.32 (notes/T04N/TABLE.md row 37).

## Expected gain
Clockwork #281, Threads=1, OpenBench, book UHO_Lichess_4852_v1.epd (both test pages), adjudication win 5 x 600 cp,
draw from move 40 (8 x 5 cp). STC 8+0.08 Hash 16 MB +5.82 +- 3.96 Elo, n=9,724, [0,5] LLR 3.09 (-2.94, 2.94),
penta [92, 1125, 2287, 1244, 114] (own conversion +10.2 +- 6.9 nElo); LTC 40+0.4 Hash 64 MB +3.35 +- 2.61, n=19,922,
[0,5] LLR 3.04, penta [119, 2314, 4936, 2440, 152] (+6.2 +- 4.8 nElo). Short STC (wide bar); gain shrinks at LTC.
Forge estimate: 0 to +3 Elo **UNPROVEN** (Clockwork's pre-change extension rule is unknown, the lock's is already
SEE-filtered; gate 59 leaned negative; plain removal elsewhere was only neutral).

## Effort
Crew hours: ~2 (5-line option, OFF pins, ON node ratio, smoke, mate probe, lint). CPU: one STC SPRT up to 3,000
games = ~6-7 h at 430-502 games/h; LTC only after an STC pass. GPU: none.

## Test plan
Pre-gate: OFF bench and perft equal to the lock pins (FD3A5190); ON bench differs, stable over 2 runs, and its node
ratio ON/OFF is written down (a large drop like the source's says the extension is a big share of Forge's tree); T1
smoke without illegal moves; mate probe OFF/ON (check-heavy lines). Gate route (crew rule): Threads=1, UHO book,
SPRT [0,5] in normalized Elo, alpha = beta = 0.05, pentanomial, cap 3,000 games; capped = UNPROVEN / no decision,
one extension if positive; LTC after an STC pass. CheckLmrExtra = 0 = plain removal (simplification line only).

## OFF-by-default design
UCI spin `CheckExtLmr`, default 0, range 0-1; spin `CheckLmrExtra`, default 1, range 0-2, read only when
CheckExtLmr = 1 (own start value: 1 = exactly the ply taken from the extension; 0 = plain removal). At 0 no new
branch runs: extension and LMR code paths are the lock's, so the tree, bench nodes and perft equal the pins.
