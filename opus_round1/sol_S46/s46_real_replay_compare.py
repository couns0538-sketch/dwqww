#!/usr/bin/env python3
"""s46_real_replay_compare.py (S46, opus 2026-10-27): compare the decision sequence of the REAL autopromote.log (a read-only
copy) in a time window with the simulator's log of the replay fixture. Decisions compared, in order: HOLD (first held
chain), NOT eligible, race pick winner, promote, RH-Q2 rework, REBUILT gates. Exit 0 if equal."""
import argparse
import re
import sys

REAL = [(re.compile(r'PROMOTE_HOLD on \S+: eligible chain\(s\) (\S+?)\+'), 'HOLD'),
        (re.compile(r'\| chain (\S+?)\+\S+: NOT eligible'), 'INELIGIBLE'),
        (re.compile(r'race pick decision: winner (\S+)'), 'PICK'),
        (re.compile(r'promote candidate (AUTOLOCK_\S+) from'), 'PROMOTE'),
        (re.compile(r'STEP REWORK-LIST (\S+) \(RH-Q2'), 'REWORK'),
        (re.compile(r'\|\s+REBUILT (\S+) ->'), 'REBUILD')]
SIM = re.compile(r'^(\S+) \| (HOLD|INELIGIBLE|PICK|PROMOTE|REWORK|REBUILD) \| (\S+?)(?:\+\S+)? \|')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--real', required=True)
    ap.add_argument('--sim', required=True)
    ap.add_argument('--start', required=True, help='e.g. "2026-10-25 15:40"')
    ap.add_argument('--end', required=True)
    a = ap.parse_args()
    real = []
    for line in open(a.real, encoding='utf-8-sig', errors='replace'):
        ts = line[:16]
        if not (a.start <= ts <= a.end) or ('ALERT' in line[:80]):
            continue
        for rx, kind in REAL:
            m = rx.search(line)
            if m and not (kind == 'HOLD' and 'ALERT:' in line):
                real.append((kind, m.group(1)))
    sim = []
    for line in open(a.sim, encoding='utf-8'):
        m = SIM.match(line)
        if m and a.start.replace(' ', 'T') <= m.group(1) <= a.end.replace(' ', 'T'):
            sim.append((m.group(2), m.group(3)))
    n = max(len(real), len(sim))
    ok = real == sim
    print(f'real decisions {len(real)}, simulated {len(sim)}: {"IDENTICAL" if ok else "DIFFERENT"}')
    for i in range(n):
        r = real[i] if i < len(real) else ('-', '-')
        s = sim[i] if i < len(sim) else ('-', '-')
        print(f'{"  " if r == s else "!!"} {i + 1:2d} real {r[0]:<10} {r[1]:<45} sim {s[0]:<10} {s[1]}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
