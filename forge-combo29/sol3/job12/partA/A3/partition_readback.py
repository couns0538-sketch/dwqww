from itertools import zip_longest
import json
from pathlib import Path
import re

root = Path('forge-combo29')
job = root / 'sol3/job12/partA'
before = {'k11v': root / 'sol3/job8/step1/trace.jsonl',
          'k13': root / 'sol3/job10/step1/trace.jsonl'}
volatility = re.compile(r' (?:nps|time|hashfull) -?\d+(?= |$)')

def normalized(path, first_game, last_game):
    with path.open(encoding='ascii') as stream:
        for raw in stream:
            row = json.loads(raw)
            if not first_game <= row['game'] <= last_game:
                continue
            if row['last_info']:
                row['last_info'] = volatility.sub('', row['last_info'])
            yield row

for build, original in before.items():
    resized = job / f'A3/{build}/trace.jsonl'
    hash4 = job / f'A1/Hash4/{build}/trace.jsonl'
    for reference, low, high, size in ((original, 0, 29, 16), (hash4, 30, 59, 4)):
        count = 0
        for left, right in zip_longest(normalized(reference, low, high), normalized(resized, low, high)):
            if left != right:
                raise ValueError(f'{build} size {size} first mismatching row: {left!r} vs {right!r}')
            count += 1
        print(f'{build} A3 vs constant Hash {size}, games {low} to {high}, all {count} rows equal')
