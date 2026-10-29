"""R7 J1 test: the Triton Forge-v2 path equals Grok Bot's plain torch path (forward and every gradient) on real
loader batches, and the comparison catches planted errors. GPL-3.0 tool code (tools/nnue_pytorch_amd/).

usage: python test_forge_v2_kernels.py <data.binpack> [batch=2048] [batches=3]
PASS: |out| max diff < 2e-4 and every gradient max diff < 1e-4 * max(1, max|grad|) on every batch;
the planted cases (one wrong remap entry; swapped side to move) must FAIL the same check.
Runs seconds on the GPU (smoke size, 1 loader thread)."""
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import train_forge_v2_fast as T  # noqa: E402

from data_loader import DataloaderSkipConfig  # noqa: E402
from data_loader import stream as st  # noqa: E402


def compare(plain, fast, us, wi_raw, bi_raw, pc, outcome, score, plut, tlut, tol_out=2e-4, tol_g=1e-4,
            swap_fast=False):
    for p in plain.parameters():
        p.grad = None
    for p in fast.parameters():
        p.grad = None
    wi_p, bi_p = plut[wi_raw.long()], plut[bi_raw.long()]
    out_p = plain(us, wi_p, bi_p, pc)
    out_f = fast(1.0 - us if swap_fast else us, wi_raw, bi_raw, pc, tlut)
    target = 0.75 * torch.sigmoid(score * 2.25 / 400.0) + 0.25 * outcome
    ((torch.sigmoid(out_p) - target) ** 2).mean().backward()
    ((torch.sigmoid(out_f) - target) ** 2).mean().backward()
    res = {"out": (out_p - out_f).abs().max().item()}
    gp = {"w1": plain.w1.grad[:T.NF], "b1": plain.b1.grad, "w2": plain.w2.grad, "b2": plain.b2.grad}
    gf = {"w1": fast.w1.grad, "b1": fast.b1.grad, "w2": fast.w2.grad, "b2": fast.b2.grad}
    ok = res["out"] < tol_out
    for k in gp:
        scale = max(1.0, gp[k].abs().max().item())
        d = (gp[k] - gf[k]).abs().max().item()
        res[k] = d
        res[k + "_scale"] = scale
        ok &= d < tol_g * scale
    res["pad_grad"] = plain.w1.grad[T.PAD].abs().max().item()  # embedding_bag padding row: must stay 0
    ok &= res["pad_grad"] == 0.0
    return ok, res


def main():
    data = sys.argv[1]
    batch = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
    nb = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    dev = torch.device("cuda")
    ok_probe, why = T.K.triton_usable(dev)
    print("triton probe:", why)
    if not ok_probe:
        sys.exit(1)
    torch.manual_seed(7)
    fast = T.ForgeV2Triton(256, 8).to(dev)
    plain = T.ForgeV2Plain(256, 8).to(dev)
    with torch.no_grad():
        plain.w1[:T.NF] = fast.w1
        plain.w1[T.PAD] = 0
        plain.b1[:] = fast.b1
        plain.w2[:] = fast.w2
        plain.b2[:] = fast.b2
    plut, tlut = T.plain_lut(dev), T.triton_lut(dev)
    cfg = DataloaderSkipConfig(filtered=False, wld_filtered=False, random_fen_skipping=0, early_fen_skipping=-1,
                               soft_early_fen_skipping=0)
    s = st.create_sparse_batch_stream(b"K32H3", 1, [data], batch, True, cfg)
    all_ok = True
    planted_caught = 0
    for i in range(nb):
        b = st.fetch_next_sparse_batch(s)
        us, them, wi, bi, outcome, score, pc, qb = b.contents.get_tensors(dev)
        us = us.float()
        outcome, score, pc = outcome.float().view(-1), score.float().view(-1), pc.long()
        wi, bi = wi.clone(), bi.clone()
        st.destroy_sparse_batch(b)
        active = (wi >= 0).sum(1).float()
        ok, res = compare(plain, fast, us, wi, bi, pc, outcome, score, plut, tlut)
        print(f"batch {i}: size {wi.shape[0]} max_active {wi.shape[1]} mean active {active.mean().item():.1f} "
              f"-> {'OK' if ok else 'FAIL'} {res}")
        all_ok &= ok
        if i == 0:
            bad_lut = tlut.clone()
            used = tlut[wi[0, 0].long()].item()
            bad_lut[wi[0, 0].long()] = (used + 1) % T.NF  # one wrong remap entry
            okb, resb = compare(plain, fast, us, wi, bi, pc, outcome, score, plut, bad_lut)
            print(f"planted wrong remap entry -> {'FAIL (caught)' if not okb else 'NOT CAUGHT'} out {resb['out']:.3g}")
            planted_caught += 0 if okb else 1
            okw, resw = compare(plain, fast, us, wi, bi, pc, outcome, score, plut, tlut, swap_fast=True)
            print(f"planted swapped side to move (fast path only) -> {'FAIL (caught)' if not okw else 'NOT CAUGHT'} "
                  f"out {resw['out']:.3g}")
            planted_caught += 0 if okw else 1
    st.destroy_sparse_batch_stream(s)
    print(f"planted errors caught: {planted_caught}/2")
    final = all_ok and planted_caught == 2
    print("PASS" if final else "FAIL")
    sys.exit(0 if final else 1)


if __name__ == "__main__":
    main()
