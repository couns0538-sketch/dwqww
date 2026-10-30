#!/usr/bin/env python3
"""Read-only comparison of a sealed pilot against the completed prefix of a live run.
IDEA_SOURCE: Forge kept-row provenance, FPOS column spool and bounded native-worker determinism contract.
This checks only the requested prefix. It never seals or writes either input folder.
"""
from pathlib import Path
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/data'))
from forge_pos import PosReader


def need(condition,message):
    if not condition:raise ValueError(message)


def sha(data):return hashlib.sha256(data).hexdigest()


def kept_prefix(folder,limit):
    rows=[];raw=[]
    with (folder/'kept_rows.tsv').open('rb') as source:
        header=source.readline();raw.append(header)
        names=header.decode().rstrip('\n').split('\t')
        need('input_index' in names and 'output_index' in names,'missing provenance indices')
        for line in source:
            values=line.decode().rstrip('\n').split('\t')
            need(len(names)==len(values),'malformed provenance row')
            row=dict(zip(names,values));index=int(row['input_index'])
            if index>=limit:break
            need(int(row['output_index'])==len(rows),'retained rows are not an initial contiguous output prefix')
            need(not rows or index>int(rows[-1]['input_index']),'source indices not strictly increasing')
            rows.append(row);raw.append(line)
    return rows,b''.join(raw)


def decisions_prefix(folder,limit):
    raw=[];rows=[]
    with gzip.open(folder/'decisions.tsv.gz','rb') as source:
        header=source.readline();raw.append(header)
        names=header.decode().rstrip('\n').split('\t')
        for expected in range(limit):
            line=source.readline();need(bool(line),'decision prefix not yet available')
            values=line.decode().rstrip('\n').split('\t')
            need(len(values)==len(names),'malformed decision row')
            row=dict(zip(names,values));need(int(row['input_index'])==expected,'decision source index gap')
            rows.append(row);raw.append(line)
    return rows,b''.join(raw)


def live_columns(folder,stem,count):
    result={}
    for name,width in (('boards',32),('scores',2),('meta',1),('hce-data',2)):
        with (folder/(stem+'.'+name+'.part')).open('rb') as source:
            value=source.read(width*count)
        need(len(value)==width*count,'live column prefix not yet fully flushed: '+name)
        result[name]=value
    with (folder/(stem+'.fen.part')).open('rb') as source:
        lines=[source.readline() for _ in range(count)]
    need(all(line.endswith(b'\n') for line in lines),'live FEN prefix incomplete')
    result['fen']=b''.join(lines)
    return result,lines


def pilot_columns(folder,stem,expected):
    columns={k:bytearray() for k in ('boards','scores','meta','hce-data')}
    with PosReader(folder/(stem+'.pos'),folder/(stem+'.hce')) as reader:
        need(reader.n==expected,'pilot record count differs from prefix retained count')
        for row in reader:
            columns['boards'].extend(row.board);columns['scores'].extend(struct.pack('<h',row.score))
            columns['meta'].append(row.meta);columns['hce-data'].extend(struct.pack('<h',row.hce))
    with (folder/(stem+'.fen')).open('rb') as source:lines=list(source)
    need(len(lines)==expected and all(x.endswith(b'\n') for x in lines),'pilot FEN count/integrity mismatch')
    result={k:bytes(v) for k,v in columns.items()};result['fen']=b''.join(lines)
    return result,lines


def record(columns,lines,index):
    return (columns['boards'][32*index:32*(index+1)],columns['scores'][2*index:2*(index+1)],
            columns['meta'][index:index+1],columns['hce-data'][2*index:2*(index+1)],lines[index])


