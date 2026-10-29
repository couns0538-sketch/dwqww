"""J2 (R6): Triton FT kernels vs the plain PyTorch path on random sparse batches.

Checks forward output, weight gradient and bias gradient of
  - the fused double-perspective FT (backend "triton")
  - the per-perspective sparse linear (backend "triton-sparse")
against backend "torch" (embedding_bag fallback).  Pass: max abs diff < 1e-4.

Gradients use grad_out = randn / batch (the scale a mean-reduced loss gives).
A unit-scale stress case (grad_out = randn) is also reported with relative
error, because fp32 sums of thousands of atomics in a different order differ
by more than 1e-4 in absolute terms there; that case is judged against a
float64 reference instead.

Run:  python tests/test_amd_triton_ft.py   (or pytest)
"""

import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.modules.feature_transformer.double_ft_functions import (  # noqa: E402
    double_feature_transform,
)
from model.modules.feature_transformer.sparse_linear_functions import (  # noqa: E402
    SparseLinearFunction,
)
from model.modules.feature_transformer.triton_ft_functions import (  # noqa: E402
    triton_import_error,
    triton_usable,
)

TOL = 1e-4
DEV = torch.device("cuda")


def make_batch(batch, active, num_inputs, l1, seed, holes=False, wscale=0.3):
    g = torch.Generator(device="cpu").manual_seed(seed)
    n_act = torch.randint(0, active + 1, (batch,), generator=g)
    n_act[: min(batch, 2)] = torch.tensor([active, 0])[: min(batch, 2)]  # full and empty rows

    def rows():
        out = torch.full((batch, active), -1, dtype=torch.int32)
        for b in range(batch):
            k = int(n_act[b])
            if k:
                out[b, :k] = torch.randperm(num_inputs, generator=g)[:k].to(torch.int32)
        if holes:  # -1 in the middle of a row (not produced by the loaders)
            out[:, 1::3] = -1
        return out

    wi = rows()
    bi = rows()
    us = (torch.rand(batch, 1, generator=g) < 0.5).float()
    them = 1.0 - us
    weight = torch.randn(num_inputs, l1, generator=g) * wscale
    bias = torch.randn(l1, generator=g) * 0.1
    return [t.to(DEV) for t in (us, them, wi, bi, weight, bias)]


def run_double(backend, us, them, wi, bi, weight, bias, max_act, l1, gout, dtype=torch.float32):
    w = weight.detach().to(dtype).clone().requires_grad_(True)
    b = bias.detach().to(dtype).clone().requires_grad_(True)
    out = double_feature_transform(
        us.to(dtype), them.to(dtype), wi, bi, w, b, max_act, l1, backend=backend
    )
    out.backward(gout.to(dtype))
    torch.cuda.synchronize()
    return out.detach().double(), w.grad.double(), b.grad.double()


def run_sparse(backend, wi, weight, bias, gout, dtype=torch.float32):
    w = weight.detach().to(dtype).clone().requires_grad_(True)
    b = bias.detach().to(dtype).clone().requires_grad_(True)
    out = SparseLinearFunction.apply(wi, w, b, backend=backend)
    out.backward(gout.to(dtype))
    torch.cuda.synchronize()
    return out.detach().double(), w.grad.double(), b.grad.double()


CASES = [
    # name, batch, active, num_inputs, l1, holes
    ("tiny-odd", 7, 5, 50, 96, False),
    ("holes", 33, 12, 300, 128, True),
    ("k32h3-l256", 4096, 32, 73728, 256, False),
    ("k32h3-l1024", 1024, 32, 73728, 1024, False),
    ("collide", 2048, 32, 64, 256, False),  # many atomics on the same rows
    ("full288-l1024", 256, 288, 138096, 1024, False),
]


def check_case(name, batch, active, num_inputs, l1, holes, seed=1234):
    us, them, wi, bi, weight, bias = make_batch(batch, active, num_inputs, l1, seed, holes)
    max_act = 1.0
    gen = torch.Generator(device="cpu").manual_seed(seed + 1)
    gout = (torch.randn(batch, l1, generator=gen) / batch).to(DEV)
    results = []

    ref = run_double("torch", us, them, wi, bi, weight, bias, max_act, l1, gout)
    tri = run_double("triton", us, them, wi, bi, weight, bias, max_act, l1, gout)
    diffs = [(a - r).abs().max().item() for a, r in zip(tri, ref)]
    results.append((f"{name}/double", diffs))

    gout_s = (torch.randn(batch, l1, generator=gen) / batch).to(DEV)
    ref_s = run_sparse("torch", wi, weight, bias, gout_s)
    tri_s = run_sparse("triton-sparse", wi, weight, bias, gout_s)
    diffs = [(a - r).abs().max().item() for a, r in zip(tri_s, ref_s)]
    results.append((f"{name}/sparse", diffs))
    return results


def stress_case(seed=99):
    """Unit-scale gradients: compare both fp32 paths against a float64 reference."""
    batch, active, num_inputs, l1 = 4096, 32, 1000, 256
    us, them, wi, bi, weight, bias = make_batch(batch, active, num_inputs, l1, seed)
    gout = torch.randn(batch, l1, device=DEV)
    ref64 = run_double("torch", us, them, wi, bi, weight, bias, 1.0, l1, gout, dtype=torch.float64)
    t32 = run_double("torch", us, them, wi, bi, weight, bias, 1.0, l1, gout)
    tr32 = run_double("triton", us, them, wi, bi, weight, bias, 1.0, l1, gout)

    def rel(a, r):
        return ((a - r).abs().max() / r.abs().max().clamp(min=1e-30)).item()

    return [rel(t, r) for t, r in zip(t32, ref64)], [rel(t, r) for t, r in zip(tr32, ref64)]


def main() -> int:
    print(f"torch {torch.__version__} hip {torch.version.hip} dev {torch.cuda.get_device_name(0)}")
    if not triton_usable(DEV):
        print("FAIL: Triton kernels not usable:", triton_import_error())
        return 2
    ok = True
    t0 = time.time()
    print(f"{'case':24s} {'fwd':>10s} {'grad_w':>10s} {'grad_b':>10s}  verdict (tol {TOL:g})")
    for case in CASES:
        for label, (d_out, d_w, d_b) in check_case(*case):
            good = max(d_out, d_w, d_b) < TOL
            ok &= good
            print(f"{label:24s} {d_out:10.3e} {d_w:10.3e} {d_b:10.3e}  {'PASS' if good else 'FAIL'}")
    torch_rel, triton_rel = stress_case()
    worse = max(tr / max(t, 1e-12) for tr, t in zip(triton_rel, torch_rel))
    print("stress (grad_out=randn, rel. err vs float64): torch fp32 "
          + " ".join(f"{x:.2e}" for x in torch_rel)
          + " | triton fp32 " + " ".join(f"{x:.2e}" for x in triton_rel))
    stress_ok = max(triton_rel) < 1e-5
    ok &= stress_ok
    print(f"stress verdict (triton rel. err < 1e-5): {'PASS' if stress_ok else 'FAIL'} "
          f"(triton/torch error ratio max {worse:.2f})")
    print(f"total {time.time() - t0:.1f}s  RESULT {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def test_triton_ft_matches_torch():
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
