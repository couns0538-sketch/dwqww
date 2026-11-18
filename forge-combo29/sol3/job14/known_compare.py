import csv
import json
from itertools import zip_longest
from pathlib import Path
import sys

left, right = map(Path, sys.argv[1:3])
check_counts = '--counts' in sys.argv
def load(path):
    with path.open(encoding='ascii', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))
def counts(row, reference):
    if reference:
        marker = row['nc0'].split()
        assert marker[0] == 'NC0' and len(marker) >= 6
        return [int(x) for x in marker[1:6]]
    return [int(row[f'nc{i}']) for i in range(5)]
old, current = load(left), load(right)
first = None
mismatches = 0
for index, (a, b) in enumerate(zip_longest(old, current), 1):
    if (a is None or b is None or any(a[key] != b[key] for key in ('index', 'fen', 'nodes', 'bestmove'))
            or (check_counts and counts(a, True) != counts(b, False))):
        mismatches += 1
        if first is None:
            first = dict(index=index, reference=a, candidate=b)
sums = dict(reference_nodes=sum(int(row['nodes']) for row in old),
            candidate_nodes=sum(int(row['nodes']) for row in current),
            first_three_nodes=[int(row['nodes']) for row in current[:3]])
if check_counts:
    sums['candidate_count_sums'] = [sum(int(row[f'nc{i}']) for row in current) for i in range(5)]
print(json.dumps(dict(old_rows=len(old), candidate_rows=len(current), mismatches=mismatches, first=first, **sums), indent=2))
raise SystemExit(int(mismatches > 0))
