# Astra A1: residual H256 data and blend experiment, 2026-10-30

**Status: experiment plan; training and strength results are UNVERIFIED.** No trainer, engine, accepted network or running GPU job was changed for this plan. These are sequential ablations for Engine NNUE after the data tools are reviewed, not a request to interrupt its current training.

Source of truth: `tools/nnue/train_resid_v3b.py`, SHA-256 `7379d1fcf47dcba6297b591dc2bc07b47caac865cee5d1d4632be1877fc96fe5`. The existing trainer is preserved, including its memory fixes. The source and input contract were checked against `/tmp/astra-a1-recon/data_contract_provenance.json`.

## Label and schedule contract

- `.pos` scores are **side-to-move centipawns**; stored results are **White results** (0, 0.5, 1). For Black to move, the trainer converts the result to `1 - white_result`. Do not flip the score a second time.
- Teacher probability is `sigmoid(clamp(cp * 2.25 / 400, -40, 40))`. With lambda the **teacher fraction**, the training target is `lambda * teacher + (1 - lambda) * stm_result`. This is a scalar expected-score target; the model does not predict a three-class W/D/L distribution.
- The actual schedule is **linear in optimizer steps**, although the existing log text calls it “cosine blend”: `lambda(s) = start + (end - start) * min(1, s / max(1, T - 1))`, for steps `s = 0..T-1`. `T = epochs * min(floor(N / batch), steps_per_epoch)` when that limit is nonzero. Only the learning-rate decay is cosine. Do not report a cosine target schedule.
- Preserve residual `768 -> 256` per perspective, SCReLU, concatenated output, QAT enabled, sigmoid K=2.25, and HCE addition. Do not use `--pure`, `--no-qat`, feature buckets, threats or pawn pairs in these ablations. Start each arm from the same seed initialization; this is not an import or replacement of the accepted engine network. Omit `--resume`.
- Every training and holdout `.pos` must have its matching, same-order/count `<stem>.hce` in the single `--hce-dir`. Verify hashes, record counts, alignment and the HCE invalid-sentinel count before launching. A relabelled score and HCE must come from the exact full FEN sidecar; reconstructed state must remain separately identified and excluded from the exact-label cohort.

## Holdouts and sealed cohorts

Never train on shards 013 or 014, or their positions or identifiable games. Keep their original files immutable. Use 013 for development comparisons and reserve 014 for one final, preselected checkpoint evaluation. The available verified 013 head contains 1.5M positions; **014 and authentic game identifiers are unavailable here**. Zero observed position overlap against the available 013 head is not proof of exclusion against all of 013/014 or of game-level isolation. Full-corpus leakage clearance remains blocked until those inputs exist. The commands below refuse missing paths; they do not fabricate holdouts.

Prepare NEW sealed cohort files before training; the cohort sampling procedure is a prerequisite, not an implemented feature of this trainer. Save source/output hashes, source row IDs, policy, sample seed, counts by result/STM/material/score bin, and verified holdout overlap counts. Use the same deterministic sample/order in all blend arms. Match the same count and sampling policy across filter arms, whose membership intentionally differs. Sample before launching: `--max-train` selects file **prefixes**, not a random or balanced cohort. Leave it zero in pilot runs.

For the pilot, use exactly 1,048,576 eligible positions, with a fixed sample seed 20261030 and stable sampling independent of input traversal. Reject or separately report strata that cannot supply the planned count; do not silently duplicate records. Keep all position identities from a known game together if IDs become available. No game-split claim can be made from the current sidecar alone.

## Sequential matrix

All proposed thresholds below are starting hypotheses chosen here, not tuned constants copied from another engine. The trainer's existing hyperparameter values are reused as controls.

