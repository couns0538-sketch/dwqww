"""Verify that both side processes received quit after every audited game's final search."""
import json
from pathlib import Path
import sys

snapshot = json.loads(Path(sys.argv[1]).read_text())
assert snapshot['final'] and not snapshot['excluded_stages']
root = Path(sys.argv[2])
games = 0
for b in snapshot['common_block_ids']:
    for arm in snapshot['arms']:
        for path in sorted((root / f'block{b:03d}' / arm).glob('g*/wire.txt')):
            with path.open('rb') as wire:
                wire.seek(-32, 2)
                assert wire.read().endswith(b'\nW > quit\nB > quit\n'), path
            games += 1
assert games == sum(s['games'] for s in snapshot['arms'].values())
print(f'Each of {games} completed match wire files ends with W > quit and B > quit after the final search ({2*games} explicit shutdown commands).')
