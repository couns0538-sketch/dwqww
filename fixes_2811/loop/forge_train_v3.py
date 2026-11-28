"""Trainer for the FORGENN3 net of the engine tree forge/r7: a stand-alone net with king-bucketed inputs.

    8 mirrored king buckets x 768 inputs per side  ->  H hidden units, clamp 0..1 and square, both sides
    ->  8 output buckets by piece count  ->  one value; centipawns = value * 400.

Written on the owner's PC on 2026-11-15. The net format and its layouts are those of the earlier work on branch
fable/standalone-h512-20261111 of the owner's repo (see pipeline/forge_v3.py and forge/r7/EXPORT_NOTE.txt); the
recipe follows what made that branch's "candidate 3" (survey/h512_candidate3_recipe.md, read by the Opus session):
a factoriser, weight decay on the king-bucketed weights only, a constant target mix, cosine cycles.
Everything else is shared with forge_train.py: the data files and their caches, the loader that puts one round
at a time on the card, the heat and memory guards, the loss, the Triton first layer (here with one index row per
side: pipeline/ft_triton/ft_kernels.py, SparseRowsAct), the teacher switch.

    python forge_train_v3.py train  --datasets A.plain B.plain ... --val V.plain --out-model M.pt --hce-exe X
                                    [--hidden 512] [--epochs 40] [--batch-size 8192] [--lr 5e-4]
                                    [--w1-decay 0.3] [--lr-cycles 6,12,24,40] [--mix 0.75] [--keep-noisy]
    python forge_train_v3.py export --model M.pt --net N.fnn3
    python forge_train_v3.py score  --model M.pt --val V.plain --hce-exe X      hold-out losses at the 0.6 mix

Lines printed: "LOSS x epoch i/n ..." per pass, "FIT epoch i: train-sample x, hold-out y" (how far the training
rows are ahead of unseen ones), "VAL x" at the end. Needs the graphics card.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forge_train as ft  # noqa: E402
import forge_v3  # noqa: E402

QA, QB = float(forge_v3.QA), float(forge_v3.QB)

# The wide record on the card, bytes a position (2026-11-16, review of the compact record, F3): the 32 int16 inputs
# (64) + score, result and the hand-written value as float32 (12) + the zeroed or teacher's copy of the hand-written
# value (4) + the stored teacher value (4) + the pass order (4). When the compact record was asked for (FORGE_COMPACT=1)
# and the wide record is loaded instead, it is loaded only if this many bytes a position + WIDE_FIT_RESERVE_BYTES fit
# into the card's free memory; otherwise the training stops with one line instead of spilling into main memory.
WIDE_BYTES_PER_POSITION = 88
# what the wide window must leave for the rest: the loader's stm_features temporaries of one 500,000-row chunk (about
# 1.7 GB), the model with its Adam state, the teacher, the hold-out, the train-sample rows
WIDE_FIT_RESERVE_BYTES = 2 * 2 ** 30


def wide_fits(paths: list[str], hce_exe: str, skip_noisy: bool, dev) -> tuple[bool, str]:
    """Would the wide record of these files fit into the card's free memory now? Returns (fits, one line of text).
    True also when the free memory cannot be read (the check never stops a training on a guess);
    FORGE_WIDE_FIT_CHECK=0 switches the check off."""
    n = int(sum(ft._count_one(p, hce_exe, skip_noisy, True) for p in paths))
    torch.cuda.empty_cache()                    # blocks this process holds in reserve count as free; given back
    #                                             also when the check is switched off (the wide record loads next)
    if os.environ.get("FORGE_WIDE_FIT_CHECK", "1") == "0":
        return True, f"{n} positions; fit check switched off (FORGE_WIDE_FIT_CHECK=0)"
    need = n * WIDE_BYTES_PER_POSITION + WIDE_FIT_RESERVE_BYTES
    try:
        free, total = torch.cuda.mem_get_info(dev)
    except Exception as e:  # noqa: BLE001
        return True, f"{n} positions; the card's free memory could not be read ({type(e).__name__}): not checked"
    return need <= free, (f"{n} positions x {WIDE_BYTES_PER_POSITION} bytes + {WIDE_FIT_RESERVE_BYTES / 2 ** 30:.1f} GB "
                          f"reserve = {need / 2 ** 30:.2f} GB needed, {free / 2 ** 30:.2f} of {total / 2 ** 30:.2f} GB "
                          f"free on the card: {'fits' if need <= free else 'does NOT fit'}")


def _grid(p: torch.Tensor, steps: float) -> torch.Tensor:
    """The value on the engine's grid (1 / steps) in the forward pass, the plain value in the backward pass."""
    return p + (torch.round(p * steps) / steps - p).detach()


