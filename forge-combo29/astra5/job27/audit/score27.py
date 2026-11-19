"""Compute all three readings only from fully completed common opening blocks."""
import argparse
from collections import Counter
import json
from pathlib import Path
from replay27 import CUTOFF,STOP,check,table_out,time
from stats_seed import evaluate

N=434
ARMS=('M1','M2','M3')


def summarize(games):
    roles={r:Counter() for r in ('A','B')}
    colors=Counter();endings=Counter();penta=[0]*5;wdl=Counter();flags=[]
    ids={g['game']:g for g in games};check(len(ids)==len(games),'duplicate match game')
    opens=sorted({g['opening'] for g in games});scores=[];pairs=[];n=len(games)
    for k in opens:
        a,b=ids[2*k-1],ids[2*k]
        check((a['opening'],b['opening'],a['white'],b['white'])==(k,k,'A','B'),('swapped pair',k))
        x=a['score']+b['score'];scores.append(x/4);penta[x]+=1
        pairs.append([k,2*k-1,2*k,a['result'],b['result'],x/2])
    for g in games:
        wdl[g['score']]+=1;endings[g['ending']]+=1
        if g['flag']:flags.append(g['flag'])
        for r in roles:
            rs=roles[r];c='W' if g['white']==r else 'B'
            rs['clock']+=g['clocks'][c]
            for field in ('count','spent','nodes','holds','holdlines'):rs[field]+=g[field].get(r,0)
        for c in ('W','B'):colors[c]+=g['clocks'][c]
    check(sum(roles[r]['clock'] for r in roles)==sum(colors.values()),'clock roles versus colors')
    players={}
    for r,rs in roles.items():
        f=[x for x in flags if x[3]==r]
        expected=6000*n+60*(rs['count']-len(f))-rs['spent']+sum(x[5] for x in f)
        check(rs['clock']==expected,(r,'clock balance',expected,rs))
        players[r]=dict(searches=rs['count'],used_total=rs['spent'],N_total=rs['nodes'],mean_used=rs['spent']/rs['count'] if rs['count'] else None,
            hold_searches=rs['holds'],hold_lines=rs['holdlines'],clock_total=rs['clock'],mean_final_clock=rs['clock']/n if n else None)
    try:elo=evaluate(scores)
    except (ZeroDivisionError,ValueError):elo=None
    result=dict(pairs=len(opens),games=n,searches=sum(v['searches'] for v in players.values()),plies=sum(g['plies'] for g in games),A_WLD=[wdl[2],wdl[0],wdl[1]],penta=penta,
        elo_lower_upper=elo,reading=('A BETTER' if elo[1]>0 else 'B BETTER' if elo[2]<0 else 'LEVEL') if elo else 'NO FINITE INTERVAL',
        endings=dict(endings),time_losses=flags,players=players,by_colour_mean_clock={c:colors[c]/n if n else None for c in ('W','B')},distinct_processes=2*n)
    return result,pairs


