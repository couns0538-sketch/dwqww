"""Freeze a separate capture-measurement cohort from completed Forge gate PGNs.

This selects original FD3A5190 searched moves; it neither searches nor relabels.
The cohort is not a training recipe and must not be pooled with the self-play
million. Fastchess source was inspected, not copied: Match::processMove obtains
engine.bestmove(), addMoveData stores its score/depth, and PgnBuilder emits that
move/comment before advancing the board. Book comments have no search score.
"""
import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import time

import chess
import chess.pgn

from filter_positions import low_priority, sha256
from records import EV, dumps, record, read_pgn_game
from resource_policy import storage_guard

BASELINE_NAME = 'base_AL1_s198_ltopgo_x_FD3A5190'
BASELINE_SHA256 = 'FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072'
BASELINE_PINS = [312866, 862329, 3024920, 12389307, 34048354]
GATE_NAMES = (
    'uhoT2_sf26b14',
    'uhoSF26bit1_razor_e417_vs_AL1lp',
    'uhoE3a_evalmatscale12_vs_AL1lp',
    'uhoE3b_evaloptimism40_vs_AL1lp',
    'uhoE3c_evalrule50damp30_vs_AL1lp',
)
DEFAULT_GATES = tuple(Path('F:/forge_push') / name for name in GATE_NAMES)
SEMANTICS_EVIDENCE = {
    'licence': 'MIT; inspected only, no Fastchess source copied',
    'data': 'Owned completed Forge gate game outputs; their UHO opening provenance is retained. No external corpus or Leela data is imported.',
    'root': 'C:/Users/Administrator/grok-pc/tools/fastchess',
    'files': {
        'app/src/matchmaking/match/match.cpp': {
            'sha256': 'FABC0C41D02A03D122F4C35A780B8676C81771348C37F4EF30762D7EF0828615',
            'basis': 'lines 515-524: engine.bestmove() passed to addMoveData; lines 272-329 store that move and engine score/depth'},
        'app/src/game/pgn/pgn_builder.cpp': {
            'sha256': 'CEE379E910E66DD634C00D037298C16F8E65C52F12C3ACCD5F539A5F03E5F43B',
            'basis': 'lines 104-114 emit move/comment before board.makeMove; lines 174-181 distinguish book from score/depth comments'},
        'app/src/engine/uci_engine.cpp': {
            'sha256': 'DC3EFF8F922254AB830C1E9D0352716A322768E0C776F8077611FF8B061FC70F',
            'basis': 'lines 435-463 parse the engine bestmove response'},
        'LICENSE': {'sha256': '6272375921D96A6E55966FD6C991A192D5211E6B20E4C3338D23B79F02ABC428'},
    },
}


def snapshot(path):
    """Hash the complete file and reject changes during that read."""
    path = Path(path)
    before = path.stat()
    digest = sha256(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f'source changed while hashing: {path}')
    return {'path': str(path), 'bytes': after.st_size, 'mtime_ns': after.st_mtime_ns,
            'sha256_before': digest}


def qualify_gate(gate):
    gate = Path(gate)
    paths = {'pgn': gate / (gate.name + '.pgn'),
             'run_info': gate / 'RUN_INFO.json', 'result': gate / 'RESULT.md'}
    files = {name: snapshot(path) for name, path in paths.items()}
    info = json.loads(paths['run_info'].read_text(encoding='utf-8-sig'))
    base = info.get('base', {})
    if (base.get('name') != BASELINE_NAME or
            base.get('sha256', '').upper() != BASELINE_SHA256 or
            base.get('options') != [] or base.get('pins') != BASELINE_PINS):
        raise ValueError(f'baseline identity/options do not match frozen FD3A5190: {gate}')
    candidate = info.get('candidate', {}).get('name')
    if (not isinstance(candidate, str) or not candidate or candidate == BASELINE_NAME or
            info.get('tag') != gate.name or not info.get('runner', '').startswith('forge_queue.ps1 ')):
        raise ValueError(f'unsupported gate provenance: {gate}')
    result = paths['result'].read_text(encoding='utf-8-sig')
    required = ('fastchess exit code 0;', 'Crashes/disconnects/stalls/illegal: 0',
                'Time losses: 0', "fastchess 'Warning;' lines: 0")
    if any(marker not in result for marker in required):
        raise ValueError(f'gate lacks completed clean result receipt: {gate}')
    return {'gate': gate.name, 'files': files, 'baseline': base,
            'candidate_name': candidate, 'opening_provenance': info.get('book'),
            'games_consumed': 0, 'rows_selected': 0,
            'baseline_without_positive_depth_score': 0}


