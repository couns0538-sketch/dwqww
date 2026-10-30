"""R11 hold switch (CR fix 1: replaces the STOP/PAUSE control files).

  r11_hold.py hold [--minutes N]   create the named event Local\\Forge_R11_Hold (signalled) and keep it alive until
                                   N minutes pass or this process ends; every R11 stage waits at its next unit while
                                   the event is signalled, the trainer sleeps between steps
  r11_hold.py status               print whether a hold is active
Stopping R11: end its process by the PID in <root>/run/<stage>.pid.json; every stage resumes from its done markers
(data: per-shard JSON markers, train: the newest checkpoint of the run's own index).
"""
from __future__ import annotations

import ctypes
import os
import sys
import time
from ctypes import wintypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r11_common as C  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("hold", "status"):
        print(__doc__)
        return 2
    if argv[0] == "status":
        print("hold active" if C.hold_requested() else "no hold")
        return 0
    minutes = float(argv[argv.index("--minutes") + 1]) if "--minutes" in argv else None
    k32 = ctypes.windll.kernel32
    k32.CreateEventW.restype = wintypes.HANDLE
    k32.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    h = k32.CreateEventW(None, True, True, C.HOLD_EVENT)  # manual reset, initially signalled
    if not h:
        print("FAIL could not create the hold event")
        return 1
    print(f"hold active ({C.HOLD_EVENT}); end this process to release it" +
          (f", or wait {minutes} minutes" if minutes else ""), flush=True)
    t0 = time.time()
    while minutes is None or time.time() - t0 < minutes * 60:
        time.sleep(5)
    print("hold released")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
