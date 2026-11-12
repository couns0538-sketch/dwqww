#!/usr/bin/env python
"""average_ckpts.py - JOB E phase 2 (2026-11-11): plain weight averaging of trainer checkpoints. Own code.

  average_ckpts.py --pts a.pt b.pt [c.pt ...] --out-pt avg.pt --out-net avg.fnn3

Every float parameter tensor of the model (w1, wf, b1, w2, b2) is the arithmetic mean over the given checkpoints
(equal weights). The result is clipped like a training step clips it and exported with the trainer's own exporter,
so the net file is on the engine's integer grid exactly like a trained checkpoint. The output .pt holds cfg + state
only (no optimizer): it is a net to score and play, not a state to resume training from.
"""
import argparse
import hashlib
import json
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "train"))
import fable_nnue_train as fb       # noqa: E402
import train_h512_gpu as tr         # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pts", nargs="+", required=True)
    ap.add_argument("--out-pt", required=True)
    ap.add_argument("--out-net", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_pt) or os.path.exists(a.out_net):
        sys.exit("refused: output exists")
    cks = [torch.load(p, map_location="cpu", weights_only=False) for p in a.pts]
    cfg = cks[0]["cfg"]
    for c in cks[1:]:
        if {k: c["cfg"][k] for k in ("hidden", "king_buckets", "output_buckets")} != {k: cfg[k] for k in ("hidden", "king_buckets", "output_buckets")}:
            sys.exit("refused: checkpoints of different shapes")
    state = {}
    for k in cks[0]["state"]:
        state[k] = sum(c["state"][k].to(torch.float64) for c in cks) / len(cks)
        state[k] = state[k].to(cks[0]["state"][k].dtype)
    model = fb.build_model(cfg, torch)
    model.load_state_dict(state)
    model.clip()
    checksum, mw1, mb1, mw2 = tr.export_cpu(model, cfg, a.out_net)
    torch.save({"cfg": cfg, "state": model.state_dict(), "averaged_from": [
        {"pt": p, "md5": hashlib.md5(open(p, "rb").read()).hexdigest(), "seen": c.get("train_state", {}).get("seen")}
        for p, c in zip(a.pts, cks)]}, a.out_pt)
    print(json.dumps({"out_net": a.out_net, "net_md5": hashlib.md5(open(a.out_net, "rb").read()).hexdigest(),
                      "checksum": f"{checksum:x}", "max_w1": mw1, "max_b1": mb1, "max_w2": mw2,
                      "from": [{"pt": p, "seen": c.get("train_state", {}).get("seen")} for p, c in zip(a.pts, cks)]}))


if __name__ == "__main__":
    main()