class ForgeNetV3(nn.Module):
    def __init__(self, hidden: int = 512, king_buckets: int = 8, out_buckets: int = 8, mirror: bool = True):
        super().__init__()
        self.hidden, self.king_buckets, self.out_buckets, self.mirror = hidden, king_buckets, out_buckets, mirror
        self.standalone = True
        # w1: the part of the first layer that belongs to one king bucket; fac: a part shared by all buckets
        # (the "factoriser": a piece on a square means much the same wherever the king is). The engine sees their
        # sum. Decay acts on w1 only, so what a bucket has no evidence for falls back to the shared part.
        self.w1 = nn.Parameter(torch.zeros(king_buckets, forge_v3.INPUTS, hidden))
        self.fac = nn.Parameter(torch.randn(forge_v3.INPUTS, hidden) * 0.02)
        self.b1 = nn.Parameter(torch.zeros(hidden))
        self.out = nn.Linear(2 * hidden, out_buckets)
        nn.init.normal_(self.out.weight, std=0.05 / ft.K)
        nn.init.zeros_(self.out.bias)
        self.register_buffer("king_map", torch.tensor(forge_v3.king_layout(king_buckets), dtype=torch.int64))
        self.register_buffer("output_map", torch.tensor(forge_v3.output_layout(out_buckets), dtype=torch.int64))

    def table(self) -> torch.Tensor:
        """The first-layer weights as the engine will hold them: [king_buckets * 768, hidden], on its grid."""
        return _grid((self.w1 + self.fac.unsqueeze(0)).reshape(-1, self.hidden), QA)

    def forward(self, feat, stm, hce_logit):
        fk = ft.triton_kernels()
        if feat.dtype != torch.int16:                       # 64 piece codes: make the side-to-move inputs first
            feat = fk.stm_features(feat, stm)
        idx = fk.king_bucket_rows(feat, self.king_map, self.mirror)
        h = fk.SparseRowsAct.apply(self.table().contiguous(), _grid(self.b1, QA), idx).view(feat.shape[0], 2 * self.hidden)
        o = F.linear(h, _grid(self.out.weight, QB), _grid(self.out.bias, QA * QB))
        pieces = (feat >= 0).sum(1).clamp(max=32)
        o = o.gather(1, self.output_map[pieces].unsqueeze(1)).squeeze(1)
        # o is the engine's value in units of 400 centipawns; the loss works with sigmoid(K * centipawns / 400)
        return ft.K * o + hce_logit

    @torch.no_grad()
    def project(self):
        """Keep every weight inside what the file format can hold: |w2| <= 127/64 and
        max|b1| + 32 * max|w1 + fac| <= 32767/255 (here: |w1|, |fac| <= 1.98 and |b1| <= 1.7)."""
        self.w1.clamp_(-1.98, 1.98)
        self.fac.clamp_(-1.98, 1.98)
        self.b1.clamp_(-1.7, 1.7)
        self.out.weight.clamp_(-forge_v3.MAX_W2 / QB, forge_v3.MAX_W2 / QB)
        self.out.bias.clamp_(-30.0, 30.0)


def save_model(model: ForgeNetV3, path: Path) -> None:
    tmp = path.with_name("tmp_" + path.name)
    torch.save({"arch": "v3", "hidden": model.hidden, "king_buckets": model.king_buckets,
                "out_buckets": model.out_buckets, "mirror": bool(model.mirror),
                "state": {k: v.cpu() for k, v in model.state_dict().items()}}, tmp)
    os.replace(tmp, path)


def load_model(path) -> ForgeNetV3:
    ck = torch.load(path, map_location="cpu", weights_only=True)
    if ck.get("arch") != "v3":
        raise SystemExit(f"{path} is not a v3 model")
    model = ForgeNetV3(int(ck["hidden"]), int(ck["king_buckets"]), int(ck["out_buckets"]), bool(ck["mirror"]))
    model.load_state_dict(ck["state"])
    return model


