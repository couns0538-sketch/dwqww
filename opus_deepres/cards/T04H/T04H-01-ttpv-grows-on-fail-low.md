# T04H-01-ttpv-grows-on-fail-low: a node that fails low under a ttpv parent is stored as ttpv
Status: COMPLETE

## Source
- Stockfish commit [c02b3a4](https://github.com/official-stockfish/Stockfish/commit/c02b3a4c7a) (2020-08-30), "Add /
  remove leaves from search tree ttPv", PR https://github.com/official-stockfish/Stockfish/pull/3075 . Tests: STC
  https://tests.stockfishchess.org/tests/view/5f49203c3def640786115314 , LTC
  https://tests.stockfishchess.org/tests/view/5f494bea3def640786115336 (TC, book, threads, bounds from api/get_run).
- Later history of the same family (titles + miner numbers only): [e31f97e](https://github.com/official-stockfish/Stockfish/commit/e31f97e)
  (2022-03-19) "Remove ttPv tree shrinking" dropped the "remove" half as a non-regression simplification;
  [1b31e26](https://github.com/official-stockfish/Stockfish/commit/1b31e26) (2025-01-25) "Consider more nodes as ttPv nodes".

## Licence
Stockfish GPL-3.0 (Copying.txt at c02b3a4c7a): ideas only. Read: commit titles and messages, PR 3075 text, two
fishtest run records. No source file or diff was read.

## Mechanism
The message: "add if previous leaf is in search tree and we didn't find a counter move, else remove the position if
the leaf is the last one in search tree". Own words: a node whose parent was a ttpv node (on or formerly on the PV)
and which fails low (no move raised alpha, so the parent's move into it looks good for the parent) is flagged ttpv
when its result is written to the TT; later visits then treat it as a former-PV node. Only this "add" half is
proposed: the "remove" half was dropped by e31f97e. The depth condition of the source is not in any text read; the
start value below is own. (Verify 2026-11-05: the STC run's own note reads "If previous node is ttPv and we find a
good move, consider child node as ttPv", which is this reading; 1b31e26's message says a depth condition existed.)

## Forge fit
`bash tools/forge_has.sh 'tt_pv'` -> 10 hits: `ss->tt_pv` is set once per visit at `src/search.cpp:919` (pv node or
the stored pv bit, `include/forge/search.hpp:73-79`) and written unchanged at `:1214`; nothing updates it after the
move loop. The bit feeds the LMR term `r -= 1` and the capture-LMR exemption (`:1137-1139`), the ProbCut store
(`:1023`) and qsearch (`:793`, `:868`). Change: at the main store (`:1212-1214`) pass `pv = ss->tt_pv || grow`, where
grow = option on, bound == BoundUpper (no move beat alpha, `:1212`), depth >= N, `(ss - 1)->tt_pv` and a real parent
move (`(ss - 1)->current_move` not none: own choice, keeps null-move children out, `:972`). The root's parent is the
sentinel `stack_[3]` (`:1360`, tt_pv false), and the root itself is a pv node, so the root never changes. `ss->tt_pv`
itself is not modified, so the LMR term of the same visit is unchanged; the qsearch store (`:868`) is out of scope
for the first gate. Not in TRIED_GATES; no existing card or table row on ttpv propagation (T04B-04, T04C-02 use the
bit, they do not grow it).

## Expected gain
Source (Stockfish master of 2020-08, NNUE era start, Threads=1, book noob_3moves.epd, logistic SPRT; Elo +- 95 % from
the pentanomial, own arithmetic): STC 10+0.1 [-0.25,1.25] LLR 2.95, 29,968 games, Ptnml 146 / 2,432 / 9,671 / 2,560 /
175 = +2.16 +- 1.80; LTC 60+0.6 [0.25,1.25] LLR 2.96, 84,952 games = +1.17 +- 0.74. Both halves were in that test.
Caution: e31f97e (removal of the "remove" half) STC ~-0.25 n=270,408 / LTC ~+1.45 n=34,368 (non-reg); 1b31e26 (a
later widening) STC ~+0.73 n=82,528 / LTC ~-0.09 n=310,440 / VLTC ~+1.02 n=59,496 (miner numbers, messages not read).
Forge estimate: 0 to +2 Elo **UNPROVEN** (the lock reads the bit in fewer places than the source, so less leverage).

## Effort
Crew 1-1.5 h (option, store argument, OFF pins, ON bench, smoke, one counter). CPU at 430-502 games/h: STC SPRT
[0,5] about 6-14 h, then one LTC; no GPU.

## Test plan
Pre-gate: OFF bench d11/d13/d16/d20/d22 = lock pins; ON bench differs (live); perft unchanged; on the bench set count
stores with the pv bit per 1M stores OFF vs ON (if ON more than doubles it, raise N); mate probe OFF/ON. Gate: UHO
SPRT [0,5] at STC, then LTC; if STC is flat, one SPSA pass of N (forge-o30-spsa) before dropping it.

## OFF-by-default design
UCI spin `TtPvFailLowDepth`, default 0 = off, range 0-20, own start 5 for the first gate. At 0 the store receives
`ss->tt_pv` exactly as the lock does, so every entry, node and bench pin equals the lock. At N > 0 the grow rule above
applies to the main-search store only (no change at ProbCut, qsearch or excluded-move searches, which never store).
