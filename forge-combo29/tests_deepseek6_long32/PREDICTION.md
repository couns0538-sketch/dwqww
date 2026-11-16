# deepseek6 long 32 — PREDICTION (written before the first measuring command)

Item (file 8, long 32): **RECIPE R on kimi5's `SoundArms.patch.txt` (57524c71) and `SoundSteps.patch.txt`
(07713c3b), one at a time** — one line and skip for a patch my branch already has a recipe-R report for.

Model: DeepSeek V4.1 Flash 1017. Time: see `stamps.txt`, first line.

## What recipe R means here, fixed now so the report cannot redefine it

| step | what I do |
|---|---|
| R1 | the sha256 of the patch file must start with the 8 hex the job names; `patch -p1 --dry-run --fuzz=0`, then the real apply |
| R2 | four pins (bench 11/13/16, perft 5) and the `uci` option list with every new option's default, pasted |
| R3 | identity: **at the DEFAULTS** (not under S14 — my long-10 lesson: kimi5's base is defaults + its own switch), rows on O and G versus kimi5's `k5_j5_none_d12` rows from its job-5 json, position by position |
| R4 | every non-default setting kimi5's job-5 report tested for THAT patch, rows on O, compared position by position with its json (`runs_O/k5_j5_<cfg>_d12.json` → `records[].nodes`/`bestmove`) |

**R2's pin check uses the plain-build numbers because these patches add options whose defaults must change
nothing.** If a patch's defaults are NOT an identity, that is an R3 failure and the item stops there for that
patch (a finding, committed with raw output).

## Which patches get a full R and which get a skip line

| patch | my branch already has | action |
|---|---|---|
| `SoundRegret.patch.txt` (10208495) | full recipe R in `REPORT_deepseek6_long10.md` | **one line, skip** |
| `SoundArms.patch.txt` (57524c71) | only inside bundle (b) of long 19, never standalone R | **full R** |
| `SoundSteps.patch.txt` (07713c3b) | only inside bundle (b) of long 19, never standalone R | **full R** |

## The settings kimi5's job-5 report tests (read from its `k5_j5.py`, committed)

- **SoundArms** (its config set on the plain build): `none` (K1), `smp` = `SoundMatePruning true` (K2),
  `pv` = `SoundPvArm 1` (K3), `chk` = `SoundInCheckArm 1` (K4), `mat` = `SoundMateAlphaArm 1` (K5),
  `pvchk` = `SoundPvArm 1 + SoundInCheckArm 1` (K6), `off7` = `SoundMatePruning true + the three arms -1` (K7).
  **Seven settings.** These are the R4 set for SoundArms; five more (`cnt`, `cntsmp`, `probe`, `mask*`,
  `pvmask*`) belong to the regret/steps patch and say "not comparable" for this one.
- **SoundSteps** (applies on top of SoundArms, because `SoundStepMask` gates the arms' steps):
  `mask0` = `SoundMatePruning true + SoundStepMask 0` (its K1 check), `mask1`, `mask15`, `mask33`, `mask48`,
  `mask51`, `mask60`, `mask62`, `pvmask1`, `pvmask15`, `pvmask33`, `pvmask48`, `pvmask51`, `pvmask60`, `pvmask62`.
  **Fifteen settings**, all on the SoundArms+SoundSteps chain.

## Predictions, each with the range that kills it

**P1 — both patches apply with zero fuzz on the plain tree, and SoundSteps needs SoundArms first.**
`SoundSteps` declares `SoundStepMask`, which gates arms that only exist after `SoundArms`, so a dry run of
SoundSteps ALONE on the plain tree should FAIL on a missing context line. Kill range: if SoundSteps applies alone,
its option would be inert and I would say so — but my prediction is that it does not apply alone.

**P2 — the defaults are an identity for both patches.** Rows at defaults on O and G equal kimi5's `none` rows
**200 of 200** and **353 of 353**, and equal my own plain rows (9,500,069 / 18,466,239 at depth 12). Kill range:
any single position differing → item stops for that patch.

**P3 — SoundArms: `smp` (all arms on) shrinks the O tree, by between 0.5 % and 6 %.** kimi5's own numbers say O
0.99885 for the whole switch and 0.9500 for mask 1, so the whole switch is nearly inert on O and the mask is
what bites. Prediction: `smp`/`none` ∈ [0.94, 0.995] on O. Kill range: outside.

**P4 — SoundArms: `pvchk` and `chk` are the two that move the O tree most among the single-arm settings**,
because kimi5's regret table found the in-check s1 cell the worst. Kill range: if `mat` or `pv` moves it more
than both, P4 is killed.

**P5 — `off7` is the LARGEST tree of the seven** (arms at -1 disable pruning paths, so more nodes).
Prediction: `off7`'s O sum > 9,600,000. Kill range: below 9,600,000 kills P5.

**P6 — every one of the seven SoundArms settings changes at least one best move on O** (kimi5 reports a live
effect on both sets for each). Kill range: a setting with 0 changed best moves and 0 changed node counts is an
inert setting and gets said so.

**P7 — SoundSteps: `mask0` is an exact identity with `smp`** (its own K1 check: mask 0 lets every step through).
Prediction: `mask0` rows equal `smp` rows **200 of 200**. Kill range: any difference.

**P8 — SoundSteps: the mask values that matter are low-bit ones.** Prediction: `mask1` ≤ 0.97 × `smp` on O,
while `mask62` ≥ 0.999 × `smp` (bits for steps that rarely fire). Kill range: either side inverted.

**P9 — budget.** Two builds and 22 runs at depth 12 on O: about 25–40 minutes. Kill range: if a patch's R3 fails
I stop that patch inside the hour and say which step is unfinished.

## What would make me report "not done"
A patch whose sha does not match (refuse it, say so), a build that fails the pins, or an R3 identity failure
(stop that patch, commit the raw output). A differing R4 row is a FINDING, not a stop.
