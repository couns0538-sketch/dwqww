from pathlib import Path
import sys

from compare_limits import read_arm, read_positions

fixture, ref_root, candidate_root = map(Path, sys.argv[1:4])
cell = sys.argv[4]
positions = read_positions(fixture)
baseline = read_arm(ref_root, 50000, '11', cell, positions)
candidate = read_arm(candidate_root, 50000, '11', cell, positions)
changes = [(i, old, new) for i, (old, new) in enumerate(zip(baseline, candidate, strict=True), 1)
           if old.row(i) != new.row(i)]
print(f'{cell} nodes=50000 rows={len(positions)} equal={len(positions) - len(changes)} '
      f'k11f_at_cap={sum(row.final_nodes == 50000 for row in baseline)} '
      f'k11vf_at_cap={sum(row.final_nodes == 50000 for row in candidate)}')
if changes:
    index, old, new = changes[0]
    print(f'First differing FEN {index}: {positions[index - 1]}')
    print('k11f row    ', old.row(index))
    print('k11f info   ', old.last_info)
    print('k11vf row   ', new.row(index))
    print('k11vf info  ', new.last_info)
    raise SystemExit(1)
