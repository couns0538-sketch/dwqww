# REPORT job1b — area 6 job 1, SECOND RUN (cycle (c)), SEED 611, new position set

## What was asked / the answer / how sure

**Asked.** The brief's cycle step (c): after jobs 1–3 are done, run job 1 again with the next seed (SEED + 10 =
611) and a new position set (R with SEED + 10), and say in the report what differs from the first run.

**Answer.** **The first run's answer holds exactly: 0 colour-mirror differences in hce, nnue and total across
6,706 position-pairs from a completely different random set** (G 353 + 500 new R + 5,000 new R + 853 in the
`UseNNUE false` configuration). The symmetry of the evaluation is not an artifact of one seed.

**How sure.** High. Same build (sha256 `e06310eca…`, honesty pins 4/4), same harnesses, and both controls run
beside the zero as Rule 1 of `FABLE_TO_swarm_2.md` requires: the self-control gives 0 of 100, and the **planted**
control (FEN *i* paired with FEN *i+1*, which is not a mirror) is caught **99 of 99**.

## What differs from the first run (required by the brief)

| | first run | this run |
|---|---|---|
| seed | 601 | **611** |
| R set (500) | 16 random games, one position per 7 plies | **11 different games, same rule** |
| R set (5,000) | 92 games, one position per 5 plies | **93 different games, same rule** |
| G set | 353 positions | same fixed file (unchanged by design) |
| configurations measured | default, `UseNNUE false`, `DeadMaterial true`, dead-material set | default and `UseNNUE false` |
| build, harnesses, comparison rule | — | identical |

The two R sets really are different in content, not just in seed (`distinctness.txt`):

| statistic | seed 601 | seed 611 |
|---|---|---|
| positions with \|hce\| > 600 | 232 | 255 |
| positions with fewer than 8 pieces | 160 | 199 |
| positions in check | 38 | 24 |
| mean pieces per position | 14.44 | 13.41 |

## Prediction outcomes (prediction.txt, pushed alone before measuring)

| # | prediction | outcome |
|---|---|---|
| R1 | 0 differences in hce/nnue/total over G + 500 R611 + 5,000 Rbig611 | **CONFIRMED**: 0 of 5,853 |
| R2 | control (position against itself) 0 differences | **CONFIRMED**: 0 of 100 |
| R3 | negative control flags every pair | **CONFIRMED**: 99 of 99 flagged |
| R4 | `UseNNUE false` also 0 differences | **CONFIRMED**: 0 of 853 |
| R5 | the new R set is materially different from the old one | **CONFIRMED**: table above |
| R6 | the second run reproduces the first run's conclusion | **CONFIRMED**: 0 everywhere, same sign and magnitude |

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone first | done | `prediction.txt` | commit "swarm 06 job1b (cycle c) prediction (alone), seed 611" |
| R set built from SEED 611 (500, one per 7 plies) | done | `make_R.py`, `R_611.fens` | 11 games, 500 FENs |
| R set built from SEED 611 (5,000, one per 5 plies) | done | `make_R_big.py`, `Rbig_611.fens` | 93 games, 5,000 FENs |
| G + 500 R colour-mirror comparison | done | `harness_mirror.py`, `out_GR.txt`, `meta_GR.txt`, `table_GR.txt` | **0 of 853** |
| 5,000 R colour-mirror comparison | done | `out_Rbig.txt`, `meta_Rbig.txt`, `table_Rbig.txt` | **0 of 5,000** |
| `UseNNUE false` on all 853 | done | `harness_variant.py`, `out_NoNNUE.txt`, `table_NoNNUE.txt` | **0 of 853** |
| control: position against itself | done | `control_self.py`, `ctrl_self.txt`, `table_ctrl_self.txt` | 0 of 100 (as predicted) |
| **planted control (Rule 1): a pairing that is not a mirror** | done | `ctrl_shift.txt`, `table_ctrl_shift.txt` | **99 of 99 caught** |
| R5 distinctness of the new set | done | `distinctness.py`, `distinctness.txt` | PASS |

Total: 5,853 colour-mirror pairs + 853 `UseNNUE false` pairs + 199 control pairs.

Commands that show each result again (from this folder):

```
python3 harness_mirror.py  ~/bld/release/forge GR_853_611.fens out_GR.txt meta_GR.txt && python3 compare.py out_GR.txt
python3 harness_mirror.py  ~/bld/release/forge Rbig_611.fens out_Rbig.txt meta_Rbig.txt && python3 compare.py out_Rbig.txt
python3 harness_variant.py ~/bld/release/forge GR_853_611.fens out_NoNNUE.txt meta_NoNNUE.txt "name UseNNUE value false"
python3 control_self.py    shift ~/bld/release/forge G_100.fens ctrl_shift.txt meta_ctrl_shift.txt && python3 compare.py ctrl_shift.txt
python3 distinctness.py    ~/bld/release/forge ../job1/R_500.fens R_611.fens seed601 seed611
```

## Findings

**F1 — the evaluation's colour-mirror symmetry is seed-independent: a second, independent position set
(seed 611: 11 new games at one position per 7 plies, 93 new games at one per 5 plies) again gives 0 differences
in 5,853 pairs, and 0 of 853 in the `UseNNUE false` configuration, with a planted control catching 99 of 99.**
Shows again: `python3 compare.py out_Rbig.txt` and `python3 compare.py ctrl_shift.txt`.

**F2 — the SEED-611 set is materially more extreme than the SEED-601 set (255 vs 232 positions with |hce|>600,
199 vs 160 with fewer than 8 pieces, mean 13.41 vs 14.44 pieces) and still shows zero asymmetry**, so the
symmetry is not an artifact of quiet, balanced positions.
Shows again: `python3 distinctness.py ~/bld/release/forge ../job1/R_500.fens R_611.fens seed601 seed611`.

## Suspicions, not proven

- None new. The open question from the fix attempt stands unchanged and is not a suspicion about symmetry: the
  search asymmetry's remaining candidate is the root loop's alpha accumulation
  (`src/search.cpp:2043-2044`), and both the tie-break and the aspiration window have been tested and refuted.

## What I did NOT do

- I did not re-run `DeadMaterial true` or the dead-material position set at seed 611. Those were checked once
  (job 1) and are orthogonal to the seed question; the two configurations that matter for `total` (default and
  pure HCE) were both re-run.
- I did not build a third seed. Two independent sets agreeing at 0 is the evidence; a third would not change the
  conclusion.
- No search work in this job: it is the static-evaluation job by definition.

## What I am NOT sure about

- Whether "the same conclusion twice" is worth the tokens it cost. The brief asks for exactly this (cycle step c),
  so I did it, but the value is in the negative being seed-independent, not in a new number.

## Times

`date -u` lines are in `stamps.txt`.

## Last command's output

`git status --short` and `ls` of this folder are appended to `stamps.txt`.
