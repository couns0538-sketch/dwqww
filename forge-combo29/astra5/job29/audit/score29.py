"""Summarize fully shared opening blocks, independently scored from replayed game evidence."""
from common29 import *
from stats_seed import evaluate

CLOSE=utc('2026-11-19T23:28:09+00:00')
STOP=utc('2026-11-19T23:33:09+00:00')
EARLY=utc('2026-11-19T23:18:09+00:00')

def per_arm(arm, games):
    lookup={x['game']:x for x in games};check(len(lookup)==len(games),(arm,'duplicate games'))
    openings=sorted({x['opening'] for x in games});score=[];penta=[0]*5;pairs=[]
    for k in openings:
        w=lookup[2*k-1];b=lookup[2*k]
        check((w['opening'],b['opening'],w['white'],b['white'])==(k,k,'A','B'),(arm,k))
        mark=w['score']+b['score'];penta[mark]+=1;score.append(mark/4)
        pairs.append((k,2*k-1,2*k,w['result'],b['result'],mark/2))
    wld=Counter(x['score'] for x in games);endings=Counter(x['ending'] for x in games);plies=sum(x['plies'] for x in games)
    try:elo=evaluate(score)
    except (ValueError,ZeroDivisionError):elo=None
    result=dict(pairs=len(score),games=len(games),A_WLD=[wld[2],wld[0],wld[1]],penta=penta,elo_lower_upper=elo,
                reading=None if not elo else 'A BETTER' if elo[1]>0 else 'B BETTER' if elo[2]<0 else 'LEVEL',
                endings=dict(endings),plies=plies,mean_plies=plies/len(games) if games else None)
    players={}
    for k,cmd in zip(('A','B'),GO[arm]):
        acc=Counter()
        for g in games:acc.update(g['players'][k])
        cnt=acc['searches'];reads=acc['depth_reported']
        players[k]=dict(go='go '+cmd,**{key:acc[key] for key in ('searches','n_total','spent_total','depth_reported','depth_total','no_score')},
                        mean_n=acc['n_total']/cnt if cnt else None,mean_spent=acc['spent_total']/cnt if cnt else None,
                        mean_depth=acc['depth_total']/reads if reads else None,mean_depth_zero=acc['depth_total']/cnt if cnt else None,
                        hardcap=acc['hardcap'] if cmd.startswith('soft') else None,
                        hardcap_share=acc['hardcap']/cnt if cnt and cmd.startswith('soft') else None)
    result['players']=players;result['nodes_ratio']=players['A']['mean_spent']/players['B']['mean_spent'] if games else None
    check(plies==sum(v['searches'] for v in players.values()),arm)
    crosses=[]
    for threshold in THRESHOLDS:
        for side in ('A','B'):
            x=Counter();remain=0;triggered=0
            for g in games:
                j=g['first'][side].get(str(threshold),g['first'][side].get(threshold))
                if j is None:continue
                triggered+=1;remain+=g['plies']-int(j);mark=g['score'] if side=='A' else 2-g['score']
                x[mark]+=1
            crosses.append((arm,side,threshold,len(games),triggered,x[2],x[1],x[0],remain,remain/triggered if triggered else None))
    return result,pairs,crosses

