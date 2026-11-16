# REPORT_job6 — perft 4 at the DIVIDE level on 200 G positions (real-game material)

## What was asked
The coordinator's job 1 for the remaining hours: the depth-4 divide check was clean on the synthetic
R set, so extend it where it is cheap to **200 G positions**, because G is real-game material and R is
synthetic. If that is also clean, say the move-generation chapter is fully closed.

## The answer
**Clean on all three runs.** 200 G positions, **5,107 root moves compared per run, 0 differing** —
base build (Threads 1, Hash 16), PC r15 (Threads 1, Hash 16), and PC r15 under PC20. Zero missing root
moves, zero extra root moves, zero wrong counts, and both totals cross-checks held 200/200.

## The move-generation chapter is closed — with the limits stated
Across jobs 1, 1b, 2, 3, 4 and 6, move generation agrees with python-chess on:

| evidence | material | depth | granularity | result |
|---|---|---|---|---|
| job 1 | 5,000 synthetic R (seed 1301) | 1–4 | totals | 20,000 pairs, 0 differences |
| job 1b | 5,000 synthetic R (seed 1311) | 1–4 | totals | 20,000 pairs, 0 differences |
| job 2 | 494 selected special positions | 1–4 | totals + divide at d2 | 1,976 pairs 0; 494 divides 0 |
| job 3 | 230 (200 R + 30 G) | 4 **and 5** | totals | 460 pairs, 0 differences |
| job 4 | 200 synthetic R | 4 | **divide** | 5,182 root moves, 0 differences (3 builds) |
| job 6 | 200 **real-game G** | 4 | **divide** | 5,107 root moves, 0 differences (3 builds) |

So: two independent synthetic samples, real-game material, selected edge-case positions, depths 1 to
5, and at the divide level on both material types and all three build/settings combinations. I am
prepared to say **the move generator matches python-chess on everything I could measure**.

What "closed" does NOT cover, stated plainly:
- **Depth 5 is totals-only.** The divide at depth 5 was not run (the coordinator agreed it is not
  worth the cost); a compensating error at depth 5 that cancels in the total would escape. The divide
  evidence covers depths 2 and 4.
- **python-chess is the only oracle.** If both implementations shared a misreading of a rule, every
  comparison here would still pass. I have not cross-checked against a published perft table except
  at startpos and Kiwipete in job 1's control.
- **Positions python-chess refuses but the engine accepts** (area 1's ground: adjacent-digit ranks,
  impossible castling rights) cannot be tested this way at all, because there is no reference value.
- **Sampling.** R is my generator's output and under-represents sparse endgames; G is 353 engine-game
  positions and I sampled 200 of them by stride.
- **Move generation ≠ move choice.** This says the legal move lists are right, not that the search
  picks the right one.

## How sure
High for what it claims, because the harness is proven able to fail on THIS material:
`CONTROL_DIVIDE.md` was re-run on the G set before measuring — control position
`1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1` (37 root moves, total 743,255):

| plant | total unchanged? | caught |
|---|---|---|
| P0 identity | yes | correctly **not** flagged |
| A compensating `b8a8 +1`, `b8b3 -1` | **yes (743,255 vs 743,255)** | **CAUGHT** |
| B missing move (`g7g6` deleted) | no | **CAUGHT** |
| C extra move | no | **CAUGHT** |

## How the 200 were chosen
Not the first 200 of the file — that could cluster. I took a **fixed stride** (every 353/200 ≈ 1.765th
line) so the sample spans all 353 and keeps the side-to-move and piece-count proportions close to the
full file: white 89/200 vs 165/353, black 111/200 vs 188/353. Recorded in `prediction.txt` before
measuring.

## Prediction vs result
| predicted | predicted value | actual | verdict |
|---|---|---|---|
| positions differing | 0 on all three runs | 0, 0, 0 | held |
| root moves per run | 4,000–12,000 | 5,107 | held |
| per-divide sum equals engine total | 200/200 | 200/200 ×3 | held |
| engine total equals python total | 200/200 | 200/200 ×3 | held |
| a difference would involve castling | — | no differences | held trivially |

## Settings and build
Threads 1 and Hash 16 in every regime (swarm rule on scores); perft is single-threaded anyway, and it
is stated so the table cannot be misread. Base build sha256 `e06310ec...`; PC r15 sha256
`068f0927...` built with `-DFORGE_MATE_ALPHA_GUARD=1`. Option names validated against each exe's own
`uci` list before sending.

## Findings
- S-F8: at the **divide** level on **200 real-game G positions**, perft 4 equals python-chess —
  5,107 root moves, 0 differing — on base (Threads 1/Hash 16), PC r15 (Threads 1/Hash 16) and PC r15
  under PC20. With S-F5 (synthetic R, 5,182 root moves, same three builds) this closes the
  move-generation chapter at depths 1–4 at divide granularity, subject to the stated limits
  (depth 5 totals-only; python-chess is the only oracle; refused-FEN positions untestable this way).
  Reproduce: `cd forge-combo29/swarm/13/job6 && python3 control_divide.py G200_spread.fens && python3
  divide_perft4.py ~/b/pc/forge G200_spread.fens /tmp/g.json PC20`.

## Suspicions, not proven
- None about the engine.

## What I did NOT do
- Depth-5 divide (justified: cost, and the coordinator agreed).
- Positions python-chess refuses (needs a different oracle).
- Cross-check against a third perft implementation.

## What I am NOT sure about
- The identical 5,107 root-move count across all three runs is expected (perft ignores settings), and
  is a consistency signal rather than independent evidence — the independent evidence is python-chess
  being a different implementation.
- G's 353 positions come from engine games at some unknown time control and skill level; they are
  real-game material but not the owner's match games.

## Times
See `stamps.txt`.

## Last command output

```
$ ls
base_none.json
base_none.json.engine_raw.json
base_none.log
CONTROL_DIVIDE.md
control_divide.py
divide_perft4.py
G200_spread.fens
G_all.fens
pc_none.json
pc_none.json.engine_raw.json
pc_none.log
pc_pc20.json
pc_pc20.json.engine_raw.json
pc_pc20.log
prediction.txt
REPORT_job6.md
set_G.epd
stamps.txt
status.txt
```
