"""Read-only numeric transport census over already-admitted source bytes. UNPROVEN.

This does not rerun board validity, call native code or measure loader throughput.
The complete strict admission union supplies board/result validity separately.
"""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(HERE))
sys.dont_write_bytecode=True
from audit_forge_admission import DigestReader, make_plan
from filter_positions import low_priority, sha256
from profile_corpus import stat_key, write_json
from resource_policy import storage_guard
from seal_admission import BoundInputs

ROOT=Path('C:/astra8_data/extension5h_20261103')
UNION=ROOT/'admission_union_v1/SUMMARY.json'
UNION_SHA='e125a32916ebfd751a21a03d79e10baf2b94d3f13bb32e6c9a3522afc24f9dd4'
PROFILES=[Path('C:/astra8_data/quality6h_20261102')/name/'SUMMARY.json'
          for name in ('corpus_profile','corpus_profile_rest')]


def numeric_fields(line):
    parts=[part.strip() for part in line.split('|')]
    if len(parts)!=3:
        raise ValueError('expected three selfplay fields')
    fields=parts[0].split()
    if len(fields)!=6 or fields[1] not in ('w','b'):
        raise ValueError('full FEN with turn required')
    score,halfmove,fullmove=int(parts[1]),int(fields[4]),int(fields[5])
    ply=2*(fullmove-1)+(fields[1]=='b')
    return (score,halfmove,fullmove,ply), (
        -32768<=score<=32767, 0<=halfmove<=255, 0<=ply<=65534)


def scan(item):
    path=Path(item['path'])
    if stat_key(path)!=item['identity'] or sha256(item['sidecar'])!=item['sidecar_sha256']:
        raise ValueError('source/sidecar identity differs before census')
    digest,md5=hashlib.sha256(),hashlib.md5()
    counts=Counter();examples=[];minimum=None;maximum=None
    started=time.perf_counter()
    with path.open('rb') as source, io.TextIOWrapper(io.BufferedReader(
            DigestReader(source,digest,md5)),encoding='utf-8-sig',errors='strict',newline=None) as logical:
        for source_row,line in enumerate(logical,1):
            if not line.strip() or line.lstrip().startswith('#'):
                counts['skipped']+=1
                continue
            values,valid=numeric_fields(line)
            counts['rows']+=1
            counts['numeric_eligible']+=all(valid)
            for name,good in zip(('score_int16','halfmove_u8','native_ply_u16'),valid):
                counts[name]+=good
            minimum=values if minimum is None else tuple(map(min,zip(minimum,values)))
            maximum=values if maximum is None else tuple(map(max,zip(maximum,values)))
            if not all(valid) and len(examples)<16:
                examples.append(dict(source_row=source_row,values=values,valid=valid))
            if counts['rows']%1000000==0:
                storage_guard(allowance=4096)
                print(json.dumps({'event':'numeric_census','source':path.name,'rows':counts['rows']}),flush=True)
    if stat_key(path)!=item['identity'] or sha256(item['sidecar'])!=item['sidecar_sha256']:
        raise ValueError('source/sidecar identity changed during census')
    if (digest.hexdigest()!=item['expected_sha256'] or md5.hexdigest()!=item['expected_md5']
            or counts['rows']!=item['expected_data_rows']):
        raise ValueError('complete source bytes/count differ from admission')
    return dict(status='PASS',numeric_range_status='PASS' if counts['rows']==counts['numeric_eligible'] else 'FAIL',
                strength='UNPROVEN',path=str(path),counts=dict(counts),
                sha256=digest.hexdigest(),md5=md5.hexdigest(),source_identity=item['identity'],
                sidecar_sha256=item['sidecar_sha256'],fields=['score','halfmove','fullmove','zero_based_ply'],
                minimum=minimum,maximum=maximum,excluded_examples=examples,
                seconds=time.perf_counter()-started,complete_scan=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--max-sources',type=int)
    args=parser.parse_args();low_priority()
    storage_guard(args.output,allowance=2_000_000)
    args.output.mkdir()
    bound=BoundInputs();union=bound.read(UNION)
    if bound.files[str(UNION.resolve())]!=UNION_SHA or union['complete_reference_set'] is not True:
        raise ValueError('complete strict admission union required')
    plan=make_plan(PROFILES,max_sources=args.max_sources)
    admitted={str(Path(row['path']).resolve()):row for row in union['sources']}
    all_names=set(admitted)
    for item in plan['sources']:
        prior=admitted.get(str(Path(item['path']).resolve()))
        if (prior is None or prior['invalid_rows']!=0 or prior['complete_scan'] is not True
                or (prior['sha256'],prior['data_rows'],prior['source_identity'])
                != (item['expected_sha256'],item['expected_data_rows'],item['identity'])):
            raise ValueError('selected source lacks matching complete admission')
    if plan['complete_reference_set'] and {str(Path(item['path']).resolve()) for item in plan['sources']}!=all_names:
        raise ValueError('complete source union differs')
    files=[*HERE.glob('*.py'),Path(__file__).resolve()]
    pins={str(path):sha256(path) for path in files}
    write_json(args.output/'RUN.json',dict(source_files=pins,plan=plan,strict_union_sha256=UNION_SHA,
          scope='Numeric storage-range census only. Strict board/result admission retains original source identity.',
          strength='UNPROVEN'))
    bound.files[str((args.output/'RUN.json').resolve())]=sha256(args.output/'RUN.json')
    started=time.perf_counter();reports=[];totals=Counter()
    for index,item in enumerate(plan['sources']):
        report=scan(item);write_json(args.output/f'{index:03d}.json',report)
        reports.append(dict(path=str(args.output/f'{index:03d}.json'),sha256=sha256(args.output/f'{index:03d}.json')))
        bound.files[str((args.output/f'{index:03d}.json').resolve())]=reports[-1]['sha256']
        totals.update(report['counts'])
    if any(sha256(path)!=digest for path,digest in pins.items()):
        raise ValueError('census source changed')
    if any(stat_key(item['path'])!=item['identity'] or sha256(item['sidecar'])!=item['sidecar_sha256']
           for item in plan['sources']):
        raise ValueError('source identity changed before publication')
    bound.verify()
    write_json(args.output/'COMPLETE.json',dict(status='PASS',strength='UNPROVEN',counts=dict(totals),
          numeric_range_status='PASS' if totals['rows']==totals['numeric_eligible'] else 'FAIL',
          source_files=pins,reports=reports,strict_union_sha256=UNION_SHA,
          complete_reference_set=plan['complete_reference_set'],seconds=time.perf_counter()-started,
          limitations='Numeric bounds only; no native allocation, training, relabeling, loader-throughput or full-corpus holdout claim.'))


if __name__=='__main__':main()
