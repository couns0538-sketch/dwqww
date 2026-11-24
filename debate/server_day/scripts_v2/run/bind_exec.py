"""Opus 2026-11-23 (Fable's FABLE-2311-PDEATHSIG-ANSWER; Neon 223800Z 1 and 231830Z): Linux only. Binds the
engine's life to the worker that starts it, then becomes the engine. Standard library only.

    bind_exec.py <parent pid> <exe>

1. prctl(PR_SET_PDEATHSIG, SIGKILL) in this process: when the thread that started it ends, the kernel ends this
   process. A result other than 0: one line on stderr, exit 3; NEVER an exec without the binding.
2. If the parent has changed (it died before step 1 took effect), exit 1: no engine.
3. os.execv(exe, [exe]). The kernel keeps the setting across the exec of an ordinary program (it clears it only for
   set-user-ID, set-group-ID or capability files), and the process keeps its number, so the worker's pid line, its
   ProcHandle and its pidfd name the engine.
A wrong usage: exit 2; an exec that fails: one stderr line, exit 4. No Python runs between the worker's fork and
this program's exec (Fable: a child stuck there would hold the worker's main thread inside Popen for the day).
"""
import ctypes
import os
import sys

PR_SET_PDEATHSIG, SIGKILL = 1, 9                 # Linux's numbers


def main() -> int:
    if len(sys.argv) != 3 or not sys.argv[1].isdigit() or not sys.argv[2]:
        print("usage: bind_exec.py <parent pid> <exe>", file=sys.stderr)
        return 2
    parent, exe = int(sys.argv[1]), sys.argv[2]
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_PDEATHSIG, SIGKILL, 0, 0, 0) != 0:
        print(f"bind_exec: prctl(PR_SET_PDEATHSIG) failed (errno {ctypes.get_errno()}): no engine is started",
              file=sys.stderr, flush=True)
        return 3
    if os.getppid() != parent:
        os._exit(1)
    try:
        os.execv(exe, [exe])
    except OSError as e:
        print(f"bind_exec: the engine could not be started ({e})", file=sys.stderr, flush=True)
    return 4


if __name__ == "__main__":
    sys.exit(main())
