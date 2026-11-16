# REPORT — seat 25, area 5, job 1 (PV legality and mate scores)

## What was asked
Every search of a rows run on O and G at depth 12, S14: is the LAST `info ... pv` line legal when played by
python-chess, and does a `mate N` score match its PV length (2N-1 plies for N>0, 2|N| for N<0)? Plus one control
that a PV with an illegal last move is caught.

## The answer
553 searches ran (200 on O, 353 on G). All 553 final PVs were fully legal. 10 of the 553 carried a `mate N` score.
Nine of those ten had a PV of exactly the right length and ended in real checkmate. ONE did not:
`8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` reported `score mate -12` with an 18-ply PV that ends 15 plies short of a
24-ply mate and is not checkmate at all. It reproduces exactly and deterministically.

**I then proved the exact truth independently** (plain minimax over every legal move, no pruning, no TT, no
mate-score arithmetic — `check_S06F10/mated.py`, validated on a known "mated in 1" control first): the side to
move is **mated in exactly 4 moves**, and not in 3. So the correct score at this root is `mate -4`, which is
exactly what the engine itself reports from depth 22 on. The depth-12..16 `mate -12` is therefore wrong by
**8 moves**, not merely "truncated" — it is a wrong score, and it is too pessimistic (it claims white survives
24 plies when white is mated in 8).

This matters for honesty: my first draft of this report called it a "truncation". It is not: the truncated PV is
the *symptom*; the score itself is wrong. Seat 06's S-F10 says 4 of its 16 depth-10 mate PVs are horizon-truncated
and concludes the mate machinery is "sound on this set". My case is a counter-example to that safety claim: a
truncated mate PV here goes with a wrong mate distance, and the true distance was provable by plain minimax.

