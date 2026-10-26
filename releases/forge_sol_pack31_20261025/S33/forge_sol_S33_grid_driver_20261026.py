"""Original reproducible S33 full-grid worker. ADVICE only; no engine execution.

Two shards use independent logical-group seeds; every original terminal sample
is retained as deterministic gzip JSONL. One completed pair is the decision unit.
"""
from pathlib import Path
import argparse
import datetime
import gzip
import hashlib
import json
import math
import os
import sys
import time

import numpy as np
import forge_sol_S33_sprt_planner_20261026 as planner
from forge_sol_S48_gate_guard_20261026 import selection_bias

DATE='20261026'
PLANNER_SHA='008819d5387cdd5ac5d512bb2ebafd09f141aafc9b6904cba2f73a8373634d03'
S48_SHA='21713b327007b0cda450200e172f6affb27cd65ac10e26ed8680d9447669d855'
BASE_SEED=20261026330000


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--shard',type=int,choices=(0,1),required=True)
    p.add_argument('--cpu',type=int,choices=(3,4),required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();root=Path(__file__).resolve().parent
    assert not a.out.exists() and not a.out.is_symlink(),'NEW output directory required'
    sources={'forge_sol_S33_sprt_planner_20261026.py':PLANNER_SHA,
             'forge_sol_S48_gate_guard_20261026.py':S48_SHA}
    assert all(sha(root/name)==digest for name,digest in sources.items()),'frozen product changed'
    validation=json.loads((root/'forge_sol_S33_six_cell_validation_20261026.json').read_text())
    equivalence=json.loads((root/'forge_sol_S33_numerical_ast_equivalence_20261026.json').read_text())
    assert validation['status']=='PASS' and len(validation['cells'])==6 and not validation['failed_cells']
    assert all(x['runs']>=20000 and x['status']=='PASS' for x in validation['cells'])
    assert validation['source_sha256']==equivalence['old_source_sha256']
    assert equivalence['new_source_sha256']==PLANNER_SHA and equivalence['retained_AST_identical']
    assert {a.cpu}<=os.sched_getaffinity(0)
    os.sched_setaffinity(0,{a.cpu})
    a.out.mkdir(exist_ok=False)
    groups=[(name,-5+2.5*i) for name in planner.PROFILES for i in range(15)]
    selected=[(i,*g) for i,g in enumerate(groups) if i%2==a.shard]
    protocol={'schema':'forge_sol_S33_full_grid_worker_v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'shard':a.shard,'cpu_affinity':sorted(os.sched_getaffinity(0)),
        'argv':sys.argv,'source_hashes':sources,'driver_sha256':sha(Path(__file__)),
        'runs_per_cell':20000,'block_size':128,'base_seed':BASE_SEED,
        'seed_rule':'BASE_SEED + logical group index; independent of scheduling and shard order',
        'groups':[{'index':i,'profile':name,'true_logistic_elo':elo} for i,name,elo in selected],
        'protocols':planner.PROTOCOLS,'common_random_numbers':'within a profile/true-Elo group only; no observed gates pooled',
        'validation_source':validation['source_sha256'],'numerical_equivalence_to_current':equivalence['canonical_retained_AST_sha256'],
        'numpy_version':np.__version__,'python_version':sys.version,'acceptance_authorized':False}
    save(a.out/f'forge_sol_S33_shard_{a.shard}_protocol_{DATE}.json',protocol)
    started=time.monotonic();complete=[]
    for group_index,name,elo in selected:
        begin=time.monotonic();definition=planner.PROFILES[name]
        profile=definition['counts'] if 'counts' in definition else planner.draw_profile(definition['draw_ratio'],elo)
        mc=planner.simulate_protocols(profile,elo,planner.PROTOCOLS,runs=20000,
            seed=BASE_SEED+group_index,block_size=128,return_samples=True)
        arrays=[row.pop('samples') for row in mc]
        rawpath=a.out/f'forge_sol_S33_group_{group_index:03d}_terminal_{DATE}.jsonl.gz'
        with rawpath.open('xb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0,compresslevel=6) as z:
                z.write((json.dumps({'schema':'forge_sol_S33_terminal_arrays_v1','group':group_index,
                    'protocols':[x['name'] for x in planner.PROTOCOLS],'nonfinite_encoding':'null with signed nonfinite_elo list; zero=finite'},separators=(',',':'))+'\n').encode())
                for j in range(20000):
                    values=[float(x['terminal_elo'][j]) for x in arrays]
                    row={'replicate':j,'games':[int(x['games'][j]) for x in arrays],
                         'outcome':[str(x['outcome'][j]) for x in arrays],
                         'terminal_elo':[x if math.isfinite(x) else None for x in values],
                         'nonfinite_elo':[0 if math.isfinite(x) else (1 if x>0 else -1) for x in values]}
                    z.write((json.dumps(row,separators=(',',':'),allow_nan=False)+'\n').encode())
        results=[]
        for spec,summary,samples in zip(planner.PROTOCOLS,mc,arrays):
            analytic=planner.analytic_cell(profile,elo,e0=spec['e0'],e1=spec['e1'],cap_games=spec['cap_games'])
            assert summary['runs']==20000
            assert sum(int(round(v*20000)) for v in summary['probabilities'].values())==20000
            results.append({'profile':name,'concurrency':definition['concurrency'],
                'profile_kind':definition['kind'],'true_logistic_elo':elo,'protocol':spec,
                'mc':summary,'analytic':analytic,
                'selection_bias':{label:selection_bias(samples,elo,outcome=label) for label in ('H1','H0','cap')}})
        entry={'status':'COMPLETE','group_index':group_index,'profile':name,'true_logistic_elo':elo,
            'seed':BASE_SEED+group_index,'source_hashes':sources,'results':results,
            'raw_terminal':{'path':rawpath.name,'sha256':sha(rawpath),'bytes':rawpath.stat().st_size,'replicates':20000},
            'elapsed_seconds':time.monotonic()-begin,'acceptance_authorized':False}
        path=a.out/f'forge_sol_S33_group_{group_index:03d}_results_{DATE}.json';save(path,entry)
        complete.append({'group_index':group_index,'path':path.name,'sha256':sha(path)})
        print(json.dumps({'shard':a.shard,'completed_groups':len(complete),'total_groups':len(selected),
                          'group_index':group_index,'profile':name,'true_elo':elo,'elapsed':time.monotonic()-started}),flush=True)
    assert len(complete)==45 and all(sha(root/name)==digest for name,digest in sources.items())
    save(a.out/f'forge_sol_S33_shard_{a.shard}_completion_{DATE}.json',
         {'status':'PASS','groups':complete,'cells':len(complete)*7,'runs_per_cell':20000,
          'elapsed_seconds':time.monotonic()-started,'sources_unchanged':True,'acceptance_authorized':False})
    print('PASS: 315 advisory cells completed; no engine games',flush=True)


if __name__=='__main__':main()
