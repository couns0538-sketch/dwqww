# T04-03: Null-move margin discount when the child ply produced few cutoffs
Status: COMPLETE

## Source
- Caissa commit e53fe6e "Search: NMP eval margin discount on cutoff count" (2025-08-05), two OpenBench blocks in the
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
(`--grep 'nmp|null'` = 0 rows) nor in R15 / FB2-J3.

## Expected gain
Source: Caissa, OpenBench, 1 thread: LTC 60+0.6, Hash 128 MB, SPRT [0, 3], n=10,918 (W 2568 L 2381 D 5969)
+5.95 +- 3.14, LLR 2.95; STC 10+0.1, Hash 16 MB, SPRT [0, 2], n=61,474 (W 14682 L 14329 D 32463) +2.00 +- 1.41,
LLR 2.95. Book: not stated. Larger at LTC than at STC: a TC-scaling term.
Forge estimate: +0 to +2 Elo at STC, +1 to +4 at LTC **UNPROVEN** (Forge's NMP has no cut-node condition, Caissa's
has; the discount acts on a different base rule).

## Effort
Crew 2 h (field + clear + increment + option, OFF identity, ON bench, smoke). CPU: STC SPRT [0, 5] then LTC; given
the source's TC trend, the LTC run is the deciding one. No GPU.

## Test plan
Pre-gate: OFF bench pins d11-d22 equal the lock; ON bench live; null-move try / cutoff counts per 1M nodes OFF vs ON
(the lock already counts `null_tries_` / `null_cutoffs_`); zugzwang probe set unchanged in result. Gate: UHO SPRT
[0, 5] at STC, then LTC (do not stop after an STC H0 inside +-2 Elo; the source gain was 3x larger at LTC).

## OFF-by-default design
UCI spins `NmpFewCutoffs` default 0 (0 = off; own start 3, range 1-6: counter at or below it triggers the discount)
and `NmpFewCutoffsDiscount` default 0 (own start 24 cp = one ply of the lock's own NMP slope, range 0-72) lowering the
`static_eval` condition at `:965`. The new counter is written but never read at the defaults, so the tree and the
bench pins equal the lock (prove with the pins; check nps ABBA if the extra store shows).
