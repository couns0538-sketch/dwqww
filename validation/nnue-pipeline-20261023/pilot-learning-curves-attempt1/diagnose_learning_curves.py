"""Read-only constant pure-teacher checkpoint diagnostic; no training/selection."""
from pathlib import Path
import csv
import hashlib
import json
import math
import sys
import time

import torch
sys.path.insert(0, '/workspace/dwqww/tools/nnue')
from residual_train import NNUE, _load_initial, evaluate, load_prepared_data, verify_unchanged_inputs

ROOT = Path('/workspace/dwqww')
HANDOFF = Path('/workspace/forge-nnue-handoff-20261023')
OUT = Path(__file__).resolve().parent
DATA = HANDOFF / 'prepared-fresh-only-attempt1'
RUNS = {'zero': HANDOFF / 'pilot-fresh14895-zero20-attempt1',
        'warm': HANDOFF / 'pilot-fresh14895-warm20-attempt1'}
EXPECTED_MANIFEST = 'c4054706afa50324398a6ef6319da5341da10d02a21736aacaf25d9639e00653'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

bound = {}
def bind(path):
    path = path.resolve()
    record = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest(path)}
    previous = bound.get(str(path))
    if previous is not None and previous != record:
        raise ValueError(f'Changed bound input: {path}')
    bound[str(path)] = record
    return record

def read_json(path):
    bind(path)
    return json.loads(path.read_text())

def require(condition, message):
    if not condition:
        raise ValueError(message)

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

start = time.monotonic()
torch.set_num_threads(1)
for name in ['residual_train.py', 'train_nnue.py', 'include_parser.py', 'engine_contract.json']:
    bind(ROOT / 'tools/nnue' / name)
bind(Path(__file__))
train, validation, manifest, manifest_sha = load_prepared_data(DATA)
require(manifest_sha == EXPECTED_MANIFEST, 'Unexpected prepared manifest revision')
require(len(train['score']) == 14895 and len(validation['score']) == 4149, 'Unexpected fixed row counts')
bind(DATA / 'manifest.json')
for name in manifest['files']:
    bind(DATA / name)
for name, entry in manifest.get('artifacts', {}).items():
    require(digest(DATA / name) == entry['sha256'], f'Artifact hash mismatch: {name}')
    bind(DATA / name)

records = []
summaries = {}
with (OUT / 'checkpoint-metrics.jsonl').open('x') as progress:
    for label, run in RUNS.items():
        summary = read_json(run / 'summary.json')
        require(summary['status'] == 'completed' and summary['input_integrity'] == 'passed', f'Incomplete original run: {label}')
        require(summary['epochs_completed'] == 20 and len(summary['epochs']) == 20, f'Wrong epoch count: {label}')
        require(summary['training_count'] == 14895 and summary['validation_count'] == 4149, f'Wrong original counts: {label}')
        require(summary['manifest_sha256'] == manifest_sha, f'Wrong original data revision: {label}')
        require(Path(summary['config']['data_dir']).resolve() == DATA, f'Different data directory: {label}')
        require(read_json(run / 'input-manifest.json') == manifest, f'Original manifest snapshot differs: {label}')
        summaries[label] = summary
        for epoch in range(21):
            stem = 'initial' if epoch == 0 else f'epoch-{epoch:04d}'
            report = read_json(run / ('initial-report.json' if epoch == 0 else f'{stem}-report.json'))
            require(report['manifest_sha256'] == manifest_sha, f'Report manifest differs: {label}/{stem}')
            require(report['training_count'] == 14895 and report['validation_count'] == 4149, f'Report counts differ: {label}/{stem}')
            original = report['initial'] if epoch == 0 else report['latest']
            require(original['count'] == 4149, f'Validation was not complete: {label}/{stem}')
            if epoch:
                require(original == summary['epochs'][epoch - 1], f'Per-epoch report differs from final ledger: {label}/{stem}')
                require(original['epoch'] == epoch, f'Epoch identity differs: {label}/{stem}')
            else:
                require(original == summary['initial'], f'Initial report differs: {label}')
            metadata = read_json(run / 'exports' / (stem + '.json'))
            require(metadata['epoch'] == epoch and metadata['manifest_sha256'] == manifest_sha, f'Export provenance differs: {label}/{stem}')
            require(metadata['metrics']['count'] == 4149, f'Export validation count differs: {label}/{stem}')
            require(metadata['metrics']['teacher_mse_combined'] == original['teacher_mse_combined'], f'Export metric differs: {label}/{stem}')
            inc = bind(run / 'exports' / (stem + '.inc'))
            binary = bind(run / 'exports' / (stem + '.bin'))
            require(inc['sha256'] == metadata['inc_sha256'] and binary['sha256'] == metadata['bin_sha256'], f'Export hash mismatch: {label}/{stem}')
            model = NNUE([128], qat=True)
            identity = _load_initial(model, inc['path'])
            require(identity['sha256'] == inc['sha256'], f'Loaded export hash differs: {label}/{stem}')
            measured = evaluate(model, train, batch_size=1024, result_weight=0.0)
            require(measured['count'] == 14895, 'Training evaluation was truncated')
            require(math.isfinite(measured['teacher_mse_combined']), 'Nonfinite fixed-target metric')
            record = {'run': label, 'epoch': epoch, 'stem': stem,
                      'export_inc_sha256': inc['sha256'], 'export_bin_sha256': binary['sha256'],
                      'training_count': measured['count'], 'validation_count': original['count'],
                      'training_pure_teacher_mse_combined': measured['teacher_mse_combined'],
                      'training_pure_teacher_mse_hce': measured['teacher_mse_hce'],
                      'training_pure_teacher_mse_net_only': measured['teacher_mse_net_only'],
                      'validation_pure_teacher_mse_combined_original': original['teacher_mse_combined'],
                      'validation_pure_teacher_mse_hce_original': original['teacher_mse_hce'],
                      'original_online_ramped_training_target_mse': original.get('training_target_mse'),
                      'original_result_weight': original.get('result_weight', 0.0)}
            records.append(record)
            progress.write(json.dumps(record, allow_nan=False) + '\n')
            progress.flush()
            print(json.dumps({'run': label, 'epoch': epoch, 'train_pure_teacher_mse': record['training_pure_teacher_mse_combined'],
                              'validation_pure_teacher_mse_original': record['validation_pure_teacher_mse_combined_original']}), flush=True)

