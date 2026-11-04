#!/usr/bin/env python3
"""loader_fuzz_o30.py <exe> <valid net.nnue2> <new work dir> [--mask 0x1] - Opus 30-h job: every way a FORGENN2 file can
be wrong must be refused by the engine's v2 loader with an `info string ERROR EvalFileV2 ...` line, and the engine must
then play with its compiled-in net (bench d11 = the lock pin 312866). Own code (o30_v2net.py for the checksum).

Variants (each with a VALID checksum unless the checksum itself is the target, so only the targeted check can fire):
truncated / one byte longer, bad magic, version 3, header size 161, feature set 1, inputs 769, hidden 512, king buckets
0 / 33, output buckets 0 / 17, unknown flag bit, weight scale 4095, a king map entry = king buckets, an output map entry
= output buckets, a reserved byte set, a weight byte flipped (checksum mismatch). Then the sequences: valid net loaded
-> bad file -> the v2 net must be gone (bench = lock pin), and valid net -> empty value -> lock pin.
Prints one line per case and LOADER FUZZ PASS / FAIL; exit 0 only on PASS.
"""
import argparse
import ctypes
import os
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o30_v2net import fnv1a64_fast  # noqa: E402

LOCK_D11 = 312866


def with_checksum(body):
    return body + struct.pack('<Q', fnv1a64_fast(body))


def variants(raw):
    body = raw[:-8]
    kb, ob = struct.unpack_from('<II', body, 28)

    def put(fmt, off, val):
        b = bytearray(body)
        struct.pack_into(fmt, b, off, val)
        return with_checksum(bytes(b))
    out = [('truncated by 1 byte', raw[:-1], 'size'),
           ('one byte longer', raw + b'\0', 'size'),
           ('bad magic', with_checksum(b'FORGENN3' + body[8:]), 'magic'),
           ('version 3', put('<I', 8, 3), 'version'),
           ('header size 161', put('<I', 12, 161), 'header'),
           ('feature set 1', put('<I', 16, 1), 'feature set'),
           ('inputs 769', put('<I', 20, 769), 'inputs'),
           ('hidden 512', put('<I', 24, 512), 'hidden'),
           ('king buckets 0', put('<I', 28, 0), 'king buckets'),
           ('king buckets 33', put('<I', 28, 33), 'king buckets'),
           ('output buckets 0', put('<I', 32, 0), 'output buckets'),
           ('output buckets 17', put('<I', 32, 17), 'output buckets'),
           ('unknown flag bit 2', put('<I', 36, struct.unpack_from('<I', body, 36)[0] | 4), 'flag'),
           ('weight scale 4095', put('<f', 40, 4095.0), 'scale'),
           ('king map entry = king buckets', put('<B', 52 + 7, kb), 'king bucket map'),
           ('output map entry = output buckets', put('<B', 116 + 20, ob), 'output bucket map'),
           ('reserved byte set', put('<B', 155, 1), 'reserved')]
    b = bytearray(raw)
    b[200] ^= 0x01   # a weight byte; the stored checksum no longer matches
    out.append(('weight byte flipped', bytes(b), 'checksum'))
    return out


def session(exe, commands, mask):
    """Run the engine with these UCI lines (+ bench 11 + quit); return its output."""
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    me = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(me, 0x40) or not k32.SetProcessAffinityMask(me, ctypes.c_size_t(mask)):
        sys.exit('cannot set Idle / CPU mask (fail closed)')
    text = '\n'.join(commands + ['isready', 'bench 11', 'isready', 'quit']) + '\n'
    r = subprocess.run([exe], input=text, capture_output=True, text=True, timeout=300)
    return r.stdout + r.stderr


def bench11(out):
    for line in out.splitlines():
        if 'bench depth 11 nodes' in line:
            return int(line.split('nodes')[1].split()[0])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('net')
    ap.add_argument('work')
    ap.add_argument('--mask', default='0x1')
    a = ap.parse_args()
    mask = int(a.mask, 16)
    if os.path.exists(a.work):
        sys.exit(f'refusing: {a.work} exists')
    os.makedirs(a.work)
    raw = open(a.net, 'rb').read()
    fails = 0
    for name, data, reason in variants(raw):
        p = os.path.join(a.work, name.replace(' ', '_').replace('=', 'eq') + '.nnue2')
        with open(p, 'xb') as f:
            f.write(data)
        out = session(a.exe, [f'setoption name EvalFileV2 value {p}'], mask)
        err = [l for l in out.splitlines() if l.startswith('info string ERROR EvalFileV2')]
        nodes = bench11(out)
        ok = bool(err) and reason in err[0] and nodes == LOCK_D11 and 'loaded' not in out
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {err[0][len('info string '):][:110] if err else 'NO ERROR LINE'}; "
              f"bench d11 {nodes}")
    bad = os.path.join(a.work, 'weight_byte_flipped.nnue2')
    for name, cmds in (('valid net, then a damaged file -> no v2 net left', [f'setoption name EvalFileV2 value {a.net}',
                                                                              f'setoption name EvalFileV2 value {bad}']),
                       ('valid net, then empty value -> unloaded', [f'setoption name EvalFileV2 value {a.net}',
                                                                    'setoption name EvalFileV2 value'])):
        out = session(a.exe, cmds, mask)
        nodes = bench11(out)
        ok = nodes == LOCK_D11 and 'EvalFileV2 loaded' in out
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: bench d11 {nodes} (lock {LOCK_D11})")
    valid = session(a.exe, [f'setoption name EvalFileV2 value {a.net}'], mask)
    vn = bench11(valid)
    ok = vn is not None and vn != LOCK_D11 and 'EvalFileV2 loaded' in valid
    fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'} control: the valid net loads and is live (bench d11 {vn})")
    print(f"LOADER FUZZ {'PASS' if fails == 0 else 'FAIL'}: {fails} failing case(s), exe {a.exe}")
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