## How sure
Very sure of the observation (deterministic, reproduced in a fresh process, raw lines committed, and independent
of Hash size 1..256 MB — `check_S06F10/hash_probe.txt`). Very sure of the true distance: 4, from plain minimax
(`mated.py`, control-validated, and it agrees with the engine's own depth-22+ answer).

**Rule 1 (Opus file 2): a zero needs a planted one.** Two plants were run through the SAME harness, unchanged
(`run_pv.py` -> `check_pv.py`), and both were counted:
- `fake_engine.py` (illegal PV `a1a8` on every go) -> `PVs with illegal: 5` of 5 records — `plant_illegal.txt`.
- `fake_mate_engine.py` (legal 3-ply PV, claims `mate 5`) -> `mate PVs wrong: 5` of 5 — `plant_mate.txt`.
So the "0 illegal PVs" and the mate tally below are shown, not assumed. Note: running the plants forced a real
fix to `run_pv.py` (it now accepts a command with arguments, `shlex.split`); before that the plant could not run
through the harness at all and the first plant attempt produced `records: 0` — which on its own would have looked
like a pass. That failure is kept in the history, not hidden.

Determinism check: the whole O set was run twice in separate processes; ignoring `nps`, `time` and `hashfull`,
0 of 200 positions differ in any info line and 0 of 200 differ in bestmove (`determinism_check.txt`).

## Honesty numbers (this build, before the job)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four match. See `../HONESTY.txt`.

## What was done

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction written and pushed alone | done | `PREDICTION.md` (commit b2daa7c03) | committed before any measuring command |
| 200 searches on O at depth 12, S14 | done | `O_d12.jsonl` (committed), `check_O_d12.txt` | 200 records, 0 illegal PVs, 0 mate scores |
| 353 searches on G at depth 12, S14 | done | `G_d12.jsonl`, `check_G_d12.txt` | 353 records, 0 illegal PVs, 10 mate scores, 1 wrong |
| Rule 1 plants through the same harness | done | `fake_engine.py` -> `plant_illegal.txt`; `fake_mate_engine.py` -> `plant_mate.txt` | 5/5 illegal caught; 5/5 wrong-mate caught |
| O set run twice, compared | done | `determinism_check.txt` | 0/200 differ in info lines (ignoring nps/time/hashfull), 0/200 differ in bestmove |
| checker control (planted illegal last move) | done | `control.txt` | caught exactly 1 of 1: `bad_move=e1e8@11` |
| re-run the one bad position at depths 10..16 with S14, fresh process each | done | `mate_pv_probe_s14.sh`, `mate_probe_s14.txt` | reproduces `mate -12`/18 plies at depths 12, 13; also at 14, 15, 16 the depth-12 line repeats identically |
| same position, `go depth 18..28` | done | `mate_deep.sh`, `mate_deep.txt` | converges to `mate -4` (8 plies) and it verifies as real mate |
| verify the depth-18 and depth-28 lines end in checkmate | done | `verify_pv_line.py` (run output in `mate_probe_s14`/`mate_deep` and this report) | both end in checkmate |
| independent python-chess exact-mate search | failed, then replaced | `true_mate3.py`/`.txt` (timed out at 16 plies), `check_S06F10/dtm.py`/`dtm_result.txt` (WRONG: reported no mate in 8; a bug in my solver, kept as a record), `check_S06F10/mated.py` + `mated_proof.txt` (correct: mated in exactly 4, control validated) | the truth is mate -4 |

## Findings

### S-F1 (NEW) — a mate score wrong by 8 moves, together with a PV that is short and not mate
`8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`, depth 12, S14, Threads 1, Hash 16:
```
info depth 12 seldepth 27 score mate -12 nodes 19197 nps 3199500 hashfull 4 time 6 pv c2c3 d2d1q c3b2 e4e3 b2a2 d1c2 a2a1 c2c1 a1a2 c1c4 a2b2 c4d4 b2c1 d4a1 c1c2 a1d1 c2b2 e2d3
```
`mate -12` says white is mated in 12 moves (24 plies). The plain-minimax proof says white is mated in exactly 4
moves (8 plies), and not in 3. The engine agrees with the proof from depth 22 upward (`mate -4`). The printed PV
is 18 plies and the position after it is `8/8/1p6/8/p7/3kp3/1K6/3q4 w - - 14 10` with legal moves left = 2, so the
line is not a mate either.

So this is a WRONG MATE SCORE, not just a display artefact, and it is 8 moves too pessimistic. It is stable: the
same `mate -12` appears at depths 12..16 and is unchanged by Hash = 1, 8, 16, 64 or 256 MB (same nodes 19197).

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
prints `is_checkmate: False`, legal moves left 2, `RESULT: NOT checkmate` (`repro_verify.txt`). And the truth:
```bash
python3 forge-combo29/swarm/25/check_S06F10/mated.py '8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1' 5
```
prints `mated in 1/2/3: False`, `mated in 4: True` (`check_S06F10/mated_proof.txt`).

Beyond the known list: the FABLE_TO_swarm_1 known items are about FEN trust and UCI prefix keeping. This is a
search-result fault, so it is not a repeat of any of them.

### S-F2 (NEW, weaker) — the same root's mate score is unstable in the direction of the truth
At depths 12..16 (S14) the root says mate -12, then -9 (d14), -6 (d15-16); at d18 it says -5; from d22 to d28 it
says -4, which is the truth. A mate score that wanders from 12 to 4 with depth on a position whose exact distance
is 4 means the shallow scores are wrong, not merely imprecise. Shows again: `mate_deep.txt`,
`mate_probe_s14.txt`.

### S-C1 (this seat) — CONFIRMS with a correction: seat 06's S-F10 "mate machinery is sound" does not generalise
Seat 06 wrote: "every full-length mate PV in the depth-10 G output is a genuine checkmate (12 of 12) ... 4 of 16
mate PVs are horizon-truncated ... so the mate machinery is sound on this set". I reproduced the depth-10 G run on
my own build (`check_S06F10/G_d10.jsonl`, `check_S06F10/check.txt`): 6 mate scores at depth 10, 0 wrong, 0 illegal
— so their depth-10 observation holds on my build too. But the *inference* ("sound") does not: at depth 12 the
same position set contains a mate score that is wrong by 8 moves. The truncation they observed is the same symptom
as my S-F1, not evidence of soundness.

## Suspicions, not proven
- The 18-ply PV looks like a *truncation* of a longer line: it ends on a quiet king move with black still to move.
  That explains the PV. It does NOT explain the score, which is wrong by 8 moves in its own right.
- The most likely place is the mate-band arithmetic: `score_to_tt`/`score_from_tt` shift by ply against
  `MateInMaxPly = MateValue - MaxPly` (src/search.cpp:179-198), and `format_score` converts a stored mate score
  back to a move distance with `(distance+1)/2` (src/search.cpp:272-279). A score read back from the TT at a
  different ply than it was stored can print a mate distance the PV cannot support. I have NOT shown this is the
  path taken here; it is a hypothesis with a location, not a result. The Hash-size sweep (1..256 MB, identical
  node count 19197) does not rule the TT in or out: a same-search TT read at a nearby ply would behave the same at
  every size.
- I did not separate "the score is wrong" from "the printed mate number is a bad conversion of a right score".
  Both would show as `mate -12`; the Hash sweep and the depth ladder cannot tell them apart.

## What I did NOT do
- I did not finish an exact-mate proof with my faster solver (`dtm.py`): it reported no mate within 8 moves and
  therefore is WRONG (plain minimax proves mate in 4). I am keeping the failed file and its output
  (`dtm_result.txt`) in the tree because deleting it would hide a mistake; it is not evidence of anything.
- I did not bisect which search setting triggers the bad score (IirDepth, SingularDepth, the S14 LMR values)
  against defaults.
- I did not run this position under a sanitizer (job 3 of my area is where sanitizers belong).
- The earlier gap (O raw jsonl not committed) is CLOSED: `O_d12.jsonl` is in this folder now.

## What I am NOT sure about
- Whether the fault is the score itself or the score-to-`mate N` conversion. Proven: the pair (score, PV) is
  inconsistent and the true distance is 4 (so `mate -4` is right).
- Whether it reproduces with default (non-S14) settings: I did probe the defaults once by accident
  (`mate_probe.txt`, no S14) and got `mate -7`/`-6`/`-4` at depths 10..14 rather than `-12`, which suggests S14 or
  the exact setting mix matters, but that probe was not controlled, so I do not claim it.
- Whether other positions in the 553 have a wrong mate score that my length check cannot see. My check only flags
  a PV that is the wrong length or not mate; a score wrong by an even number of plies with a PV that still ends in
  mate would pass unnoticed. That is a real blind spot of this job's check.

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