| Stage | Arms, run in order | Fixed controls and rationale |
|---|---|---|
| 0: CPU smoke | One four-step run, below | Real data, matching HCE, residual init check, finite loss and exports. This checks plumbing only. |
| 1: blend | T0: 1.0→1.0; T1: 1.0→0.8; T2: 1.0→0.6 | Identical sealed cohort, labels, HCE and order; seeds 17 and 29 for every arm. T0 isolates teacher fitting. T1 introduces at most 20% outcome weight late; T2 tests the trainer's existing, more substantial 40% endpoint. Six runs, sequential, no concurrent GPU training. |
| 2: filter attribution | D0: quiet/legal + exact dedupe; D1: D0 + disagreement; D2: D1 + near-dedupe | Use only the selected blend and both seeds; match 1,048,576 rows and distribution targets. D0 still excludes holdouts and terminal/in-check/capture/promotion-best-move rows. D1 starts with opposite decisive outcomes at abs(cp)≥400 and draws at abs(cp)≥800. D2 uses the implemented near-duplicate policy only after its manifest/test review. Report every removal fraction and remaining distribution. |
| 3: deeper labels | Old vs new scores on precisely the same position IDs | Hold blend and filters fixed. Preserve original score/result and source row IDs. Compare fixed-node budgets, achieved nodes/depth, score deltas and label stability. A higher node budget alone does **not** prove a better label. |
| 4: opening variety | Old-only vs 80% old + 20% newly generated self-play | Deferred until new R8 games and results actually exist. Match count, blend, label budget and distributions; split/exclude whole games when IDs exist. The initial 20% is deliberately modest, not an established optimum. |

For stages 1–3: batch 4096, three epochs, 256 steps/epoch, exactly 768 optimizer steps, LR 0.001, warmup 300 steps, minimum LR fraction 0.01, QAT and residual H256. These are short screening runs, not evidence of convergence. The linear blend endpoint is reached at step 767. Evaluate the final epoch, not whichever epoch happened to look best. If fewer eligible rows remain, stop and document a revised common design before any arm runs.

For deeper labels, start with a bounded paired slice at 10,000 and 100,000 nodes per position (original proposals, configurable). Report mate/terminal handling separately and median/p90 abs(cp delta), sign changes, achieved depth/nodes and throughput. Inspect a higher-budget subset where the two budgets disagree. Preserve the old-score control; do not replace all 305M labels on the strength of a small slice.

## Exact trainer commands: Linux CPU smoke and pilot

These paths are deliberately explicit variables for NEW prepared files. Edit the root paths; the referenced cohort and matching HCE must already be sealed. Commands do not create or overwrite data shards. Output roots and run directories must be new. The CPU smoke uses a small immutable derivative of 013 only; its source-row manifest must identify that subset.

```bash
set -euo pipefail
PY=python3
REPO=/path/to/dwqww
DATA=/path/to/sealed_astra_a1_cohorts
HCE=/path/to/sealed_astra_a1_hce
RUNS=/path/to/new_runs/astra_a1_$(date -u +%Y%m%dT%H%M%SZ)_$$
test ! -e "$RUNS"
mkdir "$RUNS"
SMOKE="$DATA/smoke_real.pos"
SMOKE_HOLD="$DATA/holdout_013_smoke.pos"
TRAIN="$DATA/cohort_d0_1048576.pos"
HOLD="$DATA/forge_selfplay_013.pos"
for f in "$SMOKE" "$SMOKE_HOLD" "$TRAIN" "$HOLD"; do
  test -f "$f"
  stem=$(basename "$f" .pos)
  test -f "$HCE/$stem.hce"
done
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
"$PY" "$REPO/tools/nnue/train_resid_v3b.py" \
  --train "$SMOKE" --holdout "$SMOKE_HOLD" --hce-dir "$HCE" \
  --device cpu --adam-impl torch --dev-scalars 0 --shape 256 --residual \
  --epochs 1 --batch-size 64 --steps-per-epoch 4 --max-train 4096 \
  --val-positions 512 --lr 0.001 --warmup-steps 1 --min-lr-frac 0.01 \
  --blend-start 1 --blend-end 0.8 --sigmoid-k 2.25 --seed 17 \
  --mmap-data --order-buffers 1 --init-check --loss-sync-every 1 \
  --run-dir "$RUNS/smoke" > "$RUNS/smoke.log" 2>&1

# Pilot only when scheduled: six sequential CPU runs; no GPU/live trainer touched.
for seed in 17 29; do
  for end in 1.0 0.8 0.6; do
    tag="d0_lambda_${end}_seed_${seed}"
    test ! -e "$RUNS/$tag"
    "$PY" "$REPO/tools/nnue/train_resid_v3b.py" \
      --train "$TRAIN" --holdout "$HOLD" --hce-dir "$HCE" \
      --device cpu --adam-impl torch --dev-scalars 0 --shape 256 --residual \
      --epochs 3 --batch-size 4096 --steps-per-epoch 256 --max-train 0 \
      --val-positions 262144 --lr 0.001 --warmup-steps 300 --min-lr-frac 0.01 \
      --blend-start 1.0 --blend-end "$end" --sigmoid-k 2.25 --seed "$seed" \
      --mmap-data --order-buffers 1 --init-check --loss-sync-every 128 \
      --run-dir "$RUNS/$tag" > "$RUNS/$tag.log" 2>&1
  done
done
```

