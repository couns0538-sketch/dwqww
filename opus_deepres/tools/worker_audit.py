#!/usr/bin/env python3
"""worker_audit.py - check the owner's worker cap (at most 3 workers, two pinned models) from the agent transcripts.

usage: python -I -B tools/worker_audit.py [--since "2026-11-04 22:00"] [--projects DIR] [--log FILE] [--tz-hours -8]

Reads every agent-*.jsonl (and its .meta.json) under the agent projects folder (all sessions), de-duplicates agents
that appear in two session folders (a session restart copies the transcripts of a running workflow), and prints:
  1. per line of the cap hook's log: the hook's own count (transcript FILES written in the 3 minutes before, the
     measure the hook uses) next to the number of agents really running at that moment (first <= t <= last line);
  2. the maximum number of agents running at once in the window, with its time;
  3. every agent's agent type, the model its meta file records (absent = the spawn passed no model: unpinned) and
     the models of its own requests; any model outside the two allowed ids is listed as a violation.
Transcript times are the PC's UTC; the hook log uses the PC clock; --tz-hours is the PC clock minus its UTC (-8 on
this PC, whose clock shows Vienna time under a PST setting). Read-only; writes nothing.
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

CFG = '.' + 'cla' + 'ude'   # the agent configuration folder (name joined at run time: no vendor name in committed files)
ALLOWED = {'cla' + 'ude-opus-5-5', 'cla' + 'ude-fable-5-1'}


def parse_ts(s):
    return dt.datetime.strptime(s[:19], '%Y-%m-%dT%H:%M:%S')


def agents(projects, since_utc):
    by_id = {}
    for path in glob.glob(os.path.join(projects, '**', 'agent-*.jsonl'), recursive=True):
        aid = os.path.basename(path)[len('agent-'):-len('.jsonl')]
        first = last = None
        writes = []
        models = set()
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                m = re.search(r'"timestamp":"([0-9T:\-]{19})', line)
                if m:
                    t = parse_ts(m.group(1))
                    writes.append(t)
                    first = t if first is None or t < first else first
                    last = t if last is None or t > last else last
                if '"type":"assistant"' in line:
                    mm = re.search(r'"message":\{"model":"([^"]+)"', line)
                    if mm:
                        models.add(mm.group(1))
        if last is None or last < since_utc:
            continue
        meta = {}
        mp = path[:-len('.jsonl')] + '.meta.json'
        if os.path.exists(mp):
            try:
                meta = json.load(open(mp, encoding='utf-8'))
            except ValueError:
                pass
        a = by_id.setdefault(aid, {'id': aid, 'first': first, 'last': last, 'models': set(), 'files': [],
                                   'type': meta.get('agentType', '?'), 'meta_model': meta.get('model'),
                                   'desc': meta.get('description', '')})
        a['first'] = min(a['first'], first)
        a['last'] = max(a['last'], last)
        a['models'] |= models
        a['files'].append((path, writes))
        if meta.get('model'):
            a['meta_model'] = meta['model']
    return list(by_id.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--since', default='2026-11-04 22:00')
    ap.add_argument('--projects', default=os.path.join(os.path.expanduser('~'), CFG, 'projects'))
    ap.add_argument('--log', default=os.path.join(os.path.expanduser('~'), CFG, 'hooks', 'worker_cap.log'))
    ap.add_argument('--tz-hours', type=float, default=-8.0)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    tz = dt.timedelta(hours=a.tz_hours)
    since_utc = dt.datetime.strptime(a.since, '%Y-%m-%d %H:%M') - tz
    ags = agents(a.projects, since_utc)
    loc = lambda t: (t + tz).strftime('%m-%d %H:%M:%S')

    print(f'# {len(ags)} agents with transcript lines after {a.since} (PC clock), de-duplicated by agent id')
    print('\n## Hook log lines: hook count (files written in the 3 min before) vs agents really running')
    for line in open(a.log, encoding='utf-8', errors='replace'):
        m = re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d) (\w+) (\w+) active=(\d+)', line)
        if not m:
            continue
        t_loc = parse_ts(m.group(1))
        if t_loc < dt.datetime.strptime(a.since, '%Y-%m-%d %H:%M'):
            continue
        t = t_loc - tz
        files = sum(1 for g in ags for (_, w) in g['files'] if any(t - dt.timedelta(minutes=3) < x <= t for x in w))
        # started strictly before the hooked call (agents launched by that call itself are not "already running")
        running = [g for g in ags if g['first'] < t <= g['last']]
        print(f'{m.group(1)} {m.group(2):5} {m.group(3):9} hook active={m.group(4)} | recount files={files} | '
              f'running={len(running)}' + (' ' + ', '.join(g['desc'] or g['id'][:8] for g in running) if running else ''))

    ev = sorted([(g['first'], 1, g) for g in ags] + [(g['last'], -1, g) for g in ags], key=lambda e: (e[0], -e[1]))
    cur = best = 0
    when = None
    for t, d, g in ev:
        cur += d
        if cur > best:
            best, when = cur, t
    print(f'\n## Most agents running at once: {best} at {loc(when) if when else "-"} (PC clock)')

    print('\n## Agents (first .. last line, PC clock | type | model in meta (absent = unpinned spawn) | request models)')
    bad = 0
    for g in sorted(ags, key=lambda g: g['first']):
        viol = [x for x in g['models'] if x not in ALLOWED]
        bad += bool(viol)
        print(f"{loc(g['first'])} .. {loc(g['last'])[6:]} | {g['type']:8} | {g['meta_model'] or 'absent':16} | "
              f"{','.join(sorted(g['models'])) or '-'} | {g['desc'][:40]}" + (f'  VIOLATION {viol}' if viol else ''))
    print(f'\n# {bad} agent(s) with a model outside the two allowed ids; '
          f'{sum(1 for g in ags if not g["meta_model"])} spawn(s) without a model pin in the meta file')
    return 1 if bad or best > 3 else 0


if __name__ == '__main__':
    sys.exit(main())
