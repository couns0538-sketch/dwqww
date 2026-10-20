#!/usr/bin/env python3
"""One prospective TT opening reservation from frozen source/exclusion inputs.

No engines, network, Git mutations, timing trials or outcome selection. Once
frozen, use check_frozen_openings.py to verify without replacing these files.
"""
from collections import Counter
import copy
import hashlib
import io
import json
from pathlib import Path
import zipfile

import chess
import chess.pgn

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / '.github/hosted-tt-strength'
SEED = '20261020-tt-exclusive-drain-strength-v1'
RUNTIME_SEED = 20261022


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    report_path = PACKAGE / 'provenance/openings-selection.json'
    assert not (PACKAGE / 'provenance/tt-reservation-frozen.json').exists(), 'Reservation already frozen'
    original_path = REPO / '.github/hosted-nnue-strength/provenance/openings-selection.json'
    original_raw = original_path.read_bytes()
    original = json.loads(original_raw)
    report = copy.deepcopy(original)
    excluded = set()
    assert len(original['registries']) == 42
    for row in original['registries']:
        raw = Path(row['path']).read_bytes()
        assert sha(raw) == row['sha256'], row['path']
        for line in raw.decode().splitlines():
            if line.strip():
                fen = ' '.join(line.split()[:4])
                excluded.add(fen)
                # Historical-equivalence exclusion only; no candidate rewriting.
                board = chess.Board(fen + ' 0 1')
                excluded.add(' '.join(board.fen(en_passant='legal').split()[:4]))
    confirmation_path = REPO / '.github/hosted-confirmation/provenance/openings-selection.json'
    confirmation_raw = confirmation_path.read_bytes()
    confirmation = json.loads(confirmation_raw)
    confirmation_fens = {item['fen'] for rows in confirmation['selections'].values() for item in rows}
    assert len(confirmation_fens) == 164 and confirmation_fens <= excluded
    excluded.update(confirmation['exclusions']['canonical_positions'])
    nnue_fens = {row['fen'] for row in original['prospective_selection']['selections']}
    assert len(nnue_fens) == 1028
    for phase, count in [('aa', 4), ('sprt', 1024)]:
        path = REPO / ('.github/hosted-nnue-strength/openings/' + phase + '.epd')
        raw = path.read_bytes()
        assert sha(raw) == original['prospective_selection']['outputs'][phase]['sha256']
        assert len(raw.decode().splitlines()) == count
        assert set(raw.decode().splitlines()) <= nnue_fens
    excluded.update(nnue_fens)
    source = report['source']
    archive = (PACKAGE / 'provenance/8moves_v3.pgn.zip').read_bytes()
    assert sha(archive) == source['archive_sha256']
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        pgn = zipped.read(source['zip_member'])
    assert sha(pgn) == source['pgn_sha256']
    stream = io.StringIO(pgn.decode('utf-8-sig'))
    stats = Counter()
    eligible = {}
    all_positions = set()
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
        stats['strict_ep_none_before_exclusions'] += 1
        if fen in excluded:
            stats['prior_reserved_positions_excluded'] += 1
            continue
        eligible[fen] = stats['games']
    assert stats == {'games': 34700, 'strict_ep_none_before_exclusions': 31603,
                     'actual_ep_positions_excluded_without_rewrite': 3097,
                     'prior_reserved_positions_excluded': 1028}, stats
    assert len(eligible) == 30575
    selected = sorted(eligible, key=lambda fen: hashlib.sha256((SEED + '\n' + fen).encode()).digest())[:1028]
    assert len(set(selected)) == 1028 and not set(selected) & excluded
    outputs = {}
    runtime = {}
    for phase, fens in [('aa', selected[:4]), ('sprt', selected[4:])]:
        raw = ('\n'.join(fens) + '\n').encode('ascii')
        path = PACKAGE / ('openings/' + phase + '.epd')
        path.write_bytes(raw)
        outputs[phase] = {'path': path.relative_to(REPO).as_posix(), 'sha256': sha(raw), 'positions': len(fens)}
        ordered = sorted(fens, key=lambda fen: hashlib.sha256((str(RUNTIME_SEED) + '\n' + fen).encode()).digest())
        ordered_raw = ('\n'.join(ordered) + '\n').encode('ascii')
        (PACKAGE / ('provenance/runtime-' + phase + '.epd')).write_bytes(ordered_raw)
        runtime[phase] = {'seed': RUNTIME_SEED, 'positions': len(fens),
                          'selector_pool_sha256': sha(raw), 'selected_epd_sha256': sha(ordered_raw),
                          'ordered_fens': ordered}
    report.update(statistics=dict(stats), eligible_unique_after_all_exclusions=len(eligible),
                  prior_overlap_ep_dash_unique=1028,
                  excluded_exact_or_legal_ep_historical_keys=len(excluded))
    report['nnue_strength_reserved_exclusion'] = {
        'selection_path': original_path.relative_to(REPO).as_posix(),
        'selection_sha256': sha(original_raw), 'positions': 1028,
        'active_run_id': 39348571407, 'frozen_launch_commit': '563bd406',
        'canonical_positions': sorted(nnue_fens),
        'pool_sha256': {phase: original['prospective_selection']['outputs'][phase]['sha256'] for phase in ('aa', 'sprt')}}
    report['confirmation_selection_sha256'] = sha(confirmation_raw)
    report['prospective_selection'].update(
        state='PROSPECTIVE_RESERVED_PENDING_ROOT_SOURCE_FREEZE_AND_REVIEW_NO_LAUNCH', seed=SEED,
        eligibility='All34700standard16plygames legally replayed. Unique valid final strict-FEN first4fields with actualEPsquare absent; exclude frozen42historicalregistries, unusedtails, explicit164confirmationcohort and all1028activeNNUEstrengthreservedpositions. NoEPnormalization, engine/outcome selection or substitution.',
        outputs=outputs,
        selections=[{'source_game_1based': eligible[fen], 'fen': fen,
                     'ranking_sha256': sha((SEED + '\n' + fen).encode())} for fen in selected])
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    (PACKAGE / 'provenance/runtime-order.json').write_text(json.dumps(runtime, indent=2) + '\n')
    marker = {'status': 'reserved_once_no_games_or_launch', 'selector_seed': SEED,
              'runtime_seed': RUNTIME_SEED, 'selection_sha256': sha(report_path.read_bytes()),
              'statistics': dict(stats), 'eligible_unique_after_all_exclusions': len(eligible),
              'historical_registries': 42, 'explicit_confirmation_excluded': 164,
              'active_nnue_reserved_excluded': 1028, 'engine_executions': 0}
    (PACKAGE / 'provenance/tt-reservation-frozen.json').write_text(json.dumps(marker, indent=2) + '\n')
    print(json.dumps(marker))


if __name__ == '__main__':
    main()
