#!/usr/bin/env python
"""freeze_net.py - JOB E phase 2 (2026-11-11): freeze one already exported net as the next candidate. Own code.

  freeze_net.py --net _work/runs/avg/A12.fnn3 --float _work/runs/avg/A12.pt --tag A12 \
                --score h512/results/phase2/avg_A12_on_select_2m.json --others <score json> [...] \
                --prev h512/results/step7/FROZEN_CANDIDATE.json --label 2 --what "average of ..." \
                --out h512/results/phase2/FROZEN_CANDIDATE_2.json

Rule (results/phase2/PHASE2_DECLARATION.md): among all nets that are eligible at the time of the freeze, the one with
the lowest selection loss (`select_2m`, blend 0.6) becomes the candidate, and only if that loss is at least 2e-5 below
the previous candidate's. --score is the selection-set score of the chosen net (written by `train_h512_gpu.py score`);
--others are the score files of the other eligible nets, listed so that the choice is on record; the tool refuses if
one of them is lower. No test set is read. The net and its float state are copied to _work/nets/h512_cand_<tag>.*
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
    ap.add_argument("--net", required=True)
    ap.add_argument("--float", required=True, dest="float_pt")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--score", required=True)
    ap.add_argument("--others", nargs="*", default=[])
    ap.add_argument("--other-values", nargs="*", default=[], help="name=loss of eligible nets scored inside a run log")
    ap.add_argument("--prev", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--what", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-improve", type=float, default=2e-5)
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit("refused: the output file exists (a freeze is done once)")
    sc = json.load(open(a.score, encoding="utf-8"))
    if "select_2m" not in os.path.basename(sc["pos"]):
        sys.exit("refused: --score is not a selection-set score")
    if sc["net_md5"] != digest(a.net, "md5"):
        sys.exit("refused: --score was not made with this net")
    metric = sc["mse_b0.6"]
    field = []
    for o in a.others:
        d = json.load(open(o, encoding="utf-8"))
        if "select_2m" not in os.path.basename(d["pos"]):
            sys.exit(f"refused: {o} is not a selection-set score")
        field.append({"name": d.get("name") or os.path.basename(o), "metric": d["mse_b0.6"], "net_md5": d["net_md5"]})
    for ov in a.other_values:
        nm, val = ov.rsplit("=", 1)
        field.append({"name": nm, "metric": float(val)})
    lower = [f for f in field if f["metric"] < metric]
    if lower:
        sys.exit(f"refused: an eligible net has a lower selection loss: {lower}")
    prev = json.load(open(a.prev, encoding="utf-8"))
    gain = prev["metric"] - metric
    if gain < a.min_improve:
        sys.exit(f"refused: gain over the previous candidate {gain:.7f} is below {a.min_improve}")
    dst = os.path.join(a.repo, "_work", "nets", f"h512_cand_{a.tag}.fnn3")
    fdst = dst[:-5] + "_float.pt"
    if os.path.exists(dst) or os.path.exists(fdst):
        sys.exit("refused: the candidate files already exist")
    shutil.copyfile(a.net, dst)
    shutil.copyfile(a.float_pt, fdst)
    rec = {"frozen": time.strftime("%Y-%m-%dT%H:%M:%S"), "label": a.label, "what": a.what, "new_candidate": True,
           "rule": f"lowest select_2m.mse_b0.6 among the eligible nets at the time of the freeze; at least {a.min_improve} "
                   "below the previous candidate; no test set was read",
           "metric": metric, "scores": {"select_2m": {k: v for k, v in sc.items() if k.startswith(("mse_", "phase_", "rows"))}},
           "gain_over_previous": gain,
           "previous_candidate": {"file": a.prev, "metric": prev["metric"], "net_md5": prev["net_md5"]},
           "other_eligible_nets": sorted(field, key=lambda f: f["metric"]),
           "source_net": a.net, "source_float": a.float_pt,
           "net": dst, "net_md5": digest(dst, "md5"), "net_sha256": digest(dst, "sha256"), "net_bytes": os.path.getsize(dst),
           "float_checkpoint": fdst, "float_checkpoint_md5": digest(fdst, "md5")}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1, sort_keys=True)
    print(json.dumps({k: rec[k] for k in ("label", "what", "metric", "gain_over_previous", "net", "net_md5", "net_sha256")}, indent=1))


if __name__ == "__main__":
    main()
