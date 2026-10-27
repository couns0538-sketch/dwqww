"""Compare two trainer checkpoints (.pt) tensor by tensor (read-only; no training, no export).

usage: python -B opus_s18_pt_diff.py <a.pt> <b.pt>
Prints, per state_dict tensor of the model and of the optimizer state, whether the tensors are equal and the
largest absolute difference, then one summary line. Used to size the Linux (Sol) vs Windows (PC) difference
of the float checkpoints whose quantized .inc exports are byte-identical.
"""
import sys

import torch


def flatten(prefix, value, out):
    if isinstance(value, torch.Tensor):
        out[prefix] = value
    elif isinstance(value, dict):
        for key in sorted(value, key=str):
            flatten(f"{prefix}.{key}" if prefix else str(key), value[key], out)
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            flatten(f"{prefix}[{i}]", item, out)


def main(argv):
    a = torch.load(argv[0], map_location="cpu", weights_only=True)
    b = torch.load(argv[1], map_location="cpu", weights_only=True)
    worst = 0.0
    differing = 0
    for section in ("model", "optimizer"):
        fa, fb = {}, {}
        flatten(section, a[section], fa)
        flatten(section, b[section], fb)
        if set(fa) != set(fb):
            print(f"{section}: different tensor names")
            return 1
        for name in sorted(fa):
            x, y = fa[name], fb[name]
            if x.shape != y.shape or x.dtype != y.dtype:
                print(f"{name}: shape/dtype differ {tuple(x.shape)} {tuple(y.shape)}")
                return 1
            equal = bool(torch.equal(x, y))
            diff = float((x.double() - y.double()).abs().max()) if x.numel() else 0.0
            scale = float(x.double().abs().max()) if x.numel() else 0.0
            if not equal:
                differing += 1
                worst = max(worst, diff)
            print(f"{name:60s} equal={equal!s:5s} max_abs_diff={diff:.3e} max_abs={scale:.3e}")
    same_meta = {k: a[k] == b[k] for k in ("config", "next_epoch", "step", "val") if k in a}
    print(f"SUMMARY differing_tensors={differing} max_abs_diff={worst:.3e} metadata_equal={same_meta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
