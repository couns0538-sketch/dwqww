# T07-01: time-disadvantage scaling (spend less when own clock is behind)
Status: COMPLETE

## Source
Stockfish PR 7113, commit https://github.com/official-stockfish/Stockfish/commit/5ca4bfe72b (2026-09-09, "Decrease
time usage if engine has time disadvantage"). Logs:
STC https://tests.stockfishchess.org/tests/view/6a8738495b1b38ebda864ed0 ,
LTC https://tests.stockfishchess.org/tests/view/6a8ade7a08c0f6a39c9e79cc , 15+0 non-regression
https://tests.stockfishchess.org/tests/view/6a94002a08c0f6a39c9e8b31 , 40/10 non-regression link printed cut short in
the commit (.../6a967e3408c0f6a39c9e91). Numbers below are from the commit / PR text; the fishtest pages were not
readable (bot check). (corrected by verify: fishtest API get_run of the STC / LTC runs is readable; numbers match.)

## Licence
GPL-3.0 at 5ca4bfe72b (notes/T07/licences.md) -> ideas only. Read: commit title, PR 7113 text with its result blocks.
No source file. The PR names two skip cases (nodestime; cyclic TC at movestogo 1) but no formula.

## Mechanism
Exact source formula not read (licence); this is this worker's design of the idea. Parse the opponent's clock too.
Before the soft limit is fixed, compare own and opponent "time capital" (remaining time plus K moves of increment).
If own capital is below the opponent's, multiply the soft limit by f = clamp(1 - S * (1 - own/opp), Fmin, 1);
otherwise f = 1 (reduce-only, never spend more because the opponent is behind). f = 1 when the opponent's clock is
missing, with movestogo > 0 (the source's own reason: at the last move of a cycle the opponent's clock may already
hold the next cycle), and for movetime / infinite / ponder searches. Hard limit unchanged.

## Forge fit
Lacks it. The parser stores only the side to move's clock and drops the opponent's (src/uci.cpp:99-102);
SearchLimits has no opponent fields (include/forge/search.hpp:19-41). `forge_has.sh 'opponent|time_advantage|
their_time'` -> 0 time hits (2 unrelated: nnue.hpp:12, board.cpp:1018). Change = 2 int fields + 4 parser lines +
one multiply on `soft` in the increment / sudden-death branch (src/search.cpp:1268-1270); cyclic branch 1264-1267
untouched; Forge has no nodestime, so the source's first skip case does not arise.

## Expected gain
Source: STC 10+0.1 +1.13 +- 0.90 (95 %, own pentanomial calc from the printed Ptnml 169/13235/36487/13589/200),
127,360 games, LLR 2.97 (-2.94, 2.94) bounds [0.00, 2.00]; LTC 60+0.6 +1.08 +- 0.69, 191,328 games, LLR 2.94
bounds [0.50, 2.50]; non-regression 15+0 +2.23 +- 1.81 (33,984 games) and 40/10 +1.44 +- 1.51 (47,872 games), both
[-1.75, 0.25]. Book and thread count: not checked (pages unreadable). (corrected by verify: get_run: Threads 1,
book UHO_Lichess_4852_v1.epd at STC and LTC; per the commit the 40/10 run also includes PR 7117's cyclic-TM fix.) Stockfish dev vs master.
Forge estimate: 0 to +2 Elo, centre about +1 - at the job's drop line; kept only because the source passed both STC
and LTC **UNPROVEN**. The crew's logged gates stop at 1000-1500 games ("Cap with no decision", notes/TRIED_GATES.md),
which cannot resolve 1 Elo; a [0,5] SPRT needs about 7-12k games (own estimate from a UHO-type pentanomial variance)
and a true +1 would most likely end H0.

## Effort
Crew 3 h (parser + fields + factor 1 h, OFF inspection + box test 1 h, packaging 1 h). CPU: STC SPRT about 10-12k
games = 10-19 h at the 640-980 games/h seen in D:/o15/reports/gates_20261103.html (corrected by verify: those rates are the older gates vs
h256e12 / ep10; the UHO gates vs the lock (uho*_vs_AL1lp) in that file ran 430.6-455.7 games/h, all *_vs_AL1* rows
430-502, so 10-12k games = about 20-28 h); LTC only after an STC pass. GPU 0.

## Test plan
Pre-gate: bench / perft pins OFF and ON equal the lock - by construction, since bench is depth-limited and never
runs the clock code, so the pins prove nothing about ON. OFF proof = code inspection (f is exactly 1.0 when OFF) plus
a box test: a verify build prints `info string tm soft <ms> f <x>`; replay 20 `go wtime A btime B winc 100 binc 100`
lines with A < B, A = B, A > B, missing btime, movestogo 10: f = 1 except A < B; OFF build prints the lock's soft.
UCI edge cases A1-A3, B4-B8 of notes/T07/UCI_EDGE_CASES.md must keep their lock behaviour. Gate route: UHO SPRT
[0,5] at STC, then LTC; gate_summary must show 0 time forfeits.

## OFF-by-default design
Options (own values, not the source's): TmBehind spin default 0 (OFF) range 0-1; TmBehindScale default 50 (x0.01,
range 0-150); TmBehindMin default 70 (x0.01, 40-100); TmBehindIncMoves default 20 (0-60). OFF: the opponent fields
are parsed but never read, `soft` is the lock's value, so every search with a clock is the lock's; bench pins equal.
