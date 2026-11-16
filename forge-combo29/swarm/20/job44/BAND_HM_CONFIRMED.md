# seat 20 — job 44: the fifty-move score band 91–99, confirmed with per-run data

Second independent confirmation, `Threads 1`, both builds, **every** halfmove value 85–100, **3 runs per value**,
fresh process per run. Board: `1K6/8/8/3R4/8/8/8/k7 w - - 0 1` (K+R v K, genuinely won for White), `go depth 10`.

| halfmove | base 6b98f217 + S14 | PC r15 + PC20 | nodes base | nodes PC20 | 3-run stability |
|---|---|---|---|---|---|
| 85 | cp 349 | **mate 8** | 29,104 | 35,652 | stable ×3 / ×3 |
| 86 | cp 349 | cp 294 | 37,420 | 87,480 | stable |
| 87 | cp 404 | cp 342 | 12,755 | 67,952 | stable |
| 88 | cp 320 | cp 271 | 192,711 | 178,232 | stable |
| 89 | cp 324 | cp 279 | 972,341 | 306,279 | stable |
| 90 | cp 314 | cp 231 | 946,042 | 930,573 | stable |
| **91** | **cp 0** | **cp 0** | 13,791,896 | 7,251,835 | **stable** |
| 92 | cp 0 | cp 0 | 1,659,545 | 1,459,778 | stable |
| 93 | cp 0 | cp 0 | 1,075,193 | 1,004,522 | stable |
| 94 | cp 0 | cp 0 | 97,276 | 108,603 | stable |
| 95 | cp 0 | cp 0 | 95,459 | 81,364 | stable |
| 96 | cp 0 | cp 0 | 10,002 | 9,329 | stable |
| 97 | cp 0 | cp 0 | 5,013 | 4,729 | stable |
| 98 | cp 0 | cp 0 | 541 | 541 | stable |
| 99 | cp 0 | cp 0 | 200 | 200 | stable |
| **100** | cp 0 | cp 0 | **0** | **200** | stable |

Every one of the 32 cells was identical across its 3 runs.

## What the band actually is, stated precisely
1. **The score collapses from a winning `cp 231`–`cp 349` to exactly `cp 0` at halfmove 91, on BOTH builds, and stays
   0 through 100.** This confirms the band's edge is 91 (not 100) on the engine the PC plays, independently of my
   earlier sampled sweep and of seat 05's original finding.
2. **It is not the root shortcut on the PC build**: at 91 the PC searches **7,251,835 nodes** and the base
   13,791,896 — both are *searching*, so the zero is the in-tree fifty-move horizon, not a 0-node adjudication
   (my S-F16 distinction, now shown across the whole band on both builds).
3. **The one cell where the builds differ is 100**: base reports 0 nodes, PC reports 200. That is the root repair
   visible at the boundary, and it is the only place in the band where the method differs.
4. **Node counts fall monotonically as the counter rises** (13.8 M at 91 → 200 at 99), i.e. the closer the fifty-move
   draw is, the less search is needed to see it. That is textbook and it is a useful sanity signal for the owner.

## The extra finding in this table
**At halfmove 85 the PC build reports `mate 8` where the base reports `cp 349`.** The PC build *proves a forced mate*
that the base tree does not see at that depth — consistent with S-F38 (`MateAlphaGuard`) and with S-F34/S-C18. It
also means the PC's "zero band" is genuine: it finds the mate at 85, loses it to the fifty-move horizon at 91, and
that transition is correct chess because at 91 White cannot both mate and reset the counter in time.

## Rule-1 control
The dead board `8/8/8/8/8/8/7k/K7 w - - 0 1` (K v K) gives `cp 0` at hm 85/91/95/99/100 on both builds — so the
harness *can* see a legitimately-zero score, and the `cp 0` band in the won position is a real transition rather
than a parser giving up. The band's upper edge (85–90 = non-zero) is the internal positive control.

## Honest limits
- One board, `go depth 10`, `Threads 1` only.
- The value at halfmove 100 for the PC build (200 nodes) is stable ×3 but I did not test *why* 200 rather than some
  other small number; it is a searched answer either way.
- `mate 8` at hm 85 is a PC-only result on one board; I am not generalising it.
