#!/usr/bin/env python3
"""Read-only static validation; no engine, build or Git invocation."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PACKAGE = REPO / '.github/hosted-tt-refresh-strength'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cfg = json.loads((PACKAGE / 'protocol.json').read_text())
    spec = importlib.util.spec_from_file_location('static_tt_refresh_runner', PACKAGE / 'run_hosted.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    inventory = runner.verify_package_inventory(REPO, PACKAGE)
    assert len(inventory) == 24
    assert cfg['candidate_sha'] == runner.CANDIDATE_SHA == '1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
    assert cfg['baseline_sha'] == 'ff2e269c6058be84456e3b98344826d17b0056eb'
    assert cfg['candidate_benchmark_nodes'] is runner.CANDIDATE_BENCHMARK_NODES is None
    assert cfg['status'] == 'DRAFT_BLOCKED_PREPARATION_ONLY'
    assert cfg['correctness_evidence_sha256'] == {}
    assert cfg['seed'] == 20261101
    assert cfg['source_file_counts'] == {'baseline':77, 'candidate':77}
    assert cfg['sprt_settings'] == dict(elo0=0,elo1=10,alpha=.05,beta=.05,pair_cap=512,game_cap=1024,tc='1+0.01',concurrency=1,emergency_seconds=18000)
    assert cfg['aa_settings'] == dict(pairs=4,tc='1+0.01',nodes=0,identical_moves_required=False,binary='baseline')
    rejected = []
    for name, modified in [('draft', cfg), ('forced_ready_missing_actual_signature',dict(cfg,status='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH'))]:
        try:
            runner.require_launch_protocol(modified)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError(name)
    workflow = REPO / '.github/workflows/forge-hosted-tt-refresh-strength.yml'
    text = workflow.read_text()
    assert 'on: []' in text and 'if: ${{ false }}' in text and 'workflow_dispatch:' not in text
    for bound in (360,8,310):
        assert f'timeout-minutes: {bound}' in text
    assert cfg['candidate_sha'] in text and cfg['baseline_sha'] in text
    tree = ast.parse((PACKAGE/'build_evidence.py').read_text())
    values = {n.targets[0].id:n.value for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
    names = ast.literal_eval(values['BASELINE_TESTS'])
    assert len(names)==14 and names[5]=='forge_pv_metadata_tests'
    assert isinstance(values['CANDIDATE_TESTS'],ast.Name) and values['CANDIDATE_TESTS'].id=='BASELINE_TESTS'
    assert ast.literal_eval(values['SOURCE_COUNTS'])=={'baseline':77,'candidate':77}
    references = {}
    for source in ('IMMUTABLE22-REFERENCES.json','CONSUMED-HISTORICAL-REFERENCES.json'):
        mapping = json.loads((ROOT/source).read_text())
        for relative, record in mapping.items():
            path=REPO/relative
            assert sha(path)==record['sha256'] and path.stat().st_size==record['bytes'], relative
        references[source]=len(mapping)
    gate = REPO/cfg['candidate_source_manifest_path']
    assert sha(gate)==cfg['candidate_source_manifest_sha256']
    g=json.loads(gate.read_text())
    assert g['source_commit']==cfg['candidate_sha'] and g['source_files']==77 and len(g['inputs'])==77
    opening=json.loads((ROOT/'opening-check.json').read_text())
    assert opening['status']=='passed' and opening['fresh_unique_positions']==516
    assert opening['full_reserved_cohorts_excluded']['hosted-pv-metadata-strength']==516
    assert opening['full_reserved_cohorts_excluded']['hosted-correction-history-strength']==260
    assert opening['independent_selected_source_games_legally_replayed']==516
    assert opening['runtime_seed']==20261101
    return dict(status='PASS_DISABLED_PREPARATION_NOT_LAUNCH_READY',package_files=24,
                baseline_named_tests=list(names),candidate_named_tests=list(names),
                references_rehashed=references,negative_controls=rejected,
                pending=['actual23 native/root proofs','actual23 canonical signature and22/23 captures','complete proof bindings/reviews/one-attempt authorization'],
                windows23_required=False,engine_build_match_executions=0,
                protocol_sha256=sha(PACKAGE/'protocol.json'),workflow_sha256=sha(workflow),
                inventory_sha256=sha(PACKAGE/'PACKAGE-SHA256SUMS'),
                execution_python_sha256={str(p.relative_to(REPO)):sha(p) for p in sorted(PACKAGE.rglob('*.py'))})


if __name__ == '__main__':
    print(json.dumps(main(),indent=2))