def to_file_net(model: ForgeNetV3) -> forge_v3.Net:
    """The model's weights as the integers of the net file (the same rounding as the forward pass)."""
    net = forge_v3.Net(model.hidden, model.king_buckets, model.out_buckets, model.mirror, eval_scale=400)
    with torch.no_grad():
        e = (model.w1 + model.fac.unsqueeze(0)).double()
        net.w1 = torch.round(e * QA).to(torch.int16).cpu().numpy()
        net.b1 = torch.round(model.b1.double() * QA).to(torch.int16).cpu().numpy()
        net.w2 = torch.round(model.out.weight.double() * QB).to(torch.int16).cpu().numpy()
        net.b2 = torch.round(model.out.bias.double() * QA * QB).to(torch.int32).cpu().numpy()
    return net


def lr_at(step: int, steps_per_epoch: int, cycles: list[int], a) -> float:
    """Cosine cycles: every cycle starts with warm-up steps at rising rate, then falls from --lr to
    --min-lr-frac of it at the cycle's end. cycles = the pass counts at which cycles end."""
    start = 0
    for end in cycles:
        if step < end * steps_per_epoch:
            n = (end - start) * steps_per_epoch
            k = step - start * steps_per_epoch
            if k < a.warmup_steps:
                return a.lr * (k + 1) / a.warmup_steps
            prog = (k - a.warmup_steps) / max(1, n - a.warmup_steps - 1)
            return a.lr * (a.min_lr_frac + (1 - a.min_lr_frac) * 0.5 * (1 + math.cos(math.pi * min(1.0, prog))))
        start = end
    return a.lr * a.min_lr_frac


def batch_loss_once(model, d, idx, dev, blend, teacher_p, t_weight):
    """forge_train.batch_loss for a distilled v3 training, with the teacher's values read from teacher_p (computed
    once, see cmd_train) instead of computed for every batch. The same operations in the same order otherwise."""
    codes, stm = d["feat"][idx], None
    score = d["score"][idx].to(dev)
    res = d["res"][idx].to(dev)
    hce_logit = d["hce"][idx].to(dev) * (ft.K / 400.0)
    teacher = torch.sigmoid(torch.clamp(score * (ft.K / 400.0), -40, 40))
    target = blend * teacher + (1.0 - blend) * (res + 1.0) * 0.5
    target = (1.0 - t_weight) * target + t_weight * teacher_p[idx]
    pred = torch.sigmoid(model(codes, stm, hce_logit))
    return F.mse_loss(pred, target)


