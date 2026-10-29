"""R6: shadow-check the fused (Triton) RangerLite step against the Python path in a real run.

Before each real step the params, grads, full optimizer state and counters are
cloned into a shadow RangerLite; after the real step the shadow runs the Python
update path; params and state are compared. Reports the first divergence.
"""

import os
import runpy
import sys

sys.path.insert(0, os.getcwd())
import torch  # noqa: E402

import trainer.engine as E  # noqa: E402
import model.optimizers.ranger_lite as rl  # noqa: E402

S = {"step": 0, "shadow": None, "sparams": None, "names": {}}
MAX_STEPS = int(os.environ.get("NANHUNT_MAX_STEPS", "120"))

orig_training_step = E.SimpleTrainer._training_step


def training_step(self, batch):
    S["step"] += 1
    if not S["names"]:
        for n, p in self.model.named_parameters():
            S["names"][id(p)] = n
    return orig_training_step(self, batch)


orig_opt_step = rl.RangerLite.step


def real_params(opt):
    return [p for g in opt.param_groups for p in g["params"]]


def build_shadow(opt):
    sparams = [torch.nn.Parameter(p.detach().clone()) for p in real_params(opt)]
    groups, i = [], 0
    for g in opt.param_groups:
        n = len(g["params"])
        sg = {k: v for k, v in g.items() if k != "params"}
        sg["params"] = sparams[i : i + n]
        groups.append(sg)
        i += n
    sh = rl.RangerLite(
        groups, lr=1.0, weight_decay=0.0,
        use_legacy_scoping_bug=opt.use_legacy_scoping_bug, normloss_active=opt.normloss_active,
        pnm_activate=opt.pnm_active, lookahead_active=opt.lookahead_active,
        lookahead_blending_alpha=opt.lookahead_alpha, lookahead_mergetime=opt.lookahead_mergetime,
        use_stable_weight_decay=opt.use_stable_weight_decay,
    )
    return sh, sparams


def opt_step(self, *a, **k):
    if S["shadow"] is None:
        S["shadow"], S["sparams"] = build_shadow(self)
        info = [(len(g["params"]), g["lr"], g.get("weight_decay")) for g in self.param_groups]
        print(f"NANHUNT4 groups (n, lr, wd): {info}", flush=True)
    sh, sparams = S["shadow"], S["sparams"]
    rps = real_params(self)
    for rp, sp in zip(rps, sparams):
        sp.data = rp.data.clone()
        sp.grad = None if rp.grad is None else rp.grad.clone()
        st = sh.state[sp]
        st.clear()
        for key, v in self.state[rp].items():
            st[key] = v.clone() if isinstance(v, torch.Tensor) else v
    for sg, rg in zip(sh.param_groups, self.param_groups):
        for key, v in rg.items():
            if key != "params":
                sg[key] = v
    sh.lookahead_step = self.lookahead_step
    sh.param_size = self.param_size
    grads_in = {id(rp): (rp.grad.clone() if rp.grad is not None else None) for rp in rps}

    r = orig_opt_step(self, *a, **k)

    old = (rl._HAS_FUSED, rl._HAS_TRITON_FUSED)
    rl._HAS_FUSED, rl._HAS_TRITON_FUSED = False, False
    try:
        orig_opt_step(sh)
    finally:
        rl._HAS_FUSED, rl._HAS_TRITON_FUSED = old
    torch.cuda.synchronize()

    for rp, sp in zip(rps, sparams):
        name = S["names"].get(id(rp), "?")
        pairs = [("param", rp.detach(), sp.detach())]
        for key, v in self.state[rp].items():
            if isinstance(v, torch.Tensor):
                pairs.append((key, v, sh.state[sp][key]))
        for key, a_, b_ in pairs:
            fin_a = bool(torch.isfinite(a_).all())
            fin_b = bool(torch.isfinite(b_).all())
            d = (a_ - b_).abs()
            dmax = d.max().item() if fin_a and fin_b else float("nan")
            scale = b_.abs().max().item() if fin_b else float("nan")
            if not fin_a or not fin_b or dmax > 1e-5 * max(scale, 1e-3):
                flat = torch.nonzero((~torch.isfinite(a_.reshape(-1))) | (d.reshape(-1) > 1e-5 * max(scale, 1e-3)))
                i0 = int(flat[0]) if flat.numel() else -1
                g = grads_in[id(rp)]
                print(f"NANHUNT4 DIVERGENCE step {S['step']} {name} {tuple(rp.shape)} '{key}': "
                      f"fused finite={fin_a} python finite={fin_b} maxdiff={dmax:.3e} scale={scale:.3e} "
                      f"n_bad={flat.numel()} first idx {i0}", flush=True)
                if i0 >= 0:
                    print(f"   fused={a_.reshape(-1)[i0].item()!r} python={b_.reshape(-1)[i0].item()!r} "
                          f"grad_in={(g.reshape(-1)[i0].item() if g is not None else None)!r} "
                          f"grad dtype={None if g is None else g.dtype} contiguous={None if g is None else g.is_contiguous()} "
                          f"stride={None if g is None else g.stride()} p.stride={rp.stride()} "
                          f"data_ptr%16={rp.data_ptr() % 16} grad_ptr%16={None if g is None else g.data_ptr() % 16}",
                          flush=True)
                os._exit(9)
    if S["step"] >= MAX_STEPS:
        print(f"NANHUNT4 clean for {S['step']} steps", flush=True)
        os._exit(0)
    return r


E.SimpleTrainer._training_step = training_step
rl.RangerLite.step = opt_step
sys.argv = ["train.py", *sys.argv[1:]]
runpy.run_path("train.py", run_name="__main__")
