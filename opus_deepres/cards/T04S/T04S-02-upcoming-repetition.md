# T04S-02: Upcoming-repetition test in search (a draw one reversible move away raises alpha)
Status: COMPLETE

## Source
- Sirius PR #229 "Detect upcoming repetitions in search" (merged 2024-12-21, commit b91b2a1e75):
  https://github.com/mcthouacbb/Sirius/pull/229 ; test https://mcthouacbb.pythonanywhere.com/test/488/ . Not reverted in
  the Sirius PR list (reverts seen: #224, #269, #349). Two days earlier #228 moved the plain repetition check to start
  4 plies back (no test logged).
- Table-only rows of other tracks for the same idea: notes/T04E/TABLE.md row 40 (Viridithas #465, AGPL-3.0),
  notes/T04F/TABLE.md row 4 and notes/T04F/DIFF.md row 1 (Caissa, MIT: search 50b25dc, qsearch 8e9ce37).

## Licence
Sirius: no LICENSE file at b91b2a1e75 (all rights reserved; row in notes/T04S/licences.md): ideas only; only the PR
title and its test block were read, never a source file or a diff. The mechanism below is built from that title and
from the Caissa description T04F already wrote (Caissa is MIT at 57cae7ef71: its code may be read, copy only with
notice; nothing copied here).

## Mechanism
A side can force a draw by repetition when one reversible move takes the board back to a position seen earlier in the
same reversible stretch (no pawn move or capture since). This can be tested cheaply before searching: a table built at
start-up holds, for every non-pawn piece and every pair of squares that piece can move between on an empty board, the
XOR of the two piece-square keys and the side key. At a node, walk back over earlier positions of the stretch (every
second ply from 3 plies back, within the half-move clock); if the current key XOR an earlier key is in the table and
the squares between the two squares are empty, a repeating move exists. If the draw score is above alpha, alpha is
raised to it, and the node returns at once when that reaches beta. Caissa restricts it to non-PV nodes with alpha < 0;
Sirius's title says search only. Draw score as in the lock (no new contempt).

## Forge fit
`bash tools/forge_has.sh 'cuckoo|upcoming|game_cycle|has_repeated'` -> 0 hits: LACKS. What exists: `is_draw`
src/search.cpp:692-702 (50-move rule, `board.is_repetition(root_history_index_)`, insufficient material), called at
:780 (qsearch) and :893 (search); Board::is_repetition src/board.cpp:892-910 walks the key history;
`halfmove_clock()` include/forge/board.hpp:157. New: a start-up key table (board layer, built from Forge's own Zobrist
keys), a Board::has_upcoming_repetition(ply-limit) test next to is_repetition, one call in search after the draw check
(non-PV, alpha below the draw score). Larger than a search-only tweak (T04E row 40: "larger work"). Not T04F-03: that
card changes how a repetition that has already occurred is scored (twofold vs threefold by node type); this card sees a
repetition one move ahead, before any move is made - a different test and different code.

## Expected gain
Sirius: STC 8+0.08, Threads=1, Hash 16 MB, +5.29 +- 3.19, n=15,976 (penta [192, 1860, 3689, 2007, 240]), SPRT [0,3],
LLR 2.95 (own nElo +8.9); no LTC; book not named (missing). Viridithas #465: LTC +2.27 +- 1.70 n=36,622 [0,3] (no STC).
Caissa qsearch variant 8e9ce37: +1.03 +- 1.33 [0,2] n=124,388, did not pass. Sirius was a weak hand-crafted-eval engine
then; repetition-heavy endgames matter less in UHO openings.
Forge estimate: +1 to +3 Elo at STC, **UNPROVEN**.

## Effort
Crew 5-7 h (key table and its self-check: entry count against a brute-force enumeration, board test positions with and
without a repeating move, search hook, OFF identity, ON bench). CPU: one STC SPRT up to the 3,000-game cap = 6-7 h at
430-502 games/h; LTC the same again. GPU: none.

## Test plan
Pre-gate: OFF bench / perft pins equal to the lock FD3A5190; unit tests (a position one knight move from a repetition is
found, a blocked slider path is not, nothing found after a pawn move); ON bench stable over two runs; a mate-finding
sanity set unchanged (the test must not raise alpha in mate-relevant lines). Gate route (crew decision): Threads=1, SPRT
[0,5] normalized Elo, alpha = beta = 0.05, pentanomial, UHO book, cap 3,000 games; a capped run is UNPROVEN / no
decision, one extension if its Elo is positive. Then LTC with the same rule. Qsearch use only as a later second value.

## OFF-by-default design
UCI option UpcomingRep (int, default 0 = off, 1 = search non-PV nodes, 2 = also qsearch). At 0 the table may be built
but is never probed, so every node, the bench and the pins equal the lock.
