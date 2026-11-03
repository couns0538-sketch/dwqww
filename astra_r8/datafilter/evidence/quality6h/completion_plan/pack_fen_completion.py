"""Fresh, bounded final inventory after reviewed FEN admission repair. UNPROVEN."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

WORK=Path('D:/grok-pc-data/dwqww/astra-r8-datafilter')
ROOT=Path('C:/astra8_data/quality6h_20261102')
HERE=WORK/'astra_r8/datafilter'
sys.path.insert(0,str(HERE))
from filter_positions import low_priority, sha256, input_identity
from native_forge_smoke import ENGINE, LOCK, PINS
from report_corpus import combine
from resource_policy import storage_guard
from verify_handoff import verify


def require(condition,message):
    if not condition: raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path,value):
    data=json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n'
    storage_guard(path,allowance=len(data.encode('utf-8'))+1024*1024)
    with path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(data)


def main():
    low_priority()
    output=ROOT/'final_pack_v2'
    storage_guard(output,allowance=10_000_000)
    output.mkdir()
    original=ROOT/'pack_completion.py'
    require(sha256(original)=='25a4626eb6a3116070600019eb636714a0267df02931afc8496a09f40e40f874','inventory helper changed')
    spec=importlib.util.spec_from_file_location('original_inventory',original)
    helper=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)  # Only definitions/imports; its main is guarded.
    pins={str(p):sha256(p) for p in sorted([*HERE.glob('*.py'),*HERE.glob('*.ps1'),
         *(HERE/'tests').glob('*.py'), HERE/'evidence/conftest.py', Path(__file__)])}
    candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORK,text=True).strip()
    save(output/'RUN.json',dict(source_commit=candidate,source_files=pins,strength='UNPROVEN',
         started_utc=datetime.now(timezone.utc).isoformat(),excluded_directory=str(output)))
    current=read(ROOT/'fen_validation/COMPLETE.json')
    require(current['status']=='PASS' and current['known_cohort_rows']==2_000_000,'FEN validation incomplete')
    require(all(sha256(path)==digest for path,digest in current['source_files'].items()),'FEN-validation source drift')
    published=verify(ROOT/'handoff_v5/manifest.json')
    require(published['manifest_sha256']==current['manifest_sha256'],'current handoff mismatch')
    save(output/'published_verify.json',published)
    prior=read(ROOT/'corpus_completion/COMPLETE.json')
    require(prior['status']=='PASS','historical corpus completion failed')
    historical={}
    for name,digest in prior['script_files'].items():
        path=Path(name)
        if sha256(path)==digest: continue
        require(path in (HERE/'records.py',HERE/'native_forge_smoke.py'),'unexpected source drift since corpus audit')
        old=subprocess.check_output(['git','show',prior['source_commit']+':'+path.relative_to(WORK).as_posix()],cwd=WORK)
        require(hashlib.sha256(old).hexdigest()==digest,'historical source attribution differs')
        historical[name]=dict(commit=prior['source_commit'],sha256=digest,current_sha256=sha256(path))
    report=combine([ROOT/'corpus_profile/SUMMARY.json',ROOT/'corpus_profile_rest/SUMMARY.json'])
    require(report==read(ROOT/'corpus_report/corpus_report.json'),'descriptive report changed')
    for key,path in [('report_sha256',ROOT/'corpus_report/corpus_report.json'),
                     ('reservoir_receipt_sha256',ROOT/'reservoir_audit/reservoir_receipt.json'),
                     ('native_receipt_sha256',ROOT/'native_corpus/report.json')]:
        require(sha256(path)==prior[key],'historical corpus evidence changed')
    reservoir=read(ROOT/'reservoir_audit/reservoir_receipt.json')
    require(reservoir['status']=='PASS' and reservoir['rows']==4736
            and sha256(ROOT/'reservoir_audit/audit_reservoir.jsonl')==reservoir['reservoir_sha256'],
            'reservoir payload differs from the original source-label audit')
    runtime=read(HERE/'evidence/quality6h/full_fen_green/runtime.json')
    require(runtime['before']==runtime['after'],'runtime changed during full tests')
    require(all(sha256(path)==digest for path,digest in runtime['after']['files'].items()),'tested runtime changed afterward')
    log=(ROOT/'full_fen_green/pytest.log').read_text()
    require('323 passed' in log and '11 subtests passed' in log,'current full suite missing')
    native_path=ROOT/'fen_validation/native'
    native=read(native_path/'report.json')
    old_native=read(ROOT/'native_corpus/report.json')
    require(sha256(native_path/'report.json')==current['native_receipt_sha256'],'native receipt changed')
    require(native['status']=='PASS' and native['sample_positions']==4736 and native['positions']==9486,'native coverage missing')
    require(len(native['fens'])==len(native['expected_perft2'])==len(native['actual_perft2'])==9486,'native vectors incomplete')
    require(native['fens']==old_native['fens'] and native['expected_perft2']==old_native['expected_perft2']==native['actual_perft2'],
            'native corpus/reference differs')
    require(native['sample_unchanged'] and native['sample_sha256']==sha256(ROOT/'reservoir_audit/audit_reservoir.jsonl'),
            'native sample mismatch')
    require(native['sha256']==LOCK==sha256(ENGINE),'lock executable changed')
    stdout=(native_path/'stdout.log').read_text()
    require([int(v) for v in re.findall(r'^nodes (\d+)\s*$',stdout,re.M)]==native['actual_perft2'],'native log mismatch')
    require({int(d):int(n) for d,n in re.findall(r'bench depth (\d+) nodes (\d+)',stdout)}==PINS,'bench log mismatch')
    commands=['uci','setoption name Threads value 1','setoption name Hash value 16',
              'setoption name OwnBook value false','setoption name UseNNUE value true','isready']
    for fen in native['fens']: commands+=['position fen '+fen,'go perft 2']
    commands+=['bench '+str(depth) for depth in PINS]+['quit']
    require((native_path/'stdin.txt').read_text().splitlines()==commands,'native protocol mismatch')
    save(output/'resource_before.json',storage_guard(output,allowance=10_000_000))
    paths,aliases=helper.inventory_paths(output)
    inventory=[input_identity(path) for path in paths]
    require(helper.inventory_paths(output)==(paths,aliases),'inventory membership changed')
    for path,item in zip(paths,inventory):
        info=path.stat()
        require((info.st_size,info.st_ino,info.st_mtime_ns,info.st_ctime_ns)==
                (item['bytes'],item['inode'],item['mtime_ns'],item['ctime_ns']),'inventoried file changed')
    actual={Path(item['path']):item for item in inventory}
    for name,kept in {'all_off':1000000,'check':1000000,'mate':1000000,'ply160':909569,
                      'recipe_a':1000000,'recipe_b':1000000,'capture':849465}.items():
        folder=ROOT/'filter_budget_million'/('capture' if name=='capture' else 'million/'+name)
        receipt=read(folder/'report.json')
        require(receipt==read(HERE/'evidence/quality6h/filter_budget_million'/(name+'.report.json')),'filter receipt changed')
        require(receipt['input']==1000000 and receipt['kept']==kept,'filter counts changed')
        require((receipt['workers'],receipt['coordinator_workers'],receipt['pool_workers'])==(2,1,1),'filter allocation differs')
        require(set(receipt['hashes'])=={'records.jsonl','metadata.jsonl'},'filter inventory incomplete')
        for name,digest in receipt['hashes'].items(): require(actual[folder/name]['sha256']==digest,'filter payload changed')
    baseline=read(ROOT/'final_pack/COMPLETE.json')
    for item in baseline['legacy_production']: require(sha256(item['path'])==item['sha256'],'production converter/helper changed')
    skills=read(WORK/'skills/SAVED_ENGINE_SKILLS_SOURCE.json')
    for item in skills['files']:
        data=(WORK/'skills'/item['path']).read_bytes()
        require(hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest()==item['source_blob'],'saved upstream skill changed')
    require(all(sha256(path)==digest for path,digest in pins.items()),'packaged source changed')
    save(output/'full_output_hashes.json',dict(root=str(ROOT),excluded_directory=str(output),
         regular_files=len(inventory),payload_bytes=sum(item['bytes'] for item in inventory),aliases=aliases,files=inventory))
    resource=storage_guard(output,allowance=1024*1024)
    save(output/'resource_after.json',resource)
    save(output/'COMPLETE.json',dict(status='PASS',strength='UNPROVEN',source_commit=candidate,source_files=pins,
         verified_files=len(inventory),historical_source_attribution=historical,
         current_fen_validation_sha256=sha256(ROOT/'fen_validation/COMPLETE.json'),
         manifest_sha256=published['manifest_sha256'],native_positions=9486,source_rows=report['totals']['data_rows'],
         inventory_sha256=sha256(output/'full_output_hashes.json'),resource=resource,
         finished_utc=datetime.now(timezone.utc).isoformat(),
         limitations=['Filter timing remains the source-88b7c6b1 measurement, not a measurement of the later admission changes.',
                     'Full corpus profiling is descriptive; only the bounded cohort has holdout clearance.',
                     'No training, GPU or strength gate. True qsearch remains BLOCKED.']))
    print(json.dumps(dict(status='PASS',verified_files=len(inventory),manifest_sha256=published['manifest_sha256'])),flush=True)


if __name__=='__main__': main()
