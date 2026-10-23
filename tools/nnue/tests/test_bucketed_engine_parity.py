#!/usr/bin/env python3
"""Actual Forge C++ versus exported eight-head trainer inference, without games.

Adapted from this repository's original test_engine_parity.py. Preserves original
probe streams, expected CP records and hashes. Distinct-head diagnostic exports
must distinguish a forced-head-zero control in every nonzero material bucket.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys

import chess
import numpy as np
import torch

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bucket_for_piece_count(count):
    if type(count) is not int:
        raise ValueError('Integer piece count required')
    return max(0, min(7, (count - 1) // 4))


def validate_head_layout(weights, require_distinct):
    if (weights.get('output_buckets') != 8
            or np.asarray(weights.get('bucket_w2')).shape != (8, 256)
            or np.asarray(weights.get('bucket_b2')).shape != (8,)):
        raise ValueError('Expected eight 256-input output heads and eight biases')
    heads = [np.asarray(weights['bucket_w2'][i]).tobytes()
             + np.asarray(weights['bucket_b2'][i]).tobytes() for i in range(8)]
    distinct = len(set(heads))
    if require_distinct and distinct != 8:
        raise ValueError('Diagnostic export must contain eight distinct heads')
    return {'output_buckets': 8, 'distinct_head_count': distinct,
            'distinct_head_diagnostic_required': require_distinct}


def informative_head_zero_control(rows, differences):
    return (all(rows.get(i, 0) > 0 for i in range(8))
            and differences.get(0, 0) == 0
            and all(differences.get(i, 0) > 0 for i in range(1, 8)))


def corpus(sample, count, seed):
    """Valid material-boundary seeds plus deterministic legal continuations."""
    records, seen, origins = [], set(), {}

    def add(board, origin):
        if not board.is_valid():
            raise ValueError('Invalid parity board: ' + board.fen(en_passant='fen'))
        key = ' '.join(board.fen(en_passant='fen').split()[:4])
        if key in seen or len(records) == count:
            return False
        seen.add(key); records.append(board.fen(en_passant='fen'))
        origins[origin] = origins.get(origin, 0) + 1
        return True

    starts = [
        chess.STARTING_FEN,
        'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1',
        '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1',
        '4k3/P7/8/8/8/8/7p/4K3 w - - 0 1',
        'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',
        '8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1',
        '4k3/8/8/8/8/8/4r3/4K3 w - - 0 1',
        '7k/6Q1/5K2/8/8/8/8/8 b - - 0 1',
        '4k3/8/8/8/8/8/8/4K3 w - - 0 1',
    ]
    boards = [chess.Board(fen) for fen in starts]
    # These are valid constructed inference fixtures, not generated training
    # games. Removing home-square non-kings cannot expose either home king to
    # an opposing rook/bishop/queen on the starting piece squares.
    initial = chess.Board()
    removable = sorted(square for square, piece in initial.piece_map().items()
                       if piece.piece_type != chess.KING)
    for pieces in range(2, 33):
        board = initial.copy(stack=False)
        board.castling_rights = 0
        for square in removable[:32 - pieces]:
            board.remove_piece_at(square)
        boards.append(board)
    boards += [board.mirror() for board in boards.copy()]
    # Seed both turns of every material bucket before potentially larger
    # sample files or first-move enumerations consume the requested capacity.
    for board in boards:
        add(board, 'valid_material_or_special_seed')
    for line in sample.read_text(encoding='ascii').splitlines():
        if line.strip():
            add(chess.Board(line.split('|', 1)[0].strip()), 'bundled_sample')
    special = {'castles': 0, 'en_passant': 0, 'promotions': 0, 'captures': 0}
    for board in boards:
        for move in sorted(board.legal_moves, key=lambda move: move.uci()):
            child = board.copy(stack=False); child.push(move)
            if add(child, 'special_or_material_first_move'):
                special['castles'] += int(board.is_castling(move))
                special['en_passant'] += int(board.is_en_passant(move))
                special['promotions'] += int(bool(move.promotion))
                special['captures'] += int(board.is_capture(move))
    rng = random.Random(seed)
    for walk in range(512):
        if len(records) == count:
            break
        board = boards[walk % len(boards)].copy(stack=False)
        for _ in range(256):
            add(board, 'legal_walk')
            moves = list(board.legal_moves)
            if not moves or len(records) == count:
                break
            board.push(moves[rng.randrange(len(moves))])
    if len(records) != count:
        raise ValueError(f'Only generated {len(records)} of {count} unique parity positions')
    return records, origins, special


def run_probe(probe, arguments, payload, out, stem):
    (out / (stem + '.stdin')).write_bytes(payload)
    command = [str(probe), *arguments]
    try:
        completed = subprocess.run(command, input=payload, capture_output=True,
                                   timeout=120, check=False)
        stdout, stderr, code, timeout = completed.stdout, completed.stderr, completed.returncode, False
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code, timeout = error.stdout or b'', error.stderr or b'', None, True
    (out / (stem + '.stdout')).write_bytes(stdout)
    (out / (stem + '.stderr')).write_bytes(stderr)
    (out / (stem + '.command.json')).write_text(json.dumps({
        'command': command, 'returncode': code, 'timed_out': timeout,
        'stdin_sha256': hashlib.sha256(payload).hexdigest(),
        'stdout_sha256': hashlib.sha256(stdout).hexdigest(),
        'stderr_sha256': hashlib.sha256(stderr).hexdigest()}, indent=2) + '\n')
    if timeout:
        raise TimeoutError('Probe timed out; original partial streams retained')
    return completed


def load_trainer(path):
    spec = importlib.util.spec_from_file_location('forge_bucketed_nnue_trainer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def integer_cp(logits):
    continuous = logits.numpy().reshape(-1) * np.float32(400.0) / np.float32(2.25)
    return np.trunc(np.clip(continuous, -30000, 30000)).astype(np.int64)


def run(args):
    args.out.mkdir(parents=True, exist_ok=False)
    args.created_output = True
    from include_parser import load_include
    paths = [args.probe, args.trainer, args.weights, args.sample, Path(__file__),
             HERE / 'engine_probe.cpp', HERE / 'include_parser.py', HERE / 'train_nnue.py']
    if args.reference_probe:
        paths.append(args.reference_probe)
    frozen = {str(path.resolve()): sha(path) for path in paths}
    weights = load_include(args.weights, expected_hidden=128)
    layout = validate_head_layout(weights, args.require_distinct_heads)
    if not weights['residual']:
        raise ValueError('Expected existing residual inference architecture')
    module = load_trainer(args.trainer)
    torch.set_num_threads(1)
    model = module.BucketedNNUE(qat=True).cpu().eval()
    module.load_initial(model, args.weights)
    forced_zero = None
    if args.require_distinct_heads:
        forced_zero = copy.deepcopy(model)
        with torch.no_grad():
            forced_zero.output.weight.copy_(model.output.weight[0:1].clone().expand_as(model.output.weight))
            forced_zero.output.bias.copy_(model.output.bias[0:1].clone().expand_as(model.output.bias))
    fens, origins, special = corpus(args.sample, args.positions, args.seed)
    payload = ('\n'.join(fens) + '\n').encode('ascii')
    completed = run_probe(args.probe, [], payload, args.out, 'actual-engine')
    if completed.returncode or completed.stderr:
        raise ValueError('Actual C++ probe failed; original streams retained')
    rows = [json.loads(line) for line in completed.stdout.splitlines()]
    if len(rows) != args.positions:
        raise ValueError('Probe row count differs from input')
    bucket_counts = {i: 0 for i in range(8)}
    bucket_turns = {(i, turn): 0 for i in range(8) for turn in (False, True)}
    wrong_zero_differences = {i: 0 for i in range(8)}
    integer_errors, feature_mismatches, differences, expected_records = [], [], [], []
    for start in range(0, len(fens), 128):
        selected = fens[start:start + 128]
        x = np.zeros((len(selected), 2, 768), dtype=np.float32)
        expected_buckets = []
        for offset, fen in enumerate(selected):
            index = start + offset; row = rows[index]; board = chess.Board(fen)
            expected = module.feature_indices(board)
            pieces = len(board.piece_map()); bucket = bucket_for_piece_count(pieces)
            expected_buckets.append(bucket); bucket_counts[bucket] += 1
            bucket_turns[(bucket, board.turn)] += 1
            if (row['index'] != index or row['hidden_size'] != 128 or not row['residual_mode']
                    or row['hce_only'] or not row['nnue_available']
                    or type(row['output_bucket']) is not int or row['output_bucket'] != bucket
                    or row['output_bucket_count'] != 8):
                raise ValueError(f'Actual architecture or selected bucket differs at row {index}')
            if (len(expected) != 2 or any(len(expected[p]) != pieces for p in (0, 1))
                    or len(row['features']) != 2
                    or any(sorted(row['features'][p]) != sorted(expected[p]) for p in (0, 1))):
                feature_mismatches.append(index)
            legal = list(board.legal_moves)
            terminal = not legal or board.is_insufficient_material() or board.halfmove_clock >= 100
            tactical = any(board.is_capture(move) or move.promotion or board.gives_check(move) for move in legal)
            if (row['in_check'] != board.is_check() or row['terminal'] != terminal
                    or row['has_tactical_legal_move'] != tactical):
                raise ValueError(f'Legal/filter flags differ at row {index}')
            for perspective in (0, 1):
                x[offset, perspective, expected[perspective]] = 1.0
        with torch.no_grad():
            tensor = torch.from_numpy(x)
            if module.bucket_indices(tensor).tolist() != expected_buckets:
                raise ValueError('Trainer bucket indices differ from actual board piece counts')
            predicted = integer_cp(model(tensor))
            zero_predicted = integer_cp(forced_zero(tensor)) if forced_zero is not None else None
        for offset, cp in enumerate(predicted):
            index = start + offset; engine_cp = rows[index]['nnue_cp_stm']; bucket = expected_buckets[offset]
            error = abs(int(cp) - engine_cp); integer_errors.append(error)
            zero_cp = int(zero_predicted[offset]) if zero_predicted is not None else None
            if zero_cp is not None:
                wrong_zero_differences[bucket] += int(zero_cp != int(cp))
            expected_records.append({'index': index, 'bucket': bucket, 'trainer_cp': int(cp),
                                     'engine_cp': engine_cp, 'forced_head_zero_cp': zero_cp})
            if error:
                differences.append({'index': index, 'bucket': bucket, 'engine_cp': engine_cp,
                                    'trainer_cp': int(cp), 'error_cp': error})
    (args.out / 'python-expected-cp.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in expected_records))
    controls = []
    for name, invalid in [('missing_king', b'8/8/8/8/8/8/8/4K3 w - - 0 1\n'),
                          ('extra_field', (fens[0] + ' unexpected\n').encode('ascii')), ('empty', b'')]:
        rejected = run_probe(args.probe, [], invalid, args.out, 'invalid-' + name)
        controls.append({'name': name, 'rejected': rejected.returncode != 0 and bool(rejected.stderr)})
    hce = run_probe(args.probe, ['--hce-only'], payload, args.out, 'hce-only')
    hce_rows = [json.loads(line) for line in hce.stdout.splitlines()]
    hce_equal = (not hce.returncode and not hce.stderr and len(hce_rows) == len(rows)
                 and all({k: v for k, v in a.items() if k not in ('nnue_cp_stm', 'hce_only')}
                         == {k: v for k, v in b.items() if k not in ('nnue_cp_stm', 'hce_only')}
                         and b['nnue_cp_stm'] is None and b['hce_only'] is True
                         for a, b in zip(rows, hce_rows)))
    reference_equal = None
    if args.reference_probe:
        reference = run_probe(args.reference_probe, [], payload, args.out, 'reference-shipped-engine')
        reference_rows = [json.loads(line) for line in reference.stdout.splitlines()]
        reference_equal = (not reference.returncode and not reference.stderr and len(reference_rows) == len(rows)
                           and all({k: v for k, v in a.items() if k not in ('output_bucket', 'output_bucket_count')}
                                   == {k: v for k, v in b.items() if k not in ('output_bucket', 'output_bucket_count')}
                                   for a, b in zip(rows, reference_rows)))
    changed = [name for name, expected in frozen.items() if sha(name) != expected]
    informative = (informative_head_zero_control(bucket_counts, wrong_zero_differences)
                   if args.require_distinct_heads else None)
    passed = (not feature_mismatches and max(integer_errors) <= 1 and hce_equal
              and not changed and all(c['rejected'] for c in controls) and all(special.values())
              and all(bucket_turns.values()) and reference_equal is not False
              and (informative is True if args.require_distinct_heads else True))
    artifacts = {path.name: {'sha256': sha(path), 'bytes': path.stat().st_size}
                 for path in sorted(args.out.iterdir()) if path.is_file()}
    result = {
        'status': 'PASS' if passed else 'FAIL', 'utc': datetime.now(timezone.utc).isoformat(),
        'positions': len(fens), 'seed': args.seed, 'hidden_size': 128, 'residual_mode': True, **layout,
        'integer_cp_tolerance': 1, 'maximum_integer_cp_error': max(integer_errors),
        'exact_integer_matches': sum(error == 0 for error in integer_errors),
        'within_one_cp': sum(error <= 1 for error in integer_errors),
        'feature_mismatch_count': len(feature_mismatches), 'feature_mismatch_indices': feature_mismatches,
        'different_integer_rows': differences, 'bucket_positions': bucket_counts,
        'bucket_turn_positions': {f'{i}:{"white" if turn else "black"}': n for (i, turn), n in bucket_turns.items()},
        'head_zero_control_different_integer_rows_by_bucket': wrong_zero_differences,
        'head_zero_control_informative': informative, 'hce_only_records_match': bool(hce_equal),
        'reference_shipped_records_equal': reference_equal, 'invalid_input_controls': controls,
        'corpus_origins': origins, 'special_first_moves_included': special,
        'filter_flags_match_python_chess': True, 'probe_sha256': sha(args.probe),
        'weights_sha256': weights['sha256'], 'trainer_sha256': sha(args.trainer),
        'probe_source_sha256': sha(HERE / 'engine_probe.cpp'), 'sample_sha256': sha(args.sample),
        'fen_input_sha256': hashlib.sha256(payload).hexdigest(), 'frozen_inputs_sha256': frozen,
        'changed_inputs': changed, 'artifacts': artifacts,
        'torch_version': torch.__version__, 'numpy_version': np.__version__, 'python_chess_version': chess.__version__,
        'scope': 'Eight-bucket C++/export inference and legal/filter flags only; no training, loss, speed, games or Elo conclusion.'}
    with (args.out / 'RESULT.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'positions', 'maximum_integer_cp_error',
        'exact_integer_matches', 'feature_mismatch_count', 'bucket_positions', 'head_zero_control_informative',
        'reference_shipped_records_equal')}, indent=2))
    return 0 if passed else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--probe', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--weights', type=Path, default=REPO / 'src/nnue_weights.inc')
    p.add_argument('--trainer', type=Path, default=HERE / 'train_bucketed_nnue.py')
    p.add_argument('--sample', type=Path, default=HERE / 'examples/forge_sample.txt')
    p.add_argument('--positions', type=int, default=10000)
    p.add_argument('--seed', type=int, default=20261023)
    p.add_argument('--require-distinct-heads', action='store_true')
    p.add_argument('--reference-probe', type=Path)
    args = p.parse_args()
    if not 1000 <= args.positions <= 10000 or args.seed < 0:
        p.error('Expected 1000..10000 positions and a nonnegative seed')
    args.probe = args.probe.resolve()
    try:
        return run(args)
    except Exception as error:
        if getattr(args, 'created_output', False) and not (args.out / 'RESULT.json').exists():
            with (args.out / 'RESULT.json').open('x') as stream:
                json.dump({'status': 'FAIL_TOOL_EXCEPTION', 'error_type': type(error).__name__,
                           'error': str(error), 'utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2)
        raise


if __name__ == '__main__':
    raise SystemExit(main())
