"""A published proof must not pass by omitting the evidence to check."""
import json
from pathlib import Path

import pytest

import verify_handoff as v
from test_handoff_adversarial import fixture


@pytest.mark.parametrize('damage', [
    'missing_tooling', 'empty_tooling', 'missing_one_tool', 'missing_sources',
    'source_count', 'source_order', 'source_boundary', 'source_bytes',
    'missing_sign', 'sign_payload', 'sign_known', 'sign_correlation',
    'mirror_failed', 'mirror_short', 'schema_bool', 'payload_float_count',
    'clearance_input', 'clearance_accounting', 'clearance_original',
])
def test_incomplete_or_inconsistent_proof_is_rejected(tmp_path, monkeypatch, damage):
    path, m, receipt = fixture(tmp_path, monkeypatch)
    if damage == 'missing_tooling': m.pop('tooling')
    elif damage == 'empty_tooling': m['tooling'] = {}
    elif damage == 'missing_one_tool': m['tooling'].pop(next(iter(m['tooling'])))
    elif damage == 'missing_sources': m['cohort']['sources'] = []
    elif damage == 'source_count': m['cohort']['count'] += 1
    elif damage == 'source_order': m['cohort']['source_order'] = []
    elif damage == 'source_boundary': m['cohort']['sources'][0]['last_source_row'] = 1
    elif damage == 'source_bytes': m['cohort']['sources'][0]['bytes'] += 1
    elif damage == 'missing_sign': m.pop('sign_audit')
    elif damage == 'sign_payload': m['sign_audit']['selection_sha256'] = '0'*64
    elif damage == 'sign_known': m['sign_audit']['known_result_count'] = 1
    elif damage == 'sign_correlation': m['sign_audit']['pearson_stm_score_result'] = 0.9
    elif damage == 'mirror_failed': m['sign_audit']['mirror_status'] = 'FAIL'
    elif damage == 'mirror_short': m['sign_audit']['mirror_checked'] = 1
    elif damage == 'schema_bool': m['schema'] = True
    elif damage == 'payload_float_count': m['sample']['rows'] = 2.0
    elif damage == 'clearance_input': receipt['selection']['input'] += 1
    elif damage == 'clearance_accounting': receipt['selection']['holdout_excluded'] = 1
    elif damage == 'clearance_original': receipt['original_selection_sha256'] = '0'*64
    if damage.startswith('clearance_'):
        cp = Path(m['clearance']['path'])
        cp.write_text(json.dumps(receipt))
        m['clearance']['sha256'] = v.sha256(cp)
    path.write_text(json.dumps(m))
    with pytest.raises(ValueError):
        v.verify(path)


def test_runtime_exception_requires_the_approved_historical_manifest(tmp_path, monkeypatch):
    path, m, _ = fixture(tmp_path, monkeypatch)
    path.write_text(json.dumps(m))
    with pytest.raises(ValueError, match='historical'):
        v.verify(path, allow_runtime_changes=v.REVIEWABLE_RUNTIME)


def test_only_pinned_historical_input_can_omit_new_proofs(tmp_path, monkeypatch):
    path, m, _ = fixture(tmp_path, monkeypatch)
    m.pop('tooling')
    m.pop('sign_audit')
    path.write_text(json.dumps(m))
    monkeypatch.setattr(v, 'APPROVED_PREVIOUS_SHA256', v.sha256(path))
    assert v.verify(path, allow_runtime_changes=v.REVIEWABLE_RUNTIME)['status'] == 'PASS'
    with pytest.raises(ValueError, match='tooling'):
        v.verify(path)
    m['note'] = 'changed after approval'
    path.write_text(json.dumps(m))
    with pytest.raises(ValueError, match='historical'):
        v.verify(path, allow_runtime_changes=v.REVIEWABLE_RUNTIME)


def test_manifest_mutation_during_verification_rejected(tmp_path, monkeypatch):
    path, m, _ = fixture(tmp_path, monkeypatch)
    path.write_text(json.dumps(m))
    original = v.verify_payload
    def mutate(item):
        result = original(item)
        m['unexpected_change'] = True
        path.write_text(json.dumps(m))
        return result
    monkeypatch.setattr(v, 'verify_payload', mutate)
    with pytest.raises(ValueError, match='manifest changed'):
        v.verify(path)
