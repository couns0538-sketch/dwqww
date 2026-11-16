# REPORT job 2 — seat 15, area 5 (draw scores)

**What was asked.** 20 positions each of K v K, KN v K, KB v K, KNN v K, 20 with a
threefold repetition on the board (reached by a move list), 20 with the fifty-move counter
at 99; the score at depth 10.

**The answer.** K v K, KN v K, KB v K and threefold all return exactly `cp 0` — 80 positions,
unanimous. KNN v K does **not**: 19 of 20 return a winning score for the side with the two
knights, up to `cp +309`, although KNN v K cannot be won by force. The halfmove-99 set returns
ordinary scores up to `cp 390`; my prediction called that a failure, and the prediction was
wrong, not the engine.

**How sure.** High for every number (one committed script over committed transcripts; the
parser now raises instead of silently skipping). High that KNN v K is not scored as a draw by
default and that the engine's own `DeadMaterial` option fixes it. Not established: whether
`DeadMaterial` should be on by default, or whether S14 is meant to have it on.

## Honesty numbers

Release build `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`;
bench 11/13/16 and perft 5 exact (`HONESTY.txt`). Per-run metadata: `meta.txt` in this folder
(exe, sha256, `id name`, every option sent, `go depth 10`).

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| KvK set | done | `sets/kvk_20.fens` | 20, every FEN `is_valid()` |
| KNvK set | done | `sets/knk_20.fens` | 20, valid |
| KBvK set | done | `sets/kbk_20.fens` | 20, valid |
| KNNvK set | done | `sets/knnk_20.fens` | 20, valid |
| threefold set | done | `sets/rep_20.ucimoves` | 20 move lists, each reaches a position 3× on the repetition key (board, turn, castling, ep) — `rep_verify.txt` |
| fifty-move set | done | `sets/fifty_20.fens` | 20, every FEN valid, halfmove clock 99 |
| 120 searches at depth 10 | done | `out_d10.jsonl`, `raw/` | 120 accepted, 0 refused |
| per-set summary | done | `analyze_d10.txt` | see below |
| illegal bestmoves | done | `analyze_d10.txt` | 0 of 120 |
| `DeadMaterial` control | done | `evidence_deadmaterial.txt` | all 20 KNNK → cp 0 with the option on |
| parser hardened after seat 19's warning | done | `analyze_draw.py`, `drawrun.py` | raises on a missing `score` token or a short set |

## Prediction, as committed before measuring

| # | prediction | verdict |
|---|---|---|
| P1 | K v K all exactly 0 | **HELD** |
| P2 | KN v K all exactly 0 | **HELD** |
| P3 | KB v K all exactly 0 | **HELD** |
| P4 | KNN v K all exactly 0 | **REFUTED** — 19 of 20 nonzero, +147…+309 |
| P5 | threefold all exactly 0 | **HELD** |
| P6 | fifty-move all inside [-30, +30] | **REFUTED as written** — min 0, max 390 |
| P7 | no crash, no illegal bestmove | **HELD** |

P6 deserves the plain statement: my kill band was too tight. Every position scoring above 200
had a capture or a pawn move available, both of which reset the fifty-move counter, so a nonzero
score is defensible and the engine is not at fault. The prediction was wrong.

## Findings

### 15-F3 — KNN v K is scored as a win with S14 (NEW)

```bash
cd forge-combo29/swarm/15/job2
python3 analyze_draw.py out_d10.jsonl | head -12
```

```
knnk     20 309 147 -223 -207 159 257 252 255 218 246 ... accepted=20 refused/noinfo=0
knnk     n=20 nonzero=19 min=-223 max=309 mates=0
```

KNN v K (king and two knights against a bare king) is a theoretical draw: mate cannot be forced.
19 of 20 positions at depth 10 report a decisive score, from `cp -223` to `cp +309`.

The engine has an option aimed at exactly this, and it fixes it:

```bash
cat forge-combo29/swarm/15/job2/evidence_deadmaterial.txt
```

```
k4K2/8/8/8/1N6/8/8/N7 w - - 0 1   DeadMaterial=false  score cp 309    DeadMaterial=true  score cp 0
8/8/8/3k1K2/8/2N5/7N/8 b - - 0 1  DeadMaterial=false  score cp -223   DeadMaterial=true  score cp 0
4K3/8/8/8/2N5/2k5/8/3N4 b - - 0 1 DeadMaterial=false  score cp 0      DeadMaterial=true  score cp 0
```

So the behaviour is *known to the engine* and off in S14. That is the finding: with the PC's
S14 settings the engine will happily "win" an unwinnable endgame, and it can be dragged into a
50-move draw by an opponent who knows it. Whether S14 should set `DeadMaterial true` is Fable's
and Opus's call — I report the behaviour, not the tuning decision.

### 15-F4 — a dead-draw root prints an EMPTY pv, which silently defeats a `" pv "` grep (NEW)

```bash
sed -n '3,6p' forge-combo29/swarm/15/job2/raw/kvk_000.txt
```

```
info depth 1 seldepth 1 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
info depth 2 seldepth 2 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
```

The line ends in ` pv` with **no move after it**. My first analysis filtered on `" pv "` (with
trailing space) and therefore dropped all 80 K v K / KN v K / KB v K / threefold records, and the
summary printed `NO_INFO` for four whole sets. The engine's answer was correct all along; the
harness was not. Fixed by matching `info depth` and then asserting a `score` token exists.

This is the same class of defect as seat 19's `clock_plan` warning and as the `bestmove a2a3`
fabrication: a parser that cannot distinguish "absent" from "zero" reports success. Worth knowing
for anyone building a harness on this engine: **an empty PV is a normal answer for a dead draw.**

## Suspicions, not proven

- `DeadMaterial` presumably recognises the bare-king/insufficient-material cases by material key.
  I did not read the code, and I did not test whether it also handles KB v KN or KNN v KN.
- The single KNN v K position that already scored 0 (`4K3/8/8/8/2N5/2k5/8/3N4 b`) may be a
  position where depth 10 happened to see the draw; not investigated.

## What I did NOT do

- Did not test KNN v K at other depths to see whether the false win persists deeper.
- Did not test KB v KN, KNN v KN or other theoretically drawn material.
- Did not run these under a sanitizer; job 3 carries the sanitizer run.
- Did not tune or recommend a default for `DeadMaterial`.

## What I am NOT sure about

- Whether `DeadMaterial true` costs nodes/strength elsewhere; I only measured the KNN v K scores.
- Whether the 390 in the fifty-move set is a good evaluation; I only show it is not a draw score,
  and that a capture/pawn move was available in each such position.

## Times

`stamps.txt` — every line is a pasted `date -u`.

## Last command's output

```
$ ls
analyze_d10.txt
analyze_draw.py
drawrun.py
evidence
evidence_deadmaterial.txt
evidence_knnk_fifty.txt
make_draw_sets.py
meta.txt
out_d10.jsonl
prediction.txt
raw
REPORT_job2.md
rep_verify.txt
run_d10.log
sets
sets_report.txt
stamps.txt
```
