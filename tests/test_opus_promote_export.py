"""Refusal rules of tools/opus_promote_export.py on fixtures (owner's fix list item 7, review finding F-014).
The promotion command itself is never run here: the rules live in check_proof(), which is called directly on
fixture dicts; the only subprocess run is the flag-less invocation, which must refuse before reading any file."""
import importlib.util
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / 'tools' / 'opus_promote_export.py'
SPLIT_MD5 = 'f2304604a07ceab3d8baca0da3661a26'


def load():
    spec = importlib.util.spec_from_file_location('opus_promote_export', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def good_proof():
    return dict(scoped_checks='PASS', problems=[], audit_failure_counters_zero=True, split=dict(md5=SPLIT_MD5))


def test_bad_audit_counters_are_refused():
    tool = load()
    proof = good_proof()
    proof['audit_failure_counters_zero'] = False
    text = tool.check_proof(proof, SPLIT_MD5)
    assert text and 'audit reported position / game / state failures' in text


def test_missing_audit_counter_field_is_refused():
    tool = load()
    proof = good_proof()
    del proof['audit_failure_counters_zero']
    assert 'audit reported' in tool.check_proof(proof, SPLIT_MD5)


def test_non_pass_scoped_checks_or_problems_are_refused():
    tool = load()
    proof = good_proof()
    proof['scoped_checks'] = 'UNVERIFIED'
    assert 'scoped checks are not PASS' in tool.check_proof(proof, SPLIT_MD5)
    proof = good_proof()
    proof['problems'] = ['a problem']
    assert 'scoped checks are not PASS' in tool.check_proof(proof, SPLIT_MD5)


def test_changed_split_is_refused_and_good_fixture_passes_the_rules():
    tool = load()
    assert 'SPLIT.json changed' in tool.check_proof(good_proof(), '0' * 32)
    assert tool.check_proof(good_proof(), SPLIT_MD5) is None


def test_command_without_the_owner_flag_refuses_before_reading_anything(tmp_path):
    proc = subprocess.run([sys.executable, '-I', '-B', str(TOOL), '--split', str(tmp_path / 'absent_SPLIT.json'),
                           '--proof', str(tmp_path / 'absent_PROOF.json'), '--out', str(tmp_path / 'export')],
                          capture_output=True, text=True)
    assert proc.returncode != 0
    assert 'needs the owner' in proc.stderr
    assert not (tmp_path / 'export').exists()
