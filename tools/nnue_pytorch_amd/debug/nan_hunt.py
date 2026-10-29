"""R6: find the first non-finite value in a short nnue-pytorch run (debug wrapper).

Usage (cwd = clone): python nan_hunt.py <train.py args>
Per step: checks the batch (index range, finite floats), the grads before the
optimizer step and the parameters after it. Prints the first failure and exits.
"""

import os
import runpy
import sys

sys.path.insert(0, os.getcwd())
import torch  # noqa: E402

import trainer.engine as E  # noqa: E402
from model.optimizers import ranger_lite  # noqa: E402

state = {"step": 0, "num_inputs": None, "names": {}}


def fail(msg):
    print(f"NANHUNT FIRST FAILURE at step {state['step']}: {msg}", flush=True)
    os._exit(7)


orig_step = E.SimpleTrainer._training_step


def training_step(self, batch):
    state["step"] += 1
    if state["num_inputs"] is None:
        m = self.model.model if hasattr(self.model, "model") else self.model
        m = getattr(m, "_orig_mod", m)
        state["num_inputs"] = m.input.NUM_INPUTS
        for n, p in self.model.named_parameters():
            state["names"][id(p)] = n
    us, them, wi, bi = batch[0], batch[1], batch[2], batch[3]
    for name, t in (("white", wi), ("black", bi)):
        mx = int(t.max())
        mn = int(t.min())
        if mx >= state["num_inputs"] or mn < -1:
            fail(f"{name} indices out of range: min {mn} max {mx} (num_inputs {state['num_inputs']})")
    for i, t in enumerate(batch):
        if isinstance(t, torch.Tensor) and t.is_floating_point() and not torch.isfinite(t).all():
            fail(f"batch tensor {i} has non-finite values")
    out = orig_step(self, batch)
    if not torch.isfinite(out["loss"]).all():
        fail(f"loss non-finite: {out['loss'].item()}")
    return out


orig_opt_step = ranger_lite.RangerLite.step


def opt_step(self, *a, **k):
    for g in self.param_groups:
        for p in g["params"]:
            if p.grad is not None and not torch.isfinite(p.grad).all():
                fail(f"grad non-finite before step: {state['names'].get(id(p), '?')} {tuple(p.shape)}")
    r = orig_opt_step(self, *a, **k)
    for g in self.param_groups:
        for p in g["params"]:
            if not torch.isfinite(p).all():
                st = self.state[p]
                info = {k2: bool(torch.isfinite(v).all()) for k2, v in st.items() if isinstance(v, torch.Tensor)}
                fail(f"param non-finite after step: {state['names'].get(id(p), '?')} {tuple(p.shape)} "
                     f"lr={g['lr']} wd={g.get('weight_decay')} state_finite={info} step={st.get('step')}")
    return r


E.SimpleTrainer._training_step = training_step
ranger_lite.RangerLite.step = opt_step
sys.argv = ["train.py", *sys.argv[1:]]
runpy.run_path("train.py", run_name="__main__")
print(f"NANHUNT clean after {state['step']} steps", flush=True)
