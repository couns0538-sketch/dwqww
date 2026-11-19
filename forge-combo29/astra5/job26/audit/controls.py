"""Compare control signatures by opening and game identity, independently of execution order."""
import argparse
from collections import Counter
import csv
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path


def tab(path):
    with path.open() as f:return list(csv.DictReader(f,delimiter='\t'))


def extract(root, stage):
    folder=root/stage
    assert len(tab(folder/'pairs.tsv'))==10
    launches=tab(folder/'launch.tsv')
    expected=list(range(1,11)) if stage!='K26-2' else list(range(10,0,-1))
    assert [int(r['game']) for r in launches]==[i for k in expected for i in (2*k-1,2*k)]
    games={}; pids=set(); intervals=[]
    for rec in tab(folder/'games.tsv'):
        i=int(rec['game']);k=int(rec['opening']);assert k==(i+1)//2
        sub=folder/f'g{i:04d}'
        rows=tab(sub/'searches.tsv')
        assert i not in games
        games[i]=([r['bestmove'] for r in rows],[int(r['N']) for r in rows],
                   [int(r['used']) for r in rows],(rec['result'],rec['ending'],rec['plies'],rec['wclock'],rec['bclock']))
        intervals.append((datetime.fromisoformat(rec['started_utc']),1))
        intervals.append((datetime.fromisoformat(rec['ended_utc']),-1))
        for proc in json.loads((sub/'engines.json').read_text()).values():
            key=proc['pid'],proc['start_ticks']
            assert key not in pids
            pids.add(key)
    assert set(games)==set(range(1,21))
    assert len(pids)==40
    return games,pids,intervals


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    data={name:extract(a.root,name) for name in ('K26-1','K26-2','C26')}
    all_pids={y for _,pids,_ in data.values() for y in pids};assert len(all_pids)==120
    active=0;peak=0
    for t,n in sorted(y for _,_,v in data.values() for y in v):
        active+=n;peak=max(peak,active)
    assert active==0 and peak<=4
    base=data['K26-1'][0];reports={}
    for name in ('K26-2','C26'):
        other=data[name][0];all_diff=[];move_diff=[];n_diff=[];outcome_diff=[];clock_diff=[];first=None
        for i in sorted(base):
            b=base[i];o=other[i]
            if b==o:continue
            all_diff.append(i)
            if b[0]!=o[0]:move_diff.append(i)
            if b[1]!=o[1]:n_diff.append(i)
            if b[3][:2]!=o[3][:2]:outcome_diff.append(i)
            if b[3][3:]!=o[3][3:]:clock_diff.append(i)
            if first is None:
                cut=next((j for j in range(min(len(b[0]),len(o[0]))) if (b[0][j],b[1][j])!=(o[0][j],o[1][j])),min(len(b[0]),len(o[0])))
                def at(x):return {'move':x[0][cut],'N':x[1][cut],'used':x[2][cut]} if cut<len(x[0]) else None
                first=dict(game=i,opening=(i+1)//2,attempt_ply=cut+1,first_run=at(b),other=at(o))
        reports[name]=dict(complete_games=20,first_run_searches=sum(len(x[0]) for x in base.values()),other_searches=sum(len(x[0]) for x in other.values()),
            games_different=all_diff,move_list_different=move_diff,cost_list_different=n_diff,result_or_ending_different=outcome_diff,
            final_clock_different=clock_diff,first=first,passes=(not all_diff if name=='K26-2' else bool(all_diff)))
    doc=dict(controls=reports,distinct_engine_processes=len(all_pids),max_concurrent_games=peak)
    (a.out/'controls-independent.json').write_text(json.dumps(doc,indent=2)+'\n')
    print(json.dumps(doc,separators=(',',':')))


if __name__=='__main__':main()
