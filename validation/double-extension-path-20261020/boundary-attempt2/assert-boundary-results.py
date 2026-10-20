#!/usr/bin/env python3
"""Unchanged actual path-budget assertion for baseline and proposal captures."""
from pathlib import Path
import argparse
import json

parser=argparse.ArgumentParser()
parser.add_argument('--commands',type=Path,required=True)
parser.add_argument('--variant',choices=['baseline','proposal'],required=True)
a=parser.parse_args()
x=json.loads(a.commands.read_text())
assert len(x['cases'])==6 and x['runtime_used_seconds']<=60
assert len([s for s in x['steps'] if '-seed' in s['label']])==6
assert all(s['exit_code']==0 for s in x['steps'])
keys=['same_ply_changed','single_parent_mismatch','eligibility_mismatch',
      'actual_vs_true_path_mismatch','null_parent_path_mismatch',
      'probcut_parent_path_mismatch','incoming_parent_path_mismatch',
      'true_path_limit_breaches']
failures={}
for seed in [0,6,7]:
    r=x['cases'][f'{a.variant}-seed{seed}'];t=r['summary_totals']
    assert t['children']>0 and t['singular_attempts']>0
    assert r['seed']==seed and r['engine_exit_code']==0
    issues={key:t[key] for key in keys if t[key]}
    if r['max_true_path']>7:issues['max_true_path']=r['max_true_path']
    if r['max_actual_path']>7:issues['max_actual_path']=r['max_actual_path']
    if seed==6 and t['double_extensions']==0:issues['no_count6_double_extension_exercised']=True
    if seed==7 and t['double_extensions']!=0:issues['count7_double_extension']=t['double_extensions']
    if issues:failures[str(seed)]=issues
print(json.dumps({'status':'FAIL' if failures else 'PASS','variant':a.variant,'failures':failures,
                  'scope':'Synthetic inherited-state budget and bookkeeping only; no normal-root overflow or strength inference.'}))
raise SystemExit(1 if failures else 0)
