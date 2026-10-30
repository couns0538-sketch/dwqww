"""Probe: a process in background mode touches 300 MB once per second and prints its working set."""
import ctypes
import sys
import time
from ctypes import wintypes

import numpy as np
import psutil

k32 = ctypes.windll.kernel32
k32.GetCurrentProcess.restype = wintypes.HANDLE
k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
h = k32.GetCurrentProcess()
k32.SetPriorityClass(h, 0x00100000)  # PROCESS_MODE_BACKGROUND_BEGIN (what the old R11 code did)
k32.SetPriorityClass(h, 0x00000040)
a = np.ones(300 * 2**20 // 8)
p = psutil.Process()
for i in range(int(sys.argv[1]) if len(sys.argv) > 1 else 40):
    t = time.perf_counter()
    a += 1.0
    dt = time.perf_counter() - t
    print(i, round(p.memory_info().wset / 2**20), round(dt, 3), p.memory_info().num_page_faults, flush=True)
    time.sleep(1)
