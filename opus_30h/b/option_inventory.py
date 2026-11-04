#!/usr/bin/env python3
"""option_inventory.py <exe> [--names-from <exe or uci.txt>] [--mask 0x1] [--depth 11] [--pin 312866] - Opus 30-h job:
is every advertised search constant LIVE and identical at its default? (own code)
For each spin option of the exe that is not a standard / time-management option: bench <depth> with the option moved
(+25 % of its default, at least 1 step, inside its range; then -25 % if the first move left the node count unchanged)
must differ from the pin, and bench with the option set explicitly to its default must equal the pin. Prints one row per
option (LIVE / DEAD-AT-DEPTH, nodes) and INVENTORY PASS / FAIL (FAIL = an option at its default does not give the pin).
A DEAD-AT-DEPTH row is not a failure by itself (some constants only act deeper); it is listed for a deeper check."""
import argparse
import ctypes
import re
import subprocess
import sys

STANDARD = {'Threads', 'Hash', 'Move Overhead', 'Book Depth', 'Book Variety', 'MultiPV'}


def pin_self(mask):
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    me = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(me, 0x40) or not k32.SetProcessAffinityMask(me, ctypes.c_size_t(mask)):
        sys.exit('cannot set Idle / CPU mask (fail closed)')


def run(exe, lines):
    r = subprocess.run([exe], input='\n'.join(lines + ['quit']) + '\n', capture_output=True, text=True, timeout=600)
    return r.stdout


def bench(exe, setopts, depth):
    out = run(exe, [f'setoption name {n} value {v}' for n, v in setopts] + [f'bench {depth}'])
    m = re.search(r'bench depth \d+ nodes (\d+)', out)
    return int(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('--mask', default='0x1')
    ap.add_argument('--depth', type=int, default=11)
    ap.add_argument('--pin', type=int, default=312866)
    ap.add_argument('--only', default='', help='comma list of option names (default: all non-standard, non-Tm spins)')
    a = ap.parse_args()
    pin_self(int(a.mask, 16))
    spins = re.findall(r'^option name (.+?) type spin default (-?\d+) min (-?\d+) max (-?\d+)', run(a.exe, ['uci']), re.M)
    only = set(x for x in a.only.split(',') if x)
    rows, bad, dead = [], 0, []
    for name, d, lo, hi in spins:
        d, lo, hi = int(d), int(lo), int(hi)
        if name in STANDARD or name.startswith('Tm') or (only and name not in only):
            continue
        step = max(1, abs(d) // 4)
        moved = None
        for v in (d + step, d - step, d + 1, d - 1):
            if lo <= v <= hi and v != d:
                n = bench(a.exe, [(name, v)], a.depth)
                if n is not None and n != a.pin:
                    moved = (v, n)
                    break
        at_default = bench(a.exe, [(name, d)], a.depth)
        ok_default = at_default == a.pin
        bad += not ok_default
        state = 'LIVE' if moved else 'DEAD-AT-DEPTH'
        if not moved:
            dead.append(name)
        print(f"{state:13} {name:28} default {d:6} -> {('%d: %d nodes' % moved) if moved else 'no change found':24} "
              f"at default {at_default} {'= pin' if ok_default else '!= PIN'}", flush=True)
        rows.append(name)
    print(f"INVENTORY {'PASS' if bad == 0 and rows else 'FAIL'}: {len(rows)} options, {len(rows) - len(dead)} live at depth "
          f"{a.depth}, dead at this depth: {', '.join(dead) or '-'}; {bad} not equal to the pin at their default")
    sys.exit(0 if bad == 0 and rows else 1)


if __name__ == '__main__':
    main()
