"""Second line of defence for the cores 3-6 rule of the fable52 search-gap job.

Every Python tool of this job calls ensure() before it does any CPU work or starts an engine.
ensure() sets this process to affinity mask 0x78 (CPU 3,4,5,6) and Idle priority, reads both
back, and aborts if they did not stick. Child processes inherit both settings.

Normally the tool is already started through tools/pin.ps1, so this is a re-check, not the pin.
"""
import ctypes
import ctypes.wintypes as wt

MASK = 0x78
IDLE_PRIORITY_CLASS = 0x40


def ensure(mask: int = MASK) -> str:
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.GetCurrentProcess.restype = wt.HANDLE
    k.SetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.c_size_t]
    k.SetProcessAffinityMask.restype = wt.BOOL
    k.GetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    k.GetProcessAffinityMask.restype = wt.BOOL
    k.SetPriorityClass.argtypes = [wt.HANDLE, wt.DWORD]
    k.SetPriorityClass.restype = wt.BOOL
    k.GetPriorityClass.argtypes = [wt.HANDLE]
    k.GetPriorityClass.restype = wt.DWORD
    h = k.GetCurrentProcess()
    if not k.SetProcessAffinityMask(h, mask):
        raise SystemExit(f"pinguard: SetProcessAffinityMask failed ({ctypes.get_last_error()})")
    if not k.SetPriorityClass(h, IDLE_PRIORITY_CLASS):
        raise SystemExit(f"pinguard: SetPriorityClass failed ({ctypes.get_last_error()})")
    proc_mask = ctypes.c_size_t()
    sys_mask = ctypes.c_size_t()
    if not k.GetProcessAffinityMask(h, ctypes.byref(proc_mask), ctypes.byref(sys_mask)):
        raise SystemExit(f"pinguard: GetProcessAffinityMask failed ({ctypes.get_last_error()})")
    prio = k.GetPriorityClass(h)
    if proc_mask.value != mask or prio != IDLE_PRIORITY_CLASS:
        raise SystemExit(f"pinguard: not pinned (mask {proc_mask.value:#x}, priority class {prio:#x})")
    return f"pinned: affinity {proc_mask.value:#x} (CPU 3-6), priority Idle"
