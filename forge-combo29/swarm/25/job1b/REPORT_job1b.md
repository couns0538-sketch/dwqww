# REPORT — seat 25, area 5, job 1 SECOND RUN (seed 2511, new position set R2)

## What was asked
Cycle step (c): job 1 of my area again, with the next seed (2511 = SEED+10) and a new position set (R2,
250 random-game positions from seed 2511, one every 7 plies). Same check: is every final PV legal, and does
every `mate N` score match its PV?

## The answer
250 searches, 0 illegal PVs, 12 mate scores, and **1 of the 12 has a PV that is not a mate** (15 plies for a
`mate -9` that needs 18). This is the same defect as S-F1 on a completely unrelated middlegame position, so
the fault is **not confined to endgames** — that is the main thing this second run adds.
The S-F1 control reproduced exactly: `mate -12`, 18-ply PV, still not checkmate.

## How sure
Very sure of the observations (deterministic, raw jsonl committed, `--expect-records=250` asserted).
For the second case I can only say the PV is not a mate; I could NOT prove the true distance within the
time I had (see below), so I do NOT claim that score is wrong by a specific number.

## What was done

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone | done | `PREDICTION.md` (commit 0193aa675) | before any measuring command |
| R2 generated from seed 2511 | done | `make_R.py`, `make_R.txt`, `R2_2511.fens` | 250 positions |
| 250 depth-12 S14 searches | done | `R2_d12.jsonl` | 250 records |
| PV + mate check with record count asserted | done | `check_R2.txt` | 0 illegal, 12 mates, 1 bad |
| S-F1 control re-run | done | `../job1/mate_pv_probe_s14.txt` and `../check_S06F10/mated_proof.txt` | reproduces; mated in exactly 4 |

## Predictions, scored
| id | prediction | outcome |
|---|---|---|
| Q1 | 250 searches | HELD |
| Q2 | 0 illegal PVs | HELD (0 of 250) |
| Q3 | 0..5 mate scores, killed above 10 | **KILLED** — 12 mate scores |
| Q4 | at most 2 bad mate PVs | HELD (1), but see below |
| Q5 | S-F1 control still prints mate -12 | HELD |
| Q6 | mean nodes in [20k, 120k] | HELD — mean 75,725 nodes (min 438, max 658,454) |

Q3 was killed: 12 mate scores in 250 random-game positions at depth 12 is far more than I predicted. That is
itself a useful number — depth-12 searches on random games hit mates often, because random games reach
tactical positions.

## Findings (new line)

### S-F8 (NEW) — the mate-PV defect is not confined to endgames
`2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1qB3NR w - - 0 22`, depth 12, S14:
```
score mate -9   pv g1f3 f5g4 h1d1 c7f4 d2e1 f4g3 e1f1 g4f3 e2f3 g3f3 f1e1 h6g5 a2a3 g5d2 e1d2
```
15 plies, needs 18. After the PV: `2b2knr/3pp3/1r2n1p1/p7/4P2p/P2P1q1P/1P1K4/1qBR4 b - - 0 29`,
is_checkmate = False, 53 legal moves left. So the printed line is not a mate, on a middlegame position.
What I do NOT claim: that the score itself is wrong by 3 moves. `mated.py` proves white is not mated within
4 moves on this board; proving the exact distance needed deeper search than I had time for, so the score may
be right and only the PV truncated. For S-F1 I had that proof (mated in exactly 4, score said 12); here I do not.

Shows again:
```bash
python3 forge-combo29/swarm/25/job1/verify_pv_line.py \
 '2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1qB3NR w - - 0 22' \
 'g1f3 f5g4 h1d1 c7f4 d2e1 f4g3 e1f1 g4f3 e2f3 g3f3 f1e1 h6g5 a2a3 g5d2 e1d2'
```

## Measurement-integrity audits done in this run (the coordinator's two broadcasts)

### 19-F12 — "quit mid-search fabricates a bestmove"
Reproduced the failure mode and cleared my own harness (`../check_19F12/`):
- pipelined `go depth 12` + `quit` on one write, stdin closed -> `bestmove a2a3`, 0 info lines (the fabrication).
- my pattern (stdin OPEN, read stdout until `bestmove`) -> 12 info lines, 56720 nodes, `e2e4`.
- `quit` during a still-running search (0.5 s into `go depth 30`) -> 1391723 nodes at depth 19, a real answer.
So: closing stdin is what fabricates; `quit` alone is safe. **None of my recorded results used the
fabricating pattern.**

### Clear Hash vs ucinewgame (seat 10's rule)
Independently reproduced on my build (`../audit/warm_cold_audit.txt`):
```
three fresh processes            : [18407, 18407, 18407]
one process, ucinewgame before   : [18407, 18407, 18407]   <- cold
one process, Clear Hash before   : [18407, 22693, 52170]   <- NOT cold
```
I never issued `Clear Hash` in any script (`grep -rn "Clear Hash"` over my folder: no hits). My node-count
tables all send `ucinewgame` then `isready` before every search, which this audit shows is cold. **No table of
mine needs a warm relabel.**

### My own solver had a bug; S-F1 was re-verified after fixing it
`mated.py` had a double `pop()` after a single push, which crashed on some boards (it raised
`IndexError: pop from empty list` on the S-F8 board). Fixed. I then RE-RAN the S-F1 proof with the fixed
solver: still "mated in 1/2/3: False, mated in 4: True". So S-F1's conclusion stands, and the control
(stalemate/mate-in-1 board) still passes.

## What I did NOT do
- Did not prove the exact mate distance for S-F8's board (timed out at 6 moves).
- Did not run the 5 remaining jobs' worth of seeds, or a third position set.
- No sanitizer run in this job (job 3 covered that).

## What I am NOT sure about
- Whether S-F8's `mate -9` score is wrong or only its PV is short. Both are defects but they are different
  defects; I have evidence only for the PV.
- Whether 12 mate scores in 250 random positions is typical; I have one sample.

## Times
see `stamps.txt`.
