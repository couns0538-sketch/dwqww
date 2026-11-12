#!/usr/bin/env python
"""freeze_candidate.py - JOB E (2026-11-11): freeze the candidate net from the staged run. Own code.

  freeze_candidate.py --run-dir _work/runs/main --out h512/results/step7/FROZEN_CANDIDATE.json

Selection uses the selection set only: the checkpoint with the lowest `select_2m.mse_b0.6` in metrics.jsonl (the
earliest one on an exact tie). The final-test set is not read here. The net is copied to
_work/nets/h512_cand_seen<presentations>.fnn3 and a net entry `h512_cand` plus a build configuration `h512_v3` are
added to fair_eval/configs.json (refused when they already exist: a candidate is frozen once).
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
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    a = ap.parse_args()
    entries = [json.loads(line) for line in open(os.path.join(a.run_dir, "metrics.jsonl"), encoding="utf-8")]
    best = min(entries, key=lambda e: (e["metric"], e["seen"]))
    status = json.load(open(os.path.join(a.run_dir, "status.json"), encoding="utf-8"))
    src = os.path.join(a.run_dir, best["net"])
    name = f"h512_cand_seen{best['seen']:011d}.fnn3"
    dst = os.path.join(a.repo, "_work", "nets", name)
    cfg_path = os.path.join(a.repo, "fair_eval", "configs.json")
    text = open(cfg_path, "r", encoding="utf-8").read()
    if '"h512_cand"' in text or '"h512_v3": {' in text or os.path.exists(a.out):
        sys.exit("refused: a candidate is already frozen (configs.json or the output file has it)")
    shutil.copyfile(src, dst)
    sha, md5 = digest(dst, "sha256"), digest(dst, "md5")
    if md5 != digest(os.path.join(a.run_dir, "best.fnn3"), "md5"):
        sys.exit("refused: best.fnn3 in the run folder is not the lowest-loss checkpoint's net")
    best_pt = os.path.join(a.run_dir, "best.pt")
    frozen = {
        "frozen": time.strftime("%Y-%m-%dT%H:%M:%S"), "rule": "lowest select_2m.mse_b0.6 over all checkpoints of the staged run; the final test was not read",
        "run_dir": a.run_dir, "checkpoints_considered": len(entries), "exit": status.get("exit"),
        "seen": best["seen"], "stage": best["stage"], "reason": best["reason"], "index": best["index"],
        "unique_training_rows": 271830023, "passes_over_training_rows": round(best["seen"] / 271830023, 2),
        "metric": best["metric"], "scores": best["scores"], "lr": best["lr"], "alpha": best["alpha"],
        "net": dst, "net_md5": md5, "net_sha256": sha, "net_bytes": os.path.getsize(dst), "net_checksum_fnv1a": best["checksum"],
        "float_checkpoint": best_pt, "float_checkpoint_md5": digest(best_pt, "md5"),
        "all_checkpoints": [{"seen": e["seen"], "stage": e["stage"], "reason": e["reason"], "metric": e["metric"]} for e in entries],
    }
    net_line = ('    "h512_cand": { "file": "%s", "sha256": "%s", "what": "JOB E frozen candidate: stand-alone H512 FORGENN3, '
                '%d presentations, selection loss %.6f" },\n' % (name, sha, best["seen"], best["metric"]))
    anchor_net = '    "h512_fb2best": {'
    cfg_block = '''    "h512_v3": {
      "path": "JOB E candidate: stand-alone integer NNUE v3 H512 (FORGE_NNUE_V3); the net is the whole evaluation, trained with the net loaded",
      "defines": ["-DFORGE_NNUE_V3=1"], "extra_units": ["nnue_v3.cpp", "search_v3.cpp"], "net": "h512_cand",
      "train_setoptions": ["setoption name NNUEArchFile value {NET}", "setoption name NNUEArch value true"],
      "run_setoptions": ["setoption name NNUEArchFile value {NET}", "setoption name NNUEArch value true"],
      "expect_nodes": [],
      "must_run": ["Worker::static_evaluate_v3\\\\(", "forge::nnue::v3::evaluate\\\\(", "forge::nnue::v3::apply_changes\\\\(", "forge::nnue::v3::refresh_cached\\\\("],
      "must_be_zero": ["forge::nnue::evaluate\\\\(", "forge::nnue::update\\\\(", "forge::nnue::refresh\\\\(", "Evaluator::evaluate\\\\(", "Evaluator::evaluate_runtime\\\\(", "Evaluator::refresh_runtime_psqt\\\\("]
    },
'''
    anchor_cfg = '    "h512_v3_rehearsal": {'
    if text.count(anchor_net) != 1 or text.count(anchor_cfg) != 1:
        sys.exit("refused: configs.json anchors not found exactly once")
    text = text.replace(anchor_net, net_line + anchor_net).replace(anchor_cfg, cfg_block + anchor_cfg)
    json.loads(text)                      # must still be valid JSON
    with open(cfg_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(frozen, f, indent=1, sort_keys=True)
    print(json.dumps({k: frozen[k] for k in ("seen", "stage", "reason", "metric", "net", "net_md5", "net_sha256", "float_checkpoint_md5")}, indent=1))


if __name__ == "__main__":
    main()
