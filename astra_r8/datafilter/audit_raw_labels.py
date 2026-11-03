"""Independent literal outcome oracle against original source text, not normalization."""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import time
from filter_positions import low_priority, sha256
from resource_policy import storage_guard

ORACLE={('w','0'):-1,('b','0'):1,('w','0.5'):0,('b','0.5'):0,
        ('w','1'):1,('b','1'):-1,('w','?'):None,('b','?'):None}

def run(root):
    manifest=json.loads((root/'cohort/manifest.json').read_text())
    checked=[]
    with open(root/'cohort/million.jsonl',encoding='utf-8') as normalized:
        for source in manifest['sources']:
            with open(source['path'],encoding='utf-8-sig') as raw:
                for line_number,line in enumerate(raw,1):
                    if not line.strip() or line.lstrip().startswith('#'):continue
                    if len(checked)==1000:break
                    fen,score,result=[v.strip() for v in line.split('|')]
                    token={'0.0':'0','1.0':'1','*':'?','':'?'}.get(result,result)
                    expected=ORACLE[(fen.split()[1],token)]
                    row=json.loads(next(normalized))
                    assert row['fen']==fen and row['score_stm']==int(score)
                    assert row['result_stm']==expected and row['has_result']==(expected is not None)
                    assert Path(row['source'])==Path(source['path']) and row['source_row']==line_number
                    checked.append(dict(source=source['path'],source_row=line_number,fen=fen,
                                        raw_white_result=result,expected_stm=expected,score_stm=int(score)))
            if len(checked)==1000:break
    assert len(checked)==1000
    destination=root/'actual_source_orientation1000.json'
    with open(destination,'x',encoding='utf-8') as fh:
        json.dump(dict(status='PASS',rows=len(checked),cases=checked),fh,indent=1)
    return dict(status='PASS',rows=len(checked),output=str(destination))


def audit_reservoirs(profiles, output):
    """Replay selected original lines and full source digests; never emit training data."""
    from profile_corpus import stat_key, write_json
    from report_corpus import combine
    output=Path(output).resolve()
    partial=output.with_name(output.name+'.partial')
    if os.path.lexists(output) or os.path.lexists(partial):
        raise FileExistsError('refusing existing reservoir audit output')
    storage_guard(output,allowance=20_000_000)
    accounting=combine(profiles)
    watched={str(Path(__file__).with_name(name)):sha256(Path(__file__).with_name(name))
             for name in ('audit_raw_labels.py','report_corpus.py','profile_corpus.py',
                          'filter_positions.py','resource_policy.py')}
    partial.mkdir(parents=True)
    receipts=[]
    started=time.perf_counter()
    with (partial/'audit_reservoir.jsonl').open('xb') as combined:
        for profile_path in profiles:
            profile_path=Path(profile_path).resolve()
            summary=json.loads(profile_path.read_text(encoding='utf-8'))
            for index,source in enumerate(summary['sources']):
                sample_path=profile_path.with_name(f'{index:03}.sample.jsonl')
                payload=sample_path.read_bytes()
                if hashlib.sha256(payload).hexdigest()!=source['sample_sha256']:
                    raise ValueError('reservoir changed after profile verification')
                lines=payload.splitlines(keepends=True)
                expected_count=min(summary['sample_rows_per_source'],source['valid_rows'])
                if not expected_count or len(lines)!=expected_count:
                    raise ValueError('incomplete audit reservoir')
                wanted={}
                for raw in lines:
                    row=json.loads(raw)
                    if (type(row['score_stm']) is not int or any(
                            value is not None and (type(value) is not int or value not in (-1,0,1))
                            for value in (row['result_white'],row['result_stm']))):
                        raise ValueError('invalid reservoir score or outcome type')
                    number=row['source_row']
                    if (type(number) is not int or not 1<=number<=source['last_source_row']
                            or number in wanted or Path(row['source']).resolve()!=Path(source['path']).resolve()):
                        raise ValueError('invalid reservoir source provenance')
                    wanted[number]=row
                if stat_key(source['path'])!=source['source_identity']:
                    raise ValueError('source changed before reservoir replay')
                digest=hashlib.sha256(); md5=hashlib.md5(); checked=0; source_lines=0
                with open(source['path'],'rb') as original:
                    for number,raw in enumerate(original,1):
                        digest.update(raw);md5.update(raw);source_lines=number
                        if number not in wanted:
                            continue
                        fields=[part.strip() for part in raw.decode('utf-8-sig' if number==1 else 'utf-8').split('|')]
                        if len(fields)!=3:raise ValueError('invalid selected raw source row')
                        fen,score,result=fields
                        token={'0.0':'0','1.0':'1','*':'?','':'?'}.get(result,result)
                        expected=ORACLE[(fen.split()[1],token)]
                        white={'0':-1,'0.5':0,'1':1,'?':None}[token]
                        row=wanted[number]
                        if (row['fen']!=fen or row['score_stm']!=int(score) or
                                row['result_stm']!=expected or row['result_white']!=white):
                            raise ValueError(f'reservoir differs from original source: {source["path"]}:{number}')
                        checked+=1
                if (checked!=expected_count or digest.hexdigest()!=source['sha256']
                        or md5.hexdigest()!=source['expected_md5']
                        or stat_key(source['path'])!=source['source_identity']):
                    raise ValueError('source hash, identity or selected row count changed')
                if sha256(source['path']+'.md5')!=source['sidecar_sha256']:
                    raise ValueError('producer sidecar changed during replay')
                storage_guard(partial,allowance=len(payload)+1024*1024)
                combined.write(payload)
                combined.flush()
                receipt=dict(source=source['path'],source_sha256=digest.hexdigest(),
                             source_md5=md5.hexdigest(),source_lines=source_lines,
                             checked_rows=checked,sample_sha256=source['sample_sha256'])
                receipts.append(receipt)
                print(json.dumps(receipt),flush=True)
    after=combine(profiles)
    if after['profile_inputs']!=accounting['profile_inputs'] or any(sha256(p)!=h for p,h in watched.items()):
        raise ValueError('profile evidence or auditor changed during replay')
    result=dict(status='PASS',strength='UNPROVEN',training_ready=False,
                scope='Full-source rehash and literal outcome/full-FEN checks on bounded audit reservoirs only.',
                rows=sum(r['checked_rows'] for r in receipts),sources=receipts,
                profile_inputs=accounting['profile_inputs'],auditor_files=watched,
                reservoir_sha256=sha256(partial/'audit_reservoir.jsonl'),
                elapsed_seconds=time.perf_counter()-started)
    write_json(partial/'reservoir_receipt.json',result)
    storage_guard(output,allowance=0)
    partial.rename(output)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path)
    p.add_argument('--profiles',nargs='+',type=Path,help='complete profile summaries; root becomes a fresh audit output')
    a=p.parse_args();low_priority()
    print(json.dumps(audit_reservoirs(a.profiles,a.root) if a.profiles else run(a.root),indent=2))