def searched_rows(source):
    path = Path(source['files']['pgn']['path'])
    with path.open(encoding='utf-8-sig') as fh:
        while (game := read_pgn_game(fh)) is not None:
            source['games_consumed'] += 1
            game_number = source['games_consumed']
            if game.errors:
                raise ValueError(f'malformed PGN: {path} game {game_number}')
            players = (game.headers.get('White'), game.headers.get('Black'))
            if set(players) != {BASELINE_NAME, source['candidate_name']}:
                raise ValueError(f'PGN players differ from pinned gate: {path} game {game_number}')
            if game.headers.get('Event') != 'forge_' + source['gate']:
                raise ValueError(f'PGN event differs from pinned gate: {path} game {game_number}')
            outcomes = {'1-0': 1, '0-1': -1, '1/2-1/2': 0}
            outcome = game.headers.get('Result')
            if outcome not in outcomes or game.headers.get('Termination') not in ('normal', 'adjudication'):
                raise ValueError(f'PGN game is not completed cleanly: {path} game {game_number}')
            board = game.board()
            if board.chess960:
                raise ValueError('capture measurement requires standard chess')
            for ply, node in enumerate(game.mainline()):
                player = players[0 if board.turn == chess.WHITE else 1]
                if player == BASELINE_NAME:
                    match = EV.match(node.comment or '')
                    if match and int(match[4]) > 0:
                        value = Decimal(match[3]) * (1 if match[2] else 100)
                        if value != value.to_integral_value():
                            raise ValueError(f'nonintegral stored score: {path} game {game_number} ply {ply}')
                        score = int(value) * (-1 if match[1] == '-' else 1)
                        yield record(board.fen(en_passant='fen'), score,
                                     'mate' if match[2] else 'cp', outcomes[outcome],
                                     str(path), f'{game_number}:{ply}', 'pgn',
                                     node.move.uci(), node.comment, int(match[4]))
                    else:
                        source['baseline_without_positive_depth_score'] += 1
                board.push(node.move)


def freeze(out, *, gates=DEFAULT_GATES, limit=1_000_000, batch_size=1024):
    """Publish only after the exact row count and every full-input hash recheck."""
    if type(limit) is not int or not 1 <= limit <= 1_000_000:
        raise ValueError('limit must be an integer from 1 to 1000000')
    if type(batch_size) is not int or not 1 <= batch_size <= 4096:
        raise ValueError('batch_size must be an integer from 1 to 4096')
    out = Path(out)
    partial = out.with_name(out.name + '.partial')
    if os.path.lexists(out) or os.path.lexists(partial):
        raise FileExistsError('refusing existing capture cohort destination')
    storage_guard(out)
    storage_guard(partial)
    low_priority()
    started = time.perf_counter()
    sources = [qualify_gate(path) for path in gates]
    if not sources or len({s['files']['pgn']['path'] for s in sources}) != len(sources):
        raise ValueError('nonempty distinct ordered gate sources required')
    storage_guard(partial)
    partial.mkdir(parents=True)
    count = 0
    pending = []
    with (partial / 'records.jsonl').open('xb') as output:
        def flush():
            if pending:
                payload = ''.join(pending).encode('utf-8')
                storage_guard(partial, allowance=len(payload) + 1024 * 1024)
                output.write(payload)
                output.flush()
                pending.clear()
        for source in sources:
            for row in searched_rows(source):
                pending.append(dumps(row) + '\n')
                count += 1
                source['rows_selected'] += 1
                if len(pending) == batch_size:
                    flush()
                if count == limit:
                    break
            if count == limit:
                break
        flush()
    if count != limit:
        raise ValueError(f'insufficient baseline searched rows: {count} < {limit}')
    for source in sources:
        for original in source['files'].values():
            after = snapshot(original['path'])
            if any(original[k] != after[k] for k in ('bytes', 'mtime_ns', 'sha256_before')):
                raise ValueError(f'source changed during cohort freeze: {original["path"]}')
            original['sha256_after'] = after['sha256_before']
    report = {'schema': 1, 'count': count, 'requested_rows': limit,
              'measurement_only': True, 'training_recipe': False, 'workers': 1,
              'baseline_name': BASELINE_NAME, 'baseline_sha256': BASELINE_SHA256,
              'selection': 'first requested positive-depth scored baseline moves, ordered gates then game then mainline ply; no search, relabel, deduplication, or shuffle',
              'sources': sources, 'semantics_evidence': SEMANTICS_EVIDENCE,
              'elapsed_seconds': time.perf_counter() - started,
              'hashes': {'records.jsonl': sha256(partial / 'records.jsonl')}}
    manifest = (json.dumps(report, sort_keys=True, indent=2) + '\n').encode('utf-8')
    storage_guard(partial, allowance=len(manifest) + 1024 * 1024)
    with (partial / 'manifest.json').open('xb') as fh:
        fh.write(manifest)
    storage_guard(out, allowance=0)
    partial.rename(out)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--limit', type=int, default=1_000_000)
    args = parser.parse_args()
    print(json.dumps(freeze(args.output, limit=args.limit), indent=2))
