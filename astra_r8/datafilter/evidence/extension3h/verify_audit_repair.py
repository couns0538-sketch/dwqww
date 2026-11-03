"""Fresh evidence for the optimization-safe audit repair; no training. UNPROVEN."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter')
ROOT = Path('C:/astra8_data/extension3h_20261103')
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
os.environ.update(PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='',
                  HIP_VISIBLE_DEVICES='', ROCR_VISIBLE_DEVICES='',
                  OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')

from filter_positions import low_priority, run_filter, sha256
from resource_policy import storage_guard
from audit_followup import run as audit
from refresh_handoff import refresh
from verify_handoff import verify


def write(path, value):
    encoded = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'
    storage_guard(path, allowance=len(encoded.encode('utf-8')) + 1024 * 1024)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(encoded)


def main():
    low_priority()
    output = ROOT / 'audit_repair_validation'
    storage_guard(output, allowance=130_000_000)
    output.mkdir()
    files = list(HERE.glob('*.py')) + list((HERE / 'tests').glob('*.py'))
    source = {str(path): sha256(path) for path in files}
    run = {'source_commit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=HERE, text=True).strip(),
        'source_files': source, 'strength': 'UNPROVEN'}
    write(output / 'RUN.json', run)
    started = time.perf_counter()
    stages = {}
    for stage in ('identity', 'orientation'):
        print('START ' + stage, flush=True)
        before = time.perf_counter()
        audit(stage, output)
        stages[stage] = {'receipt': str(output / (stage + '_receipt.json')),
                         'sha256': sha256(output / (stage + '_receipt.json')),
                         'seconds': time.perf_counter() - before}
        print('PASS ' + stage, flush=True)
    sample = HERE / 'sample/positions_stm_v1.jsonl'
    expected = 'c7394f11aebf2e76a2e5a1b8e834c8b5b92676180f5896e8ac30062472f7462c'
    if sha256(sample) != expected:
        raise ValueError('selected sample identity changed')
    filters = {}
    for name, options in [('all_off', {}), ('recipe_a', {'drop_in_check': True,
                            'drop_mate_scores': True}), ('recipe_b', {
                            'drop_in_check': True, 'drop_mate_scores': True})]:
        report = run_filter(sample, output / name, workers=2, **options)
        if report['input'] != 10000 or report['kept'] != 10000:
            raise ValueError('selected quiet sample count changed')
        if report['hashes']['records.jsonl'] != expected:
            raise ValueError('filter output identity changed')
        filters[name] = report
    if filters['recipe_a']['hashes'] != filters['recipe_b']['hashes']:
        raise ValueError('repeated selection is not deterministic')
    write(output / 'bounded_filter.json', filters)
    print('PASS bounded filters', flush=True)
    destination = ROOT / 'handoff_v7'
    refresh(destination)
    checked = verify(destination / 'manifest.json')
    write(output / 'published_verify.json', checked)
    if source != {str(path): sha256(path) for path in files}:
        raise ValueError('candidate changed during verification')
    write(output / 'COMPLETE.json', {
        **run, 'status': 'PASS', 'seconds': time.perf_counter() - started,
        'stages': stages, 'manifest': str(destination / 'manifest.json'),
        'manifest_sha256': sha256(destination / 'manifest.json'),
        'resource': storage_guard(output),
        'limitations': 'Bounded sample filter rerun is not a new million-row timing; '
                        'original native/data runtime unchanged; no training or strength claim.'})
    print('PASS fresh audit repair verification', flush=True)


if __name__ == '__main__':
    main()