def cmd_train(a) -> int:
    dev = torch.device("cuda")
    if not torch.cuda.is_available():
        raise SystemExit("the v3 trainer needs the graphics card (its first layer is a Triton kernel)")
    torch.manual_seed(a.seed)
    ft.triton_kernels()
    if a.init_model and Path(a.init_model).exists():
        model = load_model(a.init_model)
        init = a.init_model
    else:
        model = ForgeNetV3(a.hidden, a.king_buckets, a.out_buckets)
        init = "scratch"
    model.to(dev)
    t0 = time.time()
    # FORGE_COMPACT=1 (2026-11-15, card work): the window on the card as the compact 44-byte record instead of 88
    # bytes a position (ft_triton/compact_record.py). Used only after the first data file, loaded alone, gave the
    # same loss and gradients both ways on one batch, without and with stored teacher values.
    # 2026-11-16 (review of the compact record, F1 + F3): a refusal of the record (compact_record.CompactRefused)
    # at the probe OR at the full load makes the wide record load, as promised; before, it ended the training
    # (SystemExit). The wide record is loaded in place of the compact one only if it fits the card (wide_fits).
    cr = None
    compact_asked = os.environ.get("FORGE_COMPACT", "") == "1"
    tw_check = float(a.distill_weight) or 0.2       # the weight this training uses for teacher values (0: 0.2)
    if compact_asked and a.distill_net and not a.teacher_once:
        print("COMPACT RECORD: not used (a teacher without --teacher-once is computed per batch); the wide record is loaded", flush=True)
    elif compact_asked:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent / "ft_triton"))
            import compact_record
            probe = compact_record.load_compact(a.datasets[:1], a.hce_exe, not a.keep_noisy, dev, False)
            ok_a, text_a = compact_record.self_check_c(model, probe, dev, a.mix, None, 0.0, a.batch_size)
            fake_tp = torch.rand(probe["n"], device=dev, generator=torch.Generator(device=dev).manual_seed(1))
            ok_b, text_b = compact_record.self_check_c(model, probe, dev, a.mix, fake_tp, tw_check, a.batch_size)
            del probe, fake_tp
            torch.cuda.empty_cache()                    # give the probe's blocks back before the window is loaded
            print(f"COMPACT RECORD, no teacher values: {text_a}", flush=True)
            print(f"COMPACT RECORD, with teacher values: {text_b}", flush=True)
            cr = compact_record if (ok_a and ok_b) else None
        except Exception as e:  # noqa: BLE001   (CompactRefused is one of these; SystemExit is not)
            print(f"COMPACT RECORD: could not be used ({type(e).__name__}: {str(e)[:200]}); the wide record is loaded", flush=True)
            cr = None
        # 2026-11-16 (review E3): on every way out, and AFTER the except clause, where the exception and the frames
        # it held are gone: a probe that failed stayed bound (and on the card) for the whole training
        probe = fake_tp = None
        torch.cuda.empty_cache()
    d = None
    if cr is not None:
        refused = ""
        try:                    # the probe read only the first file: a later one may hold what the record cannot
            d = cr.load_compact(a.datasets, a.hce_exe, not a.keep_noisy, dev, bool(a.distill_net))
        except cr.CompactRefused as e:
            refused = f"{type(e).__name__}: {str(e)[:200]}"
        if d is not None:
            # 2026-11-16 (review of the compact record, F2.3 + F5): the probe's rows all lie in the first file. The
            # record's own check once more, its rows strided over the WHOLE window: it reaches the rows above
            # 2^26 = 67,108,864, from where the packed record lies beyond 2^31 bytes, and it checks loss_fused_c
            # there, the step that trains when STEP V2 says NOT used (before, only STEP V2's own check reached
            # those rows). It catches an addressing fault that stays inside the buffer (a wrong row, a wrong
            # stride); an offset that wraps to a negative one would more likely end the process than disagree.
            # Not agreeing is a refusal.
            fake_tp = None
            ok_w = ok_x = False
            text_w = text_x = "not run; NOT used"
            stage = "w"         # which of the two checks an exception belongs to (review E5)
            try:
                ok_w, text_w = cr.self_check_c(model, d, dev, a.mix, None, 0.0, a.batch_size)
                stage = "x"
                fake_tp = torch.rand(d["n"], device=dev, generator=torch.Generator(device=dev).manual_seed(2))
                ok_x, text_x = cr.self_check_c(model, d, dev, a.mix, fake_tp, tw_check, a.batch_size)
            except Exception as e:  # noqa: BLE001
                failed = f"check failed with {type(e).__name__}: {str(e)[:200]}; NOT used"
                if stage == "w":
                    ok_w, text_w = False, failed
                else:
                    ok_x, text_x = False, failed
            fake_tp = None      # given back on every way out, before anything else is loaded
            print(f"COMPACT RECORD, whole window, no teacher values: {text_w}", flush=True)
            print(f"COMPACT RECORD, whole window, with teacher values: {text_x}", flush=True)
            if not (ok_w and ok_x):
                refused = "the check over the whole window did not agree"
                d = None        # the record's tensors go with the last name that held them
            # on BOTH ways (review E1): the made-up values' 4 bytes a position must not stay cached and be split
            # by the hold-out that loads next (the teacher values need a block of that size later); and a refused
            # record's blocks go back before the wide record loads
            torch.cuda.empty_cache()
        if d is None:           # refused at the load (its tensors went with the exception) or by the check above
            torch.cuda.empty_cache()    # (review E2) also when the fit check, which would do it, is switched off
            cr = None
            print(f"COMPACT RECORD: could not be used ({refused}); the wide record is loaded", flush=True)
    if d is None:
        if compact_asked:       # the wide record in place of the compact one: only if it fits the card
            fits, text = wide_fits(a.datasets, a.hce_exe, not a.keep_noisy, dev)
            print(f"WIDE RECORD: {text}", flush=True)
            if not fits:
                raise SystemExit("WIDE RECORD: it does not fit the card's free memory, and the compact record is not "
                                 "used (see the COMPACT RECORD lines above); stopping. Lower [train] "
                                 "max_window_positions, or repair what the compact record refused.")
        d = ft.load_plain_to_device(a.datasets, a.hce_exe, not a.keep_noisy, dev, True)

    def pass_order(k: int) -> torch.Tensor:
        # The order of pass k (2026-11-15): drawn on the processor as int32 with a generator of its own, seeded from
        # (training seed, k), so it is a pure function of the two whatever the thread timing. The card's own randperm
        # sorts and peaks at about 48 bytes a position; this one costs the card 4 bytes a position.
        g = torch.Generator()
        g.manual_seed(a.seed * 1_000_003 + k)
        # permfix3 (2026-11-15 22:27): into ONE reused buffer. A new tensor every pass, copied to the card with
        # .to(dev), left its 4 bytes a position behind in main memory EVERY PASS on this PC (round 14's first
        # training: 23.6 GB at pass 36, ended by the memory guard; tmp/perm_leak_probe.py, tmp/make_permfix3.py).
        torch.randperm(d["n"], generator=g, out=order_buf)
        return order_buf

    order_buf = torch.empty(d["n"], dtype=torch.int32)

    # one worker draws the order of the next pass while the current one trains; the first order is drawn while the
    # teacher's values and the hold-out are computed (FORGE_ORDER_THREAD=0: every order in the main thread)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1) if os.environ.get("FORGE_ORDER_THREAD", "1") != "0" else None
    nxt = pool.submit(pass_order, 0) if pool else None
    val = ft.load_plain_to_device([a.val], a.hce_exe, True, dev, True) if a.val and Path(a.val).exists() else None
    distill = None
    if a.distill_net:                                   # a residual teacher, as in forge_train.py; or a king-bucket model (.pt with arch "v3")
        t_path = Path(a.distill_net)
        t_v3 = (t_path.suffix == ".pt"
                and torch.load(t_path, map_location="cpu", weights_only=True).get("arch") == "v3")
        if t_v3:
            t_net = load_model(t_path)                  # its forward takes the side-to-move inputs as they are on the card
        else:
            t_net = ft.load_checkpoint(t_path) if t_path.suffix == ".pt" else ft.model_from_inc(t_path)
            t_net.ft_backend = "triton"
        t_net.to(dev).eval()
        for prm in t_net.parameters():
            prm.requires_grad_(False)
        # a stand-alone teacher has no hand-written term: its value is its own output only
        if cr is None:
            d["hce_teacher"] = torch.zeros_like(d["hce"]) if t_v3 else d["hce"]
        distill = (t_net, float(a.distill_weight))
        print(f"distillation: teacher {t_path} ({'king-bucket model, no hand-written term' if t_v3 else 'residual, with the hand-written term'}), "
              f"weight {a.distill_weight}", flush=True)
    if cr is None:
        d["hce"] = torch.zeros_like(d["hce"])           # a stand-alone net: no hand-written term anywhere
    if val:
        val["hce"] = torch.zeros_like(val["hce"])
    teacher_p = None
    if distill is not None and a.teacher_once:
        # --teacher-once (2026-11-15, from the Opus session's copy exp_train_v3.py, where stored and per-batch values
        # differed by at most 6.6e-7): the teacher's value of every training position, computed once and kept on the card
        # (exact: the teacher does not change during a training), in chunks of the training batch size so that its
        # arithmetic is that of the batches; every batch then reads it instead of running the teacher again.
        t_net, t_weight = distill
        t_pre = time.time()
        teacher_p = torch.empty(d["n"], device=dev, dtype=torch.float32)
        with torch.no_grad():
            for i in range(0, d["n"], a.batch_size):
                ix = torch.arange(i, min(d["n"], i + a.batch_size), device=dev)
                if cr is not None:      # the compact record: the inputs of these rows are made for the teacher
                    t_hce = (torch.zeros(len(ix), device=dev) if t_v3 else d["hce16"][ix].float()) * (ft.K / 400.0)
                    teacher_p[i:i + len(ix)] = torch.sigmoid(t_net(cr.unpack_feat(d, ix), None, t_hce))
                else:
                    t_hce = d["hce_teacher"][ix].to(dev) * (ft.K / 400.0)
                    teacher_p[i:i + len(ix)] = torch.sigmoid(t_net(d["feat"][ix], None, t_hce))
        print(f"teacher values computed once: {d['n']} positions in {time.time() - t_pre:.1f} s, "
              f"{teacher_p.numel() * 4 / 2 ** 30:.2f} GB on the card", flush=True)
    if cr is not None:
        cr.free_teacher_inputs(d)                       # the hand-written value was only for the teacher
        torch.cuda.empty_cache()                        # and its block goes back before the pass order is made
    steps_per_epoch = max(1, d["n"] // a.batch_size)
    if a.lr_cycles.strip().lower() == "auto":      # the recipe's cycle ends at 15, 30, 60 and 100 % of the passes
        cycles = sorted({max(1, round(a.epochs * f)) for f in (0.15, 0.3, 0.6, 1.0)})
    else:
        cycles = [int(x) for x in a.lr_cycles.split(",") if x.strip()] if a.lr_cycles else [a.epochs]
    if cycles[-1] != a.epochs or sorted(cycles) != cycles:
        raise SystemExit(f"--lr-cycles {a.lr_cycles} must rise and end at --epochs {a.epochs}")
    n_sample = min(d["n"], 2_000_000)
    # torch.randperm on the card sorts and peaks at about 48 bytes a position (2026-11-15): the sample rows are drawn on
    # the processor (int32) and only the 2 million chosen ones go to the card
    # .clone(): only the chosen rows are copied to the card, not a view of the whole order (permfix3)
    sample = torch.randperm(d["n"], generator=torch.Generator().manual_seed(12345), dtype=torch.int32)[:n_sample].clone().to(dev).long()
    print(f"v3 net: hidden {model.hidden}, {model.king_buckets} mirrored king buckets, {model.out_buckets} output buckets; "
          f"init {init}; {d['n']} train positions, {val['n'] if val else 0} hold-out positions, data ready in "
          f"{time.time() - t0:.0f} s; batch {a.batch_size}, rate {a.lr} in cycles ending at passes {cycles}, "
          f"decay {a.w1_decay} on the king-bucketed weights, target mix {a.mix} score + {1 - a.mix:.2f} result", flush=True)

    # the compact record: the two million train-sample rows are kept once in the wide form for this loss (made
    # 65,536 rows at a time by cr.wide_rows, and the blocks of the making given back: review F4)
    sample_wide = cr.wide_rows(d, sample, dev) if cr is not None else None
    if cr is not None:
        torch.cuda.empty_cache()
        print(f"COMPACT RECORD in use: {d['n']} positions, {sum(v.numel() * v.element_size() for v in d.values() if torch.is_tensor(v)) / 2 ** 30:.2f} GB "
              f"on the card for the window (+ teacher values and the pass order, 4 bytes a position each)", flush=True)

    @torch.no_grad()
    def sample_loss() -> float:
        model.eval()
        tot = 0.0
        for i in range(0, n_sample, 65536):
            if sample_wide is not None:
                ix = torch.arange(i, min(n_sample, i + 65536), device=dev)
                tot += float(ft.batch_loss(model, sample_wide, ix, dev, a.mix)) * len(ix)
            else:
                ix = sample[i:i + 65536]
                tot += float(ft.batch_loss(model, d, ix, dev, a.mix)) * len(ix)
        return tot / n_sample

    if val:
        print(f"hold-out loss before training: {ft.dataset_loss(model, val, dev, 65536, a.mix):.6f}", flush=True)
    fused = None
    if cr is None and os.environ.get("FORGE_FUSED_STEP", "") == "1":
        # 2026-11-15, speed jobs K7 + K3 (pipeline/ft_triton/fused_step.py): the batch by one kernel, the dense end and
        # the loss by two. Used only after one batch gave the same loss and gradients both ways.
        if distill is not None and teacher_p is None:
            print("FUSED STEP: not used (a teacher without --teacher-once is computed per batch)", flush=True)
        else:
            try:
                sys.path.insert(0, str(Path(__file__).resolve().parent / "ft_triton"))
                import fused_step
                ok_f, text_f = fused_step.self_check(model, d, dev, a.mix, teacher_p,
                                                     distill[1] if distill is not None else 0.0, a.batch_size)
            except Exception as e:  # noqa: BLE001
                ok_f, text_f = False, f"could not be loaded ({type(e).__name__}: {str(e)[:200]}); the old step trains"
            print(f"FUSED STEP: {text_f}", flush=True)
            fused = fused_step if ok_f else None
    opt = torch.optim.Adam(model.parameters(), lr=a.lr, fused=True)
    # FORGE_STEP_V2=1 (2026-11-15, card work): the whole step (batch, forward, loss, gradients, Adam, decay, clamps,
    # next table) by pipeline/ft_triton/step_v2.py without autograd. Used only after three steps on copies of the
    # model gave the same weights both ways; otherwise the step above trains.
    stepper = None
    if os.environ.get("FORGE_STEP_V2", "") == "1":
        if distill is not None and teacher_p is None:
            print("STEP V2: not used (a teacher without --teacher-once is computed per batch)", flush=True)
        else:
            t_w = distill[1] if distill is not None else 0.0
            try:
                sys.path.insert(0, str(Path(__file__).resolve().parent / "ft_triton"))
                import step_v2
                ok_s, text_s = step_v2.self_check(model, d, dev, a.mix, teacher_p, t_w, a.w1_decay, a.batch_size, a.lr)
                if ok_s:
                    stepper = step_v2.StepperV2(model, d, teacher_p, a.mix, t_w, a.w1_decay)
            except Exception as e:  # noqa: BLE001
                ok_s, text_s, stepper = False, f"could not be used ({type(e).__name__}: {str(e)[:200]})", None
            print(f"STEP V2: {text_s}", flush=True)
    guard = ft.GpuHeatGuard(a.gpu_hot_pause_c, a.gpu_hot_resume_c)
    ram = ft.RamGuard(float(os.environ.get("FORGE_MIN_FREE_RAM_GB", "1.5") or 0))
    step = 0
    t1 = time.time()
    lr = a.lr
    perm = None
    for ep in range(a.epochs):
        model.train()
        order = None
        if pool:
            try:
                order = nxt.result()
            except Exception as e:  # noqa: BLE001
                print(f"order thread failed for pass {ep + 1} ({type(e).__name__}: {e}); drawn in the main thread", flush=True)
        if order is None:
            order = pass_order(ep)
        if os.environ.get("FORGE_ORDER_CHECK") == "1":         # tests only: the order of every pass as a checksum
            import hashlib
            print(f"ORDER pass {ep + 1} sha256 {hashlib.sha256(order.numpy().tobytes()).hexdigest()[:16]}", flush=True)
        if perm is None:
            perm = torch.empty(d["n"], dtype=torch.int32, device=dev)
        perm.copy_(order)                # the buffer is free again after this line (the copy waits for its end)
        del order
        if pool:                         # only now may the worker fill the buffer with the next pass's order
            nxt = pool.submit(pass_order, ep + 1) if ep + 1 < a.epochs else None
        run, cnt = 0.0, 0
        for bi in range(steps_per_epoch):
            idx = perm[bi * a.batch_size:(bi + 1) * a.batch_size]
            if fused is None and cr is None and stepper is None:
                idx = idx.long()
            lr = lr_at(step, steps_per_epoch, cycles, a)
            if stepper is not None:
                lv = stepper.step(idx, lr, bi % 20 == 0)
                step += 1
                if bi % 20 == 0:
                    run += float(lv)
                    cnt += 1
                    guard.tick()
                    ram.tick()
                continue
            for g in opt.param_groups:
                g["lr"] = lr
            if cr is not None:
                loss = cr.loss_fused_c(model, d, idx, dev, a.mix, teacher_p, distill[1] if distill is not None else 0.0)
            elif fused is not None:
                loss = fused.batch_loss_fused2(model, d, idx, dev, a.mix, teacher_p,
                                               distill[1] if distill is not None else 0.0)
            elif teacher_p is not None:
                loss = batch_loss_once(model, d, idx, dev, a.mix, teacher_p, distill[1])
            else:
                loss = ft.batch_loss(model, d, idx, dev, a.mix, distill)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            with torch.no_grad():
                if a.w1_decay > 0:
                    model.w1.mul_(1.0 - lr * a.w1_decay)     # decoupled decay, on the king-bucketed part only
            model.project()
            step += 1
            if bi % 20 == 0:
                run += float(loss.detach())
                cnt += 1
                guard.tick()
                ram.tick()
        if stepper is not None:
            stepper.sync_to_model()          # the three small tensors back into the model before anything reads it
            # step v2 keeps Adam's moments itself; a NaN there pins a weight for the rest of the training and
            # shows in neither the loss nor (before 2026-11-16) the weights: look at all of its tensors once a pass
            bad = stepper.not_finite()
            if bad:
                raise SystemExit(f"not finite after pass {ep + 1} (step v2): {', '.join(bad)}; stopping")
        # a NaN in a weight is invisible to the first layer's kernel (the card's min / max turn it into 0), so the
        # loss stays finite; look at the weights themselves once a pass (review of 2026-11-15, F3)
        if not all(bool(torch.isfinite(p_).all()) for p_ in model.parameters()):
            raise SystemExit(f"a weight is not finite after pass {ep + 1}; stopping")
        tl = run / max(1, cnt)
        if not math.isfinite(tl):
            raise SystemExit("training loss is not finite; stopping")
        print(f"LOSS {tl:.6f}  epoch {ep + 1}/{a.epochs} lr {lr:.2e} "
              f"{(ep + 1) * steps_per_epoch * a.batch_size / max(1e-9, time.time() - t1 - guard.paused_s):,.0f} pos/s", flush=True)
        if (ep + 1) in cycles or a.fit_every and (ep + 1) % a.fit_every == 0:
            ho = ft.dataset_loss(model, val, dev, 65536, a.mix) if val else float("nan")
            print(f"FIT epoch {ep + 1}: train-sample {sample_loss():.6f}, hold-out {ho:.6f}", flush=True)
            if a.save_cycles and (ep + 1) in cycles and (ep + 1) != a.epochs:
                out = Path(a.out_model)
                save_model(model, out.with_name(f"{out.stem}_e{ep + 1}{out.suffix}"))
    if pool:
        pool.shutdown(wait=True)
    if guard.max_seen is not None:
        print(f"GPU hottest sensor during training: {guard.max_seen:.0f} C, cooling pauses: {guard.pauses}", flush=True)
    if val:
        print(f"VAL {ft.dataset_loss(model, val, dev, 65536, a.mix):.6f}", flush=True)
        # the same hold-out with the 0.6 mix of forge_train.py's VAL lines, so one table can hold both kinds of net
        print(f"VAL_MIX60 {ft.dataset_loss(model, val, dev, 65536, 0.6):.6f}", flush=True)
    save_model(model, Path(a.out_model))
    print(f"saved {a.out_model}", flush=True)
    return 0


def cmd_score(a) -> int:
    """Hold-out losses of a finished model at the 0.6 mix of forge_train.py: quiet positions (as VAL there) and
    with capture and promotion positions kept (as VAL_WITH_CAPTURES there)."""
    dev = torch.device("cuda")
    ft.triton_kernels()
    model = load_model(a.model).to(dev).eval()
    for name, skip_noisy in (("VAL_MIX60", True), ("VAL_WITH_CAPTURES_MIX60", False)):
        v = ft.load_plain_to_device([a.val], a.hce_exe, skip_noisy, dev, True)
        v["hce"] = torch.zeros_like(v["hce"])
        print(f"{name} {ft.dataset_loss(model, v, dev, 65536, 0.6):.6f} ({v['n']} positions)", flush=True)
    return 0


def cmd_export(a) -> int:
    model = load_model(a.model)
    net = to_file_net(model)
    checksum = forge_v3.write_net(a.net, net)
    print(f"exported {a.net}: hidden {net.hidden}, max|w1| {int(np.abs(net.w1).max())}, max|b1| {int(np.abs(net.b1).max())}, "
          f"max|w2| {int(np.abs(net.w2).max())}, checksum {checksum:016x}", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train")
    t.add_argument("--datasets", nargs="+", required=True)
    t.add_argument("--val", default="")
    t.add_argument("--init-model", default="")
    t.add_argument("--out-model", required=True)
    t.add_argument("--hce-exe", required=True)
    t.add_argument("--hidden", type=int, default=512)
    t.add_argument("--king-buckets", type=int, default=8)
    t.add_argument("--out-buckets", type=int, default=8)
    t.add_argument("--keep-noisy", action="store_true")
    t.add_argument("--epochs", type=int, default=40)
    t.add_argument("--batch-size", type=int, default=8192)
    t.add_argument("--lr", type=float, default=5e-4)
    t.add_argument("--min-lr-frac", type=float, default=0.05)
    t.add_argument("--warmup-steps", type=int, default=500)
    t.add_argument("--lr-cycles", default="", help="pass counts at which a cosine cycle ends, e.g. 6,12,24,40")
    t.add_argument("--w1-decay", type=float, default=0.3)
    t.add_argument("--mix", type=float, default=0.75, help="share of the search score in the target (rest: game result)")
    t.add_argument("--fit-every", type=int, default=0, help="also print the FIT line every N passes")
    t.add_argument("--save-cycles", action="store_true", help="save a model at the end of every cycle")
    t.add_argument("--distill-net", default="")
    t.add_argument("--distill-weight", type=float, default=0.2)
    t.add_argument("--teacher-once", action="store_true",
                   help="compute the teacher's values once per position instead of once per batch (exact, 25 to 40 %% faster)")
    t.add_argument("--seed", type=int, default=1)
    t.add_argument("--gpu-hot-pause-c", type=float, default=100.0)
    t.add_argument("--gpu-hot-resume-c", type=float, default=80.0)
    e = sub.add_parser("export")
    e.add_argument("--model", required=True)
    e.add_argument("--net", required=True)
    sc = sub.add_parser("score")
    sc.add_argument("--model", required=True)
    sc.add_argument("--val", required=True)
    sc.add_argument("--hce-exe", required=True)
    a = ap.parse_args()
    return {"train": cmd_train, "export": cmd_export, "score": cmd_score}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
