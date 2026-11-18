import argparse
from itertools import zip_longest
import json
from pathlib import Path
import re


MOVE = re.compile(r'[a-h][1-8][a-h][1-8][qrbn]?')
IDENTITY = ('game', 'ply', 'position', 'bestmove', 'nodes', 'score', 'final', 'terminal')


def records(path):
    previous = None
    with path.open(encoding='ascii') as stream:
        for number, line in enumerate(stream, 1):
            row = json.loads(line)
            game, ply = row['game'], row['ply']
            command = row['position'].split()
            if (command[:3] != ['position', 'startpos', 'moves'] or len(command) - 3 != ply
                    or not all(MOVE.fullmatch(move) for move in command[3:])):
                raise ValueError(f'{path}:{number}: invalid position command for game {game}, ply {ply}')
            if previous is not None:
                if game == previous['game']:
                    wanted = [*previous['position'].split(), previous['bestmove']]
                    if (previous['terminal'] or ply != previous['ply'] + 1 or command != wanted):
                        raise ValueError(f'{path}:{number}: broken in-game position sequence')
                elif game != previous['game'] + 1:
                    raise ValueError(f'{path}:{number}: nonconsecutive game index')
            if row['terminal']:
                last = (row['last_info'] or '').split()
                last_nodes_zero = 'nodes' in last and last[last.index('nodes') + 1:last.index('nodes') + 2] == ['0']
                if (row['final_line'] is not None or row['final'] != 0
                        or not (row['bestmove'] == '0000' or last_nodes_zero)):
                    raise ValueError(f'{path}:{number}: invalid terminal fallback')
            elif (row['final_line'] or '').split() != ['info', 'string', 'softnodes', 'nodes', str(row['final'])]:
                raise ValueError(f'{path}:{number}: final line does not match parsed final nodes')
            previous = row
            yield row


def fnv(value, text):
    for byte in text.encode('ascii'):
        value = ((value ^ byte) * 0x100000001B3) % (1 << 64)
    return value


def summarize(path, hard_cap):
    result = dict(searches=0, total_nodes=0, final_sum=0, at_cap=0, terminal=0,
                  terminal_0000=0, terminal_nonzero_move=0, first_terminal=None)
    trace_hash = final_hash = 0xCBF29CE484222325
    for row in records(path):
        result['searches'] += 1
        result['total_nodes'] += row['nodes']
        result['final_sum'] += row['final']
        result['at_cap'] += row['final'] == hard_cap
        if row['terminal']:
            result['terminal'] += 1
            result['terminal_0000'] += row['bestmove'] == '0000'
            result['terminal_nonzero_move'] += row['bestmove'] != '0000'
            if result['first_terminal'] is None:
                result['first_terminal'] = row
        trace_hash = fnv(trace_hash, '{game},{ply},{bestmove},{nodes},{score};'.format(**row))
        final_hash = fnv(final_hash, '{game},{ply},{final};'.format(**row))
    result['trace_fnv1a64'] = f'{trace_hash:016x}'
    result['final_fnv1a64'] = f'{final_hash:016x}'
    return result


def compare(left, right):
    for index, (a, b) in enumerate(zip_longest(records(left), records(right)), 1):
        if a is None or b is None or any(a[field] != b[field] for field in IDENTITY):
            return {'row': index, 'left': a, 'right': b}
    return None


def main():
    parser = argparse.ArgumentParser(description='Read back Job 6 JSONL trace evidence.')
    commands = parser.add_subparsers(dest='command', required=True)
    roots = commands.add_parser('positions', help='write the exact timed UCI position commands')
    roots.add_argument('trace', type=Path)
    roots.add_argument('--expected', type=int, default=8612)
    summary = commands.add_parser('summary', help='recompute aggregates and terminal split')
    summary.add_argument('trace', type=Path)
    summary.add_argument('--hard-cap', type=int, default=8000)
    difference = commands.add_parser('compare', help='write the first differing pair, ignoring elapsed-time metadata')
    difference.add_argument('left', type=Path)
    difference.add_argument('right', type=Path)
    args = parser.parse_args()
    if args.command == 'positions':
        wanted = [row['position'] for row in records(args.trace)]
        if len(wanted) != args.expected:
            raise ValueError(f'expected {args.expected} root commands, read {len(wanted)}')
        print('\n'.join(wanted))
    elif args.command == 'summary':
        print(json.dumps(summarize(args.trace, args.hard_cap)))
    else:
        print(json.dumps(compare(args.left, args.right)))


if __name__ == '__main__':
    main()
