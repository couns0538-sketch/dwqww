"""O4 local CPU checks on the shared PC: runs a (renamed) trainer or checker script with torch limited to one
thread and a free-RAM guard. Exit status 3 when free physical memory is below 6 GB at the start or at any check
(every 2 s) while the script runs.
usage: python opus_nnue_smoke_run1t.py <script.py> [script args...]"""
import os
import runpy
import sys
import threading
import time

for _var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_var] = "1"
LIMIT_GB = 6.0


def free_gb():
    if os.name == "nt":
        import ctypes

        class MSX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [(f, ctypes.c_ulonglong) for f in (
                "ullTotalPhys", "ullAvailPhys", "ullTotalPageFile", "ullAvailPageFile", "ullTotalVirtual", "ullAvailVirtual",
                "ullAvailExtendedVirtual")]
        ms = MSX()
        ms.dwLength = ctypes.sizeof(MSX)
        ctypes.WinDLL("kernel32").GlobalMemoryStatusEx(ctypes.byref(ms))
        return ms.ullAvailPhys / 2**30
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 2**20
    return float("inf")


start = free_gb()
print(f"RAM GUARD: free RAM {start:.2f} GB at start (limit {LIMIT_GB} GB)", flush=True)
if start < LIMIT_GB:
    print("RAM GUARD: below the limit: not starting", flush=True)
    sys.exit(3)


def guard():
    while True:
        time.sleep(2)
        free = free_gb()
        if free < LIMIT_GB:
            print(f"RAM GUARD: free RAM {free:.2f} GB < {LIMIT_GB} GB: stopping", flush=True)
            os._exit(3)


threading.Thread(target=guard, daemon=True).start()
import torch  # noqa: E402  (after the thread environment variables)

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
script = sys.argv[1]
sys.argv = [script] + sys.argv[2:]
sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
runpy.run_path(script, run_name="__main__")
