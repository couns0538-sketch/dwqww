"""Second line of defence for the cores 3-6 rule of job 3 (adapted from job 2's tools/pinguard.py, own code).

Every Python tool of this job calls ensure() before it does any CPU work or starts an engine.
ensure() checks that this process already runs inside affinity mask 0x78 (CPU 3,4,5,6) at Idle
priority; if it does not, it sets both, reads them back, and aborts if they did not stick.
A mask that is a subset of 0x78 (set by scripts/pin_run.ps1 -Mask) is kept as it is.
Child processes inherit both settings; check_child() reads a child's settings back before it gets work.

Run as a script it prints the settings this process INHERITED (before ensure() touches anything):
that is the test of the launcher.
"""
import ctypes
import ctypes.wintypes as wt

LANE = 0x78
IDLE_PRIORITY_CLASS = 0x40
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


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
    k.GetProcessTimes.argtypes = [wt.HANDLE] + [ctypes.POINTER(wt.FILETIME)] * 4
    k.GetProcessTimes.restype = wt.BOOL
    return k


def read(handle=None):
    """(affinity mask, priority class) of a process handle (default: this process)."""
    k = _k32()
    h = wt.HANDLE(handle) if handle is not None else k.GetCurrentProcess()
    proc_mask = ctypes.c_size_t()
    sys_mask = ctypes.c_size_t()
    if not k.GetProcessAffinityMask(h, ctypes.byref(proc_mask), ctypes.byref(sys_mask)):
        raise SystemExit(f"pinguard3: GetProcessAffinityMask failed ({ctypes.get_last_error()})")
    return proc_mask.value, k.GetPriorityClass(h)


def ok(mask: int, prio: int) -> bool:
    return mask != 0 and (mask & ~LANE) == 0 and prio == IDLE_PRIORITY_CLASS


def ensure() -> str:
    k = _k32()
    h = k.GetCurrentProcess()
    mask, prio = read()
    if mask == 0 or (mask & ~LANE) != 0:
        if not k.SetProcessAffinityMask(h, LANE):
            raise SystemExit(f"pinguard3: SetProcessAffinityMask failed ({ctypes.get_last_error()})")
    if prio != IDLE_PRIORITY_CLASS:
        if not k.SetPriorityClass(h, IDLE_PRIORITY_CLASS):
            raise SystemExit(f"pinguard3: SetPriorityClass failed ({ctypes.get_last_error()})")
    mask, prio = read()
    if not ok(mask, prio):
        raise SystemExit(f"pinguard3: not pinned (mask {mask:#x}, priority class {prio:#x})")
    return f"pinned: affinity {mask:#x} (inside CPU 3-6), priority Idle"


def check_child(handle) -> str:
    """Read a child's affinity and priority back; abort if it is outside the lane or not Idle."""
    mask, prio = read(int(handle))
    if not ok(mask, prio):
        raise SystemExit(f"pinguard3: child not pinned (mask {mask:#x}, priority class {prio:#x})")
    return f"child pinned: affinity {mask:#x}, priority Idle"


def cpu_seconds(handle) -> float:
    """Kernel + user CPU time a process has used so far (tells a starved process from a hung one)."""
    k = _k32()
    c, e, kt, ut = wt.FILETIME(), wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
    if not k.GetProcessTimes(wt.HANDLE(int(handle)), ctypes.byref(c), ctypes.byref(e), ctypes.byref(kt), ctypes.byref(ut)):
        return -1.0
    total = ((kt.dwHighDateTime << 32) | kt.dwLowDateTime) + ((ut.dwHighDateTime << 32) | ut.dwLowDateTime)
    return total / 1e7


if __name__ == "__main__":
    m, p = read()
    print(f"inherited: affinity {m:#x}, priority class {p:#x}, inside lane and Idle: {ok(m, p)}")
    print(ensure())
