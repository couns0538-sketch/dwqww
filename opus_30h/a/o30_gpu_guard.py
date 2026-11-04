#!/usr/bin/env python3
"""o30_gpu_guard.py - run the own GPU trainer under a thermal + yield guard (Opus 30-h job; own code).

  o30_gpu_guard.py --log <file> [--mask 0x30] [--test-hot T] -- <trainer exe> [args ...]
Starts the trainer as a child at Idle priority on --mask (set on this process first and read back; children inherit
it), then every 2 s:
  - temperatures from the HWiNFO CSV the PC's GPU guard reads: fan curve active (PWM >= 35 %): HARD at hot spot >= 76
    or memory junction >= 86, resume at <= 72 / <= 83; fan low: HARD 74 / 85, resume 70 / 82; EMERGENCY 78 / 88 (stays
    suspended >= 60 s). Same thresholds as F:\\forge_nnue_train\\tools\\gpu_guard.ps1, which does not watch this exe.
  - the CSV must be fresh (written within 30 s); a stale or unreadable feed SUSPENDS (fail closed).
  - yield: any python process whose command line names the npt training data or trainer tree (npt-like GPU trainer)
    suspends the own trainer until it is gone.
Suspend / resume act only on the child, through the psutil handle opened at start (pid + create time checked by
is_running), never on a remembered raw pid. The guard never kills; on its own exit it resumes the child. Every
transition is logged with time, reason and temperatures. Exit code = the trainer's.
--test-hot T: lower HARD hot spot to T (resume T-3) for the one-time proof that suspend and resume work.
"""
import argparse
import ctypes
import datetime
import os
import subprocess
import sys
import time

import psutil

CSV = r'C:\Users\Administrator\grok-pc\nnue\tools\hwinfo\gpu_sensors.csv'
NPT_MARKS = ('forge_j1_data', 'nnue-pytorch', 'forge_nnue_train')   # npt binpack, trainer tree, run root


def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class Feed:
    def __init__(self, path):
        self.path = path
        self.cols = None

    def read(self):
        """(hot, memj, pwm, util) of the newest row, or None if stale / unreadable."""
        try:
            if time.time() - os.path.getmtime(self.path) > 30:
                return None
            with open(self.path, 'rb') as f:
                header = f.readline().decode('latin-1').strip().split(',')
                f.seek(max(0, os.path.getsize(self.path) - 30000))
                tail = f.read().decode('latin-1').splitlines()
            names = [h.strip('"') for h in header]

            def col(prefix):
                for i, n in enumerate(names):
                    if n.startswith(prefix):
                        return i
                raise KeyError(prefix)
            ih, im = col('GPU Hot Spot Temperature'), col('GPU Memory Junction Temperature')
            ip, iu = col('GPU Fan PWM'), col('GPU Utilization')
            for line in reversed(tail):
                x = line.split(',')
                if len(x) >= len(names) - 1 and x[0][:1].isdigit():
                    return float(x[ih]), float(x[im]), float(x[ip] or 0), float(x[iu] or 0)
        except (OSError, ValueError, KeyError, IndexError):
            return None
        return None


def npt_like():
    """pids of python processes that name the npt data / trainer tree; an unreadable python command line counts as
    npt-like (fail closed, R11 rule: an unreadable python command line = production)."""
    found = []
    for p in psutil.process_iter(['name']):
        try:
            if (p.info['name'] or '').lower() != 'python.exe':
                continue
            if any(m in ' '.join(p.cmdline()) for m in NPT_MARKS):
                found.append(p.pid)
        except psutil.AccessDenied:
            found.append(p.pid)
        except psutil.Error:
            continue
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--log', required=True)
    ap.add_argument('--mask', default='0x30')
    ap.add_argument('--test-hot', type=float)
    ap.add_argument('cmd', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd[:1] == ['--'] else a.cmd
    if not cmd:
        sys.exit('no trainer command')
    log = open(a.log, 'a', encoding='utf-8', newline='\n')

    def say(msg):
        log.write(f'{now()} {msg}\n')
        log.flush()
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    me = ctypes.c_void_p(k32.GetCurrentProcess())
    mask = int(a.mask, 16)
    pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
    if (not k32.SetPriorityClass(me, 0x40) or not k32.SetProcessAffinityMask(me, ctypes.c_size_t(mask))
            or not k32.GetProcessAffinityMask(me, ctypes.byref(pm), ctypes.byref(sm)) or pm.value != mask):
        say('cannot set / confirm Idle + mask (fail closed)')
        sys.exit(78)
    feed = Feed(CSV)
    if feed.read() is None:
        say('sensor feed stale or unreadable at start: not starting the trainer (fail closed)')
        sys.exit(78)
    if npt_like():
        say(f'npt-like trainer running {npt_like()}: not starting (yield)')
        sys.exit(78)
    env = dict(os.environ)
    child = subprocess.Popen(cmd, env=env)
    proc = psutil.Process(child.pid)
    say(f'start trainer pid {child.pid} mask {a.mask} cmd {" ".join(cmd)}')
    suspended, reason, hold_until = False, '', 0.0
    hard_h = a.test_hot if a.test_hot else None
    stats = dict(suspends=0, suspended_seconds=0.0)
    t_susp = 0.0
    try:
        while child.poll() is None:
            v = feed.read()
            npt = npt_like()
            want, why = False, ''
            if npt:
                want, why = True, f'npt-like process {npt}'
            elif v is None:
                want, why = True, 'sensor feed stale/unreadable'
            else:
                hot, mj, pwm, util = v
                fan = pwm >= 35
                hh, hm, rh, rm = (76, 86, 72, 83) if fan else (74, 85, 70, 82)
                if hard_h:
                    hh, rh = hard_h, hard_h - 3
                if hot >= 78 or mj >= 88:
                    want, why, hold_until = True, f'EMERGENCY hot {hot} memj {mj}', time.time() + 60
                elif hot >= hh or mj >= hm:
                    want, why = True, f'HARD hot {hot} memj {mj} (limits {hh}/{hm})'
                elif suspended and (hot > rh or mj > rm or time.time() < hold_until):
                    want, why = True, f'cooling hot {hot} memj {mj} (resume <= {rh}/{rm})'
            if want and not suspended:
                if proc.is_running():
                    proc.suspend()
                    suspended, t_susp = True, time.time()
                    stats['suspends'] += 1
                    say(f'SUSPEND: {why}')
            elif not want and suspended:
                if proc.is_running():
                    proc.resume()
                    stats['suspended_seconds'] += time.time() - t_susp
                    suspended = False
                    say(f'RESUME: hot {v[0]} memj {v[1]}' if v else 'RESUME')
            time.sleep(2)
    finally:
        if suspended and proc.is_running():
            proc.resume()
            say('guard exit: resumed the trainer')
        code = child.poll()
        say(f'end: trainer exit {code}, suspends {stats["suspends"]}, suspended {stats["suspended_seconds"]:.0f} s')
        log.close()
    sys.exit(child.returncode if child.returncode is not None else 1)


if __name__ == '__main__':
    main()
