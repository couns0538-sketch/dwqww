#!/usr/bin/env python3
"""gen_partial_tables.py - job-local table folders with missing or damaged files, from the 3-4 piece copies in out/tb/man34. Originals stay untouched.

usage: python -I -B gen_partial_tables.py <man34 dir> <out root> [--flips 40] [--seed 41]
Folders:
  nodtz:     no KQvKR.rtbz (a root with WDL only)
  nochild:   no KQvK.rtbw / .rtbz (the capture child of KQvKR has no table)
  dtzonly:   KRvK.rtbz without KRvK.rtbw (a DTZ file alone is not used)
  rejected:  KQvK.rtbw truncated to half, KRvK.rtbw junk bytes, KBvK.rtbw empty, KPvK.rtbz truncated (each must be rejected at load, the rest stays usable)
  flip_NN:   one table (KQvKR or KRPvK style 4-man) with random body bytes flipped: parses, values may be wrong; the reader must not crash or read out of range
"""
import argparse
import os
import random
import shutil
import sys


def clone(src, dst, skip=()):
    os.makedirs(dst)
    for name in os.listdir(src):
        if name not in skip:
            shutil.copyfile(os.path.join(src, name), os.path.join(dst, name))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('root')
    ap.add_argument('--flips', type=int, default=40)
    ap.add_argument('--seed', type=int, default=41)
    a = ap.parse_args()
    if os.path.exists(os.path.join(a.root, 'nodtz')):
        sys.exit('refusing: folders exist')
    rng = random.Random(a.seed)
    clone(a.src, os.path.join(a.root, 'nodtz'), {'KQvKR.rtbz'})
    clone(a.src, os.path.join(a.root, 'nochild'), {'KQvK.rtbw', 'KQvK.rtbz'})
    clone(a.src, os.path.join(a.root, 'dtzonly'), {'KRvK.rtbw'})
    d = os.path.join(a.root, 'rejected')
    clone(a.src, d)
    for name, mode in (('KQvK.rtbw', 'half'), ('KRvK.rtbw', 'junk'), ('KBvK.rtbw', 'empty'), ('KPvK.rtbz', 'half')):
        p = os.path.join(d, name)
        data = open(p, 'rb').read()
        if mode == 'half':
            data = data[:len(data) // 2]
        elif mode == 'junk':
            data = bytes(rng.randrange(256) for _ in range(len(data)))
        else:
            data = b''
        open(p, 'wb').write(data)
    targets = ['KQvKR.rtbw', 'KQvKR.rtbz', 'KRPvK.rtbw', 'KRPvK.rtbz', 'KPvKP.rtbw', 'KPvKP.rtbz']
    for i in range(a.flips):
        d = os.path.join(a.root, f'flip_{i:02d}')
        os.makedirs(d)
        for name in os.listdir(a.src):
            # only the tables the fixture reads, to keep the copies small
            if name.split('.')[0] in ('KQvKR', 'KRPvK', 'KPvKP', 'KQvK', 'KRvK', 'KPvK', 'KQPvK', 'KRvKP', 'KQvKP', 'KNPvK', 'KBPvK', 'KBvK', 'KNvK'):
                shutil.copyfile(os.path.join(a.src, name), os.path.join(d, name))
        name = targets[i % len(targets)]
        p = os.path.join(d, name)
        data = bytearray(open(p, 'rb').read())
        n = rng.choice((1, 4, 32, 256, len(data) // 16))
        lo = 0 if i % 3 == 0 else 64  # every third folder may also hit the header
        for _ in range(n):
            data[rng.randrange(lo, len(data))] = rng.randrange(256)
        open(p, 'wb').write(data)
    print('folders written under', a.root)


if __name__ == '__main__':
    main()
