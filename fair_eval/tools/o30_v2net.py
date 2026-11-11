#!/usr/bin/env python3
"""o30_v2net.py - Opus 30-h job: read / write Forge v2 net files (FORGENN2, feature set 0) and build v2 nets from the
lock's compiled-in net (own code; numpy only).

usage:
  python -I -B o30_v2net.py from-lock <nnue_weights.inc> <out.nnue2> [--kb-map one|rank4] [--ob N] [--stand-alone]
      Writes the lock net as a v2 file: w1 copied into every king bucket, w2 / b2 into every output bucket. With an
      unmirrored king map this is the SAME function as the lock net (the engine's v2 path must reproduce the lock's
      evals and bench node counts exactly) - the warm start for fine-tuning and the port's identity test.
  python -I -B o30_v2net.py info <file.nnue2>
      Prints the header, checks size and FNV-1a checksum (exit 1 on any problem).
  python -I -B o30_v2net.py random <out.nnue2> --seed S [--kb-map ...] [--ob N] [--mirror] [--stand-alone]
      A seeded random net for parity tests (weights in a range that keeps accumulators inside SCReLU's [0, 1] often).

Format (see the engine's include/forge/nnue_v2.hpp): 160-byte header, i16 w1[kb][768][H], b1[H], w2[ob][2H], b2[ob],
u64 FNV-1a 64 of every preceding byte. Scales 4096 / 4096, sigmoid K 2.25. Flags: bit0 residual, bit1 mirror.
Never overwrites an existing output file.
"""
import argparse
import os
import re
import struct
import sys

import numpy as np

MAGIC = b'FORGENN2'
HEADER = 160
INPUTS = 768
FLAG_RESIDUAL = 1
FLAG_MIRROR = 2


def fnv1a64_fast(data):
    """FNV-1a 64 over bytes (plain loop; ~1 s per 1.5 MB)."""
    h = 0xcbf29ce484222325
    prime = 0x100000001b3
    mask = 0xFFFFFFFFFFFFFFFF
    for b in bytes(data):
        h = ((h ^ b) * prime) & mask
    return h


KING_MAPS = ('one', 'rank4', 'rank4x2', 'rank4x4', 'rank4x8')


