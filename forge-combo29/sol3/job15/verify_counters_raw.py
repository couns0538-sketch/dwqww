import csv
import json
from pathlib import Path
import re
import sys

out = Path(sys.argv[1])
required = int(sys.argv[2])
with (out / 'rows.tsv').open(newline='', encoding='ascii') as stream:
    rows = list(csv.DictReader(stream, delimiter='\t'))
pattern = re.compile(r'^NC0 ((?:\d+ ){4}\d+)$')
counts = []
nodes = []
last_nodes = None
with (out / 'engine.stdout.txt').open(encoding='ascii') as stream:
    for raw in stream:
        line = raw.rstrip('\n')
        if line.startswith('info depth '):
            match = re.search(r'\bnodes (\d+)\b', line)
            last_nodes = int(match[1]) if match else None
        if line.startswith('bestmove '):
            if last_nodes is None:
                raise ValueError(f'Missing last iteration count before {line!r}')
            marker = next(stream).rstrip('\n')
            parsed = pattern.fullmatch(marker)
            if parsed is None:
                raise ValueError(f'Expected NC0 immediately after bestmove, got {marker!r}')
            counts.append(list(map(int, parsed[1].split())))
            nodes.append(last_nodes)
            last_nodes = None
        elif line.startswith('NC0 '):
            raise ValueError(f'Unexpected extra counter line: {line!r}')
if len(rows) != required or len(counts) != required:
    raise ValueError(f'Expected {required} lines, got TSV={len(rows)} raw={len(counts)}')
for index, (row, count, node_count) in enumerate(zip(rows, counts, nodes, strict=True), 1):
    if count != [int(row[f'nc{i}']) for i in range(5)] or node_count != int(row['nodes']):
        raise ValueError(f'Raw UCI differs from count/label table at row {index}')
node_sum = sum(nodes)
total = [sum(row) for row in zip(*counts, strict=True)]
print(json.dumps({'lines': len(counts), 'nodes': node_sum, 'sums': total,
                  'per_1000_nodes': [1000 * count / node_sum for count in total],
                  'last_row_counters': counts[-1]}, indent=2))
