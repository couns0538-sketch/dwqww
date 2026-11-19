"""Screen recorded Job 22 search roots for lost pre-root repetition evidence. No engine is run."""

import argparse
from collections import Counter
import csv
from hashlib import sha256
from io import BytesIO, StringIO
from pathlib import Path
import subprocess

import chess


SOURCE = '040834de294a31f81a3d6aa54a605af692a4fcb4'
DIRECTORY = 'forge-combo29/astra5/job22/L1-r15d'
FIRST = 700001


def read_reference(repo, name):
    return subprocess.check_output(['git', '-C', str(repo), 'show', f'{SOURCE}:{DIRECTORY}/{name}'])


def table(raw):
    return csv.DictReader(StringIO(raw.decode('ascii')), delimiter='\t')


def position_key(board):
    # FIDE identity: pieces, side, castling rights, and a legally capturable en-passant right.
    return ' '.join(board.fen(en_passant='legal').split()[:4])


def scan(repo, end):
    assert chess.__version__ == '1.11.2'
    print(f'source {SOURCE}:{DIRECTORY}')
    data = {name: read_reference(repo, name) for name in ['games.tsv', 'openings.tsv', 'records.txt']}
    for name, blob in data.items():
        print(f'input {name} {len(blob)} bytes sha256 {sha256(blob).hexdigest()}')
    stream = BytesIO(data['records.txt'])
    counts = Counter()
    eligible = []
    for opening, receipt in zip(table(data['openings.tsv']), table(data['games.tsv'])):
        game = int(receipt['book_line'])
        if game > end:
            break
        assert game == FIRST + counts['games'] == int(opening['game'])
        counts['games'] += 1
        rows = stream.read(int(receipt['record_bytes']) - stream.tell()).splitlines()
        assert len(rows) == int(receipt['plies'])
        counts['searches'] += len(rows)
        counts['terminal openings'] += int(not rows)
        board = chess.Board()
        keys = [position_key(board)]
        for move in opening['moves'].split():
            board.push_uci(move)
            keys.append(position_key(board))
        fen0 = len(keys) - 1
        counts['clock zero' if board.halfmove_clock == 0 else 'clock positive'] += 1
        for row in rows:
            recorded_game, ply, best, _ = row.split()
            i = len(keys) - 1
            assert int(recorded_game) == game and int(ply) == i
            begin = i - board.halfmove_clock
            if begin >= fen0:
                # Once an irreversible move removes the opening, later searches cannot restore it.
                break
            counts['search roots whose reversible window reaches before FEN0'] += 1
            full = Counter(keys[begin:i])
            truncated = Counter(keys[max(fen0, begin):i])
            for key, occurrences in full.items():
                if occurrences >= 2 and truncated[key] < 2:
                    indices = [p for p in range(begin, i) if keys[p] == key]
                    eligible.append((game, i, indices, truncated[key], key))
            board.push_uci(best.decode('ascii'))
            keys.append(position_key(board))
    assert counts['games'] == end - FIRST + 1
    print(f'games {FIRST}..{end}')
    for key, value in counts.items():
        print(f'{key}: {value}')
    print(f'eligible roots: {len({(row[0],row[1]) for row in eligible})}')
    print(f'eligible games: {len({row[0] for row in eligible})}')
    for game, ply, indices, retained, key in eligible:
        print(f'game {game} search ply {ply}; matching pre-root plies {indices}; retained {retained}; key {key}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path, help='local Git repository containing the pinned Job 22 commit')
    parser.add_argument('--end', type=int, default=702000, help='last game, inclusive (default 702000)')
    args = parser.parse_args()
    scan(args.repo, args.end)
