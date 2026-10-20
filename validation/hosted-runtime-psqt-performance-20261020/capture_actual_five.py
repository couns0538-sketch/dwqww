"""Actual five-command producer captures only; no comparative speed acceptance."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

REPO=Path('/workspace/dwqww')
HERE=Path(__file__).resolve().parent
HELPER=REPO/'.github/hosted-runtime-psqt-performance/owned_process.py'
EXPECTED_HELPER='de13ad7c32832144a75f9c5080558f3c3e08952390eece6d70bd249058dcebea'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def main():
    assert digest(HELPER)==EXPECTED_HELPER
    spec=importlib.util.spec_from_file_location('native_five_capture_owner',HELPER)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    out=HERE/'actual-five-captures';out.mkdir(exist_ok=False)
    native=REPO/'validation/lazy-runtime-psqt-native-20261020'
    for profile in ('release','asan','tsan'):
        assert json.loads((native/('frozen-'+profile+'-attempt1/summary.json')).read_text())['status']=='PASS'
    active=json.loads((native/'active-uci-wrapper-attempt1/COMMAND.json').read_text())
    assert active['status']=='PASS'
    plans={
        'baseline':{'source_sha':'fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b',
            'source':Path('/workspace/.cloud-setup/correction-history-native-source'),
            'build':Path('/workspace/.cloud-setup/correction-history-native-release'),
            'manifest':REPO/'validation/correction-history-native-20261020/frozen-source-fc51e43-files.json',
            'receipt':REPO/'validation/correction-history-native-20261020/frozen-release-attempt1/summary.json'},
        'candidate':{'source_sha':'61f598056572dfade6994af8ad2e38817cd28aa3',
            'source':Path('/workspace/.cloud-setup/lazy-runtime-psqt-native-source'),
            'build':Path('/workspace/.cloud-setup/lazy-runtime-psqt-native-release'),
            'manifest':native/'ROOT-FROZEN-SOURCE-GATES.json',
            'receipt':native/'frozen-release-attempt1/summary.json'}}
    original_affinity=sorted(os.sched_getaffinity(0));cpu=min(original_affinity)
    stdin=b'bench 11\n'*5+b'quit\n'
    provenance={'status':'CAPTURING_NOT_A_PERFORMANCE_COMPARISON','utc':datetime.now(timezone.utc).isoformat(),
        'helper_sha256':EXPECTED_HELPER,'original_affinity':original_affinity,'capture_cpu':cpu,
        'stdin_sha256':hashlib.sha256(stdin).hexdigest(),'captures':{},
        'scope':'Original producer/transport bytes and process facts only. Existing local-host small-speed calibration failed previously; these times/CPU values are not an A/B speed estimate or Elo result.'}
    save(out/'PROVENANCE.json',provenance)
    for label,plan in plans.items():
        manifest=json.loads(plan['manifest'].read_text())
        expected=manifest['inputs'] if label=='candidate' else manifest
        receipt=json.loads(plan['receipt'].read_text())
        assert receipt['status']=='PASS' and receipt['source_commit']==plan['source_sha']
        source_before={name:digest(plan['source']/name) for name in expected}
        assert source_before==expected
        binary_before={name:digest(plan['build']/name) for name in ('forge','libforge_core.a')}
        assert all(receipt['binary_sha256_after'][name]==value for name,value in binary_before.items())
        row={'source_commit':plan['source_sha'],'source_manifest_sha256':digest(plan['manifest']),
            'build_receipt_sha256':digest(plan['receipt']),'source_sha256_before':source_before,
            'binary_paths':{name:str(plan['build']/name) for name in binary_before},'binary_sha256_before':binary_before}
        provenance['captures'][label]=row;save(out/'PROVENANCE.json',provenance)
        try:
            facts=helper.run_owned([str(plan['build']/'forge')],stdin,out/label,cpu,60)
            row['process_facts']=facts
            save(out/'PROVENANCE.json',provenance)
            assert facts['returncode_before_verdict']==facts['returncode_after_cleanup']==0
            assert facts['owned_group_empty_before_verdict'] and facts['owned_group_empty_after_cleanup']
            assert not facts['timed_out'] and not facts.get('error') and not facts.get('cleanup_error')
            assert (out/label/'stderr.txt').read_bytes()==b''
            raw=(out/label/'stdout.txt').read_bytes();lines=raw.splitlines(keepends=True)
            assert len(lines)==5 and all(re.fullmatch(rb'info string bench depth 11 nodes 321912 time [1-9]\d* nps [1-9]\d*\n',line) for line in lines)
            row.update(status='PASS_ACTUAL_FIVE_CANONICAL_ROWS',stdout_sha256=digest(out/label/'stdout.txt'),
                stderr_sha256=digest(out/label/'stderr.txt'),stdin_sha256=digest(out/label/'stdin.txt'),rows=5)
        finally:
            row['source_sha256_after']={name:digest(plan['source']/name) for name in expected}
            row['binary_sha256_after']={name:digest(plan['build']/name) for name in binary_before}
            save(out/'PROVENANCE.json',provenance)
        assert row['source_sha256_before']==row['source_sha256_after']
        assert binary_before==row['binary_sha256_after']
    assert digest(HELPER)==EXPECTED_HELPER and sorted(os.sched_getaffinity(0))==original_affinity
    provenance.update(status='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE',
        helper_sha256_after=digest(HELPER),completed_utc=datetime.now(timezone.utc).isoformat(),
        measured_nps_difference=None,elo_gain=None)
    save(out/'PROVENANCE.json',provenance)
    print(json.dumps({'status':provenance['status'],'baseline_rows':5,'candidate_rows':5,
        'sources':[p['source_sha'] for p in plans.values()],'nps_difference':None,'elo_gain':None},indent=2))

if __name__=='__main__':main()
