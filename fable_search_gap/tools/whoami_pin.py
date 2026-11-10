"""Print (read-only) the affinity mask and priority class this process was STARTED with.

Used to test tools/pin.ps1: started through the launcher it must print mask 0x78 and class 0x40 (Idle).
It deliberately does not set anything, unlike pinguard.ensure().
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import sys

k = ctypes.WinDLL("kernel32", use_last_error=True)
k.GetCurrentProcess.restype = wt.HANDLE
k.GetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
k.GetPriorityClass.argtypes = [wt.HANDLE]
k.GetPriorityClass.restype = wt.DWORD
pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
k.GetProcessAffinityMask(k.GetCurrentProcess(), ctypes.byref(pm), ctypes.byref(sm))
prio = k.GetPriorityClass(k.GetCurrentProcess())
role = sys.argv[1] if len(sys.argv) > 1 else "parent"
print(f"{role}: affinity {pm.value:#x} priority_class {prio:#x} temp {__import__('os').environ.get('TEMP')}", flush=True)
if role == "parent":
    # A grandchild must inherit the same mask and class without anyone setting them again.
    subprocess.run([sys.executable, "-I", "-B", __file__, "child"], check=True)
ok = pm.value == 0x78 and prio == 0x40
raise SystemExit(0 if ok else 1)
