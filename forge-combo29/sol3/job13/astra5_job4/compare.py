import csv
import json
from pathlib import Path
import sys

job = Path(sys.argv[1])
compare = job / 'astra5_job4'
def load(path):
    with path.open(encoding='ascii', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))

def slots(row):
    return [int(row[f'nc{number}']) for number in range(5)]

def reference_slots(row):
    fields = row['nc0'].split()
    assert fields[0] == 'NC0' and len(fields) >= 6
    return [int(count) for count in fields[1:6]]

embedded = load(job / 'C1/counted/rows.tsv')
net = load(job / 'C2/counted/rows.tsv')
reference = load(compare / 'G_F0.tsv')
assert len(embedded) == len(net) == len(reference) == 353
for index, (a, b) in enumerate(zip(embedded, reference, strict=True), 1):
    if any(a[key] != b[key] for key in ('index', 'fen', 'nodes', 'bestmove')) or slots(a) != reference_slots(b):
        raise ValueError(f'First G mismatch at {index}: own={a!r} reference={b!r}')

p = load(job / 'C0/P_builtin/rows.tsv')[-1]
ref_p, = load(compare / 'P_F0.tsv')
assert all(p[key] == ref_p[key] for key in ('fen', 'nodes', 'bestmove'))
assert slots(p) == reference_slots(ref_p)
result = {'comparison_equal_G_rows': 353, 'P_depth_16_vector': slots(p)}
for arm, rows in [('local_C1', embedded), ('local_C2', net), ('astra5_G_F0', reference)]:
    counts = [reference_slots(row) if arm.startswith('astra5') else slots(row) for row in rows]
    nodes = sum(int(row['nodes']) for row in rows)
    totals = [sum(column) for column in zip(*counts, strict=True)]
    result[arm] = dict(nodes=nodes, sums=totals, per_1000_nodes=[1000 * value / nodes for value in totals],
                       positions_with_4=sum(row[4] > 0 for row in counts),
                       fraction_of_shallow_cutoffs=totals[4] / totals[3])
print(json.dumps(result, indent=2))
