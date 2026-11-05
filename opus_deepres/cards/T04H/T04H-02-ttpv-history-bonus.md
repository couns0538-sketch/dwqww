# T04H-02-ttpv-history-bonus: bigger history update for the cutoff move of a ttpv node
Status: COMPLETE

## Source
- Stockfish commit [71e0b53](https://github.com/official-stockfish/Stockfish/commit/71e0b5385e) (2020-01-28), "More
  bonus for bestMoves on past PV nodes", PR https://github.com/official-stockfish/Stockfish/pull/2529 . Tests: STC
  https://tests.stockfishchess.org/tests/view/5e2ff5efab2d69d58394fd52 , LTC
  https://tests.stockfishchess.org/tests/view/5e2fff38ab2d69d58394fd55 (TC, book, threads, bounds from api/get_run;
  test note: "apply it on ex-pv nodes only").
- Removal check (corrected by verify 2026-11-05): the source REVERTED this patch three days later in
  [6ccb1cac5a](https://github.com/official-stockfish/Stockfish/commit/6ccb1cac5a) "Revert 5 recent patches"
  (2020-01-31, issue 2531: a regression test of the merged batch showed negative Elo). Removing this patch alone
  passed as a simplification: STC 10+0.1 {-1.5,0.5} n=46,100 W 8,853 L 8,727 D 28,520 (removal +0.93 +- 1.93) and
  LTC 60+0.6 {-1.5,0.5} n=16,920 W 2,161 L 2,055 D 12,704 (removal +2.11 +- 2.60), own pentanomial arithmetic from the
  revert message. A re-add was not found by a grep of all cached Stockfish messages 2016-now for ttpv / past PV
  together with bonus / stat / history / remove (a differently worded one would escape it). acb0d20 (2023) concerns
  a 2023 PV-node malus.

## Licence
Stockfish GPL-3.0 (Copying.txt at 71e0b5385e): ideas only. Read: commit title and message, PR 2529 text, two
fishtest run records. No source file or diff was read.

## Mechanism
Own words: when a node that is or was on the PV (ttpv) gets a cutoff, its best move's history update is made larger
than at other nodes, so the move ordering of former-PV regions stays close to that of the PV ("keep past PV nodes as
close as possible to current PV nodes"). The size and the exact tables of the source's change are not in any text
read; the design below is own.

## Forge fit
`bash tools/forge_has.sh 'update_quiet_stats\(|update_capture_stats\(|history_bonus\('` -> LACKS at
`src/search.cpp:1198`: the fail-high update passes `depth + (best_score > beta + 100)`, no ttpv term (`:1200` captures:
plain depth). Related but different: `:1203-1204` gives a quarter bonus to a PV best move without a cutoff. Note the
lock's `update_quiet_stats` (`:729-750`) also moves killers / counter and uses one bonus for the best move AND the
malus of the tried quiets, so a depth bump scales both (the source's split is unknown). Not in TRIED_GATES. Nearest
earlier row: notes/T04G/TABLE.md row 12 (Altair PR 50, pv + improving + null-search terms bundled in the bonus,
+1.64 +- 1.86 n=73,928 [0,5], did not pass): same family, other flag (pv node, not the stored ttpv bit) and a
bundle, so a caution, not a duplicate. x1 TtCutoffHistory (TT-cutoff updates) is another site.

## Expected gain
Source (Stockfish master of 2020-01, classical eval, Threads=1, book noob_3moves.epd, logistic SPRT; Elo +- 95 % from
the pentanomial, own arithmetic): LTC 60+0.6 [0,2] LLR 2.95, 15,797 games (W 2,137 L 1,960 D 11,700) = +3.81 +- 2.71;
STC 10+0.1 [-1,3] LLR 2.95, 13,302 games (W 2,647 L 2,507 D 8,148) = +3.62 +- 3.69 (consistent with zero at 95 %).
Forge estimate: 0 to +3 Elo **UNPROVEN** (old engine, old book; Forge's ttpv set is the same kind, its history
gravity and tables differ). Verify caution: the source reverted the patch after 3 days (removal +0.93 +- 1.93 STC /
+2.11 +- 2.60 LTC, see Source): the LTC pass was not durable there; the coordinator should re-judge the card's rank.

## Effort
Crew 1 h (one depth term at two call sites, option, OFF pins, ON bench, smoke). CPU at 430-502 games/h: STC SPRT
[0,5] about 6-14 h, then one LTC; no GPU.

## Test plan
Pre-gate: OFF bench d11/d13/d16/d20/d22 = lock pins; ON bench differs (live); perft unchanged; mate probe OFF/ON;
spot check that main-history magnitudes stay inside HistoryMax on the bench set. Gate: UHO SPRT [0,5] at STC, then
LTC (decide at LTC: the source's STC is inside its noise).

## OFF-by-default design
UCI spin `TtPvHistPlies`, default 0 = off, range 0-2, own start 1. At 0 the depth passed at `:1198` / `:1200` is the
lock's, so every bonus, node and bench pin equals the lock. At N > 0 both calls get `+ N` when `ss->tt_pv` (pv nodes
and stored-pv nodes alike). Untested variant for a later pass: bump only the best move's bonus (needs a second bonus
argument in `update_quiet_stats`).
