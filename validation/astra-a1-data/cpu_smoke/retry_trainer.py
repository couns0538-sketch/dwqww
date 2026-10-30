#!/usr/bin/env python3
"""Retry only the trainer after the retained wrapper mkdir error.
IDEA_SOURCE: unchanged Forge trainer's new-run-directory contract.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import prepare_and_run as original

root = Path(__file__).resolve().parent
run = Path('/tmp/astra-a1-cpu-smoke-run-retry1')
if run.exists(): raise FileExistsError(run)
selection = json.loads((root/'selection.json').read_text())
for expected in selection['inputs_before']:
    path = Path(expected['path'])
    if path.name == 'prepare_and_run.py':
        path = root/'prepare_and_run_failed_v1.py'
        if original.file_hash(path) != expected['sha256']:
            raise ValueError('Failed wrapper snapshot changed')
    elif original.metadata(path) != expected:
        raise ValueError('Prepared smoke input/source changed: '+str(path))
for expected in selection['outputs']:
    if original.metadata(Path(expected['path'])) != expected:
        raise ValueError('Prepared output changed')
argv = json.loads((root/'trainer.command.json').read_text())['argv']
argv[-1] = str(run)
original.run_logged('trainer_retry1',argv)
text = (root/'trainer_retry1.stdout').read_text()
epoch = re.search(r'EPOCH 1/1.*train_mse=([0-9.eE+-]+).*HOLDOUT n=512.*mse_teacher=([0-9.eE+-]+)',text)
if not epoch or not all(math.isfinite(float(x)) for x in epoch.groups()):
    raise ValueError('Missing/nonfinite final losses')
if not (run/'epoch001-step000000004.pt').exists() or 'Finished: 256 positions' not in text:
    raise ValueError('Four-step checkpoint or presented count missing')
for expected in selection['inputs_before']:
    if Path(expected['path']).name != 'prepare_and_run.py' and original.metadata(Path(expected['path'])) != expected:
        raise ValueError('Input/source changed during training')
original.record_json(root/'result_retry1.json',{
    'status':'PASS_CPU_TRAINER_COMPATIBILITY_SMOKE',
    'train_mse_printed':float(epoch[1]),'holdout_teacher_mse_printed':float(epoch[2]),
    'trained_updates':4,'presented_training_rows':256,'train_rows_loaded':512,'holdout_rows_loaded':512,
    'unchanged_input_and_source_hashes_verified':True,
    'trainer_sha256':original.file_hash(original.TRAINER),
    'outputs':[original.metadata(p) for p in sorted(run.iterdir()) if p.is_file()],
    'initial_failure':'Smoke wrapper pre-created run dir; trainer rejected it before any updates. Original files retained.',
    'scope':'Compatibility/finite-loss smoke only; no network adoption, training-gain or Elo claim.'})
print((root/'result_retry1.json').read_text())
