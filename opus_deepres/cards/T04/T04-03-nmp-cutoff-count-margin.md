# T04-03: Null-move margin discount when the child ply produced few cutoffs
Status: COMPLETE (review: KEEP-WITH-FIX by the second vote - source-faithful ON form added, estimate narrowed)

## Source
- Caissa commit e53fe6e "Search: NMP eval margin discount on cutoff count" (2026-08-05; corrected by verify: was 2025-08-05, committer date 2026-08-05, author 2026-08-04), two OpenBench blocks in the
  message (LTC first, then STC), diff read (`src/backend/Search.cpp`, `Search.hpp`):
  https://github.com/Witek902/Caissa/commit/e53fe6ebf2a48af382fd5d3355e36e3ef63aa173 (LTC test link in the message:
  https://furybench.com/test/6982/)

## Licence
Caissa @57cae7ef71: MIT (notes/T04/licences.md). Copy allowed with notice; nothing copied, own words, own constants.

## Mechanism
Each stack frame counts the beta cutoffs that happen at its ply; a node clears the counter two plies below itself
when it starts, so at null-move time the counter one ply below holds the cutoffs that the earlier siblings' children
produced since the parent started. Few cutoffs there means the position is not an "easy" one where replies refute
quickly; the null-move eval threshold is then lowered by a fixed discount, so null move is tried more often there.

## Forge fit
`bash tools/forge_has.sh 'cutoff_count'` -> `src/search.cpp:905` clears `(ss + 1)->cutoff_count` at node entry,
`:1180` counts cutoffs, `:1145` uses it in LMR. Because the lock clears the child counter at its own entry, that
counter is always 0 when null move runs (`:965`), so the Caissa signal does not exist in Forge yet: it needs a second
counter with the clear-two-plies-ahead rule (the LMR counter must stay as it is, or LmrCutoffThreshold changes
meaning). NMP threshold today: `eval >= beta` and `static_eval >= beta - 24*depth + 180` (`:965`). Lines to touch:
~10 (one stack field, its clear at entry, its increment next to `:1180`, one margin term). Not in the tried gates
(`--grep 'nmp|null'` = 0 rows) nor in R15 / FB2-J3. (review fix, second vote: the second counter's slot ss+2 needs no
stack growth - the lock already writes `(ss + 2)->killers` at node entry (`:907`); Caissa had to add 2 entries.)
(review fix, second vote: in Caissa @e53fe6e the NMP test is `eval >= beta + margin` on the CORRECTED eval AND raw
eval >= beta, margin (depth < 4 ? 16 : 0) - (few cutoffs ? 19 : 0), so its discount is live at every depth >= 4 where
the corrected eval sits just below beta while the raw eval is >= beta; the lock's `static_eval >= beta - 24*depth +
180` binds only at depth 3-7 (NullMoveMinDepth 3; from depth 8 `eval >= beta` binds) - a different rule.)

## Expected gain
Source: Caissa, OpenBench, 1 thread: LTC 60+0.6, Hash 128 MB, SPRT [0, 3], n=10,918 (W 2568 L 2381 D 5969)
+5.95 +- 3.14, LLR 2.95; STC 10+0.1, Hash 16 MB, SPRT [0, 2], n=61,474 (W 14682 L 14329 D 32463) +2.00 +- 1.41,
LLR 2.95. Book: not stated. Larger at LTC than at STC: a TC-scaling term (verify note: the 95 % intervals overlap, LTC 2.81-9.09 vs STC 0.59-3.41, and both runs stopped at an SPRT bound, so the TC trend is suggestive, not shown).
Forge estimate: 0 to +2 Elo for each ON form (source-faithful and shallow-term) **UNPROVEN** (Forge's NMP has no
cut-node condition, Caissa's has; review fix, second vote: the former "+1 to +4 at LTC" TC-scaling estimate is dropped -
the shallow-term form is live at depth 3-7 only, a share that shrinks at LTC).

## Effort
Crew 2 h (field + clear + increment + option, OFF identity, ON bench, smoke). CPU: the crew gate runs about 1,000 games/h at concurrency 8 (R7 J4 measurement, 28.3 s per STC game), so a 3,000-game STC cap is about 3 h of the gate PC; an LTC at k times the STC time costs about k times that. STC SPRT [0, 5], then LTC; given the source's TC trend, the LTC run decides (review fix, critic / T04 verifier: STC is the no-loss check; the source's TC trend is suggestive only). No GPU.

## Test plan
Pre-gate: OFF bench pins d11-d22 equal the lock; ON bench live; null-move try / cutoff counts per 1M nodes OFF vs ON
(the lock already counts `null_tries_` / `null_cutoffs_`); zugzwang probe set unchanged in result. Gate: UHO SPRT
[0, 5] at STC, then LTC (do not stop after an STC H0 inside +-2 Elo; the source gain was 3x larger at LTC).

## OFF-by-default design
UCI spins `NmpFewCutoffs` default 0 (0 = off; own start 3, range 1-6: counter at or below it triggers the discount)
and `NmpFewCutoffsDiscount` default 0 (own start 24 cp = one ply of the lock's own NMP slope, range 0-72) lowering the
`static_eval` condition at `:965` (verify note: the Caissa diff lowers the margin of its `eval >= beta + margin` test, which can go below beta; this design keeps the lock's `eval >= beta` and lowers only the `static_eval` term, a narrower change than the source's, so its number transfers less directly). The new counter is written but never read at the defaults, so the tree and the
bench pins equal the lock (prove with the pins; check nps ABBA if the extra store shows).
(review fix, second vote: add spin `NmpFewCutoffsForm` default 1, range 1-2 - 1 = the source-faithful form: when the
few-cutoffs signal holds, `eval >= beta - NmpFewCutoffsDiscount` is enough provided `ss->raw_eval >= beta`
(include/forge/search.hpp:271), the lock's static term kept; 2 = the shallow-term form above. Read only when
NmpFewCutoffs > 0, so OFF stays the lock; gate form 1 first, form 2 as the second value.)
