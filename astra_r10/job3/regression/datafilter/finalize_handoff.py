"""Seal new handoff artifacts after completed audits. Never runs training."""
import argparse
import itertools
import json
import math
from pathlib import Path
import shutil
from filter_positions import low_priority,sha256,storage_guard
from npt_adapter import runtime_identity
import train  # Include actual imported trainer modules in identity, without calling main.
from verify_handoff import verify

HERE=Path(__file__).resolve().parent

def finalize(root):
    output=root/'handoff'; output.mkdir()
    cleared=json.loads((root/'holdout_cleared/clearance.json').read_text())
    audit=json.loads((root/'independent_audit/audit.json').read_text())
    if cleared['status']!='PASS': raise ValueError('clearance required')
    source=root/'holdout_cleared/records.jsonl'
    sample=output/'sample.jsonl'
    n=sx=sy=sxx=syy=sxy=0; sample_count=0; rows=0
    with open(source,encoding='utf-8') as fh, open(sample,'x',encoding='utf-8',newline='\n') as out:
        for line in fh:
            r=json.loads(line);rows+=1
            if rows<=10000:out.write(line);sample_count+=1
            if r['has_result']:
                x=r['score_stm'];y=r['result_stm'];n+=1;sx+=x;sy+=y;sxx+=x*x;syy+=y*y;sxy+=x*y
    if rows!=cleared['selection']['kept']:raise ValueError('selection count mismatch')
    corr=(n*sxy-sx*sy)/math.sqrt((n*sxx-sx*sx)*(n*syy-sy*sy))
    def payload(p,count):return dict(path=str(p.resolve()),sha256=sha256(p),rows=count)
    val=root/'independent_audit/validation013.jsonl'
    with open(val,'rb') as fh: val_count=sum(1 for _ in fh)
    runtime=runtime_identity()
    manifest=dict(schema=1,strength='UNPROVEN',training_ready=corr>0.1,
                  train=payload(source,rows),metadata=payload(root/'holdout_cleared/metadata.jsonl',rows),
                  validation=payload(val,val_count),sample=payload(sample,sample_count),
                  cohort=json.loads((root/'cohort/manifest.json').read_text()),
                  holdouts=audit['holdouts'],clearance=dict(path=str((root/'holdout_cleared/clearance.json').resolve()),sha256=sha256(root/'holdout_cleared/clearance.json')),
                  pearson_stm_score_result=corr,known_result_count=n,
                  source_proportions={'selfplay':1.0,'lichess':0.0},
                  filters=['drop_in_check','drop_mate_scores'],split='explicit complete 013/014 board+STM exclusion',
                  runtime=runtime,
                  baseline_wrapper={'path':'F:/forge_nnue_train/tools/train_resid_nnuepytorch_v2.py','sha256':sha256('F:/forge_nnue_train/tools/train_resid_nnuepytorch_v2.py')},
                  recipes={'filtered_eval_v1':{'selfplay_known_lambda':1.0,'other_lambda':1.0},'filtered_wdl_v1':{'selfplay_known_lambda':0.8,'other_lambda':1.0}},
                  hyperparameters={'features':'K32H3^','L1':1024,'batch_size':16384,'epoch_size':152500000,'epochs':8,'lr':0.000875,'gamma':0.72,'seed':5108})
    with open(output/'manifest.json','x',encoding='utf-8') as fh:json.dump(manifest,fh,indent=2)
    checked=verify(output/'manifest.json')
    with open(output/'verification.json','x') as fh:json.dump(checked,fh,indent=2)
    hashes={}
    for directory in ('cohort','old','new','result','legacy_logs','filtered_a','filtered_b','filtered_default','independent_audit','holdout_cleared','handoff'):
        for p in sorted((root/directory).glob('*')):
            if p.is_file():hashes[str(p.relative_to(root))]=dict(bytes=p.stat().st_size,sha256=sha256(p))
    with open(output/'full_output_hashes.json','x') as fh:json.dump(hashes,fh,indent=2)
    # Reviewable repository copies, each new; full data remains at the authorized root.
    (HERE/'sample').mkdir(exist_ok=True)
    for src,dst in [(sample,HERE/'sample/positions.jsonl'),
                    (output/'manifest.json',HERE/'evidence/handoff_manifest.json'),
                    (output/'verification.json',HERE/'evidence/handoff_verification.json'),
                    (output/'full_output_hashes.json',HERE/'evidence/full_output_hashes.json'),
                    (root/'holdout_cleared/clearance.json',HERE/'evidence/holdout_clearance.json'),
                    (root/'independent_audit/audit.json',HERE/'evidence/original_holdout_audit.json'),
                    (root/'cohort/manifest.json',HERE/'evidence/cohort_manifest.json')]:
        if dst.exists():raise FileExistsError(dst)
        shutil.copyfile(src,dst)
    with open(HERE/'evidence/npt_runtime.json','x') as fh:json.dump(runtime,fh,indent=2)
    return checked

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    low_priority();storage_guard(allowance=100*10**6);print(json.dumps(finalize(a.root),indent=2))
