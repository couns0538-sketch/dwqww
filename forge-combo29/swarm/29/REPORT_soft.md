# REPORT_soft - NEW AREA: `go softnodes N` on the PC build under PC20, Threads 1

what was asked (file 6, point 4): on the PC build under PC20 at Threads 1, is `go softnodes N` deterministic run to
run; does it stop at a finished depth; and how far past N does it go.
the answer: **deterministic — yes, 24 of 24 repeated runs identical on all three numbers. Stops at a finished depth —
yes, 9 of 9 cases reproduce exactly under a plain `go depth D`. Overshoot — median 1.20–1.42x N, worst 3.01x N over
48 runs, and the documented 4x hard stop never bound.**
how sure: high. Fresh process per run (seat 10's cold rule), every run drained to `bestmove`, and any run producing
no `info depth` line aborts rather than being counted.

## why this is the right area for me
File 6 says a find on the PC's real path counts most, and names `go softnodes 2000` as what the PC's self-play uses.
My profiling work is about where time goes in exactly that build and settings, so this is the highest-value area
left for me after finishing area 9's own jobs.

## Q1 - determinism (the one that MUST hold)
| N | repeats | distinct (depth, nodes, score, move) tuples |
|---|---|---|
| 2000 | 3 per position x 2 positions | 1 |
| 20000 | 3 x 2 | 1 |
| 50000 | 3 x 2 | 1 |
| 250000 | 3 x 2 | 1 |

**24 of 24 runs identical.** Command: `python3 soft/softnodes_test.py ~/build/pc/forge soft/pos2.txt 3`
(`soft/raw_softnodes.txt`).

## Q2 - does it stop at a FINISHED depth?
Tested rather than assumed: for each `go softnodes N`, take the depth D it reported, then run `go depth D` in a
FRESH process and compare score, move and full PV. If softnodes stopped mid-iteration, the two would differ.

| position | N | softnodes depth/nodes/score/move | `go depth D` | |
|---|---|---|---|---|
| startpos | 2000 | 7 / 4121 / cp 32 / d2d4 | identical | MATCH |
| startpos | 20000 | 12 / 21600 / cp 25 / d2d4 | identical | MATCH |
| startpos | 50000 | 15 / 78579 / cp 21 / d2d4 | identical | MATCH |
| kiwipete | 2000 | 5 / 2341 / cp -170 / e2a6 | identical | MATCH |
| kiwipete | 20000 | 9 / 23992 / cp -140 / e2a6 | identical | MATCH |
| kiwipete | 50000 | 11 / 57518 / cp -99 / e2a6 | identical | MATCH |
| endgame | 2000 | 8 / 4001 / cp 210 / b4f4 | identical | MATCH |
| endgame | 20000 | 12 / 24418 / cp 171 / b4f4 | identical | MATCH |
| endgame | 50000 | 14 / 72388 / cp 216 / b4f4 | identical | MATCH |

**9 of 9 mid-iteration stops: 0.** `soft/raw_depth_completion.txt`.

## Q3 - how far past N
12 positions from my seeded random-game set, four N values the PC actually uses (48 runs):

| N | runs | nodes/N min | median | max | runs over 4x |
|---|---|---|---|---|---|
| 2000 | 12 | 1.12 | 1.42 | 2.79 | 0 |
| 20000 | 12 | 1.04 | 1.20 | 2.30 | 0 |
| 50000 | 12 | 1.01 | 1.20 | 3.01 | 0 |
| 250000 | 12 | 1.01 | 1.22 | 1.56 | 0 |

The engine also prints its own confirmation, `info string softnodes nodes <n>`, which matches the `info depth` node
count in every run I read (e.g. `softnodes 2000` → `info string softnodes nodes 4121`).

**The 4x hard stop never bound (0 of 48).** So on realistic positions the iteration-completion rule alone contains
the overshoot well inside 4x; the hard stop is a backstop that these searches never reach. Worst observed: 3.01x at
N=50000 (position 9, depth 11, 150,599 nodes) — a one-instant jump from depth 10 to 11, which is the expected
mechanism (a new iteration must finish whatever it costs).

## findings
| id | area | one sentence | file | type |
|---|---|---|---|---|
| 29-F22 | softnodes | `go softnodes N` on the PC r15 build (PC20, Threads 1, Hash 16) is fully deterministic: 24 of 24 repeated fresh-process runs gave the same depth, node count, score and move across N = 2000/20000/50000/250000. | `soft/softnodes_test.py`, `raw_softnodes.txt` | NEW |
| 29-F23 | softnodes | `go softnodes N` genuinely stops at a COMPLETED iteration: in 9 of 9 cases, a fresh `go depth D` at the depth softnodes reported reproduces its score, move and full PV exactly, so no mid-iteration truncation occurs. | `soft/depth_completion.py`, `raw_depth_completion.txt` | NEW |
| 29-F24 | softnodes | Overshoot of `go softnodes N` on realistic positions is bounded by iteration granularity, not by the 4x hard stop: median 1.20-1.42x N and worst 3.01x N over 48 runs at N = 2000/20000/50000/250000, with the 4x stop never binding (0 of 48). | `soft/overshoot.py`, `raw_overshoot.txt` | NEW |

## suspicions, not proven
- The worst case (3.01x) is a single depth jump. On a position where one iteration costs >3x the previous, the
  overshoot would grow; whether any real PC position reaches 4x I did not find, and 48 runs is not a proof of never.
- Overshoot at N=2000 has the widest spread (1.12–2.79x) because a fixed 2000-node budget is a small fraction of
  even the first few iterations on a tactical position.

## what I did NOT do
- Not the clock regime (`6s + 0.06`) or `go nodes 20000/50000/250000`, which file 6 also names as PC-path. Those are
  the natural next jobs.
- Not positions from the owner's real game files (I do not have them); mine are seeded random games.

## what I am NOT sure about
- Whether determinism holds with N values between my four samples, or under S14 instead of PC20. I tested the four
  values file 6 names, under PC20.

times: see `soft/stamps.txt`.
