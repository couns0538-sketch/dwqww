"""Merge the two completed original S33 shards; no simulations or engine runs."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math

import forge_sol_S33_sprt_planner_20261026 as planner
from forge_sol_S48_gate_guard_20261026 import comparability, simulate_gate_bias


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--grid',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists()
    groups={};sources={}
    for shard in (0,1):
        root=a.grid/f'shard{shard}'
        p=root/f'forge_sol_S33_shard_{shard}_completion_20261026.json'
        done=json.loads(p.read_text());assert done['status']=='PASS' and done['cells']==315 and done['sources_unchanged']
        sources[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
        for row in done['groups']:
            rel=Path(row['path']);assert rel.name==str(rel) and '..' not in rel.parts
            p=root/rel;assert sha(p)==row['sha256'];r=json.loads(p.read_text())
            i=r['group_index'];assert i%2==shard and i not in groups and row['group_index']==i
            raw=root/r['raw_terminal']['path'];assert raw.parent==root and sha(raw)==r['raw_terminal']['sha256']
            assert raw.stat().st_size==r['raw_terminal']['bytes'] and r['raw_terminal']['replicates']==20000
            assert len(r['results'])==7 and r['status']=='COMPLETE';groups[i]=r
            sources[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
            sources[str(raw)]={'sha256':sha(raw),'bytes':raw.stat().st_size}
    assert set(groups)==set(range(90))
    expected=[(name,-5+2.5*i) for name in planner.PROFILES for i in range(15)]
    fields=['profile','concurrency','true_logistic_elo','protocol','e0_nelo','e1_nelo','cap_games',
            'runs','seed','mc_H1','mc_H0','mc_cap','analytic_H1','analytic_H0','analytic_cap',
            'mc_mean_games','mc_median_games','analytic_mean_games','analytic_median_games']
    flat=[]
    for index in range(90):
        g=groups[index];assert (g['profile'],g['true_logistic_elo'])==expected[index]
        assert g['seed']==20261026330000+index
        for protocol,row in zip(planner.PROTOCOLS,g['results']):
            mc=row['mc'];an=row['analytic'];assert row['protocol']==protocol and mc['runs']==20000
            assert mc['hypothesis_units']=='nelo' and mc['seed']==g['seed']
            assert abs(sum(mc['probabilities'].values())-1)<1e-12
            assert abs(sum(an['probabilities'].values())-1)<1e-12
            assert mc['observed_gates_pooled'] is False
            flat.append({'profile':g['profile'],'concurrency':row['concurrency'],
                'true_logistic_elo':g['true_logistic_elo'],'protocol':protocol['name'],
                'e0_nelo':protocol['e0'],'e1_nelo':protocol['e1'],'cap_games':protocol['cap_games'],
                'runs':20000,'seed':g['seed'],**{'mc_'+k:mc['probabilities'][k] for k in ('H1','H0','cap')},
                **{'analytic_'+k:an['probabilities'][k] for k in ('H1','H0','cap')},
                'mc_mean_games':mc['mean_games'],'mc_median_games':mc['median_games'],
                'analytic_mean_games':an['mean_games'],'analytic_median_games':an['median_games']})
    assert len(flat)==630
    a.out.mkdir(exist_ok=False)
    csvpath=a.out/'forge_sol_S33_sprt_plan_table_20261026.csv'
    with csvpath.open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(flat)
    md=['# S33 full advisory plan table — 2026-10-26','',
        'Modeled trials only, not played games. True Elo is logistic; hypotheses are nElo. No observed gates or concurrency groups pooled. Each cell has 20,000 trials.','',
        '|Profile|Conc|True Elo|Protocol|P(H1)|P(H0)|P(cap)|Mean games|Median games|',
        '|---|---|---:|---|---:|---:|---:|---:|---:|']
    for row in flat:
        md.append('|{profile}|{concurrency}|{true_logistic_elo:g}|{protocol}|{mc_H1:.5f}|{mc_H0:.5f}|{mc_cap:.5f}|{mc_mean_games:.2f}|{mc_median_games:.0f}|'.format(**{**row,'concurrency':row['concurrency'] if row['concurrency'] else 'model'}))
    (a.out/'forge_sol_S33_sprt_plan_table_20261026.md').write_text('\n'.join(md)+'\n')
    s48={'status':'MODELED_DIAGNOSTICS_WITH_REAL_DATA_GAPS','assumed_true_logistic_elo':10,
         'true10_H1_demonstration':groups[36]['results'][0]['selection_bias']['H1'],
         'gate_rows':[],'acceptance_authorized':False,
         'comparability_G120_G104':comparability({'gate':'G120','concurrency':7,'tc':'10+0.1'},
                                                {'gate':'G104','concurrency':5,'tc':'10+0.1'})}
    for gate,index,observed,error in [('G100r',21,10.89,8.38),('G119',36,9.50,8.84)]:
        g=groups[index];b=g['results'][0]['selection_bias']['cap'];assert b['status']=='MODELED_DIAGNOSTIC'
        adjusted=observed-b['bias_estimate'];ci=b['bias_mc_ci95']
        s48['gate_rows'].append({'gate':gate,'concurrency':5,'selection':'cap','observed_elo':observed,
            'reported_original_error95':error,'conditional_bias':b,
            'adjusted_elo_assuming_true10_model':adjusted,
            'adjusted_elo_mc_ci95':[observed-ci[1],observed-ci[0]],
            'corrected_observation_ci95':None,'source_group':index,'seed':g['seed'],
            'interpretation':'Sensitivity under assumed true+10 and supplied pair-profile shape; MC interval is not observational or sequential coverage.'})
    for gate,concurrency,elo in [('G104',5,29.44),('G120',7,23.62)]:
        s48['gate_rows'].append({**simulate_gate_bias({'gate':gate,'concurrency':concurrency,'observed_elo':elo},profile=None),
                                'concurrency':concurrency,'reported_observed_elo':elo})
    demo=s48['true10_H1_demonstration'];assert demo['conditional_mean_elo']>10 and demo['bias_estimate']>0
    assert s48['comparability_G120_G104']['can_compare'] is False
    write_json(a.out/'forge_sol_S48_bias_and_comparability_20261026.json',s48)
    summary={'status':'PASS','groups':90,'cells':630,'replicates_per_cell':20000,
             'cell_replications_total':12600000,'unique_modeled_paths':1800000,
             'paths_shared_between_protocols':True,'new_engine_games':0,
             'source_files':sources,'csv_sha256':sha(csvpath),'acceptance_authorized':False,
             'interpretation':'12.6million cell evaluations on1.8million modeled paths, not12.6million independent paths and not matches.'}
    write_json(a.out/'forge_sol_S33_full_grid_merge_receipt_20261026.json',summary)
    print(json.dumps({'status':'PASS','cells':630,'unique_paths':1800000,
        'true10_H1_mean':demo['conditional_mean_elo'],'true10_H1_bias':demo['bias_estimate'],
        'capped_gate_sensitivity':[(x['gate'],x.get('adjusted_elo_assuming_true10_model')) for x in s48['gate_rows']]}))


if __name__=='__main__':main()
