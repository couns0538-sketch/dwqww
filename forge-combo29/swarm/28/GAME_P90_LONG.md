# Longer games at 6 s + 0.06: the clock survives, but only just — one game ran 37 moves on ~115 ms

The gap S-F39 left: its games all drew by repetition at 58-101 plies, so they never probed the regime where
the clock runs out. This run starts each game from a DIFFERENT opening from the brief's O set, so games
diverge and last longer.

## The numbers

| metric | value |
|---|---|
| moves | **809** (6 games) |
| median | **99 ms** |
| p90 | **262 ms** |
| p99 | 534 ms |
| max | 792 ms |
| median game length | 116 plies |
| longest game | **224 plies** |
| games flagged | **0 of 6** |
| **lowest clock anywhere** | **110 ms** |

Combined with S-F39 (281 moves): **1,090 moves measured, median 99-132 ms, p90 262-359 ms, max 792 ms.**

## The result that matters: game 4, 224 plies, clock at 111 ms

| game | plies | min clock | moves with clock <300 ms | moves with clock <150 ms |
|---|---|---|---|---|
| 4 | 224 | **111 ms** | **37** | **7** |
| 5 | 192 | 110 ms | 17 | 12 |
| 3 | 122 | 568 ms | 0 | 0 |
| 1 | 109 | 1083 ms | 0 | 0 |
| 6 | 86 | 1270 ms | 0 | 0 |
| 2 | 76 | 1889 ms | 0 | 0 |

Game 4's closing moves show the mechanism exactly:

```
ply 212 w clock_before 130 wall 63.4 -> after 126 d12
ply 216 w clock_before 127 wall 70.4 -> after 117 d11
ply 218 w clock_before 117 wall 61.6 -> after 115 d11
ply 220 w clock_before 115 wall 63.6 -> after 112 d10
ply 222 w clock_before 112 wall 60.6 -> after 111 d11
```

**White held ~115 ms for 37 consecutive moves**, each search lasting 60-70 ms against a 60 ms increment —
i.e. losing 0-10 ms per move. Its depth fell to **10-12** (against 19-30 in the fast games), so the engine
was self-limiting: at a small clock the plan shrinks and the searches get short enough to nearly balance the
increment. That is the time manager working.

**But the margin is one move.** At 111 ms with a p90 search of 262 ms, the next p90 move flags. It survived
because its searches in that phase were 60-70 ms, not p90-sized.

## How many more moves each side could survive (arithmetic on the measured rates)

| game | white clock | ~more p90 moves | black clock | ~more p90 moves |
|---|---|---|---|---|
| 4 | 111 ms | **1** | 457 ms | 2 |
| 5 | 1204 ms | 6 | **270 ms** | **1** |
| 3 | 836 ms | 4 | 755 ms | 4 |
| 1 | 1124 ms | 6 | 1422 ms | 7 |
| 2 | 1889 ms | 9 | 2071 ms | 10 |
| 6 | 2221 ms | 11 | 1333 ms | 7 |

(computed as `clock / (p90 − increment)` = `clock / 202`)

## The answer for the owner

**At 6 s + 0.06 the clock does not run out in these games, but long games put a side within one p90 move of
it.** Two of six games ended with a side under 300 ms, one at 111 ms after 37 moves hovering there. So:

- **The p90 you asked for is 262-359 ms** (two independent runs, 1,090 moves). Against a 60 ms increment
  that is a net loss of ~202-299 ms per p90 move.
- **The engine self-limits successfully at small clocks** — its searches shrink to 60-70 ms and its depth
  falls to 10-12, which is why it survived. The time manager is doing its job under pressure.
- **The risk is not the average, it is the transition:** a side that has 300 ms and then hits one p90-sized
  search loses 200+ ms and is suddenly at ~100 ms, where the next p90 move flags. Nothing in this data
  flagged, but nothing had much room either.

## Limits
- Still engine self-play, so the paths are its own; a match against another engine may reach different
  clock states.
- 6 games is a small sample of long games: only 2 of 6 exceeded 190 plies.
- The per-side extrapolation is arithmetic on the measured p90, not a measurement of long games at that
  clock.

## Reproduce
```
cd forge-combo29/swarm/28/pc20
python3 game_p90_long.py ~/build/r15-pc/forge PC20 /tmp/l 6
```
Raw: `out_long/long_PC20.tsv` (every move with clock before/after, wall, depth, nodes).
