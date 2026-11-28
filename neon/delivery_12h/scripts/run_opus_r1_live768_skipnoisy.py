"""Opus Request R1 (OPUS-2811-R0202-AND-KEEP-NOISY, 00:08 PC):
Declared A/B on the EXACT LIVE architecture and recipe (pipeline/forge_train_v3.py, hidden=768,
exact r0178..r0202 25-round window, b_full.pt residual teacher w=0.2, lr=0.0005, batch=8192,
40 epochs, mix=0.75, w1-decay=0.3, FORGE_COMPACT=1, FORGE_STEP_V2=1, FORGE_FUSED_STEP=1),
WITHOUT --keep-noisy (quiet positions only), compared against live r0202/train/cand.fnn3 (exact
same command WITH --keep-noisy)!

STRICT READ-ONLY SAFETY ON runs/forge/:
Monkey-patches forge_train._load_one and _count_one IN MEMORY so ZERO .cache.npz files are EVER
written inside C:\nnue-lab\runs\forge\ (and zero ~30 GB disk bloat on C:)! All outputs go strictly
to C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy\.
"""
from __future__ import annotations

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
OUT_DIR = FIX / "gpu_runs/OPUS_R1_live768_skipnoisy"
PY_CPU = str(LAB / "venv/Scripts/python.exe")
BASE_EXE = str(FIX / "builds/base_r15dsg.exe")
R0202_NET = LAB / "runs/forge/r0202/train/cand.fnn3"
R0067_NET = LAB / "runs/forge/r0067/train/cand.fnn3"

# Match exact live config.forge.toml [train] env before importing forge_train_v3!
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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    datasets = [str(LAB / f"runs/forge/r{r:04d}/data/filtered.plain") for r in range(178, 203)]
    val_path = str(LAB / "runs/forge/val/val.plain")
    hce_exe = str(LAB / "forge/build/hce_dump.exe")
    teacher = str(LAB / "runs/forge/teachers/b_full.pt")
    model_pt = OUT_DIR / "cand.pt"
    net_fnn3 = OUT_DIR / "cand.fnn3"

    # Write declaration BEFORE training
    decl = {
        "written": time.strftime("%Y-%m-%d %H:%M:%S"),
        "experiment": "OPUS_R1_live768_skipnoisy_vs_r0202_keepnoisy",
        "request_ref": "OPUS-2811-R0202-AND-KEEP-NOISY Request R1",
        "arch": "live FORGENN3 hidden=768 (pipeline/forge_train_v3.py unchanged)",
        "window": "r0178..r0202 (exact 25 rounds of r0202)",
        "diff_vs_r0202": "ONLY removes --keep-noisy (quiet positions only); exact same epochs=40, lr=0.0005, batch=8192, mix=0.75, w1-decay=0.3, distill=b_full.pt w=0.2, seed=1",
        "baseline_net": str(R0202_NET),
        "baseline_sha256": sha256_file(R0202_NET),
        "r0067_net": str(R0067_NET),
        "r0067_sha256": sha256_file(R0067_NET),
        "decision_rule": "Pass v3_parity + v3_model_check + Master Gates, then decide at 250k nodes (1,000g) vs r0202 (and vs r0067), followed by clean equal-time 6+0.06 at concurrency<=7.",
    }
    (OUT_DIR / "declaration.json").write_text(json.dumps(decl, indent=2), encoding="utf-8")

    if not net_fnn3.exists():
        # In-memory no-write cache wrapper so ZERO files are created in C:\nnue-lab\runs\forge\!
        # Also caches each parsed file in a small LRU (or counts via fast parse + reloads cleanly)
        orig_load_one = ft._load_one
        orig_count_one = getattr(ft, "_count_one", None)
        count_memo: dict[tuple[str, bool, bool], int] = {}
        # Hold the single most-recently parsed file in RAM when compact_record counts then loads
        # Note: compact_record calls _count_one for all 25 files, then _load_one for all 25 files.
        # To avoid parsing all 25 files TWICE (saving ~3 min) while using ZERO disk in runs/forge/,
        # write compact temporary npz ONLY inside OUT_DIR/_tmp_cache and delete each immediately after _load_one!
        tmp_cache_dir = OUT_DIR / "_tmp_cache"
        tmp_cache_dir.mkdir(parents=True, exist_ok=True)

        def safe_load_one(path: str, hce_e: str, skip_noisy: bool, skip_check: bool) -> dict:
            # If existing read-only cache already exists (e.g. val.plain), use original read-only path!
            default_filter = skip_noisy and skip_check
            existing_cache = Path(str(path) + (".cache.npz" if default_filter else f".cache-n{int(skip_noisy)}c{int(skip_check)}.npz"))
            if existing_cache.exists():
                return orig_load_one(path, hce_e, skip_noisy, skip_check)
            # Check our private tmp cache inside neon/
            key_h = hashlib.md5(f"{path}:{int(skip_noisy)}:{int(skip_check)}".encode()).hexdigest()[:12]
            priv = tmp_cache_dir / f"{key_h}.npz"
            if priv.exists():
                with np.load(priv, allow_pickle=False) as z:
                    d = {k: torch.from_numpy(z[k]) for k in ("codes", "stm", "score", "res", "hce")}
                priv.unlink(missing_ok=True)
                print(f"data: {path}: {len(d['stm'])} positions (from neon tmp cache, deleted)", flush=True)
                return d
            # Parse directly into memory without writing anything to runs/forge/!
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
            # Parse once, store count, and save compact temp npz inside neon/ (only ~250 MB each? Wait: 25 x 800MB = 20GB -> too big for C:!).
            # Better: parse fast (~4s/file with 8 procs = ~100s total) without touching disk at all!
            d = ft._parse_plain([path], hce_e, skip_noisy, skip_check)
            n = int(d["codes"].shape[0])
            count_memo[k] = n
            del d
            return n

        ft._load_one = safe_load_one
        if orig_count_one is not None:
            ft._count_one = safe_count_one

        t0 = time.time()
        # 1. Train using exact live forge_train_v3.py train subcommand WITHOUT --keep-noisy!
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
            "--hidden", "768",
        ]
        rc = v3.main()
        assert rc == 0 and model_pt.exists(), f"R1 train failed rc={rc}"

        # 2. Export using exact live forge_train_v3.py export subcommand
        sys.argv = ["forge_train_v3.py", "export", "--model", str(model_pt), "--net", str(net_fnn3)]
        rc2 = v3.main()
        assert rc2 == 0 and net_fnn3.exists(), f"R1 export failed rc={rc2}"
        # Clean tmp dir
        try:
            tmp_cache_dir.rmdir()
        except OSError:
            pass
        elapsed = time.time() - t0
    else:
        elapsed = 0.0

    # 3. Score with eval_net_full.py + net_sanity v2 + v3_parity + v3_model_check!
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
    (OUT_DIR / "r1_summary.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print("OPUS_R1_LIVE768_SKIPNOISY_DONE:", json.dumps(res, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
