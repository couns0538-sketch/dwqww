#!/usr/bin/env python
"""parity_h512.py - JOB E (2026-11-11): engine integer inference against the trainer's integer reference.

Own code. For one FORGENN3 net and a fixed position list it compares, position by position:
  ref    fable_nnue_v3.evaluate   Python integer reference (python-chess board, exact engine arithmetic)
  gpu    train_h512_gpu.forward_int   the integer forward the selection scorer uses (FPOS codes on the GPU)
  tool   forge_nnue_v3_tool eval  the engine's loader, cache refresh and compiled kernel (built from forge-combo29);
                                  the tool itself also checks fast path == scalar path (exit 3 on a mismatch)
  diag   evalfens of a FORGE_FAIR_DIAG engine exe with the net active: `total` is the search's own static
         evaluation, `network` the scalar reference inside the exe, `hce` = total - network
PASS needs ref == gpu == tool == diag.total == diag.network on every position, diag.hce == 0 everywhere, and equal
output buckets and king keys between ref and tool.
With --ckpt (the float checkpoint the net was exported from) it also reports float-against-integer error.

Score: centipawns from the side to move. out = trunc(sum / 255) + b2; cp = trunc(out * eval_scale / (255 * 64));
accumulator inputs clamp to 0..255; cp clamps to +-30000.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "train"))
import fable_nnue_v3 as v3          # noqa: E402
import fable_nnue_train as fb       # noqa: E402
from ckpt_io import load_checkpoint  # noqa: E402

PIECES = " PNBRQKpnbrqk"


def fen_from_codes(codes, stm_black):
    rows = []
    for r in range(7, -1, -1):
        row, empty = "", 0
        for f in range(8):
            c = int(codes[r * 8 + f])
            if c == 0:
                empty += 1
            else:
                if empty:
                    row += str(empty)
                    empty = 0
                row += PIECES[c]
        if empty:
            row += str(empty)
        rows.append(row)
    return "/".join(rows) + (" b" if stm_black else " w") + " - - 0 1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", required=True)
    ap.add_argument("--fens", nargs="*", default=[])
    ap.add_argument("--select-pos", default="")
    ap.add_argument("--select-rows", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=2026111103)
    ap.add_argument("--tool", required=True)
    ap.add_argument("--diag", default="")
    ap.add_argument("--ckpt", default="")
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-gpu", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    res = {"net": a.net, "net_md5": hashlib.md5(open(a.net, "rb").read()).hexdigest(), "sources": []}

    fens = []
    for f in a.fens:
        lines = [x.strip() for x in open(f, "r", encoding="utf-8") if x.strip()]
        res["sources"].append({"file": f, "md5": hashlib.md5(open(f, "rb").read()).hexdigest(), "positions": len(lines)})
        fens += lines
    if a.select_pos:
        data = fb.read_fpos(a.select_pos)
        rng = np.random.Generator(np.random.PCG64(a.seed))
        rows = np.sort(rng.choice(data["n"], size=a.select_rows, replace=False))
        fens += [fen_from_codes(data["codes"][r], bool(data["meta"][r] & 1)) for r in rows]
        res["sources"].append({"file": a.select_pos, "seed": a.seed, "positions": int(len(rows)),
                               "note": "FPOS rows carry no castling or en-passant rights; the FEN uses '-'"})
    fen_path = os.path.join(a.work, "parity_fens.txt")
    with open(fen_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(fens) + "\n")
    n = len(fens)
    res["positions"] = n
    res["fen_file_md5"] = hashlib.md5(open(fen_path, "rb").read()).hexdigest()

    # ---- Python integer reference
    net = v3.read_net(a.net)
    ref_cp = np.zeros(n, np.int64)
    ref_ob = np.zeros(n, np.int64)
    ref_keys = np.zeros((n, 4), np.int64)
    stm_black = np.zeros(n, bool)
    codes = np.zeros((n, 64), np.uint8)
    for i, fen in enumerate(fens):
        board = v3.board_from_fen(fen)
        cp, ob, (kw, fw), (kb, fbk), _ = v3.evaluate(net, board)
        ref_cp[i], ref_ob[i] = cp, ob
        ref_keys[i] = (kw, fw, kb, fbk)
        stm_black[i] = not board.turn
        for sq, piece in board.piece_map().items():
            codes[i, sq] = piece.piece_type + (0 if piece.color else 6)
    pieces = (codes != 0).sum(axis=1)
    res["coverage"] = {
        "side_to_move": {"white": int((~stm_black).sum()), "black": int(stm_black.sum())},
        "white_king_bucket_x_mirror": {f"{k}/{'m' if f else 'n'}": int(((ref_keys[:, 0] == k) & ((ref_keys[:, 1] != 0) == bool(f))).sum())
                                       for k in range(net.king_buckets) for f in (0, 1)},
        "black_king_bucket_x_mirror": {f"{k}/{'m' if f else 'n'}": int(((ref_keys[:, 2] == k) & ((ref_keys[:, 3] != 0) == bool(f))).sum())
                                       for k in range(net.king_buckets) for f in (0, 1)},
        "output_bucket": {str(k): int((ref_ob == k).sum()) for k in range(net.output_buckets)},
        "pieces_min_max": [int(pieces.min()), int(pieces.max())],
        "ref_cp_abs_mean": float(np.abs(ref_cp).mean()), "ref_cp_min_max": [int(ref_cp.min()), int(ref_cp.max())],
        "saturated_30000": int((np.abs(ref_cp) >= 30000).sum()),
    }
    res["coverage"]["all_white_king_cells_hit"] = all(v > 0 for v in res["coverage"]["white_king_bucket_x_mirror"].values())
    res["coverage"]["all_black_king_cells_hit"] = all(v > 0 for v in res["coverage"]["black_king_bucket_x_mirror"].values())
    res["coverage"]["all_output_buckets_hit"] = all(v > 0 for v in res["coverage"]["output_bucket"].values())

    ok = True
    # ---- engine tool
    p = subprocess.run([a.tool, "eval", a.net, fen_path], capture_output=True, text=True)
    rows = [[int(x) for x in line.split()] for line in p.stdout.splitlines() if line.strip()]
    tool = np.array(rows, np.int64)
    res["tool"] = {"exe": a.tool, "md5": hashlib.md5(open(a.tool, "rb").read()).hexdigest(), "exit": p.returncode,
                   "stderr_tail": p.stderr.strip()[-300:], "lines": int(len(tool))}
    if len(tool) != n or p.returncode != 0:
        ok = False
        res["tool"]["cp_mismatches"] = None
    else:
        res["tool"]["cp_mismatches"] = int((tool[:, 0] != ref_cp).sum())
        res["tool"]["bucket_mismatches"] = int((tool[:, 1] != ref_ob).sum())
        res["tool"]["king_key_mismatches"] = int((tool[:, 2:6] != ref_keys).any(axis=1).sum())
        res["tool"]["max_abs_cp_diff"] = int(np.abs(tool[:, 0] - ref_cp).max())
        ok &= res["tool"]["cp_mismatches"] == 0 and res["tool"]["bucket_mismatches"] == 0 and res["tool"]["king_key_mismatches"] == 0

    # ---- diagnostic engine exe (the search's own static evaluation)
    if a.diag:
        out_path = os.path.join(a.work, "diag_evalfens.tsv")
        if os.path.exists(out_path):
            os.remove(out_path)
        cmds = (f"uci\nsetoption name NNUEArchFile value {a.net}\nsetoption name NNUEArch value true\nisready\n"
                f"evalfens {fen_path} {out_path}\nquit\n")
        p = subprocess.run([a.diag], input=cmds, capture_output=True, text=True)
        info = [line for line in p.stdout.splitlines() if "NNUE v3" in line or "evalfens" in line]
        d = np.array([[int(x) for x in line.split("\t")] for line in open(out_path) if line.strip()], np.int64) if os.path.exists(out_path) else np.zeros((0, 5), np.int64)
        res["diag"] = {"exe": a.diag, "md5": hashlib.md5(open(a.diag, "rb").read()).hexdigest(), "exit": p.returncode,
                       "info": info, "lines": int(len(d))}
        if len(d) != n:
            ok = False
        else:
            res["diag"]["total_vs_ref_mismatches"] = int((d[:, 1] != ref_cp).sum())
            res["diag"]["network_vs_ref_mismatches"] = int((d[:, 2] != ref_cp).sum())
            res["diag"]["hce_nonzero"] = int((d[:, 3] != 0).sum())
            res["diag"]["hce_abs_max"] = int(np.abs(d[:, 3]).max())
            ok &= res["diag"]["total_vs_ref_mismatches"] == 0 and res["diag"]["network_vs_ref_mismatches"] == 0 and res["diag"]["hce_nonzero"] == 0

    # ---- GPU integer forward (the selection scorer's arithmetic) and float error
    if not a.no_gpu:
        import torch
        import train_h512_gpu as t
        dev = torch.device("cuda")
        boards = (codes[:, 0::2] | (codes[:, 1::2] << 4)).astype(np.uint8)
        bt = torch.from_numpy(boards).to(dev)
        mt = torch.from_numpy(stm_black.astype(np.uint8)).to(dev)
        inet = t.IntNet(a.net, dev)
        T = t.Tables(inet.cfg, dev)
        with torch.no_grad():
            us_white, wi, bi, ob, phase = t.features(bt, mt, T)
            gcp = t.forward_int(inet, us_white, wi, bi, ob).cpu().numpy()
        res["gpu_int"] = {"cp_mismatches": int((gcp != ref_cp).sum()), "bucket_mismatches": int((ob.cpu().numpy() != ref_ob).sum())}
        ok &= res["gpu_int"]["cp_mismatches"] == 0 and res["gpu_int"]["bucket_mismatches"] == 0
        if a.ckpt:
            ck = load_checkpoint(a.ckpt, torch)
            cfg = ck["cfg"]
            model = fb.build_model(cfg, torch)
            model.load_state_dict(ck["state"])
            model = model.to(dev)
            tmp = os.path.join(a.work, "ckpt_reexport.fnn3")
            t.export_cpu(model, cfg, tmp)
            same = hashlib.md5(open(tmp, "rb").read()).hexdigest() == res["net_md5"]
            Tm = t.Tables(cfg, dev)
            with torch.no_grad():
                cq = t.forward_plain(model, cfg, us_white, wi, bi, ob, Tm, quant=True).double().clamp(-30000, 30000).cpu().numpy()
                cf = t.forward_plain(model, cfg, us_white, wi, bi, ob, Tm, quant=False).double().clamp(-30000, 30000).cpu().numpy()
            dq, df = np.abs(cq - ref_cp), np.abs(cf - ref_cp)
            res["float_vs_int"] = {
                "ckpt": a.ckpt, "ckpt_exports_to_this_net": bool(same),
                "fake_quantised_float": {"max_cp": float(dq.max()), "mean_cp": float(dq.mean()), "over_2cp": int((dq > 2).sum())},
                "unquantised_float": {"max_cp": float(df.max()), "mean_cp": float(df.mean()), "over_2cp": int((df > 2).sum()),
                                      "over_20cp": int((df > 20).sum())}}
    res["PASS"] = bool(ok)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print(json.dumps(res, indent=1, sort_keys=True))
    print("PARITY PASS" if ok else "PARITY FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
