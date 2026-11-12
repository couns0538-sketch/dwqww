#!/usr/bin/env python3
"""abba_fair.py - JOB D (own code, 2026-11-11): quiet paired A/B timing of two UCI engines on one pinned core.

  abba_fair.py --name LABEL --out NEW_DIR --a EXE --b EXE [--a-opt "setoption ..."]... [--b-opt "setoption ..."]...
               [--slots 16] [--bench 20] [--cpu 8] [--priority normal|high] [--same-nodes] [--evalbench FENS --reps N]

Protocol (fixed before the first measurement, see fair_eval/REPORT.md):
  - every run is a fresh process: uci, Threads 1, Hash 16, OwnBook false, the arm's options, isready, `bench D`, quit;
  - the engine process is pinned to ONE logical CPU (--cpu) before it receives any input; the driver itself sits
    on CPUs 0-1; nothing else of this job runs meanwhile. Priority: Normal by default since 2026-11-12 (the safety
    review the owner passed on that day flagged High priority as against the owner's preference); every
    summary.json written before that date was measured with High, and --priority high repeats that protocol;
  - one untimed warm-up run per arm, then --slots slots; slot i runs both arms once, order A,B for even i and B,A
    for odd i (two consecutive slots = one ABBA block, so a linear drift cancels);
  - ONE PAIR = the two runs of one slot; pair ratio = value(B) / value(A);
  - value = nodes * 1000 / time_ms from the engine's own bench line (NPS). With --evalbench the value is the
    engine's nanoseconds per static evaluation (two values: root, warm), so the ratio is a COST ratio.
  - --same-nodes: every run of both arms must report the same node count (deterministic same-evaluation control).
Outputs in --out (refused when it exists): runs.tsv (every sample), summary.json, load.txt.
Summary: geometric mean of the pair ratios, two-sided 95 % Student-t interval on the log ratios, median, min, max,
sample SD of the ratios, elapsed seconds.
"""
import argparse
import ctypes
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
        31: 2.040, 32: 2.037, 47: 2.012, 63: 1.998}
K32 = ctypes.windll.kernel32
K32.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
K32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
K32.GetCurrentProcess.restype = ctypes.c_void_p
PRIORITY = {'normal': 0x20, 'high': 0x80}   # Windows priority classes


def busy_percent(seconds=1.0):
    """Whole-machine CPU busy % over `seconds` (GetSystemTimes)."""
    def snap():
        i, k, u = ctypes.c_uint64(), ctypes.c_uint64(), ctypes.c_uint64()
        K32.GetSystemTimes(ctypes.byref(i), ctypes.byref(k), ctypes.byref(u))
        return i.value, k.value + u.value
    i0, t0 = snap()
    time.sleep(seconds)
    i1, t1 = snap()
    return 100.0 * (1.0 - (i1 - i0) / max(1, t1 - t0))


def run(exe, opts, command, cpu, priority):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         cwd=os.path.dirname(exe))
    handle = int(p._handle)
    if not K32.SetProcessAffinityMask(handle, 1 << cpu) or not K32.SetPriorityClass(handle, PRIORITY[priority]):
        p.kill()
        raise RuntimeError('could not pin the engine process')
    lines = ['uci', 'setoption name Threads value 1', 'setoption name Hash value 16', 'setoption name OwnBook value false']
    lines += list(opts) + ['isready', command, 'quit']
    out, _ = p.communicate('\n'.join(lines) + '\n', timeout=1800)
    if p.returncode != 0:
        raise RuntimeError(f'{exe} exit {p.returncode}')
    if re.search(r'ERROR|invalid value', out):
        raise RuntimeError(f'{exe}: engine reported an error: ' + out[-300:])
    return out


def t975(df):
    if df in T975:
        return T975[df]
    return 1.96 + 2.4 / df


