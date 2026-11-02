"""Refresh must never publish readiness after a failed audit or preflight."""
import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def small_selection(tmp_path):
    from records import record, dumps
    from filter_positions import sha256
    rows = []
    for turn, score, white in [('w', 100, 1), ('b', -100, 1),
                               ('w', -100, -1), ('b', 100, -1),
                               ('w', 30000, None)]:
        rows.append(record(f'7k/8/8/8/4Q3/8/8/K7 {turn} - - 0 1', score,
                           'cp', white, 'fixture', len(rows)+1, 'selfplay'))
    source = tmp_path/'input.jsonl'
    source.write_text('\n'.join(map(dumps, rows))+'\n', encoding='utf-8')
    return {'path': str(source), 'rows': len(rows), 'sha256': sha256(source)}


def test_sign_sample_excludes_unknown_and_checks_mirrors(tmp_path):
    import refresh_handoff as h
    data = small_selection(tmp_path)
    sample, audit = h.audit_selection(data, tmp_path/'sample.jsonl')
    assert sample['rows'] == 5
    assert audit['known_result_count'] == 4
    assert audit['unknown_result_count'] == 1
    assert audit['pearson_stm_score_result'] == 1.0
    assert audit['mirror_checked'] == 5
    assert audit['mirror_status'] == 'PASS'


def prepare(tmp_path, monkeypatch):
    import refresh_handoff as h
    selection = small_selection(tmp_path)
    previous = tmp_path/'previous.json'
    previous.write_text('{}', encoding='utf-8')
    manifest = dict(schema=1, strength='UNPROVEN', training_ready=True,
                    train=selection, metadata=selection, validation=selection,
                    runtime={'files': {}}, source_proportions={'selfplay': 1.0})
    monkeypatch.setattr(h, 'validate_previous', lambda path: manifest)
    monkeypatch.setattr(h, 'current_runtime', lambda: {'files': {}})
    monkeypatch.setattr(h, 'verify', lambda path: {'status': 'PASS'})
    monkeypatch.setattr(h, 'MIN_MIRRORS', 5)
    return h, previous, tmp_path/'handoff'


def test_failed_preflight_never_publishes_readiness(tmp_path, monkeypatch):
    h, previous, output = prepare(tmp_path, monkeypatch)
    def fail(*args, **kwargs):
        raise RuntimeError('fixture second preflight failed')
    monkeypatch.setattr(h, 'run_cpu_checks', fail)
    with pytest.raises(RuntimeError, match='preflight failed'):
        h.refresh(output, previous)
    assert not output.exists()
    assert (tmp_path/'handoff.partial/manifest.json').exists()
    assert (tmp_path/'handoff_sample_stm_v1.jsonl').exists()


def test_refresh_requires_both_preflights_before_publication(tmp_path, monkeypatch):
    h, previous, output = prepare(tmp_path, monkeypatch)
    observed = []
    def checks(manifest_path, output_dir):
        assert not output.exists()
        assert manifest_path.parent.name == 'handoff.partial'
        observed.append(manifest_path)
        return {name: {'status': 'PASS', 'exit_code': 0} for name in h.RECIPES}
    monkeypatch.setattr(h, 'run_cpu_checks', checks)
    result = h.refresh(output, previous)
    assert len(observed) == 1 and result['status'] == 'PASS'
    manifest = json.loads((output/'manifest.json').read_text())
    assert manifest['training_ready'] is True
    assert Path(manifest['sample']['path']).is_file()
    assert not (tmp_path/'handoff.partial').exists()
    with pytest.raises(FileExistsError):
        h.refresh(output, previous)


def test_missing_preflight_never_publishes(tmp_path, monkeypatch):
    h, previous, output = prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(h, 'run_cpu_checks', lambda *a: {
        'filtered_eval_v1': {'status': 'PASS', 'exit_code': 0}})
    with pytest.raises(ValueError, match='both recipe'):
        h.refresh(output, previous)
    assert not output.exists()


def test_runtime_drift_never_publishes(tmp_path, monkeypatch):
    h, previous, output = prepare(tmp_path, monkeypatch)
    calls = iter(({'files': {}}, {'files': {'drift': 'changed'}}))
    monkeypatch.setattr(h, 'current_runtime', lambda: next(calls))
    monkeypatch.setattr(h, 'run_cpu_checks', lambda *a: {
        name: {'status': 'PASS', 'exit_code': 0} for name in h.RECIPES})
    with pytest.raises(ValueError, match='runtime or tooling changed'):
        h.refresh(output, previous)
    assert not output.exists()


def test_previous_manifest_drift_never_publishes(tmp_path, monkeypatch):
    h, previous, output = prepare(tmp_path, monkeypatch)
    def checks(*args):
        previous.write_text('{"changed":true}', encoding='utf-8')
        return {name: {'status': 'PASS', 'exit_code': 0} for name in h.RECIPES}
    monkeypatch.setattr(h, 'run_cpu_checks', checks)
    with pytest.raises(ValueError, match='previous manifest changed'):
        h.refresh(output, previous)
    assert not output.exists()


def test_cpu_environment_precedes_native_imports_and_uses_new_temp(tmp_path, monkeypatch):
    import refresh_handoff as h
    for key in ('CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES', 'ROCR_VISIBLE_DEVICES',
                'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                'TEMP', 'TMP', 'TORCHINDUCTOR_CACHE_DIR', 'TRITON_CACHE_DIR',
                'PYTHONDONTWRITEBYTECODE'):
        monkeypatch.setenv(key, 'unsafe-caller-value')
    monkeypatch.setattr(sys, 'dont_write_bytecode', False)
    temp = h.configure_cpu_runtime(tmp_path)
    assert temp == tmp_path/'runtime_tmp' and temp.is_dir()
    assert sys.dont_write_bytecode is True
    for key in ('CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES', 'ROCR_VISIBLE_DEVICES'):
        assert os.environ[key] == ''
    for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'PYTHONDONTWRITEBYTECODE'):
        assert os.environ[key] == '1'
    for key in ('TEMP', 'TMP', 'TORCHINDUCTOR_CACHE_DIR', 'TRITON_CACHE_DIR'):
        assert Path(os.environ[key]).is_relative_to(tmp_path)
    with pytest.raises(FileExistsError):
        h.configure_cpu_runtime(tmp_path)