For crew-scheduled DirectML pilots only, change the same three flags in **every** pilot arm to `--device directml --adam-impl dml --dev-scalars 1`. Do not compare a CPU arm against a DirectML arm as if hardware/numerics were matched. This trainer has no `--device cuda` choice. These commands have not launched a GPU job. `--mmap-data` maps training inputs, not the whole holdout; `--max-ram-gb` would only warn, not enforce a memory limit.

## Equivalent PowerShell trainer invocation

Run this in a dedicated new PowerShell process on grok-pc. Set its spare-core affinity/Idle priority using the data-job launcher in the final A1 report before executing; the commands here specify trainer arguments, not a verified Windows scheduler. A fresh GUID prevents reuse of a prior output directory. This is a separate CPU smoke followed by optional sequential CPU pilots, not a command to modify the live trainer.

```powershell
$ErrorActionPreference = 'Stop'
$Python = 'C:\path\to\python.exe'
$Repo = 'D:\path\to\dwqww'
$Data = 'D:\path\to\sealed_astra_a1_cohorts'
$Hce = 'D:\path\to\sealed_astra_a1_hce'
$RunsParent = 'D:\path\to\new_runs'
$Runs = Join-Path $RunsParent ('astra_a1_' + [guid]::NewGuid().ToString('N'))
if (Test-Path $Runs) { throw "Output already exists: $Runs" }
New-Item -ItemType Directory -Path $Runs | Out-Null
$Trainer = Join-Path $Repo 'tools\nnue\train_resid_v3b.py'
$Smoke = Join-Path $Data 'smoke_real.pos'
$SmokeHold = Join-Path $Data 'holdout_013_smoke.pos'
$Train = Join-Path $Data 'cohort_d0_1048576.pos'
$Hold = Join-Path $Data 'forge_selfplay_013.pos'
foreach ($File in @($Smoke,$SmokeHold,$Train,$Hold)) {
  if (!(Test-Path -LiteralPath $File -PathType Leaf)) { throw "Missing $File" }
  $Pair = Join-Path $Hce ([IO.Path]::GetFileNameWithoutExtension($File) + '.hce')
  if (!(Test-Path -LiteralPath $Pair -PathType Leaf)) { throw "Missing $Pair" }
}
$env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'
$Common = @('--hce-dir',$Hce,'--device','cpu','--adam-impl','torch',
  '--dev-scalars','0','--shape','256','--residual','--lr','0.001',
  '--min-lr-frac','0.01','--sigmoid-k','2.25','--mmap-data',
  '--order-buffers','1','--init-check')
$SmokeArgs = $Common + @('--train',$Smoke,'--holdout',$SmokeHold,
  '--epochs','1','--batch-size','64','--steps-per-epoch','4','--max-train','4096',
  '--val-positions','512','--warmup-steps','1','--blend-start','1',
  '--blend-end','0.8','--seed','17','--loss-sync-every','1',
  '--run-dir',(Join-Path $Runs 'smoke'))
& $Python $Trainer @SmokeArgs *> (Join-Path $Runs 'smoke.log')
if ($LASTEXITCODE -ne 0) { throw "Smoke failed: $LASTEXITCODE" }
# Optional pilot after review/scheduling; six sequential runs.
foreach ($Seed in @(17,29)) {
  foreach ($End in @('1.0','0.8','0.6')) {
    $Tag = "d0_lambda_${End}_seed_${Seed}"
    $Run = Join-Path $Runs $Tag
    if (Test-Path $Run) { throw "Output already exists: $Run" }
    $PilotArgs = $Common + @('--train',$Train,'--holdout',$Hold,
      '--epochs','3','--batch-size','4096','--steps-per-epoch','256','--max-train','0',
      '--val-positions','262144','--warmup-steps','300','--blend-start','1.0',
      '--blend-end',$End,'--seed',[string]$Seed,'--loss-sync-every','128','--run-dir',$Run)
    & $Python $Trainer @PilotArgs *> (Join-Path $Runs "$Tag.log")
    if ($LASTEXITCODE -ne 0) { throw "$Tag failed: $LASTEXITCODE" }
  }
}
```

