"""Clean Quiet (--skip-fqs-noisy) Server-Day FORGENN3-P Architecture Suite (~2.5 min total on RX 7900 XT).

Retrains all 3 Server-Day architectures with mandatory --skip-fqs-noisy (bit0=0) on the exact
G3b CC0+3-anchors dataset (restoring non-collapsed Q/P ~ 10.5 across all 3 archs!):
  - G5a_quiet_768p_kb8   (H=768,  kb=8)
  - G5b_quiet_1536p_kb8  (H=1536, kb=8)
  - G5c_quiet_1024p_kb16 (H=1024, kb=16)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
PY101 = str(LAB / "venv101/Scripts/python.exe")
PY = str(LAB / "venv/Scripts/python.exe")
V3P_EXE = str(FIX / "builds/v3p_fused_v3_engine.exe")
CC0_DIR = str(FIX / "cc0_shards_4k_v2_nodrawconf")
ANCHORS = [
    str(FIX / "anchors/dead_draws_20k_s5disjoint.fqs.z"),
    str(FIX / "anchors/won_endings_syzygy_20k.fqs.z"),
    str(FIX / "anchors/opening_ply012_anchors.fqs.z"),
]


def main() -> int:
    arms = [
        ("G5a_quiet_768p_kb8", 768, 8),
        ("G5b_quiet_1536p_kb8", 1536, 8),
        ("G5c_quiet_1024p_kb16", 1024, 16),
    ]
    out_summary = {}
    for name, hidden, kb in arms:
        od = FIX / "gpu_runs" / name
        od.mkdir(parents=True, exist_ok=True)
        net = od / "cand.fnn3"
        if not net.exists():
            print(f"=== TRAIN {name} (H={hidden}, kb={kb}, skip-fqs-noisy, ep=40) ===", flush=True)
            r = subprocess.run([
                PY101, str(FIX / "train_v3p.py"),
                "--fqs-shards", CC0_DIR, "--fqs-repeat", "1",
                "--skip-fqs-noisy",
                "--anchor-shards", *ANCHORS, "--anchor-repeat", "4",
                "--out-dir", str(od),
                "--hidden", str(hidden), "--king-buckets", str(kb),
                "--epochs", "40", "--batch-size", "8192", "--lr", "0.0005",
                "--lr-cycles", "auto", "--w1-decay", "0.3", "--ob-smooth", "2e-6",
                "--mix", "0.85", "--loss-pow", "2.0", "--seed", "1",
                "--save-ckpt-every", "0", "--mem-need-gb", "8.0",
            ])
            assert r.returncode == 0 and net.exists(), f"Training failed for {name}"
        ef = od / "eval_full.json"
        if not ef.exists():
            subprocess.run([PY, str(FIX / "eval_net_full.py"), str(net), "--out", str(ef)], check=False)
        hs = od / "heldout_syzygy_4k.json"
        if not hs.exists():
            subprocess.run([PY, str(FIX / "eval_heldout_syzygy.py"), str(net), "--exe", V3P_EXE, "--out", str(hs)], check=False)
        mg = od / "master_gate_quick.json"
        if not mg.exists():
            subprocess.run([
                PY, str(FIX / "teamwork_wave2/streamC_gates/run_master_gates.py"),
                "--exe", V3P_EXE, "--net", str(net), "--quick", "--json-out", str(mg),
            ], check=False)
        m = json.loads((od / "metrics.json").read_text(encoding="utf-8")) if (od / "metrics.json").exists() else {}
        ej = json.loads(ef.read_text(encoding="utf-8")) if ef.exists() else {}
        hj = json.loads(hs.read_text(encoding="utf-8")) if hs.exists() else {}
        gj = json.loads(mg.read_text(encoding="utf-8")) if mg.exists() else {}
        ols = ej.get("m4_mid20_26_ols_piece_cp") or {}
        p_val = float(ols.get("P") or 1.0)
        out_summary[name] = {
            "hidden": hidden,
            "king_buckets": kb,
            "net_bytes": net.stat().st_size,
            "train_seconds": m.get("train_seconds"),
            "final_train_loss": m.get("final_train_loss"),
            "r0203_quiet_mix60": m.get("final_eval_r0203_quiet_mix60"),
            "m4_wdl_mse": ej.get("m4_wdl_mse"),
            "m4_corr": ej.get("m4_corr"),
            "ols_Q_over_P": round(float(ols.get("Q", 0.0)) / p_val, 3) if p_val else None,
            "ols_R_over_P": round(float(ols.get("R", 0.0)) / p_val, 3) if p_val else None,
            "syz_draw_med_cp": (hj.get("heldout_draws_2000") or {}).get("median_abs_cp"),
            "syz_win_ok_pct": (hj.get("heldout_wins_2000") or {}).get("sign_correct_pct"),
            "master_gate_hard_pass": gj.get("hard_pass"),
        }
    (FIX / "SERVERDAY_ARCH_SUITE_QUIET_SUMMARY.json").write_text(json.dumps(out_summary, indent=2), encoding="utf-8")
    print("SERVERDAY_ARCH_SUITE_QUIET_DONE:", json.dumps(out_summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
