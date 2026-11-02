"""Bounded reruns for the R8 follow-up; no training. UNPROVEN."""
import argparse
import json
from pathlib import Path
import shutil
import time

from audit import legacy
from audit_stm_roundtrip import run as roundtrip
from filter_positions import low_priority, run_filter, sha256
from resource_policy import storage_guard

OLD = Path('D:/grok-pc-data/dwqww/astra8_data')


def run(stage, root):
    root=Path(root)
    storage_guard(root)
    if stage == 'identity':
        output=root/'identity'
        storage_guard(output,allowance=100*10**6)
        output.mkdir(); (output/'cohort').mkdir()
        source=OLD/'cohort/legacy100k.txt'
        expected=json.loads((OLD/'cohort/manifest.json').read_text())['hashes']['legacy100k.txt']
        if sha256(source)!=expected: raise ValueError('legacy input changed')
        shutil.copyfile(source,output/'cohort/legacy100k.txt')
        if sha256(output/'cohort/legacy100k.txt')!=expected: raise ValueError('copy mismatch')
        report=legacy(output)
    elif stage == 'orientation':
        report=roundtrip(root/'orientation_roundtrip')
    elif stage == 'million':
        source=OLD/'cohort/million.jsonl'
        expected=json.loads((OLD/'cohort/manifest.json').read_text())['hashes']['million.jsonl']
        if sha256(source)!=expected: raise ValueError('million input changed')
        output=root/'million'; output.mkdir()
        report={}
        cases=[('all_off',{}),('check',{'drop_in_check':True}),
               ('mate',{'drop_mate_scores':True}),('ply160',{'max_ply_from_start':160}),
               ('recipe_a',{'drop_in_check':True,'drop_mate_scores':True}),
               ('recipe_b',{'drop_in_check':True,'drop_mate_scores':True})]
        for name,options in cases:
            print('START '+name,flush=True)
            report[name]=run_filter(source,output/name,workers=2,**options)
            assert report[name]['input']==1_000_000
            print('DONE '+name+' '+json.dumps(report[name]),flush=True)
        assert report['all_off']['kept']==1_000_000
        assert report['all_off']['hashes']['records.jsonl']==expected
        assert report['recipe_a']['hashes']==report['recipe_b']['hashes']
        if sha256(source)!=expected: raise ValueError('million source changed during audit')
        report['source_sha256']=expected
        report['capture']='BLOCKED on this cohort: no stored best moves'
        report['qsearch']='BLOCKED: exact FD3A5190 lacks oracle'
        report['status']='PASS for measured rules only'
    else:
        raise ValueError(stage)
    destination=root/(stage+'_receipt.json')
    storage_guard(destination)
    with destination.open('x',encoding='utf-8') as fh:json.dump(report,fh,indent=2)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['identity','orientation','million'])
    p.add_argument('output',type=Path);a=p.parse_args();low_priority()
    print(json.dumps(run(a.stage,a.output),indent=2))
