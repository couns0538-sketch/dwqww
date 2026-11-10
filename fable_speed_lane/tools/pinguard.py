"""Second line of defence for the cores 3-6 rule of the fable2 speed-lane job.

Every Python tool of this job calls ensure() before it does any CPU work or starts an engine.
ensure() checks that this process already runs inside affinity mask 0x78 (CPU 3,4,5,6) at Idle
priority; if it does not, it sets both, reads them back, and aborts if they did not stick.
A mask that is a subset of 0x78 (set by tools/pin.ps1 -Mask) is kept as it is.
Child processes inherit both settings; narrow() pins a child further to one CPU of the lane.
"""
import ctypes
import ctypes.wintypes as wt

LANE = 0x78
IDLE_PRIORITY_CLASS = 0x40


def _k32():
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
    return k


def read(handle=None):
    """(affinity mask, priority class) of a process handle (default: this process)."""
    k = _k32()
    h = handle if handle is not None else k.GetCurrentProcess()
    proc_mask = ctypes.c_size_t()
    sys_mask = ctypes.c_size_t()
    if not k.GetProcessAffinityMask(h, ctypes.byref(proc_mask), ctypes.byref(sys_mask)):
        raise SystemExit(f"pinguard: GetProcessAffinityMask failed ({ctypes.get_last_error()})")
    return proc_mask.value, k.GetPriorityClass(h)


def ensure() -> str:
    k = _k32()
    h = k.GetCurrentProcess()
    mask, prio = read(h)
    if mask == 0 or (mask & ~LANE) != 0:
        if not k.SetProcessAffinityMask(h, LANE):
            raise SystemExit(f"pinguard: SetProcessAffinityMask failed ({ctypes.get_last_error()})")
    if prio != IDLE_PRIORITY_CLASS:
        if not k.SetPriorityClass(h, IDLE_PRIORITY_CLASS):
            raise SystemExit(f"pinguard: SetPriorityClass failed ({ctypes.get_last_error()})")
    mask, prio = read(h)
    if mask == 0 or (mask & ~LANE) != 0 or prio != IDLE_PRIORITY_CLASS:
        raise SystemExit(f"pinguard: not pinned (mask {mask:#x}, priority class {prio:#x})")
    return f"pinned: affinity {mask:#x} (inside CPU 3-6), priority Idle"


def narrow(handle, mask: int) -> str:
    """Pin a child process (by handle) to `mask`, which must lie inside the lane; read it back."""
    if mask == 0 or (mask & ~LANE) != 0:
        raise SystemExit(f"pinguard: child mask {mask:#x} is not inside {LANE:#x}")
    k = _k32()
    if not k.SetProcessAffinityMask(wt.HANDLE(handle), mask):
        raise SystemExit(f"pinguard: child SetProcessAffinityMask failed ({ctypes.get_last_error()})")
    got, prio = read(wt.HANDLE(handle))
    if got != mask or prio != IDLE_PRIORITY_CLASS:
        raise SystemExit(f"pinguard: child not pinned (mask {got:#x}, priority class {prio:#x})")
    return f"child pinned: affinity {got:#x}, priority Idle"
