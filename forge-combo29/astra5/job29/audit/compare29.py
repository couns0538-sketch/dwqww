"""Compare independently replayed cutoffs, outcomes, and threshold timing with the second reader."""
from pathlib import Path
import csv,json,sys
def tab(p):
    with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
root=Path(sys.argv[1]);other=Path(sys.argv[2]);ours=json.loads((root/'independent.json').read_text());theirs=json.loads((other/'status.json').read_text())
assert ours['common_complete_blocks']==theirs['common_complete_blocks'],(ours['common_complete_blocks'],theirs['common_complete_blocks'])
candidates=tab(root/'thresholds.tsv');gold=tab(other/'summary.tsv');index={(r['match'],r['side'],r['threshold_cp']):r for r in gold}
n=0
for r in candidates:
    if r['games']=='0':continue
    ref=index[r['match'],r['side'],r['threshold']]
    assert [int(r[k]) for k in ['reached','wins','draws','losses']]==[int(ref[k]) for k in ['games_reached','won','drew','lost']],(r,ref)
    if int(r['reached']):assert abs(float(r['mean_remaining_plies'])-float(ref['mean_plies_remaining']))<1e-9,(r,ref)
    n+=1
assert n==len(index),(n,len(index))
print(f'All {n} match/side/threshold rows agree on crossings, W/D/L and remaining-ply means across {len(ours["common_complete_blocks"])} common blocks.')
def near(x,y):return abs(float(x)-float(y))<1e-8
for r in tab(other/'match-check.tsv'):
    a=ours['arms'][r['match']];assert a['games']==int(r['games']) and a['pairs']==int(r['pairs'])
    assert a['A_WLD']==[int(r[k]) for k in ('A_wins','A_losses','A_draws')] and a['penta']==[int(r[k]) for k in ('p0','p05','p1','p15','p2')]
    assert all(near(x,r[k]) for x,k in zip(a['elo_lower_upper'],('elo','ci_low','ci_high')))
    assert a['reading']==r['reading'] and near(a['mean_plies'],r['mean_plies']) and near(a['nodes_ratio'],r['A_to_B_spend'])
for r in tab(other/'search-check.tsv'):
    a=ours['arms'][r['match']]['players'][r['side']]
    for prop,k in [('searches','searches'),('n_total','sum_n'),('spent_total','sum_spent'),('depth_reported','scored_searches'),('no_score','no_score'),('depth_total','sum_depth')]:
        assert a[prop]==int(r[k]),(r,prop,a[prop])
    for prop,k in [('mean_n','mean_n'),('mean_spent','mean_spent'),('mean_depth','mean_scored_depth')]:assert near(a[prop],r[k]),(r,prop,a[prop])
    if a['hardcap'] is not None:
        assert a['hardcap']==int(r['soft_cap_hits']) and near(a['hardcap_share'],r['soft_cap_share'])
endings={}
for r in tab(other/'endings-check.tsv'):endings.setdefault(r['match'],{})[r['ending']]=int(r['games'])
assert all(endings[k]==s['endings'] for k,s in ours['arms'].items() if s['games'])
print(f"All per-arm scores, pair histograms, limits, endings, depth/spend/scoreless/hardcap counts, means, ratios and readings agreed on the same scope.")
