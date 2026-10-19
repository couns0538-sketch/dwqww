from pathlib import Path
import datetime
import hashlib
import importlib.util
import json

ROOT = Path('/workspace/.cloud-setup/windows-validation-bundle with spaces')
EXPECTED_FASTCHESS = '4faf9592df9a7955fa326f3281cd4bdcabe8b651101cd65629b49dd9c7e83729'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(ROOT / 'fastchess/fastchess.exe') == EXPECTED_FASTCHESS
assert sha(ROOT / 'engine/candidate.exe') == '7928cfbf3e5da6e508c4da5b4c6d4c2a6582a3058951ed5d5479c3098909e324'
original = json.loads((ROOT / 'provenance/original-6.4.json').read_text())
candidate = json.loads((ROOT / 'provenance/candidate-6.4.2.json').read_text())
files = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(ROOT.rglob('*'))
         if p.is_file() and p.name != 'manifest.json'}
manifest = {
    'schema_version': 1,
    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'bundle': 'Forge 6.4.2 candidate native Windows validation',
    'provenance': {
        'fastchess_source': '60d7a7a26c6b0582a15c112fb29a1829bef2adb3',
        'fastchess': {'sha256': EXPECTED_FASTCHESS, 'record': 'fastchess/provenance.json'},
        'candidate': {**candidate, 'bundled_source_directory': 'sources/candidate-6.4.2',
                      'record': 'provenance/candidate-6.4.2.json'},
        'original': {**original, 'bundled_source_directory': 'sources/original-6.4.0',
                     'record': 'provenance/original-6.4.json'},
        'python': json.loads((ROOT / 'provenance/python-verified-python.json').read_text()),
        'openings': {'record': 'provenance/openings-selection.json', 'seed': 20261019},
        'comparison_scope': 'Complete Windows releases, including original znver4 versus candidate Zen5 compiler/architecture differences; not causal source-only isolation'},
    'protocol': {'aa_pairs': 4, 'aa_nodes_per_move': 10000, 'aa_concurrency': 2,
                 'pilot_pairs': 8, 'timed_control': '10+0.1', 'sprt_max_pairs': 5000,
                 'sprt': {'elo0': 0, 'elo1': 5, 'alpha': .05, 'beta': .05, 'model': 'logistic'},
                 'timed_concurrency': 1, 'threads': 1, 'hash_mib': 32,
                 'ownbook': False, 'ponder': False, 'move_overhead_ms': 100,
                 'restart_per_game': True, 'strict': True, 'adjudication': None,
                 'native_windows_only_for_strength': True, 'wine_readiness_only': True,
                 'no_accepted_elo_gain_yet': True, 'stockfish_superiority_proven': False,
                 'stopping_rule': 'Exactly one native boundary plus independent paired GLR crossing, otherwise full cap inconclusive; any fault invalidates; no resume/retry/pooling'},
    'files': files}
(ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
spec = importlib.util.spec_from_file_location('frozen_validator', ROOT / 'windows_validate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
loaded, frozen = module.load_bundle(ROOT)
report = {'status': 'frozen_bundle_python_loader_passed', 'bundle': str(ROOT),
          'manifest_sha256': sha(ROOT / 'manifest.json'), 'file_count': len(files),
          'total_file_bytes': sum((ROOT / name).stat().st_size for name in files),
          'fastchess_sha256': EXPECTED_FASTCHESS, 'candidate_sha256': sha(ROOT / 'engine/candidate.exe'),
          'original_sha256': sha(ROOT / 'engine/original-6.4.exe'),
          'runner_sha256': sha(ROOT / 'windows_validate.py')}
report_path=ROOT.parent / 'windows-validation-bundle-freeze.json'
report_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
