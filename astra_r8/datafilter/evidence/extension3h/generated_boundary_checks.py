"""Original generated PGN and native-FEN checks; fixtures are not training data."""
import io
import json
import os
from pathlib import Path
import random
import sys
import time
import traceback

HERE = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter')
ROOT = Path('C:/astra8_data/extension3h_20261103')
sys.dont_write_bytecode = True
os.environ.update(PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='',
                  HIP_VISIBLE_DEVICES='', ROCR_VISIBLE_DEVICES='',
                  OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                  HYPOTHESIS_STORAGE_DIRECTORY=str(ROOT / 'hypothesis_boundary_cache'))
sys.path[:0] = [str(ROOT / 'python_tools'), str(HERE)]
import chess
import chess.pgn
import hypothesis
from hypothesis import given, settings, strategies as st
from filter_positions import low_priority, matches, sha256
from records import board_from_fen, record, read_pgn_game
from resource_policy import storage_guard
from native_forge_smoke import run as native

CASES = 0
SEEDS = [chess.STARTING_FEN,
         'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1',
         '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 81',
         '4k3/P7/8/8/8/8/7p/4K3 w - - 0 81',
         '4k3/8/8/8/8/8/4r3/4K3 w - - 0 1',
         '7k/6Q1/6K1/8/8/8/8/8 b - - 0 1',
         '7k/5Q2/6K1/8/8/8/8/8 b - - 0 1']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save(path, value):
    text = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'
    storage_guard(path, allowance=len(text.encode('utf-8')) + 1024 * 1024)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)


@settings(max_examples=500, deadline=None, derandomize=True, database=None)
@given(st.lists(st.tuples(st.integers(0, len(SEEDS)-1),
                         st.lists(st.integers(0, 8191), max_size=48),
                         st.sampled_from(['1-0', '0-1', '1/2-1/2', '*'])),
                min_size=1, max_size=4),
       st.sampled_from(['\n', '\r\n']))
def concatenated_games(items, newline):
    global CASES
    games, expected = [], []
    for seed, choices, result in items:
        board = board_from_fen(SEEDS[seed])
        game = chess.pgn.Game.from_board(board)
        game.headers['Result'] = result
        node, moves = game, []
        for choice in choices:
            legal = list(board.legal_moves)
            if not legal:
                break
            move = legal[choice % len(legal)]
            node = node.add_variation(move)
            node.comment = '+0.20/12 generated parser fixture'
            moves.append(move.uci())
            board.push(move)
        games.append(str(game))
        expected.append((result, moves, board.fen(en_passant='fen')))
    stream = io.StringIO(('\n\n'.join(games) + '\n\n').replace('\n', newline))
    for result, moves, final_fen in expected:
        parsed = read_pgn_game(stream)
        require(parsed is not None, 'lost concatenated game')
        require(parsed.headers['Result'] == result, 'result crossed a game boundary')
        require([m.uci() for m in parsed.mainline_moves()] == moves, 'move stream changed')
        require(parsed.end().board().fen(en_passant='fen') == final_fen, 'game state changed')
    require(read_pgn_game(stream) is None, 'spurious game after end of input')
    CASES += 1


def native_cases():
    rng = random.Random(5108)
    seen = {}
    for seed_index, seed in enumerate(SEEDS):
        for game_index in range(12):
            board = board_from_fen(seed)
            for ply in range(48):
                fen = board.fen(en_passant='fen')
                legal = list(board.legal_moves)
                best = next((m for m in legal if m.promotion or board.is_en_passant(m)),
                            legal[0] if legal else None)
                row = record(fen, 0, 'cp', None, 'original-generated-native-fixture',
                             f'{1+seed_index*12+game_index}:{ply}', 'pgn',
                             best.uci() if best else None, 'NOT TRAINING DATA')
                seen.setdefault(fen, row)
                if not legal:
                    break
                checking = [m for m in legal if board.gives_check(m)]
                captures = [m for m in legal if board.is_capture(m) or m.promotion]
                special = [m for m in legal if board.is_castling(m) or board.is_en_passant(m)]
                candidates = special or (checking if ply % 3 == 0 and checking else captures or legal)
                board.push(rng.choice(candidates))
    rows = list(seen.values())
    require(100 <= len(rows) <= 10000, 'unexpected bounded native corpus size')
    counts = dict(rows=len(rows), in_check=0, capture_or_promotion_bestmove=0,
                  missing_bestmove=0,
                  legal_en_passant=0, legal_castling=0, legal_promotion=0,
                  checkmate=0, stalemate=0)
    for row in rows:
        board = board_from_fen(row['fen'])
        counts['in_check'] += int(board.is_check())
        capture = matches(row)[1]
        counts['capture_or_promotion_bestmove'] += int(capture is True)
        counts['missing_bestmove'] += int(capture is None)
        counts['legal_en_passant'] += int(board.has_legal_en_passant())
        counts['legal_castling'] += int(any(board.is_castling(m) for m in board.legal_moves))
        counts['legal_promotion'] += int(any(m.promotion for m in board.legal_moves))
        counts['checkmate'] += int(board.is_checkmate())
        counts['stalemate'] += int(board.is_stalemate())
    require(all(counts.values()), 'native fixture missed a required state category')
    return rows, counts


def main():
    low_priority()
    output = ROOT / 'generated_boundaries_v2'
    storage_guard(output, allowance=20_000_000)
    output.mkdir()
    paths = [*HERE.glob('*.py'), Path(__file__).resolve()]
    pins = {str(p): sha256(p) for p in paths}
    save(output / 'RUN.json', {'source_files': pins, 'strength': 'UNPROVEN',
                              'hypothesis_version': hypothesis.__version__, 'seed_native': 5108})
    started = time.perf_counter()
    try:
        concatenated_games()
        print('PASS concatenated PGNs: ' + str(CASES), flush=True)
        rows, counts = native_cases()
        sample = output / 'generated_fens.jsonl'
        with sample.open('x', encoding='utf-8', newline='\n') as stream:
            for row in rows:
                stream.write(json.dumps(row, sort_keys=True) + '\n')
        save(output / 'fixture_categories.json', counts)
        report = native(output / 'native', sample, max_positions=len(rows))
        require(report['sample_positions'] == len(rows), 'native sample truncated')
        require(pins == {str(p): sha256(p) for p in paths}, 'source changed during probe')
        save(output / 'COMPLETE.json', {'status': 'PASS', 'generated_pgn_cases': CASES,
            'fixture_categories': counts, 'native_report_sha256': sha256(output / 'native/report.json'),
            'sample_sha256': sha256(sample), 'source_files': pins,
            'seconds': time.perf_counter()-started, 'strength': 'UNPROVEN',
            'purpose': 'Original synthetic fixtures only; not training labels or a strength test.'})
    except Exception as error:
        save(output / 'FAIL.json', {'status': 'FAIL', 'exception': repr(error),
             'notes': getattr(error, '__notes__', []), 'traceback': traceback.format_exc(),
             'completed_pgn_cases': CASES, 'source_files': pins})
        raise


if __name__ == '__main__':
    main()
