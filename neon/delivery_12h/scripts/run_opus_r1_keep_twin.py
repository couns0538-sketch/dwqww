r"""Opus Request R1 Twin (OPUS-2811-CLOCK-RECOUNTED-AND-R1-TWIN, 01:12 PC):
Exact twin of run_opus_r1_live768_skipnoisy.py WITH --keep-noisy (same runner, same seed=1,
same exact r0178..r0202 25-round window, same b_full.pt residual teacher w=0.2, lr=0.0005,
batch=8192, 40 epochs, mix=0.75, w1-decay=0.3, hidden=768, FORGE_COMPACT=1, FORGE_STEP_V2=1,
FORGE_FUSED_STEP=1). ONLY the --keep-noisy flag differs vs OPUS_R1_live768_skipnoisy!

STRICT READ-ONLY SAFETY ON runs/forge/:
Zero .cache.npz files are EVER written inside C:\nnue-lab\runs\forge\. All outputs go strictly
to C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_keepnoisy_twin\.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
SKIP_DIR = FIX / "gpu_runs/OPUS_R1_live768_skipnoisy"
PY_CPU = str(LAB / "venv/Scripts/python.exe")
BASE_EXE = str(FIX / "builds/base_r15dsg.exe")
R0202_NET = LAB / "runs/forge/r0202/train/cand.fnn3"
R0067_NET = LAB / "runs/forge/r0067/train/cand.fnn3"

LIVE_ENV = {
    "FORGE_COMPACT": "1",
    "FORGE_STEP_V2": "1",
    "FORGE_TRITON2_BLOCK": "512",
    "FORGE_TRITON2_KC": "32",
    "FORGE_TRITON2_BBLOCK": "256",
    "FORGE_TRITON2_BKC": "16",
    "FORGE_TRITON2_WARPS": "4",
    "FORGE_TRITON2_LPOS": "16",
    "FORGE_DENSE_GW_R": "128",
    "FORGE_DENSE_GW_BC": "128",
    "FORGE_DENSE_GW_WARPS": "8",
    "FORGE_DENSE_FWD_WARPS": "1",
    "FORGE_FUSED_STEP": "1",
    "FORGE_PARSE_PROCS": "8",
}
for _k, _v in LIVE_ENV.items():
    os.environ[_k] = _v

sys.path.insert(0, str(LAB / "pipeline"))
import forge_train as ft  # noqa: E402
import forge_train_v3 as v3  # noqa: E402


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--skip-noisy", action="store_true", help="Train without --keep-noisy (for seed-2 skip replicate)")
    args = ap.parse_args()

    keep_noisy = not args.skip_noisy
    if keep_noisy:
        OUT_DIR = FIX / ("gpu_runs/OPUS_R1_live768_keepnoisy_twin" if args.seed == 1 else f"gpu_runs/OPUS_R1_live768_keepnoisy_seed{args.seed}")
    else:
        OUT_DIR = FIX / (f"gpu_runs/OPUS_R1_live768_skipnoisy_seed{args.seed}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    datasets = [str(LAB / f"runs/forge/r{r:04d}/data/filtered.plain") for r in range(178, 203)]
    val_path = str(LAB / "runs/forge/val/val.plain")
    hce_exe = str(LAB / "forge/build/hce_dump.exe")
    teacher = str(LAB / "runs/forge/teachers/b_full.pt")
    model_pt = OUT_DIR / "cand.pt"
    net_fnn3 = OUT_DIR / "cand.fnn3"

    decl = {
        "written": time.strftime("%Y-%m-%d %H:%M:%S"),
        "experiment": f"OPUS_R1_live768_{'keepnoisy' if keep_noisy else 'skipnoisy'}_seed{args.seed}",
        "request_ref": "OPUS-2811-CLOCK-RECOUNTED-AND-R1-TWIN Point 3",
        "arch": "live FORGENN3 hidden=768 (pipeline/forge_train_v3.py unchanged)",
        "window": "r0178..r0202 (exact 25 rounds)",
        "seed": args.seed,
        "keep_noisy": keep_noisy,
        "diff_vs_R1_skip": "ONLY --keep-noisy flag differs; identical runner, window, epochs=40, lr=0.0005, batch=8192, mix=0.75, w1-decay=0.3, distill=b_full.pt w=0.2",
        "skip_twin_net": str(SKIP_DIR / "cand.fnn3"),
        "r0067_net": str(R0067_NET),
        "r0067_sha256": sha256_file(R0067_NET),
        "decision_rule": "Decide R1-skip vs R1-keep at 250k nodes (1,000 games, base_r15dsg both sides). Decision rule: 95% lower bound > 0, else inconclusive. If positive, train seed 2 of both, then R1-skip vs r0067 at 250k and 6+0.06 (concurrency=7).",
    }
    (OUT_DIR / "declaration.json").write_text(json.dumps(decl, indent=2), encoding="utf-8")

    if not net_fnn3.exists():
        orig_load_one = ft._load_one
        orig_count_one = getattr(ft, "_count_one", None)
        count_memo: dict[tuple[str, bool, bool], int] = {}

        def safe_load_one(path: str, hce_e: str, skip_noisy: bool, skip_check: bool) -> dict:
            default_filter = skip_noisy and skip_check
            existing_cache = Path(str(path) + (".cache.npz" if default_filter else f".cache-n{int(skip_noisy)}c{int(skip_check)}.npz"))
            if existing_cache.exists():
                return orig_load_one(path, hce_e, skip_noisy, skip_check)
            d = ft._parse_plain([path], hce_e, skip_noisy, skip_check)
            count_memo[(path, skip_noisy, skip_check)] = int(d["codes"].shape[0])
            return d

        def safe_count_one(path: str, hce_e: str, skip_noisy: bool, skip_check: bool) -> int:
            default_filter = skip_noisy and skip_check
            existing_cache = Path(str(path) + (".cache.npz" if default_filter else f".cache-n{int(skip_noisy)}c{int(skip_check)}.npz"))
            if existing_cache.exists() and orig_count_one is not None:
                return orig_count_one(path, hce_e, skip_noisy, skip_check)
            k = (path, skip_noisy, skip_check)
            if k in count_memo:
                return count_memo[k]
            d = ft._parse_plain([path], hce_e, skip_noisy, skip_check)
            n = int(d["codes"].shape[0])
            count_memo[k] = n
            del d
            return n

        ft._load_one = safe_load_one
        if orig_count_one is not None:
            ft._count_one = safe_count_one

        t0 = time.time()
        sys.argv = [
            "forge_train_v3.py", "train",
            "--datasets", *datasets,
            "--val", val_path,
            "--out-model", str(model_pt),
            "--hce-exe", hce_exe,
            "--epochs", "40",
            "--lr", "0.0005",
            "--batch-size", "8192",
            "--lr-cycles", "auto",
            "--w1-decay", "0.3",
            "--mix", "0.75",
            "--distill-net", teacher,
            "--distill-weight", "0.2",
            "--teacher-once",
            "--seed", str(args.seed),
            *(["--keep-noisy"] if keep_noisy else []),
            "--hidden", "768",
        ]
        rc = v3.main()
        assert rc == 0 and model_pt.exists(), f"R1-keep twin train failed rc={rc}"

        sys.argv = ["forge_train_v3.py", "export", "--model", str(model_pt), "--net", str(net_fnn3)]
        rc2 = v3.main()
        assert rc2 == 0 and net_fnn3.exists(), f"R1-keep twin export failed rc={rc2}"
        elapsed = time.time() - t0
    else:
        elapsed = 0.0

    ef = OUT_DIR / "eval_full.json"
    if not ef.exists():
        subprocess.run([PY_CPU, str(FIX / "eval_net_full.py"), str(net_fnn3), "--exe", BASE_EXE, "--out", str(ef)], check=False)
    res = {
        "finished": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_s": round(elapsed, 1),
        "net": str(net_fnn3),
        "net_bytes": net_fnn3.stat().st_size,
        "net_sha256": sha256_file(net_fnn3),
        "eval_full": json.loads(ef.read_text(encoding="utf-8")) if ef.exists() else None,
    }
    (OUT_DIR / "r1_keep_summary.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print("OPUS_R1_LIVE768_KEEPNOISY_TWIN_DONE:", json.dumps(res, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
