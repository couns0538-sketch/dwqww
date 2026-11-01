"""Freeze a phase-balanced clock fixture without consulting ON timing outcomes."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    source, output = map(Path, sys.argv[1:3])
    seed = 81230
    buckets = [set(), set(), set()]
    for line in source.read_text().splitlines():
        row = json.loads(line)
        ply = row['ply']
        buckets[0 if ply < 30 else 1 if ply < 80 else 2].add(row['fen'])
    key = lambda fen: hashlib.sha256(f'{seed}\n{fen}'.encode()).hexdigest()
    ordered = [sorted(bucket, key=key) for bucket in buckets]
    selected = [ordered[phase][i] for i in range(20) for phase in range(3)]
    # Runner applies its separately recorded seed to choose the fixed 20/50 subset.
    output.mkdir(parents=True, exist_ok=False)
    fixture = output/'positions.epd'
    fixture.write_text('\n'.join(selected)+'\n', encoding='ascii', newline='\n')
    (output/'fixture.json').write_text(json.dumps(dict(seed=seed,
        source=str(source), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(), count=60,
        selection='SHA256 order within ply<30 /30..79 /80+; round robin phases; no ON results used',
        purpose='Liveness and hard-cap mechanism tests, not predictive validation or strength'), indent=2)+'\n')


if __name__ == '__main__':
    main()
