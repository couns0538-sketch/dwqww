# T04G-05: History update one ply deeper when the score reached the node's eval
Status: COMPLETE

## Source
Altair PR 182 "depth bonus to history" (https://github.com/Alex2262/AltairChessEngine/pull/182, merge cbb5e27ab2,
2024-07-18, test https://chess.swehosting.se/test/7457/; patch read: 2 lines in `src/search.cpp`). Still the rule at
Altair@b2447b825b `src/search.cpp:1103-1104` (applied on every alpha raise); its `eval` is set at `:665-685`.

## Licence
MIT at b2447b825b and at the PR's merge (LICENSE touched once, 7f28fb4127 2023-05-28, before the PR;
notes/T04G/licences.md): copy with notice. Nothing copied; mechanism in own words; no constants carried over.

## Mechanism
The node's eval (corrected static eval, replaced by the TT score when the bound allows) is a prediction of the
result. When the move that raised alpha scored at least that eval, the history update is done as if the node were
one ply deeper: a larger bonus for the move and a larger malus for the moves tried before it. A cutoff the eval had
already promised with room to spare (eval above the score) teaches less than one that met or beat it (including a
cutoff at a node whose eval was below beta). Altair has no other depth term. The lock has one of a different kind:
+1 when the score beat beta by 100 cp (quiets only). The two tests disagree exactly in the interesting cases: eval
below beta with a small cutoff (lock 0, this +1) and eval far above beta with score between beta + 100 and the eval
(lock +1, this 0).

## Forge fit
LACKS the eval test. `bash tools/forge_has.sh 'best_score > beta \+ 100'` -> `src/search.cpp:1198` only (quiet stats:
`depth + (best_score > beta + 100)`); capture stats use plain depth (`:1200`); the PV best move without a cutoff gets
history_bonus(depth) / 4 (`:1203-1205`). The lock's `eval` (`:929-943`) is the same quantity as Altair's; in check
it is ValueNone 32002 (`include/forge/search.hpp:59`), so `best_score >= eval` is false there with no special case; in
a singular search it is the plain static eval. history_bonus = min(2048, 20 d^2 + 48 d - 32) (`:153-155`), so +1
ply is x4 at d 1, +48 % at d 4, +24 % at d 8 and nothing from d 10 (cap). T04 TABLE.md row "history depth bonus"
judged PR 182 HAS from its title; the patch shows the eval condition, not a beta margin, so this is a new angle.
Not in TRIED_GATES (`tools/tried_gates.py --grep 'Hist|Bonus'`: PawnHist, ContHist4Pct, ThreatHist, HistMalusPct
only); R9 / 30-h SPSA only scaled HistoryBonus* constants. Other tracks' bonus rows test beta, not the eval (T04F
DIFF row 78 score-gap curve; T04E TABLE Viridithas #344, unclear). Change: ~4 lines before `:1196`.

## Expected gain
Altair PR 182: +5.61 +- 3.85 Elo (95 %), 8+0.08, Threads=1, Hash 32 MB, SPRT [0,5] (-2.94, 2.94), LLR 3.01,
n=9,422 (W 2,323 L 2,171 D 4,928; penta 73 / 1,044 / 2,330 / 1,186 / 78); book not stated; no LTC. A short SPRT
stop inflates the point value (stopping-rule bias); 95 % range about +1.8 to +9.5. Mid-2024 Altair (NNUE era).
Altair updates on every alpha raise, the lock only at a cutoff, so the rule touches fewer updates in Forge.
Forge estimate: 0 to +3 Elo **UNPROVEN**.

## Effort
Crew ~1.5 h (4 lines + 2 options, OFF pins, ON-live bench, planted bug, pin_check, smoke). CPU: one STC SPRT [0,5]
~6.6k games ~13-15 h at 430-502 games/h; LTC only if STC passes. No GPU.

## Test plan
Pre-gate: OFF bench / perft pins equal to the lock FD3A5190; ON bench nodes differ (live); planted bug (test
inverted to best_score < eval) gives other ON nodes; T1 smoke. Gate: UHO SPRT [0,5] at STC (Threads=1), then LTC.
Bit 1 alone (quiets only) or a non-zero margin only as a second line after the first is decided.

## OFF-by-default design
UCI option `HistEvalDepth` (bits, default 0, range 0-3): bit 1 = quiet stats at a cutoff get +1 depth when
best_score >= eval + `HistEvalDepthMargin` (added to the lock's beta + 100 term, so up to +2), bit 2 = capture stats
the same. `HistEvalDepthMargin` cp (default 0, range -60..+60). Own start: bits 3 (all tables, as measured),
margin 0. At 0 the extra term is 0, the depths passed at `:1198` / `:1200` are the lock's, so the tree and the bench
pins are the lock's.
