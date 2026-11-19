#!/usr/bin/env python3
"""Independently recount integer-millisecond timing and check published Job 36 bytes."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess


ROOT = Path('/workspace/work/sol-job36')
REPO = Path('/workspace/work/sol-job1/repo')
ARCHIVE = 'forge-combo29/sol/job36/raw'
FINISHED = re.compile(r'^Finished game (\d+) \((\S+) vs (\S+)\): (1-0|0-1|1/2-1/2) \{([^}]+)\}$', re.M)
STARTED = re.compile(r'^Started game (\d+) of (\d+) \((\S+) vs (\S+)\)$', re.M)
TAG = re.compile(r'^\[([^ ]+) "((?:[^"\\]|\\.)*)"\]$', re.M)
MOVE = re.compile(r'\s*(?:(\d+)(\.{3}|\.)\s*)?(\S+)\s+\{([^}]*)\}')
ELAPSED = re.compile(r'[^/\s]*/\d+ (\d+)\.(\d{3})s(?=,|$)')
CLOCK = re.compile(r'(?:^|, )tl=(-?\d+)\.(\d{3})s(?=,|$)')
TIMEOUT = re.compile(r'(White|Black) loses on time \((\d+)ms overrun\)')


def milliseconds(match):
    seconds, msec = match.groups()
    return (-1 if seconds.startswith('-') else 1) * (int(seconds.lstrip('-')) * 1000 + int(msec))


def per_engine(hist):
    count = hist.total()
    if count == 0:
        return {'moves': 0, 'sum_ms': 0, 'mean_ms': None, 'p99_ms': None,
                'p99_rank': None, 'max_ms': None, 'above_500ms': 0}
    rank = (99 * count + 99) // 100
    cumulative = 0
    for value, frequency in sorted(hist.items()):
        cumulative += frequency
        if cumulative >= rank:
            break
    total = sum(value * frequency for value, frequency in hist.items())
    return {'moves': count, 'sum_ms': total, 'mean_ms': total / count, 'p99_ms': value,
            'p99_rank': rank, 'max_ms': max(hist), 'above_500ms': sum(n for ms, n in hist.items() if ms > 500)}


def recount(pgn, out):
    started_rows = STARTED.findall(out)
    starts = {int(game_id): (white, black) for game_id, _, white, black in started_rows}
    finished_rows = FINISHED.findall(out)
    finishes = {int(game_id): (white, black, result, reason) for game_id, white, black, result, reason in finished_rows}
    assert len(starts) == len(started_rows) and len(finishes) == len(finished_rows)
    assert all(starts[game_id] == end[:2] for game_id, end in finishes.items())
    assert len({total for _, total, _, _ in started_rows}) <= 1
    a, b = 'A', 'B'
    assert all(sides == ((a, b) if game_id % 2 else (b, a)) for game_id, sides in starts.items())

    hist = {a: Counter(), b: Counter()}
    all_wld = Counter()
    scores = {'1-0': 2, '0-1': 0, '1/2-1/2': 1}
    rounds = defaultdict(list)
    flags = []
    reviewed = set()
    for block in re.split(r'(?m)(?=^\[Event ")', pgn):
        if not block.strip():
            continue
        header, movetext = block.split('\n\n', 1)
        tags = dict(TAG.findall(header))
        assert len(tags) == len(header.splitlines())
        rnd = int(tags['Round'])
        white, black = tags['White'], tags['Black']
        game_id = 2 * rnd - (white == a)
        assert int(tags.get('GameId', game_id)) == game_id and game_id not in reviewed
        reviewed.add(game_id)
        console_white, console_black, result, reason = finishes[game_id]
        assert (white, black, tags['Result']) == (console_white, console_black, result)
        assert tags['TimeControl'] == '6+0.06'
        ended_on_time = TIMEOUT.fullmatch(reason)
        assert tags['Termination'] == ('time forfeit' if ended_on_time else 'normal')

        fen = tags['FEN']
        start_turn = fen.split()[1] == 'b'
        fullmove = int(fen.split()[5])
        start_index = 2 * (fullmove - 1) + start_turn
        preceding = {0: 6060, 1: 6060}
        moves = []
        last = None
        offset = 0
        for move in MOVE.finditer(movetext):
            assert move.start() == offset, (game_id, movetext[offset:move.start()])
            offset = move.end()
            number, dots, san, comment = move.groups()
            absolute_ply = start_index + len(moves)
            turn = absolute_ply % 2
            if number is not None:
                assert int(number) == absolute_ply // 2 + 1 and dots == ('...' if turn else '.')
            moves.append(san)
            elapsed = ELAPSED.match(comment)
            assert elapsed is not None, (game_id, absolute_ply, comment)
            elapsed = milliseconds(elapsed)
            pre_clock = preceding[turn]
            assert pre_clock > 0
            overrun = max(0, elapsed - pre_clock)
            preceding[turn] = pre_clock - elapsed + (0 if overrun else 60)
            post_clock = CLOCK.search(comment)
            assert post_clock is not None, (game_id, absolute_ply, comment)
            if not (comment.startswith('/0 ') and milliseconds(post_clock) == 0):
                assert milliseconds(post_clock) == preceding[turn], (game_id, absolute_ply, comment, preceding[turn])
            hist[black if turn else white][elapsed] += 1
            last = (turn, absolute_ply, san, elapsed, pre_clock, overrun, comment)
            if overrun:
                assert ended_on_time and movetext[offset:].strip() == result
        assert movetext[offset:].strip() == result
        assert len(moves) == int(tags['PlyCount'])
        if last is not None:
            assert last[-1].endswith(', ' + reason), (game_id, last[-1], reason)

        if ended_on_time:
            loser = {'White': 0, 'Black': 1}[ended_on_time[1]]
            overrun = int(ended_on_time[2])
            assert result == ('1-0' if loser else '0-1')
            next_index = start_index + len(moves)
            if last is not None and (next_index - 1) % 2 == loser:
                assert last[-2] == overrun > 0 and last[0] == loser
                _, ply, san, elapsed, pre_clock, _, _ = last
                provenance = 'PGN final bestmove and clock recurrence'
            else:
                ply, san, pre_clock = next_index, None, preceding[loser]
                assert ply % 2 == loser and (pre_clock > 0 or overrun == 0)
                elapsed = pre_clock + overrun if pre_clock > 0 else None
                provenance = 'console overrun and clock recurrence' if pre_clock > 0 else 'no search'
            flags.append({'game': game_id, 'round': rnd, 'side': black if loser else white,
                          'move_number': ply // 2 + 1, 'color': ended_on_time[1], 'san': san,
                          'elapsed_ms': elapsed, 'clock_before_ms': pre_clock, 'overrun_ms': overrun,
                          'provenance': provenance})

        a_score = scores[result] if white == a else 2 - scores[result]
        all_wld[a_score] += 1
        rounds[rnd].append((white, black, fen, a_score, moves))

    assert reviewed == set(finishes)
    pair_wld, penta, same, singleton = Counter(), [0] * 5, 0, 0
    for games in rounds.values():
        if len(games) == 1:
            singleton += 1
            continue
        first, second = games
        assert first[:2] == second[:2][::-1] and first[2] == second[2]
        pair_wld.update((first[3], second[3]))
        penta[first[3] + second[3]] += 1
        same += first[4] == second[4]
    timings = {engine: per_engine(hist[engine]) for engine in (a, b)}
    console_flags = Counter(black if term[1] == 'Black' else white
                            for _, white, black, _, reason in finished_rows if (term := TIMEOUT.fullmatch(reason)))
    flags_by_side = Counter(flag['side'] for flag in flags)
    assert console_flags == flags_by_side
    a99, b99 = timings[a]['p99_ms'], timings[b]['p99_ms']
    within_limit = a99 is not None and b99 is not None and abs(a99 - b99) * 10 <= b99
    return {'started': len(starts), 'games': len(finishes), 'complete_pairs': sum(penta), 'singletons': singleton,
            'complete_pair_wld_A': [pair_wld[2], pair_wld[0], pair_wld[1]],
            'all_wld_A': [all_wld[2], all_wld[0], all_wld[1]], 'penta': penta, 'exact_SAN_pairs': same,
            'timing_ms': timings, 'fastchess_time_forfeits': {a: console_flags[a], b: console_flags[b]},
            'flag_evidence': sorted(flags, key=lambda flag: flag['game']),
            'candidate_p99_within_10pct': within_limit,
            'clock_ok': console_flags[a] == 0 and within_limit}


def blob(commit, name):
    return subprocess.check_output(['git', 'show', f'{commit}:{ARCHIVE}/{name}'], cwd=REPO)


def publication(commit, run, suffix, raw):
    name = f'{run}.{suffix}'
    if suffix == 'pgn' and len(raw) > 20_000_000:
        manifest = json.loads(blob(commit, name + '.manifest.json'))
        parts = []
        for part in manifest['parts']:
            part_bytes = blob(commit, part['file'])
            assert len(part_bytes) == part['bytes'] <= 20_000_000
            assert sha256(part_bytes).hexdigest() == part['sha256']
            parts.append(part_bytes)
        assert b''.join(parts) == raw
        return {'bytes': len(raw), 'sha256': sha256(raw).hexdigest(), 'parts': len(parts)}
    archived = blob(commit, name)
    assert archived == raw and len(archived) <= 20_000_000
    return {'bytes': len(archived), 'sha256': sha256(archived).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', choices=['K26', 'Q1', 'Q2'])
    parser.add_argument('--directory', type=Path, default=ROOT / 'raw')
    parser.add_argument('--commit')
    args = parser.parse_args()
    raw = {suffix: (args.directory / f'{args.run}.{suffix}').read_bytes()
           for suffix in ('pgn', 'out', 'meta') if (args.directory / f'{args.run}.{suffix}').is_file()}
    metadata = json.loads(raw['meta'])
    assert metadata['match'] == args.run and metadata['status'] in ('complete', 'interrupted')
    assert metadata['timecontrol'] == '6+0.06' and metadata['time_margin_ms'] == 0
    assert metadata['concurrency'] < metadata['nproc']
    for suffix in ('pgn', 'out'):
        if suffix not in raw:
            assert suffix == 'pgn' and metadata['status'] == 'interrupted' and 'pgn_sha256' not in metadata
        else:
            assert metadata[f'{suffix}_bytes'] == len(raw[suffix])
            assert metadata[f'{suffix}_sha256'] == sha256(raw[suffix]).hexdigest()
    result = recount(raw.get('pgn', b'').decode(), raw['out'].decode())
    if metadata['status'] == 'complete':
        assert result['games'] == metadata['games_requested'] == result['started']
        assert result['complete_pairs'] == metadata['pairs_requested']
    result['run'] = args.run
    if args.commit:
        result['archive_commit'] = args.commit
        result['archive_equals_scratch'] = {suffix: publication(args.commit, args.run, suffix, data)
                                            for suffix, data in raw.items()}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
