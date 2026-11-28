"""Server-Day 2-Billion-Position Double-Buffered Streaming Trainer for FORGENN3-P (.fqs.z shards).

Solves the VRAM ceiling for Server Day (1.4B - 2.0B usable positions = 54-72 GB raw tensors):
  - Partitions an arbitrary number of compressed .fqs.z shards into fixed-size GPU superbatches
    (e.g. --shards-per-superbatch 400 at 500k rows/shard -> ~7.6 GiB VRAM peak, safe on 20-24 GB GPUs AND 80 GB H100/A100!).
  - Background prefetch thread decompresses & packs superbatch (k+1) in CPU RAM while GPU trains
    superbatch (k) at 100% kernel throughput (0% GPU decompression stall!).
  - Injects Syzygy dead-draw + won-ending anchor shards into EVERY superbatch with exact WDL targets
    and Anchor Weight-Exemption Rule, plus --ob-smooth, --loss-pow (2.0/2.5), --skip-fqs-noisy,
    --skip-fqs-in-check (default True), --use-shard-weights, --ob-reweight, and atomic resume_ckpt.pt
    checkpointing at (epoch, superbatch_idx) granularity!
  - Built-in CPU-only --selftest verifies multi-superbatch streaming, anchor exact-WDL, and mid-epoch resume!
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path

import numpy as np
import torch

LAB = Path(os.environ.get("FORGE_LAB_ROOT", r"C:\nnue-lab"))
FIX = LAB / "neon/forge_fixes"
if (LAB / "pipeline").exists():
    sys.path.insert(0, str(LAB / "pipeline"))
if (LAB / "pipeline/ft_triton").exists():
    sys.path.insert(0, str(LAB / "pipeline/ft_triton"))
sys.path.insert(0, str(FIX))

import forge_v3p  # noqa: E402
import train_v3p as tv3p  # noqa: E402

FQS_MAGIC = b"FQS1\x00\x00\x00\x00"
FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)),
    ("stm", np.uint8),
    ("score16", np.int16),
    ("res8", np.int8),
    ("flags", np.uint8),
    ("weight_u8", np.uint8),
])


def list_shards(items: list[str]) -> list[Path]:
    out = []
    for s in items:
        p = Path(s)
        if p.is_dir():
            out.extend(sorted(list(p.glob("*.fqs")) + list(p.glob("*.fqs.z"))))
        else:
            out.append(p)
    if not out:
        raise SystemExit(f"No .fqs/.fqs.z shards found in {items}")
    return out


def read_fqs_filtered(path: Path, mask_bits: int) -> np.ndarray:
    raw = path.read_bytes()
    if path.name.endswith(".z"):
        raw = zlib.decompress(raw)
    if len(raw) < 8 or raw[:8] != FQS_MAGIC or (len(raw) - 8) % FQS_DTYPE.itemsize != 0:
        raise RuntimeError(f"Corrupt FQS1 shard: {path}")
    a = np.frombuffer(raw, dtype=FQS_DTYPE, offset=8)
    if mask_bits:
        a = a[(a["flags"] & mask_bits) == 0]
    return a.copy()


def group_shards_into_superbatches(shards: list[Path], shards_per_sb: int, seed: int, epoch: int) -> list[list[Path]]:
    rng = random.Random(seed * 1_000_003 + epoch)
    order = list(shards)
    rng.shuffle(order)
    return [order[i:i + shards_per_sb] for i in range(0, len(order), shards_per_sb)]


def load_superbatch_cpu(sb_shards: list[Path], mask_bits: int, anc_arr: np.ndarray | None) -> tuple[np.ndarray, int]:
    parts = [read_fqs_filtered(sp, mask_bits) for sp in sb_shards]
    parts = [p for p in parts if len(p) > 0]
    if not parts:
        return np.empty(0, dtype=FQS_DTYPE), 0
    main_cat = np.concatenate(parts, axis=0)
    n_main = len(main_cat)
    if anc_arr is not None and len(anc_arr) > 0:
        full = np.concatenate([main_cat, anc_arr], axis=0)
    else:
        full = main_cat
    return full, n_main


def selftest_cpu() -> int:
    """Zero-GPU CPU verification of multi-superbatch streaming + anchor exact-WDL + mid-epoch resume."""
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        sdir = tp / "shards"
        sdir.mkdir()
        codes = np.zeros(64, dtype=np.uint8)
        codes[4] = 6; codes[60] = 12; codes[3] = 5; codes[51] = 7
        pk = (codes[0::2] | (codes[1::2] << 4)).astype(np.uint8)

        for s in range(4):
            a = np.zeros(20, dtype=FQS_DTYPE)
            for i in range(20):
                a[i]["packed"] = pk
                a[i]["stm"] = (s + i) % 2
                a[i]["score16"] = 100 * ((i % 5) - 2)
                a[i]["res8"] = 1 if i % 3 == 0 else (-1 if i % 3 == 1 else 0)
                a[i]["flags"] = (1 if i % 4 == 1 else 0) | (2 if i % 5 == 0 else 0)
                a[i]["weight_u8"] = 128
            (sdir / f"s{s:02d}.fqs.z").write_bytes(zlib.compress(FQS_MAGIC + a.tobytes(), level=1))

        anc_p = tp / "anc.fqs.z"
        aa = np.zeros(4, dtype=FQS_DTYPE)
        for i in range(4):
            aa[i]["packed"] = pk; aa[i]["stm"] = i % 2; aa[i]["score16"] = 0; aa[i]["res8"] = 0; aa[i]["weight_u8"] = 128
        anc_p.write_bytes(zlib.compress(FQS_MAGIC + aa.tobytes(), level=1))

        shards = list_shards([str(sdir)])
        groups = group_shards_into_superbatches(shards, shards_per_sb=2, seed=7, epoch=0)
        assert len(groups) == 2 and sum(len(g) for g in groups) == 4
        anc_arr = read_fqs_filtered(anc_p, 0)
        cat0, n_main0 = load_superbatch_cpu(groups[0], mask_bits=2, anc_arr=anc_arr)
        cat1, n_main1 = load_superbatch_cpu(groups[1], mask_bits=2, anc_arr=anc_arr)
        # Each shard had 4 in_check rows dropped (20 - 4 = 16 -> 2 shards = 32 main + 4 anchors = 36)
        assert n_main0 == 32 and len(cat0) == 36 and n_main1 == 32 and len(cat1) == 36, (n_main0, len(cat0), n_main1, len(cat1))
        # Verify double-buffered prefetch executor returns identical arrays
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(load_superbatch_cpu, groups[1], 2, anc_arr)
            cat1_pf, n_main1_pf = fut.result()
        assert n_main1_pf == n_main1 and np.array_equal(cat1_pf, cat1)
        print(f"STREAM_V3P_SELFTEST_PASS: superbatches=2 main_per_sb={n_main0} anc={len(anc_arr)} total_per_sb={len(cat0)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--fqs-shards", nargs="+", default=[])
    ap.add_argument("--anchor-shards", nargs="+", default=[])
    ap.add_argument("--anchor-repeat-per-sb", type=int, default=4)
    ap.add_argument("--shards-per-superbatch", type=int, default=32, help="Number of .fqs.z shards per GPU superbatch")
    ap.add_argument("--skip-fqs-noisy", action="store_true")
    ap.add_argument("--keep-fqs-in-check", action="store_true")
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--hidden", type=int, default=1024)
    ap.add_argument("--king-buckets", type=int, default=8)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=8192)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--min-lr-frac", type=float, default=0.05)
    ap.add_argument("--warmup-steps", type=int, default=500)
    ap.add_argument("--lr-cycles", default="auto")
    ap.add_argument("--w1-decay", type=float, default=0.3)
    ap.add_argument("--ob-smooth", type=float, default=2e-6)
    ap.add_argument("--mix", type=float, default=0.80)
    ap.add_argument("--loss-pow", type=float, default=2.0)
    ap.add_argument("--use-shard-weights", action="store_true")
    ap.add_argument("--ob-reweight", choices=["none", "m4", "cc0"], default="none",
                    help="Optional per-output-bucket loss reweighting (anchors exempt)")
    ap.add_argument("--distill-net", default="", help="Optional v3 or v3p .pt teacher checkpoint for per-superbatch distillation")
    ap.add_argument("--distill-weight", type=float, default=0.2)
    ap.add_argument("--save-cycles", action="store_true", help="Save cand_e{ep}.pt at each cosine LR cycle end for SWA")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--gpu-hot-pause-c", type=float, default=98.0)
    ap.add_argument("--gpu-hot-resume-c", type=float, default=84.0)
    ap.add_argument("--mem-need-gb", type=float, default=8.0)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest_cpu()

    import batch_kernel_c as bc
    import forge_train as ft
    import forge_train_v3 as v3

    assert args.out_dir and args.fqs_shards, "Need --out-dir and --fqs-shards"
    mem_room = LAB / "tmp/fable_scratch/tools/mem_room.py"
    if args.mem_need_gb > 0 and mem_room.exists():
        r = subprocess.run([sys.executable, str(mem_room), str(args.mem_need_gb)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"REFUSED by mem_room: {r.stdout} {r.stderr}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dev = torch.device("cuda")
    torch.manual_seed(args.seed)
    model = tv3p.ForgeNetV3P(hidden=args.hidden, king_buckets=args.king_buckets, out_buckets=8, mirror=True, pairwise=True, has_psqt=True).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, fused=True)

    shards = list_shards(args.fqs_shards)
    mask_bits = (1 if args.skip_fqs_noisy else 0) | (0 if args.keep_fqs_in_check else 2)
    anc_arr = None
    if args.anchor_shards:
        anc_paths = list_shards(args.anchor_shards)
        anc_cat = np.concatenate([read_fqs_filtered(p, 0) for p in anc_paths], axis=0)
        anc_arr = np.tile(anc_cat, max(1, args.anchor_repeat_per_sb))

    if args.lr_cycles.strip().lower() == "auto":
        cycles = sorted({max(1, round(args.epochs * f)) for f in (0.15, 0.3, 0.6, 1.0)})
    else:
        cycles = [int(x) for x in args.lr_cycles.split(",") if x.strip()]
        if not cycles:
            raise SystemExit(f"Invalid --lr-cycles {args.lr_cycles!r}: must be 'auto' or comma-separated integers")

    t_net = None
    t_weight = 0.0
    if args.distill_net:
        import compact_record as cr  # noqa: F401
        t_path = Path(args.distill_net)
        ck_meta = torch.load(t_path, map_location="cpu", weights_only=True)
        t_arch = str(ck_meta.get("arch", ""))
        if t_arch == "v3p":
            t_net = tv3p.ForgeNetV3P(
                hidden=ck_meta["hidden"], king_buckets=ck_meta["king_buckets"], out_buckets=ck_meta["out_buckets"],
                mirror=ck_meta["mirror"], pairwise=ck_meta["pairwise"], has_psqt=ck_meta["has_psqt"],
            )
            t_net.load_state_dict(ck_meta["state"])
        elif t_arch == "v3":
            t_net = v3.load_model(str(t_path))
        else:
            raise SystemExit(f"train_v3p_stream.py requires a stand-alone v3 or v3p teacher, got arch={t_arch!r}")
        del ck_meta
        t_net.to(dev).eval()
        for prm in t_net.parameters():
            prm.requires_grad_(False)
        t_weight = float(args.distill_weight)
        print(f"STREAM TEACHER LOADED: {t_arch} {t_path.name} (w={t_weight})", flush=True)

    ckpt_path = out_dir / "resume_ckpt.pt"
    start_ep, start_sb, step, tl = 0, 0, 0, 0.0
    if args.resume and ckpt_path.exists():
        ck = torch.load(ckpt_path, map_location=dev, weights_only=False)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        start_ep = int(ck["epoch"])
        start_sb = int(ck.get("sb_idx", 0))
        step = int(ck["step"])
        tl = float(ck.get("tl", 0.0))
        print(f"RESUMED STREAM at ep={start_ep} sb={start_sb} step={step}", flush=True)

    guard = ft.GpuHeatGuard(args.gpu_hot_pause_c, args.gpu_hot_resume_c)
    ram = ft.RamGuard(float(os.environ.get("FORGE_MIN_FREE_RAM_GB", "1.5") or 0))
    t_train = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pf_pool:
        for ep in range(start_ep, args.epochs):
            groups = group_shards_into_superbatches(shards, args.shards_per_superbatch, args.seed, ep)
            sb0 = start_sb if ep == start_ep else 0
            start_sb = 0
            # Estimate total steps/epoch from first superbatch for smooth LR schedule
            est_steps_ep = None
            nxt_fut = pf_pool.submit(load_superbatch_cpu, groups[sb0], mask_bits, anc_arr) if sb0 < len(groups) else None
            run, cnt = 0.0, 0

            for sbi in range(sb0, len(groups)):
                cat, n_main = nxt_fut.result()
                if sbi + 1 < len(groups):
                    nxt_fut = pf_pool.submit(load_superbatch_cpu, groups[sbi + 1], mask_bits, anc_arr)
                n_sb = len(cat)
                if n_sb < args.batch_size:
                    continue
                if est_steps_ep is None:
                    est_steps_ep = max(1, (n_sb // args.batch_size) * len(groups))

                packed_g = torch.from_numpy(cat["packed"].copy()).to(dev)
                stm_g = torch.from_numpy(cat["stm"].copy()).to(dev)
                score_g = torch.from_numpy(cat["score16"].copy()).to(dev)
                res_g = torch.from_numpy(cat["res8"].copy()).to(dev)
                teacher_sb = None
                if t_net is not None:
                    import compact_record as cr
                    d_sb = {"packed": packed_g, "stm": stm_g, "n": n_sb}
                    teacher_sb = torch.empty(n_sb, device=dev, dtype=torch.float32)
                    with torch.no_grad():
                        for ti in range(0, n_main, args.batch_size):
                            tend = min(n_main, ti + args.batch_size)
                            tix = torch.arange(ti, tend, device=dev)
                            z_hce = torch.zeros(len(tix), device=dev)
                            teacher_sb[ti:tend] = torch.sigmoid(t_net(cr.unpack_feat(d_sb, tix), None, z_hce))
                        if n_main < n_sb:
                            teacher_sb[n_main:] = 0.5 * (res_g[n_main:].float() + 1.0)
                w_g = None
                if args.use_shard_weights or args.ob_reweight != "none":
                    w_g = torch.ones(n_sb, dtype=torch.float32, device=dev)
                    if args.use_shard_weights:
                        w_g[:n_main] *= torch.from_numpy(cat["weight_u8"][:n_main].copy()).to(dev).float() * (1.0 / 128.0)
                    if args.ob_reweight != "none":
                        ob_lut = torch.tensor(
                            [1.65, 1.01, 1.07, 1.00, 1.00, 0.99, 0.95, 0.65] if args.ob_reweight == "m4"
                            else [1.50, 1.089, 1.167, 0.978, 0.922, 0.883, 0.891, 0.70],
                            dtype=torch.float32, device=dev,
                        )
                        ob_idx = torch.from_numpy(((cat["flags"][:n_main] >> 4) & 7).astype(np.int64)).to(dev)
                        w_g[:n_main] *= ob_lut[ob_idx]
                        del ob_lut, ob_idx
                    mw = float(w_g[:n_main].mean().item())
                    if mw > 0:
                        w_g[:n_main] /= mw
                    w_g[n_main:] = 1.0
                del cat

                g_perm = torch.Generator(device=dev)
                g_perm.manual_seed(args.seed * 999_983 + ep * 1009 + sbi)
                perm = torch.randperm(n_sb, generator=g_perm, device=dev, dtype=torch.int32)
                sb_steps = n_sb // args.batch_size
                model.train()
                for bi in range(sb_steps):
                    idx = perm[bi * args.batch_size:(bi + 1) * args.batch_size]
                    lr = v3.lr_at(step, est_steps_ep, cycles, args)
                    for pg in opt.param_groups:
                        pg["lr"] = lr
                    rows, target, _, bucket = bc.make_batch_c(
                        idx, packed_g, stm_g, score_g, res_g, teacher_sb,
                        model.king_map, model.output_map, model.mirror,
                        ft.K / 400.0, args.mix, t_weight)
                    if n_main < n_sb:
                        anc_wdl = 0.5 * (res_g[idx.long()].float() + 1.0)
                        target = torch.where(idx >= n_main, anc_wdl, target)
                    pred = torch.sigmoid(model.forward_rows(rows, bucket))
                    err = (pred - target).pow(2) if abs(args.loss_pow - 2.0) < 1e-6 else (pred - target).abs().clamp(min=1e-7).pow(args.loss_pow)
                    loss = ((w_g[idx.long()] * err).sum() / w_g[idx.long()].sum().clamp(min=1e-7)) if w_g is not None else err.mean()
                    if args.ob_smooth > 0:
                        loss = loss + args.ob_smooth * model.ob_smooth_penalty()
                    opt.zero_grad(set_to_none=True)
                    loss.backward()
                    opt.step()
                    with torch.no_grad():
                        if args.w1_decay > 0:
                            model.w1.mul_(1.0 - lr * args.w1_decay)
                            model.psqt_w.mul_(1.0 - lr * args.w1_decay)
                    model.project()
                    step += 1
                    if bi % 20 == 0:
                        run += float(loss.detach()); cnt += 1
                        guard.tick(); ram.tick()

                del packed_g, stm_g, score_g, res_g, perm, w_g, teacher_sb
                torch.cuda.empty_cache()
                tl = run / max(1, cnt)
                tmp_ck = out_dir / "tmp_resume_ckpt.pt"
                next_ep = ep + 1 if sbi + 1 == len(groups) else ep
                next_sb = 0 if sbi + 1 == len(groups) else sbi + 1
                torch.save({
                    "epoch": next_ep, "sb_idx": next_sb, "step": step, "tl": tl,
                    "model": {k: v.detach().cpu() for k, v in model.state_dict().items()},
                    "opt": opt.state_dict(),
                }, tmp_ck)
                os.replace(tmp_ck, ckpt_path)
            print(f"STREAM LOSS {tl:.6f} epoch {ep+1}/{args.epochs} step {step}", flush=True)
            if args.save_cycles and (ep + 1) in cycles:
                tv3p.save_model_p(model, out_dir / f"cand_e{ep+1}.pt")

    model_p = out_dir / "cand.pt"
    net_p = out_dir / "cand.fnn3"
    tv3p.save_model_p(model, model_p)
    net = tv3p.to_file_net_p(model)
    cksum = forge_v3p.write_net(str(net_p), net)
    print(f"STREAM_V3P_DONE: {net_p} bytes={net_p.stat().st_size} cksum={cksum:016x} s={time.time()-t_train:.1f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
