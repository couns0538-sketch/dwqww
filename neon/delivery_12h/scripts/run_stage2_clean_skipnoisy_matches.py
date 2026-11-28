"""Declared 1,000g @ 50k Head-to-Head Matches on Clean Quiet-Filtered (--skip-fqs-noisy) Stage-2 Arms.

Tests every Filter Quest hypothesis on NON-COLLAPSED nets (OLS Q ~ 1016 cp, +700 Elo above keep_noisy!):
  1. G4a_quiet: --loss-pow 2.5 vs G3b_skipnoisy (loss_pow 2.0)
  2. G4b_quiet: --ob-reweight cc0 vs G3b_skipnoisy
  3. EXP-F1_quiet (eq-raw): s2q_f1_hard vs G3b_skipnoisy
  4. EXP-F1_quiet (eq-ret): s2q_f1_hard vs s2q_f1_ctrl_eqret
  5. EXP-F2_quiet (first vs ctrl): s2q_f2_dedup_first vs G3b_skipnoisy
  6. EXP-F2_quiet (avg vs first):  s2q_f2_dedup_avg vs s2q_f2_dedup_first
  7. EXP-R1_quiet (0.5% 16k rescore): s2q_r1_rescore16k_0p5pct vs s2q_f2_dedup_avg
  8. EXP-R1b_quiet (2% opp-castle 16k rescore): s2q_r1b_rescore16k_2pct_oppcastle vs s2q_f2_dedup_avg
  9. EXP-W3_quiet (soft-weight vs dedup_avg): s2q_w3_soft_weight vs s2q_f2_dedup_avg
 10. EXP-W3_quiet (soft-weight vs F1_hard):   s2q_w3_soft_weight vs s2q_f1_hard
"""
from __future__ import annotations

import subprocess
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
FQ = LAB / "neon/filter_quest"
PY = str(LAB / "venv/Scripts/python.exe")
RUNNER = str(FIX / "run_net_match.py")
V3P_EXE = str(FIX / "builds/v3p_fused_v3_engine.exe")
G3B = FIX / "gpu_runs/G3b_cc0_skip_noisy/cand.fnn3"
S2Q = FQ / "stage2_runs_quiet"
MATCHES = FIX / "matches"


def run_pair(name: str, cand: Path, base: Path, seed: int, rule: str) -> None:
    if (MATCHES / name / "summary.json").exists():
        print(f"SKIP (done): {name}", flush=True)
        return
    if not cand.exists() or not base.exists():
        print(f"SKIP (missing net): {name}", flush=True)
        return
    print(f"=== LAUNCH {name} (1000g @ 50k) ===", flush=True)
    subprocess.run([
        PY, RUNNER, "--name", name,
        "--cand-exe", V3P_EXE, "--base-exe", V3P_EXE,
        "--cand-net", str(cand), "--base-net", str(base),
        "--games", "1000", "--nodes", "50000", "--concurrency", "6", "--seed", str(seed),
        "--rule", rule,
    ], check=False)


def main() -> int:
    pairs = [
        ("S2Q_G4a_losspow25_vs_G3b_1000g_50k", S2Q / "s2q_g4a_losspow25/cand.fnn3", G3B, 202611801,
         "Clean quiet (--skip-fqs-noisy) --loss-pow 2.5 vs 2.0 on identical 2M CC0 4k + 3 anchors"),
        ("S2Q_G4b_obreweight_vs_G3b_1000g_50k", S2Q / "s2q_g4b_obreweight/cand.fnn3", G3B, 202611802,
         "Clean quiet (--skip-fqs-noisy) --ob-reweight cc0 vs unweighted G3b"),
        ("S2Q_EXP_F1_hard_vs_G3b_eqraw_1000g_50k", S2Q / "s2q_f1_hard/cand.fnn3", G3B, 202611803,
         "Clean quiet Filter Quest EXP-F1 (equal-raw): Tier-2 hard filter vs G3b control"),
        ("S2Q_EXP_F1_hard_vs_ctrl_eqret_1000g_50k", S2Q / "s2q_f1_hard/cand.fnn3", S2Q / "s2q_f1_ctrl_eqret/cand.fnn3", 202611804,
         "Clean quiet Filter Quest EXP-F1 (equal-retained): Tier-2 hard filter vs G3b truncated to exact kept rows"),
        ("S2Q_EXP_F2_first_vs_G3b_1000g_50k", S2Q / "s2q_f2_dedup_first/cand.fnn3", G3B, 202611805,
         "Clean quiet Filter Quest EXP-F2: exact cross-shard dedup (first) vs undeduped G3b"),
        ("S2Q_EXP_F2_avg_vs_first_1000g_50k", S2Q / "s2q_f2_dedup_avg/cand.fnn3", S2Q / "s2q_f2_dedup_first/cand.fnn3", 202611806,
         "Clean quiet Filter Quest EXP-F2: score-averaged + sqrt(k)-weighted dedup vs first-occurrence dedup"),
        ("S2Q_EXP_R1_rescore16k_vs_dedup_avg_1000g_50k", S2Q / "s2q_r1_rescore16k_0p5pct/cand.fnn3", S2Q / "s2q_f2_dedup_avg/cand.fnn3", 202611807,
         "Clean quiet Filter Quest EXP-R1: 0.5% selective 16k Forge-only rescore vs dedup_avg"),
        ("S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_1000g_50k", S2Q / "s2q_r1b_rescore16k_2pct_oppcastle/cand.fnn3", S2Q / "s2q_f2_dedup_avg/cand.fnn3", 202611808,
         "Clean quiet Filter Quest EXP-R1b: 2.0% opposite-side-castled 16k Forge-only rescore vs dedup_avg"),
        ("S2Q_EXP_W3_softweight_vs_dedup_avg_1000g_50k", S2Q / "s2q_w3_soft_weight/cand.fnn3", S2Q / "s2q_f2_dedup_avg/cand.fnn3", 202611809,
         "Clean quiet Filter Quest EXP-W3: gradient-informed soft weighting (0 rows dropped) vs dedup_avg"),
        ("S2Q_EXP_W3_softweight_vs_f1_hard_1000g_50k", S2Q / "s2q_w3_soft_weight/cand.fnn3", S2Q / "s2q_f1_hard/cand.fnn3", 202611810,
         "Clean quiet Filter Quest EXP-W3 vs EXP-F1: soft-weighting vs hard-discarding head-to-head"),
    ]
    for nm, cn, bn, sd, rl in pairs:
        run_pair(nm, cn, bn, sd, rl)
    print("STAGE-2 QUIET HEAD-TO-HEAD MATCHES COMPLETE.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
