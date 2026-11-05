#!/usr/bin/env python3
"""handbacks.py - print the structured hand-backs of finished workflow agents (research + verify) compactly.

usage: python -I -B handbacks.py <workflow transcript dir> [<more dirs>] [--json OUT]
Reads journal.jsonl ("result" records) and agent-*.meta.json (labels); prints per agent: label, then per card
id | status | source number | Forge estimate | effort | gate route, dead ends, pending; for verifiers the counts,
corrections, unverifiable items and violations. --json writes all results to one file (for the report tables).
"""
import glob
import json
import os
import sys


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    args = sys.argv[1:]
    out = None
    if '--json' in args:
        i = args.index('--json')
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
    allres = []
    for d in args:
        labels = {}
        for m in glob.glob(os.path.join(d, 'agent-*.meta.json')):
            aid = os.path.basename(m)[len('agent-'):-len('.meta.json')]
            labels[aid] = json.load(open(m, encoding='utf-8')).get('description', '?')
        jp = os.path.join(d, 'journal.jsonl')
        if not os.path.exists(jp):
            continue
        for line in open(jp, encoding='utf-8'):
            rec = json.loads(line)
            if rec.get('type') != 'result':
                continue
            label = labels.get(rec.get('agentId'), rec.get('agentId'))
            r = rec.get('result')
            allres.append({'label': label, 'result': r})
            print(f'=== {label}')
            if not isinstance(r, dict):
                print(f'  (non-structured result) {str(r)[:300]}')
                continue
            for c in r.get('cards', []):
                print(f"  {c.get('id')} | {c.get('status', '')[:30]} | {c.get('title', '')[:70]}")
                for k in ('source_number', 'forge_estimate', 'effort', 'gate_route'):
                    if c.get(k):
                        print(f'      {k}: {c[k][:260]}')
            for k in ('deliverables', 'dead_ends', 'pending', 'corrected', 'unverifiable', 'violations'):
                for x in r.get(k, []) or []:
                    print(f'  {k}: {str(x)[:260]}')
            for k in ('checked', 'confirmed', 'lint_clean', 'sources_used'):
                if k in r:
                    print(f'  {k}: {r[k]}')
            if r.get('summary'):
                print(f"  summary: {r['summary'][:600]}")
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(allres, f, indent=1)


if __name__ == '__main__':
    main()
