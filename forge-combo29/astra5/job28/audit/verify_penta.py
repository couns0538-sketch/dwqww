"""Verify matched-pair Elo directly from the compact game table, without importing scoring code."""
import csv
import json
import math
from pathlib import Path
from statistics import NormalDist
import sys


snapshot = json.loads(Path(sys.argv[1]).read_text())
archive = Path(sys.argv[2])
for name, expected in snapshot['arms'].items():
    games = {}
    for block in snapshot['common_block_ids']:
        with (archive / f'block{block:03d}' / name / 'games.tsv').open() as source:
            for record in csv.DictReader(source, delimiter='\t'):
                gid = int(record['game'])
                assert gid not in games
                a_white = record['white'] == 'A'
                first_score = {'1-0': 1, '0-1': 0, '1/2-1/2': 0.5}[record['result']]
                games[gid] = first_score if a_white else 1 - first_score
    penta = [0] * 5
    for opening in snapshot['common_opening_ids']:
        penta[int(2 * (games[2 * opening - 1] + games[2 * opening]))] += 1
    assert penta == expected['penta']
    assert [list(games.values()).count(x) for x in (1, 0, 0.5)] == expected['A_WLD']
    total = sum(penta)
    point = sum(i*cnt for i, cnt in enumerate(penta))/(4*total)
    var = sum(cnt*(i/4-point)**2 for i, cnt in enumerate(penta))/total
    delta = NormalDist().inv_cdf(.975)*math.sqrt(var/total)
    def convert(score): return 400*math.log10(score/(1-score))
    elo = convert(point)
    halfwidth = (convert(point+delta)-convert(point-delta))/2
    recomputed = [elo, elo-halfwidth, elo+halfwidth]
    maxerror = max(abs(x-y) for x, y in zip(recomputed, expected['elo_lower_upper']))
    assert maxerror < 1e-9, (name, maxerror)
    print(f'{name}: {len(games)} committed-format game rows; W-L-D and pentanomial exact; maximum Elo discrepancy {maxerror:.3g}.')
