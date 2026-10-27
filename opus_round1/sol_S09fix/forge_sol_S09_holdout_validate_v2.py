#!/usr/bin/env python3
"""S09-5: validation of the S09 v2 trainer's 8-head path on the REAL 013/014 holdout (no net is trained).

On every row of the holdout subset (all rows, float64 sums, the trainer's own forward and targets) it reports:
  1. head occupancy: rows per piece-count head, counted independently from the raw board nibbles
     (pieces incl. kings, head = clamp((pieces-1)//4, 0, 7));
  2. MSE (blend 1.0 / 0.6 / 0.8, overall and per head) of HCE alone and of every given net, with the trainer's
     forward (`--net NAME=PATH`; 1-head nets use buckets=1, 8-head nets buckets=8);
  3. parity: the 1-head e12 net vs the same net replicated into 8 heads (max |logit difference|, limit 1e-5);
  4. head selection on real rows: a control copy with head h bias += (h+1)/64 must shift every row's logit by exactly
     (head+1)/64 of the independently counted head (0 mismatches allowed);
  5. optimizer check (CPU proxy of the DirectML optimizer check): from the replicated 8-head e12 init, --opt-steps
     in-memory steps on real holdout batches with the trainer's default optimizer (AdamDML + dev-scalars, as
     `--adam-impl dml --dev-scalars 1`) and with stock torch.optim.Adam; parameters compared after every step; heads
     without rows in any batch so far must stay bit-identical. Nothing is saved or exported (no 8-head net trained).
DirectML itself is not run here (no torch_directml in the read-only venv; the GPU is busy with production training).
usage: forge_sol_S09_holdout_validate_v2.py --trainer V2.py --pos H.pos --hce-dir DIR --rep8 NAME --out DIR
       --net NAME=PATH [--net ...] [--batch 4096] [--opt-steps 5] [--lr 7.07e-4]
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forge_sol_S09_export_identity_v2 import parse_inc, load_trainer, model_from_net  # noqa: E402

BLENDS = (1.0, 0.6, 0.8)
K = 2.25


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def heads_from_boards(boards):
    lo, hi = boards & 15, boards >> 4
    pieces = (lo > 0).sum(axis=1) + (hi > 0).sum(axis=1)
    return pieces.astype(np.int64), np.clip((pieces - 1) // 4, 0, 7).astype(np.int64)


def replicate8(net):
    r = copy.deepcopy(net)
    r["arrays"]["NnueW2"] = np.tile(net["arrays"]["NnueW2"], 8)
    r["arrays"]["NnueB2"] = np.tile(net["arrays"]["NnueB2"], 8)
    r["heads"] = 8
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trainer", required=True)
    ap.add_argument("--pos", required=True)
    ap.add_argument("--hce-dir", required=True)
    ap.add_argument("--net", action="append", required=True)
    ap.add_argument("--rep8", required=True, help="name of the 1-head net to replicate into 8 heads")
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=4096)
    ap.add_argument("--opt-steps", type=int, default=5)
    ap.add_argument("--lr", type=float, default=7.07e-4)
    ap.add_argument("--max-rows", type=int, default=0, help="0 = all rows")
    a = ap.parse_args(argv)
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    tr = load_trainer(a.trainer, "s09_v2_trainer_validate")
    t0 = time.time()
    hold = tr.load_set([a.pos], a.hce_dir)
    n = hold["n"] if not a.max_rows else min(a.max_rows, hold["n"])
    pieces, heads = heads_from_boards(hold["boards"][:n])
    occ = np.bincount(heads, minlength=8).tolist()
    res = {"trainer": a.trainer, "trainer_sha256": hashlib.sha256(Path(a.trainer).read_bytes()).hexdigest(),
           "holdout": {"pos": a.pos, "pos_md5": md5(a.pos), "hce_md5": md5(Path(a.hce_dir) / (Path(a.pos).stem + ".hce")),
                       "rows": int(n)}, "head_occupancy": occ, "pieces_min_max": [int(pieces.min()), int(pieces.max())]}
    print(f"holdout rows {n:,} loaded in {time.time() - t0:.0f}s; head occupancy {occ}", flush=True)

    nets = {}
    for spec in a.net:
        name, _, path = spec.partition("=")
        net = parse_inc(path)
        nets[name] = {"net": net, "path": path, "md5": md5(path)}
    base = nets[a.rep8]["net"]
    rep = replicate8(base)
    ctrl = replicate8(base)
    ctrl["arrays"]["NnueB2"] = (ctrl["arrays"]["NnueB2"].astype(np.int32) + 64 * np.arange(1, 9)).astype(np.int16)
    models = {"HCE": None}
    for name, v in nets.items():
        models[name] = model_from_net(tr, v["net"], buckets=v["net"]["heads"]).eval()
    models[a.rep8 + "_rep8"] = model_from_net(tr, rep, buckets=8).eval()
    models[a.rep8 + "_rep8_ctrl"] = model_from_net(tr, ctrl, buckets=8).eval()

    sse = {m: {b: np.zeros(8) for b in BLENDS} for m in models}
    par = {"max_abs_logit_diff_1head_vs_rep8": 0.0}
    ctrl_mismatch, ctrl_max_err = 0, 0.0
    t1 = time.time()
    with torch.no_grad():
        for s in range(0, n, a.batch):
            idx = np.arange(s, min(n, s + a.batch))
            bt = tr.pack_batch(tr.make_batch(hold, idx), K)
            codes, stm, wres, score, hce_l = tr.to_dev(bt, torch.device("cpu"), K)
            h = torch.from_numpy(heads[idx])
            tgt = {b: tr.targets(score, stm, wres, K, b)[2].double() for b in BLENDS}
            logits = {}
            for m, model in models.items():
                logit = hce_l if model is None else model(codes, stm, hce_l)
                logits[m] = logit
                pred = torch.sigmoid(logit).double()
                for b in BLENDS:
                    err = (pred - tgt[b]) ** 2
                    sse[m][b] += np.bincount(h.numpy(), weights=err.numpy(), minlength=8)
            d = (logits[a.rep8] - logits[a.rep8 + "_rep8"]).abs().max().item()
            par["max_abs_logit_diff_1head_vs_rep8"] = max(par["max_abs_logit_diff_1head_vs_rep8"], d)
            shift = (logits[a.rep8 + "_rep8_ctrl"] - logits[a.rep8 + "_rep8"]).double() * 64.0
            derived = torch.round(shift).long() - 1
            ctrl_mismatch += int((derived != h).sum())
            ctrl_max_err = max(ctrl_max_err, float((shift - (h + 1).double()).abs().max()))
            if (s // a.batch) % 50 == 0:
                print(f"  rows {min(n, s + a.batch):,}/{n:,} ({time.time() - t1:.0f}s)", flush=True)
    occ_arr = np.asarray(occ, dtype=np.float64)
    table = {}
    for m in models:
        table[m] = {str(b): float(sse[m][b].sum() / n) for b in BLENDS}
        table[m]["per_head_b0.6"] = [float(x) if c else None for x, c in zip(sse[m][0.6] / np.maximum(occ_arr, 1), occ)]
    res["mse"] = table
    res["nets"] = {k: {"path": v["path"], "md5": v["md5"], "heads": v["net"]["heads"]} for k, v in nets.items()}
    res["parity_1head_vs_rep8"] = dict(par, limit=1e-5, status="PASS" if par["max_abs_logit_diff_1head_vs_rep8"] <= 1e-5 else "FAIL")
    res["head_selection_control"] = {"rows": int(n), "mismatches": ctrl_mismatch, "max_abs_shift_error_in_64ths": ctrl_max_err,
                                     "status": "PASS" if ctrl_mismatch == 0 else "FAIL"}
    print(f"eval done in {time.time() - t1:.0f}s", flush=True)

    # 5. optimizer check on CPU (no export, nothing saved)
    m_dml = model_from_net(tr, rep, buckets=8).train()
    m_ref = copy.deepcopy(m_dml)
    sys.path.insert(0, str(Path(a.trainer).resolve().parent))
    from qa_adam_dml import AdamDML  # the trainer's helper (same folder as the trainer copy, as the trainer imports it)
    opt_dml = tr.make_adam_devscalars(AdamDML)(m_dml.parameters(), lr=a.lr, foreach=False, dev=torch.device("cpu"))
    opt_ref = torch.optim.Adam(m_ref.parameters(), lr=a.lr, foreach=False)
    sc = torch.zeros(2)
    seen_heads, steps = np.zeros(8, bool), []
    rng = np.random.default_rng(20261027)
    init = model_from_net(tr, rep, buckets=8)
    one_head = 4  # step 1 uses rows of this head only: exactly this head's output row may move
    for step in range(a.opt_steps):
        if step == 0:
            idx = np.flatnonzero(heads == one_head)[: a.batch]
        elif step % 2:
            idx = np.sort(rng.choice(n, a.batch, replace=False))
        else:
            idx = np.arange(step * a.batch, min(n, (step + 1) * a.batch))
        bt = tr.pack_batch(tr.make_batch(hold, idx), K)
        codes, stm, wres, score, hce_l = tr.to_dev(bt, torch.device("cpu"), K)
        seen_heads |= np.bincount(heads[idx], minlength=8) > 0
        sc.copy_(torch.tensor([0.6, 0.4], dtype=torch.float32))
        losses = {}
        for label, model, opt, use_t in (("dml", m_dml, opt_dml, True), ("torch", m_ref, opt_ref, False)):
            if use_t:
                _, _, tg = tr.targets_t(score, stm, wres, K, sc[0], sc[1])
            else:
                _, _, tg = tr.targets(score, stm, wres, K, 0.6)
            opt.zero_grad(set_to_none=True)
            loss = torch.nn.functional.mse_loss(torch.sigmoid(model(codes, stm, hce_l)), tg)
            loss.backward()
            opt.step()
            model.project_weights()
            losses[label] = float(loss)
        diffs = {k: float((p1 - p2).abs().max()) for (k, p1), (_, p2) in zip(m_dml.named_parameters(), m_ref.named_parameters())}
        moved = ((m_dml.out.weight.detach() != init.out.weight.detach()).any(dim=1)
                 | (m_dml.out.bias.detach() != init.out.bias.detach())).numpy()
        steps.append({"step": step + 1, "rows": int(len(idx)), "rows_per_head": np.bincount(heads[idx], minlength=8).tolist(),
                      "max_abs_param_diff_dml_vs_torch": diffs, "heads_moved_dml": moved.tolist(),
                      "unseen_heads_unchanged": bool(not (moved & ~seen_heads).any()), "loss": losses})
        print(f"  opt step {step + 1}: rows/head {steps[-1]['rows_per_head']}; max|dml-torch| {max(diffs.values()):.3e}; "
              f"moved heads {moved.astype(int).tolist()}", flush=True)
    only_one = steps[0]["heads_moved_dml"] == [i == one_head for i in range(8)]
    worst = max(max(s["max_abs_param_diff_dml_vs_torch"].values()) for s in steps)
    res["optimizer_check_cpu"] = {"steps": steps, "lr": a.lr, "worst_max_abs_param_diff": worst,
                                  "step1_single_head": one_head, "step1_only_that_head_moved": only_one,
                                  "status": "PASS" if worst <= 1e-6 and only_one and all(s["unseen_heads_unchanged"] for s in steps) else "FAIL",
                                  "directml": "UNVERIFIED (not run: no torch_directml in the read-only venv; GPU busy with production training)"}
    (out / "holdout_validate_result.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    lines = [f"Holdout `{Path(a.pos).name}` md5 {res['holdout']['pos_md5']}, {n:,} rows (all rows, float64 sums).", "",
             "| net | b1.0 (teacher) | b0.6 | b0.8 |", "|---|---:|---:|---:|"]
    for m in models:
        lines.append(f"| {m} | {table[m]['1.0']:.7f} | {table[m]['0.6']:.7f} | {table[m]['0.8']:.7f} |")
    lines += ["", "Head occupancy (rows per head 0..7): " + ", ".join(f"{c:,}" for c in occ), "",
              "| net | " + " | ".join(f"h{i} b0.6" for i in range(8)) + " |", "|---|" + "---:|" * 8]
    for m in models:
        lines.append(f"| {m} | " + " | ".join("-" if v is None else f"{v:.5f}" for v in table[m]["per_head_b0.6"]) + " |")
    lines += ["", f"Parity 1-head vs replicated 8: max |logit diff| {par['max_abs_logit_diff_1head_vs_rep8']:.3e} "
              f"({res['parity_1head_vs_rep8']['status']}); head-selection control mismatches {ctrl_mismatch} "
              f"({res['head_selection_control']['status']}); optimizer check worst |dml-torch| {worst:.3e} "
              f"({res['optimizer_check_cpu']['status']})."]
    (out / "holdout_validate_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    ok = all(res[k]["status"] == "PASS" for k in ("parity_1head_vs_rep8", "head_selection_control", "optimizer_check_cpu"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
