# T04S-01: Continuation-history update with the summed continuation score as the gravity base
Status: COMPLETE

## Source
- Sirius #328 "Update conthist entries based on the sum of conthist scores" (2025-11-17, 9d808836c6):
  https://github.com/mcthouacbb/Sirius/pull/328 ; tests https://mcthouacbb.pythonanywhere.com/test/1091/ (STC),
  https://mcthouacbb.pythonanywhere.com/test/1093/ (LTC). Stage 2: #330 (3b2cd0247b), test 1100 on the same host.
- Tarnished #132 "Update conthist with sum as base" (2bd208333e): https://github.com/Bobingstern/Tarnished/pull/132 ;
  tests https://chess.n9x.co/test/4877/ (STC), https://chess.n9x.co/test/4888/ (LTC).
- Clockwork #234 (413106d9bc): https://github.com/official-clockwork/Clockwork/pull/234 , test
  https://clockworkopenbench.pythonanywhere.com/test/497/ . Origin credited to PlentyChess (not read). Table-only so far:
  notes/T04E/TABLE.md row 39 (Viridithas #370), notes/T04B/TABLE.md row 28 (Stormphrax PR 270).

## Licence
Sirius: no LICENSE file at 9d808836c6 and 3b2cd0247b (all rights reserved). Tarnished: no LICENSE at 2bd208333e (GPL-3.0
at HEAD). Clockwork: AGPL-3.0 at 413106d9bc. Rows in notes/T04S/licences.md. Use: ideas only. Read: PR titles, PR bodies
(test blocks, a few lines of text) and commit titles; never a source file or a diff.

## Mechanism
History tables decay with a gravity term (entry += bonus - entry x |bonus| / Max), so each table saturates on its own,
while a quiet move's ordering score is the sum of several tables. The idea: when the continuation entries of one move
are updated (bonus for the best quiet, malus for the tried ones), first compute the move's summed continuation score S
over the updated plies, then use a blend of S and the entry's own value as the decay term of every one of those entries.
When the plies already agree that a move is good, each entry gains less; an entry that disagrees with the others is
pulled harder toward them. The tables learn a bounded combined score instead of saturating one by one. Stage 2 (Sirius
#330, Stormphrax PR 270): a share of the main-history value is added to S. No source mix weight is carried over.

## Forge fit
`bash tools/forge_has.sh 'apply_history|skip_quiets'` -> src/search.cpp:157-160 `apply_history` (entry-local gravity,
HistoryMax 16384 at :107); :720-727 `update_continuation` applies it to plies 1, 2, 4 (ply 4 at half bonus); callers
:743 / :748 (best quiet / tried quiets), :1156 (late quiet beat alpha), :1208 (previous move). Ordering reads main +
cont1 + cont2 (:704-712). LACKS. Change: in update_continuation compute S once before any write (plies 1, 2 and 4, ply 4
at half weight, own choice), then per entry base = entry + p x (S - entry) / 100 and entry += bonus - base x |bonus| /
HistoryMax, done in int and clamped to +-HistoryMax before the int16 store (base can reach about 2.5 x HistoryMax). Side effect: the cont part of
quiet_history settles lower, so HistoryPruneMultiplier / LmrHistoryDivisor (old scale) may need a short retune.

## Expected gain
Sirius (hand-crafted eval engine): STC 8+0.08 +5.86 +- 3.36 n=13,748 [0,3] LLR 2.95 (own nElo +10.1); LTC 40+0.4 +14.38
+- 5.27 n=4,642 [0,3] LLR 2.97 (+27.3 nElo). Tarnished (NNUE): STC 8+0.08 +2.23 +- 1.70 n=39,808 [0,3] LLR 2.95 (+4.5
nElo); LTC 40+0.4 +2.53 +- 1.85 n=32,122 [0,3] LLR 2.96 (+5.2 nElo). Clockwork (hand-crafted eval): STC 8+0.08 +14.67
+- 7.14 n=3,460 [0,5] LLR 3.04; a VLTC "+34" is only quoted in the Sirius text (test 503 not fetched). Stage 2: Sirius
+4.50 +- 2.83 n=18,604 [0,3], no LTC. All Threads=1; books not named (missing). Viridithas #370 LTC +2.84 +- 2.00. The
hand-crafted-eval engines gain far more than the NNUE engines; Forge (HCE + small residual net) is in between.
Forge estimate: +1 to +4 Elo at STC, **UNPROVEN**.

## Effort
Crew 2-3 h (option, OFF identity, ON bench, clamp check). CPU: STC SPRT up to the 3,000-game cap = 6-7 h at 430-502
games/h, LTC the same, stage 2 another 6-7 h. GPU: none.

## Test plan
Pre-gate: OFF bench / perft pins equal to the lock FD3A5190; ON bench stable across two runs; assert build that no entry
leaves +-HistoryMax; unit check that p = 0 gives the old entry bit for bit. Gate route (crew decision): Threads=1, SPRT
[0,5] normalized Elo, alpha = beta = 0.05, pentanomial, UHO book, cap 3,000 games; a capped run is UNPROVEN / no
decision, one extension if its Elo is positive. Then LTC with the same rule. Stage 2 only after stage 1 passes.

## OFF-by-default design
UCI option ContHistSumBase (int, default 0 = off, range 0-100 %, own start for the ON test 60, SPSA-able). At 0 the
base is the entry itself, which is exactly the lock's apply_history (:157-160): every node, the bench and the pins stay
identical. Stage 2: ContHistMainShare (int, default 0, range 0-100 % of the main-history entry added to S, own start
25), inert while ContHistSumBase = 0.
