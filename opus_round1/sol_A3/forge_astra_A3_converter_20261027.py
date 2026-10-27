#!/usr/bin/env python3
"""Forge full-NNUE converter (Astra A3, 2026-10-27): trainer checkpoint (.pt) -> engine net file "FORGEFN1" (.fnn).

usage:
  forge_astra_A3_converter_20261027.py convert <epoch.pt> <out.fnn>
  forge_astra_A3_converter_20261027.py info <net.fnn>

File format FORGEFN1, version 1, little-endian (spec: forge_astra_A3_fullnnue_spec_20261027.md section 3):
  off  type         field
  0    char[8]      magic "FORGEFN1"
  8    u32          version = 1
  12   u32          header_bytes = 256
  16   u32          inputs per king block = 768
  20   u32          H  feature-transformer width (multiple of 16)
  24   u32          KB king blocks (1..64)
  28   u32          flags: bit0 = king mirror (files e-h fold onto d-a); other bits 0
  32   u32          OB output buckets (1..16)
  36   u32          L1 first hidden width (multiple of 16)
  40   u32          L2 second hidden width (0 = one hidden layer, else multiple of 16)
  44   u32          ft activation = 1 (SCReLU: clamp(x, 0, 1)^2)
  48   u32          hidden activation = 1 (CReLU: clamp(x, 0, 1))
  52   f32          ft scale = 4096 (stored int16 / 4096 = weight)
  56   f32          sigmoid K = 2.25 (output in sigmoid units; cp = out * 400 / K)
  60   u8[64]       king map: own-king square in the perspective frame (rank-flipped for Black) -> block
  124  u8[33]       output map: piece count 0..32 (kings included) -> output bucket
  157  u8[99]       reserved, zero
  256  i16          ft_w[KB][768][H]   (feature-major: one H-column per feature, as the lock's w1)
       i16          ft_b[H]
       f32          l1_w[OB][L1][2H]   (inputs 0..H-1 = side to move, H..2H-1 = the other side)
       f32          l1_b[OB][L1]
       f32          l2_w[OB][L2][L1], l2_b[OB][L2]       (only when L2 > 0)
       f32          out_w[OB][L2 or L1], out_b[OB]
  end  u64          FNV-1a 64 of every preceding byte
The int16 values are exactly the integers the trainer's QAT forward uses (round half away from zero of
(block + factor) * 4096, clamped to +-32767); the float32 blocks are the checkpoint's tensors bit for bit.
No timestamps or paths are written, so the same checkpoint always gives the same bytes.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np

MAGIC = b"FORGEFN1"
VERSION = 1
HEADER_BYTES = 256
INPUTS = 768
FLAG_MIRROR = 1
ACT_SCRELU = 1
ACT_CRELU = 1
FT_SCALE = 4096.0
SIGMOID_K = 2.25
QMAX = 32767


def fnv1a64(data: bytes) -> int:
    """FNV-1a 64 (offset 0xcbf29ce484222325, prime 0x100000001b3), byte by byte (about 1 s per 2 MB)."""
    h = 0xcbf29ce484222325
    prime = 0x100000001b3
    mask = 0xFFFFFFFFFFFFFFFF
    for b in data:
        h = ((h ^ b) * prime) & mask
    return h


def header_bytes(hidden, kb, mirror, ob, l1, l2, king_map, output_map) -> bytes:
    head = MAGIC + struct.pack("<IIIIIIIIIIIff", VERSION, HEADER_BYTES, INPUTS, hidden, kb,
                               FLAG_MIRROR if mirror else 0, ob, l1, l2, ACT_SCRELU, ACT_CRELU, FT_SCALE, SIGMOID_K)
    if len(king_map) != 64 or any(not 0 <= b < kb for b in king_map):
        raise ValueError("king map needs 64 entries in [0, KB)")
    if len(output_map) != 33 or any(not 0 <= b < ob for b in output_map):
        raise ValueError("output map needs 33 entries in [0, OB)")
    head += bytes(king_map) + bytes(output_map)
    head += bytes(HEADER_BYTES - len(head))
    assert len(head) == HEADER_BYTES
    return head


def write_fnn(path, *, hidden, kb, mirror, ob, l1, l2, king_map, output_map, ft_w, ft_b, l1_w, l1_b, l2_w, l2_b,
              out_w, out_b) -> int:
    """ft_w int16 [KB, 768, H], ft_b int16 [H]; dense blocks float32 in the shapes of the module docstring."""
    def i16(a, shape):
        a = np.asarray(a)
        if a.dtype != np.int16 or a.shape != shape:
            raise ValueError(f"int16 block {a.dtype} {a.shape}, expected {shape}")
        return a.astype("<i2").tobytes()

    def f32(a, shape):
        a = np.asarray(a)
        if a.dtype != np.float32 or a.shape != shape or not np.isfinite(a).all():
            raise ValueError(f"float32 block {a.dtype} {a.shape}, expected finite {shape}")
        return a.astype("<f4").tobytes()

    lk = l2 if l2 else l1
    body = [header_bytes(hidden, kb, mirror, ob, l1, l2, king_map, output_map),
            i16(ft_w, (kb, INPUTS, hidden)), i16(ft_b, (hidden,)),
            f32(l1_w, (ob, l1, 2 * hidden)), f32(l1_b, (ob, l1))]
    if l2:
        body += [f32(l2_w, (ob, l2, l1)), f32(l2_b, (ob, l2))]
    body += [f32(out_w, (ob, lk)), f32(out_b, (ob,))]
    data = b"".join(body)
    checksum = fnv1a64(data)
    Path(path).write_bytes(data + struct.pack("<Q", checksum))
    return checksum


def quant_int16(t):
    """The integers of the trainer's quantise() for a float32 torch tensor: round half away from zero of t * 4096,
    clamped to +-32767 (same torch float32 operations, so the same values)."""
    import torch
    s = t.detach().float() * FT_SCALE
    r = torch.clamp(torch.sign(s) * torch.floor(torch.abs(s) + 0.5), -QMAX, QMAX)
    return r.numpy().astype(np.int16)


def convert(pt_path, out_path) -> dict:
    import torch
    ck = torch.load(pt_path, map_location="cpu", weights_only=True)
    cfg, sd = ck["config"], ck["model"]
    if cfg.get("format") != "FN1":
        raise ValueError(f"{pt_path}: not an FN1 checkpoint (config format {cfg.get('format')!r})")
    if not cfg.get("qat", True):
        raise ValueError("a checkpoint trained without QAT cannot be exported exactly")
    hidden, l1, l2, kb, ob = cfg["hidden"], cfg["l1"], cfg["l2"], cfg["king_blocks"], cfg["output_buckets"]
    folded = sd["ft_w"] + sd["ft_f"].unsqueeze(0) if cfg["factor"] else sd["ft_w"]      # [KB, H, 768] float32
    ft_w = np.ascontiguousarray(quant_int16(folded).transpose(0, 2, 1))                  # [KB, 768, H]
    ft_b = quant_int16(sd["ft_b"])
    l1_w = sd["fc1.weight"].numpy().reshape(ob, l1, 2 * hidden)
    l1_b = sd["fc1.bias"].numpy().reshape(ob, l1)
    if l2:
        l2_w = sd["fc2.weight"].numpy().reshape(ob, l2, l1)
        l2_b = sd["fc2.bias"].numpy().reshape(ob, l2)
    else:
        l2_w = l2_b = None
    out_w = sd["out.weight"].numpy().reshape(ob, l2 if l2 else l1)
    out_b = sd["out.bias"].numpy().reshape(ob)
    checksum = write_fnn(out_path, hidden=hidden, kb=kb, mirror=cfg["king_mirror"], ob=ob, l1=l1, l2=l2,
                         king_map=cfg["king_map"], output_map=cfg["output_map"], ft_w=ft_w, ft_b=ft_b, l1_w=l1_w,
                         l1_b=l1_b, l2_w=l2_w, l2_b=l2_b, out_w=out_w, out_b=out_b)
    return {"checksum": checksum, "hidden": hidden, "king_blocks": kb, "output_buckets": ob, "l1": l1, "l2": l2,
            "bytes": Path(out_path).stat().st_size}


def info(path) -> str:
    data = Path(path).read_bytes()
    if data[:8] != MAGIC:
        raise ValueError("not a FORGEFN1 file")
    f = struct.unpack_from("<IIIIIIIIIIIff", data, 8)
    version, hb, inputs, hidden, kb, flags, ob, l1, l2, act_ft, act_h, scale, k = f
    stored = struct.unpack_from("<Q", data, len(data) - 8)[0]
    ok = fnv1a64(data[:-8]) == stored
    return (f"FORGEFN1 v{version} header {hb} inputs {inputs} H {hidden} king blocks {kb} mirror {bool(flags & 1)} "
            f"output buckets {ob} L1 {l1} L2 {l2} act {act_ft}/{act_h} scale {scale:g} K {k:g} "
            f"bytes {len(data)} fnv1a {stored:016x} checksum {'OK' if ok else 'BAD'}")


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 3 and argv[0] == "convert":
        r = convert(argv[1], argv[2])
        print(f"wrote {argv[2]}: {r['bytes']} bytes, H {r['hidden']}, king blocks {r['king_blocks']}, output buckets "
              f"{r['output_buckets']}, L1 {r['l1']}, L2 {r['l2']}, fnv1a {r['checksum']:016x}")
        print(info(argv[2]))
        return 0
    if len(argv) == 2 and argv[0] == "info":
        print(info(argv[1]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