def run(pilot,live,limit):
    pilot_bytes=(pilot/'summary.json').read_bytes();live_bytes=(live/'progress.json').read_bytes()
    a=json.loads(pilot_bytes);b=json.loads(live_bytes)
    need(a['status']=='SEALED' and a['input_rows']==limit,'pilot must be sealed at the requested input prefix')
    need(b['input_rows']>=limit,'live progress has not completed requested prefix')
    need(a['config']['nodes']==b['config']['nodes']==1024,'comparison requires both requested1024-node budgets')
    need(a['config']['workers']==1 and b['config']['workers']==3,'comparison requires 1worker versus3workers')
    pa,raw_pa=kept_prefix(pilot,limit);pb,raw_pb=kept_prefix(live,limit)
    da,raw_da=decisions_prefix(pilot,limit);db,raw_db=decisions_prefix(live,limit)
    ia=[int(row['input_index']) for row in pa];ib=[int(row['input_index']) for row in pb]
    need(ia==[i for i,row in enumerate(da) if row['decision']=='kept'],'pilot decisions/provenance disagree')
    need(ib==[i for i,row in enumerate(db) if row['decision']=='kept'],'live decisions/provenance disagree')
    ca,fa=pilot_columns(pilot,a['config']['stem'],len(pa));cb,fb=live_columns(live,b['config']['stem'],len(pb))
    by_a={index:i for i,index in enumerate(ia)};by_b={index:i for i,index in enumerate(ib)}
    common=sorted(set(ia)&set(ib));matching=0;record_mismatch=[]
    for index in common:
        if record(ca,fa,by_a[index])==record(cb,fb,by_b[index]):matching+=1
        elif len(record_mismatch)<20:record_mismatch.append(index)
    decision_mismatch=[i for i in range(limit) if da[i]!=db[i]]
    transitions=Counter(da[i]['decision']+' -> '+db[i]['decision'] for i in decision_mismatch)
    # Re-read only the same bounded prefix; growing tails are intentionally ignored.
    reread,_=live_columns(live,b['config']['stem'],len(pb))
    _,reread_kept=kept_prefix(live,limit);_,reread_decisions=decisions_prefix(live,limit)
    stable=(reread==cb and reread_kept==raw_pb and reread_decisions==raw_db)
    need(stable,'live prefix changed during comparison')
    identical=(ia==ib and matching==len(ia) and not decision_mismatch and raw_pa==raw_pb)
    return {'status':'PASS' if identical else 'NOT_IDENTICAL','utc':datetime.now(timezone.utc).isoformat(),
            'input_prefix_rows':limit,'pilot_retained':len(pa),'live_prefix_retained':len(pb),
            'original_input_indices_identical':ia==ib,'original_input_indices_sha256':{'pilot':sha(json.dumps(ia).encode()),'live':sha(json.dumps(ib).encode())},
            'common_retained_records':len(common),'matching_retained_records':matching,'record_mismatch_input_indices_sample':record_mismatch,
            'decision_rows_equal':limit-len(decision_mismatch),'decision_mismatch_input_indices_sample':decision_mismatch[:20],
            'decision_mismatch_transitions':dict(transitions),'live_prefix_holdout_drops':sum(r['decision']=='holdout' for r in db),
            'provenance_prefix_equal':raw_pa==raw_pb,'prefix_stable_on_reread':stable,
            'compared_prefixes':{name:{'pilot_bytes':len(ca[name]),'pilot_sha256':sha(ca[name]),'live_bytes':len(cb[name]),'live_sha256':sha(cb[name]),'equal':ca[name]==cb[name]} for name in ca},
            'provenance_prefix_sha256':{'pilot':sha(raw_pa),'live':sha(raw_pb)},
            'decisions_prefix_sha256':{'pilot':sha(raw_da),'live':sha(raw_db)},
            'snapshots':{'pilot_summary_sha256':sha(pilot_bytes),'live_progress_sha256':sha(live_bytes),'live_status':b['status'],'live_input_rows':b['input_rows'],
                         'pilot_workers':a['config']['workers'],'live_workers':b['config']['workers'],'nodes':1024,
                         'pilot_probe_sha256':a['probe']['sha256'],'live_probe_sha256':b['probe']['sha256'],
                         'pilot_holdouts':a['config']['holdouts'],'live_holdouts':b['config']['holdouts']},
            'qualification':'Only these first input rows and corresponding retained column/FEN/provenance bytes were compared. Live output remains unsealed; no full-output or playing-strength claim.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot',type=Path,required=True);parser.add_argument('--live',type=Path,required=True)
    parser.add_argument('--rows',type=int,default=10000);args=parser.parse_args()
    need(args.rows>0,'rows must be positive')
    report=run(args.pilot,args.live,args.rows)
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