verify_unchanged_inputs(DATA, manifest, manifest_sha)
for path, before in list(bound.items()):
    require(bind(Path(path)) == before, f'Bound input changed after evaluation: {path}')
write_json(OUT / 'input-identities.json', sorted(bound.values(), key=lambda item: item['path']))
diagnostics = {}
for label in RUNS:
    rows = [r for r in records if r['run'] == label]
    first, last = rows[0], rows[-1]
    train_delta = last['training_pure_teacher_mse_combined'] - first['training_pure_teacher_mse_combined']
    val_delta = last['validation_pure_teacher_mse_combined_original'] - first['validation_pure_teacher_mse_combined_original']
    diagnostics[label] = {'initial_training_mse': first['training_pure_teacher_mse_combined'],
                          'final_training_mse': last['training_pure_teacher_mse_combined'],
                          'training_final_minus_initial': train_delta,
                          'initial_validation_mse': first['validation_pure_teacher_mse_combined_original'],
                          'final_validation_mse': last['validation_pure_teacher_mse_combined_original'],
                          'validation_final_minus_initial': val_delta,
                          'training_down_validation_up_from_initial': train_delta < 0 and val_delta > 0,
                          'minimum_training_mse_epoch': min(rows, key=lambda r: r['training_pure_teacher_mse_combined'])['epoch'],
                          'minimum_validation_mse_epoch_diagnostic_only': min(rows, key=lambda r: r['validation_pure_teacher_mse_combined_original'])['epoch'],
                          'original_selection_unchanged': summaries[label]['best']}
result = {'status': 'completed', 'manifest_sha256': manifest_sha,
          'training_rows': 14895, 'validation_rows': 4149, 'checkpoint_count': len(records),
          'total_training_rows_evaluated': sum(r['training_count'] for r in records),
          'threads': 1, 'batch_size': 1024,
          'training_metric': 'Complete fixed training set pure search-score teacher probability MSE of HCE plus engine-quantized residual export',
          'validation_metric': 'Original complete fixed heldout pure-teacher MSE read from authenticated original per-epoch reports; not rerun',
          'ramped_online_loss_is_a_different_metric': True,
          'diagnostics': diagnostics, 'records': records,
          'inputs_unchanged': True, 'selection_modified': False, 'confidence_interval_claim': None, 'elo_claim': None,
          'elapsed_seconds': time.monotonic() - start}
write_json(OUT / 'metrics.json', result)
with (OUT / 'curves.csv').open('x', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
report = ['# Fixed pure-teacher pilot learning curves', '',
          'This read-only diagnostic evaluates every exported checkpoint on the same complete 14,895 fresh training positions. '
          'Validation MSE comes from the authenticated original full 4,149-position reports. Teacher targets are constant across epochs. '
          'The original online training loss uses changing result weights and parameters during each epoch; it is a different metric and cannot establish teacher-loss learning or overfitting.', '',
          '| Run | Initial train MSE | Epoch 20 train MSE | Initial validation MSE | Epoch 20 validation MSE |',
          '| --- | ---: | ---: | ---: | ---: |']
for label, d in diagnostics.items():
    report.append(f"| {label} | {d['initial_training_mse']:.10f} | {d['final_training_mse']:.10f} | {d['initial_validation_mse']:.10f} | {d['final_validation_mse']:.10f} |")
report += ['', 'Train-down/heldout-up divergence is consistent with overfitting to these small fresh training games. '
               'It does not establish behavior on the full legacy corpus or playing strength. '
               'All 42 exports, reports, source modules and prepared inputs were authenticated; original selection is unchanged. '
               'No training, model modification, CI, acceptance or Elo conclusion is produced.', '',
          '| Epoch | Zero train MSE | Zero original validation MSE | Warm train MSE | Warm original validation MSE |',
          '| ---: | ---: | ---: | ---: | ---: |']
for epoch in range(21):
    a, b = records[epoch], records[21 + epoch]
    report.append(f"| {epoch} | {a['training_pure_teacher_mse_combined']:.10f} | {a['validation_pure_teacher_mse_combined_original']:.10f} | {b['training_pure_teacher_mse_combined']:.10f} | {b['validation_pure_teacher_mse_combined_original']:.10f} |")
(OUT / 'REPORT.md').write_text('\n'.join(report) + '\n')
print(json.dumps({'status': 'completed', 'checkpoint_count': len(records), 'diagnostics': diagnostics}), flush=True)
