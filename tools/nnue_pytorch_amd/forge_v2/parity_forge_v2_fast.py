"""R7 J1 parity: a net trained on the Triton path vs the engine's own v2 evaluation. GPL-3.0 tool code.
Derived from Grok Bot's F:\\nnue_pytorch\\forge_tools\\parity_forge_v2.py (read only).

usage: python parity_forge_v2_fast.py <ckpt.pt> <net.fnn2> <positions.fen> <engine_prefix> [--json out.json]
  <engine_prefix>.tsv comes from `nnue_v2_tool eval <net.fnn2> <positions.fen> <engine_prefix>` (the engine's
  loader and kernels, tools/nnue/nnue_v2_tool.cpp, built with the engine exe's flags).
Checks over every position:
  keys    K32H3 -> Forge remap (the kernel's table) == an independent Forge feature function written from
          include/forge/nnue_v2.hpp's comment (both perspectives, as sets)
  kernel  Triton forward == plain torch reference forward on the same float weights (max |diff| cp)
  outbkt  output bucket: trainer == engine
  deq     dequantised trainer (the .fnn2 integers / 4096, read back with Forge's reader) vs engine cp:
          max |diff| <= 1.001 (the engine truncates toward zero)
  float   float (pre-quantisation) trainer vs engine cp: the job's gate, max |diff| <= 2 cp
PASS needs keys, outbkt, deq and float on all positions."""
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import train_forge_v2_fast as T  # noqa: E402

from data_loader import stream as st  # noqa: E402

TYPES = "pnbrqk"


def forge_features(fen, persp, kmap):
    rows = fen.split()[0].split("/")
    pcs = []
    ksq = None
    for ri, row in enumerate(rows):
        f = 0
        for ch in row:
            if ch.isdigit():
                f += int(ch)
                continue
            sq = (7 - ri) * 8 + f
            color = 0 if ch.isupper() else 1
            typ = TYPES.index(ch.lower())
            pcs.append((sq, color, typ))
            if typ == 5 and color == persp:
                ksq = sq
            f += 1
    kr = ksq if persp == 0 else ksq ^ 56
    bucket = kmap[kr]
    flip = 7 if (kr & 7) >= 4 else 0
    out = set()
    for sq, color, typ in pcs:
        r = (sq if persp == 0 else sq ^ 56) ^ flip
        out.add(bucket * 768 + ((0 if color == persp else 1) * 6 + typ) * 64 + r)
    return out


def sparse(fens, dev):
    b = st.get_sparse_batch_from_fens("K32H3", fens, [0] * len(fens), [40] * len(fens), [0] * len(fens))
    us, them, wi, bi, outcome, score, pc, qb = [x.clone() for x in b.contents.get_tensors("cpu")]
    st.destroy_sparse_batch(b)
    return us.float().to(dev), wi.to(dev), bi.to(dev), pc.long().to(dev)


