"""The training window on the card as the COMPACT record: 44 bytes a position instead of 88 (card work, 2026-11-15).

The record and its loader are the Opus session's (pipeline/experiments/exp_train_v3c.py, job 16 d; its proofs:
every input of 2.6 million rows identical to the wide record's, the teacher's values bit-identical, a short
training equal to the old one within run-to-run noise, model check PASS). This module is the same record for the
loop's trainer, with the batch kernel batch_kernel_c.make_batch_c reading it directly, so the inputs of a batch
never exist as a tensor and no launch is spent on unpacking (Opus's copy lost 12 % of its speed there).

    d = load_compact(paths, hce_exe, skip_noisy, dev)
        packed  uint8 [N, 32]   64 four-bit piece codes of the board (square 2j low half of byte j, 2j + 1 high half)
        stm     uint8 [N]       0 = white to move
        score16 int16 [N], res8 int8 [N]
        hce16   int16 [N]       the hand-written value, needed ONLY to compute a residual teacher's values:
                                delete it afterwards (free_teacher_inputs)
        what the record cannot hold exactly, or a chunk that does not read back equal to the file's arrays, is
        refused with CompactRefused (a ValueError); the trainer then loads the wide record instead
    unpack_feat(d, idx)         the wide inputs (int16 [B, 32]) of some rows, by the old loader's own kernel:
                                for the teacher's values, the train-sample rows and the self-check
    wide_rows(d, idx, dev)      a dict in the WIDE form for some rows (feat, score, res, hce = 0, n), made
                                WIDE_ROWS_CHUNK rows at a time
    loss_fused_c(model, d, idx, dev, blend, teacher_p, t_weight)
                                the training loss of a batch: make_batch_c, first layer, dense kernels
                                (the compact twin of fused_step.batch_loss_fused2)
    self_check_c(...)           one batch through forge_train_v3.batch_loss_once on the unpacked rows and through
                                loss_fused_c: loss and every gradient compared; the trainer uses the compact path
                                only when it passes

Bytes a position on the card: 32 + 1 + 2 + 1 = 36, + the stored teacher value 4, + the pass order 4 = 44
(the wide record: 64 + 12 + 4 + 4 + 4 = 88).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import forge_train as ft  # noqa: E402
import forge_train_v3 as v3  # noqa: E402

fk = ft.triton_kernels()
import batch_kernel_c as bc  # noqa: E402  (same folder)
import dense_kernels as dk  # noqa: E402

# Rows at a time (2026-11-16): load_compact moves and packs a file's piece codes LOAD_CHUNK positions at a time (as
# before), and wide_rows makes the wide inputs WIDE_ROWS_CHUNK rows at a time (review of the compact record, F4:
# one stm_features call on the trainer's two million train-sample rows held about 7 GB of int64 temporaries).
LOAD_CHUNK = 500_000
WIDE_ROWS_CHUNK = 65_536


class CompactRefused(ValueError):
    """The compact record cannot hold these data exactly, or what was written did not read back equal to the
    file's arrays. The trainer catches this class at the probe and at the full load and loads the wide record
    instead. Until 2026-11-16 every refusal was a SystemExit, which the trainer's `except Exception` does not
    catch, so a refusal ended the training (review of the compact record, F1)."""


def load_compact(paths: list[str], hce_exe: str, skip_noisy: bool, dev, with_hce: bool = True) -> dict:
    """One file at a time in main memory, as the old loader. Refuses what the record cannot hold exactly, by
    CompactRefused. What is written is read back at once (the piece codes chunk by chunk, the rest file by
    file): the unpacked piece codes, the side to move, the score, the result and (with_hce) the hand-written value
    must equal the file's arrays exactly, or the file is refused the same way (2026-11-16, review F2: the
    trainer's own checks compare the record only with itself, so a fault in the packing or in a conversion would
    pass them).
    with_hce=False: the hand-written value is not put on the card at all (no teacher will read it)."""
    counts = [ft._count_one(p, hce_exe, skip_noisy, True) for p in paths]
    total = int(sum(counts))
    if total == 0:
        raise CompactRefused("no usable positions in " + ", ".join(paths))
    out = {"packed": torch.empty(total, 32, dtype=torch.uint8, device=dev),
           "stm": torch.empty(total, dtype=torch.uint8, device=dev),
           "score16": torch.empty(total, dtype=torch.int16, device=dev),
           "res8": torch.empty(total, dtype=torch.int8, device=dev)}
    if with_hce:
        out["hce16"] = torch.empty(total, dtype=torch.int16, device=dev)
    at = 0
    for p, n in zip(paths, counts):
        part = ft._load_one(p, hce_exe, skip_noisy, True)
        if int(part["stm"].shape[0]) != n:
            raise CompactRefused(f"{p}: {int(part['stm'].shape[0])} positions read, {n} counted; the file changed while loading")
        if n == 0:                      # a cached file without a usable position: nothing to write (and max() of
            del part                    # nothing would fail)
            continue
        for k in (("score", "hce") if with_hce else ("score",)):
            v = part[k]
            if not bool(torch.all(v == torch.round(v))) or float(v.abs().max()) > 32767:
                raise CompactRefused(f"{p}: {k} is not an integer within int16; the compact record cannot hold it")
        if not bool(torch.all((part["res"] == -1) | (part["res"] == 0) | (part["res"] == 1))):
            raise CompactRefused(f"{p}: a result outside -1, 0, 1")
        if not bool(torch.all((part["stm"] == 0) | (part["stm"] == 1))):
            raise CompactRefused(f"{p}: a side to move outside 0, 1")
        for i in range(0, n, LOAD_CHUNK):
            c = part["codes"][i:i + LOAD_CHUNK].to(dev)
            if int(c.max()) > 12:
                raise CompactRefused(f"{p}: a piece code above 12")
            if int((c != 0).sum(1).max()) > 32:
                raise CompactRefused(f"{p}: a position with more than 32 pieces")
            rows = slice(at + i, at + i + int(c.shape[0]))
            out["packed"][rows] = bc.pack_codes(c)
            if not torch.equal(_unpack_codes(out["packed"][rows]).to(torch.int16), c.to(torch.int16)):
                raise CompactRefused(f"{p}: the piece codes of rows {i} to {i + int(c.shape[0]) - 1} do not read "
                                     f"back equal from the compact record")
            del c
        out["stm"][at:at + n] = part["stm"].to(torch.uint8).to(dev)
        out["score16"][at:at + n] = part["score"].to(torch.int16).to(dev)
        out["res8"][at:at + n] = part["res"].to(torch.int8).to(dev)
        if with_hce:
            out["hce16"][at:at + n] = part["hce"].to(torch.int16).to(dev)
        # what was written, read back as numbers and compared with the file's own arrays on the processor (the
        # written values are copied back from the card; the file's arrays do not go to the card a second time)
        for k, key in (("stm", "stm"), ("score", "score16"), ("res", "res8")) + ((("hce", "hce16"),) if with_hce else ()):
            if not torch.equal(out[key][at:at + n].cpu().to(part[k].dtype), part[k]):
                raise CompactRefused(f"{p}: {k} does not read back equal from the compact record")
        at += n
        del part
    out["n"] = total
    return out


def free_teacher_inputs(d: dict) -> None:
    """The hand-written value is only read while a residual teacher's values are computed."""
    d.pop("hce16", None)


