"""R6: Triton fused RangerLite update vs the Python update path (same random grads).

Covers fast path A (no weight decay: one fused kernel per parameter) and fast
path B (stable weight decay: variance kernel, global variance norm, phase-2
kernel), pnm on and off, 12 steps (odd/even pnm steps, two lookahead merges).
Pass: max abs diff of parameters and optimizer state < 1e-6 (params ~0.1, lr 1e-3).

Run:  python tests/test_amd_triton_ranger.py
"""

import os
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import model.optimizers.ranger_lite as rl  # noqa: E402

DEV = torch.device("cuda")
TOL = 1e-6


def make_params(seed):
    g = torch.Generator(device="cpu").manual_seed(seed)
    shapes = [(73728, 256), (256,), (512, 512), (32,)]
    return [(torch.randn(*s, generator=g) * 0.1).to(DEV) for s in shapes]


def tiny_grads(shape, gen):
    """Grads whose squares put variance_ma into the fp32 denormal range (|g| ~ 1e-21..1e-18)."""
    g = torch.randn(shape, generator=gen) * 0.01
    mask = torch.rand(shape, generator=gen) < 0.25
    tiny = torch.randn(shape, generator=gen) * 10.0 ** torch.randint(-21, -17, shape, generator=gen).float()
    return torch.where(mask, tiny, g)


def run(fused: bool, pnm: bool, wd: float, stable: bool, steps=12, seed=7, tiny=False):
    params = [torch.nn.Parameter(t.clone()) for t in make_params(seed)]
    groups = [
        {"params": params[:2], "lr": 1e-3, "weight_decay": wd},
        {"params": params[2:], "lr": 5e-4, "weight_decay": 0.0},
    ]
    old = (rl._HAS_FUSED, rl._HAS_TRITON_FUSED)
    rl._HAS_FUSED, rl._HAS_TRITON_FUSED = (fused, fused) if not rl._HAS_CUPY else old
    try:
        opt = rl.RangerLite(
            groups, lr=1.0, weight_decay=0.0, normloss_active=False,
            use_legacy_scoping_bug=False, pnm_activate=pnm, pnm_momentum=1.0,
            lookahead_blending_alpha=0.5, lookahead_mergetime=5,
            use_stable_weight_decay=stable,
        )
        gen = torch.Generator(device="cpu").manual_seed(seed + 100)
        for _ in range(steps):
            for p in params:
                g = tiny_grads(p.shape, gen) if tiny else torch.randn(p.shape, generator=gen) * 0.01
                p.grad = g.to(DEV)
            opt.step()
        torch.cuda.synchronize()
        out = [p.detach().clone() for p in params]
        for p in params:
            st = opt.state[p]
            for k in ("grad_ma", "neg_grad_ma", "variance_ma", "lookahead_params"):
                if k in st:
                    out.append(st[k].detach().clone())
        return out
    finally:
        rl._HAS_FUSED, rl._HAS_TRITON_FUSED = old


CALLS: dict[str, int] = {}


def count_kernel_calls():
    """Wrap the Triton launchers so the test proves which fused path ran."""
    for name in ("pnm_full", "adam_full", "variance", "pnm_phase2", "adam_phase2"):
        fn = getattr(rl._rlt, name)

        def wrap(*a, _fn=fn, _name=name, **k):
            CALLS[_name] = CALLS.get(_name, 0) + 1
            return _fn(*a, **k)

        setattr(rl._rlt, name, wrap)


EXPECTED = {  # path -> launchers that must run (4 params x 12 steps = 48 calls each)
    "A": {"pnm": {"pnm_full"}, "adam": {"adam_full"}},
    "B": {"pnm": {"variance", "pnm_phase2"}, "adam": {"variance", "adam_phase2"}},
    "A+wd": {"pnm": {"pnm_full"}, "adam": {"adam_full"}},
}


def main() -> int:
    print(f"torch {torch.__version__} hip {torch.version.hip}; cupy={rl._HAS_CUPY} "
          f"triton_fused={rl._HAS_TRITON_FUSED}")
    if not rl._HAS_TRITON_FUSED:
        print("FAIL: Triton fused RangerLite not available")
        return 2
    count_kernel_calls()
    ok = True
    for tiny in (False, True):
        for pnm in (True, False):
            for wd, stable, path in ((0.0, True, "A"), (1e-2, True, "B"), (1e-2, False, "A+wd")):
                CALLS.clear()
                ref = run(False, pnm, wd, stable, tiny=tiny)
                ref_calls = dict(CALLS)
                CALLS.clear()
                tri = run(True, pnm, wd, stable, tiny=tiny)
                want = EXPECTED[path]["pnm" if pnm else "adam"]
                calls_ok = not ref_calls and set(CALLS) == want and all(v == 48 for v in CALLS.values())
                finite = all(bool(torch.isfinite(t).all()) for t in tri)
                d = max((a - b).abs().max().item() for a, b in zip(ref, tri))
                good = d < TOL and calls_ok and finite
                ok &= good
                print(f"{'denormal-vm' if tiny else 'normal-grads':12s} pnm={pnm!s:5s} wd={wd:<5g} "
                      f"stable_wd={stable!s:5s} path {path:5s}: max abs diff {d:.3e}, finite={finite}, "
                      f"triton calls {CALLS} (python run: {ref_calls or 'none'})  {'PASS' if good else 'FAIL'}")
    print("RESULT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def test_triton_ranger_matches_python():
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
