"""Offline-only final preparation checks; imports no process entrypoint."""
import ast
import copy
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PACKAGE = REPO / '.github/hosted-nearest-pawn-performance'
PARENT = REPO / '.github/hosted-pawn-span-performance'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name):
    spec = importlib.util.spec_from_file_location('nearest_static_' + name, PACKAGE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

common, evidence = load('common'), load('build_evidence')
cfg = json.loads((PACKAGE / 'protocol.json').read_text())
paths = common.inventory(REPO, PACKAGE)
assert len(paths) == 22
assert cfg['baseline_sha'] == common.BASELINE == 'fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'
assert cfg['candidate_sha'] == common.CANDIDATE == '2e151d019bc58dff2ab4e76e99ef99516af8d222'
assert cfg['correctness_evidence_sha256'] == cfg['transport_captures'] == {}
assert cfg['source_file_counts'] == evidence.SOURCE_FILE_COUNTS == {'baseline': 75, 'candidate': 76}
assert cfg['mandatory_finite_proof_paths'] == list(common.REQUIRED_PROOFS)
assert len(common.REQUIRED_PROOFS) == 13
assert len(evidence.BASELINE_TESTS) == 12 and len(evidence.CANDIDATE_TESTS) == 13
assert evidence.CANDIDATE_TESTS == evidence.BASELINE_TESTS[:4] + ('forge_nearest_pawn_tests',) + evidence.BASELINE_TESTS[4:]
workflow = REPO / common.WORKFLOW
parsed = yaml.load(workflow.read_text(), Loader=yaml.BaseLoader)
assert parsed['on'] == [] and parsed['jobs']['performance']['if'] == 'false'
assert parsed['jobs']['performance']['env']['BASELINE_SHA'] == cfg['baseline_sha']
assert parsed['jobs']['performance']['env']['CANDIDATE_SHA'] == cfg['candidate_sha']
assert sha(workflow) == cfg['workflow_sha256']
for name in ['owned_process.py', 'run_hosted.py', 'archive_results.py']:
    assert (PACKAGE / name).read_bytes() == (PARENT / name).read_bytes()
assert sha(PACKAGE / 'owned_process.py') == '461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
assert (PACKAGE / 'analysis.py').read_text() == (PARENT / 'analysis.py').read_text().replace('20261028', '20261029')
for path, expected in json.loads((HERE / 'IMMUTABLE20-BEFORE.json').read_text()).items():
    assert sha(REPO / path) == expected
for path in (PACKAGE / 'fixtures/historical-18-19').iterdir():
    assert path.read_bytes() == (PARENT / 'fixtures/historical-18-19' / path.name).read_bytes()
# Recheck execution files against the exact inventory from the completed suite.
for line in (HERE / 'PACKAGE-SHA256SUMS.offline-attempt1').read_text().splitlines():
    digest, name = line.split('  ', 1)
    if not name.endswith('/README.md'):
        assert sha(REPO / name) == digest
refusals = {}
def reject(name, metadata):
    try:
        common.require_ready(metadata)
    except ValueError as error:
        refusals[name] = str(error)
    else:
        raise AssertionError('Unexpectedly accepted ' + name)

reject('actual_DRAFT', cfg)
synthetic = copy.deepcopy(cfg)
synthetic.update(status=common.READY, source_gates_status='PASSED', parity_review_status='PASSED', capture_review_status='PASSED', root_review_status='PASSED', independent_review_status='PASSED', workflow_status='FROZEN', operational_qualification_status='authorized_for_one_fresh_host_calibration_attempt_with_prior_anomalies_unresolved')
reject('forged_READY_with_actual_empty_proofs', synthetic)
synthetic['correctness_evidence_sha256'] = {name: '1' * 64 for name in common.REQUIRED_PROOFS}
reject('synthetic_proof_names_without_actual_captures', synthetic)
synthetic['transport_captures'] = {'baseline': {}, 'candidate': {}}
for name in common.REQUIRED_PROOFS:
    missing = copy.deepcopy(synthetic)
    del missing['correctness_evidence_sha256'][name]
    reject('missing:' + name, missing)
for counts in [None, {'baseline': 74, 'candidate': 75}, {'baseline': 75}, {'baseline': 75, 'candidate': 77}]:
    wrong = copy.deepcopy(synthetic); wrong['source_file_counts'] = counts
    reject('wrong_source_counts:' + str(counts), wrong)
frozen = common.snapshot(paths)
assert common.rehash(frozen)['status'] == 'passed'
changes = []
for name in ['analysis.py', 'build_evidence.py', 'common.py', 'prepare_hosted.py', 'protocol.json', 'README.md']:
    changes.append(''.join(difflib.unified_diff((PARENT / name).read_text().splitlines(True), (PACKAGE / name).read_text().splitlines(True), fromfile='verified20/' + name, tofile='disabled21/' + name)))
(HERE / 'PACKAGE-ADAPTATION.diff').write_text(''.join(changes))
result = {'status': 'PASS_DISABLED_PREPARATION_ONLY_NOT_INDEPENDENT_REVIEW_OR_LAUNCH_AUTHORIZATION',
          'package_entries': 21, 'baseline': common.BASELINE, 'candidate': common.CANDIDATE,
          'workflow_disabled': True, 'actual_proofs': 0, 'actual_capture_entries': 0,
          'named_ctests': {'baseline': evidence.BASELINE_TESTS, 'candidate': evidence.CANDIDATE_TESTS},
          'source_file_counts': evidence.SOURCE_FILE_COUNTS, 'refusals': refusals,
          'package_snapshot': frozen, 'immutable20_package_and_workflow_unchanged': True,
          'execution_inputs_match_completed43_check_inventory': True,
          'historical18_19_fixture_bytes_preserved': True,
          'independent_review_child': 'Agent thread limit reached; no independent review claimed.',
          'engines_compilers_benchmarks_hosted_git_actions': 0,
          'script_sha256': sha(Path(__file__))}
(HERE / 'PREPARER-STATIC-CHECKS.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ['package_snapshot', 'refusals']}, indent=2))
