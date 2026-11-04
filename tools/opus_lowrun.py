#!/usr/bin/env python3
"""opus_lowrun.py --mask 0x4 -- <program> [args ...] - R14 finish (Opus): run a program at Idle priority on a CPU mask.
Pins THIS process first (SetPriorityClass Idle + SetProcessAffinityMask, both read back; fail closed with exit 78),
then starts the program, which inherits both; also sets CUDA_VISIBLE_DEVICES=-1 and HIP_VISIBLE_DEVICES=-1 (no GPU).
Exit code = the program's. Own code, standard library only."""
import argparse
import ctypes
import os
import subprocess
import sys

IDLE = 0x40


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mask', required=True, help='hex CPU mask, e.g. 0x4 = CPU 2')
    ap.add_argument('cmd', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd[:1] == ['--'] else a.cmd
    if not cmd:
        sys.exit('opus_lowrun: no program given')
    mask = int(a.mask, 16)
    if mask <= 0 or mask >= 1 << (os.cpu_count() or 64):
        sys.exit(f'opus_lowrun: mask {a.mask} names no CPU of this PC')
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    me = ctypes.c_void_p(k32.GetCurrentProcess())
    pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
    if (not k32.SetPriorityClass(me, IDLE) or not k32.SetProcessAffinityMask(me, ctypes.c_size_t(mask))
            or k32.GetPriorityClass(me) != IDLE or not k32.GetProcessAffinityMask(me, ctypes.byref(pm), ctypes.byref(sm))
            or pm.value != mask):
        print('opus_lowrun: cannot set / confirm Idle + mask (fail closed)', file=sys.stderr)
        sys.exit(78)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='-1', HIP_VISIBLE_DEVICES='-1')
    sys.exit(subprocess.call(cmd, env=env))


if __name__ == '__main__':
    main()
