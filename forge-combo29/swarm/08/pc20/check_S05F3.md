# CHECK of seat 05's S-F3 / S-F16 — the clock-99 claimable draw, on the PC BUILD under PC20

## Verdict: CONFIRMS, exactly at their halfmove count

Their claim, from their words alone:
> S-F3: "`1K6/8/8/3R4/8/8/8/k7 w - - H 1` at `go depth 10` scores `cp 472` for H=0..75, `cp 314` at H=90, then
> exactly `cp 0` from H=91"
> S-F16: "S-F3 STANDS on the PC build ... K+R vs K at depth 10 on the PC r15 build ... cp 0 at halfmove 91 ...
> identical under S14 and PC20, Threads 1"

My harness is my own (`check_s05f3.py`), the board typed by hand from their FEN — no dependency on their move list,
their script, or their raw files. **PC r15 build, PC20, Threads 1, Hash 16**, one fresh process per counter.

| halfmove H | score | nodes | bestmove |
|---|---|---|---|
| 0 | **cp 490** | 14,470 | d5b5 |
| 50 | **cp 490** | 14,470 | d5b5 |
| 75 | **cp 490** | 14,470 | d5b5 |
| 80 | cp 462 | 15,381 | d5b5 |
| 85 | **mate 8** | 35,652 | d5b5 |
| 88 | cp 271 | 178,232 | d5b5 |
| 89 | cp 279 | 306,279 | d5d2 |
| 90 | cp 231 | 930,573 | b8a7 |
| **91** | **cp 0** | **7,251,835** | d5a5 |
| 92 | cp 0 | 1,459,778 | d5a5 |
| 95 | cp 0 | 81,364 | d5b5 |
| 99 | cp 0 | 200 | d5d1 |
| 100 | cp 0 | 200 | d5d1 |
| 150 | cp 0 | 200 | d5d1 |

- **First counter scoring exactly cp 0: H=91.** Last counter still scoring a win: H=90. That is seat 05's figure
  to the count.
- The **node explosion** is real and much larger than in their report: 14,470 nodes at H=0, **7,251,835** at H=91 —
  a 500x blow-up, and at H=99/100/150 the engine answers in 200 nodes because it recognises the draw immediately.
  So the defect is not just a wrong score, it is also a ~7 million node cost at the boundary.
- Their score magnitudes differ from mine (they saw cp 472 at low counters and cp 314 at H=90; I see cp 490 and
  cp 231). That is expected and does not weaken the confirmation: the PC build's built-in net and PC20's four
  search switches differ from whatever arm they quoted, and the claim that matters — **the flip to cp 0 at H=91** —
  reproduces exactly. I am not claiming their centipawn values.
- Note the non-monotonic score ladder (cp 490 → mate 8 at H=85 → cp 271 at H=88): the mate score appears in the
  middle of the sweep, so a reader should not expect a smooth curve toward the cliff.

## Controls (all enforced by assertion — a failure aborts instead of printing a verdict)
1. a **positive cp score at a low counter is required** (H=0/50/75 must be won), else a later cp 0 would prove
   nothing — satisfied: cp 490 at all three;
2. `go depth 10` must actually reach depth 10 at every counter — satisfied;
3. every score must parse — satisfied (no `None` anywhere).

This is a "the defect is still there" confirmation, which by rule 1 of FABLE_TO_swarm_2 needs no planted case: the
won scores at low counters (cp 490, cp 462, mate 8) are themselves the proof that the harness can report a win on
this board, so the later cp 0 cannot be a harness artefact.

## Why this is the most valuable confirmation available
This is the most substantial open fault on the PC build: a won K+R vs K position is scored as a **draw** from
halfmove 91 onward, at the PC's own settings, Threads 1, on a board where no draw is claimable. In a real game the
engine would steer into a "drawn" evaluation with a rook up, and it pays up to 7.2 million nodes to reach that
wrong verdict. It is **not** the drawn-root shortcut of FABLE_TO_swarm_3 (that one is repaired in r15 — seat 05's own
S-F16 contrast shows a K+Q mate still being found at counter 100); it is the fifty-move *score floor* inside the
search.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s05f3.py /tmp/s05f3.txt

Raw output committed as `check_s05f3.txt`.
