import json
from collections import defaultdict
from hashlib import sha256
from math import ceil
from pathlib import Path
import re

import chess.pgn

raw = Path('raw')
meta = json.loads((raw / 'K26.meta').read_bytes())
pgn = raw / 'K26.pgn'
assert sha256(pgn.read_bytes()).hexdigest() == meta['pgn_sha256']
assert meta['status'] == 'complete' and meta['games_requested'] == 20
groups = defaultdict(list)
times = {'A': [], 'B': []}
with pgn.open() as source:
    while (game := chess.pgn.read_game(source)) is not None:
        assert not game.errors
        headers = game.headers
        assert headers['TimeControl'] == '6+0.06' and headers['Result'] in ('1-0', '1/2-1/2', '0-1')
        assert 'time forfeit' not in headers['Termination'].lower()
        board = game.board()
        points = {'1-0': 2, '1/2-1/2': 1, '0-1': 0}[headers['Result']]
        if headers['White'] == 'B':
            points = 2 - points
        moves = []
        for node in game.mainline():
            sec, millis = re.match(r'^.*?/\d+\s+(\d+)\.(\d{3})s\b', node.comment).groups()
            assert re.search(r'\btl=-?\d+\.\d{3}s\b', node.comment)
            times[headers['White' if board.turn else 'Black']].append(1000 * int(sec) + int(millis))
            moves.append(node.move.uci())
            board.push(node.move)
        assert len(moves) == int(headers['PlyCount'])
        groups[int(headers['Round'])].append((headers['White'], headers['FEN'], moves, points))
assert set(groups) == set(range(1, 11))
penta, scores, same = [0] * 5, [0] * 3, 0
for pair in groups.values():
    first, second = pair
    assert first[0] != second[0] and first[1] == second[1]
    penta[first[3] + second[3]] += 1
    scores[first[3]] += 1
    scores[second[3]] += 1
    same += first[2] == second[2]
output = (raw / 'K26.out').read_text()
assert len(re.findall(r'(?m)^Finished game \d+ ', output)) == 20
assert not re.search(r'(?mi)^Finished game .*\{[^}]*loses on time', output)
print(f'K26 PASS. Both kF, PC20 and net768, tc=6+0.06. All 20 games completed and zero flags. A W-L-D '
      f'{scores[2]}-{scores[0]}-{scores[1]}, penta {penta}, exact UCI move lists {same}/10.')
for arm, values in times.items():
    print(f'{arm} {len(values)} moves, mean {sum(values)/len(values):.3f} ms, '
          f'p99 {sorted(values)[ceil(0.99*len(values))-1]} ms, max {max(values)} ms, above500 {sum(x>500 for x in values)}.')
