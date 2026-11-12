"""test_ckpt_io.py - JOB E (own code, 2026-11-12): checks of h512/train/ckpt_io.py. Read-only on real checkpoints.

  python -I -B test_ckpt_io.py --scratch NEW_DIR [--loads FILE.pt ...]

1. A checkpoint that carries a command (pickle `__reduce__` that would create an empty marker file) is written
   into NEW_DIR. Control: the unrestricted loader runs that command - done once, on purpose, on this self-made
   file only (the single weights_only=False in this job's code). `load_checkpoint` must refuse the same kind of
   file and its marker must not appear.
2. A plain checkpoint (tensors, numbers, lists, strings, a numpy scalar) written into NEW_DIR must load with
   equal content.
3. Every --loads file must load through `load_checkpoint` and hold a dict with "cfg" and "state".
NEW_DIR must not exist; it is created and left in place. Exit 0 = all checks passed.
"""
import argparse
import os
import pickle
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "train"))
from ckpt_io import load_checkpoint  # noqa: E402


class Carrier:
    """Unpickling this object calls open(marker, 'w'): a stand-in for any command hidden in a checkpoint."""

    def __init__(self, marker):
        self.marker = marker

    def __reduce__(self):
        return (open, (self.marker, "w"))


def same(a, b, where="ckpt"):
    if type(a) is not type(b):
        return f"{where}: type {type(a).__name__} != {type(b).__name__}"
    if isinstance(a, torch.Tensor):
        return None if (a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b)) else f"{where}: tensors differ"
    if isinstance(a, dict):
        if list(a.keys()) != list(b.keys()):
            return f"{where}: keys differ"
        for k in a:
            why = same(a[k], b[k], f"{where}[{k!r}]")
            if why:
                return why
        return None
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return f"{where}: length differs"
        for i, (x, y) in enumerate(zip(a, b)):
            why = same(x, y, f"{where}[{i}]")
            if why:
                return why
        return None
    if isinstance(a, np.ndarray):
        return None if (a.dtype == b.dtype and np.array_equal(a, b)) else f"{where}: arrays differ"
    if isinstance(a, float) and a != a:
        return None if b != b else f"{where}: nan vs number"
    return None if a == b else f"{where}: {a!r} != {b!r}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--loads", nargs="*", default=[])
    a = ap.parse_args()
    if os.path.exists(a.scratch):
        sys.exit(f"refusing: {a.scratch} exists")
    os.makedirs(a.scratch)
    fails = 0

    def check(name, ok, detail=""):
        nonlocal fails
        fails += 0 if ok else 1
        print(("PASS " if ok else "FAIL ") + name + (" :: " + detail if detail else ""), flush=True)

    # 1. a file that carries a command
    bad = os.path.join(a.scratch, "carries_a_command.pt")
    marker_unsafe = os.path.join(a.scratch, "MARKER_unrestricted_loader_ran_it")
    marker_safe = os.path.join(a.scratch, "MARKER_must_never_exist")
    torch.save({"cfg": {"hidden": 512}, "state": Carrier(marker_unsafe)}, bad)
    torch.load(bad, map_location="cpu", weights_only=False)
    check("control: the unrestricted loader runs the command in the file", os.path.exists(marker_unsafe))
    torch.save({"cfg": {"hidden": 512}, "state": Carrier(marker_safe)}, bad)
    try:
        load_checkpoint(bad, torch)
        check("load_checkpoint refuses the file", False, "it loaded")
    except pickle.UnpicklingError as e:
        check("load_checkpoint refuses the file", True, str(e).splitlines()[-1][:110] if str(e) else "")
    check("the command in the file did not run", not os.path.exists(marker_safe))

    # 2. a plain checkpoint
    good = os.path.join(a.scratch, "plain.pt")
    obj = {"cfg": {"hidden": 512, "king_map": list(range(64)), "name": "x"}, "state": {"w": torch.arange(12.0).reshape(3, 4)},
           "seen": 123, "lr": 5e-4, "rng": torch.get_rng_state(), "np_scalar": np.float64(1.5), "flags": [True, None]}
    torch.save(obj, good)
    check("a plain checkpoint loads with equal content", same(load_checkpoint(good, torch), obj) is None,
          same(load_checkpoint(good, torch), obj) or "")

    # 3. real checkpoints load
    for path in a.loads:
        try:
            got = load_checkpoint(path, torch)
        except Exception as e:  # noqa: BLE001 - the message is the result
            check(f"loads: {path}", False, str(e).splitlines()[0][:200])
            continue
        check(f"loads: {path}", isinstance(got, dict) and "cfg" in got and "state" in got)
    print(f"RESULT {'PASS' if fails == 0 else 'FAIL'}: {fails} failed check(s), {len(a.loads)} real checkpoint(s) loaded")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
