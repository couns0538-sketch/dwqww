"""Dump the gate manifest copy (forge_gates.json, read from scratch) as a compact table.

Usage: python -I -B dump_manifest.py <forge_gates.json copy> [--fields]
Read-only on its input; prints to stdout.
"""
import json
import sys
from collections import Counter


def load(path):
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    return json.loads(raw.decode('utf-8'))


def main():
    path = sys.argv[1]
    man = load(path)
    gates = man['gates']
    print('top-level keys:', sorted(man.keys()))
    print('base:', json.dumps(man.get('base'), ensure_ascii=True))
    print('n gates:', len(gates))
    if '--fields' in sys.argv:
        c = Counter()
        for g in gates:
            c.update(g.keys())
        for k, v in sorted(c.items()):
            print(f'  field {k}: {v}')
        return
    for g in gates:
        opts = ' '.join(g.get('options') or [])
        sp = g.get('sprt')
        print('|'.join(str(x) for x in [
            g.get('gate'), g.get('tag'), g.get('srand'), g.get('openings_start'),
            g.get('concurrency'), g.get('tc'), json.dumps(sp) if sp else '',
            g.get('status', ''), g.get('exe'), opts,
            (g.get('base_override') or {}).get('name', '')]))


if __name__ == '__main__':
    main()
