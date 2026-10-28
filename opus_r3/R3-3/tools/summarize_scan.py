"""Summarize srand_scan.py outputs (fs and git) into categories for SRAND_CHECK.md.

Usage: python -I -B summarize_scan.py <out_summary.json> <scan1.json> [<scan2.json> ...]
Prints per-category counts and writes the merged used-value set with one example source per value.
"""
import json
import re
import sys

CATS = [
    ('gate RUN_INFO.json', re.compile(r'run_info[^/\\]*\.json', re.I)),
    ('gate RESULT.md', re.compile(r'result\.md$', re.I)),
    ('fastchess config.json (seed)', re.compile(r'[/\\]config\.json$', re.I)),
    ('queue manifest forge_gates*.json (live + backups)', re.compile(r'forge_gates[^/\\]*', re.I)),
    ('queue state / queue log', re.compile(r'forge_queue(_state\.json|\.log)', re.I)),
    ('FORGE_RESULTS / GATE_RESULTS ledgers', re.compile(r'(forge_results|gate_results|auto_results)', re.I)),
    ('chain_gates*.ps1 / *.log (older runners)', re.compile(r'chain_gates', re.I)),
    ('test plans (OPUS_TEST_PLAN / TEST_PLAN_ALL_IDEAS)', re.compile(r'test_plan', re.I)),
    ('SOL_LEFTOVERS / OPUS_PROMPT', re.compile(r'(sol_leftovers|opus_prompt)', re.I)),
    ('job REPORT.md / IDEA_SOURCE.md', re.compile(r'(report|idea_source)[^/\\]*\.md$', re.I)),
    ('skills', re.compile(r'[/\\]skills[/\\]', re.I)),
    ('other', re.compile(r'.')),
]


def cat_of(path):
    for name, rx in CATS:
        if rx.search(path):
            return name
    return 'other'


def main():
    merged = {}
    kinds = {}
    for p in sys.argv[2:]:
        d = json.load(open(p, encoding='utf-8'))
        for v, srcs in d['context'].items():
            for path, kind, snip in srcs:
                is_srand = kind.startswith('srand') or kind.endswith('_column')
                ent = merged.setdefault(v, {'srand_ctx': False, 'cats': set(), 'example': None})
                ent['srand_ctx'] |= is_srand
                c = cat_of(path)
                ent['cats'].add(c)
                if ent['example'] is None or (is_srand and not ent['example'][2]):
                    ent['example'] = [path, snip, is_srand]
                kinds.setdefault(c, set()).add(v)
    srand_vals = sorted(int(v) for v, e in merged.items() if e['srand_ctx'])
    seed_vals = sorted(int(v) for v, e in merged.items() if not e['srand_ctx'])
    print(f'srand-context values: {len(srand_vals)}; seed-only values: {len(seed_vals)}')
    for c, vs in sorted(kinds.items(), key=lambda kv: -len(kv[1])):
        print(f'  {c}: {len(vs)} distinct values')
    out = {'srand_context_values': srand_vals, 'seed_only_values': seed_vals,
           'per_category_counts': {c: len(vs) for c, vs in kinds.items()},
           'examples': {v: e['example'] for v, e in merged.items()}}
    with open(sys.argv[1], 'w', newline='\n', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1)


if __name__ == '__main__':
    main()
