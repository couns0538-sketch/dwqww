"""Static preparation check only. Never executes an engine, compiler or workflow."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
PACKAGE=REPO/'.github/hosted-correction-history-strength'

def main():
    spec=importlib.util.spec_from_file_location('correction_preparation',PACKAGE/'run_hosted.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    cfg=json.loads((PACKAGE/'protocol.json').read_text())
    assert cfg['status']=='DRAFT_BLOCKED_CANDIDATE18_GATES_PENDING'
    assert cfg['baseline_sha']=='b5908f0fe9db227158d39e156652f2467252e68a'
    assert cfg['candidate_sha']=='fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b'
    assert runner.CANDIDATE_SHA==cfg['candidate_sha']
    assert cfg['candidate_benchmark_nodes']==runner.CANDIDATE_BENCHMARK_NODES==321912
    assert cfg['source_gates_status']=='PENDING' and cfg['correctness_evidence_sha256']=={}
    assert cfg['root_review_status']==cfg['astra_review_status']=='PENDING'
    assert not (REPO/'.github/workflows/forge-hosted-correction-history-strength.yml').exists()
    try:runner.require_launch_protocol(cfg)
    except ValueError:pass
    else:raise AssertionError('Blocked preparation admitted launch')
    inventory=runner.verify_package_inventory(REPO,PACKAGE)
    opening=json.loads((ROOT/'opening-check.json').read_text())
    assert opening['status']=='passed'
    output={'status':'PREPARED_BLOCKED_NOT_READY','candidate_benchmark_nodes':321912,
        'source_gates':'PENDING','root_review':'PENDING','astra_review':'PENDING','workflow_exists':False,
        'package_files_verified':len(inventory),'opening_check_sha256':hashlib.sha256((ROOT/'opening-check.json').read_bytes()).hexdigest(),
        'engines_tests_compilers_matches_launched_by_this_check':False}
    print(json.dumps(output,indent=2))

if __name__=='__main__':main()
