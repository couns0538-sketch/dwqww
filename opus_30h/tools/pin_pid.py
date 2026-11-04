#!/usr/bin/env python3
"""pin_pid.py <windows pid> <hex cpu mask> - Opus 30-h job: set Idle priority + a CPU mask on one process (own code).
Used by pin_self.sh to pin a bash script's own process first, so every program it starts afterwards inherits Idle and
the mask (Windows CreateProcess passes an Idle class and the affinity mask on to children). Fail closed: exit 1 if the
process cannot be opened, if a call fails, or if the read-back of priority class / mask differs."""
import ctypes
import sys

IDLE = 0x40
PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_INFORMATION = 0x0400


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pid, mask = int(sys.argv[1]), int(sys.argv[2], 16)
    if mask <= 0 or mask >= 1 << 16:
        sys.exit(f'pin_pid: mask {sys.argv[2]} names no CPU of this PC')
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.OpenProcess.restype = ctypes.c_void_p
    h = k32.OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_INFORMATION, False, pid)
    if not h:
        sys.exit(f'pin_pid: cannot open process {pid} (error {ctypes.get_last_error()})')
    h = ctypes.c_void_p(h)
    try:
        if not k32.SetPriorityClass(h, IDLE):
            sys.exit(f'pin_pid: SetPriorityClass failed (error {ctypes.get_last_error()})')
        if not k32.SetProcessAffinityMask(h, ctypes.c_size_t(mask)):
            sys.exit(f'pin_pid: SetProcessAffinityMask failed (error {ctypes.get_last_error()})')
        pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
        if not k32.GetProcessAffinityMask(h, ctypes.byref(pm), ctypes.byref(sm)) or pm.value != mask:
            sys.exit(f'pin_pid: read-back mask {pm.value:#x} != {mask:#x}')
        if k32.GetPriorityClass(h) != IDLE:
            sys.exit('pin_pid: read-back priority class is not Idle')
    finally:
        k32.CloseHandle(h)
    print(f'pinned pid {pid}: Idle, mask {mask:#x}')


if __name__ == '__main__':
    main()
