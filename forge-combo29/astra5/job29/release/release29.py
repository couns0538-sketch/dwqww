"""Verify the frozen Job 29 game/search tables, threshold outcomes and raw samples."""
import argparse
from collections import Counter,defaultdict
from csv import DictReader,writer
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import re
from statistics import NormalDist

THRESHOLDS=(300,500,800,1200,2000)
LIMITS={'D1':(4000,2000),'D2':(2000,1000),'E':(4000,2000),'D3':(8000,4000),'D4':(1000,500)}
Z=NormalDist().inv_cdf(.975)

def require(x,detail):
    if not x:raise ValueError(detail)

def table(path):
    if path.is_file():data=path.read_bytes()
    else:
        index=list(DictReader(path.with_name(path.name+'.parts.tsv').read_text().splitlines(),delimiter='\t'))
        chunks=[]
        for i in index:
            if i['kind']=='part':
                b=(path.parent/i['filename']).read_bytes()
                require(len(b)==int(i['bytes']) and sha256(b).hexdigest()==i['sha256'],str(i));chunks.append(b)
        data=b''.join(chunks)
        require(sha256(data).hexdigest()==next(i['sha256'] for i in index if i['kind']=='whole'),str(path))
    return list(DictReader(io.StringIO(data.decode()),delimiter='\t'))

def tsv(path,cols,rows):
    with path.open('w',newline='') as f:
        w=writer(f,delimiter='\t',lineterminator='\n');w.writerow(cols);w.writerows(rows)

def check_samples(path,lookup):
    count=0;packet=[];key=None
    for line in (path/'wire-samples.txt').read_text().splitlines()+['']:
        h=re.match(r'game (\d+) ply (\d+) \(',line)
        if h:key=tuple(map(int,h.groups()));packet=[]
        elif key and line:
            content=line.split(' ',1)[1]
            packet.append(content)
        elif key:
            r=lookup[key];commands=[x.split(' > ',1)[1] for x in packet if ' > ' in x];replies=[x.split(' < ',1)[1] for x in packet if ' < ' in x]
            scores=[x for x in replies if x.startswith('info depth ') and ' score ' in x]
            dnodes=[re.search(r'\bnodes (\d+)\b',x)[1] for x in replies if x.startswith('info depth ') and ' nodes ' in x]
            footers=[x for x in replies if x.startswith('info string softnodes nodes ')]
            require(commands[-1]==r['go'] and replies[-1]==r['move_line'] and
                    (scores[-1] if scores else 'NA')==r['info_line'] and
                    (dnodes[-1] if dnodes else 'NA')==r['info_nodes'] and
                    footers==([] if r['soft_line']=='NA' else [r['soft_line']]),(path,key))
            count+=1;key=None;packet=[]
    return count

