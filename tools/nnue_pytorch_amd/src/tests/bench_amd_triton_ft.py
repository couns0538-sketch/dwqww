"""R6 J3a: feature-transformer forward+backward time, torch vs Triton (synthetic batches).

Usage: python tests/bench_amd_triton_ft.py [--tune] [--iters N]
Times one FT step = forward + backward of double_feature_transform (weight and
bias gradients) with CUDA events, median of N iterations after warm-up.
"""

import argparse
import itertools
import os
import statistics
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.modules.feature_transformer.double_ft_functions import (  # noqa: E402
    double_feature_transform,
)

DEV = torch.device("cuda")


def make(batch, active, num_inputs, l1, fill=0.75, seed=0):
    g = torch.Generator(device="cpu").manual_seed(seed)
    k = int(active * fill)
    wi = torch.full((batch, active), -1, dtype=torch.int32)
    bi = torch.full((batch, active), -1, dtype=torch.int32)
    # unique per row: random offsets in disjoint strides
    stride = num_inputs // active
    base = torch.arange(active, dtype=torch.int64) * stride
    wi[:, :k] = (base[:k] + torch.randint(0, stride, (batch, k), generator=g)).to(torch.int32)
    bi[:, :k] = (base[:k] + torch.randint(0, stride, (batch, k), generator=g)).to(torch.int32)
    us = (torch.rand(batch, 1, generator=g) < 0.5).float()
    them = 1.0 - us
    w = (torch.randn(num_inputs, l1, generator=g) * 0.05).to(DEV).requires_grad_(True)
    b = (torch.randn(l1, generator=g) * 0.05).to(DEV).requires_grad_(True)
    gout = (torch.randn(batch, l1, generator=g) / batch).to(DEV)
    return us.to(DEV), them.to(DEV), wi.to(DEV), bi.to(DEV), w, b, gout


def step(backend, data, l1):
    us, them, wi, bi, w, b, gout = data
    w.grad = None
    b.grad = None
    out = double_feature_transform(us, them, wi, bi, w, b, 1.0, l1, backend=backend)
    out.backward(gout)


def time_ms(backend, data, l1, iters, fwd_only=False):
    us, them, wi, bi, w, b, gout = data
    for _ in range(3):
        step(backend, data, l1)
    torch.cuda.synchronize()
    ts = []
    for _ in range(iters):
        s = torch.cuda.Event(enable_timing=True)
        e = torch.cuda.Event(enable_timing=True)
        s.record()
        if fwd_only:
            with torch.no_grad():
                double_feature_transform(us, them, wi, bi, w, b, 1.0, l1, backend=backend)
        else:
            step(backend, data, l1)
        e.record()
        e.synchronize()
        ts.append(s.elapsed_time(e))
    return statistics.median(ts)


SHAPES = [
    # batch, active, inputs, l1   (fill 75% of active slots)
    (4096, 32, 73728, 256),  # baseline smoke config (K32H3^, --l1 256, bs 4096)
    (16384, 32, 73728, 1024),  # K32H3^ at upstream L1 and batch
    (4096, 288, 138096, 1024),  # Full_Threats+PP_3Wide+K32H3^ at L1 1024
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=10)
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--shapes", default="0,1,2")
    args = ap.parse_args()
    print(f"torch {torch.__version__} hip {torch.version.hip} {torch.cuda.get_device_name(0)}", flush=True)
    for si in [int(x) for x in args.shapes.split(",")]:
        batch, active, num_inputs, l1 = SHAPES[si]
        data = make(batch, active, num_inputs, l1)
        t_torch = time_ms("torch", data, l1, args.iters)
        t_torch_f = time_ms("torch", data, l1, args.iters, fwd_only=True)
        t_tri = time_ms("triton", data, l1, args.iters)
        t_tri_f = time_ms("triton", data, l1, args.iters, fwd_only=True)
        print(
            f"shape B={batch} A={active} N={num_inputs} L1={l1}: "
            f"torch fwd {t_torch_f:.2f} ms, fwd+bwd {t_torch:.2f} ms | "
            f"triton fwd {t_tri_f:.2f} ms, fwd+bwd {t_tri:.2f} ms | "
            f"speedup fwd {t_torch_f / t_tri_f:.1f}x, fwd+bwd {t_torch / t_tri:.1f}x",
            flush=True,
        )
        if args.tune:
            half = l1 // 2
            best = None
            for bc, kc, nw, pos in itertools.product(
                [c for c in (32, 64, 128, 256) if c <= half], (8, 16, 32), (2, 4, 8), (4, 8, 16)
            ):
                if kc > active:
                    continue
                os.environ["NNUE_TRITON_BLOCK_C"] = str(bc)
                os.environ["NNUE_TRITON_KC"] = str(kc)
                os.environ["NNUE_TRITON_WARPS"] = str(nw)
                os.environ["NNUE_TRITON_POS"] = str(pos)
                try:
                    t = time_ms("triton", data, l1, max(3, args.iters // 2))
                except Exception as e:  # e.g. out of resources
                    print(f"  bc={bc} kc={kc} warps={nw} pos={pos}: {type(e).__name__}", flush=True)
                    continue
                print(f"  bc={bc:3d} kc={kc:2d} warps={nw} pos={pos:2d}: {t:.2f} ms", flush=True)
                if best is None or t < best[0]:
                    best = (t, bc, kc, nw, pos)
            for k in ("NNUE_TRITON_BLOCK_C", "NNUE_TRITON_KC", "NNUE_TRITON_WARPS", "NNUE_TRITON_POS"):
                os.environ.pop(k, None)
            if best:
                print(f"  BEST {best[0]:.2f} ms: bc={best[1]} kc={best[2]} warps={best[3]} pos={best[4]}", flush=True)
        del data
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
