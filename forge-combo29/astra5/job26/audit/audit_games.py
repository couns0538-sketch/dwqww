"""Independently replay Job 26 paired node-clock games, including raw protocol evidence."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import chess
from stats_seed import evaluate

BOOK_SHA = '889e8db12ee327cae68b29ada3458a2fb957cf8f5563d29a7fd13d850ff3f638'
CUTOFF = datetime(2026, 11, 19, 19, 11, 2, tzinfo=timezone.utc)
STOP = datetime(2026, 11, 19, 19, 16, 2, tzinfo=timezone.utc)
OPTIONS = (
    'Threads 1|Hash 16|OwnBook false|MateAlphaGuard true|LmrQuietBase 93|'
    'LmrQuietDivisor 205|LmrNoisyBase 13|LmrNoisyDivisor 333|LmrHistoryDivisor 5643|'
    'NullMoveBase 5|LmpBase 8|HistoryPruneMultiplier 2220|HistoryBonusQuadratic 24|'
    'HistoryBonusLinear 54|HistoryBonusMax 2212|SingularDepth 6|IirDepth 2|'
    'NonPawnCorrection true|CuckooRep true|HistRework 2|TtPruneV2 true|CorrHistV2 true'
).split('|')


def table(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def table_out(path, fields, records):
    with path.open('w', newline='') as stream:
        writer=csv.writer(stream,delimiter='\t',lineterminator='\n')
        writer.writerow(fields); writer.writerows(records)


def check(ok, detail):
    if not ok:
        raise ValueError(str(detail))


def time(s):
    return datetime.fromisoformat(s.replace('Z','+00:00'))


def rule(b):
    if b.is_checkmate():return 'checkmate'
    if b.is_stalemate():return 'stalemate'
    if b.is_insufficient_material():return 'insufficient'
    if b.can_claim_threefold_repetition():return 'threefold'
    if b.can_claim_fifty_moves():return 'fifty'
    return None


def board_end(label):
    if label in ('time','cap','checkmate','stalemate'):return label
    low=label.lower()
    if 'mate'==low:return 'checkmate'
    if 'repet' in low or 'threefold' in low:return 'threefold'
    if 'fifty' in low or '50' in low:return 'fifty'
    if 'insuff' in low or low=='material':return 'insufficient'
    raise ValueError(f'unrecognized ending {label}')


def score2(rec):
    if rec['result']=='1/2-1/2':return 1
    check(rec['result'] in ('1-0','0-1'), rec)
    return 2*int((rec['white']=='A') == (rec['result']=='1-0'))


def read_wire(path):
    packets=[]; setup={'W':[],'B':[]}; traffic={'W':[],'B':[]}
    for number,raw in enumerate(path.read_text().splitlines(),1):
        check(not re.search('unknown option|invalid value|ERROR', raw,re.I),(path,number,raw))
        m=re.match(r'^([WB])\s*([<>])\s*(.*)$',raw)
        if not m: continue
        side,sign,text=m.groups()
        if sign=='>' and text.startswith('position '):
            packets.append(dict(s=side,pos=text,go=None,soft=[],moves=[],hold=[]))
        elif sign=='>' and text.startswith('go '):
            checking=packets[-1];check(side==checking['s'] and not checking['go'],raw);checking['go']=text
        elif sign=='<' and text.startswith(('info string TmFinishIteration hold','info string softnodes nodes','bestmove ')):
            p=packets[-1];check(side==p['s'] and p['go'],raw)
            which='soft' if text.startswith('info string softnodes') else 'moves' if text.startswith('bestmove ') else 'hold'
            p[which].append(text)
        elif sign=='>' and text!='quit':
            setup[side].append(text)
        elif sign=='<' and text in ('uciok','readyok'):
            traffic[side].append(text)
    return setup,traffic,packets


def replay_game(folder, rec, stage, book):
    game=int(rec['game']);opening=int(rec['opening'])
    check(opening==(game+1)//2 and rec['white']==('A' if game%2 else 'B'),rec)
    check({rec['white'],rec['black']}=={'A','B'},rec)
    game_path=folder/f'g{game:04d}'
    data=table(game_path/'searches.tsv')
    setup,traffic,packets=read_wire(game_path/'wire.txt')
    engines=json.loads((game_path/'engines.json').read_text())
    exe=json.loads((folder/'inputs.json').read_text())['exe']
    check(table(game_path/'result.tsv')==[rec], (game,'per-game receipt differs from stage receipts'))
    ephemeral=[]
    expected_opening=' '.join(book[opening-1].split()[:4])+' 0 1'
    check((game_path/'opening.txt').read_text().strip()==f'{opening}\t{expected_opening}',(game,'wrong EPD receipt'))

    for side,engine in [('W',rec['white']),('B',rec['black'])]:
        nodeclock=2000 if engine=='A' and stage=='C26' else 1000
        params=OPTIONS+[f'NodeClock {nodeclock}',f'TmFinishIteration {str(engine=="A").lower()}']
        expected=['uci']+['setoption name '+p.rsplit(' ',1)[0]+' value '+p.rsplit(' ',1)[1] for p in params]+['ucinewgame','isready']
        meta=engines[side]
        check(meta['role']==engine and [' '.join(x) for x in meta['options']]==params,(game,'engine options',side))
        check(meta['exe']==exe,(game,meta['exe'],exe))
        ident=(int(meta['pid']),int(meta['start_ticks']))
        check(ident not in ephemeral,(game,'same process on both sides'));ephemeral.append(ident)
        check(setup[side]==expected,(game,side,setup[side],expected))
        check(traffic[side]==['uciok','readyok'],(game,side,traffic))
    check(len(data)==len(packets),(game,len(data),len(packets)))
    b=chess.Board(book[opening-1]);fen=b.fen()
    clocks={'W':6000,'B':6000};names={'W':rec['white'],'B':rec['black']}
    spent=Counter();count=Counter();holds=Counter();holdlines=Counter();nodes=Counter()
    applied=[];seq=[];end=None;result=None;flag=None
    for i,(s,p) in enumerate(zip(data,packets),1):
        who='W' if b.turn else 'B';engine=names[who];other='B' if who=='W' else 'W'
        check(end is None,(game,i,'moves after finalized board',end))
        check(int(s['game'])==game and int(s['ply'])==i and s['engine']==engine,(game,i,s))
        check(s['side'].upper() in (who,{'W':'WHITE','B':'BLACK'}[who]),(game,i,s['side'],who))
        expected_pos='position fen '+fen+' moves'+(' '+' '.join(applied) if applied else '')
        expected_go=f"go wtime {clocks['W']} btime {clocks['B']} winc 60 binc 60"
        check(p['s']==who and p['pos'].strip()==expected_pos and p['go']==expected_go,(game,i,p['pos'],expected_pos,p['go'],expected_go))
        check(len(p['soft'])==len(p['moves'])==1,(game,i,p))
        m=re.fullmatch(r'info string softnodes nodes (\d+)',p['soft'][0]);check(m,(game,i,p['soft']))
        n=int(m[1]); used=n//1000; move=p['moves'][0].split()[1]
        check(s['soft_line']==p['soft'][0] and s['move_line']==p['moves'][0],(game,i,s,p))
        check((int(s['N']),int(s['used']),s['bestmove'])==(n,used,move),(game,i,s))
        check(int(s['holds'])==len(p['hold']),(game,i,s['holds'],p['hold']))
        check((int(s['clock_before']),int(s['wtime']),int(s['btime']))==(clocks[who],clocks['W'],clocks['B']),(game,i,s))
        board_move=b.parse_uci(move)
        check(board_move in b.legal_moves,(game,i,move,b.fen()))
        before=clocks[who]
        seq.append((move,n));spent[engine]+=used;count[engine]+=1;holds[engine]+=bool(p['hold']);holdlines[engine]+=len(p['hold']);nodes[engine]+=n
        if used>before:
            end='time';result='0-1' if who=='W' else '1-0'
            flag=(game,i,who,engine,n,used,before)
        else:
            clocks[who]=before-used+60
            b.push(board_move);applied.append(move)
            end=rule(b)
            if end=='checkmate':result='1-0' if who=='W' else '0-1'
            elif end:result='1/2-1/2'
            elif len(applied)==600:end='cap';result='1/2-1/2'
        check(int(s['clock_after'])==clocks[who],(game,i,s['clock_after'],clocks))
    check((board_end(rec['ending']),rec['result'],int(rec['plies']),int(rec['wclock']),int(rec['bclock']))==(end,result,len(applied),clocks['W'],clocks['B']),(game,rec,end,result,clocks))
    return dict(game=game,opening=opening,white=rec['white'],score=score2(rec),result=result,ending=end,plies=len(applied),clocks=clocks,
                count=dict(count),spent=dict(spent),holds=dict(holds),holdlines=dict(holdlines),nodes=dict(nodes),flag=flag,seq=seq,
                start=rec['started_utc'],finish=rec['ended_utc'],processes=ephemeral)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path);parser.add_argument('stage');parser.add_argument('book',type=Path);parser.add_argument('out',type=Path)
    parser.add_argument('--target',type=int,help='require this many complete pairs');parser.add_argument('--cache',type=Path)
    a=parser.parse_args();check(chess.__version__=='1.11.2','python-chess version')
    book=a.book.read_bytes();check(sha256(book).hexdigest()==BOOK_SHA,'wrong opening book')
    book=book.decode().splitlines();folder=a.root/a.stage; a.out.mkdir(parents=True,exist_ok=True)
    pair_receipts=table(folder/'pairs.tsv');openings=sorted({int(x['opening']) for x in pair_receipts})
    check(len(openings)==len(pair_receipts) and (a.target is None or len(openings)==a.target),('pair count',openings,a.target))
    launches=table(folder/'launch.tsv')
    target_order=range(10,0,-1) if a.stage=='K26-2' else range(11,235) if a.stage=='M' else range(1,11)
    sequence=[(k,i) for k in target_order for i in (2*k-1,2*k)]
    for idx,l in enumerate(launches):
        k,g=sequence[idx]
        check((int(l['ordinal']),int(l['opening']),int(l['game']))==(idx+1,k,g),(a.stage,l))
        if a.stage=='M' and g%2:check(time(l['utc'])<CUTOFF,(a.stage,'new pair after minute 45',l))
    for r in pair_receipts:
        k=int(r['opening'])
        check((int(r['game_A_white']),int(r['game_B_white']))==(2*k-1,2*k),r)
    advertised=json.loads((folder/'inputs.json').read_text())
    check(advertised['sha256']=='9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3'
          and advertised['book_sha256']==BOOK_SHA and advertised['python_chess']=='1.11.2' and advertised['concurrent_games']<=4,advertised)
    receipts_by_k={int(x['opening']):x for x in pair_receipts}
    gameids={i for k in openings for i in (2*k-1,2*k)}
    records={int(x['game']):x for x in table(folder/'games.tsv')}
    check(set(records)>=gameids,(folder,'missing receipts'))
    games={}
    if a.cache:a.cache.mkdir(parents=True,exist_ok=True)
    for game in sorted(gameids):
        rec=records[game]
        cachefile=a.cache/f'{a.stage}-{game}.json' if a.cache else None
        if cachefile and cachefile.exists():
            g=json.loads(cachefile.read_text())
        else:
            g=replay_game(folder,rec,a.stage,book)
            if cachefile:cachefile.write_text(json.dumps(g,separators=(',',':')))
        games[game]=g
    identities=[tuple(p) for g in games.values() for p in g['processes']]
    check(len(set(identities))==len(identities),(a.stage,'PID/start-ticks reused across games'))
    n=len(openings)
    sums=Counter();ends=Counter();flags=[];bins=[0]*5
    summaries=[];pairs=[];by45=0
    for k in openings:
        left,right=games[2*k-1],games[2*k]
        v=left['score']+right['score'];bins[v]+=1
        closed=max(time(left['finish']),time(right['finish']));check(closed<STOP,('game completed after stop',k))
        receipt_time=time(receipts_by_k[k]['completed_utc'])
        check(closed<=receipt_time,(k,closed,receipt_time))
        by45+=receipt_time<=CUTOFF
        pairs.append([k,2*k-1,2*k,left['result'],right['result'],v/2,closed.isoformat()])
        for g in (left,right):
            ends[g['ending']]+=1;sums[('L','D','W')[g['score']]]+=1
            if g['flag']:flags.append(g['flag'])
            for name in ['A','B']:
                for what in ('count','spent','holds','holdlines','nodes'):
                    sums[(what,name)]+=g[what].get(name,0)
                side='W' if g['white']==name else 'B'
                sums[('clock',name)]+=g['clocks'][side]
            for side in ['W','B']:sums[('clock',side)]+=g['clocks'][side]
            summaries.append([g['game'],k,g['white'],g['result'],g['ending'],g['plies'],g['clocks']['W'],g['clocks']['B'],
                              g['count'].get('A',0),g['count'].get('B',0),g['spent'].get('A',0),g['spent'].get('B',0),
                              g['holds'].get('A',0),g['holds'].get('B',0),g['start'],g['finish']])
    scores=[i/4 for i,c in enumerate(bins) for _ in range(c)]
    try:elo=evaluate(scores)
    except (ValueError,ZeroDivisionError):elo=None
    summary=dict(stage=a.stage,openings=openings,pairs=n,pairs_by_minute45=by45,games=2*n,distinct_processes=len(set(identities)),A_WLD=[sums['W'],sums['L'],sums['D']],penta=bins,elo_lower_upper=elo,
        reading='A BETTER' if elo and elo[1]>0 else 'B BETTER' if elo and elo[2]<0 else 'LEVEL' if elo else 'not finite at this checkpoint',
        endings=dict(ends),time_losses=flags,players={name:{'searches':sums['count',name],'used_total':sums['spent',name],'N_total':sums['nodes',name],
        'mean_used':sums['spent',name]/sums['count',name] if sums['count',name] else None,'hold_searches':sums['holds',name],'hold_lines':sums['holdlines',name],
        'clock_total':sums['clock',name],'mean_final_clock':sums['clock',name]/(2*n) if n else None} for name in ('A','B')},
        by_colour_mean_clock={c:sums['clock',c]/(2*n) if n else None for c in ['W','B']})
    table_out(a.out/'paired-ends.tsv',['opening','odd_game','even_game','odd_result','even_result','A_pair_points','complete_utc'],pairs)
    table_out(a.out/'game-readback.tsv',['game','opening','White','result','ending','plays','W_final','B_final','A_searches','B_searches','A_used','B_used','A_hold_searches','B_hold_searches','started','ended'],sorted(summaries))
    table_out(a.out/'time-losses.tsv',['game','ply','side','engine','N','used','clock_before'],flags)
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='openings'},separators=(',',':')))


if __name__=='__main__':main()
