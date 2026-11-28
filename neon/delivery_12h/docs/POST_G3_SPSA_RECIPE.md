# Post-`G3_FULL25` SPSA Eval-Margin Re-Tuning Recipe (For Opus / Post-Placement)

> **Rationale:** Forge's current live search margins (`config.forge.toml:214`, Opus's Big Tune `A_FINAL.json`: `RfpMargin=84`, `RfpImproving=37`, `FutilityBase=12`, `FutilityMultiplier=59`, `ProbcutMargin=168`, `QsFutilityMargin=123`, `CaptureFutilityBase=45`, `AspirationDelta=16`, etc.) were SPSA-tuned on legacy `768w` SCReLU (`r0033`). Because `FORGENN3-P` (`G3_FULL25` `1024w` Pairwise+PSQT) has a markedly sharper centipawn scale (`unit=159.45 raw/pawn` at Ep 24 vs `r0067` `~190`) and `-9.75%` lower M4 WDL MSE (`-7.29%` lower SF19 MSE), re-tuning ONLY the 15 eval-dependent pruning margins starting **from the exact live Big Tune `v3_uci_options`** (NEVER reverting to engine defaults!) via `C:\nnue-lab\pipeline\tools\spsa_tune.py` (`SPSA_ONLY` mode) captures free UCI-only Elo with zero C++ changes!

## Ready-to-Run Command (After Opus Places `G3_FULL25` + Confirmed Search Stack)
*(Do NOT run directly from `neon\` — `spsa_tune.py` writes to `C:\nnue-lab\runs\forge\spsa\` and obeys `tmp/loop_gate.py`, `CLOCK_MATCH_RUNNING`, and `91/87 C` CPU heat guard.)*

```powershell
# Stage 1: Re-tune the 15 eval-based margins ONLY, warm-starting from ALL 45 live Big Tune v3_uci_options!
# (spsa_tune.py:25: a tuned setting passed as Name=value starts there instead of engine default!)
$env:SPSA_ONLY = "RfpMargin,RfpImproving,RazorBase,RazorMultiplier,FutilityBase,FutilityMultiplier,ProbcutMargin,QsFutilityMargin,QsSeeMargin,AspirationDelta,SeeQuietMultiplier,SeeNoisyMultiplier,CaptureFutilityBase:12,CaptureFutilityMultiplier,MaterialCorrectionWeight"
$env:SPSA_HEAT_PAUSE_C = "91"
$env:SPSA_HEAT_RESUME_C = "87"

# Note per spsa_tune.py:155: NNUEArchFile MUST precede NNUEArch=true!
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\pipeline\tools\spsa_tune.py `
  v3p_g3_eval_margins_r1 `
  <PLACED_PGO_FORGE_EXE> `
  2500 8 30000 10 `
  NNUEArchFile=<PLACED_G3_FNN3> `
  NNUEArch=true `
  MateAlphaGuard=true NonPawnCorrection=true CuckooRep=true HistRework=2 TtPruneV2=true CorrHistV2=true DrawJitter=2 `
  LmrQuietBase=132 LmrQuietDivisor=176 LmrNoisyBase=25 LmrNoisyDivisor=336 LmrHistoryDivisor=6721 LmrCutoffThreshold=9 `
  NullMoveMinDepth=2 NullMoveBase=5 NullMoveDepthDivisor=4 NullMoveEvalDivisor=184 `
  LmpBase=13 HistoryPruneDepth=2 HistoryPruneMultiplier=1945 `
  HistoryBonusQuadratic=49 HistoryBonusLinear=90 HistoryBonusMax=2429 `
  SingularDepth=6 SingularMargin=3 IirDepth=5 CheckExtensionDepth=3 `
  RfpDepth=6 RfpMargin=84 RfpImproving=37 `
  RazorDepth=3 RazorBase=182 RazorMultiplier=379 `
  FutilityDepth=8 FutilityBase=12 FutilityMultiplier=59 `
  SeeQuietMultiplier=15 SeeNoisyMultiplier=83 `
  ProbcutDepth=7 ProbcutMargin=168 QsFutilityMargin=123 AspirationDelta=16 `
  MaterialCorrectionWeight=48 CaptureFutilityBase=45 FailLowContinuationBonus=41 EvalSwingMult=15
  # Add LmrDeeperShallower=true only if independently confirmed at equal time!
```

## Verification Rule (R5)
- Never adopt tuned values directly from `state.json`.
- Run an independent pre-declared `2,000g @ 6+0.06` equal-time GPU-idle confirmation vs the live Big Tune `v3_uci_options` on the exact same binary & net before updating `config.forge.toml`.