def summarise(ratios):
    logs = [math.log(r) for r in ratios]
    n = len(logs)
    mean = sum(logs) / n
    sd = statistics.stdev(logs) if n > 1 else 0.0
    half = t975(n - 1) * sd / math.sqrt(n) if n > 1 else float('nan')
    return {'pairs': n, 'geomean': math.exp(mean), 'ci95_low': math.exp(mean - half), 'ci95_high': math.exp(mean + half),
            'median': statistics.median(ratios), 'min': min(ratios), 'max': max(ratios),
            'sd_of_ratios': statistics.stdev(ratios) if n > 1 else 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--a', required=True)
    ap.add_argument('--b', required=True)
    ap.add_argument('--a-opt', action='append', default=[])
    ap.add_argument('--b-opt', action='append', default=[])
    ap.add_argument('--slots', type=int, default=16)
    ap.add_argument('--bench', type=int, default=20)
    ap.add_argument('--cpu', type=int, default=8)
    ap.add_argument('--priority', choices=sorted(PRIORITY), default='normal')
    ap.add_argument('--same-nodes', action='store_true')
    ap.add_argument('--evalbench', default='')
    ap.add_argument('--reps', type=int, default=200)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    os.makedirs(a.out)
    K32.SetProcessAffinityMask(K32.GetCurrentProcess(), 0x3)
    arms = {'A': (os.path.abspath(a.a), a.a_opt), 'B': (os.path.abspath(a.b), a.b_opt)}
    if a.evalbench:
        command = f'evalbench {a.evalbench} {a.reps}'
        metrics = ['root_ns', 'warm_ns']
    else:
        command = f'bench {a.bench}'
        metrics = ['nps']

    def sample(arm):
        exe, opts = arms[arm]
        out = run(exe, opts, command, a.cpu, a.priority)
        if a.evalbench:
            m = re.search(r'evalbench positions (\d+) reps (\d+) root_ns ([\d.eE+-]+) warm_incl_one_refresh_ns ([\d.eE+-]+) sum_root (-?\d+)', out)
            if not m:
                raise RuntimeError('no evalbench line: ' + out[-300:])
            return {'nodes': int(m.group(5)), 'time_ms': 0, 'root_ns': float(m.group(3)), 'warm_ns': float(m.group(4))}
        m = re.findall(r'bench depth (\d+) nodes (\d+) time (\d+)', out)
        if len(m) != 1:
            raise RuntimeError('expected one bench line: ' + out[-300:])
        nodes, ms = int(m[0][1]), int(m[0][2])
        return {'nodes': nodes, 'time_ms': ms, 'nps': nodes * 1000.0 / ms}

    t0 = time.time()
    load = [f'before: machine busy {busy_percent():.1f} %']
    for arm in 'AB':
        sample(arm)  # warm-up, not recorded
    rows = []
    for slot in range(a.slots):
        order = 'AB' if slot % 2 == 0 else 'BA'
        got = {}
        for pos, arm in enumerate(order):
            got[arm] = sample(arm)
            rows.append((slot, order, pos, arm, got[arm]))
    load.append(f'after: machine busy {busy_percent():.1f} %')
    elapsed = time.time() - t0
    with open(os.path.join(a.out, 'runs.tsv'), 'w', encoding='ascii', newline='\n') as f:
        f.write('slot\torder\tposition\tarm\tnodes\ttime_ms\t' + '\t'.join(metrics) + '\n')
        for slot, order, pos, arm, s in rows:
            f.write(f'{slot}\t{order}\t{pos}\t{arm}\t{s["nodes"]}\t{s["time_ms"]}\t' + '\t'.join(f'{s[m]:.3f}' for m in metrics) + '\n')
    nodes = {arm: sorted({s['nodes'] for _, _, _, r, s in rows if r == arm}) for arm in 'AB'}
    summary = {'name': a.name, 'a': arms['A'][0], 'b': arms['B'][0], 'a_options': a.a_opt, 'b_options': a.b_opt,
               'command': command, 'cpu': a.cpu, 'priority': a.priority.capitalize(), 'slots': a.slots, 'elapsed_s': round(elapsed, 1),
               'nodes_a': nodes['A'], 'nodes_b': nodes['B'], 'load': load,
               'pairing': 'pair = the two runs of one slot; ratio = B / A; slot order alternates AB, BA'}
    summary['deterministic'] = len(nodes['A']) == 1 and len(nodes['B']) == 1
    summary['same_nodes'] = nodes['A'] == nodes['B'] and summary['deterministic']
    for m in metrics:
        ratios = []
        for slot in range(a.slots):
            va = [s[m] for sl, _, _, r, s in rows if sl == slot and r == 'A'][0]
            vb = [s[m] for sl, _, _, r, s in rows if sl == slot and r == 'B'][0]
            ratios.append(vb / va)
        summary[m] = summarise(ratios)
        summary[m]['ratios'] = [round(r, 5) for r in ratios]
        summary[m]['mean_a'] = statistics.mean(s[m] for _, _, _, r, s in rows if r == 'A')
        summary[m]['mean_b'] = statistics.mean(s[m] for _, _, _, r, s in rows if r == 'B')
    with open(os.path.join(a.out, 'summary.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(a.out, 'load.txt'), 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(load) + '\n')
    for m in metrics:
        s = summary[m]
        print(f'{a.name} [{m}] B/A geomean {s["geomean"]:.4f} (95% CI {s["ci95_low"]:.4f}-{s["ci95_high"]:.4f}) median '
              f'{s["median"]:.4f} min {s["min"]:.4f} max {s["max"]:.4f} sd {s["sd_of_ratios"]:.4f} pairs {s["pairs"]}; '
              f'A {s["mean_a"]:.0f} B {s["mean_b"]:.0f}; nodes A {nodes["A"]} B {nodes["B"]}; {elapsed:.0f} s; {"; ".join(load)}')
    if not summary['deterministic']:
        print('FAIL: an arm reported different node counts between runs')
        return 3
    if a.same_nodes and not summary['same_nodes']:
        print('FAIL: --same-nodes, but the arms searched different node counts')
        return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
