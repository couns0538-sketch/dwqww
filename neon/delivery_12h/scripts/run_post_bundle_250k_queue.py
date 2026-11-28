"""Post-Bundle & Post-R1-Keep 250k Decision Match Queue (CPU, safe alongside GPU training or alone).

Runs:
  1. OPUS_R1_skip_vs_R1_keep_1000g_250k (base_r15dsg both sides, 1,000g @ 250k, conc=8) — exact Opus R1 decision!
  2. OPUS_R1_skip_vs_r0067_1000g_250k (base_r15dsg both sides, 1,000g @ 250k, conc=8) — direct check vs live r0067!
  3. Automatic 600g @ 250k verification (v3p_fused_v3_engine.exe both sides) of the top Stage-2 Clean Quiet
     Filter Quest winners (all S2Q_* 50k filter matches with point estimate >= +5.0 Elo, capped at top 3 by Elo),
     per Opus's 01:12 PC rule: 'The Stage-2 50k matches are filters only. A winner needs 250k before it counts.'
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
FQ = LAB / "neon/filter_quest"
PY = str(LAB / "venv/Scripts/python.exe")
RUNNER = str(FIX / "run_net_match.py")
BASE_EXE = str(FIX / "builds/base_r15dsg.exe")
V3P_EXE = str(FIX / "builds/v3p_fused_v3_engine.exe")
MATCHES = FIX / "matches"

R1_SKIP = FIX / "gpu_runs/OPUS_R1_live768_skipnoisy/cand.fnn3"
R1_KEEP = FIX / "gpu_runs/OPUS_R1_live768_keepnoisy_twin/cand.fnn3"
R0067 = LAB / "runs/forge/r0067/train/cand.fnn3"


def run_match(name: str, exe: str, cand: Path, base: Path, games: int, seed: int, rule: str, conc: int = 8, sprt: str = "") -> None:
    if (MATCHES / name / "summary.json").exists():
        print(f"SKIP (done): {name}", flush=True)
        return
    if not cand.exists() or not base.exists():
        print(f"SKIP (missing net): {name} cand={cand.exists()} base={base.exists()}", flush=True)
        return
    tag = f"SPRT [{sprt}] cap {games}g" if sprt else f"{games}g"
    print(f"=== LAUNCH {name} ({tag} @ 250k) ===", flush=True)
    cmd = [
        PY, RUNNER, "--name", name,
        "--cand-exe", exe, "--base-exe", exe,
        "--cand-net", str(cand), "--base-net", str(base),
        "--games", str(games), "--nodes", "250000", "--concurrency", str(conc), "--seed", str(seed),
        "--rule", rule,
    ]
    if sprt:
        cmd += ["--sprt", sprt]
    subprocess.run(cmd, check=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["all", "stage2", "r1"], default="all")
    ap.add_argument("--concurrency", type=int, default=8)
    args = ap.parse_args()

    if args.mode in ("all", "r1"):
        # 1. Opus R1 exact twin decision match amended before game 1 per OPUS-2811-R1-TEST-SIZE (SPRT [0, 10], cap 3000g @ 250k)
        run_match(
            "OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k",
            BASE_EXE, R1_SKIP, R1_KEEP, 3000, 202611951,
            "Opus R1 declared decision (OPUS-2811-R1-TEST-SIZE, amended before game 1): R1-skip vs R1-keep twin (identical runner/seed/window, ONLY --keep-noisy differs), normalized SPRT [0, 10] alpha=0.05 beta=0.05 cap 3,000g @ 250k. Cap without decision => inconclusive.",
            conc=args.concurrency,
            sprt="0,10",
        )

        # 2. Direct R1-skip vs live r0067 @ 250k (1000g)
        run_match(
            "OPUS_R1_skip_vs_r0067_1000g_250k",
            BASE_EXE, R1_SKIP, R0067, 1000, 202611952,
            "Opus R1 direct check vs live best r0067: R1-skip (live 768w without --keep-noisy on r0178..r0202) vs r0067, 1000g @ 250k.",
            conc=args.concurrency,
        )

    if args.mode in ("all", "stage2"):
        # 3. Auto-confirm top Stage-2 Clean Quiet (S2Q_*) winners (>= +5.0 Elo at 50k, top 3, excluding eqret control) at 250k (600g)
        s2q_winners = []
        for sp in sorted(MATCHES.glob("S2Q_*/summary.json")):
            if "eqret" in sp.parent.name:
                continue
            d = json.loads(sp.read_text(encoding="utf-8"))
            ex = d.get("pentanomial_exact") or {}
            elo = ex.get("elo")
            decl = d.get("declaration") or {}
            if isinstance(elo, (int, float)) and elo >= 5.0 and decl.get("cand_net") and decl.get("base_net"):
                s2q_winners.append((elo, sp.parent.name, Path(decl["cand_net"]), Path(decl["base_net"])))
        s2q_winners.sort(reverse=True)
        for idx, (elo50, orig_name, cnet, bnet) in enumerate(s2q_winners[:3]):
            nm250 = orig_name.replace("_1000g_50k", "_600g_250k_CONFIRM")
            run_match(
                nm250, V3P_EXE, cnet, bnet, 600, 202611960 + idx,
                f"Opus 01:12 PC 250k verification of Stage-2 quiet 50k filter winner {orig_name} (50k={elo50:+.2f} Elo); fresh seed, never pooled with 50k filter.",
                conc=args.concurrency,
            )

    print(f"POST_BUNDLE_250K_QUEUE_COMPLETE (mode={args.mode}).", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
