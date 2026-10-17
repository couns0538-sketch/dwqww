# Reference ladder: Stockfish 19 at `UCI_Elo 2800`

Same protocol as `validation/release-6.0.0/`: Stockfish 19 (official
`stockfish-linux-x86-64-universal`), `UCI_LimitStrength=true`,
`UCI_Elo=2800`, `Threads=1`, `Hash=64`; Forge `Hash=64`, one thread;
fastchess, 10+0.1, `8moves_v3.pgn` openings in random order (16 plies),
colour-swapped pairs, `-recover`; 4-core Intel Xeon VM, three games at a time.
Both Forge versions were built from this tree with GCC 13.3, Release,
`-mpopcnt`, and measured back to back on the same machine on the same day.

| Engine | Games | W / L / D | Score | Elo vs SF 19 @ 2800 |
| --- | --- | --- | --- | --- |
| Forge 6.0.0 (commit 68f0112) | 100 | 63 / 22 / 15 | 70.5 % | +151 +/- 61 |
| Forge 6.1.0, one thread | 100 | 67 / 25 / 8 | 71.0 % | +156 +/- 70 |

The two results are statistically identical. At this setting Stockfish plays
at a fixed depth with skill randomisation, so once an engine is clearly
stronger the ladder saturates and cannot separate versions that differ by a
few tens of Elo; the direct matches in `README.md` of this directory are the
relevant comparison between 6.0.0 and 6.1.0. The 6.0.0 record in
`validation/release-6.0.0/` (69.0 % over 200 games on different hardware) is
consistent with the figure measured here.

Game records: `sf-610.pgn` and `sf-base.pgn` were kept out of the repository
for size; the fastchess summaries above are the complete results.
