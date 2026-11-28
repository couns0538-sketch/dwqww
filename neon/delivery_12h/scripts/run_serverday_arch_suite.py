"""Train & Gate the 3 Server-Day Candidate FORGENN3-P Architectures on the exact G3a CC0+3-anchors dataset
(~3.5 min total on RX 7900 XT; zero C++ changes required!):
  - G5a_cc0_768p_kb8   (H=768,  kb=8,  Pairwise+PSQT — 384 L1 weights, FASTER than live 768w SCReLU!)
  - G5b_cc0_1536p_kb8  (H=1536, kb=8,  Pairwise+PSQT — Server-Day 2B-pos wide architecture!)
  - G5c_cc0_1024p_kb16 (H=1024, kb=16, Pairwise+PSQT — Server-Day 16-king-bucket architecture!)
Provides real trained .fnn3 nets for clean GPU-idle PGO NPS benchmarking across all 4 architectures
(live 768w SCReLU vs 768p/kb8 vs 1024p/kb8 vs 1536p/kb8 vs 1024p/kb16).
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
        ("G5a_cc0_768p_kb8", 768, 8),
        ("G5b_cc0_1536p_kb8", 1536, 8),
        ("G5c_cc0_1024p_kb16", 1024, 16),
    ]
    out_summary = {}
    for name, hidden, kb in arms:
        od = FIX / "gpu_runs" / name
        od.mkdir(parents=True, exist_ok=True)
        net = od / "cand.fnn3"
        if not net.exists():
            print(f"=== TRAIN {name} (H={hidden}, kb={kb}, ep=40) ===", flush=True)
            r = subprocess.run([
                PY101, str(FIX / "train_v3p.py"),
                "--fqs-shards", CC0_DIR, "--fqs-repeat", "1",
                "--anchor-shards", *ANCHORS, "--anchor-repeat", "4",
                "--out-dir", str(od),
                "--hidden", str(hidden), "--king-buckets", str(kb),
                "--epochs", "40", "--batch-size", "8192", "--lr", "0.0005",
                "--lr-cycles", "auto", "--w1-decay", "0.3", "--ob-smooth", "2e-6",
                "--mix", "0.85", "--loss-pow", "2.0", "--seed", "1",
                "--save-ckpt-every", "0", "--mem-need-gb", "8.0",
            ])
            assert r.returncode == 0 and net.exists(), f"Training failed for {name}"
        # Score offline + Master Gates --quick + 4k held-out Syzygy
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
        out_summary[name] = {
            "hidden": hidden,
            "king_buckets": kb,
            "net_bytes": net.stat().st_size,
            "train_seconds": m.get("train_seconds"),
            "final_train_loss": m.get("final_train_loss"),
            "r0203_quiet_mix60": m.get("final_eval_r0203_quiet_mix60"),
            "m4_wdl_mse": ej.get("m4_wdl_mse"),
            "m4_corr": ej.get("m4_corr"),
            "syz_draw_med_cp": (hj.get("heldout_draws_2000") or {}).get("median_abs_cp"),
            "syz_win_ok_pct": (hj.get("heldout_wins_2000") or {}).get("sign_correct_pct"),
            "master_gate_hard_pass": gj.get("hard_pass"),
        }
    (FIX / "SERVERDAY_ARCH_SUITE_SUMMARY.json").write_text(json.dumps(out_summary, indent=2), encoding="utf-8")
    print("SERVERDAY_ARCH_SUITE_DONE:", json.dumps(out_summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
