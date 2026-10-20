"""Actual READY metadata and negative controls; no engine/build/Git execution."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PACKAGE = REPO / '.github/hosted-correction-history-strength'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    spec = importlib.util.spec_from_file_location('ready_runner', PACKAGE / 'run_hosted.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    cfg = json.loads((PACKAGE / 'protocol.json').read_text())
    runner.require_launch_protocol(cfg)
    inventory = runner.verify_package_inventory(REPO, PACKAGE)
    workflow = REPO / '.github/workflows/forge-hosted-correction-history-strength.yml'
    assert sha(workflow) == cfg['workflow_sha256']
    text = workflow.read_text()
    assert "- 'forge/hosted-correction-history-strength-20261020-*'" in text
    assert 'github.run_attempt == 1' in text and 'workflow_dispatch' not in text
    assert 'on: []' not in text and 'if: ${{ false }}' not in text
    assert len(cfg['correctness_evidence_sha256']) == 335
    for relative, digest in cfg['correctness_evidence_sha256'].items():
        path = REPO / relative
        assert path.is_file() and not path.is_symlink() and sha(path) == digest, relative
    negatives = [
        ('status', 'DRAFT_BLOCKED_CANDIDATE18_GATES_PENDING'),
        ('source_gates_status', 'PENDING'), ('source_scope_review_status', 'PENDING'),
        ('root_review_status', 'PENDING'), ('astra_review_status', 'PENDING'),
        ('correctness_evidence_sha256', {}),
        ('operational_qualification_status', 'PENDING_ROOT_ONE_ATTEMPT_AUTHORIZATION'),
        ('workflow_status', 'DRAFT_DISABLED_PENDING_ROOT_ASTRA_REVIEW'),
        ('workflow_sha256', None)]
    for key, value in negatives:
        changed = copy.deepcopy(cfg)
        changed[key] = value
        try:
            runner.require_launch_protocol(changed)
        except ValueError:
            continue
        raise AssertionError('Missing-gate control admitted: ' + key)
    print(json.dumps({'status':'PASS_READY_METADATA_AND_MISSING_GATE_CONTROLS',
        'package_files':len(inventory), 'proofs_verified':335,
        'missing_gate_controls_rejected':len(negatives),
        'workflow_sha256':sha(workflow), 'protocol_sha256':sha(PACKAGE/'protocol.json'),
        'inventory_sha256':sha(PACKAGE/'PACKAGE-SHA256SUMS'),
        'engine_build_match_launches':0}, indent=2))

if __name__ == '__main__':
    main()
