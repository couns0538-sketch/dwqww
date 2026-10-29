"""R6 J3: per-step time breakdown of nnue-pytorch train.py (synced wall timers).

Usage (cwd = clone): python profile_train.py <train.py args>
Patches Trainer._training_step (forward + loss), torch.Tensor.backward and the
optimizer step with torch.cuda.synchronize() timers; the rest of the step
(loader wait, H2D copy, callbacks, Python) is "other".  Prints a table at exit.
Syncs cost a little throughput; use bench_train.py for the speed numbers.
"""

import atexit
import os
import runpy
import sys
import time

sys.path.insert(0, os.getcwd())
import torch  # noqa: E402

import trainer.engine as E  # noqa: E402
from model.optimizers import ranger_lite  # noqa: E402

acc = {"fwd+loss": 0.0, "backward": 0.0, "opt.step": 0.0, "zero_grad": 0.0}
cnt = {"steps": 0}
t_epoch = {"start": None, "skip": 60}  # ignore the first steps (warm-up, compile)
wall = {"t": 0.0}


def sync():
    torch.cuda.synchronize()


def timed(key, fn):
    def wrap(*a, **k):
        if cnt["steps"] < t_epoch["skip"]:
            return fn(*a, **k)
        sync()
        t = time.perf_counter()
        r = fn(*a, **k)
        sync()
        acc[key] += time.perf_counter() - t
        return r

    return wrap


orig_step = E.SimpleTrainer._training_step


def training_step(self, batch):
    cnt["steps"] += 1
    if cnt["steps"] == t_epoch["skip"]:
        sync()
        wall["t0"] = time.perf_counter()
    return timed("fwd+loss", orig_step)(self, batch)


E.SimpleTrainer._training_step = training_step
torch.Tensor.backward = timed("backward", torch.Tensor.backward)
ranger_lite.RangerLite.step = timed("opt.step", ranger_lite.RangerLite.step)
ranger_lite.RangerLite.zero_grad = timed("zero_grad", ranger_lite.RangerLite.zero_grad)


def report():
    if "t0" not in wall:
        print("PROFILE: not enough steps")
        return
    sync()
    total = time.perf_counter() - wall["t0"]
    n = cnt["steps"] - t_epoch["skip"]
    other = total - sum(acc.values())
    print(f"PROFILE over {n} steps, {1000 * total / n:.2f} ms/step:")
    for k, v in list(acc.items()) + [("other (loader, H2D, py)", other)]:
        print(f"  {k:26s} {1000 * v / n:8.2f} ms/step  {100 * v / total:5.1f}%")


atexit.register(report)
sys.argv = ["train.py", *sys.argv[1:]]
runpy.run_path("train.py", run_name="__main__")
