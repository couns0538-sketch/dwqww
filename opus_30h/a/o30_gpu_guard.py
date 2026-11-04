#!/usr/bin/env python3
"""o30_gpu_guard.py - run the own GPU trainer under a thermal + yield guard (Opus 30-h job; own code).

  o30_gpu_guard.py --log <file> [--mask 0x30] [--test-hot T] -- <trainer exe> [args ...]
  o30_gpu_guard.py --resume-pid PID --create-time T [--expect-name forge-v2-bullet.exe]
Starts the trainer as a child at Idle priority on --mask (set on this process first and read back; children inherit
it), then every 2 s:
  - temperatures from the HWiNFO CSV the PC's GPU guard reads: fan curve active (PWM >= 35 %): HARD at hot spot >= 76
    or memory junction >= 86, resume at <= 72 / <= 83; fan low: HARD 74 / 85, resume 70 / 82; EMERGENCY 78 / 88 (stays
    suspended >= 60 s). Same thresholds as F:\\forge_nnue_train\\tools\\gpu_guard.ps1, which does not watch this exe.
  - the CSV must be fresh (written within 30 s); a stale or unreadable feed SUSPENDS (fail closed).
  - yield: any python process whose command line names the npt training data or trainer tree (npt-like GPU trainer)
    suspends the own trainer until it is gone.
Suspend / resume act only on the child, through the psutil handle opened at start (pid + create time checked by
is_running), never on a remembered raw pid. The guard never kills. Every transition is logged with time, reason,
temperatures and the child's pid + create time.
Exit paths (CR item 9):
  - trainer finished: 'end:' line, exit code = the trainer's.
  - an error in one poll is logged and guarding goes on; ERROR_CAP failed polls in a row (or any error that escapes
    the loop) = ABORT: the trainer is suspended and LEFT SUSPENDED (fail closed: it must not run on without the
    thermal guard), a loud 'ABORT' line names pid + create time and the resume command, exit 79, no 'end:' line.
  - a console event (Ctrl+C, Ctrl+Break, console closed, logoff, shutdown): a SetConsoleCtrlHandler resumes a
    suspended trainer first, so it can take the same event and end (a suspended process cannot), then the guard
    exits (exit 130).
  - NEVER `taskkill /F` the guard: a hard kill runs no handler, so a trainer suspended at that moment stays frozen.
    If it happened: find the last 'SUSPEND' line in the guard log and run
    `o30_gpu_guard.py --resume-pid <pid> --create-time <t>` (checks pid + create time + exe name before resuming).
--test-hot T: lower HARD hot spot to T (resume T-3) for the proof that suspend and resume work.
--test-raise-after N: every poll after the first N raises (proof of the ABORT path; dummy child only).
--test-hard-exit-after S: S seconds after the first SUSPEND the guard ends itself with TerminateProcess (what taskkill /F
does: no handler, no finally), to prove --resume-pid (dummy child only).
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
# npt binpack, trainer tree, run root, and the npt interpreter / venv tree F:\nnue_pytorch (review G-002). The npt
# launch line seen on 2026-11-04 10:06 contains the first three; any python whose command line names one of these, or
# cannot be read, makes the guard suspend the own trainer - never put these strings on an own python command line.
NPT_MARKS = ('forge_j1_data', 'nnue-pytorch', 'forge_nnue_train', 'nnue_pytorch')
ERROR_CAP = 15   # failed polls in a row (2 s each) before the guard gives up guarding: ABORT, trainer left suspended
EXIT_ABORT, EXIT_CONSOLE = 79, 130


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


def resume_pid(pid, create_time, expect_name):
    """--resume-pid: resume a trainer that a hard-killed guard left suspended. Acts only if pid, create time (from the
    guard log's SUSPEND line, +-0.01 s) and exe name all match; prints what it did. Exit 0 = resumed."""
    try:
        p = psutil.Process(pid)
        ct, name = p.create_time(), p.name()
    except psutil.Error as error:
        print(f'refusing: pid {pid}: {type(error).__name__}: {error}')
        return 2
    if abs(ct - create_time) > 0.01:
        print(f'refusing: pid {pid} has create time {ct:.3f}, the log says {create_time:.3f} (pid reused?)')
        return 2
    if name.lower() != expect_name.lower():
        print(f'refusing: pid {pid} is {name}, expected {expect_name}')
        return 2
    try:
        before = p.status()
        p.resume()
        print(f'{now()} resumed pid {pid} ({name}, create time {ct:.3f}); status before {before}, after {p.status()}')
    except psutil.Error as error:
        print(f'resume failed: {type(error).__name__}: {error}')
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--log')
    ap.add_argument('--mask', default='0x30')
    ap.add_argument('--test-hot', type=float)
    ap.add_argument('--test-raise-after', type=int)
    ap.add_argument('--test-hard-exit-after', type=float)
    ap.add_argument('--resume-pid', type=int)
    ap.add_argument('--create-time', type=float)
    ap.add_argument('--expect-name', default='forge-v2-bullet.exe')
    ap.add_argument('cmd', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    if a.resume_pid is not None:
        if a.create_time is None:
            sys.exit('--resume-pid needs --create-time (copy both from the SUSPEND line of the guard log)')
        sys.exit(resume_pid(a.resume_pid, a.create_time, a.expect_name))
    if not a.log:
        sys.exit('--log is required')
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
    ident = f'pid {child.pid} create_time {proc.create_time():.3f}'
    say(f'start trainer {ident} mask {a.mask} cmd {" ".join(cmd)}')
    st = dict(suspended=False, ctrl=None)

    def on_console(event):   # runs on a thread the console creates; resume first so the child can take the event
        st['ctrl'] = event
        try:
            if st['suspended'] and proc.is_running():
                proc.resume()
                st['suspended'] = False
                say(f'console event {event}: resumed the trainer ({ident}) so it can handle the event; guard exits')
            else:
                say(f'console event {event}: guard exits')
        except Exception as error:   # noqa: BLE001 - must not raise inside the handler; logged
            say(f'console event {event}: resume failed {type(error).__name__}: {error}')
        return 0   # not handled here: the default handling (end of the process) goes on
    handler_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)
    handler = handler_type(on_console)   # kept referenced for the whole run
    if not k32.SetConsoleCtrlHandler(handler, 1):
        say(f'warning: SetConsoleCtrlHandler failed (error {ctypes.get_last_error()}); console events are not caught')
    why, hold_until = '', 0.0
    hard_h = a.test_hot if a.test_hot else None
    stats = dict(suspends=0, suspended_seconds=0.0, errors=0, polls=0)
    t_susp, last_note, in_row, abort = 0.0, 0.0, 0, None
    try:
        while child.poll() is None and st['ctrl'] is None:
            # review G-003 / CR item 9: an error in one poll is logged and the next poll runs; ERROR_CAP errors in a
            # row end the guard fail closed (ABORT below), never with the trainer running on unguarded
            try:
                stats['polls'] += 1
                if a.test_raise_after is not None and stats['polls'] > a.test_raise_after:
                    raise RuntimeError('test error injected by --test-raise-after')
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
                    elif st['suspended'] and (hot > rh or mj > rm or time.time() < hold_until):
                        want, why = True, f'cooling hot {hot} memj {mj} (resume <= {rh}/{rm})'
                if want and not st['suspended']:
                    if proc.is_running():
                        proc.suspend()
                        st['suspended'], t_susp, last_note = True, time.time(), time.time()
                        stats['suspends'] += 1
                        say(f'SUSPEND {ident}: {why}')
                elif not want and st['suspended']:
                    if proc.is_running():
                        proc.resume()
                        stats['suspended_seconds'] += time.time() - t_susp
                        st['suspended'] = False
                        say(f'RESUME {ident}: hot {v[0]} memj {v[1]}' if v else f'RESUME {ident}')
                elif st['suspended'] and time.time() - last_note >= 300:   # review G-006: say it, do not go silent
                    last_note = time.time()
                    say(f'still suspended ({time.time() - t_susp:.0f} s) {ident}: {why}')
                in_row = 0
            except Exception as error:   # noqa: BLE001 - any poll error is logged and counted; the cap fails closed
                stats['errors'] += 1
                in_row += 1
                say(f'guard poll error {type(error).__name__}: {error} ({in_row} in a row, cap {ERROR_CAP})')
                if in_row >= ERROR_CAP:
                    abort = f'{in_row} poll errors in a row, last {type(error).__name__}: {error}'
                    break
            if (a.test_hard_exit_after is not None and st['suspended']
                    and time.time() - t_susp >= a.test_hard_exit_after):
                say(f'TEST: guard ends itself with TerminateProcess now (what taskkill /F does); {ident} stays suspended')
                log.close()
                k32.TerminateProcess(me, 9)
            time.sleep(2)
    except BaseException as error:   # noqa: BLE001 - anything that escapes the loop ends the guard fail closed
        abort = f'unexpected {type(error).__name__}: {error}'
    finally:
        code = child.poll()
        exit_code = child.returncode if code is not None else EXIT_ABORT
        if code is None and st['ctrl'] is not None:
            say(f'console event {st["ctrl"]}: guard exits; trainer ({ident}) left running to take the same event')
            exit_code = EXIT_CONSOLE
        elif code is None:
            abort = abort or 'guard loop ended while the trainer runs'
            try:
                if not st['suspended'] and proc.is_running():
                    proc.suspend()
                    st['suspended'] = True
                say(f'ABORT: {abort}. Trainer LEFT SUSPENDED (fail closed): {ident}. Check the GPU, then resume with '
                    f'o30_gpu_guard.py --resume-pid {child.pid} --create-time {proc.create_time():.3f} (or end it). '
                    f'No end line written.')
            except psutil.Error as error:
                say(f'ABORT: {abort}. Suspending the trainer FAILED ({type(error).__name__}: {error}): {ident} may '
                    f'run UNGUARDED. No end line written.')
        else:
            if st['suspended']:
                stats['suspended_seconds'] += time.time() - t_susp
            say(f'end: trainer exit {code}, suspends {stats["suspends"]}, suspended {stats["suspended_seconds"]:.0f} s, '
                f'poll errors {stats["errors"]}')
        log.close()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