For filter arms change only `$Train`/`TRAIN` to the reviewed sealed D1 or D2 cohort, hold the selected blend fixed, and use a NEW run root/arm tag. For old/new labels change only the paired cohort and its matching HCE directory after verifying identical row identities. A filesystem path or filename is not a substitute for the saved hashes.

## Evaluation and decision record

Record trainer/source SHA, cohort/HCE/holdout hashes and counts, complete command, Python/PyTorch/device versions, wall time, peak memory, actual steps, actual evaluated rows, fixed-final-epoch checkpoint SHA, exports and original logs. Same seed does not promise byte-identical runs across CPU/DirectML or different dependency builds. Never install an experimental export over `src/nnue_weights.inc`.

Report **teacher fit and outcome fit separately**: teacher-probability MSE at lambda=1, expected-score/Brier-style MSE at lambda=0, calibration by predicted-probability bins, and those quantities split by White result, STM, material and score range. Also report fixed lambda=.8 and .6 MSE for continuity. Normal trainer logs give 1/.6/.8 only; **they do not give pure outcome loss**. A read-only evaluator can call the existing `evaluate(..., blends=(0.0, 0.6, 0.8, 1.0))` on the exported checkpoint; that evaluator and calibration bins remain a separate prerequisite, not a result produced by these CLI commands. Do not mislabel blend-.6 loss as WDL loss.

The trainer evaluates full batches only. Report its returned/printed row count; `--val-positions 262144` is divisible by batch 4096, but final full holdout tails can be omitted. Selection uses the same fixed 013 subset and final epoch for every arm; show both seed results and their paired differences, not a claim of significance from two seeds. Freeze the selected policy before the single 014 evaluation. If seeds disagree or teacher and outcome metrics conflict, mark inconclusive and extend matched runs rather than asserting a winner.

CLI option names and proposed values were statically checked against the exact trainer's argparse declarations without importing its training dependencies. This does not certify installed dependencies, run time, trainer-load success, Windows execution or loss values. CPU smoke evidence belongs in the final A1 report if/when actually run. GPU training, 014 evaluation, production leakage clearance and playing strength are **UNVERIFIED**. No Elo or training-gain claim is made.

## IDEA_SOURCE

Original experiment design from the user's Astra A1 data request; label, loss, memory and schedule semantics from this repository's `train_resid_v3b.py`, `src/datagen.cpp`, and the verified data-contract handoff. Existing filter/relabel tools supply this project's operational contracts. No code or tuned values were copied from another chess engine.
