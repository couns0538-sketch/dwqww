# T04T-02: ProbCut returns a score pulled toward beta (fail-firm)
Status: COMPLETE

## Source
- pawnocchio PR [#57](https://github.com/JonathanHallstrom/pawnocchio/pull/57) "Probcut failfirm", merged 2026-04-17,
  merge commit [64a744b5ee](https://github.com/JonathanHallstrom/pawnocchio/commit/64a744b5ee). Test logs:
  [STC furybench.com/test/6040](https://furybench.com/test/6040/), [LTC furybench.com/test/6050](https://furybench.com/test/6050/).
  The body holds only the two test blocks (no mechanism text).
- Reckless PR [#759](https://github.com/codedeliveryservice/Reckless/pull/759), as recorded by T04E
  (notes/T04E/TABLE.md:21, "ProbCut returns a score blended toward beta"; table-only there, not re-read here).

## Licence
pawnocchio: GPL-3.0 at 64a744b5ee (`tools/licence_at.py --row`, notes/T04T/licences.md); Reckless: AGPL-3.0 (T04E).
Ideas only: PR titles, PR bodies and test logs; no source file or diff opened.

## Mechanism
ProbCut proves a capture against a bound raised above beta by a margin, first with qsearch and then with a reduced
search. On success the lock returns the verified score itself. That score was earned against the raised bound at a
reduced depth, so it overstates what the node has shown at its own depth. Fail-firm returns a score moved down by the
gap between the raised bound and beta: it still proves the node fails high (it never drops below beta), but it no
longer passes the margin-inflated number up the tree or into the TT. Exact formula of either source: not stated in the
PR text; the subtraction below is own design.

## Forge fit
LACKS. `bash tools/forge_has.sh 'return value;'` -> `src/search.cpp:1024` (ProbCut exit); the bound is
`probcut_beta = beta + ProbcutMargin - 50 * improving` (`:1001`), qsearch then a depth - 4 search (`:1016-1018`), then
a lower-bound TT store of `value` at depth - 3 and `return value` (`:1022-1024`). Change (ON): before the store,
`value -= probcut_beta - beta` (still >= beta because `value >= probcut_beta`); store and return that value.
Tried neighbours, not this site: RfpReturnBlend (gate 86, H0 at -16.42) blends a static-eval cutoff that fires at many
nodes; FailHighBlend (gates 36 / 42, no decision) blends main-search fail-highs; T04C-01 is the qsearch sibling.
Difference: here the removed amount is exactly the margin the node added itself, and ProbCut exits are rare.

## Expected gain
pawnocchio #57, Threads=1, book not named (missing): STC 10+0.1 Hash 16 MB +2.18 +- 1.85, n=34,816, [0,3], LLR 2.42 of
2.89 (did NOT conclude), penta [76, 4048, 8937, 4276, 71] (own conversion +4.3 nElo); LTC 40+0.4 Hash 64 MB
+2.92 +- 2.05, n=25,426, [0,3] LLR 2.90 (passed), penta [12, 2773, 6930, 2985, 13] (+6.1 nElo).
Reckless #759 (via T04E): STC +2.37 +- 1.76 n=39,016; LTC +3.35 +- 2.23 n=20,920 (corrected by verify, PR body re-read: STC 8+0.08 LLR 3.04 and LTC 40+0.4 LLR 2.89, Threads=1, [0,3], both passed, book missing; its title is "Standardize fail-firm in ProbCut"; whether ProbCut already had a fail-firm form there or only now received the engine's standard one is not stated, so its weight as a second introduction is uncertain).
Two engines with an LTC pass; pawnocchio's STC alone would not meet the bar.
Forge estimate: +0 to +2 Elo **UNPROVEN** (rare exit; the blend family is 0 for 3 in Forge gates).

## Effort
Crew hours: ~1 (1-line option, OFF pins, ON smoke). CPU: one STC SPRT up to 3,000 games = ~6-7 h at 430-502 games/h;
LTC after a pass. GPU: none.

## Test plan
Pre-gate: OFF bench / perft equal to the lock pins, ON bench differs and is stable, 2-minute T1 smoke, mate probe
(no mate score is shifted: `!is_mate_score(beta)` guards entry, keep a clamp below the mate range). Gate route (crew
rule): Threads=1, UHO book, SPRT [0,5] in normalized Elo, alpha = beta = 0.05, pentanomial, cap 3,000 games; capped =
UNPROVEN / no decision, one extension if positive; LTC on pass.

## OFF-by-default design
UCI spin `ProbcutFailFirm`, default 0, range 0-1. At 0 the ProbCut exit stores and returns `value` unchanged, so the
tree, bench nodes and perft equal the lock's. At 1 the stored and returned score is `value - (probcut_beta - beta)`.