def run(matches,audit,threshold_source,out,checkpoint=False):
    counts=defaultdict(Counter);ticks=defaultdict(Counter);samples=Counter()
    outcomes=defaultdict(dict);ends=defaultdict(Counter);pooled=defaultdict(Counter)
    fixed=Counter();fnodes=[];blocks=[];excluded=[];missing=Counter();positive=Counter();negative=Counter();zero=Counter()
    for b in range(1,19):
        stages=('D1','D2','E') if b<=9 else ('D3','D4')
        lo=50*((b-1)%9)+1;hi=min(434,lo+49)
        ids=set(range(2*lo-1,2*hi+1))
        groups={}
        for arm in stages:
            folder=matches/f'block{b:03d}'/arm
            if (folder/'games.tsv').is_file():
                raw=table(folder/'games.tsv')
                games={int(g['game']):g for g in raw}
                require(len(raw)==len(games) and set(games)<=ids,('extra/duplicated game',folder))
                groups[arm]=(folder,games)
        if len(groups)!=len(stages) or any(set(games)!=ids for _,games in groups.values()):
            for arm,(folder,games) in groups.items():
                unfinished=table(folder/'unfinished-searches.tsv')
                excluded.append((b,arm,sorted(games),len(unfinished)))
            continue
        blocks.append(b)
        for arm,(folder,games) in groups.items():
            rows=table(folder/'searches.tsv')
            lookup={};turns=Counter();first={}
            for r in rows:
                g,ply=int(r['game']),int(r['ply'])
                side,color=r['side'],r['color']; game=games[g]
                limit=LIMITS[arm][side=='B'];plain=arm=='E' and side=='A'
                n=int(r['n']) if r['n']!='NA' else None
                require(r['match']==arm and side==game['white' if color=='W' else 'black'] and
                        ply==turns[g]+1 and r['go']==f'go {"nodes" if plain else "softnodes"} {limit}',(folder,g,ply,'identity'))
                turns[g]+=1;lookup[g,ply]=r
                c=counts[arm,side];c['nsearch']+=1
                footer=None if r['soft_line']=='NA' else int(re.fullmatch(r'info string softnodes nodes (\d+)',r['soft_line'])[1])
                require((footer is None and r['soft_n']=='NA') or r['soft_n']==str(footer),(arm,g,ply,'footer'))
                require(r['move_line'].split()[:2]==['bestmove',r['bestmove']],(arm,g,ply,'move'))
                if plain:
                    require(r['n']==r['info_nodes'],(arm,g,ply,'E fixed'))
                    if footer is not None:
                        fnodes.append(footer)
                        fixed['lt' if footer<4000 else 'eq' if footer==4000 else 'gt']+=1
                    else:fixed['absent']+=1
                    used=4000
                else:
                    require(footer is not None and n==footer,(arm,g,ply,'soft count'))
                    used=n;c['caps']+=n>=4*limit
                    if limit==2000:
                        for group in ('all','1-40' if ply<=40 else '41-80' if ply<=80 else '81+'):
                            pooled[group]['ns']+=1;pooled[group]['sum']+=n
                if n is not None:c['sum_n']+=n;c['nreported']+=1
                c['spend']+=used
                if r['info_line']=='NA':
                    require(r['depth']==r['score']=='NA',(arm,g,ply,'NA'));c['miss']+=1;missing[arm,side]+=1
                    continue
                tokens=r['info_line'].split()
                depth=int(tokens[tokens.index('depth')+1])
                ix=tokens.index('score');kind=tokens[ix+1];v=int(tokens[ix+2])
                require(r['depth']==str(depth) and r['score']==f'{kind} {v}' and kind in ('cp','mate'),(arm,g,ply,'scored'))
                c['depth']+=depth;c['scored']+=1
                if kind=='mate':
                    (positive if v>0 else negative if v<0 else zero)[arm,side]+=1
                qualified=THRESHOLDS if kind=='mate' and v>0 else tuple(t for t in THRESHOLDS if v>=t) if kind=='cp' else ()
                for level in qualified:first.setdefault((g,side,level),ply)
            samples[arm]+=check_samples(folder,lookup)
            for g,game in games.items():
                p=int(game['plies'])
                require(turns[g]==p and int(game['opening'])==(g+1)//2 and game['white']==('A' if g%2 else 'B'),(folder,g,'game'))
                winner=game['white'] if game['result']=='1-0' else game['black'] if game['result']=='0-1' else None
                require(winner or game['result']=='1/2-1/2',game)
                outcomes[arm][g]=1 if winner is None else 2 if winner=='A' else 0
                ends[arm][game['ending']]+=1
                for side in 'AB':
                    for level in THRESHOLDS:
                        if (g,side,level) in first:
                            q=ticks[arm,side,level]
                            q['draw' if winner is None else 'won' if winner==side else 'lost']+=1
                            q['left']+=p-first[g,side,level]
    if checkpoint:return f'{blocks} complete blocks; {dict(samples)} wire packets checked'
    top=json.loads(audit.read_text())
    require(set(top['common_complete_blocks'])==set(blocks),('counted blocks',blocks,top['common_complete_blocks']))
    stated_excluded={(s['block'],s['match']):(sorted(s['finished']),s['unfinished_searches']) for s in top.get('uncounted_stages',[])}
    require(stated_excluded=={(b,arm):(games,searches) for b,arm,games,searches in excluded},('excluded stages',excluded,stated_excluded))
    th=table(threshold_source)
    require(len(th)==len(outcomes)*2*len(THRESHOLDS),('threshold rows',len(th)))
    def eq(a,b):return a==b or (a is not None and b is not None and math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-9))
    for v in th:
        arm=v['match'];side=v['side'];level=int(v['threshold_cp']);q=ticks[arm,side,level]
        wins,draws,losses=q['won'],q['draw'],q['lost'];n=wins+draws+losses
        require([int(v[x]) for x in ('games_reached','won','drew','lost')]==[n,wins,draws,losses] and
                (not n or eq(v['mean_plies_remaining'],q['left']/n)),(v,q))
    verifier_thresholds=table(audit.with_name('thresholds.tsv'))
    lookup_outcomes={(r['match'],r['side'],int(r['threshold'])):r for r in verifier_thresholds}
    for (arm,side,level),q in ticks.items():
        r=lookup_outcomes[arm,side,level]
        require((q['won'],q['draw'],q['lost'],q['left'])==tuple(int(r[col]) for col in ('wins','draws','losses','remaining_plies_total')),r)
    lines=[f'Counted global block IDs {blocks}. Excluded partial stages (block, arm, finished games, unfinished searches): '
           +str([(b,arm,len(gs),ns) for b,arm,gs,ns in excluded])+'.']
    for arm,games in outcomes.items():
        meta=top['arms'][arm]; bins=[0]*5
        for g in games:
            if g%2:bins[games[g]+games[g+1]]+=1
        w=Counter(games.values());ng=len(games);n=ng//2;p=sum(b*i for i,b in enumerate(bins))/(4*n)
        se=math.sqrt(sum(b*(i/4-p)**2 for i,b in enumerate(bins)))/(n)
        to_elo=lambda v:400*math.log10(v/(1-v))
        elo=to_elo(p);width=(to_elo(p+Z*se)-to_elo(p-Z*se))/2
        require(meta['A_WLD']==[w[2],w[0],w[1]] and bins==meta['penta'] and dict(ends[arm])==meta['endings'] and
                all(eq(a,b) for a,b in zip((elo,elo-width,elo+width),meta['elo_lower_upper'])),(arm,meta['A_WLD'],bins))
        for side in 'AB':
            c=counts[arm,side];v=meta['players'][side]
            for key,measured in [('searches',c['nsearch']),('n_total',c['sum_n']),('spent_total',c['spend']),('depth_total',c['depth']),('depth_reported',c['scored']),('no_score',c['miss'])]:
                require(eq(v[key],measured),(arm,side,key,v[key],measured))
            if not (arm=='E' and side=='A'):require(v['hardcap']==c['caps'],(arm,side,'cap'))
        lines.append(f'{arm}: pairs {n}; A W/L/D {w[2]}/{w[0]}/{w[1]}; bins {bins}; Elo {elo:.6f} [{elo-width:.6f},{elo+width:.6f}]; verified {samples[arm]} first/last raw search packets.')
        a,b=(counts[arm,side] for side in 'AB')
        require(eq(meta['nodes_ratio'],(a['spend']/a['nsearch'])/(b['spend']/b['nsearch'])),(arm,'spend ratio'))
    for band,c in pooled.items():
        v=top['pooled_2000'][band];require((v['searches'],v['n_total'])==(c['ns'],c['sum']),(band,c,v))
    lines.extend([f'Threshold rows checked {len(th)}. Positive mate rows {sum(positive.values())}, negative {sum(negative.values())}, zero {sum(zero.values())}. Only positive mate qualified. Missing scores {sum(missing.values())}; included for spend and search counts, excluded from scored depth and all thresholds.',
                  'Remaining plies equal final played plies minus first qualifying ply. Outcomes use the qualifying player perspective.',
                  f'Final independent audit SHA256 {sha256(audit.read_bytes()).hexdigest()}; threshold table SHA256 {sha256(threshold_source.read_bytes()).hexdigest()}.'])
    if fnodes:
        c=counts['E','A']
        tsv(out/'fixed-footer.tsv',('searches','footer_reported','footer_absent','footer_under_4000','footer_eq_4000','footer_over_4000','footer_min','footer_max','footer_sum','footer_mean','finished_reported','finished_sum','finished_mean','nominal_sum','nominal_mean'),
            [(c['nsearch'],len(fnodes),fixed['absent'],fixed['lt'],fixed['eq'],fixed['gt'],min(fnodes),max(fnodes),sum(fnodes),sum(fnodes)/len(fnodes),c['nreported'],c['sum_n'],c['sum_n']/c['nreported'],c['spend'],c['spend']/c['nsearch'])])
    (out/'verification.txt').write_text('\n'.join(lines)+'\n')
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('matches','audit_json','thresholds_tsv','output'):p.add_argument(k,type=Path)
    p.add_argument('--checkpoint',action='store_true')
    a=p.parse_args();print(run(a.matches,a.audit_json,a.thresholds_tsv,a.output,a.checkpoint))
