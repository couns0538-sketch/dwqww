#!/usr/bin/env python3
"""S07 fix-up driver (S07-1 / S07-2): repeated, interleaved WAC300 screens with Sol's unchanged harness, plus
the load evidence needed to read them.

Each screen is one call of Sol's tool `forge_sol_S07_screen_sweep_20261026.py wac300` (sha256 7262dcf8...,
unchanged: fresh bare `bench 11` process, then one UCI process; per position ucinewgame + Clear Hash +
`go movetime T`; final bestmove scored against bm/am). This driver only orders the screens, samples the machine
load while they run, and summarizes:
  - per screen: solved/300, wall time, and from the raw engine stdout the last `info` line before every
    bestmove (depth, nodes, time, nps) -> median nps, mean depth, total nodes;
  - per movetime and engine: mean score, range (max - min), the per-screen scores;
  - load: system CPU busy % (GetSystemTimes, every --sample-seconds), free RAM, and process snapshots
    (top CPU users, forge/fastchess/python counts) at each screen start/end.
A score difference within the observed repeat range (typically 1-3 points) is noise, not a strength signal.
No Elo or speed claim follows from a screen.

usage:
  forge_sol_S07_wac_interleave_v2.py --tool SOL_TOOL --suite WAC300 --out NEW_DIR \
      --arm lock=EXE[:OPTIONS_JSON] --arm cand=EXE[:OPTIONS_JSON] --movetimes 100,1000 --reps 3 [--order interleaved|blocked]
  Screens run movetime by movetime; within a movetime `interleaved` runs (lock, cand) x reps, `blocked` runs all
  reps of the first arm, then the next arm.
"""
import argparse
import ctypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import threading
import time

INFO = re.compile(r'^info depth (\d+) .*?\bnodes (\d+) nps (\d+) .*?\btime (\d+)\b')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


class FILETIME(ctypes.Structure):
    _fields_ = [('lo', ctypes.c_uint32), ('hi', ctypes.c_uint32)]


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [('dwLength', ctypes.c_uint32), ('dwMemoryLoad', ctypes.c_uint32),
                ('ullTotalPhys', ctypes.c_uint64), ('ullAvailPhys', ctypes.c_uint64),
                ('ullTotalPageFile', ctypes.c_uint64), ('ullAvailPageFile', ctypes.c_uint64),
                ('ullTotalVirtual', ctypes.c_uint64), ('ullAvailVirtual', ctypes.c_uint64),
                ('ullAvailExtendedVirtual', ctypes.c_uint64)]


def system_times():
    idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
    ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user))
    v = lambda t: (t.hi << 32) | t.lo  # noqa: E731
    return v(idle), v(kernel), v(user)


def free_ram_gb():
    m = MEMORYSTATUSEX()
    m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys / 2**30


class Sampler(threading.Thread):
    """System CPU busy % over each interval (kernel time includes idle time on Windows)."""

    def __init__(self, path, seconds):
        super().__init__(daemon=True)
        self.path, self.seconds, self.stop_event, self.label = path, seconds, threading.Event(), 'idle'
        self.rows = []

    def run(self):
        prev = system_times()
        with open(self.path, 'a', encoding='utf-8') as out:
            while not self.stop_event.wait(self.seconds):
                cur = system_times()
                d_idle, d_kernel, d_user = (c - p for c, p in zip(cur, prev))
                prev = cur
                total = d_kernel + d_user
                busy = 100.0 * (total - d_idle) / total if total else float('nan')
                row = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
                       'screen': self.label, 'cpu_busy_pct': round(busy, 1), 'free_ram_gb': round(free_ram_gb(), 2)}
                self.rows.append(row)
                out.write(json.dumps(row) + '\n')
                out.flush()


def process_snapshot():
    """Top CPU users and process counts (PowerShell, read-only)."""
    script = ("$p = Get-Process; "
              "$top = $p | Sort-Object CPU -Descending | Select-Object -First 12 Name,Id,"
              "@{n='cpu_s';e={[math]::Round($_.CPU,0)}},@{n='prio';e={\"$($_.PriorityClass)\"}}; "
              "$cnt = @{}; foreach ($n in 'forge','fastchess','python','cmake','ninja','g++','cc1plus') "
              "{ $cnt[$n] = @($p | Where-Object { $_.Name -like \"$n*\" }).Count }; "
              "[pscustomobject]@{top=$top; counts=$cnt} | ConvertTo-Json -Depth 4 -Compress")
    try:
        run = subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True,
                             timeout=60)
        return json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {'error': run.stderr[-500:]}
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {'error': f'{type(exc).__name__}: {exc}'}


