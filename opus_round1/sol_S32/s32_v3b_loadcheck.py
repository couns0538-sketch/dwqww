"""S32: load .pos/.hce files with the v3b trainer's own loaders (RAM: load_set, mmap: load_set_mmap) and feed a few
batches through its make_batch/pack_batch, as training would; plus sign/label sanity statistics.

The trainer is imported from a renamed copy (PC rule: never run train_resid* by that name), e.g.
F:/opus_scratch/sol_s32/opus_nnue_smoke_v3b_loader.py = copy of F:/forge_nnue_train/tools/train_resid_v3b.py.
Nothing is trained and no file is written except --out.

  python -I -B s32_v3b_loadcheck.py --trainer COPY.py --pos A.pos [B.pos ...] --hce-dir DIR --out report.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np


def load_trainer(path: Path):
    spec = importlib.util.spec_from_file_location("opus_nnue_smoke_v3b_loader", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def label_stats(d) -> dict:
    n = d["n"]
    idx = np.arange(n, dtype=np.int64)
    score = d["score"][idx].astype(np.int64)
    hce = d["hce"][idx].astype(np.int64)
    meta = d["meta"][idx]
    stm_black = (meta & 1).astype(bool)
    wres = (meta >> 1).astype(np.int64)
    white_score = np.where(stm_black, -score, score)
    both = (np.abs(score) >= 100) & (np.abs(hce) >= 100)
    ahead, behind = white_score >= 300, white_score <= -300
    return {
        "n": int(n), "meta_values": sorted(int(v) for v in np.unique(meta)), "black_to_move": round(float(stm_black.mean()), 4),
        "white_result_x2_counts": {str(k): int((wres == k).sum()) for k in (0, 1, 2)},
        "score_min_max": [int(score.min()), int(score.max())], "hce_min_max": [int(hce.min()), int(hce.max())],
        "sign_score_eq_hce_where_both_ge_100": round(float((np.sign(score[both]) == np.sign(hce[both])).mean()), 4) if both.any() else None,
        "white_ahead_300_white_not_losing": round(float((wres[ahead] >= 1).mean()), 4) if ahead.any() else None,
        "white_behind_300_white_not_winning": round(float((wres[behind] <= 1).mean()), 4) if behind.any() else None,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trainer", type=Path, required=True)
    ap.add_argument("--pos", type=Path, nargs="+", required=True)
    ap.add_argument("--hce-dir", type=Path, required=True)
    ap.add_argument("--batches", type=int, default=4)
    ap.add_argument("--batch-size", type=int, default=16384)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.out.exists():
        ap.error("--out must be a new file")
    if "train_resid" in a.trainer.name:
        ap.error("pass a renamed copy of the trainer (PC rule)")
    tr = load_trainer(a.trainer)
    files = [str(p) for p in a.pos]
    report = {"tool": "s32_v3b_loadcheck", "trainer_copy": str(a.trainer), "trainer_sha256": sha256(a.trainer),
              "files": [{"pos": f, "pos_sha256": sha256(Path(f)), "hce_sha256": sha256(a.hce_dir / (Path(f).stem + ".hce")),
                         "header_n": tr.read_pos_header(f)} for f in files]}
    t = time.perf_counter()
    ram = tr.load_set(files, str(a.hce_dir))
    report["ram"] = {"n": int(ram["n"]), "seconds": round(time.perf_counter() - t, 2), "mem_gb": [round(x, 3) for x in tr.proc_mem_gb()]}
    t = time.perf_counter()
    mm = tr.load_set_mmap(files, str(a.hce_dir))
    report["mmap"] = {"n": int(mm["n"]), "seconds": round(time.perf_counter() - t, 2), "mem_gb": [round(x, 3) for x in tr.proc_mem_gb()]}
    rng = np.random.default_rng(20261027)
    sample = np.sort(rng.choice(ram["n"], size=min(200000, ram["n"]), replace=False))
    report["ram_equals_mmap_on_sample"] = bool(all(np.array_equal(ram[k][sample], mm[k][sample]) for k in ("boards", "score", "meta", "hce")))
    packed = []
    for b in range(a.batches):
        idx = np.sort(rng.choice(ram["n"], size=min(a.batch_size, ram["n"]), replace=False))
        x = tr.pack_batch(tr.make_batch(ram, idx), tr.K_DEFAULT)
        y = tr.pack_batch(tr.make_batch(mm, idx), tr.K_DEFAULT)
        codes = x[: len(idx) * 64]
        packed.append(bool(np.array_equal(x, y) and np.isfinite(x).all() and codes.min() >= 0 and codes.max() <= 12))
    report["batches_ram_eq_mmap_finite_codes_0_12"] = packed
    report["labels"] = label_stats(ram)
    report["pass"] = (report["ram"]["n"] == report["mmap"]["n"] == sum(f["header_n"] for f in report["files"]) and
                      report["ram_equals_mmap_on_sample"] and all(packed))
    a.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
