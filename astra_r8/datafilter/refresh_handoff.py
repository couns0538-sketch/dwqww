"""Refresh the approved, unchanged cohort handoff; CPU checks only. UNPROVEN.

An unpublished .partial manifest temporarily has training_ready=true because the
unchanged trainer's --check requires it. Only the final directory is a handoff.
Failures retain the .partial evidence and never publish that final directory.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

# Standalone CLI safety: the environment setting alone affects only child Python.
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import chess

from filter_positions import low_priority, sha256
from records import record
from resource_policy import ARTIFACT_ROOT, storage_guard
from verify_handoff import verify

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE/'evidence/handoff_manifest.json'
APPROVED_PREVIOUS_SHA256 = '0b75136d5d3ead9881b8dc78f0b46ee55d918de499884272c790356f8001d4bb'
RECIPES = ('filtered_eval_v1', 'filtered_wdl_v1')
TRAINING_NAMES = ('filtered_eval_stm_v1', 'filtered_wdl_stm_v1')
MIN_MIRRORS = 1000
TOOLING = ('convert_forge.py', 'result_codec.py', 'filter_positions.py',
           'resource_policy.py', 'filter_lichess_rec.py', 'signcheck.py',
           'audit.py', 'audit_followup.py', 'audit_stm_roundtrip.py', 'audit_capture_cohort.py',
           'audit_raw_labels.py', 'independent_audit.py', 'clear_holdouts.py',
           'verify_handoff.py', 'refresh_handoff.py')


def write_json(path, value):
    text = json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n'
    storage_guard(path, allowance=len(text.encode('utf-8'))+1024*1024)
    with Path(path).open('x', encoding='utf-8', newline='\n') as out:
        out.write(text)


def current_runtime():
    from npt_adapter import runtime_identity, torch
    import train  # Match modules imported by the unchanged crew entry point.
    torch.set_num_threads(1)
    return runtime_identity()


def tooling_identity():
    return {str((HERE/name).resolve()): sha256(HERE/name) for name in TOOLING}


def configure_cpu_runtime(output_dir):
    """Configure this interpreter before its first native npt import."""
    temp = Path(output_dir)/'runtime_tmp'
    storage_guard(temp)
    temp.mkdir()  # A preexisting caller temporary directory is never reused.
    sys.dont_write_bytecode = True
    os.environ.update(PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='',
                      HIP_VISIBLE_DEVICES='', ROCR_VISIBLE_DEVICES='',
                      OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                      TEMP=str(temp), TMP=str(temp),
                      TORCHINDUCTOR_CACHE_DIR=str(temp/'inductor'),
                      TRITON_CACHE_DIR=str(temp/'triton'))
    return temp


def validate_previous(path):
    if sha256(path) != APPROVED_PREVIOUS_SHA256:
        raise ValueError('previous manifest differs from approved handoff')
    manifest = json.loads(Path(path).read_text(encoding='utf-8'))
    verify(path)  # Rehash payloads, original sources, complete holdouts and receipt.
    if current_runtime() != manifest['runtime']:
        raise ValueError('runtime differs from the approved handoff')
    wrapper = manifest['baseline_wrapper']
    if sha256(wrapper['path']) != wrapper['sha256']:
        raise ValueError('baseline training recipe changed')
    holdouts = manifest['holdouts']
    if any(h.get('complete_scan') is not True for h in holdouts):
        raise ValueError('complete holdout scan evidence required')
    receipt = json.loads(Path(manifest['clearance']['path']).read_text())
    expected = {(str(Path(h['path']).resolve()), h['rows'], h['sha256']) for h in holdouts}
    observed = {(str(Path(h['path']).resolve()), h['rows'], h['sha256'])
                for h in receipt['complete_holdouts']}
    if len(receipt['complete_holdouts']) != 2 or observed != expected:
        raise ValueError('clearance does not bind both complete holdouts')
    return manifest


def audit_selection(selection, sample_path):
    """Independent signed correlation and color-swap check on the pinned rows."""
    source = Path(selection['path'])
    before = source.stat()
    storage_guard(sample_path, allowance=20*10**6+1024*1024)
    rows = known = unknown = sx = sy = sxx = syy = sxy = mirrors = sample_rows = sample_bytes = 0
    digest = hashlib.sha256()
    with source.open('rb') as inp, Path(sample_path).open('xb') as sample:
        for raw in inp:
            digest.update(raw)
            r = json.loads(raw)
            rows += 1
            turn = r['fen'].split()[1]
            if turn not in ('w', 'b') or type(r['has_result']) is not bool or type(r['score_stm']) is not int:
                raise ValueError('invalid sign-audit fields')
            if r['has_result']:
                white, y = r['result_white'], r['result_stm']
                if type(white) is not int or white not in (-1, 0, 1) or type(y) is not int:
                    raise ValueError('invalid known outcome')
                if y != (white if turn == 'w' else -white):
                    raise ValueError('STM result orientation mismatch')
                x = r['score_stm']
                known += 1; sx += x; sy += y; sxx += x*x; syy += y*y; sxy += x*y
            else:
                if r['result_stm'] is not None or r['result_white'] is not None:
                    raise ValueError('unknown outcome must remain null')
                unknown += 1
            if mirrors < MIN_MIRRORS:
                mirrored = record(chess.Board(r['fen']).mirror().fen(en_passant='fen'),
                                  r['score_stm'], r['score_type'],
                                  -r['result_white'] if r['has_result'] else None,
                                  'fresh-color-mirror', rows, r['source_kind'])
                if (mirrored['score_stm'], mirrored['result_stm'], mirrored['has_result']) != (
                        r['score_stm'], r['result_stm'], r['has_result']):
                    raise ValueError('color-swap mirror mismatch')
                mirrors += 1
            if sample_rows < 10000:
                if sample_bytes+len(raw) > 20*10**6:
                    raise ValueError('sample exceeds 20 MB')
                sample.write(raw); sample_bytes += len(raw); sample_rows += 1
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('selection changed during sign audit')
    if digest.hexdigest() != selection['sha256'] or rows != selection['rows']:
        raise ValueError('selection hash/count changed')
    denominator = (known*sxx-sx*sx)*(known*syy-sy*sy)
    if known < 2 or denominator <= 0:
        raise ValueError('insufficient score/result variance')
    correlation = (known*sxy-sx*sy)/math.sqrt(denominator)
    if not math.isfinite(correlation) or correlation <= 0.1:
        raise ValueError('score/result correlation must exceed 0.1')
    sample = {'path': str(Path(sample_path).resolve()), 'sha256': sha256(sample_path), 'rows': sample_rows}
    audit = {'rows': rows, 'known_result_count': known, 'unknown_result_count': unknown,
             'pearson_stm_score_result': correlation, 'mirror_checked': mirrors, 'mirror_status': 'PASS',
             'selection_sha256': digest.hexdigest(), 'sample_bytes': sample_bytes}
    return sample, audit


def run_cpu_checks(manifest_path, output_dir):
    result = {}
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', HIP_VISIBLE_DEVICES='',
               ROCR_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    temp = output_dir/'tmp'
    storage_guard(temp); temp.mkdir()
    env.update(TEMP=str(temp), TMP=str(temp), TORCHINDUCTOR_CACHE_DIR=str(temp/'inductor'),
               TRITON_CACHE_DIR=str(temp/'triton'))
    for recipe, name in zip(RECIPES, TRAINING_NAMES):
        destination = ARTIFACT_ROOT/'training'/name
        storage_guard(destination)
        if os.path.lexists(destination):
            raise FileExistsError('crew training destination already exists: '+str(destination))
        command = [sys.executable, str(HERE/'train_adapter.py'), '--manifest', str(manifest_path),
                   '--recipe', recipe, '--output', str(destination), '--device', 'cpu', '--check']
        write_json(output_dir/(recipe+'.command.json'), command)
        stdout, stderr = output_dir/(recipe+'.stdout.json'), output_dir/(recipe+'.stderr.log')
        storage_guard(stdout, allowance=10*10**6)
        with stdout.open('xb') as out, stderr.open('xb') as err:
            process = subprocess.run(command, stdout=out, stderr=err, env=env, timeout=120,
                                     creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == 'nt' else 0)
        receipt = {'exit_code': process.returncode, 'status': 'FAIL',
                   'stdout_sha256': sha256(stdout), 'stderr_sha256': sha256(stderr)}
        if process.returncode == 0:
            response = json.loads(stdout.read_text(encoding='utf-8'))
            if response.get('status') == 'PASS':
                receipt['status'] = 'PASS'
        write_json(output_dir/(recipe+'.receipt.json'), receipt)
        if receipt['status'] != 'PASS':
            raise RuntimeError(recipe+' CPU preflight failed')
        result[recipe] = receipt
    return result


def refresh(output, previous_manifest=PREVIOUS):
    output = Path(output).resolve()
    partial = output.with_name(output.name+'.partial')
    sample_path = output.with_name(output.name+'_sample_stm_v1.jsonl')
    for path in (output, partial, sample_path):
        storage_guard(path, allowance=25*10**6)
        if os.path.lexists(path):
            raise FileExistsError('refusing existing refresh destination: '+str(path))
    previous_digest = sha256(previous_manifest)
    partial.mkdir(parents=True)
    configure_cpu_runtime(partial)
    previous = validate_previous(previous_manifest)
    runtime = current_runtime()
    if runtime != previous['runtime']:
        raise ValueError('runtime changed after previous handoff validation')
    tools = tooling_identity()
    sample, sign = audit_selection(previous['train'], sample_path)
    if sign['mirror_checked'] < MIN_MIRRORS:
        raise ValueError('insufficient rows for 1000 mirror checks')
    manifest = copy.deepcopy(previous)
    manifest.update(sample=sample, runtime=runtime, tooling=tools, training_ready=True,
                    pearson_stm_score_result=sign['pearson_stm_score_result'],
                    known_result_count=sign['known_result_count'], sign_audit=sign,
                    previous_manifest={'path': str(Path(previous_manifest).resolve()), 'sha256': previous_digest},
                    handoff_note='Only the published handoff directory is cleared; .partial is unpublished evidence.')
    candidate = partial/'manifest.json'
    write_json(partial/'sign_audit.json', sign)
    write_json(candidate, manifest)
    checked = verify(candidate)
    preflights = run_cpu_checks(candidate, partial)
    if set(preflights) != set(RECIPES) or any(
            p.get('status') != 'PASS' or p.get('exit_code') != 0 for p in preflights.values()):
        raise ValueError('both recipe preflights must pass')
    if current_runtime() != runtime or tooling_identity() != tools:
        raise ValueError('runtime or tooling changed before publication')
    if sha256(previous_manifest) != previous_digest:
        raise ValueError('previous manifest changed before publication')
    # Reverify immutable data after preflights, including complete holdout hashes.
    checked = verify(candidate)
    report = {'status': 'PASS', 'verification': checked, 'preflights': preflights,
              'manifest_sha256': sha256(candidate), 'published_manifest': str(output/'manifest.json'),
              'strength': 'UNPROVEN'}
    write_json(partial/'verification.json', report)
    storage_guard(output, allowance=0)
    partial.rename(output)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='new handoff directory beneath C:/astra8_data')
    args = parser.parse_args()
    low_priority()
    print(json.dumps(refresh(args.output), indent=2))
