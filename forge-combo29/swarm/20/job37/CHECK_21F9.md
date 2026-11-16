# seat 20 — job 37: confirmation of seat 21's 21-F9 at Threads 1 (the halfmove >= 100 sweep)

Queue entry 4. Seat 21's 21-F9: the halfmove >= 100 root shortcut fires for EVERY counter at or above 100 —
100, 150, 9999, 65536 and up — giving `score cp 0 nodes 0`, and it misses a mate.

Board `6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1` (mate by `d1d8`), `go depth 5`, `Threads 1`, fresh process each:

| halfmove | base 6b98f217 + S14 | PC r15 + PC20 |
|---|---|---|
| 0 | d1d8 / mate 1 / 140 n | d1d8 / mate 1 / 140 n |
| 99 | d1d8 / mate 1 / 140 n | d1d8 / mate 1 / 140 n |
| **100** | **f2f3 / cp 0 / 0 n** | d1d8 / mate 1 / 140 n |
| 101 | f2f3 / cp 0 / 0 n | d1d8 / mate 1 / 140 n |
| 150 | f2f3 / cp 0 / 0 n | d1d8 / mate 1 / 140 n |
| **9999** | **f2f3 / cp 0 / 0 n** | d1d8 / mate 1 / 140 n |
| **65536** | **f2f3 / cp 0 / 0 n** | d1d8 / mate 1 / 140 n |

## Confirmed
1. **21-F9 reproduces exactly at Threads 1.** The threshold is "at or above 100" with no upper bound — 9999 and
   65536 behave identically to 100, so this is a `>=` test, not a counter-wrap effect.
2. **The control is the hm 0/99 rows**: the same harness finds the mate in 140 nodes, so the `cp 0 / 0 nodes` rows
   are the shortcut.
3. **The PC build is correct at every value**, including 65536 — so this whole family is closed on the owner's
   engine, consistent with S-C17/S-C19.
4. Note the node count here is 140, not the 168 I measured at `go depth 6` in earlier jobs — the same board at a
   shallower depth. Depth stated per row; nothing is compared across depths.

## Limits
- One board, one depth (`go depth 5`). I did not test the seed-drawn counters up to 2^31 that seat 21 swept.
- The `65536` row is 65535+1, which also tests the uint16 clamp I recorded in S-F8; it behaves like any large
  counter, so the clamp does not change this outcome.
- Threads 1 only.
