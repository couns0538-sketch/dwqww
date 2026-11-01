#!/usr/bin/env python3
"""Original NumPy logistic regression for Forge root-iteration telemetry.

No chess-engine or third-party regression implementation is incorporated.
Features are computed using the same integer transforms as the C++ model.
All empirical artifacts are UNPROVEN with respect to playing strength.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import sys

# Bound BLAS threads before importing NumPy, including on a busy shared host.
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
import numpy as np

FEATURES = ['bias', 'depth/16', 'changed', 'node_fraction',
            'clip(score_cp,-2000,2000)/1000',
            'clip(score_delta_cp,-1000,1000)/1000', 'min(elapsed_ms/soft_ms,4)']
OPTIONS = ['TmFitBias', 'TmFitDepth', 'TmFitChanged', 'TmFitEffort',
           'TmFitScore', 'TmFitDelta', 'TmFitElapsed']


def trunc_div(n, d):
    """Integer division toward zero, matching C++ for negative feature values."""
    return np.where(n < 0, -((-n) // d), n // d)


def features_q10(r):
    for key in ('depth', 'changed', 'node_fraction', 'score_cp',
                'score_delta_cp', 'elapsed_ms', 'soft_ms'):
        if key not in r or isinstance(r[key], bool) or not isinstance(r[key], (int, float)):
            raise ValueError(f'missing/non-numeric feature {key}')
        if not math.isfinite(r[key]):
            raise ValueError(f'non-finite feature {key}')
    if not 1 <= r['depth'] <= 64 or r['depth'] != int(r['depth']):
        raise ValueError('depth must be an integer in 1..64')
    if r['changed'] not in (0, 1):
        raise ValueError('changed must be 0 or 1')
    if not 0 <= r['node_fraction'] <= 1:
        raise ValueError('node_fraction outside 0..1')
    if r['elapsed_ms'] < 0 or r['soft_ms'] <= 0:
        raise ValueError('clock data requires elapsed_ms >= 0 and soft_ms > 0')
    for key in ('score_cp', 'score_delta_cp', 'elapsed_ms', 'soft_ms'):
        if r[key] != int(r[key]):
            raise ValueError(f'{key} must be integral')
    # Optional exact integer effort avoids decimal serialization roundoff.
    effort = int(r.get('node_fraction_q10', int(r['node_fraction'] * 1024)))
    if not 0 <= effort <= 1024:
        raise ValueError('node_fraction_q10 outside 0..1024')
    return np.array([1024, int(r['depth']) * 64, int(r['changed']) * 1024,
                     effort, math.trunc(max(-2000, min(2000, r['score_cp'])) * 1024 / 1000),
                     math.trunc(max(-1000, min(1000, r['score_delta_cp'])) * 1024 / 1000),
                     min(4096, int(r['elapsed_ms']) * 1024 // int(r['soft_ms']))], dtype=np.int64)


@dataclass
class Dataset:
    rows: list
    x_q10: np.ndarray
    y: np.ndarray
    groups: np.ndarray
    excluded_final: int
    excluded_incomplete: int
    returned_move_disagreements: int


def prepare(records, require_seals=False):
    """Label against the last completed iteration, never the possibly revised UCI response."""
    searches = defaultdict(list)
    for r in records:
        if require_seals and not all(k in r for k in ('complete', 'final_best_move',
                                                       'search_iteration_index', 'search_iteration_count')):
            raise ValueError('unsealed search record: final response and iteration count/index required')
        if not all(k in r for k in ('game_id', 'search_id', 'best_move')):
            raise ValueError('records require game_id, search_id, best_move')
        if not isinstance(r['best_move'], str) or len(r['best_move']) not in (4, 5):
            raise ValueError('best_move must be a UCI move')
        features_q10(r)
        key = (str(r['game_id']), str(r['search_id']))
        previous = searches[key]
        if previous and r['depth'] <= previous[-1]['depth']:
            raise ValueError(f'nonincreasing or duplicate depth in search {key}')
        previous.append(r)
    rows, labels, groups = [], [], []
    excluded_final = excluded_incomplete = returned_move_disagreements = 0
    for key, sequence in searches.items():
        final_move = sequence[-1]['best_move']
        if any('search_iteration_count' in r or 'search_iteration_index' in r for r in sequence):
            if any(r.get('search_iteration_index') != index or
                   r.get('search_iteration_count') != len(sequence)
                   for index, r in enumerate(sequence)):
                excluded_incomplete += len(sequence)
                continue
        if any(r.get('complete', True) is not True for r in sequence):
            excluded_incomplete += len(sequence)
            continue
        returned_moves = {r.get('final_best_move', final_move) for r in sequence}
        if len(returned_moves) != 1:
            raise ValueError(f'inconsistent final response receipt for {key}')
        # An interrupted later iteration may revise the returned move. Dropping
        # those searches would preferentially remove unstable cases. The task's
        # target is the final *completed iteration*, so preserve its labels.
        returned_move_disagreements += int(next(iter(returned_moves)) != final_move)
        pair_ids = {str(r.get('pair_id', r['game_id'])) for r in sequence}
        if len(pair_ids) != 1:
            raise ValueError(f'inconsistent pair/group identifier for {key}')
        excluded_final += 1
        for r in sequence[:-1]:
            rows.append(r)
            labels.append(int(r['best_move'] != final_move))
            groups.append(next(iter(pair_ids)))
    if not rows:
        raise ValueError('no eligible non-final completed iterations')
    return Dataset(rows, np.stack([features_q10(r) for r in rows]),
                   np.array(labels, dtype=np.float64), np.array(groups),
                   excluded_final, excluded_incomplete, returned_move_disagreements)


def group_split(groups, seed):
    keys = np.unique(groups)
    if len(keys) < 5:
        raise ValueError('at least five independent games/opening pairs required')
    shuffled = np.random.default_rng(seed).permutation(keys)
    count = max(1, int(math.ceil(0.2 * len(keys))))
    heldout = set(shuffled[:count])
    test = np.array([g in heldout for g in groups])
    return ~test, test


def sigmoid(z):
    z = np.asarray(z, dtype=float)
    e = np.exp(-np.abs(z))
    return np.where(z >= 0, 1 / (1 + e), e / (1 + e))


def auc(y, scores):
    """Mann-Whitney AUC with average ranks for tied predictions."""
    positives = int(np.sum(y == 1))
    negatives = int(np.sum(y == 0))
    if positives == 0 or negatives == 0:
        return None
    if positives + negatives != len(y) or len(scores) != len(y):
        raise ValueError('AUC requires aligned binary labels')
    order = np.argsort(scores, kind='stable')
    ranks = np.empty(len(scores), dtype=float)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and scores[order[end]] == scores[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2
        start = end
    return float((ranks[y == 1].sum() - positives * (positives + 1) / 2) /
                 (positives * negatives))


def fit_logistic(x, y, ridge=0.001, iterations=80):
    """Damped Newton minimization of mean binary log loss plus L2 penalty."""
    if len(np.unique(y)) != 2:
        raise ValueError('training partition needs both labels')
    beta = np.zeros(x.shape[1])
    penalty = np.full(x.shape[1], ridge)
    penalty[0] = 0

    def loss(b):
        z = x @ b
        return float(np.mean(np.logaddexp(0, z) - y * z) + 0.5 * np.sum(penalty * b * b))

    for _ in range(iterations):
        p = sigmoid(x @ beta)
        gradient = x.T @ (p - y) / len(y) + penalty * beta
        hessian = (x.T * (p * (1 - p))) @ x / len(y) + np.diag(penalty + 1e-10)
        step = np.linalg.solve(hessian, gradient)
        old_loss = loss(beta)
        scale = 1.0
        while scale > 2 ** -20 and loss(beta - scale * step) > old_loss:
            scale *= 0.5
        beta -= scale * step
        if np.max(np.abs(scale * step)) < 1e-8:
            break
    if not np.isfinite(beta).all():
        raise ValueError('non-finite fit')
    return beta


def quantize(beta):
    q = np.rint(beta * 4096).astype(np.int64)
    if (np.abs(q) > 131072).any():
        raise ValueError('fitted coefficient exceeds engine tunable range; do not silently clip')
    return q


def sigmoid_lut():
    return np.floor(sigmoid(np.arange(-128, 129) / 16) * 1024 + 0.5).astype(np.int64)


def predict_q10(x_q10, beta_q12):
    z_q12 = trunc_div(x_q10 @ beta_q12, 1024)
    index = (np.clip(z_q12, -32768, 32768) + 32768 + 128) // 256
    return sigmoid_lut()[index]


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_records(paths):
    records, sources = [], []
    for path in paths:
        size = path.stat().st_size
        before = sha256(path)
        count = 0
        with path.open(encoding='utf-8-sig') as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise ValueError('record is not an object')
                except (ValueError, TypeError) as error:
                    raise ValueError(f'{path}:{number}: {error}') from error
                records.append(record)
                count += 1
        if before != sha256(path) or size != path.stat().st_size:
            raise ValueError(f'input changed during fit: {path}')
        sources.append(dict(path=str(path.resolve()), sha256=before, bytes=size, rows=count))
    return records, sources


def partition_summary(data, mask):
    rows = [r for r, selected in zip(data.rows, mask) if selected]
    x = data.x_q10[mask] / 1024
    return dict(rows=len(rows), searches=len({(str(r['game_id']), str(r['search_id'])) for r in rows}),
                games=len({str(r['game_id']) for r in rows}), groups=len(set(data.groups[mask])),
                positives=int(data.y[mask].sum()), feature_min=x.min(axis=0).tolist(),
                feature_max=x.max(axis=0).tolist(), feature_std=x.std(axis=0).tolist(),
                constant_features=[FEATURES[i] for i in range(x.shape[1]) if np.ptp(x[:, i]) == 0])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='+', type=Path)
    parser.add_argument('--output', type=Path, required=True, help='new evidence directory; never overwrite')
    parser.add_argument('--seed', type=int, default=8128)
    parser.add_argument('--minimum-iterations', type=int, default=50000)
    parser.add_argument('--ridge', type=float, default=0.001)
    args = parser.parse_args(argv)
    if args.ridge <= 0 or args.minimum_iterations < 1:
        parser.error('ridge and minimum-iterations must be positive')
    records, sources = read_records(args.inputs)
    if len(records) < args.minimum_iterations:
        raise ValueError(f'only {len(records)} iterations; required {args.minimum_iterations}')
    data = prepare(records, require_seals=True)
    train, test = group_split(data.groups, args.seed)
    x = data.x_q10 / 1024
    beta = fit_logistic(x[train], data.y[train], ridge=args.ridge)
    q = quantize(beta)
    p = sigmoid(x @ beta)
    qp = predict_q10(data.x_q10, q) / 1024
    holdout_auc = auc(data.y[test], p[test])
    if holdout_auc is None:
        raise ValueError('held-out partition has only one label; report inadequate data, do not reshuffle')
    report = dict(status='UNPROVEN', seed=args.seed, sources=sources,
                  fitter_sha256=sha256(Path(__file__)), numpy_version=np.__version__,
                  raw_iterations=len(records), eligible_iterations=len(data.rows),
                  excluded_final_iterations=data.excluded_final,
                  excluded_incomplete_iterations=data.excluded_incomplete,
                  returned_move_disagreement_searches=data.returned_move_disagreements,
                  label='current completed best_move differs from last completed iteration best_move; terminal row excluded',
                  split_unit='pair_id when supplied, else game_id',
                  train_groups=sorted(set(data.groups[train])), test_groups=sorted(set(data.groups[test])),
                  train_rows=int(train.sum()), test_rows=int(test.sum()),
                  train_partition=partition_summary(data, train), test_partition=partition_summary(data, test),
                  dependence_note='Rows within searches/games are correlated; row count is not an independent effective sample count. Opening-group holdout does not prove transposition disjointness.',
                  train_positive_rate=float(data.y[train].mean()),
                  test_positive_rate=float(data.y[test].mean()), ridge=args.ridge,
                  holdout_auc=holdout_auc, holdout_auc_fixed=auc(data.y[test], qp[test]),
                  holdout_log_loss=float(np.mean(np.logaddexp(0, x[test] @ beta) - data.y[test] * (x[test] @ beta))),
                  holdout_brier=float(np.mean((p[test] - data.y[test]) ** 2)),
                  fixed_probability_max_abs_error=float(np.max(np.abs(qp - p))),
                  features=FEATURES, coefficients=beta.tolist(),
                  coefficients_q12=dict(zip(OPTIONS, q.tolist())), sigmoid_lut_q10=sigmoid_lut().tolist(),
                  mapping_status='UNMEASURED: choose A/B/Lo/Hi on separate calibration runs; verify actual 200-game time usage',
                  gate_status='UNPROVEN: crew SPRT and longer-TC confirmation required')
    args.output.mkdir(parents=True, exist_ok=False)
    # Exactly ceil(1%) of raw iterations; fixed RNG independent of holdout shuffling.
    selected = np.sort(np.random.default_rng(args.seed + 1).choice(
        len(records), size=max(1, math.ceil(len(records) / 100)), replace=False))
    sample = args.output / 'sample_1pct.jsonl'
    with sample.open('x', encoding='utf-8', newline='\n') as stream:
        for index in selected:
            stream.write(json.dumps(records[index], sort_keys=True, separators=(',', ':')) + '\n')
    report['sample'] = dict(path=sample.name, sha256=sha256(sample), rows=len(selected), bytes=sample.stat().st_size)
    with (args.output / 'fit.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    with (args.output / 'coefficients.uci').open('x', encoding='utf-8', newline='\n') as stream:
        for name, value in report['coefficients_q12'].items():
            stream.write(f'setoption name {name} value {value}\n')
    print(json.dumps({k: report[k] for k in ('status', 'raw_iterations', 'train_rows', 'test_rows',
                                           'holdout_auc', 'holdout_auc_fixed', 'coefficients_q12')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
