# REPORT — seat 25, area 5, job 1 (PV legality and mate scores)

## What was asked
Every search of a rows run on O and G at depth 12, S14: is the LAST `info ... pv` line legal when played by
python-chess, and does a `mate N` score match its PV length (2N-1 plies for N>0, 2|N| for N<0)? Plus one control
that a PV with an illegal last move is caught.

## The answer
553 searches ran (200 on O, 353 on G). All 553 final PVs were fully legal. 10 of the 553 carried a `mate N` score.
Nine of those ten had a PV of exactly the right length and ended in real checkmate. ONE did not:
`8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` reported `score mate -12` with an 18-ply PV that ends 14 plies short of a
24-ply mate and is not checkmate at all. It reproduces exactly and deterministically.

## How sure
Very sure of the observation (deterministic, reproduced in a fresh process, raw lines committed). Not sure of the
cause: I did not prove which line of the search produces it. The score is provably WRONG, not merely odd: at
depth 28 the same root reports `mate -4`, and that 8-ply PV verifiably ends in checkmate.

## Honesty numbers (this build, before the job)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four match. See `../HONESTY.txt`.

## What was done

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction written and pushed alone | done | `PREDICTION.md` (commit b2daa7c03) | committed before any measuring command |
| 200 searches on O at depth 12, S14 | done | `../positions/set_O.fens`, `G_d12.jsonl` (O run raw is summarised in `check_O_d12.txt`; the O raw jsonl was not committed — see "what I did NOT do") | 200 records, 0 illegal PVs, 0 mate scores |
| 353 searches on G at depth 12, S14 | done | `G_d12.jsonl`, `check_G_d12.txt` | 353 records, 0 illegal PVs, 10 mate scores, 1 wrong |
| checker control (planted illegal last move) | done | `control.txt` | caught exactly 1 of 1: `bad_move=e1e8@11` |
| re-run the one bad position at depths 10..16 with S14, fresh process each | done | `mate_pv_probe_s14.sh`, `mate_probe_s14.txt` | reproduces `mate -12`/18 plies at depths 12, 13; also at 14, 15, 16 the depth-12 line repeats identically |
| same position, `go depth 18..28` | done | `mate_deep.sh`, `mate_deep.txt` | converges to `mate -4` (8 plies) and it verifies as real mate |
| verify the depth-18 and depth-28 lines end in checkmate | done | `verify_pv_line.py` (run output in `mate_probe_s14`/`mate_deep` and this report) | both end in checkmate |
| independent python-chess exact-mate search | partly | `true_mate3.py`, `true_mate3.txt` | proved no mate inside 14 plies; timed out at 16 plies (6.65M nodes in 171 s). Did not finish the exact proof |

## Findings

### S-F1 (NEW) — a mate score whose PV is 6 plies short and does not end in checkmate
`8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`, depth 12, S14, Threads 1, Hash 16:
```
info depth 12 seldepth 27 score mate -12 nodes 19197 nps 3199500 hashfull 4 time 6 pv c2c3 d2d1q c3b2 e4e3 b2a2 d1c2 a2a1 c2c1 a1a2 c1c4 a2b2 c4d4 b2c1 d4a1 c1c2 a1d1 c2b2 e2d3
```
The PV is 18 plies = mate in 9. `mate -12` needs 24 plies. The position after the PV is
`8/8/1p6/8/p7/3kp3/1K6/3q4 w - - 14 10`, is_checkmate = False, is_stalemate = False. So the score is wrong
on its own line, whichever way you read it (too long by 6 plies, or a mate score with a non-mate line).

Shows again (one self-contained command; output lands in `repro_out.txt`):
```bash
bash forge-combo29/swarm/25/job1/repro_mate12.sh /path/to/forge /tmp/repro_out.txt
```
which prints exactly that `info depth 12 ... score mate -12 ...` line and `bestmove c2c3`, and then:
```bash
python3 forge-combo29/swarm/25/job1/verify_pv_line.py \
  '8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1' \
  'c2c3 d2d1q c3b2 e4e3 b2a2 d1c2 a2a1 c2c1 a1a2 c1c4 a2b2 c4d4 b2c1 d4a1 c1c2 a1d1 c2b2 e2d3'
```
prints `is_checkmate: False`, legal moves left 2, `RESULT: NOT checkmate` (saved as `repro_verify.txt`).

Beyond the known list: the FABLE_TO_swarm_1 known items are about FEN trust and UCI prefix keeping. This is a
search-reporting fault, so it is not a repeat of any of them.

### S-F2 (NEW, weaker) — the same root's mate score jumps 12 -> 7 -> 6 -> 4 as depth grows
At depths 12..16 (S14) the root reports mate -12, then mate -9 (depth 14), mate -6 (depth 15/16); at depth 18 it is
mate -5; at depth 22..28 it is mate -4. A mate score that large and that unstable usually means the real distance
is much smaller and the search finds it only when it gets deep enough. I did NOT prove the exact distance (see
"what I am NOT sure about"). Shows again: `mate_deep.txt` and `mate_probe_s14.txt`.

## Suspicions, not proven
- The 18-ply PV looks like a *truncation* of a longer line: it ends on a quiet king move with black still to move.
  A PV that is cut short of a mate score's own distance is what a PV array that stopped growing would look like.
- The most likely place is the mate-band arithmetic: `score_to_tt`/`score_from_tt` shift by ply against
  `MateInMaxPly = MateValue - MaxPly` (src/search.cpp:179-198), and `format_score` converts a stored mate score
  back to a move distance with `(distance+1)/2` (src/search.cpp:272-279). A score read back from the TT at a
  different ply than it was stored can print a mate distance the PV cannot support. I have NOT shown this is the
  path taken here; it is a hypothesis with a location, not a result.
- I did not test whether the `mate` value is wrong or only the printed PV; a `go depth 12` with MultiPV 1 has no
  way to separate them.

## What I did NOT do
- I did not commit the O raw jsonl (200 records, ~1.5 MB); the O result is only in `check_O_d12.txt`. The G raw
  jsonl IS committed (`G_d12.jsonl`). This is a real gap in the evidence for O.
- I did not finish the independent exact-mate proof (`true_mate3.py` timed out at 16 plies).
- I did not test a patched engine, and I did not bisect which search change (IirDepth, SingularDepth, the LMR
  settings of S14) triggers the bad score as opposed to the default settings.
- I did not run this position under a sanitizer (job 3 of my area is where sanitizers belong).

## What I am NOT sure about
- Whether the true mate distance is 4 (engine's depth-28 answer) or shorter. python-chess proved no mate inside 14
  plies for the side to move (white is mated, so that is the relevant direction: white has no mate, black does).
  My solver only searched the side-to-move mate direction; it never proved black's distance.
- Whether the same fault produces CP scores on quiet positions, or is specific to mate scores.

## Times
see `stamps.txt`.

## Last command output
```
$ ls forge-combo29/swarm/25/job1/
check_G_d12.txt  check_O_d12.txt  check_pv.py  control.txt  G_d12.jsonl  mate12_check.py  mate12_check.txt
mate_deep.sh  mate_deep.txt  mate_probe_s14.txt  mate_probe.txt  mate_pv_probe_s14.sh  mate_pv_probe.sh
PREDICTION.md  repro_mate12.sh  repro_out.txt  repro_verify.txt  run_pv.py  stamps.txt  true_mate2.py
true_mate2.txt  true_mate3.py  true_mate3.txt  true_mate.py  true_mate.txt  verify_pv_line.py
```
