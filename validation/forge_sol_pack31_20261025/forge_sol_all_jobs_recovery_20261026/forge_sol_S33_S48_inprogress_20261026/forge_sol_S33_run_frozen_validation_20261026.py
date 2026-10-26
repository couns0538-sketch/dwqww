"""Run the six frozen cells once, retaining terminal samples and full summaries."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import numpy as np

BASE = Path(__file__).resolve().parent
EXPECTED = 'b04af9f74b0ffc7cb9b9e58a04ac4cf02efff43e4d801991dfc11324a2e2f194'


def main():
    product = BASE / 'forge_sol_S33_sprt_planner_20261026.py'
    actual = hashlib.sha256(product.read_bytes()).hexdigest()
    if actual != EXPECTED:
        raise RuntimeError('frozen source hash mismatch')
    spec = importlib.util.spec_from_file_location('s33',product)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    started = time.time()
    manifest = {'source_sha256':actual,'seed':m.VALIDATION_SEED,'runs_per_cell':20000,
                'argv':sys.argv,'pid':os.getpid(),'cpu_affinity':sorted(os.sched_getaffinity(0)),
                'command':'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 3 python -B forge_sol_S33_run_frozen_validation_20261026.py',
                'outcome_encoding':{'H0':-1,'cap':0,'H1':1},'started_unix':started,
                'criterion':'all six fixed cells max absolute H1/H0/cap difference <=0.03; retain failures'}
    path = BASE / 'forge_sol_S33_validation_execution_20261026.json'
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    rows = []
    for i,cell in enumerate(m.VALIDATION_CELLS):
        profile = m.named_profile(cell['profile'],cell['true_elo'])
        protocol = next(p for p in m.PROTOCOLS if p['name']==cell['protocol'])
        kwargs = {k:protocol[k] for k in ('e0','e1','cap_games')}
        mc = m.simulate_cell(profile,cell['true_elo'],runs=20000,seed=m.VALIDATION_SEED+i,
                             return_samples=True,**kwargs)
        samples = mc.pop('samples')
        encoded = np.where(samples['outcome']=='H1',1,np.where(samples['outcome']=='H0',-1,0)).astype(np.int8)
        mc['outcome_counts'] = {k:int(np.sum(samples['outcome']==k)) for k in ('H1','H0','cap')}
        np.savez_compressed(BASE / ('forge_sol_S33_validation_'+cell['id']+'_terminal_20261026.npz'),
                            outcome=encoded,games=samples['games'].astype(np.uint16),
                            terminal_elo=samples['terminal_elo'])
        analytic = m.analytic_cell(profile,cell['true_elo'],**kwargs)
        raw = {**cell,'source_sha256':actual,'mc':mc,'analytic':analytic}
        (BASE / ('forge_sol_S33_validation_'+cell['id']+'_raw_20261026.json')).write_text(json.dumps(raw,indent=2,allow_nan=False)+'\n')
        rows.append({**cell,'runs':20000,'seed':m.VALIDATION_SEED+i,
                     'mc':mc['probabilities'],'analytic':analytic['probabilities'],
                     'mc_counts':mc['outcome_counts'],'mc_wilson95':mc['probability_wilson95'],
                     'mc_mean_games':mc['mean_games'],'analytic_mean_games':analytic['mean_games'],
                     'mc_median_games':mc['median_games'],'analytic_median_games':analytic['median_games']})
        print(json.dumps({'completed':cell['id'],'elapsed_seconds':time.time()-started,
                          'mc_counts':mc['outcome_counts']}),flush=True)
    result = m.compare_validation(rows)
    result['source_sha256'] = actual
    (BASE / 'forge_sol_S33_six_cell_validation_20261026.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    manifest.update({'return_code':0,'validation_status':result['status'],'elapsed_seconds':time.time()-started})
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'failed_cells':result['failed_cells'],
                      'elapsed_seconds':time.time()-started}),flush=True)


if __name__=='__main__':
    try:
        main()
    except BaseException as exc:
        path = BASE / 'forge_sol_S33_validation_execution_20261026.json'
        manifest = json.loads(path.read_text()) if path.exists() else {}
        manifest.update({'return_code':1,'exception':repr(exc)})
        path.write_text(json.dumps(manifest,indent=2)+'\n')
        raise
