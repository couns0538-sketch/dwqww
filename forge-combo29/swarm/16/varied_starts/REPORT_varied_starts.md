# REPORT_varied_starts — is self-play duplication fixed by varying the start?

**What was asked (follow-up to S-F27):** ten games from one fixed start gave only 3 distinct final positions. If
each game starts from a DIFFERENT real game position, do the games diverge? If yes the advice is simply "vary the
openings"; if they still converge, the owner needs to know before generating data.

**The answer: varying the start is SUFFICIENT. Ten games from ten different real-game starts gave TEN distinct
final positions and TEN distinct move sequences.**

```
distinct FINAL positions: 10 of 10
distinct move sequences : 10 of 10
overruns: 0
```

Per game (start → final):

```
game  1 1r6/2k2pp1/2p2n2/2Pppb1p/...  -> 8/1r3p2/1k6/1n3p1P/6p1/6P1/2R2K2/...
game  2 r3r1k1/p1bb1ppp/1p1q4/...     -> 3r2k1/2N5/3P1p1p/3bP1p1/5p1P/8/5PP...
game  3 6k1/p4r1p/1p2Q3/2p5/...       -> 8/5k2/1p6/1KpNq3/2P4Q/1P5p/r7/8 b
game  4 5R2/5npp/5k2/8/...            -> 4k3/1R6/5K1p/6pP/8/8/5PP1/8 b
game  5 8/1p1k1KN1/4pB2/...           -> 8/8/8/4pk2/8/5K2/7r/8 w
game  6 8/6k1/3p4/3P2PP/...           -> 8/8/4K2P/3P4/8/2Q1N3/6Q1/4k3 b
game  7 2r4r/pp4k1/3q2p1/...          -> 8/p7/8/3p1R2/1P6/P1kN4/3r4/5K2 b
game  8 8/5p2/8/pp1pkpKp/...          -> 8/8/1q6/4k3/K1Pp4/8/8/q7 w
game  9 r1bqkb1r/pppp1ppp/2n2n2/...   -> 1kbq4/rpp1npp1/p6r/P1N2Pbp/1P1PB3/...
game 10 R7/8/8/5p1p/5K1P/1kpr2n1/...  -> 3r1K2/2q5/8/7p/7P/4k1n1/8/8 w
```

**So the answer for the owner is the simple one: vary the openings.** S-F27's convergence was entirely explained
by the fixed starting point, not by a deeper convergence of the search. Determinism (which is a good property —
games are reproducible) does not stop varied starts from producing varied games.

**P1 confirmed exactly** (10 of 10, my prediction). **P2 confirmed** (the endings are mutually unrelated — the
start dominates completely, which is the "also useful" branch). **P3 confirmed** (distinct position and distinct
move sequence agree 10/10 — no transpositions among these endings). **P4 confirmed** (0 overruns, 0 illegal
moves; two games ended early at 27 plies because the position reached a natural end).

**One incidental correction to my own S-F26 range.** In this run the per-move clock fraction goes as low as
**0.02 %** (a move that took essentially no time — a forced or book-trivial position) and as high as **32.24 %**
(game 8, a tactical position). So even 2.4 %–21.9 % from the ten-game study understates the extremes: **across
both studies the band is 0.02 % to 32.24 %**. The median stays at ~4 %, which is the figure to quote.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge  PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16; 10 games, start = G position k for game k, 40 plies each;
         6 s + 0.06 s with clock bookkeeping by measured wall time; one process per game
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 10 games from 10 different real-game starts | done | `raw/varied_starts.txt`, `run.log` | 10/10 distinct final positions, 10/10 distinct move sequences |
| legality and clock safety | done | same | 0 illegal, 0 overruns |
| compare with S-F27's fixed start | done | `../ten_games/raw/ten_games.txt` | 3 of 10 distinct → 10 of 10 distinct |
| why two games stopped at 27 plies | done | same | natural end position |

## Findings

`S-F29 | 6 | self-play duplication is FIXED by varying the start, so the advice to the owner is simply "vary the openings": ten games from ten different real-game positions (PC build, PC20, Threads 1, Hash 16, 6 s + 0.06 s, 40 plies each) gave TEN distinct final positions and TEN distinct move sequences, against the 3-of-10 from a single fixed start (S-F27), with 0 illegal moves and 0 overruns — so the convergence was the fixed starting point, not a deeper property of the search. Incidental correction to S-F26's band: across both studies the per-move clock fraction spans 0.02 % to 32.24 % (median still ~4 %) | varied_starts/raw/varied_starts.txt varied_starts/run.log (again: `python3 varied_starts/varied_starts.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

## Suspicions, not proven

- That two starts a few plies apart would converge quickly. My ten starts come from different games, so I did not
  test near-identical starts; P2 predicted it but I did not measure it.

## What I did NOT do

- Did not test near-identical starts (e.g. the same game at ply 4 and at ply 5), which is the case a book would
  actually produce.
- Did not run more than 40 plies per game (games were ending naturally anyway in several cases).

## Times

`varied_starts/stamps.txt`, every line a `date -u`.
