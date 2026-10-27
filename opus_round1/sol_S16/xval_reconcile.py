"""Reconcile Sol's v3 filter (diagnostic run) with the overlap scanner on the cross-validation fixture.
Usage: python -I -B xval_reconcile.py <xval dir with sol_v3_stdout.json, sol_out/, scan_out/>   Exit 0 only if they agree."""
import collections,gzip,json,sys
X=sys.argv[1];ok=True
sol=json.load(open(X+'/sol_v3_stdout.json',encoding='utf-8'));scan=json.load(open(X+'/scan_out/forge_sol_S16_overlap_summary_20261027.json',encoding='utf-8'))
print('Sol v3 game policy:',{k:v for k,v in sol['game_policy'].items() if k in ('mode','groups','segments')},'| holdout unique',sol['holdout_unique_positions'],'| input_position_overlap',sol['input_position_overlap'])
for s in sol['shards']:print('  Sol ',s['stem'],'input',s['input'],'kept',s['kept'],'dropped',s['dropped'])
print('scanner holdout:',{k:scan['holdout'][k] for k in ('rows','unique_positions','duplicate_rows_within_holdout')})
for t in scan['train']:print('  scan',t['stem'],'rows',t['rows'],'overlap_rows',t['overlap_rows'],'distinct',t['distinct_holdout_positions_hit'],'label_conflicts',t['label_conflicts'])
for j in scan['games']['junctions']:print('  junction',j['before'],'->',j['after'],'new_game',j.get('new_game_at_junction'),'straddling_training_rows',j.get('straddling_training_rows'))
rows=[l.split(',') for l in gzip.open(X+'/scan_out/forge_sol_S16_removal_list_20261027.csv.gz','rt',encoding='utf-8').read().splitlines()[1:]]
pos={(r[0],r[1]) for r in rows if r[2]=='holdout_position'};grp={(r[0],r[1]) for r in rows if r[2]=='holdout_game_group'}
led=[json.loads(l) for l in open(X+'/sol_out/forge_sol_S16_removals_20261026.jsonl',encoding='utf-8')]
spos={(d['stem'],str(d['row'])) for d in led if d['reason']=='holdout_position'};sgrp={(d['stem'],str(d['row'])) for d in led if d['reason']=='holdout_game_group'}
checks=[('holdout unique positions equal',sol['holdout_unique_positions']==scan['holdout']['unique_positions']),
        ('holdout_position row set equal (Sol checks game group first)',spos==pos-grp),
        ('holdout_game_group row set equal',sgrp==grp),
        ('input_position_overlap == scanner overlap rows',sol['input_position_overlap']==scan['train_totals']['overlap_rows'])]
for name,good in checks:print(('PASS ' if good else 'FAIL ')+name);ok&=good
print('Sol counts duplicate_position (training-internal duplicates):',sum(s['dropped'].get('duplicate_position',0) for s in sol['shards']),'(not in the scanner\'s scope)')
print('RECONCILED' if ok else 'MISMATCH');sys.exit(0 if ok else 1)
