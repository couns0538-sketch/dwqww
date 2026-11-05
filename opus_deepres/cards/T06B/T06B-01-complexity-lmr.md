# T06B-01-complexity-lmr: reduce late moves less when the eval is far from plain material ("complexity")
Status: COMPLETE

## Source
- Alexandria: https://github.com/PGG106/Alexandria/commit/7de97e77aa "Introduce Complexity, use it to tweak LMR"
  (PR https://github.com/PGG106/Alexandria/pull/472, empty body; the commit message holds the two test blocks).
- Obsidian: https://github.com/gab8192/Obsidian/commit/e144325d52 "Use complexity in LMR" (test block in the message).
- Related signal, already tried by the crew: Stormphrax https://github.com/Ciekce/Stormphrax/pull/212 "lmr less if
  corrhist correction is high" (tests https://chess.swehosting.se/test/9263/ , https://chess.swehosting.se/test/9275/).
- Own: notes/TRIED_GATES.md row 16 (gate16_p7_epa_vs_ep10, LmrCorrThreshold=30).

## Licence
Alexandria GPL-3.0 at 7de97e77aa, Obsidian GPL-3.0 at e144325d52, Stormphrax GPL-3.0 at 639efd5c08
(tools/licence_at.py, notes/T06B/licences.md): ideas only - commit titles, commit messages, PR text and test logs
were read, never source. None of the texts gives a formula, a direction or a constant.

## Mechanism
Two engines compute a per-node "complexity" from their evaluation and let it change the late-move reduction; both
logged gains, Alexandria at STC and LTC. A third engine does the same with a different signal (the size of the
correction-history adjustment) and states the direction: reduce less when the signal is large.
Own Forge form: at a node that has a static eval (not in check), complexity C = |raw_eval - M|, where raw_eval is the
uncorrected static eval the node already holds (fresh or from the TT) and M is the plain material balance for the
side to move from Forge's own PieceValueMg table and piece counts, pawns included. C measures how much of the eval
is not material (king safety, activity, the residual net's correction) - positions where a shallow verdict is less
trustworthy. In the LMR block: if C > T, add a signed step s to the reduction (s = -1 reduces less, the stated
direction of the related signal; s = +1 is the other sign, screened only if -1 fails). Variant (screen only):
C = |network|, the residual net's own output, which needs one byte in the TT to survive TT-eval hits.

## Forge fit
Lock has no complexity term (tools/forge_has.sh 'complex': 0 hits). The LMR block is src/search.cpp:1136-1146
(integer plies, +-1 steps for tt_pv, improving, cut node, check, history). raw_eval is set at src/search.cpp:935-936
(main search, from the TT eval or static_evaluate); PieceValueMg is include/forge/eval.hpp:30. The correction-size
signal is NOT proposed: the crew gated it (gate 16, LmrCorrThreshold=30, 1,000 games, -0.69, cap, older base).
Change: compute C once per node when the option is ON (popcounts + one subtraction), one branch in the LMR block.
Scope flag: a search use of an eval-derived signal; notes/T06/FORMS.md lists complexity-in-search outside T06's
eval scope - carded here because it is the only Forge-lacking item of this sweep with STC + LTC gains; reroute to
a T04 track if the coordinator prefers. Not a duplicate of T06-03: same kind of signal (its C = |residual| is the
variant above), different use (T06-03 changes the eval itself, this changes only the reduction).

## Expected gain
Alexandria 7de97e7: STC +2.14 +- 1.67 (8+0.08, 46,374 games, [0,3], LLR 2.93); LTC +2.63 +- 1.92 (40+0.4, 30,154
games, [0,3], LLR 2.90). Obsidian e144325: +2.51 +- 1.94 (10+0.1, 31,056 games, [0,2], LLR 2.05, merged before a
full pass, no LTC). Related signal Stormphrax #212: STC +1.39 +- 1.12 (8+0.08, 105,114 games, [0,3], LLR 2.91), LTC
+2.10 +- 1.63 (40+0.4, 42,242 games, LLR 2.90). All OpenBench, Threads=1, the engines' own books (verify 00:40: all five blocks re-read and recomputed from W/L/D; Stormphrax's two tests on UHO_Lichess_4852_v1).
Forge estimate: 0 to +2 Elo **UNPROVEN** (the engines' complexity formula is unknown; Forge's C is an own definition).

## Effort
Crew: ~2 h code (C at the static-eval site, one LMR branch, two options, expose build) + ~2 h proofs. CPU: one STC
SPRT at 430-502 games/h, 3,000 games = 6-7 h, +6-7 h one extension if positive [last round, coordinator, unverified]; optional 1-parameter SPSA on T first (~14 h); LTC only if
STC is positive. GPU: none.

## Test plan
Pre-gate: OFF bench / perft = lock pins; ON bench differs; a C histogram over the bench positions (debug counter,
crew) to place the start T where the branch fires on roughly 10-30 % of LMR nodes (own choice, start T = 150 cp,
range 50..400). Gate: s = -1, UHO SPRT [0,5] at STC vs the lock (Threads=1), then LTC; s = +1 only if -1 is H0.

## OFF-by-default design
UCI `LmrComplexityStep` (-1..1, default 0) and `LmrComplexityThreshold` (cp, 25..600, default 150, unused at step 0).
With step 0 the term is neither computed nor read and no TT field changes, so search is node-identical to the lock
(bench pins).
