#!/usr/bin/env python3
"""warm_refusal_check.py - fault-injection checks of warm_identity.py's placement refusal (speed job, own code).

usage: python -I -B warm_refusal_check.py <tools dir> <engine exe> <fens file> <out root>
Called by tests/test_cr_should_w8.ps1 (W5a-e), which judges the printed lines. Owner brief, leftover job 2: when the
CPU mask or the Idle class read-back does not match, warm_identity must exit 1 and must not claim pinned engines.
  W5a mask : this process really sits on CPU 0 (0x1) at Idle; ctypes.WinDLL is wrapped so that SetProcessAffinityMask
             reports success but changes nothing; warm_identity.py run as __main__ must exit 1 ('not pinned') before
             its out dir or any engine exists.
  W5b class: the same with SetPriorityClass as the silent no-op while this process is BelowNormal on 0x3.
  W5c / W5d: no injection; this process really sits on 0x1 Idle (c) or 0x3 BelowNormal (d) and calls run() without
             place(): the engine it starts inherits that state, its read-back must raise 'not pinned', and the engine
             gets quit + EOF (never killed; the caller checks that its PID has ended).
Engine time: one engine start + quit in each of W5c and W5d. Writes only under <out root> (nothing in W5a-d).
"""
import ctypes
import pathlib
import runpy
import sys

TOOLS, EXE, FENS, ROOT = sys.argv[1:5]
sys.path.insert(0, TOOLS)
import warm_identity as w  # noqa: E402 - the tool under test, imported from <tools dir>

REAL_WINDLL = ctypes.WinDLL
K = w.kernel32()
ME = K.GetCurrentProcess()
BELOW_NORMAL = 0x4000


def put(mask, cls):
    # the REAL state of this process, which the tool must detect
    if not K.SetProcessAffinityMask(ME, mask) or not K.SetPriorityClass(ME, cls):
        raise SystemExit(f'cannot set this process to mask 0x{mask:X} class 0x{cls:X}')


class SilentNoOp:
    """Stands in for one kernel32 setter: reports success and changes nothing (the case a read-back exists for)."""
    argtypes = restype = None

    def __call__(self, *args):
        return 1


class InjectedK32:
    def __init__(self, real, silent):
        self._real, self._silent, self._noop = real, silent, SilentNoOp()

    def __getattr__(self, name):
        return self._noop if name == self._silent else getattr(self._real, name)


def main_case(tag, mask, cls, silent):
    put(mask, cls)
    out = pathlib.Path(ROOT) / tag
    sys.argv = ['warm_identity.py', EXE, EXE, FENS, str(out)]
    ctypes.WinDLL = lambda *a, **kw: InjectedK32(REAL_WINDLL(*a, **kw), silent)
    try:
        runpy.run_path(str(pathlib.Path(TOOLS) / 'warm_identity.py'), run_name='__main__')
        rc = 0
    except SystemExit as x:
        rc = x.code
    finally:
        ctypes.WinDLL = REAL_WINDLL
    print(f'{tag} rc {rc} outdir {"exists" if out.exists() else "absent"}', flush=True)


def engine_case(tag, mask, cls):
    put(mask, cls)
    fen = next(s.strip() for s in open(FENS, encoding='utf-8') if s.strip() and not s.startswith('#'))
    try:
        w.run(EXE, [fen], 2000, K)
        print(f'{tag} NOT refused', flush=True)
    except RuntimeError as x:
        print(f'{tag} refused: {x}', flush=True)


main_case('W5a', 0x1, w.IDLE, 'SetProcessAffinityMask')
main_case('W5b', 0x3, BELOW_NORMAL, 'SetPriorityClass')
engine_case('W5c', 0x1, w.IDLE)
engine_case('W5d', 0x3, BELOW_NORMAL)
put(w.MASK, w.IDLE)
print('done', flush=True)
