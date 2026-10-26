"""qa_adam_dml.py (Engine QA 2026-10-24). torch.optim.Adam with the exp_avg update written as mul_/add_ instead of lerp_.
torch-directml 2.4.1 has no aten::lerp.Scalar_out, so stock Adam copies exp_avg to the CPU and back every step (UserWarning
in every b8/v2 run's .log.err). Same math, same state keys ('step','exp_avg','exp_avg_sq'), same state_dict/checkpoint format
as torch.optim.Adam (amsgrad/weight_decay/maximize not supported -> asserts). Differences vs stock: float rounding only."""
import math, torch

class AdamDML(torch.optim.Adam):
    def __init__(self, params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8, **kw):
        kw.setdefault("foreach", False)
        super().__init__(params, lr=lr, betas=betas, eps=eps, **kw)
        for g in self.param_groups:
            assert not g.get("amsgrad") and not g.get("weight_decay") and not g.get("maximize"), "AdamDML: plain Adam only"

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        for g in self.param_groups:
            b1, b2 = g["betas"]; lr = g["lr"]; eps = g["eps"]
            for p in g["params"]:
                if p.grad is None:
                    continue
                st = self.state[p]
                if len(st) == 0:
                    st["step"] = torch.tensor(0.0)
                    st["exp_avg"] = torch.zeros_like(p, memory_format=torch.preserve_format)
                    st["exp_avg_sq"] = torch.zeros_like(p, memory_format=torch.preserve_format)
                st["step"] += 1
                t = float(st["step"])
                m, v, gr = st["exp_avg"], st["exp_avg_sq"], p.grad
                m.mul_(b1).add_(gr, alpha=1 - b1)
                v.mul_(b2).addcmul_(gr, gr, value=1 - b2)
                bc1 = 1 - b1 ** t; bc2s = math.sqrt(1 - b2 ** t)
                denom = (v.sqrt() / bc2s).add_(eps)
                p.addcdiv_(m, denom, value=-lr / bc1)
        return loss

