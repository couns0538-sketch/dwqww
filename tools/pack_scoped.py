"""Build the fresh R13 PGN-mode evidence pack from an explicit safe file list."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
from run_policy import Inputs, new_directory, safe_path, write_json, free_guard
from seal_pack import seal
from verify_pack import verify

ROOT=Path(__file__).resolve().parents[1]

def validate_suite(receipt,results,collection):
    for value in (receipt.get('exit_code'),results.get('exitstatus'),results.get('failed')):
        if type(value) is not int or value!=0:
            raise ValueError('full suite did not pass')
    if receipt.get('stop_reason') is not None or receipt.get('priority')!='Idle' or type(receipt.get('threads')) is not int or receipt['threads']!=1:
        raise ValueError('invalid suite process receipt')
    count=collection.get('count')
    nodes=collection.get('nodeids')
    if type(count) is not int or count<564 or type(results.get('collected')) is not int or results['collected']!=count:
        raise ValueError('full-suite collection incomplete')
    if not isinstance(nodes,list) or len(nodes)!=count or any(not isinstance(n,str) or not n for n in nodes) or len(set(nodes))!=count:
        raise ValueError('collection node inventory invalid')
    calls=[]
    reports=results.get('results')
    if not isinstance(reports,list):
        raise ValueError('missing per-test results')
    for report in reports:
        if report.get('outcome')!='passed' or report.get('when')!='call' or report.get('nodeid') not in nodes:
            raise ValueError('failed, skipped or foreign result')
        if report.get('kind')=='test':
            calls.append(report['nodeid'])
        elif report.get('kind')!='subtest':
            raise ValueError('untyped test result')
    if Counter(calls)!=Counter(nodes):
        raise ValueError('omitted or duplicated collected test result')
    return count


def validate_source_receipt(receipt,entry,inputs):
    if type(receipt.get('exit_code')) is not int or receipt['exit_code']!=0 or receipt.get('stop_reason') is not None:
        raise ValueError('unsuccessful producer receipt')
    script=safe_path(receipt['script'])
    if script!=ROOT/'tools'/entry or receipt.get('script_sha256_before')!=receipt.get('script_sha256_after'):
        raise ValueError('producer entry point mismatch')
    inputs.verify(script,receipt['script_sha256_after'])
    before,after=receipt.get('source_sha256_before'),receipt.get('source_sha256_after')
    if not isinstance(before,dict) or not before or before!=after:
        raise ValueError('missing or changed producer source identity')
    current={p.relative_to(ROOT).as_posix() for folder in ('tools','tests','astra_r8/datafilter')
             for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.ps1')}
    if set(before)!=current:
        raise ValueError('producer source census mismatch')
    for name,digest in before.items():
        inputs.verify(safe_path(ROOT/name),digest)


def build(output,suite,qc,qc_run):
    inputs=Inputs()
    suite=safe_path(suite)
    qc=safe_path(qc)
    qc_run=safe_path(qc_run)
    receipt=inputs.json(suite/'receipt.json')
    tests=inputs.json(suite/'test_results.json')
    collection=inputs.json(suite/'collection.json')
    statistics=inputs.json(qc/'statistics.json')
    validate_suite(receipt,tests,collection)
    validate_source_receipt(receipt,'run_tests.py',inputs)
    qc_receipt=inputs.json(qc_run/'receipt.json')
    validate_source_receipt(qc_receipt,'p5_qc.py',inputs)
    arguments=qc_receipt['arguments']
    if '--out' not in arguments or safe_path(arguments[arguments.index('--out')+1])!=qc:
        raise ValueError('QC receipt output binding mismatch')
    complete=inputs.json(qc/'COMPLETE.json')
    if complete['status']!='PASS' or set(complete['files'])!={'statistics.json','INPUTS.json','mate_rows.jsonl'}:
        raise ValueError('QC completion receipt missing or incomplete')
    for name,digests in complete['files'].items():
        snapshot=inputs.verify(qc/name,digests['sha256'])
        if snapshot.hashes['md5']!=digests['md5']:
            raise ValueError('QC completion MD5 mismatch')
    if statistics['status']!='PASS' or statistics['cohorts']['r14b']['rows']!=999921 or statistics['cohorts']['old440k']['rows']!=440000:
        raise ValueError('QC population/result mismatch')
    output=new_directory(output,32*1024*1024)
    files={
        'REPORT.md':ROOT/'pgnpack'/'REPORT.md',
        'SEARCH.json':ROOT/'pgnpack'/'SEARCH.json',
        'MIX_SPEC_BASE.md':ROOT/'astra_r8'/'datafilter'/'MIX_SPEC.md',
        'historical_PGN_COMPLETE.json':ROOT/'astra_r8'/'datafilter'/'evidence'/'extension5h'/'final_pack_v2'/'COMPLETE.json',
        'qc_statistics.json':qc/'statistics.json',
        'qc_inputs.json':qc/'INPUTS.json',
        'qc_complete.json':qc/'COMPLETE.json',
        'qc_receipt.json':qc_run/'receipt.json',
        'suite_collection.json':suite/'collection.json',
        'suite_results.json':suite/'test_results.json',
        'suite_receipt.json':suite/'receipt.json',
        'suite.log':suite/'output.log',
        'suite.stderr.log':suite/'stderr.log',
        'game_hash.py':ROOT/'tools'/'game_hash.py',
        'test_game_hash.py':ROOT/'tests'/'test_game_hash.py',
    }
    for name,source in files.items():
        snapshot=inputs.get(source)
        with (output/name).open('xb') as target:
            for chunk in snapshot.chunks():
                free_guard(len(chunk)+1024*1024)
                target.write(chunk)
    historical=inputs.json(files['historical_PGN_COMPLETE.json'])
    # Do not follow any path referenced by the historical receipt.
    write_json(output/'PACK_STATUS.json',dict(schema=1,scope='R13 scoped PGN-mode evidence',
        qc_integrity='PASS',full_suite='PASS',collected=tests['collected'],game_separation='UNVERIFIED',authentic_game_overlap=None,
        historical_receipt_included_as_context_only=True,protected_historical_checks_rerun=False,
        historical_status=historical.get('status'),historical_validation_mode=historical.get('validation_mode'),
        engine_or_training_executed=False,claim='No strength or training-readiness claim'))
    write_json(output/'INPUTS.json',inputs.receipts())
    seal(output)
    return verify(output)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True)
    parser.add_argument('--suite',required=True)
    parser.add_argument('--qc',required=True)
    parser.add_argument('--qc-run',required=True)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    args=parser.parse_args()
    print(build(args.out,args.suite,args.qc,args.qc_run))