def engine_priority(exe_path):
    """Priority class of the processes running exactly this exe path (gate engines run other copies)."""
    target = str(Path(exe_path).resolve()).replace("'", "''")
    script = (f"Get-Process -Name '{Path(exe_path).stem}' -ErrorAction SilentlyContinue | "
              f"Where-Object {{ $_.Path -eq '{target}' }} | "
              "Select-Object Id,@{n='prio';e={\"$($_.PriorityClass)\"}},Path | ConvertTo-Json -Compress")
    try:
        run = subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True,
                             timeout=60)
        return run.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def search_stats(stdout_path):
    """Last info line before each bestmove: depth, nodes, time (ms), nps."""
    rows, last = [], None
    for line in Path(stdout_path).read_text(encoding='utf-8', errors='replace').splitlines():
        m = INFO.match(line)
        if m:
            last = tuple(int(x) for x in m.groups())
        elif line.startswith('bestmove '):
            rows.append(last)
            last = None
    good = [r for r in rows if r]
    if not good:
        return {'positions': len(rows)}
    return {'positions': len(rows), 'with_info': len(good),
            'median_nps': statistics.median(r[2] for r in good),
            'mean_depth': round(statistics.fmean(r[0] for r in good), 2),
            'median_depth': statistics.median(r[0] for r in good),
            'total_nodes': sum(r[1] for r in good),
            'median_nodes': statistics.median(r[1] for r in good),
            'median_time_ms': statistics.median(r[3] for r in good)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tool', type=Path, required=True)
    ap.add_argument('--suite', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--arm', action='append', required=True, help='NAME=EXE[:OPTIONS_JSON]')
    ap.add_argument('--movetimes', default='100,1000')
    ap.add_argument('--reps', type=int, default=3)
    ap.add_argument('--order', choices=('interleaved', 'blocked'), default='interleaved')
    ap.add_argument('--sample-seconds', type=float, default=5.0)
    args = ap.parse_args()
    args.out.mkdir(exist_ok=False)
    arms = []
    for spec in args.arm:
        name, rest = spec.split('=', 1)
        exe, _, options = rest.partition(':{')
        options = json.loads('{' + options) if options else {}
        arms.append({'name': name, 'exe': str(Path(exe).resolve()), 'sha256': sha(exe), 'options': options})
    movetimes = [int(x) for x in args.movetimes.split(',')]
    plan = []
    for mt in movetimes:
        if args.order == 'interleaved':
            plan += [(mt, rep, arm) for rep in range(1, args.reps + 1) for arm in arms]
        else:
            plan += [(mt, rep, arm) for arm in arms for rep in range(1, args.reps + 1)]
    header = {'driver_sha256': sha(__file__), 'tool': str(args.tool.resolve()), 'tool_sha256': sha(args.tool),
              'suite_sha256': sha(args.suite), 'arms': arms, 'movetimes': movetimes, 'reps': args.reps,
              'order': args.order, 'python': sys.version, 'started_utc': datetime.datetime.now(
                  datetime.timezone.utc).isoformat(timespec='seconds'),
              'priority_note': 'run under nice -n 19 (Git Bash): Idle priority class, inherited by the engines',
              'machine_exclusive': 'no (PC runs fastchess gates, NNUE training and self-play permanently)'}
    (args.out / 'plan.json').write_text(json.dumps({**header, 'plan': [(m, r, a['name']) for m, r, a in plan]},
                                                  indent=2) + '\n')
    sampler = Sampler(args.out / 'load_samples.jsonl', args.sample_seconds)
    sampler.start()
    screens = []
    for index, (mt, rep, arm) in enumerate(plan, 1):
        label = f'{index:02d}_{mt}ms_rep{rep}_{arm["name"]}'
        sampler.label = label
        before = process_snapshot()
        n0 = len(sampler.rows)
        t0 = time.monotonic()
        prio = {}
        cmd = [sys.executable, '-B', str(args.tool), 'wac300', '--engine-argv-json', json.dumps([arm['exe']]),
               '--expected-engine-sha256', arm['sha256'], '--reference', 'lock', '--suite', str(args.suite),
               '--movetime-ms', str(mt), '--options-json', json.dumps(arm['options']), '--out', str(args.out / label)]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(min(20.0, 5.0 + mt / 1000.0 * 5))
        prio['during'] = engine_priority(arm['exe'])
        stdout, stderr = proc.communicate()
        wall = time.monotonic() - t0
        after = process_snapshot()
        result_path = args.out / label / 'result.json'
        result = json.loads(result_path.read_text()) if result_path.is_file() else {}
        raw = sorted((args.out / label).glob('*_wac300_fixedtime.stdout'))
        loads = [r['cpu_busy_pct'] for r in sampler.rows[n0:]]
        screen = {'screen': label, 'movetime_ms': mt, 'rep': rep, 'arm': arm['name'], 'exit': proc.returncode,
                  'status': result.get('status'), 'solved': result.get('solved'), 'evaluated': result.get('evaluated'),
                  'illegal_moves': result.get('illegal_moves'), 'first_bare_bench11': result.get('first_bare_bench11_nodes'),
                  'wall_seconds': round(wall, 1), 'search': search_stats(raw[0]) if raw else None,
                  'cpu_busy_pct': {'samples': len(loads), 'mean': round(statistics.fmean(loads), 1) if loads else None,
                                   'min': min(loads) if loads else None, 'max': max(loads) if loads else None},
                  'engine_priority_during': prio['during'], 'processes_before': before, 'processes_after': after,
                  'tool_stdout': stdout.strip()[-400:], 'tool_stderr': stderr.strip()[-400:],
                  'result_sha256': sha(result_path) if result_path.is_file() else None,
                  'solved_ids': sorted(r['id'] for r in result.get('results', []) if r.get('bestmove_allowed'))}
        screens.append(screen)
        with open(args.out / 'screens.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(screen) + '\n')
        s = screen['search'] or {}
        print(f"{label}: {screen['status']} solved {screen['solved']}/300 wall {screen['wall_seconds']}s "
              f"median_nps {s.get('median_nps')} mean_depth {s.get('mean_depth')} cpu_busy {screen['cpu_busy_pct']['mean']}%",
              flush=True)
    sampler.stop_event.set()
    sampler.join(timeout=30)
    summary = {}
    for mt in movetimes:
        for arm in arms:
            rows = [s for s in screens if s['movetime_ms'] == mt and s['arm'] == arm['name']]
            scores = [s['solved'] for s in rows if s['solved'] is not None]
            nps = [s['search']['median_nps'] for s in rows if s['search'] and s['search'].get('median_nps')]
            summary[f'{mt}ms_{arm["name"]}'] = {
                'scores': scores, 'mean': round(statistics.fmean(scores), 2) if scores else None,
                'range': (max(scores) - min(scores)) if scores else None,
                'median_nps_per_screen': nps, 'all_pass': all(s['status'] == 'PASS' for s in rows)}
    if len(arms) == 2:
        for mt in movetimes:
            a, b = (summary[f'{mt}ms_{arm["name"]}'] for arm in arms)
            if a['mean'] is not None and b['mean'] is not None:
                diff = round(b['mean'] - a['mean'], 2)
                noise = max(a['range'], b['range'], 3)
                summary[f'{mt}ms_diff_{arms[1]["name"]}_minus_{arms[0]["name"]}'] = {
                    'mean_diff': diff, 'noise_band_points': noise,
                    'reading': 'within noise' if abs(diff) <= noise else 'outside the observed noise band (screen only)'}
    loads = [r['cpu_busy_pct'] for r in sampler.rows]
    final = {**header, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
             'screens': [{k: v for k, v in s.items() if k not in ('processes_before', 'processes_after')} for s in screens],
             'summary': summary,
             'load_overall': {'samples': len(loads), 'mean': round(statistics.fmean(loads), 1) if loads else None,
                              'min': min(loads) if loads else None, 'max': max(loads) if loads else None}}
    (args.out / 'summary.json').write_text(json.dumps(final, indent=2) + '\n')
    print(json.dumps(summary, indent=1))
    return 0 if all(s['status'] == 'PASS' for s in screens) else 1


if __name__ == '__main__':
    raise SystemExit(main())