def king_map(name):
    """64 bucket ids indexed by the king square seen from the perspective (a1 = 0; files are not flipped)."""
    rank4 = lambda r: 0 if r == 0 else 1 if r == 1 else 2 if r <= 3 else 3
    if name == 'one':
        return [0] * 64
    if name == 'rank4':   # relative king rank: 1 -> 0, 2 -> 1, 3-4 -> 2, 5-8 -> 3
        return [rank4(sq // 8) for sq in range(64)]
    if name == 'rank4x2':   # rank4 x board half (files a-d -> even bucket, e-h -> odd): 8 buckets, unmirrored
        return [rank4(sq // 8) * 2 + (1 if sq % 8 >= 4 else 0) for sq in range(64)]
    if name == 'rank4x4':   # rank4 x file pair (a-b, c-d, e-f, g-h): 16 buckets, unmirrored
        return [rank4(sq // 8) * 4 + (sq % 8) // 2 for sq in range(64)]
    if name == 'rank4x8':   # rank4 x file: 32 buckets (the engine maximum), unmirrored
        return [rank4(sq // 8) * 8 + sq % 8 for sq in range(64)]
    raise SystemExit(f'unknown king map {name!r}')


def output_map(n):
    # bucket of a position with p pieces (kings included): min(n - 1, (p - 2) * n // 32) for p >= 2
    return [min(n - 1, max(p - 2, 0) * n // 32) for p in range(33)]


def write_v2(path, w1, b1, w2, b2, kmap, omap, residual, mirror):
    """w1 int16 [kb][768][H], b1 [H], w2 [ob][2H], b2 [ob]; returns the checksum. Refuses an existing path."""
    if os.path.exists(path):
        raise SystemExit(f'refusing to overwrite {path}')
    kb, inputs, hidden = w1.shape
    ob = w2.shape[0]
    assert inputs == INPUTS and b1.shape == (hidden,) and w2.shape == (ob, 2 * hidden) and b2.shape == (ob,)
    assert len(kmap) == 64 and max(kmap) < kb and len(omap) == 33 and max(omap) < ob
    for a in (w1, b1, w2, b2):
        assert a.dtype == np.int16
    flags = (FLAG_RESIDUAL if residual else 0) | (FLAG_MIRROR if mirror else 0)
    head = MAGIC + struct.pack('<IIIIIIII', 2, HEADER, 0, INPUTS, hidden, kb, ob, flags)
    head += struct.pack('<fff', 4096.0, 4096.0, 2.25) + bytes(kmap) + bytes(omap) + bytes(11)
    assert len(head) == HEADER
    body = head + w1.astype('<i2').tobytes() + b1.astype('<i2').tobytes() + w2.astype('<i2').tobytes() + b2.astype('<i2').tobytes()
    csum = fnv1a64_fast(body)
    tmp = path + '.part'
    if os.path.exists(tmp):
        raise SystemExit(f'refusing: {tmp} exists')
    with open(tmp, 'wb') as f:
        f.write(body + struct.pack('<Q', csum))
    os.replace(tmp, path)
    return csum


def read_v2(path):
    data = open(path, 'rb').read()
    if len(data) < HEADER + 8 or data[:8] != MAGIC:
        raise ValueError('not a FORGENN2 file')
    version, hb, fs, inputs, hidden, kb, ob, flags = struct.unpack_from('<IIIIIIII', data, 8)
    ws, os_, k = struct.unpack_from('<fff', data, 40)
    if (version, hb, fs, inputs) != (2, HEADER, 0, INPUTS) or (ws, os_, k) != (4096.0, 4096.0, 2.25):
        raise ValueError(f'unsupported header: version {version} header {hb} feature set {fs} inputs {inputs} scales {ws} {os_} {k}')
    kmap = list(data[52:116])
    omap = list(data[116:149])
    if any(data[149:160]):
        raise ValueError('reserved bytes not zero')
    expect = HEADER + 2 * (kb * INPUTS * hidden + hidden + ob * 2 * hidden + ob) + 8
    if len(data) != expect:
        raise ValueError(f'size {len(data)} != {expect}')
    stored = struct.unpack_from('<Q', data, len(data) - 8)[0]
    calc = fnv1a64_fast(data[:-8])
    if stored != calc:
        raise ValueError('checksum mismatch')
    off = HEADER
    def take(n):
        nonlocal off
        a = np.frombuffer(data, dtype='<i2', count=n, offset=off).astype(np.int16)
        off += 2 * n
        return a
    w1 = take(kb * INPUTS * hidden).reshape(kb, INPUTS, hidden)
    b1 = take(hidden)
    w2 = take(ob * 2 * hidden).reshape(ob, 2 * hidden)
    b2 = take(ob)
    return dict(hidden=hidden, kb=kb, ob=ob, residual=bool(flags & FLAG_RESIDUAL), mirror=bool(flags & FLAG_MIRROR),
                kmap=kmap, omap=omap, w1=w1, b1=b1, w2=w2, b2=b2, checksum=calc)


def parse_inc(path):
    text = open(path, 'r', encoding='utf-8').read()
    def array(name):
        m = re.search(r'\b' + name + r'\[(\d+)\]\s*=\s*\{([^}]*)\}', text)
        if not m:
            raise SystemExit(f'{name} not found in {path}')
        vals = [int(v) for v in m.group(2).replace('\n', ' ').split(',') if v.strip()]
        if len(vals) != int(m.group(1)):
            raise SystemExit(f'{name}: {len(vals)} values, declared {m.group(1)}')
        return np.array(vals, dtype=np.int16)
    w1 = array('NnueW1')
    b1 = array('NnueB1')
    w2 = array('NnueW2')
    m = re.search(r'\bNnueB2\s*=\s*(-?\d+)\s*;', text)
    if not m:
        raise SystemExit('NnueB2 not found')
    b2 = np.array([int(m.group(1))], dtype=np.int16)
    residual = re.search(r'#define\s+FORGE_NNUE_RESIDUAL\s+1', text) is not None
    hidden = b1.shape[0]
    return w1.reshape(INPUTS, hidden), b1, w2, b2, residual


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('from-lock')
    a.add_argument('inc')
    a.add_argument('out')
    a.add_argument('--kb-map', default='one', choices=['one', 'rank4', 'rank4x2', 'rank4x4', 'rank4x8'])
    a.add_argument('--ob', type=int, default=1)
    a.add_argument('--stand-alone', action='store_true', help='clear the residual flag (NOT the same function)')
    i = sub.add_parser('info')
    i.add_argument('file')
    r = sub.add_parser('random')
    r.add_argument('out')
    r.add_argument('--seed', type=int, required=True)
    r.add_argument('--hidden', type=int, default=256)
    r.add_argument('--kb-map', default='one', choices=['one', 'rank4', 'rank4x2', 'rank4x4', 'rank4x8'])
    r.add_argument('--ob', type=int, default=8)
    r.add_argument('--mirror', action='store_true')
    r.add_argument('--stand-alone', action='store_true')
    args = ap.parse_args()

    if args.cmd == 'from-lock':
        w1, b1, w2, b2, residual = parse_inc(args.inc)
        if not residual:
            raise SystemExit('the include file is not a residual net')
        kmap = king_map(args.kb_map)
        kb = max(kmap) + 1
        omap = output_map(args.ob)
        w1k = np.repeat(w1[None, :, :], kb, axis=0)
        w2o = np.repeat(w2[None, :], args.ob, axis=0)
        b2o = np.repeat(b2, args.ob)
        csum = write_v2(args.out, w1k, b1, w2o, b2o, kmap, omap, residual=not args.stand_alone, mirror=False)
        print(f'wrote {args.out}: hidden {b1.shape[0]} king buckets {kb} ({args.kb_map}) output buckets {args.ob} '
              f'{"stand-alone" if args.stand_alone else "residual"} fnv1a {csum:016x}')
    elif args.cmd == 'info':
        try:
            n = read_v2(args.file)
        except (ValueError, OSError) as e:
            print(f'BAD {args.file}: {e}')
            sys.exit(1)
        print(f'OK {args.file}: hidden {n["hidden"]} king buckets {n["kb"]} output buckets {n["ob"]} '
              f'{"mirrored" if n["mirror"] else "unmirrored"} {"residual" if n["residual"] else "stand-alone"} '
              f'fnv1a {n["checksum"]:016x} w1 [{n["w1"].min()}, {n["w1"].max()}] w2 [{n["w2"].min()}, {n["w2"].max()}] '
              f'kmap {n["kmap"][:8]}.. omap {n["omap"]}')
    elif args.cmd == 'random':
        rng = np.random.default_rng(args.seed)
        kmap = king_map(args.kb_map)
        kb = max(kmap) + 1
        h = args.hidden
        w1 = rng.integers(-300, 301, size=(kb, INPUTS, h), dtype=np.int64).astype(np.int16)
        b1 = rng.integers(0, 2049, size=h, dtype=np.int64).astype(np.int16)
        w2 = rng.integers(-4000, 4001, size=(args.ob, 2 * h), dtype=np.int64).astype(np.int16)
        b2 = rng.integers(-2000, 2001, size=args.ob, dtype=np.int64).astype(np.int16)
        csum = write_v2(args.out, w1, b1, w2, b2, kmap, output_map(args.ob), residual=not args.stand_alone,
                        mirror=args.mirror)
        print(f'wrote {args.out}: random seed {args.seed} hidden {h} kb {kb} ob {args.ob} mirror {args.mirror} '
              f'{"stand-alone" if args.stand_alone else "residual"} fnv1a {csum:016x}')


if __name__ == '__main__':
    main()
