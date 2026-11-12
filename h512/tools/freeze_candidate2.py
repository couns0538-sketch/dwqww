#!/usr/bin/env python
"""freeze_candidate2.py - JOB E phase 2 (2026-11-11): freeze a later candidate from the continued run. Own code.

  freeze_candidate2.py --run-dir _work/runs/phase2 --prev h512/results/step7/FROZEN_CANDIDATE.json \
                       --label 2 --out h512/results/phase2/FROZEN_CANDIDATE_2.json

Rule (declared in results/phase2/PHASE2_DECLARATION.md before any phase-2 result): the checkpoint with the lowest
`select_2m.mse_b0.6` in the run's metrics.jsonl (the earliest on an exact tie) becomes a new candidate only if that
loss is at least --min-improve (2e-5) below the previous candidate's. Otherwise nothing is frozen and the output
file records that. No test set is read here. The net and its float checkpoint are copied to _work/nets/.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time


def digest(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--prev", required=True, help="FROZEN_CANDIDATE json of the previous candidate")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-improve", type=float, default=2e-5)
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit("refused: the output file exists (a freeze is done once)")
    entries = [json.loads(line) for line in open(os.path.join(a.run_dir, "metrics.jsonl"), encoding="utf-8")]
    prev = json.load(open(a.prev, encoding="utf-8"))
    best = min(entries, key=lambda e: (e["metric"], e["seen"]))
    gain = prev["metric"] - best["metric"]
    rec = {"frozen": time.strftime("%Y-%m-%dT%H:%M:%S"), "label": a.label, "run_dir": a.run_dir,
           "rule": f"lowest select_2m.mse_b0.6 over the {len(entries)} checkpoints of the run so far; a new candidate only if "
                   f"at least {a.min_improve} below the previous candidate; no test set was read",
           "previous_candidate": {"file": a.prev, "seen": prev.get("seen"), "metric": prev["metric"], "net_md5": prev["net_md5"]},
           "checkpoints_considered": len(entries), "last_checkpoint_seen": entries[-1]["seen"],
           "best_seen": best["seen"], "best_metric": best["metric"], "gain_over_previous": gain,
           "all_checkpoints": [{"seen": e["seen"], "stage": e["stage"], "reason": e["reason"], "metric": e["metric"]} for e in entries]}
    if gain < a.min_improve:
        rec["new_candidate"] = False
        rec["finding"] = "no checkpoint is at least min-improve below the previous candidate; the previous candidate stays"
    else:
        src = os.path.join(a.run_dir, best["net"])
        name = f"h512_cand_seen{best['seen']:011d}.fnn3"
        dst = os.path.join(a.repo, "_work", "nets", name)
        fdst = dst[:-5] + "_float.pt"
        if os.path.exists(dst) or os.path.exists(fdst):
            sys.exit(f"refused: {dst} or its float checkpoint already exists")
        if digest(src, "md5") != digest(os.path.join(a.run_dir, "best.fnn3"), "md5"):
            sys.exit("refused: best.fnn3 in the run folder is not the lowest-loss checkpoint's net")
        shutil.copyfile(src, dst)
        shutil.copyfile(os.path.join(a.run_dir, "best.pt"), fdst)
        rec.update({"new_candidate": True, "seen": best["seen"], "stage": best["stage"], "reason": best["reason"],
                    "index": best["index"], "unique_training_rows": 271830023,
                    "passes_over_training_rows": round(best["seen"] / 271830023, 2), "metric": best["metric"],
                    "scores": best["scores"], "lr": best["lr"], "alpha": best["alpha"], "net": dst,
                    "net_md5": digest(dst, "md5"), "net_sha256": digest(dst, "sha256"), "net_bytes": os.path.getsize(dst),
                    "net_checksum_fnv1a": best["checksum"], "float_checkpoint": fdst, "float_checkpoint_md5": digest(fdst, "md5")})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1, sort_keys=True)
    keys = ("new_candidate", "best_seen", "best_metric", "gain_over_previous", "net", "net_md5", "net_sha256", "float_checkpoint_md5")
    print(json.dumps({k: rec.get(k) for k in keys}, indent=1))


if __name__ == "__main__":
    main()
