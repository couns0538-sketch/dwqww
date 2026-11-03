"""Bind the completed R8 evidence for the Forge consistency checker."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

WORK = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter')
HERE = WORK / 'astra_r8/datafilter'
EVIDENCE = HERE / 'evidence/quality6h'
OUTPUT = EVIDENCE / 'final_pack'
LOCAL = Path(__file__).parent
sys.path.insert(0, str(HERE))
from filter_positions import low_priority, sha256
from resource_policy import storage_guard


def ref(path):
    path = Path(path)
    return {'path': os.path.relpath(path, OUTPUT).replace('\\', '/'),
            'sha256': sha256(path)}


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def main():
    low_priority()
    storage_guard(LOCAL, allowance=2_000_000)
    receipt = json.loads((OUTPUT / 'COMPLETE.json').read_text())
    assert receipt['status'] == 'PASS'
    sources = []
    for name, expected in receipt['source_files'].items():
        original = Path(name)
        assert sha256(original) == expected, name
        snapshot = original if original.is_relative_to(WORK) else EVIDENCE / 'completion_plan/pack_completion.py'
        assert sha256(snapshot) == expected, str(snapshot)
        sources.append(ref(snapshot))
    sources.append(ref(HERE / 'evidence/conftest.py'))
    sources.append(ref(EVIDENCE / 'completion_plan/complete_corpus_checks.py'))
    baseline_commit = '175e3a1caea7605fda73ebe3d758e69cbfd1af3c'
    baseline = []
    for path in sorted((HERE / 'baseline').glob('*.py')):
        blob = subprocess.check_output(['git', 'show', baseline_commit + ':' + path.relative_to(WORK).as_posix()], cwd=WORK)
        assert hashlib.sha256(blob).hexdigest() == sha256(path), str(path)
        baseline.append(ref(path))
    evidence = {
        '100k legacy binary and stats identity': 'converter_line_validation/identity_receipt.json',
        '1000 actual binary outcomes and 1000 mirrors': 'converter_line_validation/orientation_receipt.json',
        'current converter source unchanged during replay': 'converter_line_validation/RECHECK.json',
        '301 CPU tests and 11 subtests': 'current_full_runtime_green/pytest.log',
        'tested runtime unchanged': 'current_full_runtime_green/runtime.json',
        'archive excluded; all 301 tests collected': 'collection_boundary/green.log',
        'full payload inventory and measured receipt checks': 'final_pack/COMPLETE.json',
        '7001 retained files freshly hashed': 'final_pack/full_output_hashes.json',
        'complete 37-source descriptive profile': 'corpus_report/corpus_report.json',
        '4736 original source-line label checks': 'reservoir_audit/reservoir_receipt.json',
        '9486 native perft2 checks and five lock bench pins': 'native_corpus/report.json',
        'actual native input protocol': 'native_corpus/stdin.txt',
        'actual native perft and bench transcript': 'native_corpus/stdout.log',
        'same cleared cohort and mirror/sign proof': 'handoff_v4/sign_audit.json',
        'recipe A CPU-only preflight': 'handoff_v4/filtered_eval_v1.stdout.json',
        'recipe B CPU-only preflight': 'handoff_v4/filtered_wdl_v1.stdout.json',
        'current strict published handoff verification': 'final_pack/published_verify.json',
        'storage reserves and total retained capacity': 'final_pack/resource_after.json',
    }
    for name in ['all_off', 'check', 'mate', 'ply160', 'recipe_a', 'recipe_b', 'capture']:
        evidence['million-row rule receipt: ' + name] = 'filter_budget_million/' + name + '.report.json'
    record = {
        'schema': 1, 'kind': 'correctness', 'strength': 'UNPROVEN',
        'baseline': {'commit': baseline_commit, 'artifacts': baseline},
        'candidate': {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=WORK, text=True).strip(),
                      'artifacts': sources},
        'checks': [{'name': name, 'status': 'PASS', 'evidence': ref(EVIDENCE / path)} for name, path in evidence.items()],
        'limitations': [
            'This record and the Forge checker bind declared evidence and hashes; the checker does not independently reproduce those experiments.',
            'Final 03:21-03:51 UTC independent review remains pending; no final acceptance is asserted here.',
            'True qsearch filter is BLOCKED: exact FD3A5190 has no static/root-qsearch UCI interface. No surrogate used.',
            'Original self-play has no stored best moves. Capture measurement uses a separate gate-PGN cohort, never training data.',
            'Full 304999573-row profiling is descriptive. Complete holdout clearance applies only to the selected 999953-row cohort; genuine game IDs are unavailable.',
            'Timing belongs to source 88b7c6b1c83eb360d797e33dca601fa7d8a758da. Later admission/verifier fixes are not new throughput measurements.',
            'No training, GPU, net export or strength gate was run. All playing strength is UNPROVEN.',
        ],
    }
    save(OUTPUT / 'correctness_record.json', record)
    save(LOCAL / 'correctness_record.json', record)
    print(json.dumps({'status': 'CREATED', 'candidate_files': len(sources), 'checks': len(evidence),
                      'record_sha256': sha256(OUTPUT / 'correctness_record.json')}))


if __name__ == '__main__':
    main()
