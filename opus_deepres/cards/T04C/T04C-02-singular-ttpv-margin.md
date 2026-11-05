# T04C-02: Lower singular beta at former-PV nodes (extra singular margin when the TT says tt_pv)
Status: COMPLETE

## Source
- PlentyChess PR 286 "Lower singular beta for nodes that used to be on the PV" (commit 9b8517d, merged 2024-11-19),
  https://github.com/Yoshie2000/PlentyChess/pull/286 ; tests https://chess.aronpetkovski.com/test/6088/ (STC) and
  https://chess.aronpetkovski.com/test/6089/ (LTC); that host now serves only furybench.com's certificate, so the test
  pages (book) could not be read.
- Stockfish [4e89864](https://github.com/official-stockfish/Stockfish/commit/4e8986483a) (PR 2550), [1591e5a](https://github.com/official-stockfish/Stockfish/commit/1591e5ac3b) (PR 4159): commit messages only (review fix, CRITIC2).

## Licence
PlentyChess @fdbdbccab8: GPL-3.0 (notes/T04C/licences.md) = ideas only. Read: the PR title and its OpenBench blocks;
no source, no diff, no description text. The margin below is own design; no constant carried over.
Stockfish @4e8986483a and @1591e5ac3b: GPL-3.0 (tools/licence_at.py, Copying.txt) = ideas only; two commit messages read, no source.

## Mechanism
Own words. The singular test asks whether every alternative to the TT move fails below singular_beta = TT score minus a
margin that grows with depth; if so the TT move is extended, if even singular_beta beats beta the node is cut (multicut).
At a node that the TT marks as having been on the PV (tt_pv) but that is searched now with a null window (not a PV node),
the extra-margin rule lowers singular_beta further: the TT move must stand out by more before it is extended, and the
multicut fires less often there. Own reading: at such nodes the TT score itself came from a wider search, so a small gap
between it and the alternatives is weaker evidence of a forced move, while these nodes are where a wrong prune costs most.
In Forge the double-extension threshold (`singular_score < singular_beta - 24`) moves down with singular_beta, and the
negative extensions fire more often (more verification searches end at or above the lower singular_beta).

## Forge fit
LACKS. Lock `src/search.cpp:1091`: `singular_beta = tt_score - SingularMargin * depth` (SingularMargin = 2 cp per ply,
a UCI tunable 0-10, `:37`, `:82`), no tt_pv term; `ss->tt_pv = pv_node || tte.pv()` at `:919` and LMR already uses it (`:1139`).
"Former PV" here = `ss->tt_pv && !pv_node` (every PV node has tt_pv true). Double extension `:1102`, multicut
`:1105-1106`, negative extensions `:1107-1111`. SingularV2 (FB2-J3, `singular_v2.hpp`) changes extensions and multicut,
not the margin; no FORGE_RESULTS row touches the singular margin (tools/tried_gates.py --grep Singular: 0 rows).
Change: one added term, 1-3 lines.

## Expected gain
PlentyChess 286: STC 8+0.08, 1 thread, 16 MB, SPRT [0, 3]: +5.21 +- 3.51, n=9,938 (W 2,334 L 2,185 D 5,419), LLR 2.13 of
(-2.25, 2.89); LTC 40+0.4, 64 MB, [0, 3]: +5.34 +- 3.21, n=10,536 (W 2,577 L 2,415 D 5,544), LLR 2.50. Neither SPRT
finished; the PR was merged on these numbers. Book not stated (test pages unreadable). No second engine's log found for
this term in Berserk or Alexandria (their titles do not mention it).
Better evidence, both TCs and large n (review fix, CRITIC2; Stockfish fishtest numbers from the commit messages, TC / book not
in them; Elo from W/D/L, +- 95 % from the pentanomial, own arithmetic): 4e89864 (2020; lowers singular beta at nodes that were
on the PV but are not PV nodes now = this rule) STC {-0.50,1.50} LLR 2.94 n=154,953 +0.93 +- 1.05, LTC {0.25,1.75} LLR 2.95
n=70,974 +1.83 +- 1.28; 1591e5a (2022, "Do less singular extensions for former PVnode", by its message a re-introduction in
another form of logic simplified away earlier) STC <0.00,2.00> LLR 2.94 n=23,296 +4.41 +- 2.29, LTC <0.50,2.50> LLR 2.94 n=235,592 +1.04 +- 0.64.
Forge estimate: 0 to +3 Elo **UNPROVEN** (PlentyChess: two unfinished SPRTs with wide errors; the three Stockfish runs with n > 70k are +0.9 to +1.8; Forge's singular margin is
already small at 2 cp per ply, so the relative change is large).

## Effort
Crew ~1 h (term, option, pins). CPU: UHO SPRT [0, 5] at STC ~6.6k games ~13-15 h at 430-502 games/h (cap 12k ~24-28 h),
then LTC (~3x per game). GPU: none.

## Test plan
Pre-gate: OFF bench pins d11 312866 / d13 862329 / d16 3024920 / d20 12389307 / d22 34048354 + perft; ON bench differs
(live: count singular searches and extensions at bench 16 OFF / ON, expect fewer extensions at tt_pv non-PV nodes);
2-minute smoke. Gate: UHO SPRT [0, 5] at STC with SingularTtPvMargin=32, then LTC (the source's LTC was as large as its
STC, so LTC is the confirmation, not a rescue).

## OFF-by-default design
UCI `SingularTtPvMargin` 0-96, in 1/16 cp per ply, default 0 = off; when on, singular_beta is lowered by
SingularTtPvMargin x depth / 16 only where `ss->tt_pv && !pv_node`. Own start 32 (= +2 cp per ply, i.e. the margin is
doubled at those nodes); SPSA range 8-96. OFF adds 0, so singular_beta and the bench pins equal the lock.
