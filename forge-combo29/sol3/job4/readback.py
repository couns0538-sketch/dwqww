import collections
import json
import re
import sys
from pathlib import Path

job = Path(sys.argv[1])
positions = Path(sys.argv[2]).read_text().splitlines()
commands = {'B2':'go nodes 20000', 'B3':'go softnodes 2000', 'N2':'go nodes 20000',
            'N3':'go softnodes 2000', 'ND':'go depth 8'}
found = {}
soft_counts = {}

for arm in ('10','11','P'):
    for cell, command in commands.items():
        tag = f'{arm}_{cell}'
        raw = job / f'identity_{tag}.stdout.txt'
        rows_path = job / f'rows_{tag}.txt'
        if not raw.exists() or not rows_path.exists():
            continue
        rows_file = [tuple(line.split()) for line in rows_path.read_text().splitlines()]
        transcript = (job / f'identity_{tag}.commands.txt').read_text().splitlines()
        assert transcript.count('uci') == 1 and transcript[-1] == 'quit', tag
        first_game = transcript.index('ucinewgame')
        expected_commands = [part for fen in positions for part in ('ucinewgame', 'isready', f'position fen {fen}', command)]
        assert transcript[first_game:-1] == expected_commands, tag
        stderr = (job / f'identity_{tag}.stderr.txt').read_text()
        assert not re.search(r'unknown option|invalid value|\bERROR\b', stderr, re.I), tag
        search_line = None
        final_count = None
        reconstructed = []
        finals = []
        net_activated = 0
        for line in raw.read_text().splitlines():
            assert not re.search(r'unknown option|invalid value|\bERROR\b', line, re.I), (tag, line)
            if line.startswith('info string NNUE v3 active:'):
                assert re.search(r'\bhidden 768\b.*\bchecksum 30ab43b4ba5db5f3\b', line), (tag,line)
                net_activated += 1
            elif line.startswith('info depth '):
                search_line = line.split()
            elif line.startswith('info string softnodes nodes '):
                final_count = int(line.split()[-1])
            elif line.startswith('bestmove '):
                index = str(len(reconstructed)+1)
                best = line.split()[1]
                if search_line is None:
                    raise ValueError(f'{tag} row {index}: no depth information before {best}')
                depth = search_line[2]
                nodes = search_line[search_line.index('nodes')+1]
                if 'pv' in search_line and search_line[-1] != 'pv':
                    pv_head = search_line[search_line.index('pv')+1]
                else:
                    pv_head = '-'
                reconstructed.append((index, depth, nodes, pv_head, best))
                finals.append(final_count)
                search_line = None
                final_count = None
        assert net_activated == int(cell.startswith('N')), (tag, net_activated)
        assert len(reconstructed) == len(positions) == len(rows_file), (tag, len(reconstructed), len(rows_file))
        assert reconstructed == rows_file, tag
        found[(arm,cell)] = reconstructed
        soft_counts[(arm,cell)] = finals


def compare(first, second):
    reference, alternate = found.get(first), found.get(second)
    if reference is None or alternate is None:
        return None, None
    differences = [(before,after) for before,after in zip(reference,alternate,strict=True) if before != after]
    return len(reference)-len(differences), differences[0] if differences else None


summary = {}
print('| Tree | Cell | Rows equal to k10 | First difference (k10 → tree) |')
print('| --- | --- | ---: | --- |')
for arm in ('10','11','P'):
    for cell in commands:
        equal, first = compare(('10',cell),(arm,cell))
        against_11, first_against_11 = compare(('11',cell),(arm,cell))
        equal_display = '—' if equal is None else f'{equal}/{len(positions)}'
        diff_display = f'{first[0][0]} (`{" ".join(first[0][1:])}` → `{" ".join(first[1][1:])}`)' if first else '—'
        print(f'| {arm} | {cell} | {equal_display} | {diff_display} |')
        summary[f'{arm}_{cell}'] = {'equal_to_10': equal, 'first_vs_10': first,
                                     'equal_to_11': against_11,'first_vs_11': first_against_11}
for cell in ('B3','N3'):
    if all((arm,cell) in soft_counts for arm in ('10','11','P')):
        a, b, p = [soft_counts[(arm,cell)] for arm in ('10','11','P')]
        changes = collections.Counter((left,right) for left,right in zip(b,p,strict=True) if left != right)
        first_changed = next((index for index,(left,right) in enumerate(zip(b,p,strict=True),1) if left != right), None)
        summary[f'{cell}_soft_final'] = {'k10_k11_all_equal': a == b,
                       'k11_hard_cap_8000': b.count(8000), 'P_8001': p.count(8001),
                       'first_changed_row': first_changed,
                       'changes': [{'k11': x,'P': y, 'count': count} for (x,y),count in changes.items()]}
(job/'table_evidence.json').write_text(json.dumps(summary,indent=2)+'\n')
