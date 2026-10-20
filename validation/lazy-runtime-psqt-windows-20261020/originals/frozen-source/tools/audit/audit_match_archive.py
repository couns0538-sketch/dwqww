#!/usr/bin/env python3
"""Audit archived fastchess PGN records; this does not replay move legality."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import zipfile


def initial_moves(game, limit=16):
    text = re.sub(r'^\[.*\]\s*$', '', game, flags=re.M)
    text = re.sub(r'\{[^}]*\}', ' ', text)
    tokens = re.sub(r'\d+\.(?:\.\.)?', ' ', text).split()
    return [t for t in tokens if t not in ('1-0', '0-1', '1/2-1/2', '*') and not t.startswith('$')][:limit]


def score_for(tags, engine):
    result = tags.get('Result')
    if result == '1/2-1/2':
        return 0.5
    if result not in ('1-0', '0-1'):
        return None
    return float((result == '1-0') == (tags['White'] == engine))


def audit(archive, tree_path=None):
    rows = []
    with zipfile.ZipFile(archive) as z:
        for name in sorted(n for n in z.namelist() if n.endswith('.pgn')):
            raw = z.read(name)
            stats = collections.defaultdict(collections.Counter)
            controls, terminations, rounds = collections.Counter(), collections.Counter(), collections.defaultdict(list)
            result_mismatches = []
            for game in re.split(r'(?=^\[Event ")', raw.decode('utf-8'), flags=re.M):
                if not game.startswith('[Event '):
                    continue
                tags = dict(re.findall(r'^\[(\w+) "(.*)"\]$', game, flags=re.M))
                controls[tags.get('TimeControl')] += 1
                terminations[tags.get('Termination')] += 1
                ending = re.search(r'(1-0|0-1|1/2-1/2|\*)\s*$', game)
                if not ending or ending.group(1) != tags.get('Result'):
                    result_mismatches.append(tags.get('Round'))
                for engine in (tags['White'], tags['Black']):
                    score = score_for(tags, engine)
                    stats[engine]['games'] += 1
                    stats[engine][{0.0: 'losses', 0.5: 'draws', 1.0: 'wins'}.get(score, 'unfinished')] += 1
                rounds[tags.get('Round')].append((tags, initial_moves(game)))
            pair_histograms = {engine: [0] * 5 for engine in stats}
            color_mismatches, opening_mismatches = [], []
            for round_id, games in rounds.items():
                if len(games) != 2:
                    continue
                (a, ma), (b, mb) = games
                if (a['White'], a['Black']) != (b['Black'], b['White']):
                    color_mismatches.append(round_id)
                if a.get('FEN') != b.get('FEN') or ma != mb:
                    opening_mismatches.append(round_id)
                for engine in stats:
                    s1, s2 = score_for(a, engine), score_for(b, engine)
                    if s1 is not None and s2 is not None:
                        pair_histograms[engine][round(2 * (s1 + s2))] += 1
            rows.append({
                'path': name, 'bytes': len(raw),
                'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
                'sha256': hashlib.sha256(raw).hexdigest(), 'games': sum(controls.values()),
                'stats': dict(stats), 'time_controls': dict(controls), 'terminations': dict(terminations),
                'round_sizes': dict(collections.Counter(len(g) for g in rounds.values())),
                'pair_score_histograms_0_05_1_15_2': pair_histograms,
                'pair_color_mismatches': color_mismatches,
                'pair_initial_16_plies_mismatches': opening_mismatches,
                'header_movetext_result_mismatches': result_mismatches,
            })
    totals = collections.Counter()
    for row in rows:
        totals.update(row['terminations'])
    report = {'archive': str(archive), 'archive_sha256': hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
              'pgn_count': len(rows), 'games': sum(r['games'] for r in rows),
              'uncompressed_bytes': sum(r['bytes'] for r in rows),
              'terminations': dict(totals),
              'scope': 'PGN records, hashes, results and pairs; not move-legality replay or SPRT authentication',
              'pgns': rows}
    if tree_path:
        tree = json.loads(Path(tree_path).read_text())
        expected = {f['path']: f for f in tree['tree'] if f['type'] == 'blob' and f['path'].endswith('.pgn')}
        mismatches = []
        for row in rows:
            item = expected.pop(row['path'], None)
            if not item or (item['sha'], item['size']) != (row['git_blob_sha1'], row['bytes']):
                mismatches.append(row['path'])
        report['git_tree_check'] = {'ref': tree['sha'], 'all_pgns_match': not mismatches and not expected,
                                    'mismatches': mismatches, 'missing_pgns': sorted(expected)}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--tree', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.archive, args.tree)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'pgns'}, indent=2))