def collect(out,stages,wire_root,final=False):
    out.mkdir(parents=True,exist_ok=True)
    catalog={(v['block'],v['stage']):v for v in stages}
    check(len(stages)==len(catalog),'duplicate arm')
    common=[];complete_opens=[];by45=[];receipts45=[];straddlers=[];stage_rows=[];block_rows=[];unscored=[]
    ids=set();events=[];latest=None;source=wire_root/'blocks' if (wire_root/'blocks').is_dir() else wire_root;block_times={}
    for block in range(1,10):
        lo,hi=(block-1)*50+1,min(block*50,N)
        entries=[catalog.get((block,r)) for r in ARMS]
        ok=all(x and x['complete'] for x in entries)
        if ok:
            expected=set(range(2*lo-1,2*hi+1))
            check(all(set(x['finished_ids'])==expected for x in entries),(block,'missing games'))
            receipt_path=source/f'block{block:03d}'/'receipt.json'
            if not receipt_path.is_file():
                check(not final,('missing block receipt',block))
                continue
            receipt=json.loads(receipt_path.read_text());check(receipt['complete'],(block,'scheduler disagrees'))
            finish=max(time(g['finish']) for entry in entries for g in entry['games'])
            s=time(receipt['sealed_utc'])
            check(time(receipt['last_game_end_utc'])==finish and finish<=s,(block,finish,s,receipt))
            check(receipt['finished_by_minute45']==(finish<=CUTOFF),(block,'cutoff mismatch'))
            common.append(block);complete_opens.extend(range(lo,hi+1))
            if finish<=CUTOFF:by45.append(block)
            if s<=CUTOFF:receipts45.append(block)
            if finish<=CUTOFF<s:straddlers.append(block)
            block_times[block]=(finish.isoformat(),s.isoformat())
        block_rows.append((block,lo,hi,ok,*(block_times.get(block,('','')))))
        for stage,entry in zip(ARMS,entries):
            all_games=entries and (entry['games'] if entry else [])
            first=min((time(g['start']) for g in all_games),default=None)
            last=max((time(g['finish']) for g in all_games),default=None)
            if first is not None:
                if latest is not None:check(latest<=first,(block,stage,'arm execution overlaps prior arm'))
                latest=last
                if stage=='M1':check(first<CUTOFF,('new block started after minute45',block,first))
                check(last<=STOP,('finished game past minute50',block,stage,last))
            if entry:
                for g in entry['games']:
                    for p in g['processes']:
                        ident=tuple(p);check(ident not in ids,(block,stage,'reused PID',ident));ids.add(ident)
                    events.extend([(time(g['start']),1),(time(g['finish']),-1)])
            status='counted' if ok else 'played in an uncounted block' if entry else 'not played'
            stage_rows.append((block,stage,lo,hi,status,entry['started'] if entry else 0,entry['finished'] if entry else 0,
                entry['searches'] if entry else 0,entry['unfinished_searches'] if entry else 0,(first.isoformat() if first else ''),(last.isoformat() if last else '')))
            if not ok and entry:
                unscored.append(dict(block=block,stage=stage,finished_game_ids=entry['finished_ids'],unfinished_game_ids=entry['unfinished'],
                    not_started_game_ids=entry['unstarted'],finished_games=entry['finished'],unfinished_searches=entry['unfinished_searches']))
    if common:check(common==list(range(1,common[-1]+1)),('nonprefix common blocks',common))
    phase={}
    for r in ARMS:
        games=[g for b in common for g in catalog[b,r]['games']]
        phase[r],pairs=summarize(games)
        table_out(out/(r+'-pairs.tsv'),['opening','A_White_game','B_White_game','A_White_result','B_White_result','A_pair_points'],pairs)
    balance=peak=0
    for _,d in sorted(events):balance+=d;peak=max(peak,balance)
    check(balance==0 and peak<=4,('observed concurrency',peak))
    table_out(out/'stages-independent.tsv',['block','arm','first_opening','last_opening','classification','started_games','finished_games','finished_searches','partial_searches','first_game_start_utc','last_game_finish_utc'],stage_rows)
    table_out(out/'blocks-independent.tsv',['block','first_opening','last_opening','counts','last_game_finish_utc','scheduler_sealed_utc'],block_rows)
    table_out(out/'time-losses.tsv',['arm','game','ply','side','engine','N','used','clock_before'],[(r,*f) for r in ARMS for f in phase[r]['time_losses']])
    ending=source/'schedule-end.json'
    if final:
        sch=json.loads(ending.read_text())
        check(sch['common_complete_blocks']==common and sch['blocks_complete_by_minute45']==by45,(sch,common,by45))
    result=dict(final=final,common_blocks=len(common),common_openings=len(complete_opens),common_block_ids=common,common_opening_ids=complete_opens,
        blocks_complete_by_minute45=len(by45),blocks_complete_by_minute45_ids=by45,blocks_by_scheduler_receipt_minute45=len(receipts45),cutoff_straddling_blocks=straddlers,
        arms=phase,excluded_stages=unscored,unplayed_blocks=[b for b in range(1,10) if not any((b,r) in catalog for r in ARMS)],
        peak_concurrent_games=peak,distinct_processes_verified=len(ids),total_time_losses=sum(len(phase[r]['time_losses']) for r in ARMS),
        pc_M1_elo_interval=[-14.4,-23.5,-5.4],M1_comparison='M1 READS AS THE PC\'S (B BETTER)' if phase['M1']['reading']=='B BETTER' else 'M1 READS OTHERWISE')
    outpath=out/'independent.json';temp=outpath.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2)+'\n');temp.replace(outpath)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('audited_stages',type=Path);p.add_argument('game_root',type=Path);p.add_argument('out',type=Path);p.add_argument('--final',action='store_true');a=p.parse_args()
    stages=[json.loads(x.read_text()) for x in a.audited_stages.glob('block*/M*.json')]
    s=collect(a.out,stages,a.game_root,a.final)
    print(s['common_blocks'],'complete blocks',[(r,st['A_WLD'],st['elo_lower_upper']) for r,st in s['arms'].items()])
