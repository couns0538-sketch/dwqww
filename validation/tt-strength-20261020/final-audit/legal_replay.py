#!/usr/bin/env python3
"""Independent, data-only legal replay of retained failed TT match records."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

import chess
import chess.pgn


ROOT = Path('/workspace/.cloud-setup/tt-strength-final-39403471059/verified/files/strength')
OUT = Path(__file__).with_name('legal-replay.json')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fen4(board: chess.Board) -> str:
    return ' '.join(board.fen(en_passant='fen').split()[:4])


def audit(label: str) -> dict:
    directory = ROOT / label
    inputs = [directory / name for name in ('games.pgn', 'selected.epd', 'state.json')]
    before = {str(p): sha(p) for p in inputs}
    positions = [line.strip() for line in inputs[1].read_text().splitlines() if line.strip()]
    assert len(positions) == len(set(positions)), 'Duplicate reserved positions'
    records = []
    outcomes = Counter()
    terminations = Counter()
    plies = 0
    with inputs[0].open() as stream:
        while (game := chess.pgn.read_game(stream)) is not None:
            index = len(records)
            assert not game.errors, (label, index + 1, game.errors)
            board = game.board()
            assert board.is_valid(), (label, index + 1, 'invalid root')
            assert fen4(board) == positions[index // 2], (label, index + 1, 'opening prefix')
            expected_white = 'Candidate' if index % 2 == 0 else 'Baseline'
            assert game.headers['White'] == expected_white
            assert game.headers['Black'] == ('Baseline' if index % 2 == 0 else 'Candidate')
            assert game.headers['Round'] == str(index // 2 + 1)
            assert game.headers['Termination'] == 'normal'
            assert game.headers['TimeControl'] == ('-' if label == 'aa' else '2+0.02')
            for name in ('EngineWhiteName', 'EngineBlackName'):
                advertised = '6.4.11' if label == 'aa' or 'Baseline' == game.headers['White' if name == 'EngineWhiteName' else 'Black'] else '6.4.12'
                assert advertised in game.headers[name]
            moves = []
            for move in game.mainline_moves():
                assert move in board.legal_moves, (label, index + 1, board.fen(), move.uci())
                moves.append(move.uci())
                board.push(move)
            assert int(game.headers['PlyCount']) == len(moves)
            result = game.headers['Result']
            assert result in ('1-0', '0-1', '1/2-1/2'), (label, index + 1, 'unfinished record')
            outcome = board.outcome(claim_draw=True)
            assert outcome is not None and outcome.result() == result, (label, index + 1, 'unsupported terminal result', board.fen(), result, str(outcome))
            if result == '1/2-1/2':
                score = 0.5
            else:
                white_score = 1 if result == '1-0' else 0
                score = white_score if expected_white == 'Candidate' else 1 - white_score
            outcomes[{1: 'wins', .5: 'draws', 0: 'losses'}[score]] += 1
            terminations[outcome.termination.name] += 1
            plies += len(moves)
            records.append({'game': index + 1, 'opening_index': index // 2,
                            'white': game.headers['White'], 'black': game.headers['Black'],
                            'result': result, 'candidate_score': score, 'plies': len(moves),
                            'moves_sha256': hashlib.sha256((' '.join(moves)+'\n').encode()).hexdigest(),
                            'terminal_reason': outcome.termination.name, 'final_fen': board.fen()})
    assert len(records) % 2 == 0, (label, 'orphan original PGN')
    pentanomial = [0] * 5
    for a, b in zip(records[::2], records[1::2]):
        pentanomial[int(2 * (a['candidate_score'] + b['candidate_score']))] += 1
        if label == 'aa':
            assert a['moves_sha256'] == b['moves_sha256'] and a['result'] == b['result']
    state = json.loads(inputs[2].read_text())['stats']['Candidate vs Baseline']
    assert [outcomes[n] for n in ('wins', 'draws', 'losses')] == [state[n] for n in ('wins', 'draws', 'losses')]
    native_penta = [state['penta_LL'], state['penta_LD'], state['penta_WL']+state['penta_DD'], state['penta_WD'], state['penta_WW']]
    assert pentanomial == native_penta
    after = {str(p): sha(p) for p in inputs}
    assert before == after
    return {'status': 'passed_data_only_replay', 'games': len(records), 'complete_pairs': len(records)//2,
            'unpaired_original_pgn_records': 0, 'unique_used_openings': len(records)//2,
            'frozen_reserved_openings': len(positions), 'exact_opening_order_and_swapped_colors': True,
            'candidate_wins_draws_losses': [outcomes[n] for n in ('wins','draws','losses')],
            'pentanomial': pentanomial, 'legal_plies': plies, 'terminal_reasons': dict(terminations),
            'all_original_records_replayed': True, 'native_final_state_matches': True,
            'aa_pair_moves_and_white_results_identical': label == 'aa',
            'inputs_sha256_before': before, 'inputs_sha256_after': after, 'records': records}


if __name__ == '__main__':
    result = {'status': 'passed_offline_original_record_replay', 'method': 'Independent python-chess PGN parsing, move legality, terminal boards and native-state comparison',
              'python_chess_version': chess.__version__, 'aa': audit('aa'), 'sprt': audit('sprt'),
              'acceptance': 'INVALID ENTIRE STRENGTH ATTEMPT: raw runner reports Baseline time forfeit during game85; these completed original PGN records are bookkeeping only. No trimming, pooling, retry or Elo acceptance.',
              'engine_executions': 0,
              'audit_harness_corrections': [{'attempt': 1, 'error': 'AssertionError on initial Round-per-game assumption before any final result file was written.', 'diagnosis': 'Original pinned Fastchess PGN uses one Round number per color-swapped pair, as directly observed in unchanged AA/SPRT headers.', 'correction': 'Require exact Round=index//2+1; all original bytes retained and no game retried.'}]}
    OUT.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'aa_games': result['aa']['games'], 'sprt_games': result['sprt']['games'], 'sprt_legal_plies': result['sprt']['legal_plies'], 'wdl': result['sprt']['candidate_wins_draws_losses'], 'penta': result['sprt']['pentanomial']}))
