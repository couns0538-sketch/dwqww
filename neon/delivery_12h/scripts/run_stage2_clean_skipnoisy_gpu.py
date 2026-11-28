"""Quiet-Filtered (--skip-fqs-noisy) Stage-2 Filter Quest GPU Ablation Suite (9 arms, ~6 min GPU).

Following the monumental G3b_skipnoisy vs G3a_keepnoisy (+699.72 Elo, 972-21-7) discovery
(CC0_NOISY_VS_QUIET_FORENSIC.json: keeping 17.12% noisy bit0=1 mid-exchange rows collapses scratch
PSQT/FT OLS Q from 1016 cp to 199 cp!), trains ALL Filter Quest Stage-2 arms cleanly with
--skip-fqs-noisy against the proven non-collapsed G3b_cc0_skip_noisy baseline!
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
import zlib
from pathlib import Path

import numpy as np

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
FQ = LAB / "neon/filter_quest"
S2_DATA = FQ / "stage2_data"
S2Q_RUNS = FQ / "stage2_runs_quiet"
PY_CPU = str(LAB / "venv/Scripts/python.exe")
PY_GPU = str(LAB / "venv101/Scripts/python.exe")
V3P_EXE = str(FIX / "builds/v3p_fused_v3_engine.exe")
CC0_DIR = FIX / "cc0_shards_4k_v2_nodrawconf"
ANCHORS = [
    str(FIX / "anchors/dead_draws_20k_s5disjoint.fqs.z"),
    str(FIX / "anchors/won_endings_syzygy_20k.fqs.z"),
    str(FIX / "anchors/opening_ply012_anchors.fqs.z"),
]
FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)), ("stm", np.uint8), ("score16", np.int16),
    ("res8", np.int8), ("flags", np.uint8), ("weight_u8", np.uint8),
])


def count_quiet_rows(data_dir: Path) -> int:
    tot = 0
    for sp in sorted(list(data_dir.glob("*.fqs")) + list(data_dir.glob("*.fqs.z"))):
        raw = zlib.decompress(sp.read_bytes()) if sp.name.endswith(".z") else sp.read_bytes()
        a = np.frombuffer(raw, dtype=FQS_DTYPE, offset=8)
        tot += int(((a["flags"] & 3) == 0).sum())
    return tot


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def run_arm(name: str, data_dir: Path, extra_args: list[str]) -> dict:
    od = S2Q_RUNS / name
    od.mkdir(parents=True, exist_ok=True)
    net = od / "cand.fnn3"
    if not net.exists():
        print(f"=== TRAIN QUIET STAGE-2 {name} (--skip-fqs-noisy) ===", flush=True)
        cmd = [
            PY_GPU, str(FIX / "train_v3p.py"),
            "--fqs-shards", str(data_dir), "--fqs-repeat", "1",
            "--skip-fqs-noisy",
            "--anchor-shards", *ANCHORS, "--anchor-repeat", "4",
            "--out-dir", str(od),
            "--hidden", "1024", "--king-buckets", "8",
            "--epochs", "40", "--batch-size", "8192", "--lr", "0.0005",
            "--lr-cycles", "auto", "--w1-decay", "0.3", "--ob-smooth", "2e-6",
            "--mix", "0.85", "--seed", "1",
            "--save-ckpt-every", "0", "--mem-need-gb", "8",
            *extra_args,
        ]
        r = subprocess.run(cmd)
        assert r.returncode == 0 and net.exists(), f"Failed {name}"
    ef = od / "eval_full.json"
    if not ef.exists():
        subprocess.run([PY_CPU, str(FIX / "eval_net_full.py"), str(net), "--out", str(ef)], check=False)
    hs = od / "heldout_syzygy_4k.json"
    if not hs.exists():
        subprocess.run([PY_CPU, str(FIX / "eval_heldout_syzygy.py"), str(net), "--exe", V3P_EXE, "--out", str(hs)], check=False)
    ej = json.loads(ef.read_text(encoding="utf-8")) if ef.exists() else {}
    hj = json.loads(hs.read_text(encoding="utf-8")) if hs.exists() else {}
    m = json.loads((od / "metrics.json").read_text(encoding="utf-8")) if (od / "metrics.json").exists() else {}
    return {
        "name": name,
        "net": str(net),
        "sha256": sha256_file(net),
        "train_loss": m.get("final_train_loss"),
        "r0203_quiet_mix60": m.get("final_eval_r0203_quiet_mix60"),
        "m4_wdl_mse": ej.get("m4_wdl_mse"),
        "m4_corr": ej.get("m4_corr"),
        "ols_Q": (ej.get("m4_mid20_26_ols_piece_cp") or {}).get("Q"),
        "syz_draw_med_cp": (hj.get("heldout_draws_2000") or {}).get("median_abs_cp"),
        "syz_win_ok_pct": (hj.get("heldout_wins_2000") or {}).get("sign_correct_pct"),
    }


def main() -> int:
    f1_quiet_kept = count_quiet_rows(S2_DATA / "cc0_f1_hard")
    print(f"F1_QUIET_KEPT_ROWS={f1_quiet_kept:,}", flush=True)
    specs = [
        ("s2q_g4a_losspow25", CC0_DIR, ["--loss-pow", "2.5"]),
        ("s2q_g4b_obreweight", CC0_DIR, ["--ob-reweight", "cc0"]),
        ("s2q_f1_hard", S2_DATA / "cc0_f1_hard", []),
        ("s2q_f1_ctrl_eqret", CC0_DIR, ["--max-rows", str(f1_quiet_kept)]),
        ("s2q_f2_dedup_first", S2_DATA / "cc0_f2_dedup_first", []),
        ("s2q_f2_dedup_avg", S2_DATA / "cc0_f2_dedup_avg", ["--use-shard-weights"]),
        ("s2q_r1_rescore16k_0p5pct", S2_DATA / "cc0_r1_rescore16k_0p5pct", ["--use-shard-weights"]),
        ("s2q_r1b_rescore16k_2pct_oppcastle", S2_DATA / "cc0_r1b_rescore16k_2pct_oppcastle", ["--use-shard-weights"]),
        ("s2q_w3_soft_weight", S2_DATA / "cc0_w3_soft_weight", ["--use-shard-weights"]),
    ]
    summary = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "f1_quiet_kept": f1_quiet_kept, "arms": {}}
    for name, ddir, ex in specs:
        summary["arms"][name] = run_arm(name, ddir, ex)
    (FQ / "STAGE2_QUIET_GPU_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE2_QUIET_GPU_DONE:", json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