def collect(out,cache,root,final=False):
    out.mkdir(parents=True,exist_ok=True); catalog={(s['block'],s['match']):s for s in cache}
    check(len(cache)==len(catalog),'duplicate stage archive')
    phase={'main':[],'optional':[]};by40=[];byreceipt=[];straddle=[];common=[];blockrows=[];stage_rows=[];ignored=[];pids=set();events=[]
    for b in range(1,19):
        primary=b<=9;key='main' if primary else 'optional';arms=ARMS[key]
        number=b if primary else b-9;lo=1+(number-1)*50;hi=min(434,number*50)
        stages=[catalog.get((b,a)) for a in arms];ok=all(s and s['complete'] for s in stages);end=seal=None
        bp=root/f'block{b:03d}'/'receipt.json'
        if ok and bp.exists():
            expected=set(range(2*lo-1,2*hi+1))
            check(all(set(g['game'] for g in s['games'])==expected for s in stages),(b,'coverage'))
            rec=json.loads(bp.read_text());end=max(utc(g['finish']) for s in stages for g in s['games']);seal=utc(rec['sealed_utc'])
            check(rec['complete'] and end==utc(rec['last_game_end_utc']) and end<=seal,(b,rec))
            common.append(b);phase[key].append(b)
            if end<=CLOSE:by40.append(b)
            if seal<=CLOSE:byreceipt.append(b)
            if end<=CLOSE<seal:straddle.append(b)
        elif ok:
            check(not final,('missing block at final',b));ok=False
        blockrows.append((b,key,lo,hi,ok,end.isoformat() if end else None,seal.isoformat() if seal else None))
        for a,s in zip(arms,stages):
            if s:
                times=[(utc(g['start']),utc(g['finish'])) for g in s['games']]
                if times:
                    check(max(y for _,y in times)<=STOP,(b,a,'after stop'))
                    if a==arms[0]:check(min(x for x,_ in times)<CLOSE,(b,'new block after 40'))
                for g,t in zip(s['games'],times):
                    for pid in g['processes']:
                        pair=tuple(pid);check(pair not in pids,(b,a,g['game'],pair));pids.add(pair)
                    events.extend([(t[0],1),(t[1],-1)])
                if not ok:ignored.append(dict(block=b,match=a,finished=[g['game'] for g in s['games']],unfinished=s['unfinished'],unstarted=s['unstarted'],unfinished_searches=s['unfinished_searches']))
                stage_rows.append((b,key,a,lo,hi,'counted' if ok else 'excluded',s['started'],s['finished'],s['unfinished_searches'],
                                   min((x for x,_ in times),default=''),max((y for _,y in times),default='')))
            else:stage_rows.append((b,key,a,lo,hi,'not played',0,0,0,None,None))
    arms={};cross=[];bands=defaultdict(Counter)
    for scope,names in ARMS.items():
        for a in names:
            if scope=='optional' and not any((b,a) in catalog for b in range(10,19)):continue
            games=[g for b in phase[scope] for g in catalog[b,a]['games']]
            stats,pairs,ss=per_arm(a,games);arms[a]=stats;cross+=ss
            write_table(out/(a+'-pairs.tsv'),['opening','A_white_game','B_white_game','A_white_result','B_white_result','A_pair_points'],pairs)
            for g in games:
                for band,metrics in g['bands'].items():bands[band].update(metrics)
    pooled={k:{'searches':bands[k]['searches'],'n_total':bands[k]['n_total'],'mean_n':bands[k]['n_total']/bands[k]['searches'] if bands[k]['searches'] else None} for k in ('all','1-40','41-80','81+')}
    for metric in ('searches','n_total'):check(pooled['all'][metric]==sum(pooled[k][metric] for k in ('1-40','41-80','81+')),'pooled band totals')
    side_total=sum(zz['searches'] for s in arms.values() for zz in s['players'].values() if zz['go']=='go softnodes 2000')
    check(side_total==pooled['all']['searches'],'pooled side totals')
    count=peak=0
    for _,delta in sorted(events):count+=delta;peak=max(peak,count)
    check(count==0 and peak<=4,('concurrency',count,peak))
    decision=None
    if 9 in common:
        end=utc(json.loads((root/'block009/receipt.json').read_text())['last_game_end_utc']);decision=end<EARLY
    if phase['optional']:check(decision,('optional not admitted',phase))
    if final:
        run=json.loads((root/'schedule-end.json').read_text())
        check(run['common_complete_blocks']==common and run['blocks_complete_by_minute40']==by40,(run,common,by40))
        check(run['complete_by_phase']=={'primary':phase['main'],'additional':phase['optional']},(run,phase))
        check(bool(run['additional_phase_eligible'])==bool(decision),(run,decision))
    result=dict(final=final,arms=arms,pooled_2000=pooled,common_complete_blocks=common,complete_by_phase=phase,
                blocks_complete_by_minute40=len(by40),block_ids_by_minute40=by40,scheduler_receipts_by_minute40=byreceipt,
                cutoff_straddling_blocks=straddle,additional_phase_eligible=decision,peak_simultaneous_games=peak,
                observed_processes=len(pids),observed_complete_games=len(events)//2,uncounted_stages=ignored)
    e=arms['E'];result['E_line']=None if not e['reading'] else {'A BETTER':'PER NODE THE PLAIN COUNT IS BETTER','B BETTER':'PER NODE THE SOFT LIMIT IS BETTER','LEVEL':'E IS LEVEL'}[e['reading']]
    write_table(out/'thresholds.tsv',['match','side','threshold','games','reached','wins','draws','losses','remaining_plies_total','mean_remaining_plies'],cross)
    write_table(out/'blocks.tsv',['block','phase','first_opening','last_opening','counted','last_game_finish_utc','sealed_utc'],blockrows)
    write_table(out/'stages.tsv',['block','phase','match','first_opening','last_opening','disposition','started','finished','unfinished_searches','earliest','latest'],stage_rows)
    dump(out/'independent.json',result)
    return result
