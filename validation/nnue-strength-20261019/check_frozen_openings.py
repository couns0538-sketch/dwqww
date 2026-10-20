#!/usr/bin/env python3
"""Verify the already frozen opening inputs without selecting/replacing outputs."""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import zipfile

import chess
import chess.pgn


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    package = repo / '.github/hosted-nnue-strength'
    report = json.loads((package / 'provenance/openings-selection.json').read_text())
    source = report['source']
    archive_bytes = (package / 'provenance/8moves_v3.pgn.zip').read_bytes()
    assert len(archive_bytes) == source['archive_bytes'] == 807558
    assert sha(archive_bytes) == source['archive_sha256'] == '7e1e9dd118b4bb97d8a8b5b8a790c86e21f8509d59a27d2883767d94477be02e'
    assert sha((package / 'provenance/LICENSE-upstream').read_bytes()) == source['license_sha256']
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        pgn = archive.read(source['zip_member'])
    assert len(pgn) == source['pgn_bytes'] and sha(pgn) == source['pgn_sha256']
    excluded = set()
    registries = []
    assert len(report['registries']) == 42
    for row in report['registries']:
        raw = Path(row['path']).read_bytes()
        assert sha(raw) == row['sha256'], 'Changed original registry: ' + row['path']
        for line in raw.decode().splitlines():
            if not line.strip():
                continue
            fen = ' '.join(line.split()[:4])
            excluded.add(fen)
            # Historical equivalence only, never normalize a candidate position.
            board = chess.Board(fen + ' 0 1')
            excluded.add(' '.join(board.fen(en_passant='legal').split()[:4]))
        registries.append({'path': row['path'], 'sha256': row['sha256']})
    confirmation_path = repo / '.github/hosted-confirmation/provenance/openings-selection.json'
    confirmation_bytes = confirmation_path.read_bytes()
    confirmation = json.loads(confirmation_bytes)
    confirmation_fens = {item['fen'] for rows in confirmation['selections'].values() for item in rows}
    assert len(confirmation_fens) == 164 and confirmation_fens <= excluded
    excluded.update(confirmation['exclusions']['canonical_positions'])
    stream = io.StringIO(pgn.decode('utf-8-sig'))
    eligible = {}
    all_positions = set()
    stats = Counter()
    while True:
        game = chess.pgn.read_game(stream)
        if game is None:
            break
        stats['games'] += 1
        assert not game.errors and not game.headers.get('FEN')
        assert game.headers.get('Variant', 'Standard') == 'Standard'
        board = game.board()
        plies = 0
        for move in game.mainline_moves():
            assert board.is_legal(move)
            board.push(move)
            plies += 1
        assert plies == 16 and board.is_valid() and board.legal_moves.count() > 0
        fen = ' '.join(board.fen(en_passant='fen').split()[:4])
        assert fen not in all_positions
        all_positions.add(fen)
        if board.ep_square is not None:
            stats['actual_ep_positions_excluded_without_rewrite'] += 1
            continue
        assert fen.split()[3] == '-'
        stats['strict_ep_none'] += 1
        assert fen not in excluded, 'Historical overlap'
        eligible[fen] = stats['games']
    assert stats['games'] == 34700 and stats['strict_ep_none'] == len(eligible) == 31603
    assert stats['actual_ep_positions_excluded_without_rewrite'] == 3097
    selected = report['prospective_selection']
    string_seed = '20261019-official-stockfish-8moves-v3-long-strength-v1'
    assert selected['seed'] == string_seed
    ranked = sorted(eligible, key=lambda fen: hashlib.sha256((string_seed + '\n' + fen).encode()).digest())
    frozen = selected['selections']
    assert len(frozen) == 1028
    assert ranked[:1028] == [item['fen'] for item in frozen]
    assert all(eligible[item['fen']] == item['source_game_1based'] for item in frozen)
    runtime = json.loads((package / 'provenance/runtime-order.json').read_text())
    for phase, rows in [('aa', frozen[:4]), ('sprt', frozen[4:])]:
        fens = [item['fen'] for item in rows]
        raw = ('\n'.join(fens) + '\n').encode('ascii')
        assert raw == (package / ('openings/' + phase + '.epd')).read_bytes()
        assert sha(raw) == selected['outputs'][phase]['sha256']
        ordered = sorted(fens, key=lambda fen: hashlib.sha256(('20261021\n' + fen).encode('ascii')).digest())
        ordered_raw = ('\n'.join(ordered) + '\n').encode('ascii')
        assert runtime[phase]['seed'] == 20261021 and runtime[phase]['ordered_fens'] == ordered
        assert sha(ordered_raw) == runtime[phase]['selected_epd_sha256']
        assert ordered_raw == (package / ('provenance/runtime-' + phase + '.epd')).read_bytes()
    assert not {row['fen'] for row in frozen[:4]} & {row['fen'] for row in frozen[4:]}
    result = {'status': 'passed', 'python_chess_version': chess.__version__,
              'statistics': dict(stats), 'unique_positions': len(all_positions),
              'eligible_unique': len(eligible), 'historical_registry_count': len(registries),
              'registry_hashes': registries, 'historical_overlap': 0,
              'explicit_confirmation_positions_excluded': 164,
              'confirmation_selection_sha256': sha(confirmation_bytes),
              'selector_seed': string_seed, 'unchanged_aa_rows': 4,
              'unchanged_sprt_rows': 1024, 'runtime_seed': 20261021,
              'exact_runtime_order_and_hashes': 'passed', 'engine_executions': 0,
              'frozen_inputs_reselected_or_rewritten': False}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'registry_hashes'}))


if __name__ == '__main__':
    main()
