"""Independent counts/duplicate-digest/mate-ledger readback; no QC parser imports."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import struct
from run_policy import Inputs, free_guard, safe_path, write_json

def audit(qc_directory,output):
    qc=safe_path(qc_directory)
    inputs=Inputs()
    expected=inputs.json(qc/'statistics.json')
    pins={row['path'].casefold():row for row in inputs.json(qc/'INPUTS.json')}
    expected_flags={}
    expected_original={}
    expected_locations={}
    results={}
    def source(path):
        path=safe_path(path)
        pin=pins[str(path).casefold()]
        return inputs.verify(path,pin['sha256'])
    for cohort in ('r14b','old440k'):
        n=total=white_total=mates=delta=nonmate_sum=nonmate_white=0
        turns,wdl=Counter(),Counter()
        fingerprints=set()
        def add(row_id,fen,score,result,old_score,split,original,input_path,input_line):
            nonlocal n,total,white_total,mates,delta,nonmate_sum,nonmate_white
            if n%4096==0:
                free_guard(1024*1024)
            fen=' '.join(fen.split())
            turn=fen.split()[1]
            n+=1
            total+=score
            white_total+=score if turn=='w' else -score
            delta+=abs(score-old_score)
            turns[turn]+=1
            wdl[{0:'loss',0.5:'draw',1:'win'}[result]]+=1
            fingerprints.add(hashlib.sha256(fen.encode('ascii')).digest())
            if abs(score)>=30000:
                mates+=1
                expected_flags[(cohort,row_id)]=(fen,score,result,old_score,split)
                expected_original[(cohort,row_id)]=dict(original)
                expected_locations[(cohort,row_id)]=(str(input_path),input_line)
            else:
                nonmate_sum+=score
                nonmate_white+=score if turn=='w' else -score
        if cohort=='r14b':
            path=Path('D:/o14b/r2/proof/jobA/final/labels.tsv')
            for row in csv.DictReader(source(path).lines(),delimiter='\t'):
                add(int(row['row_id']),row['fen'],int(row['score_stm']),float(row['result']),int(row['old_score_stm']),row['split'],row,path,int(row['row_id'])+2)
        else:
            job=Path('C:/o13/p5/job1')
            for entry in csv.DictReader(source(job/'shards.tsv').lines(),delimiter='\t'):
                shard=job/'shards'/entry['dir']
                stem=f"relabel_{int(entry['shard']):05}"
                raw=source(shard/(stem+'.pos')).bytes()
                magic,version,count=struct.unpack_from('<4sIQ',raw)
                if magic!=b'FPOS' or version!=1 or len(raw)!=16+35*count:
                    raise ValueError('independent FPOS header/length rejection')
                fens=iter(source(shard/(stem+'.fen')).lines())
                labels=iter(source(shard/'labels.jsonl').lines())
                for local in range(count):
                    fen=next(fens).strip()
                    label=json.loads(next(labels))
                    score=struct.unpack_from('<h',raw,16+count*32+local*2)[0]
                    metadata=raw[16+count*34+local]
                    add(int(label['input_index']),fen,score,(metadata>>1)/2,int(label['old_score_stm']),'unspecified',label,shard/'labels.jsonl',local+1)
                if next(fens,None) is not None or next(labels,None) is not None:
                    raise ValueError('independent sidecar count rejection')
        profile=expected['profiles'][cohort]
        result=dict(rows=n,score_stm_sum=total,score_white_sum=white_total,mate_rows=mates,side_to_move=dict(turns),wdl_white=dict(wdl),
                    unique_fen_sha256=len(fingerprints),duplicate_rows=n-len(fingerprints),paired_absolute_delta=delta)
        checks=[n==profile['rows'],total==profile['score_stm']['sum'],white_total==profile['score_white']['sum'],
                mates==profile['mate_rows'],dict(turns)==profile['side_to_move'],dict(wdl)==profile['wdl_white'],
                n-len(fingerprints)==expected['duplicates'][cohort]['duplicate_rows'],
                math.isclose(delta/n,profile['paired_old_score']['mean_absolute_delta'],rel_tol=1e-12)]
        if not all(checks):
            raise ValueError(f'independent report mismatch: {cohort}: {checks}')
        if cohort+':non_mate' in expected['profiles']:
            clean=expected['profiles'][cohort+':non_mate']
            if (clean['rows'],clean['score_stm']['sum'],clean['score_white']['sum'])!=(n-mates,nonmate_sum,nonmate_white):
                raise ValueError('independent non-mate profile mismatch')
        results[cohort]=result
    actual=set()
    for line in inputs.get(qc/'mate_rows.jsonl').lines():
        row=json.loads(line)
        key=(row['cohort'],row['row_id'])
        value=(row['fen'],row['score_stm'],row['result'],row['old_score_stm'],row['split'])
        if key in actual or key not in expected_flags or value!=expected_flags[key] or abs(row['score_stm'])<30000:
            raise ValueError('mate ledger differs from original rows')
        if expected.get('mate_ledger_schema',1)>=2 and row.get('original_label')!=expected_original[key]:
            raise ValueError('mate ledger producer object changed or missing')
        if expected.get('mate_ledger_schema',1)>=2 and (row.get('input_path'),row.get('input_line'))!=expected_locations[key]:
            raise ValueError('mate ledger source location changed or missing')
        actual.add(key)
    if actual!=set(expected_flags):
        raise ValueError('mate ledger incomplete')
    write_json(output,dict(status='PASS',method='Separate CSV/FPOS counter and SHA256-FEN sets; no qc_core/p5_qc imports',cohorts=results,
                           mate_ledger_rows=len(actual),game_separation='UNVERIFIED',inputs=inputs.receipts()))
    print(json.dumps(dict(status='PASS',mate_ledger_rows=len(actual),cohorts=results)),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qc',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    args=parser.parse_args()
    audit(args.qc,args.output)
