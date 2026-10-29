"""R6: how do Triton sqrt / sqrt_rn / division behave on denormal fp32 inputs on gfx1100?"""
import torch
import triton
import triton.language as tl


@triton.jit
def k(x_ptr, o_sqrt_rn, o_sqrt, o_div, o_sqrt_div, n, BLOCK: tl.constexpr):
    offs = tl.arange(0, BLOCK)
    m = offs < n
    x = tl.load(x_ptr + offs, mask=m, other=1.0)
    tl.store(o_sqrt_rn + offs, tl.sqrt_rn(x), mask=m)
    tl.store(o_sqrt + offs, tl.sqrt(x), mask=m)
    tl.store(o_div + offs, x / 0.106, mask=m)
    tl.store(o_sqrt_div + offs, tl.sqrt_rn(x / 0.106) + 1e-7, mask=m)


xs = torch.tensor([0.0, 1e-45, 3.5e-40, 3.3e-39, 1.1e-38, 1.2e-38, 1e-37, 1e-30, 1.0], dtype=torch.float32, device="cuda")
outs = [torch.empty_like(xs) for _ in range(4)]
k[(1,)](xs, *outs, xs.numel(), BLOCK=16)
torch.cuda.synchronize()
print(f"{'x':>12s} {'sqrt_rn':>12s} {'sqrt':>12s} {'x/0.106':>12s} {'sqrt_rn(x/.106)+eps':>20s} {'torch sqrt':>12s}")
ref = torch.sqrt(xs)
for i in range(xs.numel()):
    print(f"{xs[i].item():12.3e} {outs[0][i].item():12.4e} {outs[1][i].item():12.4e} "
          f"{outs[2][i].item():12.4e} {outs[3][i].item():20.4e} {ref[i].item():12.4e}")
