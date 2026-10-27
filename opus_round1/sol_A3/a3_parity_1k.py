#!/usr/bin/env python3
"""A3 acceptance 1: trainer -> converter -> reference evaluator agree on 1000 + 1000 positions.

usage: a3_parity_1k.py --trainer <copy of the trainer> --ckpt <epoch.pt> --net <epoch.fnn> --pos <h000.pos>
                       --fens <fens.txt> [--n 1000] [--tol-cp 0.05]

--trainer must be a copy named opus_nnue_smoke_<name>.py (PC rule: trainer code only runs from such copies);
it is imported, never started. Checks (stated before running, spec section 7):
  E1 export: every int16 of the file == the integer of the trainer's QAT forward (feature transformer, folded
     factoriser); every float32 of the dense layers == the checkpoint tensor, bit for bit;
  E2 output bucket of every position: trainer == reference;
  E3 accumulators (pre-activation, both perspectives): trainer float32 == reference float32, bit for bit
     (all values are multiples of 1/4096, so the sums are exact in any order);
  E4 network output: |trainer - reference| <= --tol-cp centipawns (out * 400 / 2.25) on every position: the trainer
     sums its dense layers with library GEMMs, the reference in the fixed engine order, so float32 rounding may
     differ; a layout or order bug moves outputs by whole centipawns or more.
Reported, not gated: integer-cp agreement after truncation, reference engine order vs float64.
Positions: the first --n records of the synthetic data32 holdout (FPOS) and the first --n FENs of --fens.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import forge_astra_A3_refeval_20261027 as R  # noqa: E402

F32 = np.float32


def load_trainer(path):
    name = Path(path).stem
    if "train_resid" in name:
        raise SystemExit("refusing a trainer file named train_resid*")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fpos_positions(path, n):
    raw = Path(path).read_bytes()
    assert raw[:4] == b"FPOS"
    total = int.from_bytes(raw[8:16], "little")
    b = np.frombuffer(raw, np.uint8, total * 32, 16).reshape(total, 32)[:n]
    m = np.frombuffer(raw, np.uint8, total, 16 + total * 34)[:n]
    codes = np.empty((len(b), 64), np.uint8)
    codes[:, 0::2] = b & 15
    codes[:, 1::2] = b >> 4
    return codes, (m & 1).astype(np.int64)


def fen_positions(path, n):
    codes, stm = [], []
    for line in open(path, encoding="ascii"):
        fen = line.split("|")[0].strip()
        if fen:
            c, s = R.codes_from_fen(fen)
            codes.append(c)
            stm.append(s)
        if len(codes) >= n:
            break
    return np.array(codes, np.uint8), np.array(stm, np.int64)


def check_export(T, model, net):
    import torch
    with torch.no_grad():
        w, b = model.ft_params()                      # QAT forward values [KB, H, 768], [H]
        wi = torch.round(w * 4096.0).to(torch.int64).numpy().transpose(0, 2, 1).reshape(-1, model.hidden)
        bi = torch.round(b * 4096.0).to(torch.int64).numpy()
        exact = bool((w * 4096.0 == torch.round(w * 4096.0)).all()) and bool((b * 4096.0 == torch.round(b * 4096.0)).all())
    ft_bad = int((wi != net.ft_w_int).sum()) + int((bi != net.ft_b_int).sum())
    sd = model.state_dict()
    ob, l1, l2, h = model.ob, model.l1, model.l2, model.hidden

    def same(t, a):
        return np.array_equal(t.numpy().astype(F32).reshape(a.shape).view(np.uint32), a.view(np.uint32))

    dense = [same(sd["fc1.weight"], net.l1_w), same(sd["fc1.bias"], net.l1_b), same(sd["out.weight"], net.out_w),
             same(sd["out.bias"], net.out_b)]
    if l2:
        dense += [same(sd["fc2.weight"], net.l2_w), same(sd["fc2.bias"], net.l2_b)]
    n_int = net.ft_w_int.size + net.ft_b_int.size
    return ft_bad == 0 and exact and all(dense), f"ft ints mismatching {ft_bad}/{n_int} (QAT values on the grid: {exact}); " \
        f"dense blocks bit-equal {sum(dense)}/{len(dense)}"


def compare(T, model, net, codes, stm, tol_cp, label):
    import torch
    ct = torch.from_numpy(codes.astype(np.int64))
    st = torch.from_numpy(stm)
    with torch.no_grad():
        a_s, a_o = model.accumulators(ct, st)
        out_t = model(ct, st).numpy().astype(F32)
        ob_t = model.bucket(ct).numpy()
    a_s, a_o = a_s.numpy(), a_o.numpy()
    n = len(codes)
    acc_ok = ob_ok = cp_ok = int_eq = 0
    max_cp = max_64 = 0.0
    for i in range(n):
        acc = [R.refresh(net, codes[i], 0), R.refresh(net, codes[i], 1)]
        s = int(stm[i])
        ob = R.output_bucket(net, codes[i])
        ob_ok += ob == int(ob_t[i])
        acc_ok += acc[s].tobytes() == a_s[i].astype(F32).tobytes() and acc[1 - s].tobytes() == a_o[i].astype(F32).tobytes()
        out_r, cp_r = R.evaluate_acc(net, acc[s], acc[1 - s], ob)
        out_64 = R.evaluate_acc_f64(net, acc[s], acc[1 - s], ob)
        d_cp = abs(float(out_t[i]) - float(out_r)) * 400.0 / 2.25
        max_cp = max(max_cp, d_cp)
        max_64 = max(max_64, abs(float(out_r) - out_64) * 400.0 / 2.25)
        cp_ok += d_cp <= tol_cp
        cp_t = int(np.trunc(np.clip(F32(F32(out_t[i] * F32(400.0)) / F32(2.25)), -30000, 30000)))
        int_eq += cp_t == cp_r
    ok = acc_ok == n and ob_ok == n and cp_ok == n
    lines = [f"[{label}] {n} positions",
             f"  E2 output bucket trainer == reference:                 {ob_ok}/{n}",
             f"  E3 accumulators (both perspectives, float32 bits):     {acc_ok}/{n}",
             f"  E4 |trainer - reference| <= {tol_cp} cp:                  {cp_ok}/{n}  (max {max_cp:.6f} cp)",
             f"  info: integer cp equal after truncation:               {int_eq}/{n}",
             f"  info: reference engine order vs float64, max:          {max_64:.6f} cp"]
    return ok, "\n".join(lines)


def run(trainer, ckpt, net_path, pos, fens, n=1000, tol_cp=0.05):
    import torch
    torch.set_num_threads(1)
    T = load_trainer(trainer)
    ck = torch.load(ckpt, map_location="cpu", weights_only=True)
    model = T.build_model(ck["config"])
    model.load_state_dict(ck["model"])
    model.eval()
    net = R.Net(net_path)
    ok_e, msg_e = check_export(T, model, net)
    out = [f"checkpoint {ckpt}", f"net {net_path}", f"E1 export: {msg_e} -> {'OK' if ok_e else 'MISMATCH'}"]
    ok = ok_e
    for label, (codes, stm) in (("data32 holdout h000 (synthetic FPOS)", fpos_positions(pos, n)),
                                ("real self-play FENs", fen_positions(fens, n))):
        ok_s, msg = compare(T, model, net, codes, stm, tol_cp, label)
        ok &= ok_s
        out.append(msg)
    out.append("PASS" if ok else "FAIL")
    return ok, "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trainer", required=True)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--pos", required=True)
    ap.add_argument("--fens", required=True)
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--tol-cp", type=float, default=0.05)
    a = ap.parse_args()
    ok, msg = run(a.trainer, a.ckpt, a.net, a.pos, a.fens, a.n, a.tol_cp)
    print(msg, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
