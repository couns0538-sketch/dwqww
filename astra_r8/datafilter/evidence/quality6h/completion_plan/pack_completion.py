"""Seal closed R8 evidence with fresh payload hashes; no training or source writes."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from datetime import datetime, timezone

WORK=Path('D:/grok-pc-data/dwqww/astra-r8-datafilter')
HERE=WORK/'astra_r8/datafilter'
ROOT=Path('C:/astra8_data/quality6h_20261102')
sys.path.insert(0,str(HERE))
from filter_positions import low_priority, input_identity, sha256
from native_forge_smoke import ENGINE, LOCK, PINS
from report_corpus import combine
from resource_policy import storage_guard
from verify_handoff import verify


def require(condition,message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path,value):
    payload=json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n'
    storage_guard(path,allowance=len(payload.encode('utf-8'))+1024*1024)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(payload)


def inventory_paths(excluded):
    files=[]
    aliases=[]
    directories=[ROOT]
    while directories:
        directory=directories.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path=Path(entry.path)
                if path==excluded:
                    continue
                info=entry.stat(follow_symlinks=False)
                redirected=stat.S_ISLNK(info.st_mode) or bool(
                    getattr(info,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT)
                if redirected:
                    target=path.resolve(strict=True)
                    require(target.is_relative_to(ROOT),'inventory alias escapes owned root')
                    aliases.append({'path':str(path),'target':str(target)})
                elif stat.S_ISDIR(info.st_mode):
                    directories.append(path)
                elif stat.S_ISREG(info.st_mode):
                    files.append(path)
                else:
                    raise ValueError('nonregular inventory entry: '+str(path))
    return sorted(files),sorted(aliases,key=lambda item:item['path'])


def main():
    low_priority()
    output=(ROOT/sys.argv[1]).resolve()
    require(output.parent==ROOT,'one new direct child of the quality-audit root is required')
    require(not os.path.lexists(output),'refusing existing packaging output')
    complete=read(ROOT/'corpus_completion/COMPLETE.json')
    require(complete['status']=='PASS' and complete['training_ready'] is False,'corpus completion missing')
    require(all(sha256(path)==digest for path,digest in complete['script_files'].items()),'auditor drift after completion')
    source_files=[*HERE.glob('*.py'),*HERE.glob('*.ps1'),*(HERE/'tests').glob('*.py'),Path(__file__)]
    source_pins={str(path):sha256(path) for path in sorted(source_files)}
    candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORK,text=True).strip()
    storage_guard(output,allowance=10_000_000)
    output.mkdir()
    save(output/'RUN.json',dict(source_commit=candidate,source_files=source_pins,
        started_utc=datetime.now(timezone.utc).isoformat(),strength='UNPROVEN',
        inventory_root=str(ROOT),excluded_directory=str(output),
        exclusion_reason='This packaging directory contains its own metadata, pinned separately. Stdout stays in the orchestration tool, not an inventoried file.'))
    published=verify(ROOT/'handoff_v4/manifest.json')
    save(output/'published_verify.json',published)
    profiles=[ROOT/'corpus_profile/SUMMARY.json',ROOT/'corpus_profile_rest/SUMMARY.json']
    aggregate=combine(profiles)
    require(aggregate==read(ROOT/'corpus_report/corpus_report.json'),'published descriptive report changed')
    reservoir=read(ROOT/'reservoir_audit/reservoir_receipt.json')
    native=read(ROOT/'native_corpus/report.json')
    require(reservoir['status']=='PASS' and reservoir['rows']==4736,'incomplete reservoir proof')
    require(native['status']=='PASS' and native['sample_positions']==4736 and native['positions']==9486,'incomplete native proof')
    require(len(native['fens'])==len(native['expected_perft2'])==len(native['actual_perft2'])==9486,'incomplete native vectors')
    require(native['sample_sha256']==reservoir['reservoir_sha256'],'native sample binding mismatch')
    require(native['sample_unchanged'] is True and native['expected_perft2']==native['actual_perft2'],'native state/perft mismatch')
    require(native['sha256']==LOCK==sha256(ENGINE),'exact lock executable changed')
    require({int(k):v for k,v in native['bench_actual'].items()}==PINS,'lock bench mismatch')
    stdout=(ROOT/'native_corpus/stdout.log').read_text(encoding='utf-8')
    observed=[int(value) for value in re.findall(r'^nodes (\d+)\s*$',stdout,re.M)]
    require(observed==native['actual_perft2'],'native log differs from recorded perft counts')
    benchmark={int(depth):int(nodes) for depth,nodes in re.findall(r'bench depth (\d+) nodes (\d+)',stdout)}
    require(benchmark==PINS,'native bench log differs from pins')
    options=(ROOT/'native_corpus/stdin.txt').read_text(encoding='utf-8').splitlines()
    require(options[:6]==['uci','setoption name Threads value 1','setoption name Hash value 16',
                          'setoption name OwnBook value false','setoption name UseNNUE value true','isready'],
            'native command options differ from the recorded lock transcript')
    require([line[len('position fen '):] for line in options if line.startswith('position fen ')]==native['fens'],
            'native commands differ from recorded FENs')
    expected_commands=list(options[:6])
    for fen in native['fens']:
        expected_commands+=['position fen '+fen,'go perft 2']
    expected_commands+=['bench '+str(depth) for depth in PINS]+['quit']
    require(options==expected_commands,'native command transcript differs from the bounded protocol')
    runtime=read(HERE/'evidence/quality6h/current_full_runtime_green/runtime.json')
    require(all(runtime['after']['files'].get(path)==digest==sha256(path)
                for path,digest in runtime['before']['files'].items()),'tested runtime changed')
    require('301 passed' in (ROOT/'current_full_runtime_green/pytest.log').read_text()
            and '11 subtests passed' in (ROOT/'current_full_runtime_green/pytest.log').read_text(),
            'current full suite result missing')
    save(output/'resource_before.json',storage_guard(output,allowance=10_000_000))
    paths,aliases=inventory_paths(output)
    inventory=[]
    for index,path in enumerate(paths):
        identity=input_identity(path)
        inventory.append(identity)
        if index and index%500==0:
            print(json.dumps(dict(event='inventory',files=index)),flush=True)
    paths_after,aliases_after=inventory_paths(output)
    require(paths==paths_after and aliases==aliases_after,'inventory membership changed')
    for path,identity in zip(paths,inventory):
        current=path.stat()
        require((current.st_size,current.st_ino,current.st_mtime_ns,current.st_ctime_ns)==
                (identity['bytes'],identity['inode'],identity['mtime_ns'],identity['ctime_ns']),
                'inventoried file changed: '+str(path))
    actual={Path(item['path']):item for item in inventory}
    filter_rows={}
    expected_kept={'all_off':1000000,'check':1000000,'mate':1000000,
                   'ply160':909569,'recipe_a':1000000,'recipe_b':1000000,'capture':849465}
    for name,kept in expected_kept.items():
        parent=ROOT/'filter_budget_million'
        folder=parent/'capture' if name=='capture' else parent/'million'/name
        receipt=read(folder/'report.json')
        require(receipt==read(HERE/'evidence/quality6h/filter_budget_million'/(name+'.report.json')),
                'filter receipt differs from the committed measured evidence: '+name)
        require(receipt['input']==1000000 and receipt['kept']==kept,'filter accounting mismatch: '+name)
        require((receipt['workers'],receipt['coordinator_workers'],receipt['pool_workers'])==(2,1,1),'wrong CPU allocation')
        require(set(receipt['hashes'])=={'records.jsonl','metadata.jsonl'},'incomplete filter payload inventory')
        for filename,digest in receipt['hashes'].items():
            require(actual[folder/filename]['sha256']==digest,'filter payload changed: '+name)
        filter_rows[name]=receipt
    require(filter_rows['recipe_a']['hashes']==filter_rows['recipe_b']['hashes'],'determinism mismatch')
    require(actual[ROOT/'reservoir_audit/audit_reservoir.jsonl']['sha256']==reservoir['reservoir_sha256'],
            'reservoir payload changed')
    for key,filename in [('report_sha256','corpus_report/corpus_report.json'),
                         ('reservoir_receipt_sha256','reservoir_audit/reservoir_receipt.json'),
                         ('native_receipt_sha256','native_corpus/report.json')]:
        require(actual[ROOT/filename]['sha256']==complete[key],'completion receipt changed: '+filename)
    baseline=[]
    for item in read(HERE/'evidence/baseline_hashes.json'):
        original=Path('C:/Users/Administrator/grok-pc/nnue')/Path(item['Path']).name
        expected=item['Hash'].lower()
        require(sha256(item['Path'])==expected==sha256(original),'production converter/helper changed')
        baseline.append(dict(path=str(original),sha256=expected))
    skill_sources=read(WORK/'skills/SAVED_ENGINE_SKILLS_SOURCE.json')
    for item in skill_sources['files']:
        payload=(WORK/'skills'/item['path']).read_bytes()
        blob=hashlib.sha1(('blob '+str(len(payload))+'\0').encode()+payload).hexdigest()
        require(blob==item['source_blob'],'saved upstream skill changed')
    require(all(sha256(path)==digest for path,digest in source_pins.items()),'candidate source changed during packaging')
    save(output/'full_output_hashes.json',dict(root=str(ROOT),excluded_directory=str(output),
         regular_files=len(inventory),payload_bytes=sum(item['bytes'] for item in inventory),
         aliases=aliases,files=inventory))
    save(output/'resource_after.json',storage_guard(output,allowance=1024*1024))
    receipt=dict(status='PASS',strength='UNPROVEN',source_commit=candidate,source_files=source_pins,
         full_output_hashes_sha256=sha256(output/'full_output_hashes.json'),
         verified_files=len(inventory),source_rows=aggregate['totals']['data_rows'],source_count=37,
         reservoir_rows=4736,native_positions=9486,legacy_production=baseline,
         saved_skill_files=len(skill_sources['files']),handoff_manifest_sha256=published['manifest_sha256'],
         filter_reports={name:{'kept':r['kept'],'hashes':r['hashes'],'elapsed_seconds':r['elapsed_seconds']}
                         for name,r in filter_rows.items()},
         timing_source_commit='88b7c6b1c83eb360d797e33dca601fa7d8a758da',
         timing_scope='Recorded two-total-process run; later CR/LF admission and verifier fixes are not new throughput measurements.',
         limitations=['No training or playing-strength qualification.',
                      'True qsearch unsupported by exact lock; self-play has no best moves or game IDs.',
                      'Complete source profiling is descriptive; only the bounded selected cohort has full holdout clearance.'],
         finished_utc=datetime.now(timezone.utc).isoformat())
    save(output/'COMPLETE.json',receipt)
    print(json.dumps(dict(status='PASS',verified_files=len(inventory),source_rows=receipt['source_rows'])),flush=True)


if __name__=='__main__':
    main()