def _unpack_codes(pk: torch.Tensor) -> torch.Tensor:
    """uint8 [n, 32] -> the 64 piece codes uint8 [n, 64]: the inverse of batch_kernel_c.pack_codes."""
    return torch.stack((pk & 15, pk >> 4), dim=2).view(pk.shape[0], 64)


def unpack_feat(d: dict, idx: torch.Tensor) -> torch.Tensor:
    """The wide inputs (int16 [B, 32]) of the rows idx, made by the old loader's kernel from the four-bit board."""
    pk = d["packed"][idx.long()]
    return fk.stm_features(_unpack_codes(pk), d["stm"][idx.long()])


def wide_rows(d: dict, idx: torch.Tensor, dev, chunk: int = WIDE_ROWS_CHUNK) -> dict:
    """Some rows in the wide form the old functions read (ft.batch_loss, batch_loss_once): a stand-alone net has
    no hand-written term, so hce is zero as in the loop's trainer. The inputs are made `chunk` rows at a time
    into a tensor made beforehand (2026-11-16, review F4); stm_features works row by row, so the values are
    those of one call over all rows."""
    ix = idx.long()
    n = int(ix.shape[0])
    feat = torch.empty(n, 32, dtype=torch.int16, device=dev)
    for i in range(0, n, chunk):
        feat[i:i + chunk] = unpack_feat(d, ix[i:i + chunk])
    return {"n": n, "feat": feat, "score": d["score16"][ix].float(),
            "res": d["res8"][ix].float(), "hce": torch.zeros(n, device=dev)}


