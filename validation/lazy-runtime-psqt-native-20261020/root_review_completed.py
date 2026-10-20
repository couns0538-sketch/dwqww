"""Independently inspect completed native receipts/raw logs without running engines."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
SHA = '61f598056572dfade6994af8ad2e38817cd28aa3'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    source_gate = json.loads((HERE/'ROOT-FROZEN-SOURCE-GATES.json').read_text())
    profiles = []
    for profile in ('release','asan'):
        root = HERE/('frozen-'+profile+'-attempt1')
        receipt = json.loads((root/'summary.json').read_text())
        assert receipt['status']=='PASS' and receipt['source_commit']==SHA
        assert len(receipt['ctest_names'])==11
        assert receipt['actual_ctest_commands']==receipt['expected_ctest_commands']
        assert receipt['source_sha256_before_tests']==receipt['source_sha256_after_tests']==source_gate['inputs']
        assert receipt['binary_sha256_before']==receipt['binary_sha256_after']
        assert receipt['runtime_psqt_contract_actual_summaries']==[['347','0']]
        assert not any(record['matches'] for record in receipt['sanitizer_diagnostic_scan'].values())
        raw=(root/'ctest.stdout').read_text()
        assert '100% tests passed, 0 tests failed out of 11' in raw
        last=(root/'original-LastTest.log').read_text()
        block=re.search(r'(?ms)^\d+/\d+ Testing: forge_runtime_psqt_tests\n.*?(?=^\d+/\d+ Testing: |\Z)',last)
        assert block and 'SUMMARY checks=347 failures=0' in block.group()
        exported=Path(receipt['source_export'])
        for name, expected in source_gate['inputs'].items():
            assert digest(exported/name)==expected,name
        build=Path('/workspace/.cloud-setup/lazy-runtime-psqt-native-'+profile)
        for name,expected in receipt['binary_sha256_after'].items():
            assert digest(build/name)==expected,name
        for step in receipt['steps']:
            assert step['exit_code']==0 and not step['error'] and not step['timed_out']
            assert step['cleanup']['no_live_owned_processes'] and not step['cleanup']['unexpected_live_members_after_command']
            label=step['label']
            assert digest(root/(label+'.stdout'))==step['stdout_sha256']
            assert digest(root/(label+'.stderr'))==step['stderr_sha256']
        profiles.append({'profile':profile,'ctest_passed':11,'runtime_checks':347,
            'receipt_sha256':digest(root/'summary.json'),'raw_ctest_sha256':digest(root/'ctest.stdout'),
            'engine_sha256':receipt['binary_sha256_after']['forge']})
    parity=json.loads((HERE/'search-parity-attempt1/summary.json').read_text())
    assert parity['status']=='passed' and len(parity['sessions'])==28
    normalized={}
    for session in parity['sessions']:
        assert session['exit_code']==0 and session['capture_complete'] and session['reader_threads_joined']
        assert not session['reader_errors'] and session['sanitizer_classification']=='none'
        assert len(session['searches'])==2
        values=[]
        for search in session['searches']:
            assert search['completed']
            lines=[re.sub(r'\b(time|nps)\s+\d+\b',lambda m:m[1]+' <excluded>',row) for row in search['raw_lines']]
            assert lines==search['normalized_lines']
            values.append(lines)
        key=(session['nnue_mode'],session['case'])
        normalized.setdefault(key,{})[session['engine_label']]=values
    assert len(normalized)==14
    assert all(pair['baseline']==pair['candidate'] for pair in normalized.values())
    bench=HERE/'release-parity-wrapper-attempt1/bench11.stdout.bin'
    assert re.fullmatch(rb'info string bench depth 11 nodes 321912 time \d+ nps \d+\s*',bench.read_bytes())
    record={'status':'PASS_ROOT_RELEASE_ASAN_AND_LOGICAL_PARITY_REVIEW',
        'utc':datetime.now(timezone.utc).isoformat(),'source_commit':SHA,'profiles':profiles,
        'source_files_each':74,'searches':56,'independent_normalized_pair_comparisons':14,
        'bench11_nodes':321912,'bench_stdout_sha256':digest(bench),
        'tsan_and_active_uci':'PENDING_SEPARATE_REVIEW','engine_executions_by_reviewer':0,
        'nps_ratio':None,'elo_gain':None}
    (HERE/'ROOT-RELEASE-ASAN-PARITY-PROOFS.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':
    main()
