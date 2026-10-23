#!/usr/bin/env python3
"""One-shot closure after the original preparation tool session actually exits."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

import numpy as np

BASE = Path('/workspace/forge-nnue-handoff-20261023')
OUT = BASE / 'prepared-all13m-reservoir-attempt1'
FRESH = BASE / 'prepared-fresh-only-attempt1'
REPO_TOOLS = Path('/workspace/dwqww/tools/nnue')
sys.path.insert(0, str(REPO_TOOLS))
from residual_train import load_prepared_data  # Shared strict validator, not a new schema validator.


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def position_key(fen):
    return ' '.join(fen.split()[:4])


def save_new(path, value):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent,
                                         prefix=path.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)  # Atomic publish; fail rather than overwrite an existing receipt.
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def validate_closed():
    actual_tool_receipt_path = BASE / 'FULL-PREP-TOOL-RESULT.json'
    actual_tool = json.loads(actual_tool_receipt_path.read_text())
    if actual_tool['tool_session_id'] != 24911 or actual_tool['tool_result']['exit_code'] != 0:
        raise ValueError('Actual completed original tool receipt differs')
    wrapper = json.loads((BASE / 'data-prepare-all13m.result.json').read_text())
    if wrapper['returncode'] != 0:
        raise ValueError('Original preparation subprocess failed: ' + repr(wrapper))
    if (BASE / 'data-prepare-all13m.stderr').stat().st_size:
        raise ValueError('Original preparation stderr is not empty')
    train, val, manifest, manifest_sha = load_prepared_data(OUT)
    comparison = {}
    with np.load(FRESH / 'validation.npz', allow_pickle=False) as fresh_val:
        if set(fresh_val.files) != set(val):
            raise ValueError('Validation array names differ from the original fresh-only holdout')
        for name in sorted(val):
            reference = fresh_val[name]
            actual = val[name]
            same = (actual.dtype == reference.dtype and actual.shape == reference.shape
                    and actual.tobytes(order='C') == reference.tobytes(order='C'))
            if not same:
                raise ValueError('Validation array byte contents differ: ' + name)
            comparison[name] = {'dtype': str(actual.dtype), 'shape': list(actual.shape),
                                'array_bytes_sha256': hashlib.sha256(actual.tobytes(order='C')).hexdigest(),
                                'byte_identical_to_fresh_only': True}
    recipe = OUT / 'validation-provenance.jsonl'
    if recipe.read_bytes() != (FRESH / recipe.name).read_bytes():
        raise ValueError('Validation provenance bytes differ from the original fresh-only holdout')
    for name, info in manifest['artifacts'].items():
        if sha256(OUT / name) != info['sha256']:
            raise ValueError('Provenance artifact hash differs: ' + name)

    validation_rows = [json.loads(line) for line in recipe.read_text().splitlines()]
    validation_keys = {position_key(row['fen']) for row in validation_rows}
    validation_ids = set(manifest['split']['validation_game_ids'])
    train_ids = set(manifest['split']['train_game_ids'])
    if len(validation_rows) != len(val['score']) or {row['game_id'] for row in validation_rows} != validation_ids:
        raise ValueError('Validation row/game membership differs')
    fresh_source = BASE / 'generated-games-256-attempt1/games.jsonl'
    source_lines = {}
    with fresh_source.open() as stream:
        for number, line in enumerate(stream, 1):
            source_lines[number] = json.loads(line)
    for row in validation_rows:
        original = source_lines[row['source_line']]
        if (row['source_path'] != str(fresh_source) or row['legacy_game_identity_unknown'] is not False
                or any(row[key] != original[key] for key in ('fen', 'game_id', 'ply'))):
            raise ValueError('Validation row recipe does not match the authenticated original JSONL')

    counts, legacy_selected, known_train_games = Counter(), Counter(), set()
    with (OUT / 'train-provenance.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            counts['training_rows'] += 1
            if position_key(row['fen']) in validation_keys:
                raise ValueError('Actual first-four-FEN training/validation overlap')
            if type(row['source_line']) is not int or row['source_line'] < 1:
                raise ValueError('Invalid original source-line identity')
            if row['legacy_game_identity_unknown'] is True:
                if row['game_id'] is not None or row['ply'] is not None:
                    raise ValueError('Invented legacy game or ply identity')
                legacy_selected[row['source_path']] += 1
                counts['legacy_training_rows'] += 1
            else:
                if row['game_id'] not in train_ids or row['game_id'] in validation_ids:
                    raise ValueError('Fresh training game membership differs')
                known_train_games.add(row['game_id'])
                counts['fresh_training_rows'] += 1
    if counts['training_rows'] != len(train['score']):
        raise ValueError('Training recipe count differs from prepared arrays')
    if known_train_games != train_ids:
        raise ValueError('Actual fresh training recipe game set differs')
    per_source = manifest['legacy_per_source']
    expected_names = {f'forge_selfplay_{number}_head.txt'
                      for number in ('003', '004', '005', '006', '007', '008', '009', '010', '013')}
    if len(per_source) != 9 or {Path(path).name for path in per_source} != expected_names:
        raise ValueError('The exact nine declared legacy sources were not examined')
    if any(info['examined'] != 1500000 for info in per_source.values()):
        raise ValueError('A legacy source was not examined completely')
    if manifest['statistics']['legacy_rows_examined'] != 13500000:
        raise ValueError('Total examined legacy row count differs')
    if any(legacy_selected[path] != info.get('selected', 0) for path, info in per_source.items()):
        raise ValueError('Actual selected source recipe counts differ')
    receipts = sorted((OUT / 'native-probe-evidence').glob('batch-*.json'))
    if len(receipts) != manifest['native_probe_batches']:
        raise ValueError('Native batch receipt count differs')
    native_input_rows = 0
    for path in receipts:
        fact = json.loads(path.read_text())
        if fact['returncode'] != 0 or fact['stderr_bytes'] != 0 or fact['owned_process_reaped'] is not True:
            raise ValueError('Native batch closure differs: ' + str(path))
        native_input_rows += fact['input_rows']
    checks = {
        'status': 'PASS_FULL_PREP_INTEGRITY', 'utc': datetime.now(timezone.utc).isoformat(),
        'shared_strict_loader': 'tools.nnue.residual_train.load_prepared_data',
        'shared_strict_loader_source_sha256': sha256(REPO_TOOLS / 'residual_train.py'),
        'closure_checker_sha256': sha256(Path(__file__)),
        'manifest_path': str(OUT / 'manifest.json'), 'manifest_sha256': manifest_sha,
        'validation_array_comparison': comparison,
        'validation_recipe_byte_identical_to_fresh_only': True,
        'validation_recipe_sha256': sha256(recipe), 'validation_rows': len(val['score']),
        'validation_games': len(validation_ids), 'fresh_train_games': len(train_ids),
        'exact_first4fen_training_validation_overlap': 0,
        'actual_training_recipe_counts': dict(counts),
        'legacy_examined_rows': manifest['statistics']['legacy_rows_examined'],
        'legacy_per_source': per_source, 'native_batches': len(receipts),
        'native_input_rows': native_input_rows, 'native_successful_derived_streams_retained': False,
        'original_preparation_wrapper_result': wrapper,
        'original_tool_receipt_path': str(actual_tool_receipt_path),
        'original_tool_receipt_sha256': sha256(actual_tool_receipt_path),
        'scope': 'Prepared-data integrity and provenance only; no playing-strength conclusion',
    }
    evidence = BASE / 'FULL-PREP-INTEGRITY.json'
    save_new(evidence, checks)
    return {
        'status': 'PASS_PREPARED_DATA_CLOSED',
        'tool_session_id': 24911, 'actual_tool_exit_code': 0,
        'actual_preparation_subprocess_exit_code': wrapper['returncode'],
        'original_tool_receipt_path': str(actual_tool_receipt_path),
        'original_tool_receipt_sha256': sha256(actual_tool_receipt_path),
        'utc': datetime.now(timezone.utc).isoformat(),
        'manifest_path': str(OUT / 'manifest.json'), 'manifest_sha256': manifest_sha,
        'train_rows': len(train['score']), 'validation_rows': len(val['score']),
        'legacy_examined_rows': manifest['statistics']['legacy_rows_examined'],
        'legacy_source_count': len(per_source), 'legacy_per_source': per_source,
        'integrity_evidence_path': str(evidence), 'integrity_evidence_sha256': sha256(evidence),
        'next_action': 'Root owns the predeclared zero-initialized full-data training run, then the separate warm-start run.',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--actual-tool-exit-code', required=True, type=int)
    args = parser.parse_args()
    try:
        if args.actual_tool_exit_code != 0:
            raise ValueError('Original tool session actually exited ' + str(args.actual_tool_exit_code))
        receipt = validate_closed()
    except Exception as error:
        receipt = {'status': 'FAILED', 'tool_session_id': 24911,
                   'actual_tool_exit_code': args.actual_tool_exit_code,
                   'utc': datetime.now(timezone.utc).isoformat(),
                   'reason': type(error).__name__ + ': ' + str(error),
                   'next_action': 'Preserve this original attempt; no automatic retry.'}
        save_new(BASE / 'FULL-PREP-CLOSED.json', receipt)
        print(json.dumps(receipt), flush=True)
        raise
    save_new(BASE / 'FULL-PREP-CLOSED.json', receipt)
    print(json.dumps(receipt), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