def loss_fused_c(model, d: dict, idx: torch.Tensor, dev, blend: float, teacher_p, t_weight: float, root: bool = True):
    rows, target, hce_logit, bucket = bc.make_batch_c(
        idx, d["packed"], d["stm"], d["score16"], d["res8"], teacher_p, model.king_map, model.output_map, model.mirror,
        ft.K / 400.0, blend, t_weight)
    h = fk.SparseRowsAct.apply(model.table().contiguous(), v3._grid(model.b1, v3.QA), rows)
    h = h.view(idx.shape[0], 2 * model.hidden)
    return dk.DenseBucketLoss.apply(h, v3._grid(model.out.weight, v3.QB), v3._grid(model.out.bias, v3.QA * v3.QB),
                                    bucket, hce_logit, target, float(ft.K), bool(model.training), bool(root))


def self_check_c(model, d: dict, dev, blend: float, teacher_p, t_weight: float, batch: int):
    """One batch through the trainer's old step on the UNPACKED rows and through loss_fused_c on the compact
    record. Returns (ok, one line of text)."""
    was = model.training
    model.train()
    n = int(d["n"])
    size = min(int(batch), n)
    idx = (torch.arange(size, device=dev, dtype=torch.int64) * max(1, n // size)).to(torch.int32).contiguous()

    def grads(fn):
        for p in model.parameters():
            p.grad = None
        loss = fn()
        loss.backward()
        return float(loss.detach()), [p.grad.detach().clone() for p in model.parameters()]

    try:
        wide = wide_rows(d, idx, dev)
        local = torch.arange(size, device=dev)
        tp_local = teacher_p[idx.long()] if teacher_p is not None else None
        if tp_local is not None:
            old = grads(lambda: v3.batch_loss_once(model, wide, local, dev, blend, tp_local, t_weight))
        else:
            old = grads(lambda: ft.batch_loss(model, wide, local, dev, blend, None))
        new = grads(lambda: loss_fused_c(model, d, idx, dev, blend, teacher_p, t_weight))
    except Exception as e:  # noqa: BLE001
        for p in model.parameters():
            p.grad = None
        model.train(was)
        return False, f"check failed with {type(e).__name__}: {str(e)[:200]}; NOT used"
    for p in model.parameters():
        p.grad = None
    model.train(was)
    rel = abs(new[0] - old[0]) / max(abs(old[0]), 1e-12)
    worst = max(float((a - b).abs().max()) / (float(a.abs().max()) or 1.0) for a, b in zip(old[1], new[1]))
    # Python's max() keeps its current value when the next one is NaN (review of 2026-11-15, F1): every gradient
    # must be finite, or the check fails.
    finite = all(bool(torch.isfinite(g_).all()) for g_ in old[1] + new[1])
    ok = finite and math.isfinite(new[0]) and math.isfinite(worst) and rel <= 1e-6 and worst <= 2e-5
    return ok, (f"one batch of {size} both ways (wide rows, old step / compact record, fused step): loss {old[0]:.9f} / "
                f"{new[0]:.9f} (relative difference {rel:.1e}), largest gradient difference {worst:.1e} of the largest "
                f"value: {'USED' if ok else 'NOT used'}")
