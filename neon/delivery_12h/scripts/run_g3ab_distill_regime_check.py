"""90-second Regime-Boundary Test: keep_noisy vs skip_noisy WITH r0067 teacher (distill_weight=0.2)
on identical 2M CC0 + 3 anchors (ZERO edits to train_v3p.py!).
Answers whether r0067 teacher prevents keep_noisy PSQT collapse or whether skip_noisy STILL wins!
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
PY_GPU = str(LAB / "venv101/Scripts/python.exe")
PY_CPU = str(LAB / "venv/Scripts/python.exe")
V3P_EXE = str(FIX / "builds/v3p_fused_v3_engine.exe")
CC0_DIR = str(FIX / "cc0_shards_4k_v2_nodrawconf")
TEACHER = str(LAB / "runs/forge/r0067/train/cand.pt")
ANCHORS = [
    str(FIX / "anchors/dead_draws_20k_s5disjoint.fqs.z"),
    str(FIX / "anchors/won_endings_syzygy_20k.fqs.z"),
    str(FIX / "anchors/opening_ply012_anchors.fqs.z"),
]


def main() -> int:
    out = {}
    for name, skip in [("G3a_distill_keep_noisy", False), ("G3b_distill_skip_noisy", True)]:
        od = FIX / "gpu_runs" / name
        od.mkdir(parents=True, exist_ok=True)
        net = od / "cand.fnn3"
        if not net.exists():
            cmd = [
                PY_GPU, str(FIX / "train_v3p.py"),
                "--fqs-shards", CC0_DIR, "--fqs-repeat", "1",
                "--anchor-shards", *ANCHORS, "--anchor-repeat", "4",
                "--distill-net", TEACHER, "--distill-weight", "0.2",
                "--out-dir", str(od),
                "--hidden", "1024", "--epochs", "40", "--batch-size", "8192",
                "--lr", "0.0005", "--lr-cycles", "auto", "--w1-decay", "0.3",
                "--ob-smooth", "2e-6", "--mix", "0.85", "--seed", "1",
                "--save-ckpt-every", "0", "--mem-need-gb", "8",
            ]
            if skip:
                cmd.append("--skip-fqs-noisy")
            r = subprocess.run(cmd)
            assert r.returncode == 0 and net.exists()
        ef = od / "eval_full.json"
        if not ef.exists():
            subprocess.run([PY_CPU, str(FIX / "eval_net_full.py"), str(net), "--out", str(ef)], check=False)
        ej = json.loads(ef.read_text(encoding="utf-8"))
        m = json.loads((od / "metrics.json").read_text(encoding="utf-8"))
        out[name] = {
            "skip_noisy": skip,
            "train_loss": m.get("final_train_loss"),
            "r0203_quiet_mix60": m.get("final_eval_r0203_quiet_mix60"),
            "m4_wdl_mse": ej.get("m4_wdl_mse"),
            "m4_corr": ej.get("m4_corr"),
            "ols_piece_cp": ej.get("m4_mid20_26_ols_piece_cp"),
        }
    (FIX / "G3AB_DISTILL_REGIME_CHECK.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("G3AB_DISTILL_REGIME_DONE:", json.dumps(out, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