def main():
    ckpt, net_path, fen_path, prefix = sys.argv[1:5]
    out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else ""
    dev = torch.device("cuda")
    V2 = T.load_writer()
    fens = [line.strip() for line in open(fen_path) if line.strip()]
    ck = torch.load(ckpt, map_location="cpu")
    hidden, nob = ck["hidden"], ck["ob"]
    model = T.ForgeV2Triton(hidden, nob)
    model.load_state_dict(ck["state"])
    model = model.to(dev).eval()
    net = V2.read_v2(net_path)
    deq = T.ForgeV2Triton(hidden, nob)
    with torch.no_grad():
        deq.w1[:] = torch.tensor(np.asarray(net["w1"], dtype=np.float32)).view(-1, hidden) / 4096.0
        deq.b1[:] = torch.tensor(np.asarray(net["b1"], dtype=np.float32)) / 4096.0
        deq.w2[:] = torch.tensor(np.asarray(net["w2"], dtype=np.float32)).view(nob, -1) / 4096.0
        deq.b2[:] = torch.tensor(np.asarray(net["b2"], dtype=np.float32)) / 4096.0
    deq = deq.to(dev).eval()
    lut = T.triton_lut(dev)
    table = T.triton_lut("cpu").long()
    kmap = T.king_map()
    rows = [line.rstrip("\n").split("\t") for line in open(prefix + ".tsv")]
    hdr = rows[0] if not rows[0][0].isdigit() else None
    if hdr:
        rows = rows[1:]
    eng = np.array([int(r[-1]) for r in rows], dtype=np.float64)
    eng_pieces = np.array([int(r[6]) for r in rows])
    eng_ob = np.array([int(r[7]) for r in rows])
    raw, dq, ref, keys_bad, n_sets, ob_tr = [], [], [], 0, 0, []
    with torch.no_grad():
        for i in range(0, len(fens), 1000):
            chunk = fens[i:i + 1000]
            us, wi, bi, pc = sparse(chunk, dev)
            wic, bic = wi.cpu().long(), bi.cpu().long()
            for j, fen in enumerate(chunk):
                for persp, idx in ((0, wic[j]), (1, bic[j])):
                    got = set(int(table[x]) for x in idx if int(x) >= 0)
                    keys_bad += got != forge_features(fen, persp, kmap)
                    n_sets += 1
            raw.append((model(us, wi, bi, pc, lut) * 400 / 2.25).cpu().numpy())
            dq.append((deq(us, wi, bi, pc, lut) * 400 / 2.25).cpu().numpy())
            x = T.K.reference_x(us, wi, bi, lut, model.w1, model.b1)
            obr = T.output_bucket(pc, nob).view(-1, 1)
            ref.append((((x @ model.w2.t()).gather(1, obr).view(-1) + model.b2[obr.view(-1)]) * 400 / 2.25).cpu().numpy())
            ob_tr.append(T.output_bucket(pc, nob).cpu().numpy())
    raw = np.concatenate(raw).astype(np.float64)
    dq = np.concatenate(dq).astype(np.float64)
    ref = np.concatenate(ref).astype(np.float64)
    ob_tr = np.concatenate(ob_tr)
    n = min(len(eng), len(raw))
    d_deq = np.abs(np.clip(dq[:n], -30000, 30000) - eng[:n])
    d_raw = np.abs(np.clip(raw[:n], -30000, 30000) - eng[:n])
    d_ker = np.abs(raw[:n] - ref[:n])
    res = {
        "positions": int(n), "tsv_header": hdr,
        "keys_sets": int(n_sets), "keys_mismatches": int(keys_bad),
        "kernel_vs_torch_ref_max_cp": float(d_ker.max()),
        "outbkt_equal": int((eng_ob[:n] == ob_tr[:n]).sum()),
        "deq_max_cp": float(d_deq.max()), "deq_mean_cp": float(d_deq.mean()),
        "deq_over_1p001": int((d_deq > 1.001).sum()),
        "deq_trunc_equal": int((np.trunc(np.clip(dq[:n], -30000, 30000)) == eng[:n]).sum()),
        "float_max_cp": float(d_raw.max()), "float_mean_cp": float(d_raw.mean()),
        "float_over_2cp": int((d_raw > 2).sum()),
        "corr_float_engine": float(np.corrcoef(raw[:n], eng[:n])[0, 1]),
        "engine_mean_abs_cp": float(np.abs(eng[:n]).mean()),
        "pieces_min_max": [int(eng_pieces[:n].min()), int(eng_pieces[:n].max())],
    }
    ok = (res["keys_mismatches"] == 0 and res["outbkt_equal"] == n and res["deq_over_1p001"] == 0
          and res["float_over_2cp"] == 0)
    res["PASS"] = bool(ok)
    for k, v in res.items():
        print(f"{k}: {v}")
    print("PARITY PASS" if ok else "PARITY FAIL")
    if out_json:
        with open(out_json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, indent=1)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
