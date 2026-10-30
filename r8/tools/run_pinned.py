#!/usr/bin/env python3
"""Run a Python script with this process (and so every child it starts) pinned to an affinity mask at BelowNormal.
R5B (copied unchanged into R5D): keeps the smoke games off the core of a concurrent NPS run; R5D runs the proof loops on 3 CPUs.
usage: run_pinned.py --mask 0xFFF -- <script.py> [args...]
"""
import ctypes
import ctypes.wintypes as wt
import runpy
import sys

k = ctypes.WinDLL("kernel32", use_last_error=True)
k.GetCurrentProcess.restype = wt.HANDLE
k.SetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.c_size_t]
k.SetPriorityClass.argtypes = [wt.HANDLE, wt.DWORD]
args = sys.argv[1:]
if len(args) < 4 or args[0] != "--mask" or args[2] != "--":
    raise SystemExit(__doc__)
mask = int(args[1], 0)
if not k.SetProcessAffinityMask(k.GetCurrentProcess(), mask) or not k.SetPriorityClass(k.GetCurrentProcess(), 0x4000):
    raise SystemExit(f"affinity/priority failed: {ctypes.get_last_error()}")
print(f"run_pinned: affinity mask {mask:#x}, BelowNormal: {args[3]}", flush=True)
sys.argv = args[3:]
runpy.run_path(args[3], run_name="__main__")
