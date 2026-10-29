"""R6: locate what overwrites RangerLite lookahead buffers between merge steps.

Snapshot every state tensor after each optimizer step; compare at
  (a) start of the next training step (after the loader handed over the batch)
  (b) after forward+loss
  (c) before the optimizer step (after backward)
lookahead_params may change only inside the optimizer step on merge steps.
"""

import os
import runpy
import sys

sys.path.insert(0, os.getcwd())
import torch  # noqa: E402

import trainer.engine as E  # noqa: E402
from model.optimizers import ranger_lite  # noqa: E402

S = {"step": 0, "opt": None, "snap": None, "names": {}}
MAX_STEPS = int(os.environ.get("NANHUNT_MAX_STEPS", "200"))


def snapshot(opt):
    snap = []
    for g in opt.param_groups:
        for p in g["params"]:
            st = opt.state[p]
            for k, v in st.items():
                if isinstance(v, torch.Tensor):
                    snap.append((p, k, v, v.clone()))
            snap.append((p, "param", p, p.detach().clone()))
    return snap


def compare(where, check_params=True):
    if S["snap"] is None:
        return
    torch.cuda.synchronize()
    for p, k, v, ref in S["snap"]:
        if k == "param" and not check_params:
            continue
        if not torch.equal(v, ref):
            d = (v - ref).abs()
            bad = (~torch.isfinite(v)).sum().item()
            nz = (d != 0).sum().item()
            print(f"NANHUNT2 step {S['step']} [{where}]: {S['names'].get(id(p), '?')} {tuple(p.shape)} "
                  f"state '{k}' changed: {nz} elems differ, {bad} non-finite", flush=True)
            idx = torch.nonzero(d.reshape(-1) != 0)[:8].reshape(-1).tolist()
            print(f"   first changed flat idx {idx} of {v.numel()}", flush=True)
            os._exit(9)


orig_step = E.SimpleTrainer._training_step


def training_step(self, batch):
    S["step"] += 1
    if not S["names"]:
        for n, p in self.model.named_parameters():
            S["names"][id(p)] = n
    compare("a: before forward (loader/H2D since last step)")
    out = orig_step(self, batch)
    compare("b: after forward+loss", check_params=False)
    return out


orig_opt_step = ranger_lite.RangerLite.step


def opt_step(self, *a, **k):
    compare("c: after backward, before optimizer step")
    r = orig_opt_step(self, *a, **k)
    torch.cuda.synchronize()
    S["snap"] = snapshot(self)
    if S["step"] >= MAX_STEPS:
        print(f"NANHUNT2 clean for {S['step']} steps", flush=True)
        os._exit(0)
    return r


E.SimpleTrainer._training_step = training_step
ranger_lite.RangerLite.step = opt_step
sys.argv = ["train.py", *sys.argv[1:]]
runpy.run_path("train.py", run_name="__main__")
