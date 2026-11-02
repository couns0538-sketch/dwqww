"""Stdlib-only synthetic game-provenance and runtime policy checks. UNPROVEN."""
import argparse
import contextlib
import ctypes
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).parent
sys.path[:0] = [str(HERE/'regression'), str(HERE.parent/'gameprov')]
from path_guard import owned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if os.name != 'nt':
        raise ValueError('Windows CPU admission required')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetPriorityClass.argtypes = [ctypes.c_void_p]
    kernel.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    proc = kernel.GetCurrentProcess(); affinity = ctypes.c_size_t(); system = ctypes.c_size_t()
    if kernel.GetPriorityClass(proc) != 0x40 or not kernel.GetProcessAffinityMask(proc, ctypes.byref(affinity), ctypes.byref(system)) or affinity.value not in (4, 8):
        raise ValueError('Idle, one admitted CPU2/3 required')
    if shutil.disk_usage('C:/').free < 30*1024**3 or shutil.disk_usage('D:/').free < 50*1024**3+256*1024**2:
        raise ValueError('C30GiB / D50GiB plus fixture reservation floor')
    out = owned(args.out)
    if not out.is_relative_to(Path('D:/a11/fixture-runs')):
        raise ValueError('fresh fixture output must be under D:/a11/fixture-runs')
    out.mkdir(parents=True, exist_ok=False)
    temp = out/'temp'; temp.mkdir()
    for name in ('TEMP', 'TMP', 'TMPDIR'):
        os.environ[name] = str(temp)
    tempfile.tempdir = str(temp)
    os.environ.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                      CUDA_VISIBLE_DEVICES='', HIP_VISIBLE_DEVICES='', ROCR_VISIBLE_DEVICES='')
    sys.dont_write_bytecode = True
    started = time.monotonic()
    suites = [unittest.TestLoader().discover(str(HERE.parent/'gameprov'), pattern='test_gameprov.py'),
              unittest.TestLoader().discover(str(HERE/'regression'), pattern='test_runtime_guard.py')]
    counts = [suite.countTestCases() for suite in suites]
    with (out/'unittest.log').open('x', encoding='utf8', newline='\n') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.TestSuite(suites))
    passed = result.wasSuccessful() and not result.skipped and counts == [26, 4] and result.testsRun == 30
    report = {'status': 'FIXTURE_PASS' if passed else 'FAIL', 'classification': 'UNPROVEN',
              'scope': 'Synthetic game provenance and direct runtime guard functions only; no original73, native loader, training or production data qualification',
              'tests_run': result.testsRun, 'gameprov_collected': counts[0], 'runtime_guard_collected': counts[1],
              'failures': result.failures, 'errors': result.errors, 'skipped': result.skipped,
              'elapsed_seconds': time.monotonic()-started, 'artifacts': str(temp), 'preserved': True}
    # unittest stores TestCase objects; stable string nodeids are the JSON form.
    for key in ('failures', 'errors', 'skipped'):
        report[key] = [[str(test), detail] for test, detail in report[key]]
    with (out/'RESULT.json').open('x', encoding='utf8', newline='\n') as stream:
        json.dump(report, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({key: report[key] for key in ('status', 'tests_run', 'gameprov_collected', 'runtime_guard_collected')}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
